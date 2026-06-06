import json
import re
import sqlite3
import sys
import logging
import uuid
import os
import time
from datetime import datetime
from pathlib import Path
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
import uvicorn
import psycopg2

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("hermes-webhook")

# Ajuste do path para imports corretos
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from integrations.botconversa_client import BotConversaClient, BotConversaError
from integrations.supabase_client import (
    SupabaseConfigError,
    SupabaseRequestError,
    is_supabase_configured,
    register_webhook_event,
    update_webhook_event_status,
)
from hermes_v2.processor import process_botconversa_payload

DB_PATH = PROJECT_ROOT / "database" / "pastoral.db"
ENV_PATH = PROJECT_ROOT / ".env"


def load_env() -> dict[str, str]:
    values = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip()
    return values


def get_db_connection():
    env_vars = load_env()
    db_url = env_vars.get("SUPABASE_DB_URL")
    if db_url and "SUA_SENHA_AQUI" not in db_url:
        try:
            return psycopg2.connect(db_url)
        except Exception as e:
            logger.error(f"Erro ao conectar no Postgres do Supabase: {e}. Fazendo fallback para SQLite.")
    return sqlite3.connect(DB_PATH)


def execute_sql(conn, query: str, params=()):
    is_pg = not isinstance(conn, sqlite3.Connection)
    if is_pg:
        query = query.replace("?", "%s")
    else:
        query = query.replace("%s", "?")
    
    cursor = conn.cursor()
    cursor.execute(query, params)
    return cursor


def _raw_external_id(payload: dict) -> str | None:
    subscriber_id = payload.get("subscriber_id")
    if subscriber_id and not str(subscriber_id).strip().startswith("{{"):
        return str(subscriber_id)
    telefone = payload.get("telefone")
    if telefone and not str(telefone).strip().startswith("{{"):
        return "".join(ch for ch in str(telefone) if ch.isdigit()) or None
    return None

# Mapeamentos de chaves do bloco IA para colunas do SQLite / Postgres
MAP_CAMPOS_DB = {
    "Bairro": "bairro_cidade",
    "Tempo_Igreja": "tempo_igreja",
    "Lider_Celula": "lider_celula",
    "Celula_Atual": "celula_atual",
    "G12_Pastoral": "g12_pastoral",
    "Fez_Encontro": "fez_encontro",
    "Universidade_Vida": "universidade_vida",
    "Capacitacao_Destino": "capacitacao_destino",
    "Ministerios": "ministerios",
    "Interesse_Ministerio": "interesse_ministerio",
    "Feedback_Melhorias": "feedback_melhorias",
    "Feedback_falta": "feedback_falta",
    "Data Nascimento": "data_nascimento",
    "Data_Nascimento": "data_nascimento",
    "Data_Conversao": "data_conversao",
}

# Mapeamentos de chaves do bloco IA para chaves de configuração do BotConversa (tabela botconversa_config)
MAP_CAMPOS_BOTCONVERSA_CONFIG_KEY = {
    "Bairro": "field_bairro",
    "Tempo_Igreja": "field_tempo_igreja",
    "Lider_Celula": "field_lider_celula",
    "Celula_Atual": "field_celula_atual",
    "G12_Pastoral": "field_g12_pastoral",
    "Fez_Encontro": "field_fez_encontro",
    "Universidade_Vida": "field_universidade_vida",
    "Capacitacao_Destino": "field_capacitacao_destino",
    "Ministerios": "field_ministerios",
    "Interesse_Ministerio": "field_interesse_ministerio",
    "Feedback_Melhorias": "field_feedback_melhorias",
    "Feedback_falta": "field_feedback_falta",
    "Data Nascimento": "field_data_nascimento",
    "Data_Nascimento": "field_data_nascimento",
    "Data_Conversao": "field_data_conversao",
}


def load_config() -> dict[str, str]:
    """Carrega as configurações mapeadas do BotConversa."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    is_pg = not isinstance(conn, sqlite3.Connection)
    table = "public.botconversa_config" if is_pg else "botconversa_config"
    
    cursor.execute(f"SELECT chave, valor FROM {table}")
    config = {row[0]: row[1] for row in cursor.fetchall() if row[1]}
    conn.close()
    return config


def log_sync_action(acao: str, entidade_tipo: str, entidade_id: str, payload: dict, status: str, resultado: str):
    """Registra uma ação de sincronização."""
    try:
        conn = get_db_connection()
        log_sync_action_conn(conn, acao, entidade_tipo, entidade_id, payload, status, resultado)
        conn.close()
    except Exception as exc:
        logger.error(f"Erro ao salvar log de sincronização: {exc}")


def log_sync_action_conn(conn, acao: str, entidade_tipo: str, entidade_id: str, payload: dict, status: str, resultado: str):
    cursor = conn.cursor()
    is_pg = not isinstance(conn, sqlite3.Connection)
    
    if is_pg:
        status_norm = str(status).strip().lower()
        if status_norm not in ("sucesso", "erro", "pendente"):
            status_norm = "pendente"
            
        cursor.execute(
            """
            INSERT INTO public.integration_logs (integracao, acao, entidade_tipo, entidade_id, payload, status, resultado, criado_em)
            VALUES ('botconversa', %s, %s, %s, %s, %s, %s, NOW())
            """,
            (acao, entidade_tipo, entidade_id, json.dumps(payload, ensure_ascii=False), status_norm, resultado)
        )
    else:
        cursor.execute(
            """
            INSERT INTO botconversa_sync_log (acao, entidade_tipo, entidade_id, payload, status, resultado, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (acao, entidade_tipo, entidade_id, json.dumps(payload, ensure_ascii=False), status, resultado)
        )
    conn.commit()


def extrair_bloco_cadastral(resumo_ia: str) -> dict[str, str]:
    """Extrai os dados de chave-valor contidos na tag [ATUALIZACAO_CADASTRAL]."""
    if not resumo_ia:
        return {}
    match = re.search(r"\[ATUALIZACAO_CADASTRAL\](.*?)\[/ATUALIZACAO_CADASTRAL\]", resumo_ia, re.DOTALL | re.IGNORECASE)
    if not match:
        return {}
    
    conteudo = match.group(1).strip()
    dados = {}
    for line in conteudo.splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        key, val = line.split("=", 1)
        dados[key.strip()] = val.strip()
    return dados


def normalizar_telefone(tel: str | None) -> str:
    if not tel:
        return ""
    return "".join(ch for ch in str(tel) if ch.isdigit())


def normalizar_data(dt_str: str | None) -> str | None:
    if not dt_str:
        return None
    dt_str = str(dt_str).strip()
    if not dt_str or dt_str.lower() in ("none", "null", "nulo"):
        return None
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})", dt_str)
    if match:
        return match.group(0)
    return None


def buscar_ou_criar_membro_pg(conn, telefone: str, nome: str, subscriber_id: int) -> str:
    cursor = conn.cursor()
    tel_digits = normalizar_telefone(telefone)
    
    # 1. Busca por botconversa_subscriber_id
    cursor.execute("SELECT id FROM public.membros WHERE botconversa_subscriber_id = %s", (subscriber_id,))
    row = cursor.fetchone()
    if row:
        return row[0]
        
    # 2. Busca por telefone flexível nos contatos
    if tel_digits:
        suffix = tel_digits[-9:]
        cursor.execute(
            """
            SELECT m.id, p.nome_completo, m.botconversa_subscriber_id, p.id
            FROM public.pessoa_contatos pc
            JOIN public.pessoas p ON pc.pessoa_id = p.id
            JOIN public.membros m ON m.pessoa_id = p.id
            WHERE pc.canal = 'whatsapp' AND pc.valor LIKE %s
            """,
            (f"%{suffix}",)
        )
        row = cursor.fetchone()
        if row:
            membro_uuid = row[0]
            pessoa_uuid = row[3]
            if not row[2] or row[2] != subscriber_id:
                cursor.execute(
                    "UPDATE public.membros SET botconversa_subscriber_id = %s, atualizado_em = NOW() WHERE id = %s",
                    (subscriber_id, membro_uuid)
                )
                conn.commit()
                logger.info(f"Membro '{row[1]}' vinculado ao subscriber_id {subscriber_id}")
            return membro_uuid
            
    # 3. Se não existe, cria a Pessoa, o Contato e o Membro
    pessoa_uuid = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO public.pessoas (id, nome_completo, tipo, criado_em, atualizado_em)
        VALUES (%s, %s, 'membro', NOW(), NOW())
        """,
        (pessoa_uuid, nome)
    )
    
    if tel_digits:
        cursor.execute(
            """
            INSERT INTO public.pessoa_contatos (id, pessoa_id, canal, valor, principal, verificado, criado_em, atualizado_em)
            VALUES (%s, %s, 'whatsapp', %s, true, false, NOW(), NOW())
            """,
            (str(uuid.uuid4()), pessoa_uuid, tel_digits)
        )
        
    membro_uuid = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO public.membros (id, pessoa_id, botconversa_subscriber_id, status_cadastro, criado_em, atualizado_em)
        VALUES (%s, %s, %s, 'incompleto', NOW(), NOW())
        """,
        (membro_uuid, pessoa_uuid, subscriber_id)
    )
    conn.commit()
    logger.info(f"Novo membro '{nome}' inserido no Supabase (UUID: {membro_uuid})")
    return membro_uuid


def buscar_ou_criar_membro(conn, telefone: str, nome: str, subscriber_id: int):
    """Busca o membro por ID ou telefone flexível. Se não existir, cria."""
    if not isinstance(conn, sqlite3.Connection):
        return buscar_ou_criar_membro_pg(conn, telefone, nome, subscriber_id)
        
    cursor = conn.cursor()
    tel_digits = normalizar_telefone(telefone)
    
    # 1. Busca por botconversa_subscriber_id
    cursor.execute("SELECT id FROM membros WHERE botconversa_subscriber_id = ?", (subscriber_id,))
    row = cursor.fetchone()
    if row:
        return row[0]
        
    # 2. Busca por telefone flexível (últimos 9 dígitos)
    if tel_digits:
        suffix = tel_digits[-9:]
        cursor.execute("SELECT id, nome_completo, botconversa_subscriber_id FROM membros WHERE telefone LIKE ?", (f"%{suffix}",))
        row = cursor.fetchone()
        if row:
            membro_id = row[0]
            # Atualiza o subscriber_id se estivesse vazio ou diferente
            if not row[2] or row[2] != subscriber_id:
                cursor.execute(
                    "UPDATE membros SET botconversa_subscriber_id = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
                    (subscriber_id, membro_id)
                )
                conn.commit()
                logger.info(f"Membro '{row[1]}' vinculado ao subscriber_id {subscriber_id}")
            return membro_id
            
    # 3. Criação de novo membro (incompleto)
    cursor.execute(
        """
        INSERT INTO membros (nome_completo, telefone, botconversa_subscriber_id, status_cadastro, criado_em, atualizado_em)
        VALUES (?, ?, ?, 'Incompleto', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (nome, tel_digits, subscriber_id)
    )
    conn.commit()
    logger.info(f"Novo membro '{nome}' inserido a partir do webhook (ID local: {cursor.lastrowid})")
    return cursor.lastrowid


def verificar_cadastro_completo_pg(conn, membro_id: str) -> bool:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT p.nome_completo, pc.valor as telefone, m.tempo_igreja, m.lider_celula, m.celula_atual, m.g12_pastoral, m.fez_encontro, m.universidade_vida, m.capacitacao_destino
        FROM public.membros m
        JOIN public.pessoas p ON m.pessoa_id = p.id
        LEFT JOIN public.pessoa_contatos pc ON pc.pessoa_id = p.id AND pc.canal = 'whatsapp'
        WHERE m.id = %s
        """,
        (membro_id,)
    )
    row = cursor.fetchone()
    if not row:
        return False
    # Verifica se algum campo está vazio ou nulo
    for val in row:
        if val is None:
            return False
        val_str = str(val).strip().lower()
        if not val_str or val_str in ("nulo", "none", "null", ""):
            return False
    return True


def verificar_cadastro_completo(conn, membro_id) -> bool:
    """Verifica se os campos obrigatórios mínimos de Membro estão preenchidos."""
    if not isinstance(conn, sqlite3.Connection):
        return verificar_cadastro_completo_pg(conn, str(membro_id))
        
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT nome_completo, telefone, bairro_cidade, tempo_igreja, lider_celula, celula_atual, g12_pastoral, fez_encontro, universidade_vida, capacitacao_destino
        FROM membros
        WHERE id = ?
        """,
        (membro_id,)
    )
    row = cursor.fetchone()
    if not row:
        return False
        
    for val in row:
        if val is None:
            return False
        val_str = str(val).strip().lower()
        if not val_str or val_str in ("nulo", "none", "null", ""):
            return False
            
    return True


def normalizar_tipo_atendimento(value: str | None) -> str:
    value_norm = str(value or "").strip().lower()
    mapping = {
        "cadastro": "Atualizacao Cadastro",
        "atualizacao_cadastro": "Atualizacao Cadastro",
        "atualização cadastro": "Atualizacao Cadastro",
        "atualizacao cadastro": "Atualizacao Cadastro",
        "visitante": "Informacao Visitante",
        "informacao_visitante": "Informacao Visitante",
        "informação visitante": "Informacao Visitante",
        "oracao": "Pedido Oracao",
        "oração": "Pedido Oracao",
        "pedido_oracao": "Pedido Oracao",
        "pedido oração": "Pedido Oracao",
        "aconselhamento": "Pedido Aconselhamento",
        "pedido_aconselhamento": "Pedido Aconselhamento",
        "celula": "Entrar Celula",
        "célula": "Entrar Celula",
        "entrar_celula": "Entrar Celula",
        "humano": "Humano Necessario",
        "humano_necessario": "Humano Necessario",
    }
    return mapping.get(value_norm, "Outro")


def normalizar_urgencia(value: str | None) -> str:
    value_norm = str(value or "").strip().lower()
    mapping = {
        "baixa": "Baixa",
        "normal": "Normal",
        "media": "Normal",
        "média": "Normal",
        "alta": "Alta",
        "urgente": "Urgente",
    }
    return mapping.get(value_norm, "Normal")


def criar_atendimento_rute_pg(conn, payload: dict) -> dict:
    cursor = conn.cursor()
    subscriber_id = payload.get("subscriber_id")
    telefone = payload.get("telefone") or payload.get("phone")
    nome = payload.get("nome") or payload.get("name") or "Pessoa sem nome"
    tipo = normalizar_tipo_atendimento(payload.get("tipo_solicitacao") or payload.get("intencao") or payload.get("tipo"))
    urgencia = normalizar_urgencia(payload.get("nivel_urgencia") or payload.get("urgencia"))
    resumo = payload.get("resumo") or payload.get("resumo_ia") or payload.get("mensagem") or ""

    membro_id = None
    tel_digits = normalizar_telefone(telefone)
    
    if subscriber_id and not str(subscriber_id).strip().startswith("{{"):
        cursor.execute("SELECT id FROM public.membros WHERE botconversa_subscriber_id = %s", (int(subscriber_id),))
        row = cursor.fetchone()
        membro_id = row[0] if row else None

    if membro_id is None and tel_digits:
        suffix = tel_digits[-9:]
        cursor.execute(
            """
            SELECT m.id 
            FROM public.pessoa_contatos pc
            JOIN public.membros m ON m.pessoa_id = pc.pessoa_id
            WHERE pc.canal = 'whatsapp' AND pc.valor LIKE %s
            """,
            (f"%{suffix}",)
        )
        row = cursor.fetchone()
        membro_id = row[0] if row else None

    cursor.execute(
        """
        INSERT INTO public.atendimentos_rute (
            pessoa_nome, telefone, tipo_solicitacao, origem, nivel_urgencia,
            status, resumo, membro_id, botconversa_subscriber_id, criado_em, atualizado_em
        )
        VALUES (%s, %s, %s, 'BotConversa', %s, 'Novo', %s, %s, %s, NOW(), NOW())
        RETURNING id
        """,
        (
            str(nome).strip(),
            tel_digits or None,
            tipo,
            urgencia,
            str(resumo).strip(),
            membro_id,
            int(subscriber_id) if subscriber_id and not str(subscriber_id).strip().startswith("{{") else None,
        ),
    )
    atendimento_id = cursor.fetchone()[0]
    conn.commit()

    log_sync_action_conn(
        conn,
        acao="atendimento_rute_criado",
        entidade_tipo="atendimento_rute",
        entidade_id=str(atendimento_id),
        payload=payload,
        status="Sucesso",
        resultado=f"Atendimento criado: {tipo} / {urgencia}",
    )
    return {"status": "ok", "atendimento_id": atendimento_id, "tipo_solicitacao": tipo, "nivel_urgencia": urgencia}


def criar_atendimento_rute(payload: dict) -> dict:
    conn = get_db_connection()
    is_pg = not isinstance(conn, sqlite3.Connection)
    
    if is_pg:
        try:
            res = criar_atendimento_rute_pg(conn, payload)
            conn.close()
            return res
        except Exception as e:
            conn.close()
            raise e
            
    cursor = conn.cursor()
    subscriber_id = payload.get("subscriber_id")
    telefone = payload.get("telefone") or payload.get("phone")
    nome = payload.get("nome") or payload.get("name") or "Pessoa sem nome"
    tipo = normalizar_tipo_atendimento(payload.get("tipo_solicitacao") or payload.get("intencao") or payload.get("tipo"))
    urgencia = normalizar_urgencia(payload.get("nivel_urgencia") or payload.get("urgencia"))
    resumo = payload.get("resumo") or payload.get("resumo_ia") or payload.get("mensagem") or ""
    
    membro_id = None
    tel_digits = normalizar_telefone(telefone)
    if subscriber_id and not str(subscriber_id).strip().startswith("{{"):
        cursor.execute("SELECT id FROM membros WHERE botconversa_subscriber_id = ?", (int(subscriber_id),))
        row = cursor.fetchone()
        membro_id = row[0] if row else None

    if membro_id is None and tel_digits:
        cursor.execute("SELECT id FROM membros WHERE telefone LIKE ?", (f"%{tel_digits[-9:]}",))
        row = cursor.fetchone()
        membro_id = row[0] if row else None

    cursor.execute(
        """
        INSERT INTO atendimentos_rute (
            pessoa_nome, telefone, tipo_solicitacao, origem, nivel_urgencia,
            status, resumo, membro_id, botconversa_subscriber_id, criado_em, atualizado_em
        )
        VALUES (?, ?, ?, 'BotConversa', ?, 'Novo', ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (
            str(nome).strip(),
            tel_digits or None,
            tipo,
            urgencia,
            str(resumo).strip(),
            membro_id,
            int(subscriber_id) if subscriber_id and not str(subscriber_id).strip().startswith("{{") else None,
        ),
    )
    atendimento_id = cursor.lastrowid
    conn.commit()
    conn.close()

    log_sync_action(
        acao="atendimento_rute_criado",
        entidade_tipo="atendimento_rute",
        entidade_id=str(atendimento_id),
        payload=payload,
        status="Sucesso",
        resultado=f"Atendimento criado: {tipo} / {urgencia}",
    )
    return {"status": "ok", "atendimento_id": atendimento_id, "tipo_solicitacao": tipo, "nivel_urgencia": urgencia}


async def processar_atualizacao_cadastral(payload: dict) -> dict:
    subscriber_id = payload.get("subscriber_id")
    telefone = payload.get("telefone")
    nome = payload.get("nome")
    resumo_ia = payload.get("resumo_ia") or payload.get("resumo") or ""
    
    # Tratamento amigável para chamadas de teste vazias ou com variáveis brutas do BotConversa
    is_test_raw = (
        not subscriber_id or 
        not telefone or 
        str(subscriber_id).strip() in ("", "{{subscriber_id}}") or 
        str(telefone).strip() in ("", "{{telefone}}") or
        str(subscriber_id).strip().startswith("{{") or
        str(telefone).strip().startswith("{{")
    )
    
    if is_test_raw:
        logger.info("Requisição de teste do BotConversa detectada (dados vazios ou variáveis cruas). Retornando sucesso simulado.")
        return {"status": "ok", "message": "Conexão com o Hermes Webhook estabelecida com sucesso! (Modo Teste)"}
        
    subscriber_id = int(subscriber_id)
    logger.info(f"Iniciando processamento de webhook para {nome} (Tel: {telefone}, ID: {subscriber_id})")
    
    # 1. Carrega as configurações do BotConversa
    config = load_config()
    client = BotConversaClient()
    
    # 2. Extrai dados estruturados do resumo
    dados_ia = extrair_bloco_cadastral(resumo_ia)
    status_bloco = dados_ia.get("status", "atualizado").strip().lower()

    # Mapeamento de chaves vindas direto no payload JSON para chaves correspondentes da IA
    map_payload_keys = {
        "bairro": "Bairro",
        "lider_celula": "Lider_Celula",
        "celula_atual": "Celula_Atual",
        "g12_pastoral": "G12_Pastoral",
        "tempo_igreja": "Tempo_Igreja",
        "fez_encontro": "Fez_Encontro",
        "universidade_vida": "Universidade_Vida",
        "capacitacao_destino": "Capacitacao_Destino",
        "interesse_ministerio": "Interesse_Ministerio",
        "feedback_melhorias": "Feedback_Melhorias",
        "feedback_falta": "Feedback_falta",
        "ministerios": "Ministerios",
        "data_nascimento": "Data_Nascimento",
        "data_conversao": "Data_Conversao",
    }

    # Combina dados do payload JSON com os dados extraídos da IA
    dados_totais = {}
    for pay_key, ia_key in map_payload_keys.items():
        val = payload.get(pay_key)
        if val is not None:
            val_str = str(val).strip()
            if val_str and not val_str.startswith("{{") and not val_str.endswith("}}"):
                dados_totais[ia_key] = val_str

    for k, v in dados_ia.items():
        if k not in dados_totais or not dados_totais[k]:
            dados_totais[k] = v
    
    conn = get_db_connection()
    membro_id = buscar_ou_criar_membro(conn, telefone, nome, subscriber_id)
    cursor = conn.cursor()
    
    is_pg = not isinstance(conn, sqlite3.Connection)
    data_atual = datetime.now().strftime("%Y-%m-%d")
    
    # Se o status do bloco for 'humano', interrompe atualizações e solicita atendimento
    if status_bloco == "humano":
        conn.close()
        logger.info(f"Status do bloco cadastral para {nome} é 'humano'. Solicitando atendimento humano.")
        
        if config.get("tag_humano_necessario"):
            try:
                client.add_tag(subscriber_id, int(config["tag_humano_necessario"]))
            except BotConversaError as exc:
                logger.warning(f"Erro ao aplicar tag Humano Necessário: {exc}")
                
        try:
            client.change_conversation_status(subscriber_id, open_conversation=True)
        except BotConversaError as exc:
            logger.warning(f"Erro ao abrir atendimento humano na API: {exc}")
            
        log_sync_action(
            acao="webhook_recebido",
            entidade_tipo="membro",
            entidade_id=str(membro_id),
            payload=payload,
            status="Sucesso",
            resultado="Status 'humano' processado: tag Humano Necessário aplicada e chat aberto."
        )
        return {"status": "ok", "message": "Atendimento humano acionado conforme bloco.", "membro_id": membro_id}
        
    # 3. Processamento de campos
    api_calls_log = []
    status_final = "Completo"
    
    if status_bloco == "sem_alteracao":
        logger.info(f"Membro {nome} confirmou cadastro sem alteração.")
        status_final = "Completo"
        
        if is_pg:
            cursor.execute("SELECT pessoa_id FROM public.membros WHERE id = %s", (membro_id,))
            pessoa_uuid = cursor.fetchone()[0]
            
            # Atualiza última alteração
            cursor.execute(
                "UPDATE public.membros SET status_cadastro = 'completo'::public.status_cadastro, ultima_atualizacao_cadastral = %s, atualizado_em = NOW() WHERE id = %s",
                (normalizar_data(data_atual), membro_id)
            )
            
            # Nome e Telefone
            if nome and not str(nome).startswith("{{"):
                cursor.execute("UPDATE public.pessoas SET nome_completo = %s, atualizado_em = NOW() WHERE id = %s", (str(nome).strip(), pessoa_uuid))
            if telefone and not str(telefone).startswith("{{"):
                tel_dig = normalizar_telefone(telefone)
                if tel_dig:
                    cursor.execute(
                        """
                        INSERT INTO public.pessoa_contatos (id, pessoa_id, canal, valor, principal)
                        VALUES (%s, %s, 'whatsapp', %s, true)
                        ON CONFLICT (canal, valor) DO UPDATE SET valor = EXCLUDED.valor, atualizado_em = NOW()
                        """,
                        (str(uuid.uuid4()), pessoa_uuid, tel_dig)
                    )
            conn.commit()
        else:
            updates_db = ["status_cadastro = 'Completo'", "ultima_atualizacao_cadastral = ?"]
            params_db = [data_atual]
            if nome and not str(nome).startswith("{{"):
                updates_db.append("nome_completo = ?")
                params_db.append(str(nome).strip())
            if telefone and not str(telefone).startswith("{{"):
                tel_digits = normalizar_telefone(telefone)
                if tel_digits:
                    updates_db.append("telefone = ?")
                    params_db.append(tel_digits)
            updates_db.append("atualizado_em = CURRENT_TIMESTAMP")
            sql = f"UPDATE membros SET {', '.join(updates_db)} WHERE id = ?"
            cursor.execute(sql, params_db + [membro_id])
            conn.commit()
            
        # Sincroniza campos no BotConversa
        if config.get("field_status_cadastro"):
            try:
                client.set_custom_field(subscriber_id, int(config["field_status_cadastro"]), "Completo")
            except BotConversaError as exc:
                logger.warning(f"Erro ao salvar Status_Cadastro: {exc}")
                
        if config.get("field_ultima_atualizacao"):
            try:
                client.set_custom_field(subscriber_id, int(config["field_ultima_atualizacao"]), data_atual)
            except BotConversaError as exc:
                logger.warning(f"Erro ao salvar Ultima_Atualiz_Cadas: {exc}")
                
        # Aplica tags e sequências
        tags_to_add = ["tag_atualizacao_cadastral", "tag_cadastro_completo", "tag_atualizacao_confirmada_sem_alteracao"]
        tags_to_remove = ["tag_atualizacao_pendente", "tag_cadastro_incompleto", "tag_atualizacao_recusada"]
        for key in tags_to_add:
            if config.get(key):
                try: client.add_tag(subscriber_id, int(config[key]))
                except BotConversaError as exc: logger.warning(f"Erro ao adicionar tag {key}: {exc}")
        for key in tags_to_remove:
            if config.get(key):
                try: client.remove_tag(subscriber_id, int(config[key]))
                except BotConversaError as exc: logger.warning(f"Erro ao remover tag {key}: {exc}")
        
        sequences_to_add = ["sequence_recadastro_anual"]
        for key in sequences_to_add:
            if config.get(key):
                try: client.add_to_sequence(subscriber_id, int(config[key]))
                except BotConversaError as exc: logger.warning(f"Erro ao inscrever na sequência {key}: {exc}")
                
    else:
        # Status 'atualizado' ou 'incompleto'
        if is_pg:
            cursor.execute("SELECT pessoa_id FROM public.membros WHERE id = %s", (membro_id,))
            pessoa_uuid = cursor.fetchone()[0]
            
            updates_pessoas = []
            params_pessoas = []
            
            updates_membros = []
            params_membros = []
            bairro_atualizar = None
            
            telefone_atualizar = None
            
            for chave_ia, valor in dados_totais.items():
                if chave_ia in MAP_CAMPOS_DB and valor:
                    col = MAP_CAMPOS_DB[chave_ia]
                    if col == "data_nascimento":
                        updates_pessoas.append("data_nascimento = %s")
                        params_pessoas.append(normalizar_data(valor))
                    elif col == "data_conversao":
                        updates_membros.append("data_conversao = %s")
                        params_membros.append(normalizar_data(valor))
                    elif col == "bairro_cidade":
                        bairro_atualizar = str(valor).strip()
                    else:
                        updates_membros.append(f"{col} = %s")
                        params_membros.append(valor)
                        
                    config_key = MAP_CAMPOS_BOTCONVERSA_CONFIG_KEY[chave_ia]
                    if config.get(config_key):
                        try:
                            client.set_custom_field(subscriber_id, int(config[config_key]), valor)
                            api_calls_log.append(f"Campo {chave_ia} atualizado no BotConversa para '{valor}'")
                        except BotConversaError as exc:
                            logger.warning(f"Erro ao atualizar campo {chave_ia}: {exc}")
            
            if nome and not str(nome).startswith("{{"):
                updates_pessoas.append("nome_completo = %s")
                params_pessoas.append(str(nome).strip())
            if telefone and not str(telefone).startswith("{{"):
                tel_dig = normalizar_telefone(telefone)
                if tel_dig:
                    telefone_atualizar = tel_dig
            
            updates_membros.append("ultima_atualizacao_cadastral = %s")
            params_membros.append(normalizar_data(data_atual))
            
            if updates_pessoas:
                cursor.execute(f"UPDATE public.pessoas SET {', '.join(updates_pessoas)}, atualizado_em = NOW() WHERE id = %s", params_pessoas + [pessoa_uuid])
            if telefone_atualizar:
                cursor.execute(
                    """
                    INSERT INTO public.pessoa_contatos (id, pessoa_id, canal, valor, principal)
                    VALUES (%s, %s, 'whatsapp', %s, true)
                    ON CONFLICT (canal, valor) DO UPDATE SET valor = EXCLUDED.valor, atualizado_em = NOW()
                    """,
                    (str(uuid.uuid4()), pessoa_uuid, telefone_atualizar)
                )
            if bairro_atualizar:
                cursor.execute(
                    """
                    UPDATE public.enderecos
                    SET bairro = %s,
                        atualizado_em = NOW()
                    WHERE pessoa_id = %s
                    """,
                    (bairro_atualizar, pessoa_uuid)
                )
                if cursor.rowcount == 0:
                    cursor.execute(
                        """
                        INSERT INTO public.enderecos (id, pessoa_id, bairro)
                        VALUES (%s, %s, %s)
                        """,
                        (str(uuid.uuid4()), pessoa_uuid, bairro_atualizar)
                    )
            if updates_membros:
                cursor.execute(f"UPDATE public.membros SET {', '.join(updates_membros)}, atualizado_em = NOW() WHERE id = %s", params_membros + [membro_id])
                
            conn.commit()
        else:
            updates_db = []
            params_db = []
            for chave_ia, valor in dados_totais.items():
                if chave_ia in MAP_CAMPOS_DB and valor:
                    col = MAP_CAMPOS_DB[chave_ia]
                    updates_db.append(f"{col} = ?")
                    params_db.append(valor)
                    
                    config_key = MAP_CAMPOS_BOTCONVERSA_CONFIG_KEY[chave_ia]
                    if config.get(config_key):
                        try:
                            client.set_custom_field(subscriber_id, int(config[config_key]), valor)
                            api_calls_log.append(f"Campo {chave_ia} atualizado: '{valor}'")
                        except BotConversaError as exc:
                            logger.warning(f"Erro ao atualizar campo {chave_ia}: {exc}")

            if nome and not str(nome).startswith("{{"):
                updates_db.append("nome_completo = ?")
                params_db.append(str(nome).strip())
            if telefone and not str(telefone).startswith("{{"):
                tel_digits = normalizar_telefone(telefone)
                if tel_digits:
                    updates_db.append("telefone = ?")
                    params_db.append(tel_digits)
            updates_db.append("ultima_atualizacao_cadastral = ?")
            params_db.append(data_atual)
            
            if updates_db:
                updates_db.append("atualizado_em = CURRENT_TIMESTAMP")
                sql = f"UPDATE membros SET {', '.join(updates_db)} WHERE id = ?"
                cursor.execute(sql, params_db + [membro_id])
                conn.commit()
        
        # Envia última atualização e resumo
        if config.get("field_ultima_atualizacao"):
            try: client.set_custom_field(subscriber_id, int(config["field_ultima_atualizacao"]), data_atual)
            except BotConversaError as exc: logger.warning(f"Erro ao salvar Ultima_Atualiz_Cadas na API: {exc}")
            
        resumo_texto = dados_totais.get("resumo") or payload.get("resumo") or "Atualização via Rute Cadastro"
        if config.get("field_resumo_atendimento_ia"):
            try: client.set_custom_field(subscriber_id, int(config["field_resumo_atendimento_ia"]), resumo_texto)
            except BotConversaError as exc: logger.warning(f"Erro ao salvar resumo_ia no BotConversa: {exc}")

        # 4. Verifica se está completo
        cadastro_completo = verificar_cadastro_completo(conn, membro_id)
        status_final = "Completo" if cadastro_completo else "Incompleto"
        status_final_enum = status_final.lower()
        
        if is_pg:
            cursor.execute("UPDATE public.membros SET status_cadastro = %s::public.status_cadastro, atualizado_em = NOW() WHERE id = %s", (status_final_enum, membro_id))
            conn.commit()
        else:
            cursor.execute("UPDATE membros SET status_cadastro = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?", (status_final, membro_id))
            conn.commit()
            
        if config.get("field_status_cadastro"):
            try: client.set_custom_field(subscriber_id, int(config["field_status_cadastro"]), status_final)
            except BotConversaError as exc: logger.warning(f"Erro ao salvar Status_Cadastro na API: {exc}")
            
        if cadastro_completo:
            tags_to_add = ["tag_cadastro_completo", "tag_atualizacao_cadastral"]
            tags_to_remove = ["tag_cadastro_incompleto", "tag_atualizacao_pendente", "tag_atualizacao_recusada"]
        else:
            tags_to_add = ["tag_cadastro_incompleto"]
            tags_to_remove = ["tag_cadastro_completo"]
            
        for key in tags_to_add:
            if config.get(key):
                try: client.add_tag(subscriber_id, int(config[key]))
                except BotConversaError as exc: logger.warning(f"Erro ao adicionar tag {key}: {exc}")
        for key in tags_to_remove:
            if config.get(key):
                try: client.remove_tag(subscriber_id, int(config[key]))
                except BotConversaError as exc: logger.warning(f"Erro ao remover tag {key}: {exc}")
                
        if cadastro_completo:
            sequences_to_add = ["sequence_recadastro_anual"]
            for key in sequences_to_add:
                if config.get(key):
                    try: client.add_to_sequence(subscriber_id, int(config[key]))
                    except BotConversaError as exc: logger.warning(f"Erro ao inscrever na sequência {key}: {exc}")

    conn.close()
    
    msg_resultado = f"Sincronização concluída. Status final: {status_final}."
    log_sync_action(
        acao="webhook_recebido",
        entidade_tipo="membro",
        entidade_id=str(membro_id),
        payload=payload,
        status="Sucesso",
        resultado=f"{msg_resultado} Mudanças Totais: {json.dumps(dados_totais, ensure_ascii=False)}"
    )
    
    logger.info(f"Processamento concluído com sucesso para ID {membro_id}.")
    return {"status": "ok", "membro_id": membro_id, "dados_extraidos": dados_totais}


# Endpoint Starlette
async def webhook_endpoint(request):
    supabase_event_id = None
    payload = {}
    try:
        payload = await request.json()
    except Exception as exc:
        logger.error(f"Payload inválido: {exc}")
        return JSONResponse({"status": "error", "message": "JSON inválido."}, status_code=400)

    try:
        supabase_event_id = register_webhook_event(
            provider="botconversa",
            event_type="atualizacao_cadastral",
            external_id=_raw_external_id(payload),
            payload=payload,
        )
        if supabase_event_id:
            logger.info(f"Evento bruto registrado no Supabase: {supabase_event_id}")
    except SupabaseConfigError:
        logger.info("Supabase REST Client não configurado; seguindo apenas com fluxos locais/Postgres direto.")
    except SupabaseRequestError as exc:
        logger.warning(f"Falha ao registrar evento bruto no Supabase REST: {exc}")

    try:
        resultado = await processar_atualizacao_cadastral(payload)
        try:
            update_webhook_event_status(supabase_event_id, "sucesso", json.dumps(resultado, ensure_ascii=False))
        except (SupabaseConfigError, SupabaseRequestError) as exc:
            logger.warning(f"Falha ao atualizar status do evento Supabase REST: {exc}")
        return JSONResponse(resultado)
    except Exception as exc:
        logger.error(f"Erro durante processamento do webhook: {exc}", exc_info=True)
        try:
            update_webhook_event_status(supabase_event_id, "erro", str(exc))
        except (SupabaseConfigError, SupabaseRequestError) as supa_exc:
            logger.warning(f"Falha ao atualizar erro do evento Supabase REST: {supa_exc}")
        log_sync_action(
            acao="webhook_recebido",
            entidade_tipo="erro",
            entidade_id=str(payload.get("subscriber_id", "0")),
            payload=payload,
            status="Erro",
            resultado=str(exc)
        )
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)


async def atendimento_rute_endpoint(request):
    payload = {}
    try:
        payload = await request.json()
    except Exception as exc:
        logger.error(f"Payload inválido no atendimento Rute: {exc}")
        return JSONResponse({"status": "error", "message": "JSON inválido."}, status_code=400)

    try:
        resultado = criar_atendimento_rute(payload)
        return JSONResponse(resultado)
    except Exception as exc:
        logger.error(f"Erro ao criar atendimento Rute: {exc}", exc_info=True)
        log_sync_action(
            acao="atendimento_rute_criado",
            entidade_tipo="erro",
            entidade_id=str(payload.get("subscriber_id", "0")),
            payload=payload,
            status="Erro",
            resultado=str(exc),
        )
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)


def criar_visitante_pg(conn, payload: dict) -> dict:
    nome = payload.get("nome") or payload.get("visitante_nome") or "Visitante sem nome"
    telefone = payload.get("telefone") or payload.get("visitante_whatsapp") or payload.get("phone") or ""
    tel_digits = normalizar_telefone(telefone)
    
    data_visita = payload.get("data_visita") or datetime.now().strftime("%Y-%m-%d")
    consolidador = payload.get("consolidador_nome") or payload.get("consolidador") or "Luciane"
    status = payload.get("status") or "Pendente"
    
    feedback = payload.get("feedback") or payload.get("resumo") or payload.get("resumo_ia") or ""
    bairro = payload.get("bairro")
    como_conheceu = payload.get("como_conheceu")
    interesse_celula = payload.get("interesse_celula")
    
    infos = []
    if bairro:
        infos.append(f"Bairro: {bairro}")
    if como_conheceu:
        infos.append(f"Como conheceu: {como_conheceu}")
    if interesse_celula:
        infos.append(f"Interesse em célula: {interesse_celula}")
        
    if infos:
        extra_feedback = " | ".join(infos)
        feedback = f"{feedback} ({extra_feedback})" if feedback else extra_feedback

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO public.consolidacao_visitantes (
            data_visita,
            visitante_nome,
            visitante_whatsapp,
            consolidador_nome,
            contato_24h,
            feedback,
            status,
            criado_em
        )
        VALUES (%s, %s, %s, %s, false, %s, %s, NOW())
        RETURNING id
        """,
        (data_visita, str(nome).strip(), tel_digits or None, str(consolidador).strip(), str(feedback).strip(), status)
    )
    visitante_id = cursor.fetchone()[0]
    conn.commit()

    log_sync_action_conn(
        conn,
        acao="visitante_criado",
        entidade_tipo="visitante",
        entidade_id=str(visitante_id),
        payload=payload,
        status="Sucesso",
        resultado=f"Visitante registrado no Supabase: {nome} (Tel: {tel_digits})"
    )
    return {"status": "ok", "visitante_id": visitante_id, "nome": nome, "status_consolidacao": status}


def criar_visitante(payload: dict) -> dict:
    conn = get_db_connection()
    is_pg = not isinstance(conn, sqlite3.Connection)
    
    if is_pg:
        try:
            res = criar_visitante_pg(conn, payload)
            conn.close()
            return res
        except Exception as e:
            conn.close()
            raise e
            
    nome = payload.get("nome") or payload.get("visitante_nome") or "Visitante sem nome"
    telefone = payload.get("telefone") or payload.get("visitante_whatsapp") or payload.get("phone") or ""
    tel_digits = normalizar_telefone(telefone)
    
    data_visita = payload.get("data_visita") or datetime.now().strftime("%Y-%m-%d")
    consolidador = payload.get("consolidador_nome") or payload.get("consolidador") or "Luciane"
    status = payload.get("status") or "Pendente"
    
    feedback = payload.get("feedback") or payload.get("resumo") or payload.get("resumo_ia") or ""
    bairro = payload.get("bairro")
    como_conheceu = payload.get("como_conheceu")
    interesse_celula = payload.get("interesse_celula")
    
    infos = []
    if bairro:
        infos.append(f"Bairro: {bairro}")
    if como_conheceu:
        infos.append(f"Como conheceu: {como_conheceu}")
    if interesse_celula:
        infos.append(f"Interesse em célula: {interesse_celula}")
        
    if infos:
        extra_feedback = " | ".join(infos)
        feedback = f"{feedback} ({extra_feedback})" if feedback else extra_feedback

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO consolidacao_visitantes (
            data_visita,
            visitante_nome,
            visitante_whatsapp,
            consolidador_nome,
            contato_24h,
            feedback,
            status,
            criado_em
        )
        VALUES (?, ?, ?, ?, 0, ?, ?, CURRENT_TIMESTAMP)
        """,
        (data_visita, str(nome).strip(), tel_digits or None, str(consolidador).strip(), str(feedback).strip(), status)
    )
    visitante_id = cursor.lastrowid
    conn.commit()
    conn.close()

    log_sync_action(
        acao="visitante_criado",
        entidade_tipo="visitante",
        entidade_id=str(visitante_id),
        payload=payload,
        status="Sucesso",
        resultado=f"Visitante registrado: {nome} (Tel: {tel_digits})"
    )
    return {"status": "ok", "visitante_id": visitante_id, "nome": nome, "status_consolidacao": status}


def normalizar_rede(value: str | None) -> str | None:
    if not value:
        return None
    val_norm = str(value).strip().lower()
    mapping = {
        "jovens": "Jovens",
        "jovem": "Jovens",
        "casais": "Casais",
        "casal": "Casais",
        "homens": "Homens",
        "homem": "Homens",
        "mulheres": "Mulheres",
        "mulher": "Mulheres"
    }
    return mapping.get(val_norm, None)


def criar_relatorio_celula(payload: dict) -> dict:
    nome_celula = payload.get("nome_celula") or payload.get("celula")
    lider_nome = payload.get("lider_nome") or payload.get("lider")
    
    if not nome_celula or not lider_nome:
        raise ValueError("Nome da célula e nome do líder são obrigatórios.")
        
    data_relatorio = payload.get("data_relatorio") or payload.get("data") or datetime.now().strftime("%Y-%m-%d")
    
    try:
        presenca = int(payload.get("presenca_membros") or payload.get("presenca") or 0)
        visitantes = int(payload.get("visitantes") or 0)
        decisoes = int(payload.get("decisoes_fe") or payload.get("decisoes") or 0)
    except ValueError:
        raise ValueError("Valores de presença, visitantes e decisões devem ser numéricos.")
        
    rede = normalizar_rede(payload.get("rede"))
    if rede not in ("Jovens", "Casais", "Homens", "Mulheres", None):
        raise ValueError("Rede inválida. Deve ser Jovens, Casais, Homens ou Mulheres.")

    conn = get_db_connection()
    cursor = conn.cursor()
    
    is_pg = not isinstance(conn, sqlite3.Connection)
    table = "public.relatorios_celulas" if is_pg else "relatorios_celulas"
    rede_norm = normalizar_rede(payload.get("rede")) or "Outro" if is_pg else normalizar_rede(payload.get("rede"))
    
    if is_pg:
        # No Postgres o ID é UUID e geramos localmente
        relatorio_id = str(uuid.uuid4())
        cursor.execute(
            f"""
            INSERT INTO {table} (
                id, data_relatorio, nome_celula, lider_nome, presenca_membros, visitantes, decisoes_fe, rede, criado_em
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """,
            (relatorio_id, normalizar_data(data_relatorio), str(nome_celula).strip(), str(lider_nome).strip(), presenca, visitantes, decisoes, rede_norm)
        )
    else:
        cursor.execute(
            f"""
            INSERT INTO {table} (
                data_relatorio, nome_celula, lider_nome, presenca_membros, visitantes, decisoes_fe, rede, criado_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (data_relatorio, str(nome_celula).strip(), str(lider_nome).strip(), presenca, visitantes, decisoes, rede)
        )
        relatorio_id = cursor.lastrowid
        
    conn.commit()
    conn.close()

    log_sync_action(
        acao="relatorio_celula_criado",
        entidade_tipo="relatorio_celula",
        entidade_id=str(relatorio_id),
        payload=payload,
        status="Sucesso",
        resultado=f"Relatório de Célula registrado: {nome_celula} (Líder: {lider_nome})"
    )
    return {"status": "ok", "relatorio_id": relatorio_id, "nome_celula": nome_celula, "lider_nome": lider_nome}


def atualizar_contato_visitante_pg(conn, payload: dict) -> dict:
    visitante_id = payload.get("visitante_id")
    feedback = payload.get("feedback", "")
    status = payload.get("status", "Contatado")
    consolidador = payload.get("consolidador_nome")
    
    cursor = conn.cursor()
    
    if consolidador:
        cursor.execute(
            """
            UPDATE public.consolidacao_visitantes
            SET contato_24h = true,
                data_contato = CURRENT_DATE,
                feedback = %s,
                status = %s,
                consolidador_nome = %s
            WHERE id = %s
            """,
            (feedback, status, consolidador, visitante_id)
        )
    else:
        cursor.execute(
            """
            UPDATE public.consolidacao_visitantes
            SET contato_24h = true,
                data_contato = CURRENT_DATE,
                feedback = %s,
                status = %s
            WHERE id = %s
            """,
            (feedback, status, visitante_id)
        )
        
    conn.commit()
    
    log_sync_action_conn(
        conn,
        acao="visitante_contatado",
        entidade_tipo="visitante",
        entidade_id=str(visitante_id),
        payload=payload,
        status="Sucesso",
        resultado=f"Visitante {visitante_id} atualizado para {status} no Supabase"
    )
    return {"status": "ok", "visitante_id": visitante_id, "status_consolidacao": status}


def atualizar_contato_visitante(payload: dict) -> dict:
    conn = get_db_connection()
    is_pg = not isinstance(conn, sqlite3.Connection)
    
    if is_pg:
        try:
            res = atualizar_contato_visitante_pg(conn, payload)
            conn.close()
            return res
        except Exception as e:
            conn.close()
            raise e
            
    visitante_id = payload.get("visitante_id")
    feedback = payload.get("feedback", "")
    status = payload.get("status", "Contatado")
    consolidador = payload.get("consolidador_nome")
    
    if not visitante_id:
        raise ValueError("visitante_id é obrigatório para atualização")

    cursor = conn.cursor()
    
    if consolidador:
        cursor.execute(
            """
            UPDATE consolidacao_visitantes
            SET contato_24h = 1,
                data_contato = DATE('now'),
                feedback = ?,
                status = ?,
                consolidador_nome = ?
            WHERE id = ?
            """,
            (feedback, status, consolidador, visitante_id)
        )
    else:
        cursor.execute(
            """
            UPDATE consolidacao_visitantes
            SET contato_24h = 1,
                data_contato = DATE('now'),
                feedback = ?,
                status = ?
            WHERE id = ?
            """,
            (feedback, status, visitante_id)
        )
        
    conn.commit()
    conn.close()

    log_sync_action(
        acao="visitante_contatado",
        entidade_tipo="visitante",
        entidade_id=str(visitante_id),
        payload=payload,
        status="Sucesso",
        resultado=f"Visitante {visitante_id} atualizado para {status} no SQLite"
    )
    return {"status": "ok", "visitante_id": visitante_id, "status_consolidacao": status}


async def consolidacao_contato_endpoint(request):
    payload = {}
    try:
        payload = await request.json()
    except Exception as exc:
        logger.error(f"Payload inválido no webhook consolidação contato: {exc}")
        return JSONResponse({"status": "error", "message": "JSON inválido."}, status_code=400)

    try:
        resultado = atualizar_contato_visitante(payload)
        return JSONResponse(resultado)
    except ValueError as exc:
        logger.warning(f"Erro de validação no contato: {exc}")
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=400)
    except Exception as exc:
        logger.error(f"Erro ao atualizar contato de visitante: {exc}", exc_info=True)
        log_sync_action(
            acao="visitante_contatado",
            entidade_tipo="erro",
            entidade_id=str(payload.get("visitante_id", "0")),
            payload=payload,
            status="Erro",
            resultado=str(exc),
        )
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)


async def visitante_endpoint(request):
    payload = {}
    try:
        payload = await request.json()
    except Exception as exc:
        logger.error(f"Payload inválido no webhook visitante: {exc}")
        return JSONResponse({"status": "error", "message": "JSON inválido."}, status_code=400)

    try:
        resultado = criar_visitante(payload)
        return JSONResponse(resultado)
    except Exception as exc:
        logger.error(f"Erro ao criar visitante: {exc}", exc_info=True)
        log_sync_action(
            acao="visitante_criado",
            entidade_tipo="erro",
            entidade_id=str(payload.get("subscriber_id", "0")),
            payload=payload,
            status="Erro",
            resultado=str(exc),
        )
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)


async def g12_celulas_endpoint(request):
    payload = {}
    try:
        payload = await request.json()
    except Exception as exc:
        logger.error(f"Payload inválido no webhook G12/Células: {exc}")
        return JSONResponse({"status": "error", "message": "JSON inválido."}, status_code=400)

    try:
        resultado = criar_relatorio_celula(payload)
        return JSONResponse(resultado)
    except ValueError as exc:
        logger.warning(f"Erro de validação ao criar relatório: {exc}")
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=400)
    except Exception as exc:
        logger.error(f"Erro ao criar relatório de célula: {exc}", exc_info=True)
        log_sync_action(
            acao="relatorio_celula_criado",
            entidade_tipo="erro",
            entidade_id=str(payload.get("subscriber_id", "0")),
            payload=payload,
            status="Erro",
            resultado=str(exc),
        )
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)


async def health_endpoint(request):
    return JSONResponse({
        "status": "ok",
        "service": "hermes-webhook",
        "hermes_v2": "enabled",
        "supabase_configured": is_supabase_configured(),
    })


async def botconversa_v2_endpoint(request):
    """Hermes 2.0 single BotConversa entrypoint.

    Legacy webhooks stay active below while BotConversa flows are migrated one
    by one to this endpoint.
    """
    try:
        payload = await request.json()
    except Exception as exc:
        logger.error(f"Payload inválido no webhook BotConversa v2: {exc}")
        return JSONResponse({"status": "error", "message": "JSON inválido."}, status_code=400)

    try:
        result = process_botconversa_payload(payload)
        logger.info(
            "Hermes v2 processou evento BotConversa: intencao=%s duplicate=%s inbox=%s",
            result.get("intencao"),
            result.get("duplicate"),
            result.get("inbox_id"),
        )
        return JSONResponse(result)
    except Exception as exc:
        logger.error(f"Erro no webhook BotConversa v2: {exc}", exc_info=True)
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)


# ─── NOVOS ENDPOINTS DE MÍDIA ────────────────────────────────────────────────


def processar_evento_midia(payload: dict) -> dict:
    """
    Registra evento de mídia recebida no banco para BI e auditoria.
    Chamado pelo fluxo 00 - Midia Recebida - Rute no BotConversa.
    """
    subscriber_id = payload.get("subscriber_id")
    telefone = normalizar_telefone(payload.get("telefone"))
    nome = payload.get("nome") or "Pessoa sem nome"
    acao = payload.get("acao", "resolvido")
    tipo_midia = payload.get("tipo_midia", "desconhecido")
    ultima_intencao = payload.get("ultima_intencao")
    resumo_ia = payload.get("resumo_ia", "")
    nivel_urgencia = normalizar_urgencia(payload.get("nivel_urgencia") or "Normal")
    ultimo_fluxo = payload.get("ultimo_fluxo_encaminhado")
    status_atendimento = payload.get("status_atendimento")

    # Tratamento amigável para chamadas de teste com variáveis cruas do BotConversa
    is_test_raw = (
        not subscriber_id
        or str(subscriber_id).strip().startswith("{{")
    )
    if is_test_raw:
        logger.info("Requisição de teste do webhook_midia detectada. Retornando sucesso simulado.")
        return {"status": "ok", "message": "Conexão com webhook_midia estabelecida! (Modo Teste)"}

    try:
        subscriber_id = int(subscriber_id)
    except (ValueError, TypeError):
        subscriber_id = None

    conn = get_db_connection()
    cursor = conn.cursor()
    is_pg = not isinstance(conn, sqlite3.Connection)

    if is_pg:
        cursor.execute("""
            INSERT INTO public.eventos_midia (
                subscriber_id, telefone, nome, tipo_midia, acao,
                ultima_intencao, ultimo_fluxo_encaminhado, resumo_ia,
                nivel_urgencia, status_atendimento, criado_em
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            subscriber_id, telefone or None, str(nome).strip(), tipo_midia, acao,
            ultima_intencao, ultimo_fluxo, str(resumo_ia).strip(),
            nivel_urgencia, status_atendimento,
        ))
    else:
        cursor.execute("""
            INSERT INTO eventos_midia (
                subscriber_id, telefone, nome, tipo_midia, acao,
                ultima_intencao, ultimo_fluxo_encaminhado, resumo_ia,
                nivel_urgencia, status_atendimento, criado_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            subscriber_id, telefone or None, str(nome).strip(), tipo_midia, acao,
            ultima_intencao, ultimo_fluxo, str(resumo_ia).strip(),
            nivel_urgencia, status_atendimento,
        ))

    conn.commit()
    conn.close()

    log_sync_action(
        acao="midia_recebida",
        entidade_tipo="evento_midia",
        entidade_id=str(subscriber_id or "0"),
        payload=payload,
        status="Sucesso",
        resultado=f"Mídia {tipo_midia} / ação {acao} registrada para {nome}"
    )

    logger.info(f"Mídia registrada: {nome} enviou {tipo_midia} -> {acao}")
    return {"status": "ok", "acao": acao, "tipo_midia": tipo_midia}


async def midia_endpoint(request):
    """Endpoint para registrar eventos de mídia recebida."""
    payload = {}
    try:
        payload = await request.json()
    except Exception as exc:
        logger.error(f"Payload inválido no webhook mídia: {exc}")
        return JSONResponse({"status": "error", "message": "JSON inválido."}, status_code=400)

    try:
        resultado = processar_evento_midia(payload)
        return JSONResponse(resultado)
    except Exception as exc:
        logger.error(f"Erro ao processar evento de mídia: {exc}", exc_info=True)
        log_sync_action(
            acao="midia_recebida",
            entidade_tipo="erro",
            entidade_id=str(payload.get("subscriber_id", "0")),
            payload=payload,
            status="Erro",
            resultado=str(exc),
        )
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)


async def audio_tts_endpoint(request):
    """
    Endpoint para gerar resposta em áudio (TTS) e enviar via BotConversa.
    Ativado pela tag [RESPOSTA_AUDIO] no fluxo do BotConversa.
    """
    payload = {}
    try:
        payload = await request.json()
    except Exception as exc:
        logger.error(f"Payload inválido no webhook TTS: {exc}")
        return JSONResponse({"status": "error", "message": "JSON inválido."}, status_code=400)

    subscriber_id = payload.get("subscriber_id")
    texto = payload.get("texto_resposta", "").strip()
    voz = payload.get("voz", "elevenlabs")
    nome = payload.get("nome") or "Pessoa sem nome"

    if not texto:
        return JSONResponse({"status": "error", "message": "texto_resposta é obrigatório."}, status_code=400)

    # Chamada de teste do BotConversa
    if not subscriber_id or str(subscriber_id).strip().startswith("{{"):
        logger.info("Requisição de teste do webhook TTS detectada.")
        return JSONResponse({"status": "ok", "message": "Conexão TTS estabelecida (modo teste)"})

    try:
        subscriber_id = int(subscriber_id)
    except (ValueError, TypeError):
        return JSONResponse({"status": "error", "message": "subscriber_id inválido."}, status_code=400)

    try:
        provider = voz if voz in ("elevenlabs", "openai") else "elevenlabs"

        # Tenta gerar áudio com ElevenLabs ou OpenAI TTS
        audio_bytes = None
        tts_error = None

        if provider == "elevenlabs":
            elevenlabs_key = load_env().get("ELEVENLABS_API_KEY", "")
            if elevenlabs_key:
                try:
                    import requests
                    voice_id = load_env().get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
                    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                    headers = {
                        "Accept": "audio/mpeg",
                        "Content-Type": "application/json",
                        "xi-api-key": elevenlabs_key,
                    }
                    data = {
                        "text": texto,
                        "model_id": "eleven_flash_v2_5",
                        "voice_settings": {
                            "stability": 0.5,
                            "similarity_boost": 0.75,
                            "style": 0.2,
                        }
                    }
                    resp = requests.post(url, json=data, headers=headers, timeout=30)
                    resp.raise_for_status()
                    audio_bytes = resp.content
                    logger.info(f"Áudio gerado via ElevenLabs para subscriber {subscriber_id}")
                except Exception as exc:
                    tts_error = str(exc)
                    logger.warning(f"ElevenLabs falhou, tentando fallback OpenAI: {exc}")

        # Fallback: OpenAI TTS se ElevenLabs falhou ou não configurado
        if audio_bytes is None:
            openai_key = load_env().get("OPENAI_API_KEY", "")
            if not openai_key:
                # Sem API configurada, simula sucesso (o BotConversa responderá em texto normal)
                logger.warning("Nenhuma chave de TTS configurada. Resposta será apenas em texto.")
                return JSONResponse({
                    "status": "ok",
                    "provider_used": "none",
                    "message": "TTS não configurado. Responder em texto.",
                    "texto_resposta": texto,
                })

            try:
                import openai as openai_mod
                client = openai_mod.OpenAI(api_key=openai_key)
                response = client.audio.speech.create(
                    model="tts-1",
                    voice="nova",
                    input=texto,
                )
                audio_bytes = response.content
                provider = "openai"
                logger.info(f"Áudio gerado via OpenAI TTS para subscriber {subscriber_id}")
            except Exception as exc:
                logger.error(f"OpenAI TTS também falhou: {exc}")
                return JSONResponse({
                    "status": "error",
                    "message": f"Falha ao gerar áudio: {exc}",
                    "texto_resposta": texto,
                }, status_code=500)

        # Salva arquivo de áudio temporário
        audio_cache_dir = PROJECT_ROOT / "audio_cache"
        audio_cache_dir.mkdir(exist_ok=True)
        audio_filename = f"audio_{subscriber_id}_{int(time.time())}.mp3"
        audio_path = audio_cache_dir / audio_filename
        audio_path.write_bytes(audio_bytes)

        # Envia via BotConversa API
        client = BotConversaClient()
        try:
            message_result = client.send_media(
                subscriber_id=subscriber_id,
                media_type="audio",
                media_value=str(audio_path),
                caption="",
            )
        except BotConversaError as exc:
            logger.warning(f"Erro ao enviar áudio via API BotConversa: {exc}")
            message_result = {"message_id": "erro_envio"}

        # Registra no banco
        conn = get_db_connection()
        cursor = conn.cursor()
        is_pg = not isinstance(conn, sqlite3.Connection)

        duracao_estimada = max(1, len(texto) // 15)

        if is_pg:
            cursor.execute("""
                INSERT INTO public.eventos_audio (
                    subscriber_id, nome, texto_original, provider,
                    duracao_segundos, status, criado_em
                ) VALUES (%s, %s, %s, %s, %s, 'enviado', NOW())
            """, (subscriber_id, str(nome).strip(), texto[:500], provider, duracao_estimada))
        else:
            cursor.execute("""
                INSERT INTO eventos_audio (
                    subscriber_id, nome, texto_original, provider,
                    duracao_segundos, status, criado_em
                ) VALUES (?, ?, ?, ?, ?, 'enviado', CURRENT_TIMESTAMP)
            """, (subscriber_id, str(nome).strip(), texto[:500], provider, duracao_estimada))

        conn.commit()
        conn.close()

        logger.info(f"Áudio de {duracao_estimada}s enviado para subscriber {subscriber_id} via {provider}")

        return JSONResponse({
            "status": "ok",
            "provider_used": provider,
            "audio_file": audio_filename,
            "audio_duration_seconds": duracao_estimada,
        })

    except Exception as exc:
        logger.error(f"Erro no endpoint TTS: {exc}", exc_info=True)
        return JSONResponse({
            "status": "error",
            "message": str(exc),
            "texto_resposta": texto,
        }, status_code=500)


async def documento_endpoint(request):
    """
    Endpoint para processar documentos (PDF, DOCX, XLSX) recebidos no WhatsApp.
    Extrai texto do documento e retorna para o BotConversa continuar o fluxo.
    """
    payload = {}
    try:
        payload = await request.json()
    except Exception as exc:
        logger.error(f"Payload inválido no webhook documento: {exc}")
        return JSONResponse({"status": "error", "message": "JSON inválido."}, status_code=400)

    subscriber_id = payload.get("subscriber_id")
    tipo_documento = payload.get("tipo_documento", "pdf")
    nome = payload.get("nome") or "Pessoa sem nome"
    telefone = payload.get("telefone")

    # Chamada de teste do BotConversa
    if not subscriber_id or str(subscriber_id).strip().startswith("{{"):
        logger.info("Requisição de teste do webhook_documento detectada.")
        return JSONResponse({
            "status": "ok",
            "message": "Conexão com webhook_documento estabelecida! (Modo Teste)",
            "texto_extraido": "[MODO TESTE] Texto extraído do documento apareceria aqui.",
        })

    texto_extraido = ""
    erro = None

    try:
        tipo_doc = str(tipo_documento).lower().strip()
        url_arquivo = payload.get("url_arquivo", "")

        if not url_arquivo:
            texto_extraido = payload.get("mensagem_usuario") or ""
            if not texto_extraido:
                erro = "url_arquivo não fornecida"
        else:
            import requests as req_lib

            if tipo_doc in ("pdf",):
                try:
                    import fitz  # PyMuPDF
                    resp = req_lib.get(url_arquivo, timeout=30)
                    resp.raise_for_status()
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                        tmp.write(resp.content)
                        tmp_path = tmp.name
                    doc = fitz.open(tmp_path)
                    textos_pag = []
                    for page in doc:
                        textos_pag.append(page.get_text())
                    texto_extraido = "\n".join(textos_pag)
                    doc.close()
                    os.unlink(tmp_path)
                except ImportError:
                    erro = "pymupdf não instalado. pip install pymupdf"
                except Exception as exc:
                    erro = f"Erro ao extrair PDF: {exc}"

            elif tipo_doc in ("docx", "doc"):
                try:
                    from docx import Document as DocxDocument
                    resp = req_lib.get(url_arquivo, timeout=30)
                    resp.raise_for_status()
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
                        tmp.write(resp.content)
                        tmp_path = tmp.name
                    doc = DocxDocument(tmp_path)
                    texto_extraido = "\n".join(p.text for p in doc.paragraphs)
                    os.unlink(tmp_path)
                except ImportError:
                    erro = "python-docx não instalado. pip install python-docx"
                except Exception as exc:
                    erro = f"Erro ao extrair DOCX: {exc}"

            elif tipo_doc in ("xlsx", "xls"):
                try:
                    import pandas as pd
                    resp = req_lib.get(url_arquivo, timeout=30)
                    resp.raise_for_status()
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                        tmp.write(resp.content)
                        tmp_path = tmp.name
                    dfs = pd.read_excel(tmp_path, sheet_name=None)
                    textos = []
                    for sheet_name, df in dfs.items():
                        textos.append(f"--- Aba: {sheet_name} ---")
                        textos.append(df.to_string(index=False))
                    texto_extraido = "\n".join(textos)
                    os.unlink(tmp_path)
                except ImportError:
                    erro = "pandas não instalado. pip install pandas openpyxl"
                except Exception as exc:
                    erro = f"Erro ao extrair XLSX: {exc}"
            else:
                erro = f"Tipo de documento não suportado: {tipo_doc}"

        # Limita tamanho do texto extraído
        if texto_extraido and len(texto_extraido) > 50000:
            texto_extraido = texto_extraido[:50000] + "\n\n[... documento truncado por exceder 50000 caracteres]"

        # Registra no banco
        conn = get_db_connection()
        cursor = conn.cursor()
        is_pg = not isinstance(conn, sqlite3.Connection)

        if is_pg:
            cursor.execute("""
                INSERT INTO public.eventos_documento (
                    subscriber_id, nome, telefone, tipo_documento,
                    total_chars, status, erro, criado_em
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                int(subscriber_id) if subscriber_id else None,
                str(nome).strip(),
                telefone or None,
                tipo_doc,
                len(texto_extraido),
                "erro" if erro else "sucesso",
                erro,
            ))
        else:
            cursor.execute("""
                INSERT INTO eventos_documento (
                    subscriber_id, nome, telefone, tipo_documento,
                    total_chars, status, erro, criado_em
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                int(subscriber_id) if subscriber_id else None,
                str(nome).strip(),
                telefone or None,
                tipo_doc,
                len(texto_extraido),
                "erro" if erro else "sucesso",
                erro,
            ))

        conn.commit()
        conn.close()

        if erro:
            logger.warning(f"Documento processado com erro para {nome}: {erro}")
            return JSONResponse({
                "status": "error",
                "message": erro,
                "texto_extraido": f"[Erro ao processar documento: {erro}]",
            }, status_code=422)

        logger.info(f"Documento processado: {nome} enviou {tipo_doc} ({len(texto_extraido)} chars)")

        # Trunca a resposta para evitar payloads gigantes (o BotConversa tem limite)
        texto_resposta = texto_extraido[:15000] if len(texto_extraido) > 15000 else texto_extraido
        if len(texto_extraido) > 15000:
            texto_resposta += "\n\n[... documento truncado para exibição no WhatsApp. Conteúdo completo registrado no banco.]"

        return JSONResponse({
            "status": "ok",
            "texto_extraido": texto_resposta,
            "total_chars": len(texto_extraido),
            "tipo_documento": tipo_doc,
        })

    except Exception as exc:
        logger.error(f"Erro no endpoint documento: {exc}", exc_info=True)
        return JSONResponse({
            "status": "error",
            "message": str(exc),
            "texto_extraido": f"[Erro ao processar documento: {exc}]",
        }, status_code=500)


# Rotas da Starlette
routes = [
    Route("/health", endpoint=health_endpoint, methods=["GET"]),
    Route("/webhook/botconversa", endpoint=botconversa_v2_endpoint, methods=["POST"]),
    Route("/webhook_atualizacao_cadastral", endpoint=webhook_endpoint, methods=["POST"]),
    Route("/webhook_atendimento_rute", endpoint=atendimento_rute_endpoint, methods=["POST"]),
    Route("/webhook_visitante", endpoint=visitante_endpoint, methods=["POST"]),
    Route("/webhook_consolidacao_contato", endpoint=consolidacao_contato_endpoint, methods=["POST"]),
    Route("/webhook_g12_celulas", endpoint=g12_celulas_endpoint, methods=["POST"]),
    # NOVOS ENDPOINTS DE MÍDIA
    Route("/webhook_midia", endpoint=midia_endpoint, methods=["POST"]),
    Route("/webhook_audio_tts", endpoint=audio_tts_endpoint, methods=["POST"]),
    Route("/webhook_documento", endpoint=documento_endpoint, methods=["POST"]),
]

app = Starlette(debug=True, routes=routes)


if __name__ == "__main__":
    logger.info("Iniciando servidor de Webhook Hermes local na porta 5050...")
    uvicorn.run(app, host="0.0.0.0", port=5050, log_level="info")
