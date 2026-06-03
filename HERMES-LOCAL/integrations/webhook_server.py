import json
import re
import sqlite3
import sys
import logging
from datetime import datetime
from pathlib import Path
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
import uvicorn

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

DB_PATH = PROJECT_ROOT / "database" / "pastoral.db"


def _raw_external_id(payload: dict) -> str | None:
    subscriber_id = payload.get("subscriber_id")
    if subscriber_id and not str(subscriber_id).strip().startswith("{{"):
        return str(subscriber_id)
    telefone = payload.get("telefone")
    if telefone and not str(telefone).strip().startswith("{{"):
        return "".join(ch for ch in str(telefone) if ch.isdigit()) or None
    return None

# Mapeamentos de chaves do bloco IA para colunas do SQLite
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
    """Carrega as configurações mapeadas do BotConversa a partir do SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT chave, valor FROM botconversa_config")
    config = {row[0]: row[1] for row in cursor.fetchall() if row[1]}
    conn.close()
    return config


def log_sync_action(acao: str, entidade_tipo: str, entidade_id: str, payload: dict, status: str, resultado: str):
    """Registra uma ação de sincronização na tabela botconversa_sync_log."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO botconversa_sync_log (acao, entidade_tipo, entidade_id, payload, status, resultado, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (acao, entidade_tipo, entidade_id, json.dumps(payload, ensure_ascii=False), status, resultado)
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.error(f"Erro ao salvar log de sincronização no SQLite: {exc}")


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


def buscar_ou_criar_membro(conn, telefone: str, nome: str, subscriber_id: int) -> int:
    """Busca o membro por ID ou telefone flexível. Se não existir, cria."""
    cursor = conn.cursor()
    tel_digits = "".join(ch for ch in str(telefone) if ch.isdigit())
    
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


def verificar_cadastro_completo(conn, membro_id: int) -> bool:
    """Verifica se os campos obrigatórios mínimos de Membro estão preenchidos."""
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
        
    # Verifica se algum campo está vazio ou nulo
    for val in row:
        if val is None:
            return False
        val_str = str(val).strip().lower()
        if not val_str or val_str in ("nulo", "none", "null", ""):
            return False
            
    return True


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
    
    # 1. Carrega as configurações do BotConversa do SQLite
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

    # Combina dados do payload JSON com os dados extraídos da IA (priorizando payload estruturado se válido)
    dados_totais = {}
    for pay_key, ia_key in map_payload_keys.items():
        val = payload.get(pay_key)
        if val is not None:
            val_str = str(val).strip()
            # Ignora variáveis brutas do BotConversa como "{{Bairro}}"
            if val_str and not val_str.startswith("{{") and not val_str.endswith("}}"):
                dados_totais[ia_key] = val_str

    for k, v in dados_ia.items():
        if k not in dados_totais or not dados_totais[k]:
            dados_totais[k] = v
    
    conn = sqlite3.connect(DB_PATH)
    membro_id = buscar_ou_criar_membro(conn, telefone, nome, subscriber_id)
    cursor = conn.cursor()
    
    data_atual = datetime.now().strftime("%Y-%m-%d")
    
    # Se o status do bloco for 'humano', interrompe atualizações e solicita atendimento
    if status_bloco == "humano":
        conn.close()
        logger.info(f"Status do bloco cadastral para {nome} é 'humano'. Solicitando atendimento humano.")
        
        # Aplica etiqueta Humano Necessário
        if config.get("tag_humano_necessario"):
            try:
                client.add_tag(subscriber_id, int(config["tag_humano_necessario"]))
            except BotConversaError as exc:
                logger.warning(f"Erro ao aplicar tag Humano Necessário: {exc}")
                
        # Abre conversa humana no painel
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
    updates_db = []
    params_db = []
    
    # Lista de chamadas API a serem feitas para sincronizar campos e tags no BotConversa
    api_calls_log = []
    
    if status_bloco == "sem_alteracao":
        logger.info(f"Membro {nome} confirmou cadastro sem alteração.")
        # Marca como Completo pois os dados continuam válidos e completos
        updates_db.append("status_cadastro = 'Completo'")
        updates_db.append("ultima_atualizacao_cadastral = ?")
        params_db.append(data_atual)
        
        # Atualiza nome e telefone se fornecidos no payload
        if nome and not str(nome).startswith("{{"):
            updates_db.append("nome_completo = ?")
            params_db.append(str(nome).strip())
        if telefone and not str(telefone).startswith("{{"):
            tel_digits = "".join(ch for ch in str(telefone) if ch.isdigit())
            if tel_digits:
                updates_db.append("telefone = ?")
                params_db.append(tel_digits)

        # Executa atualização no SQLite local
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
                
        # Aplica tags correspondentes
        tags_to_add = ["tag_atualizacao_cadastral", "tag_cadastro_completo", "tag_atualizacao_confirmada_sem_alteracao"]
        tags_to_remove = ["tag_atualizacao_pendente", "tag_cadastro_incompleto", "tag_atualizacao_recusada"]
        
        for key in tags_to_add:
            if config.get(key):
                try:
                    client.add_tag(subscriber_id, int(config[key]))
                except BotConversaError as exc:
                    logger.warning(f"Erro ao adicionar tag {key}: {exc}")
                    
        for key in tags_to_remove:
            if config.get(key):
                try:
                    client.remove_tag(subscriber_id, int(config[key]))
                except BotConversaError as exc:
                    logger.warning(f"Erro ao remover tag {key}: {exc}")
                    
        # Reinscreve nas sequências de 6M e Anual
        sequences_to_add = ["sequence_revisao_cadastral_6m", "sequence_recadastro_anual"]
        for key in sequences_to_add:
            if config.get(key):
                try:
                    client.add_to_sequence(subscriber_id, int(config[key]))
                except BotConversaError as exc:
                    logger.warning(f"Erro ao inscrever na sequência {key}: {exc}")
                    
        status_final = "Completo"
    else:
        # Status 'atualizado' ou 'incompleto'. Processa campos individualmente
        for chave_ia, valor in dados_totais.items():
            if chave_ia in MAP_CAMPOS_DB and valor:
                col = MAP_CAMPOS_DB[chave_ia]
                updates_db.append(f"{col} = ?")
                params_db.append(valor)
                
                # Envia atualização para o BotConversa
                config_key = MAP_CAMPOS_BOTCONVERSA_CONFIG_KEY[chave_ia]
                if config.get(config_key):
                    try:
                        client.set_custom_field(subscriber_id, int(config[config_key]), valor)
                        api_calls_log.append(f"Campo {chave_ia} atualizado no BotConversa para '{valor}'")
                    except BotConversaError as exc:
                        logger.warning(f"Erro ao atualizar campo {chave_ia} na API BotConversa: {exc}")

        # Atualiza nome e telefone se fornecidos no payload
        if nome and not str(nome).startswith("{{"):
            updates_db.append("nome_completo = ?")
            params_db.append(str(nome).strip())
        if telefone and not str(telefone).startswith("{{"):
            tel_digits = "".join(ch for ch in str(telefone) if ch.isdigit())
            if tel_digits:
                updates_db.append("telefone = ?")
                params_db.append(tel_digits)
                        
        # Sempre atualiza a data de última alteração
        updates_db.append("ultima_atualizacao_cadastral = ?")
        params_db.append(data_atual)
        if config.get("field_ultima_atualizacao"):
            try:
                client.set_custom_field(subscriber_id, int(config["field_ultima_atualizacao"]), data_atual)
            except BotConversaError as exc:
                logger.warning(f"Erro ao salvar Ultima_Atualiz_Cadas na API: {exc}")
                
        # Salva o resumo da interação IA no campo Resumo_Atend_IA do BotConversa
        resumo_texto = dados_totais.get("resumo") or payload.get("resumo") or "Atualização via Rute Cadastro"
        if config.get("field_resumo_atendimento_ia"):
            try:
                client.set_custom_field(subscriber_id, int(config["field_resumo_atendimento_ia"]), resumo_texto)
            except BotConversaError as exc:
                logger.warning(f"Erro ao salvar resumo_ia no BotConversa: {exc}")
                
        # Atualiza o banco de dados antes da checagem
        if updates_db:
            updates_db.append("atualizado_em = CURRENT_TIMESTAMP")
            sql = f"UPDATE membros SET {', '.join(updates_db)} WHERE id = ?"
            cursor.execute(sql, params_db + [membro_id])
            conn.commit()
            
        # 4. Verifica se o cadastro agora está completo
        cadastro_completo = verificar_cadastro_completo(conn, membro_id)
        status_final = "Completo" if cadastro_completo else "Incompleto"
        
        # Atualiza status final local
        cursor.execute("UPDATE membros SET status_cadastro = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?", (status_final, membro_id))
        conn.commit()
        
        # Sincroniza status e tags finais no BotConversa
        if config.get("field_status_cadastro"):
            try:
                client.set_custom_field(subscriber_id, int(config["field_status_cadastro"]), status_final)
            except BotConversaError as exc:
                logger.warning(f"Erro ao salvar Status_Cadastro na API: {exc}")
                
        if cadastro_completo:
            tags_to_add = ["tag_cadastro_completo", "tag_atualizacao_cadastral"]
            tags_to_remove = ["tag_cadastro_incompleto", "tag_atualizacao_pendente", "tag_atualizacao_recusada"]
        else:
            tags_to_add = ["tag_cadastro_incompleto"]
            tags_to_remove = ["tag_cadastro_completo"]
            
        for key in tags_to_add:
            if config.get(key):
                try:
                    client.add_tag(subscriber_id, int(config[key]))
                except BotConversaError as exc:
                    logger.warning(f"Erro ao adicionar tag {key}: {exc}")
                    
        for key in tags_to_remove:
            if config.get(key):
                try:
                    client.remove_tag(subscriber_id, int(config[key]))
                except BotConversaError as exc:
                    logger.warning(f"Erro ao remover tag {key}: {exc}")
                    
        # Se estiver completo, inscreve nas sequências 6M e Anual
        if cadastro_completo:
            sequences_to_add = ["sequence_revisao_cadastral_6m", "sequence_recadastro_anual"]
            for key in sequences_to_add:
                if config.get(key):
                    try:
                        client.add_to_sequence(subscriber_id, int(config[key]))
                    except BotConversaError as exc:
                        logger.warning(f"Erro ao inscrever na sequência {key}: {exc}")
                        
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
        logger.info("Supabase não configurado; seguindo apenas com SQLite local.")
    except SupabaseRequestError as exc:
        logger.warning(f"Falha ao registrar evento bruto no Supabase: {exc}")

    try:
        resultado = await processar_atualizacao_cadastral(payload)
        try:
            update_webhook_event_status(supabase_event_id, "sucesso", json.dumps(resultado, ensure_ascii=False))
        except (SupabaseConfigError, SupabaseRequestError) as exc:
            logger.warning(f"Falha ao atualizar status do evento Supabase: {exc}")
        return JSONResponse(resultado)
    except Exception as exc:
        logger.error(f"Erro durante processamento do webhook: {exc}", exc_info=True)
        try:
            update_webhook_event_status(supabase_event_id, "erro", str(exc))
        except (SupabaseConfigError, SupabaseRequestError) as supa_exc:
            logger.warning(f"Falha ao atualizar erro do evento Supabase: {supa_exc}")
        log_sync_action(
            acao="webhook_recebido",
            entidade_tipo="erro",
            entidade_id=str(payload.get("subscriber_id", "0")),
            payload=payload,
            status="Erro",
            resultado=str(exc)
        )
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)


async def health_endpoint(request):
    return JSONResponse({
        "status": "ok",
        "service": "hermes-webhook",
        "supabase_configured": is_supabase_configured(),
    })


# Rotas da Starlette
routes = [
    Route("/health", endpoint=health_endpoint, methods=["GET"]),
    Route("/webhook_atualizacao_cadastral", endpoint=webhook_endpoint, methods=["POST"]),
]

app = Starlette(debug=True, routes=routes)


if __name__ == "__main__":
    logger.info("Iniciando servidor de Webhook Hermes local na porta 5050...")
    uvicorn.run(app, host="0.0.0.0", port=5050, log_level="info")
