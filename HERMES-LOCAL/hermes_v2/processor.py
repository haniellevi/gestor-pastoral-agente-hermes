from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

from .classifier import Classification, classify
from .db import execute, fetch_one, get_connection, is_postgres
from .schema import ensure_sqlite_schema


def normalize_phone(value: Any) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def _clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.startswith("{{") and text.endswith("}}"):
        return ""
    return text


def _as_int(value: Any) -> int | None:
    try:
        text = _clean(value)
        return int(text) if text else None
    except (TypeError, ValueError):
        return None


def _json_dumps(value: Any) -> str:
    return json.dumps(value or {}, ensure_ascii=False, sort_keys=True)


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    campos = payload.get("campos") if isinstance(payload.get("campos"), dict) else {}
    normalized = dict(payload)
    normalized["subscriber_id"] = _as_int(payload.get("subscriber_id") or payload.get("botconversa_subscriber_id"))
    normalized["nome"] = _clean(payload.get("nome") or payload.get("name") or campos.get("nome")) or "Pessoa sem nome"
    normalized["telefone"] = normalize_phone(payload.get("telefone") or payload.get("phone") or campos.get("telefone"))
    normalized["mensagem"] = _clean(
        payload.get("mensagem")
        or payload.get("message")
        or payload.get("resumo")
        or payload.get("resumo_ia")
    )
    normalized["fluxo_origem"] = _clean(payload.get("fluxo_origem") or payload.get("flow") or payload.get("fluxo"))
    normalized["tipo_evento"] = _clean(payload.get("tipo_evento") or payload.get("evento") or payload.get("ultima_intencao") or "mensagem")
    normalized["campos"] = campos
    return normalized


def build_idempotency_key(payload: dict[str, Any]) -> str:
    explicit = _clean(
        payload.get("event_id")
        or payload.get("message_id")
        or payload.get("webhook_event_id")
        or payload.get("botconversa_event_id")
    )
    if explicit:
        return explicit

    stable = {
        "subscriber_id": payload.get("subscriber_id"),
        "telefone": payload.get("telefone"),
        "tipo_evento": payload.get("tipo_evento"),
        "fluxo_origem": payload.get("fluxo_origem"),
        "mensagem": payload.get("mensagem"),
        "campos": payload.get("campos"),
    }
    raw = _json_dumps(stable)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _now_sql(conn) -> str:
    return "NOW()" if is_postgres(conn) else "CURRENT_TIMESTAMP"


def _new_id() -> str:
    return str(uuid.uuid4())


def register_event(conn, payload: dict[str, Any], classification: Classification) -> tuple[str, bool]:
    idempotency_key = build_idempotency_key(payload)
    existing = fetch_one(conn, "SELECT id FROM event_logs WHERE idempotency_key = ?", (idempotency_key,))
    if existing:
        return str(existing["id"]), True

    event_id = _new_id()
    payload_value = payload if is_postgres(conn) else _json_dumps(payload)
    execute(conn, f"""
        INSERT INTO event_logs (
            id, provider, event_type, idempotency_key, external_id, payload, status, criado_em
        ) VALUES (?, 'botconversa', ?, ?, ?, ?, 'recebido', {_now_sql(conn)})
    """, (
        event_id,
        classification.intencao,
        idempotency_key,
        str(payload.get("subscriber_id") or payload.get("telefone") or ""),
        json.dumps(payload_value, ensure_ascii=False) if is_postgres(conn) else payload_value,
    ))
    return event_id, False


def ensure_person(conn, payload: dict[str, Any], classification: Classification) -> str | None:
    phone = payload.get("telefone") or ""
    nome = payload.get("nome") or "Pessoa sem nome"
    pessoa_tipo = "visitante" if classification.intencao == "visitante" else "outro"

    if phone:
        existing = fetch_one(conn, """
            SELECT pessoa_id FROM pessoa_contatos
            WHERE canal = 'whatsapp' AND valor = ?
        """, (phone,))
        if existing:
            return str(existing["pessoa_id"])

    pessoa_id = _new_id()
    execute(conn, f"""
        INSERT INTO pessoas (id, nome_completo, nome_preferido, tipo, criado_em, atualizado_em)
        VALUES (?, ?, ?, ?, {_now_sql(conn)}, {_now_sql(conn)})
    """, (pessoa_id, nome, nome.split()[0] if nome else None, pessoa_tipo))

    if phone:
        execute(conn, f"""
            INSERT INTO pessoa_contatos (id, pessoa_id, canal, valor, principal, criado_em, atualizado_em)
            VALUES (?, ?, 'whatsapp', ?, ?, {_now_sql(conn)}, {_now_sql(conn)})
        """, (_new_id(), pessoa_id, phone, True if is_postgres(conn) else 1))

    return pessoa_id


def create_inbox(conn, payload: dict[str, Any], classification: Classification, event_id: str, pessoa_id: str | None) -> str:
    inbox_id = _new_id()
    campos = payload.get("campos") or {}
    campos_value = campos if is_postgres(conn) else _json_dumps(campos)
    execute(conn, f"""
        INSERT INTO inbox_pastoral (
            id, event_log_id, pessoa_id, subscriber_id, nome, telefone, origem,
            fluxo_origem, tipo_evento, papel_responsavel, intencao, status,
            nivel_urgencia, prioridade, mensagem, resumo, campos, criado_em, atualizado_em
        ) VALUES (?, ?, ?, ?, ?, ?, 'BotConversa', ?, ?, ?, ?, 'Novo', ?, ?, ?, ?, ?, {_now_sql(conn)}, {_now_sql(conn)})
    """, (
        inbox_id,
        event_id,
        pessoa_id,
        payload.get("subscriber_id"),
        payload.get("nome"),
        payload.get("telefone"),
        payload.get("fluxo_origem"),
        payload.get("tipo_evento"),
        classification.papel,
        classification.intencao,
        classification.nivel_urgencia,
        classification.prioridade,
        payload.get("mensagem"),
        payload.get("resumo") or payload.get("resumo_ia") or payload.get("mensagem"),
        json.dumps(campos_value, ensure_ascii=False) if is_postgres(conn) else campos_value,
    ))
    return inbox_id


def _field(payload: dict[str, Any], *names: str) -> Any:
    campos = payload.get("campos") or {}
    for name in names:
        if payload.get(name) not in (None, ""):
            return payload.get(name)
        if isinstance(campos, dict) and campos.get(name) not in (None, ""):
            return campos.get(name)
    return None


def _int_field(payload: dict[str, Any], *names: str, default: int = 0) -> int:
    value = _field(payload, *names)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def create_task(
    conn,
    *,
    inbox_id: str,
    pessoa_id: str | None,
    titulo: str,
    tipo: str,
    responsavel: str,
    prioridade: int,
    prazo_para: datetime | None,
    payload: dict[str, Any],
) -> str:
    task_id = _new_id()
    payload_value = payload if is_postgres(conn) else _json_dumps(payload)
    execute(conn, f"""
        INSERT INTO tarefas_pastorais (
            id, inbox_id, pessoa_id, titulo, tipo, responsavel, status,
            prioridade, prazo_para, payload, criado_em, atualizado_em
        ) VALUES (?, ?, ?, ?, ?, ?, 'Pendente', ?, ?, ?, {_now_sql(conn)}, {_now_sql(conn)})
    """, (
        task_id,
        inbox_id,
        pessoa_id,
        titulo,
        tipo,
        responsavel,
        prioridade,
        prazo_para.isoformat() if prazo_para else None,
        json.dumps(payload_value, ensure_ascii=False) if is_postgres(conn) else payload_value,
    ))
    return task_id


def handle_visitante(conn, payload: dict[str, Any], inbox_id: str, pessoa_id: str | None) -> list[str]:
    today = date.today().isoformat()
    execute(conn, f"""
        INSERT INTO consolidacao_visitantes (
            data_visita, visitante_nome, visitante_whatsapp, consolidador_nome,
            contato_24h, feedback, status, criado_em
        ) VALUES (?, ?, ?, ?, ?, ?, 'Pendente', {_now_sql(conn)})
    """, (
        _field(payload, "data_visita") or today,
        payload.get("nome") or "Visitante sem nome",
        payload.get("telefone"),
        _field(payload, "consolidador_nome") or "A definir",
        False if is_postgres(conn) else 0,
        payload.get("mensagem") or payload.get("resumo") or "",
    ))

    prazo = datetime.now(timezone.utc) + timedelta(hours=24)
    task_id = create_task(
        conn,
        inbox_id=inbox_id,
        pessoa_id=pessoa_id,
        titulo=f"Contato de consolidação 24h: {payload.get('nome')}",
        tipo="followup_visitante_24h",
        responsavel="Caleb",
        prioridade=2,
        prazo_para=prazo,
        payload=payload,
    )
    return [task_id]


def handle_relatorio_celula(conn, payload: dict[str, Any]) -> list[str]:
    missing = []
    for field_name in ("nome_celula", "lider_nome", "presenca_membros"):
        if _field(payload, field_name) in (None, ""):
            missing.append(field_name)
    if missing:
        return missing

    rede = _field(payload, "rede") or "Outro"
    if not is_postgres(conn) and rede == "Outro":
        rede = "Jovens"

    execute(conn, f"""
        INSERT INTO relatorios_celulas (
            data_relatorio, nome_celula, lider_nome, presenca_membros,
            visitantes, decisoes_fe, rede, criado_em
        ) VALUES (?, ?, ?, ?, ?, ?, ?, {_now_sql(conn)})
    """, (
        _field(payload, "data_relatorio") or date.today().isoformat(),
        _field(payload, "nome_celula"),
        _field(payload, "lider_nome"),
        _int_field(payload, "presenca_membros"),
        _int_field(payload, "visitantes"),
        _int_field(payload, "decisoes_fe"),
        rede,
    ))
    return []


def mark_event_processed(conn, event_id: str, result: dict[str, Any]) -> None:
    result_value = result if is_postgres(conn) else _json_dumps(result)
    execute(conn, f"""
        UPDATE event_logs
        SET status = 'processado', resultado = ?, processado_em = {_now_sql(conn)}
        WHERE id = ?
    """, (json.dumps(result_value, ensure_ascii=False) if is_postgres(conn) else result_value, event_id))


def response_message(classification: Classification, missing: list[str]) -> str:
    if missing:
        return "Recebi, mas faltam dados para concluir o registro: " + ", ".join(missing) + "."
    if classification.intencao == "visitante":
        return "Visitante registrado. A consolidação 24h foi aberta para acompanhamento."
    if classification.intencao == "relatorio_celula":
        return "Relatório de célula registrado com sucesso."
    if classification.intencao in ("aconselhamento", "humano_necessario"):
        return "Atendimento registrado e encaminhado para acompanhamento humano."
    if classification.intencao == "pedido_oracao":
        return "Pedido registrado para acompanhamento pastoral."
    return "Registro recebido pela Central Hermes 2.0."


def process_botconversa_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_payload(payload)
    classification = classify(normalized)

    conn = get_connection()
    try:
        ensure_sqlite_schema(conn)
        event_id, duplicate = register_event(conn, normalized, classification)
        if duplicate:
            return {
                "status": "ok",
                "duplicate": True,
                "event_log_id": event_id,
                "intencao": classification.intencao,
                "papel_responsavel": classification.papel,
                "resposta": "Evento já processado anteriormente.",
            }

        pessoa_id = ensure_person(conn, normalized, classification)
        inbox_id = create_inbox(conn, normalized, classification, event_id, pessoa_id)
        tarefas: list[str] = []
        missing: list[str] = []

        if classification.intencao == "visitante":
            tarefas.extend(handle_visitante(conn, normalized, inbox_id, pessoa_id))
        elif classification.intencao == "relatorio_celula":
            missing = handle_relatorio_celula(conn, normalized)
            if missing:
                tarefas.append(create_task(
                    conn,
                    inbox_id=inbox_id,
                    pessoa_id=pessoa_id,
                    titulo="Completar relatório de célula",
                    tipo="dados_pendentes_relatorio_celula",
                    responsavel="Caleb",
                    prioridade=3,
                    prazo_para=datetime.now(timezone.utc) + timedelta(hours=12),
                    payload={"missing": missing, "payload": normalized},
                ))
        elif classification.intencao in ("pedido_oracao", "aconselhamento", "humano_necessario", "celula_g12", "agenda", "conteudo", "foco"):
            tarefas.append(create_task(
                conn,
                inbox_id=inbox_id,
                pessoa_id=pessoa_id,
                titulo=f"{classification.papel}: tratar {classification.intencao}",
                tipo=classification.intencao,
                responsavel=classification.papel,
                prioridade=classification.prioridade,
                prazo_para=datetime.now(timezone.utc) + timedelta(hours=24 if classification.intencao != "humano_necessario" else 2),
                payload=normalized,
            ))

        result = {
            "status": "ok",
            "version": "2.0",
            "duplicate": False,
            "event_log_id": event_id,
            "inbox_id": inbox_id,
            "pessoa_id": pessoa_id,
            "intencao": classification.intencao,
            "papel_responsavel": classification.papel,
            "nivel_urgencia": classification.nivel_urgencia,
            "prioridade": classification.prioridade,
            "tarefas_criadas": tarefas,
            "dados_faltando": missing,
            "resposta": response_message(classification, missing),
        }
        mark_event_processed(conn, event_id, result)
        conn.commit()
        return result
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
