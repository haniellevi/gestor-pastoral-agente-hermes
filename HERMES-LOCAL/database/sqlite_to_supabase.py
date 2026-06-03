import sqlite3
import os
import sys
import uuid
import json
import re
from datetime import datetime
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values

# Adiciona a raiz do projeto no path para imports se necessário
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / "database" / "pastoral.db"
ENV_PATH = PROJECT_ROOT / ".env"

def _load_env() -> dict[str, str]:
    values = {}
    if not ENV_PATH.exists():
        return values
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip()
    return values

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
    # Caso data esteja no formato ISO ou date
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})", dt_str)
    if match:
        return match.group(0)
    return None

def normalizar_status_cadastro(status: str | None) -> str:
    if not status:
        return "incompleto"
    status_norm = str(status).strip().lower()
    if status_norm in ("incompleto", "completo", "atualizar", "recusou"):
        return status_norm
    if status_norm == "recusou":
         return "recusou"
    return "incompleto"

def normalizar_status_geral(status: str | None) -> str:
    if not status:
        return "pendente"
    status_norm = str(status).strip().lower()
    mapping = {
        "pendente": "pendente",
        "contatado": "em_andamento",
        "integrado": "concluido",
        "desistiu": "cancelado",
        "em triagem": "em_andamento",
        "encaminhado": "em_andamento",
        "resolvido": "concluido",
        "arquivado": "arquivado",
    }
    return mapping.get(status_norm, "pendente")

def normalizar_rede(rede: str | None) -> str:
    if not rede:
        return "Outro"
    rede_norm = str(rede).strip().lower()
    mapping = {
        "jovens": "Jovens",
        "casais": "Casais",
        "homens": "Homens",
        "mulheres": "Mulheres",
    }
    return mapping.get(rede_norm, "Outro")

def migrate_all():
    env_vars = _load_env()
    db_url = env_vars.get("SUPABASE_DB_URL")
    
    if not db_url or "SUA_SENHA_AQUI" in db_url:
        print("Erro: A variável SUPABASE_DB_URL no arquivo .env está vazia ou contém a senha padrão.")
        print("Por favor, configure a senha real do seu banco de dados no .env antes de rodar a migração.")
        sys.exit(1)
        
    print("Conectando ao banco SQLite local e PostgreSQL remoto do Supabase...")
    sqlite_conn = sqlite3.connect(DB_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()
    
    try:
        pg_conn = psycopg2.connect(db_url)
        pg_cur = pg_conn.cursor()
    except Exception as e:
        print(f"Erro ao conectar ao PostgreSQL do Supabase: {e}")
        sqlite_conn.close()
        sys.exit(1)

    print("Conexões estabelecidas com sucesso! Iniciando migração...")
    
    # Dicionário de mapeamento de IDs de membros locais para UUIDs remotos
    mapeamento_membros = {}
    
    try:
        # ---- 1. CONFIGURAÇÃO DO BOTCONVERSA (botconversa_config) ----
        print("\n[1/10] Migrando botconversa_config...")
        sqlite_cur.execute("SELECT chave, valor, descricao, atualizado_em FROM botconversa_config")
        configs = sqlite_cur.fetchall()
        for cfg in configs:
            pg_cur.execute(
                """
                INSERT INTO public.botconversa_config (chave, valor, descricao, atualizado_em)
                VALUES (%s, %s, %s, COALESCE(%s, NOW()))
                ON CONFLICT (chave) DO UPDATE
                SET valor = EXCLUDED.valor,
                    descricao = EXCLUDED.descricao,
                    atualizado_em = NOW()
                """,
                (cfg["chave"], cfg["valor"], cfg["descricao"], cfg["atualizado_em"])
            )
        print(f"-> {len(configs)} configurações migradas/sincronizadas.")

        # ---- 2. LOGS DE SINCRONIZAÇÃO (botconversa_sync_log -> integration_logs) ----
        print("\n[2/10] Migrando logs de sincronização (botconversa_sync_log)...")
        sqlite_cur.execute("SELECT acao, entidade_tipo, entidade_id, payload, status, resultado, criado_em FROM botconversa_sync_log")
        logs = sqlite_cur.fetchall()
        for log in logs:
            # Normalização de status do integration_log ('sucesso', 'erro', 'pendente')
            status_norm = str(log["status"]).strip().lower()
            if status_norm not in ("sucesso", "erro", "pendente"):
                status_norm = "pendente"
            
            # Tenta ler o payload JSON
            payload_json = None
            if log["payload"]:
                try:
                    payload_json = json.loads(log["payload"])
                except Exception:
                    payload_json = {"raw_text": log["payload"]}
            
            pg_cur.execute(
                """
                INSERT INTO public.integration_logs (integracao, acao, entidade_tipo, entidade_id, payload, status, resultado, criado_em)
                VALUES ('botconversa', %s, %s, %s, %s, %s, %s, COALESCE(%s, NOW()))
                """,
                (
                    log["acao"],
                    log["entidade_tipo"],
                    log["entidade_id"],
                    json.dumps(payload_json) if payload_json else None,
                    status_norm,
                    log["resultado"],
                    log["criado_em"]
                )
            )
        print(f"-> {len(logs)} logs de sincronização migrados.")

        # ---- 3. METAS DIÁRIAS (metas_diarias) ----
        print("\n[3/10] Migrando metas_diarias...")
        sqlite_cur.execute("SELECT data, vitoria_1, vitoria_1_concluida, vitoria_2, vitoria_2_concluida, vitoria_3, vitoria_3_concluida, pontuacao_dia, anotacoes, criado_em FROM metas_diarias")
        metas = sqlite_cur.fetchall()
        for meta in metas:
            pg_cur.execute(
                """
                INSERT INTO public.metas_diarias (data, vitoria_1, vitoria_1_concluida, vitoria_2, vitoria_2_concluida, vitoria_3, vitoria_3_concluida, pontuacao_dia, anotacoes, criado_em)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, COALESCE(%s, NOW()))
                ON CONFLICT (data) DO UPDATE
                SET vitoria_1_concluida = EXCLUDED.vitoria_1_concluida,
                    vitoria_2_concluida = EXCLUDED.vitoria_2_concluida,
                    vitoria_3_concluida = EXCLUDED.vitoria_3_concluida,
                    pontuacao_dia = EXCLUDED.pontuacao_dia,
                    anotacoes = EXCLUDED.anotacoes
                """,
                (
                    normalizar_data(meta["data"]),
                    meta["vitoria_1"],
                    bool(meta["vitoria_1_concluida"]),
                    meta["vitoria_2"],
                    bool(meta["vitoria_2_concluida"]),
                    meta["vitoria_3"],
                    bool(meta["vitoria_3_concluida"]),
                    meta["pontuacao_dia"],
                    meta["anotacoes"],
                    meta["criado_em"]
                )
            )
        print(f"-> {len(metas)} metas diárias migradas.")

        # ---- 4. REGISTRO DE PROCRASTINAÇÃO (registro_procrastinacao) ----
        print("\n[4/10] Migrando registro_procrastinacao...")
        sqlite_cur.execute("SELECT data, tarefa_adiada, distracao, criado_em FROM registro_procrastinacao")
        procs = sqlite_cur.fetchall()
        for proc in procs:
            pg_cur.execute(
                """
                INSERT INTO public.registro_procrastinacao (data, tarefa_adiada, distracao, criado_em)
                VALUES (%s, %s, %s, COALESCE(%s, NOW()))
                """,
                (
                    normalizar_data(proc["data"]),
                    proc["tarefa_adiada"],
                    proc["distracao"],
                    proc["criado_em"]
                )
            )
        print(f"-> {len(procs)} registros de procrastinação migrados.")

        # ---- 5. SUGESTÕES DO BI (sugestoes_bi) ----
        print("\n[5/10] Migrando sugestoes_bi...")
        sqlite_cur.execute("SELECT origem_conversa, metrica_sugerida, justificativa, status, criado_em FROM sugestoes_bi")
        sugs = sqlite_cur.fetchall()
        for sug in sugs:
            # Garante que status esteja entre ('Pendente', 'Implementado', 'Rejeitado')
            status_norm = str(sug["status"]).strip().capitalize()
            if status_norm not in ("Pendente", "Implementado", "Rejeitado"):
                status_norm = "Pendente"
            
            pg_cur.execute(
                """
                INSERT INTO public.sugestoes_bi (origem_conversa, metrica_sugerida, justificativa, status, criado_em)
                VALUES (%s, %s, %s, %s, COALESCE(%s, NOW()))
                """,
                (
                    sug["origem_conversa"],
                    sug["metrica_sugerida"],
                    sug["justificativa"],
                    status_norm,
                    sug["criado_em"]
                )
            )
        print(f"-> {len(sugs)} sugestões de BI migradas.")

        # ---- 6. COMPROMISSOS (compromissos) ----
        print("\n[6/10] Migrando compromissos...")
        sqlite_cur.execute("SELECT titulo, categoria, data_inicio, data_fim, descricao, google_event_id, criado_em FROM compromissos")
        comps = sqlite_cur.fetchall()
        for comp in comps:
            # Trata categoria do compromisso
            cat_norm = str(comp["categoria"]).strip()
            if cat_norm not in ("Aconselhamento", "Culto", "Reuniao Lideranca", "Estudo/Sermao", "Pessoal", "Outros"):
                cat_norm = "Outros"
                
            pg_cur.execute(
                """
                INSERT INTO public.compromissos (id, titulo, categoria, data_inicio, data_fim, descricao, google_event_id, criado_em)
                VALUES (%s, %s, %s, %s, %s, %s, %s, COALESCE(%s, NOW()))
                ON CONFLICT (google_event_id) DO NOTHING
                """,
                (
                    str(uuid.uuid4()),
                    comp["titulo"],
                    cat_norm,
                    comp["data_inicio"],
                    comp["data_fim"],
                    comp["descricao"],
                    comp["google_event_id"],
                    comp["criado_em"]
                )
            )
        print(f"-> {len(comps)} compromissos migrados.")

        # ---- 7. POSTS DE CONTEÚDO (posts_conteudo -> view / conteudos) ----
        print("\n[7/10] Migrando posts_conteudo para view posts_conteudo...")
        sqlite_cur.execute("SELECT tema, tipo, roteiro, status, views, engajamento, data_publicacao, criado_em FROM posts_conteudo")
        posts = sqlite_cur.fetchall()
        for post in posts:
            # Capitalização do status ('Ideia', 'Roteirizado', 'Gravado', 'Postado')
            status_cap = str(post["status"]).strip().capitalize()
            if status_cap not in ("Ideia", "Roteirizado", "Gravado", "Postado"):
                status_cap = "Ideia"
                
            pg_cur.execute(
                """
                INSERT INTO public.posts_conteudo (tema, tipo, roteiro, status, views, engajamento, data_publicacao, criado_em)
                VALUES (%s, %s, %s, %s, %s, %s, %s, COALESCE(%s, NOW()))
                """,
                (
                    post["tema"],
                    post["tipo"],
                    post["roteiro"],
                    status_cap,
                    post["views"] or 0,
                    post["engajamento"] or 0,
                    normalizar_data(post["data_publicacao"]),
                    post["criado_em"]
                )
            )
        print(f"-> {len(posts)} posts de conteúdo migrados.")

        # ---- 8. MEMBROS (Normalização em pessoas + pessoa_contatos + membros) ----
        print("\n[8/10] Migrando e Normalizando membros...")
        sqlite_cur.execute("""
            SELECT id, nome_completo, telefone, data_nascimento, bairro_cidade, tempo_igreja,
                   lider_celula, fez_encontro, universidade_vida, capacitacao_destino,
                   interesse_ministerio, feedback_melhorias, feedback_falta, celula_atual,
                   g12_pastoral, ministerios, data_conversao, status_cadastro,
                   consentimento_comunicacao, botconversa_subscriber_id,
                   ultima_atualizacao_cadastral, proxima_atualizacao_cadastral,
                   observacoes, criado_em, atualizado_em
            FROM membros
        """)
        sqlite_membros = sqlite_cur.fetchall()
        
        membros_migrados = 0
        for mb in sqlite_membros:
            sqlite_id = mb["id"]
            nome = str(mb["nome_completo"]).strip()
            tel_dig = normalizar_telefone(mb["telefone"])
            nascimento = normalizar_data(mb["data_nascimento"])
            conversao = normalizar_data(mb["data_conversao"])
            status_cad = normalizar_status_cadastro(mb["status_cadastro"])
            
            # 1. Inserir ou buscar Pessoa
            pessoa_uuid = str(uuid.uuid4())
            # Verifica se já existe contato com esse número de celular para evitar duplicar pessoas
            if tel_dig:
                pg_cur.execute("SELECT id, pessoa_id FROM public.pessoa_contatos WHERE canal = 'whatsapp' AND valor = %s", (tel_dig,))
                contato_existente = pg_cur.fetchone()
                if contato_existente:
                    # Se já existia contato cadastrado, aproveita a pessoa
                    pessoa_uuid = contato_existente[1]
                    pg_cur.execute("UPDATE public.pessoas SET nome_completo = %s, tipo = 'membro', data_nascimento = COALESCE(data_nascimento, %s) WHERE id = %s", (nome, nascimento, pessoa_uuid))
                else:
                    pg_cur.execute(
                        """
                        INSERT INTO public.pessoas (id, nome_completo, tipo, data_nascimento, observacoes, criado_em, atualizado_em)
                        VALUES (%s, %s, 'membro', %s, %s, COALESCE(%s, NOW()), COALESCE(%s, NOW()))
                        """,
                        (pessoa_uuid, nome, nascimento, mb["observacoes"], mb["criado_em"], mb["atualizado_em"])
                    )
            else:
                pg_cur.execute(
                    """
                    INSERT INTO public.pessoas (id, nome_completo, tipo, data_nascimento, observacoes, criado_em, updated_at_placeholder_bypass)
                    VALUES (%s, %s, 'membro', %s, %s, COALESCE(%s, NOW()), COALESCE(%s, NOW()))
                    """,
                    (pessoa_uuid, nome, nascimento, mb["observacoes"], mb["criado_em"], mb["atualizado_em"])
                )
                
            # 2. Inserir Contato (se houver telefone e se ainda não existir)
            if tel_dig:
                pg_cur.execute("SELECT id FROM public.pessoa_contatos WHERE canal = 'whatsapp' AND valor = %s", (tel_dig,))
                if not pg_cur.fetchone():
                    pg_cur.execute(
                        """
                        INSERT INTO public.pessoa_contatos (id, pessoa_id, canal, valor, principal, verificado, criado_em, atualizado_em)
                        VALUES (%s, %s, 'whatsapp', %s, true, false, COALESCE(%s, NOW()), COALESCE(%s, NOW()))
                        """,
                        (str(uuid.uuid4()), pessoa_uuid, tel_dig, mb["criado_em"], mb["atualizado_em"])
                    )
                    
            # 3. Inserir Endereço (Bairro) se fornecido
            if mb["bairro_cidade"]:
                pg_cur.execute(
                    """
                    INSERT INTO public.enderecos (id, pessoa_id, bairro, criado_em, atualizado_em)
                    VALUES (%s, %s, %s, COALESCE(%s, NOW()), COALESCE(%s, NOW()))
                    """,
                    (str(uuid.uuid4()), pessoa_uuid, mb["bairro_cidade"], mb["criado_em"], mb["atualizado_em"])
                )

            # 4. Inserir Membro
            membro_uuid = str(uuid.uuid4())
            
            # Verifica se já existia entrada do membro no Supabase para esse pessoa_id (para evitar violação UNIQUE)
            pg_cur.execute("SELECT id FROM public.membros WHERE pessoa_id = %s", (pessoa_uuid,))
            membro_existente = pg_cur.fetchone()
            if membro_existente:
                membro_uuid = membro_existente[0]
                pg_cur.execute(
                    """
                    UPDATE public.membros
                    SET botconversa_subscriber_id = COALESCE(botconversa_subscriber_id, %s),
                        tempo_igreja = %s, lider_celula = %s, celula_atual = %s, g12_pastoral = %s,
                        fez_encontro = %s, universidade_vida = %s, capacitacao_destino = %s,
                        status_cadastro = %s, consentimento_comunicacao = %s,
                        ultima_atualizacao_cadastral = %s, atualizado_em = NOW()
                    WHERE id = %s
                    """,
                    (
                        mb["botconversa_subscriber_id"], mb["tempo_igreja"], mb["lider_celula"],
                        mb["celula_atual"], mb["g12_pastoral"], mb["fez_encontro"],
                        mb["universidade_vida"], mb["capacitacao_destino"], status_cad,
                        bool(mb["consentimento_comunicacao"]), normalizar_data(mb["ultima_atualizacao_cadastral"]),
                        membro_uuid
                    )
                )
            else:
                pg_cur.execute(
                    """
                    INSERT INTO public.membros (
                        id, pessoa_id, tempo_igreja, lider_celula, celula_atual, g12_pastoral,
                        fez_encontro, universidade_vida, capacitacao_destino, ministerios,
                        interesse_ministerio, data_conversao, status_cadastro, consentimento_comunicacao,
                        botconversa_subscriber_id, ultima_atualizacao_cadastral, proxima_atualizacao_cadastral,
                        feedback_melhorias, feedback_falta, observacoes, criado_em, atualizado_em
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, COALESCE(%s, NOW()), COALESCE(%s, NOW()))
                    """,
                    (
                        membro_uuid,
                        pessoa_uuid,
                        mb["tempo_igreja"],
                        mb["lider_celula"],
                        mb["celula_atual"],
                        mb["g12_pastoral"],
                        mb["fez_encontro"],
                        mb["universidade_vida"],
                        mb["capacitacao_destino"],
                        mb["ministerios"],
                        mb["interesse_ministerio"],
                        conversao,
                        status_cad,
                        bool(mb["consentimento_comunicacao"]),
                        mb["botconversa_subscriber_id"],
                        normalizar_data(mb["ultima_atualizacao_cadastral"]),
                        normalizar_data(mb["proxima_atualizacao_cadastral"]),
                        mb["feedback_melhorias"],
                        mb["feedback_falta"],
                        mb["observacoes"],
                        mb["criado_em"],
                        mb["atualizado_em"]
                    )
                )
            
            # Registra no mapeamento para uso posterior no webhook / atendimentos
            mapeamento_membros[sqlite_id] = membro_uuid
            membros_migrados += 1
            
        print(f"-> {membros_migrados} membros normalizados e migrados.")

        # ---- 9. VISITANTES & CONSOLIDAÇÃO (consolidacao_visitantes) ----
        print("\n[9/10] Migrando e Normalizando visitantes & consolidacao...")
        sqlite_cur.execute("""
            SELECT id, data_visita, visitante_nome, visitante_whatsapp, consolidador_nome,
                   contato_24h, data_contato, feedback, status, criado_em
            FROM consolidacao_visitantes
        """)
        sqlite_vis = sqlite_cur.fetchall()
        
        vis_migrados = 0
        for vis in sqlite_vis:
            nome = str(vis["visitante_nome"]).strip()
            tel_dig = normalizar_telefone(vis["visitante_whatsapp"])
            data_visita = normalizar_data(vis["data_visita"]) or datetime.now().strftime("%Y-%m-%d")
            
            # 1. Inserir ou buscar Pessoa
            pessoa_uuid = str(uuid.uuid4())
            if tel_dig:
                pg_cur.execute("SELECT id, pessoa_id FROM public.pessoa_contatos WHERE canal = 'whatsapp' AND valor = %s", (tel_dig,))
                contato_existente = pg_cur.fetchone()
                if contato_existente:
                    pessoa_uuid = contato_existente[1]
                    pg_cur.execute("UPDATE public.pessoas SET nome_completo = %s, tipo = 'visitante' WHERE id = %s", (nome, pessoa_uuid))
                else:
                    pg_cur.execute(
                        """
                        INSERT INTO public.pessoas (id, nome_completo, tipo, criado_em, atualizado_em)
                        VALUES (%s, %s, 'visitante', COALESCE(%s, NOW()), COALESCE(%s, NOW()))
                        """,
                        (pessoa_uuid, nome, vis["criado_em"], vis["criado_em"])
                    )
            else:
                pg_cur.execute(
                    """
                    INSERT INTO public.pessoas (id, nome_completo, tipo, criado_em, atualizado_em)
                    VALUES (%s, %s, 'visitante', COALESCE(%s, NOW()), COALESCE(%s, NOW()))
                    """,
                    (pessoa_uuid, nome, vis["criado_em"], vis["criado_em"])
                )
                
            # 2. Contato
            if tel_dig:
                pg_cur.execute("SELECT id FROM public.pessoa_contatos WHERE canal = 'whatsapp' AND valor = %s", (tel_dig,))
                if not pg_cur.fetchone():
                    pg_cur.execute(
                        """
                        INSERT INTO public.pessoa_contatos (id, pessoa_id, canal, valor, principal, verificado, criado_em, atualizado_em)
                        VALUES (%s, %s, 'whatsapp', %s, true, false, COALESCE(%s, NOW()), COALESCE(%s, NOW()))
                        """,
                        (str(uuid.uuid4()), pessoa_uuid, tel_dig, vis["criado_em"], vis["criado_em"])
                    )
                    
            # 3. Visitante
            visitante_uuid = str(uuid.uuid4())
            pg_cur.execute("SELECT id FROM public.visitantes WHERE pessoa_id = %s", (pessoa_uuid,))
            visitante_existente = pg_cur.fetchone()
            if visitante_existente:
                visitante_uuid = visitante_existente[0]
            else:
                status_geral_visitante = normalizar_status_geral(vis["status"])
                pg_cur.execute(
                    """
                    INSERT INTO public.visitantes (id, pessoa_id, data_primeira_visita, status, criado_em, atualizado_em)
                    VALUES (%s, %s, %s, %s, COALESCE(%s, NOW()), COALESCE(%s, NOW()))
                    """,
                    (visitante_uuid, pessoa_uuid, data_visita, status_geral_visitante, vis["criado_em"], vis["criado_em"])
                )
                
            # 4. Consolidacao Visitante
            # Status na consolidação é text com checagem: check (status in ('Pendente', 'Contatado', 'Integrado', 'Desistiu'))
            status_cons = str(vis["status"]).strip().capitalize()
            if status_cons not in ("Pendente", "Contatado", "Integrado", "Desistiu"):
                status_cons = "Pendente"
                
            pg_cur.execute(
                """
                INSERT INTO public.consolidacao_visitantes (
                    id, visitante_id, pessoa_id, data_visita, visitante_nome, visitante_whatsapp,
                    consolidador_nome, contato_24h, data_contato, feedback, status, criado_em, atualizado_em
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, COALESCE(%s, NOW()), COALESCE(%s, NOW()))
                """,
                (
                    str(uuid.uuid4()),
                    visitante_uuid,
                    pessoa_uuid,
                    data_visita,
                    nome,
                    tel_dig or None,
                    vis["consolidador_nome"],
                    bool(vis["contato_24h"]),
                    vis["data_contato"],
                    vis["feedback"],
                    status_cons,
                    vis["criado_em"],
                    vis["criado_em"]
                )
            )
            vis_migrados += 1
            
        print(f"-> {vis_migrados} visitantes migrados para o funil de consolidação.")

        # ---- 10. RELATÓRIOS DE CÉLULAS (relatorios_celulas) ----
        print("\n[10/10] Migrando relatorios_celulas...")
        sqlite_cur.execute("SELECT data_relatorio, nome_celula, lider_nome, presenca_membros, visitantes, decisoes_fe, rede, criado_em FROM relatorios_celulas")
        celulas_rel = sqlite_cur.fetchall()
        for rel in celulas_rel:
            rede_norm = normalizar_rede(rel["rede"])
            pg_cur.execute(
                """
                INSERT INTO public.relatorios_celulas (id, data_relatorio, nome_celula, lider_nome, presenca_membros, visitantes, decisoes_fe, rede, criado_em)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, COALESCE(%s, NOW()))
                """,
                (
                    str(uuid.uuid4()),
                    normalizar_data(rel["data_relatorio"]),
                    rel["nome_celula"],
                    rel["lider_nome"],
                    rel["presenca_membros"],
                    rel["visitantes"],
                    rel["decisoes_fe"],
                    rede_norm,
                    rel["criado_em"]
                )
            )
        print(f"-> {len(celulas_rel)} relatórios de células migrados.")

        # ---- 11. ATENDIMENTOS RUTE (atendimentos_rute) ----
        print("\n[Bônus] Migrando atendimentos_rute...")
        sqlite_cur.execute("""
            SELECT id, pessoa_nome, telefone, tipo_solicitacao, origem, nivel_urgencia, status,
                   responsavel, resumo, membro_id, botconversa_subscriber_id, criado_em, atualizado_em
            FROM atendimentos_rute
        """)
        atends = sqlite_cur.fetchall()
        for at in atends:
            # Mapeia membro_id do SQLite local (integer) para o UUID correspondente remoto
            local_membro_id = at["membro_id"]
            membro_uuid_remoto = mapeamento_membros.get(local_membro_id) if local_membro_id else None
            
            pg_cur.execute(
                """
                INSERT INTO public.atendimentos_rute (
                    id, pessoa_nome, telefone, tipo_solicitacao, origem, nivel_urgencia, status,
                    responsavel, resumo, membro_id, botconversa_subscriber_id, criado_em, atualizado_em
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, COALESCE(%s, NOW()), COALESCE(%s, NOW()))
                ON CONFLICT (id) DO UPDATE
                SET status = EXCLUDED.status,
                    responsavel = EXCLUDED.responsavel,
                    resumo = EXCLUDED.resumo,
                    atualizado_em = NOW()
                """,
                (
                    at["id"],
                    at["pessoa_nome"],
                    normalizar_telefone(at["telefone"]) or None,
                    at["tipo_solicitacao"],
                    at["origem"],
                    at["nivel_urgencia"],
                    at["status"],
                    at["responsavel"],
                    at["resumo"],
                    membro_uuid_remoto,
                    at["botconversa_subscriber_id"],
                    at["criado_em"],
                    at["atualizado_em"]
                )
            )
        print(f"-> {len(atends)} atendimentos da Rute migrados.")

        pg_conn.commit()
        print("\n=== MIGRAÇÃO CONCLUÍDA COM SUCESSO! ===")
        print("Todas as tabelas foram copiadas para a nuvem no Supabase.")

    except Exception as e:
        pg_conn.rollback()
        print(f"\n[ERRO CRÍTICO NA MIGRAÇÃO]: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate_all()
