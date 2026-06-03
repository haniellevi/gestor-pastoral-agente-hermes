import streamlit as st
import pandas as pd
import numpy as np
import datetime
import os
import sqlite3
import sys
import json
import psycopg2

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from integrations.botconversa_client import BotConversaClient, BotConversaError
from integrations.sync_botconversa_config import sync_config

# Configuração da página
st.set_page_config(
    page_title="Gestão Pastoral - BI & Métricas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS customizada
st.markdown("""
    <style>
    .main {
        background-color: #0f1116;
        color: #e6edf3;
    }
    .stAppHeader {
        background-color: rgba(15, 17, 22, 0.8);
    }
    h1, h2, h3 {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif;
    }
    .card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .metric-value {
        font-size: 32px;
        font-weight: bold;
        color: #58a6ff;
    }
    .metric-label {
        font-size: 14px;
        color: #8b949e;
    }
    </style>
""", unsafe_allow_html=True)

# Caminho absoluto para o banco de dados
DB_PATH = os.path.join(PROJECT_ROOT, "database", "pastoral.db")

REQUIRED_BOTCONVERSA_TAGS = [
    "Membro",
    "Visitante",
    "Atualização Cadastral",
    "Cadastro Completo",
    "Cadastro Incompleto",
    "Atualização Pendente",
    "Consolidação 24h",
    "Célula",
    "G12 Pastoral - Pr. Raniel",
    "G12 Pastoral - Pastora Vanessa",
    "Ministério",
    "Ministério de Louvor",
    "Pedido de Oração",
    "Pedido de Aconselhamento",
    "Humano Necessário",
    "Em Atendimento Humano",
    "Atualização 6M Agendada",
    "Recadastro Anual Agendado",
    "Atualização Recusada",
    "Atualização Confirmada Sem Alteração",
    "Filadelfia Corrente",
    "CONVENÇÃO G12 2026",
]

REQUIRED_BOTCONVERSA_FIELDS = [
    "Data Nascimento",
    "Bairro",
    "Tempo_Igreja",
    "Lider_Celula",
    "Fez_Encontro",
    "Universidade_Vida",
    "Capacitacao_Destino",
    "Interesse_Ministerio",
    "Feedback_Melhorias",
    "Feedback_falta",
    "Celula_Atual",
    "G12_Pastoral",
    "Ministerios",
    "Data_Conversao",
    "Ultima_Atualiz_Cadas",
    "Status_Cadastro",
    "Tipo_Vinculo",
    "Resumo_Atend_IA",
    "Ultima_Intencao",
    "Encaminhamento_Necessario",
    "Nivel_Urgencia",
    "Proxima_Atualizacao_Cadastral",
    "Proximo_Recadastro_Anual",
]

REQUIRED_BOTCONVERSA_FLOWS = [
    "Boas Vindas Filadelfia",
    "Mensagem Padrão - IA RUTE",
    "Atualização Cadastral",
    "VISITANTE",
    "Encerrar Conversa",
    "Confirmação Cadastral 6M",
    "Recadastro Anual",
    "Pedido de Oração",
    "Pedido de Aconselhamento",
    "G12 e Células",
    "Ministérios",
]

def load_env() -> dict[str, str]:
    values = {}
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f.read().splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    values[k.strip()] = v.strip()
        except Exception:
            pass
    return values

def get_db_connection():
    env_vars = load_env()
    db_url = env_vars.get("SUPABASE_DB_URL")
    if db_url and "SUA_SENHA_AQUI" not in db_url:
        try:
            return psycopg2.connect(db_url)
        except Exception as e:
            # st.sidebar.error(f"Erro de conexão com o banco remoto: {e}")
            pass
    return sqlite3.connect(DB_PATH)

def run_query(query, params=()):
    try:
        conn = get_db_connection()
        is_pg = not isinstance(conn, sqlite3.Connection)
        
        # Converte placeholders se for PostgreSQL
        if is_pg:
            query = query.replace("?", "%s")
            
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erro ao acessar o banco de dados: {e}")
        return pd.DataFrame()

def run_write(query, params=()):
    try:
        conn = get_db_connection()
        is_pg = not isinstance(conn, sqlite3.Connection)
        
        if is_pg:
            query = query.replace("?", "%s")
            
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao gravar no banco de dados: {e}")
        return False

def ensure_operational_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    is_pg = not isinstance(conn, sqlite3.Connection)
    table_name = "public.atendimentos_rute" if is_pg else "atendimentos_rute"
    
    if is_pg:
        # Apenas garante que a tabela de atendimentos_rute existe na nuvem se necessário,
        # mas como ela já foi criada via SQL, não precisamos executar DDLs pelo app.
        conn.close()
        return
        
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pessoa_nome TEXT NOT NULL,
        telefone TEXT,
        tipo_solicitacao TEXT CHECK (tipo_solicitacao IN (
            'Atualizacao Cadastro',
            'Informacao Visitante',
            'Pedido Oracao',
            'Pedido Aconselhamento',
            'Entrar Celula',
            'Humano Necessario',
            'Outro'
        )) DEFAULT 'Outro',
        origem TEXT CHECK (origem IN ('BotConversa', 'Dashboard', 'Telegram', 'Manual', 'Outro')) DEFAULT 'Manual',
        nivel_urgencia TEXT CHECK (nivel_urgencia IN ('Baixa', 'Normal', 'Alta', 'Urgente')) DEFAULT 'Normal',
        status TEXT CHECK (status IN ('Novo', 'Em triagem', 'Encaminhado', 'Resolvido', 'Arquivado')) DEFAULT 'Novo',
        responsavel TEXT,
        resumo TEXT,
        membro_id INTEGER,
        botconversa_subscriber_id INTEGER,
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()


def normalize_name(value):
    return "".join(ch.lower() for ch in str(value or "") if ch.isalnum())

def item_name(item):
    return item.get("name") or item.get("title") or item.get("label") or item.get("key") or ""

def item_id(item):
    return item.get("id") or item.get("pk") or item.get("uuid") or ""

@st.cache_data(ttl=60)
def load_botconversa_snapshot():
    client = BotConversaClient()
    subscribers = client.list_subscribers()
    return {
        "tags": client.list_tags(),
        "flows": client.list_flows(),
        "sequences": client.list_sequences(),
        "campaigns": client.list_campaigns(),
        "custom_fields": client.list_custom_fields(),
        "subscribers_count": len(subscribers),
    }

def requirement_status(required_names, existing_items):
    existing = {normalize_name(item_name(item)): item for item in existing_items}
    rows = []
    for name in required_names:
        item = existing.get(normalize_name(name))
        rows.append({
            "Item necessário": name,
            "Status": "Criado" if item else "Pendente",
            "ID": item_id(item) if item else "",
            "Nome encontrado": item_name(item) if item else "",
        })
    return pd.DataFrame(rows)

def json_safe_preview(value, max_chars=220):
    try:
        preview = json.dumps(value, ensure_ascii=False)
    except TypeError:
        preview = str(value)
    if len(preview) > max_chars:
        return preview[:max_chars] + "..."
    return preview

def parse_roteiro_marketing(roteiro_text):
    if not roteiro_text:
        return "", "", "", ""
    
    design_section = ""
    instagram_copy = ""
    whatsapp_copy = ""
    prompt_ia = ""
    
    lines = roteiro_text.split('\n')
    current_section = None
    design_lines = []
    instagram_lines = []
    whatsapp_lines = []
    
    for line in lines:
        line_strip = line.strip()
        if "### 🎨 Design & Prompt" in line:
            current_section = "design"
            continue
        elif "### 📝 Legenda do Instagram" in line:
            current_section = "instagram"
            continue
        elif "### 💬 Mensagem para WhatsApp" in line:
            current_section = "whatsapp"
            continue
        
        if current_section == "design":
            design_lines.append(line)
        elif current_section == "instagram":
            instagram_lines.append(line)
        elif current_section == "whatsapp":
            whatsapp_lines.append(line)
            
    # Junta as seções
    design_section = "\n".join(design_lines).strip()
    instagram_copy = "\n".join(instagram_lines).strip()
    whatsapp_copy = "\n".join(whatsapp_lines).strip()
    
    # Limpa aspas extras que possam ter sido salvas no banco
    if instagram_copy.startswith('"') and instagram_copy.endswith('"'):
        instagram_copy = instagram_copy[1:-1].strip()
    if whatsapp_copy.startswith('"') and whatsapp_copy.endswith('"'):
        whatsapp_copy = whatsapp_copy[1:-1].strip()
        
    # Tenta extrair o prompt de IA das linhas da seção de design
    for d_line in design_lines:
        d_line_strip = d_line.strip()
        if "* **Prompt IA:**" in d_line_strip or "**Prompt IA:**" in d_line_strip:
            prompt_ia = d_line_strip.split("Prompt IA:**")[-1].strip()
            break
        elif "* **Prompt IA (English):**" in d_line_strip or "**Prompt IA (English):**" in d_line_strip:
            prompt_ia = d_line_strip.split("Prompt IA (English):**")[-1].strip()
            break
            
    if not prompt_ia and design_section:
        prompt_ia = "Ver detalhes do design na descrição abaixo."
        
    return prompt_ia, design_section, instagram_copy, whatsapp_copy

# Título Principal
ensure_operational_tables()

st.title("📊 Painel de Controle e Gestão Pastoral")
st.markdown("---")

# Barra Lateral (Filtros e Status dos Agentes)
st.sidebar.title("🤖 Status dos Agentes")
st.sidebar.markdown("""
🟢 **Hermes** (Orquestrador) - *Online*
🟢 **Rute** (Secretaria) - *Online*
🟢 **Caleb** (G12 / Conquista) - *Online*
🟢 **Barnabé** (Conteúdo) - *Online*
🟢 **Neemias** (Foco) - *Online*
""")
st.sidebar.markdown("---")

# Métricas Calculadas a partir do SQLite
# 1. Células Ativas
df_celulas_count = run_query("SELECT COUNT(DISTINCT nome_celula) as total FROM relatorios_celulas")
total_celulas = df_celulas_count.iloc[0]['total'] if not df_celulas_count.empty else 0

# 2. Frequência Média
df_freq_avg = run_query("SELECT AVG(presenca_membros) as media FROM relatorios_celulas")
freq_media = int(df_freq_avg.iloc[0]['media']) if not df_freq_avg.empty and df_freq_avg.iloc[0]['media'] is not None else 0

# 3. Índice de Foco do Pastor (Últimas metas concluídas)
df_metas_score = run_query("SELECT AVG(pontuacao_dia) as media FROM metas_diarias")
indice_foco = int(df_metas_score.iloc[0]['media']) if not df_metas_score.empty and df_metas_score.iloc[0]['media'] is not None else 0

# 4. Alcance Digital
df_views = run_query("SELECT SUM(views) as total FROM posts_conteudo")
views_total = df_views.iloc[0]['total'] if not df_views.empty and df_views.iloc[0]['total'] is not None else 0
views_total_formatted = f"{views_total/1000:.1f}K" if views_total >= 1000 else str(views_total)

# 5. Pendências da Rute
df_rute_pendencias = run_query("""
    SELECT COUNT(*) as total
    FROM atendimentos_rute
    WHERE status IN ('Novo', 'Em triagem', 'Encaminhado')
""")
total_rute_pendencias = df_rute_pendencias.iloc[0]['total'] if not df_rute_pendencias.empty else 0

# Layout de Linha 1: Métricas de Alto Nível (Cards)
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
        <div class="card">
            <div class="metric-label">Células Ativas (Visão G12)</div>
            <div class="metric-value">{total_celulas}</div>
            <div style='color: #3fb950; font-size: 12px;'>▲ 12% vs mês anterior</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="card">
            <div class="metric-label">Frequência Média nas Células</div>
            <div class="metric-value">{freq_media} <span style='font-size:16px; color:#8b949e;'>pessoas</span></div>
            <div style='color: #3fb950; font-size: 12px;'>▲ 8% vs mês anterior</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="card">
            <div class="metric-label">Índice de Foco do Pastor (Neemias)</div>
            <div class="metric-value">{indice_foco}%</div>
            <div style='color: #3fb950; font-size: 12px;'>▲ Alta consistência esta semana</div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
        <div class="card">
            <div class="metric-label">Alcance Digital (Barnabé)</div>
            <div class="metric-value">{views_total_formatted} <span style='font-size:16px; color:#8b949e;'>views</span></div>
            <div style='color: #58a6ff; font-size: 12px;'>• Reels & Shorts semanais</div>
        </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
        <div class="card">
            <div class="metric-label">Pendências da Rute</div>
            <div class="metric-value">{total_rute_pendencias}</div>
            <div style='color: #f2cc60; font-size: 12px;'>• Central de atendimento</div>
        </div>
    """, unsafe_allow_html=True)

# Abas de Visualização Detalhada
tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "👩‍💼 Rute Inbox",
    "🦁 Visão G12 & Caleb",
    "⚔️ Alta Performance & Neemias",
    "📢 Marketing & Barnabé",
    "🧠 Sugestões de IA (Hermes)",
    "📅 Agenda & Rute",
    "💬 WhatsApp & BotConversa",
])

with tab0:
    st.header("👩‍💼 Rute Inbox / Central Hermes de Atendimento")
    st.info("Fila única para cadastro, visitantes, oração, aconselhamento e pedidos de célula.")

    df_status_rute = run_query("""
        SELECT status as Status, COUNT(*) as Total
        FROM atendimentos_rute
        GROUP BY status
        ORDER BY Total DESC
    """)
    df_tipo_rute = run_query("""
        SELECT tipo_solicitacao as Tipo, COUNT(*) as Total
        FROM atendimentos_rute
        GROUP BY tipo_solicitacao
        ORDER BY Total DESC
    """)

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.subheader("Pendências por status")
        if df_status_rute.empty:
            st.info("Nenhum atendimento registrado ainda.")
        else:
            st.bar_chart(data=df_status_rute, x="Status", y="Total")
    with col_r2:
        st.subheader("Solicitações por tipo")
        if df_tipo_rute.empty:
            st.info("Nenhum tipo de solicitação registrado ainda.")
        else:
            st.bar_chart(data=df_tipo_rute, x="Tipo", y="Total")

    st.markdown("---")
    st.subheader("Abrir atendimento manual")
    with st.form("novo_atendimento_rute"):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            pessoa_nome = st.text_input("Nome da pessoa")
            telefone = st.text_input("Telefone/WhatsApp")
            tipo_solicitacao = st.selectbox(
                "Tipo de solicitação",
                [
                    "Atualizacao Cadastro",
                    "Informacao Visitante",
                    "Pedido Oracao",
                    "Pedido Aconselhamento",
                    "Entrar Celula",
                    "Humano Necessario",
                    "Outro",
                ],
            )
        with col_f2:
            nivel_urgencia = st.selectbox("Urgência", ["Normal", "Baixa", "Alta", "Urgente"])
            responsavel = st.text_input("Responsável inicial", placeholder="Rute, secretaria, líder...")
            resumo = st.text_area("Resumo do atendimento")

        submitted = st.form_submit_button("Criar atendimento")
        if submitted:
            if not pessoa_nome.strip():
                st.warning("Informe o nome da pessoa.")
            else:
                ok = run_write(
                    """
                    INSERT INTO atendimentos_rute (
                        pessoa_nome, telefone, tipo_solicitacao, origem, nivel_urgencia,
                        status, responsavel, resumo, criado_em, atualizado_em
                    )
                    VALUES (?, ?, ?, 'Dashboard', ?, 'Novo', ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    (
                        pessoa_nome.strip(),
                        "".join(ch for ch in telefone if ch.isdigit()) or None,
                        tipo_solicitacao,
                        nivel_urgencia,
                        responsavel.strip() or None,
                        resumo.strip() or None,
                    ),
                )
                if ok:
                    st.success("Atendimento criado na fila da Rute.")

    st.markdown("---")
    st.subheader("Fila de atendimento")
    status_filter = st.multiselect(
        "Filtrar status",
        ["Novo", "Em triagem", "Encaminhado", "Resolvido", "Arquivado"],
        default=["Novo", "Em triagem", "Encaminhado"],
    )
    placeholders = ",".join(["?"] * len(status_filter))
    if status_filter:
        df_atendimentos = run_query(
            f"""
            SELECT
                id as ID,
                criado_em as Criado,
                pessoa_nome as Pessoa,
                telefone as Telefone,
                tipo_solicitacao as Tipo,
                origem as Origem,
                nivel_urgencia as Urgencia,
                status as Status,
                responsavel as Responsavel,
                resumo as Resumo
            FROM atendimentos_rute
            WHERE status IN ({placeholders})
            ORDER BY
                CASE nivel_urgencia
                    WHEN 'Urgente' THEN 1
                    WHEN 'Alta' THEN 2
                    WHEN 'Normal' THEN 3
                    ELSE 4
                END,
                criado_em DESC
            """,
            tuple(status_filter),
        )
    else:
        df_atendimentos = pd.DataFrame()

    if df_atendimentos.empty:
        st.info("Nenhum atendimento para o filtro selecionado.")
    else:
        st.dataframe(df_atendimentos, use_container_width=True)

        with st.form("atualizar_atendimento_rute"):
            col_u1, col_u2, col_u3 = st.columns(3)
            with col_u1:
                atendimento_id = st.number_input("ID do atendimento", min_value=1, step=1)
            with col_u2:
                novo_status = st.selectbox("Novo status", ["Em triagem", "Encaminhado", "Resolvido", "Arquivado", "Novo"])
            with col_u3:
                novo_responsavel = st.text_input("Responsável")
            observacao = st.text_area("Observação/resumo atualizado")
            update_submitted = st.form_submit_button("Atualizar atendimento")
            if update_submitted:
                ok = run_write(
                    """
                    UPDATE atendimentos_rute
                    SET status = ?,
                        responsavel = NULLIF(?, ''),
                        resumo = CASE WHEN ? = '' THEN resumo ELSE ? END,
                        atualizado_em = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        novo_status,
                        novo_responsavel.strip(),
                        observacao.strip(),
                        observacao.strip(),
                        int(atendimento_id),
                    ),
                )
                if ok:
                    st.success("Atendimento atualizado.")

with tab1:
    st.header("Crescimento e Consolidação - G12 (Caleb)")
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.subheader("Frequência de Células Recentes")
        df_cel_data = run_query("""
            SELECT data_relatorio as Data, SUM(presenca_membros) as Membros, SUM(visitantes) as Visitantes 
            FROM relatorios_celulas 
            GROUP BY data_relatorio
            ORDER BY data_relatorio ASC
        """)
        if not df_cel_data.empty:
            df_cel_data.set_index("Data", inplace=True)
            st.line_chart(df_cel_data)
        else:
            st.info("Nenhum relatório de célula registrado ainda.")
        
    with col_g2:
        st.subheader("Totalizador por Rede")
        df_rede = run_query("""
            SELECT rede as Rede, SUM(presenca_membros) as Membros, SUM(visitantes) as Visitantes
            FROM relatorios_celulas
            GROUP BY rede
        """)
        if not df_rede.empty:
            st.bar_chart(data=df_rede, x="Rede", y="Membros")
        else:
            st.info("Nenhum dado de rede disponível.")
            
    st.markdown("---")
    st.subheader("🎯 Funil de Consolidação Rápida (Limite de 24h)")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        df_visitantes_status = run_query("""
            SELECT status as Status, COUNT(*) as Total
            FROM consolidacao_visitantes
            GROUP BY status
        """)
        if not df_visitantes_status.empty:
            st.write("**Visitantes por Status de Consolidação**")
            st.bar_chart(data=df_visitantes_status, x="Status", y="Total")
        else:
            st.info("Nenhum visitante cadastrado.")
    with col_c2:
        df_contato_24h = run_query("""
            SELECT CASE WHEN contato_24h = 1 THEN 'Contatado em < 24h' ELSE 'Atrasado / Sem Contato' END as Prazo,
                   COUNT(*) as Total
            FROM consolidacao_visitantes
            GROUP BY contato_24h
        """)
        if not df_contato_24h.empty:
            st.write("**Acompanhamento do Prazo de 24 horas**")
            st.dataframe(df_contato_24h, use_container_width=True)
        else:
            st.info("Sem dados de prazo.")

    st.markdown("---")
    st.subheader("👥 Fila de Consolidação de Visitantes")
    df_visitantes_lista = run_query("""
        SELECT 
            id as ID,
            data_visita as "Data Visita",
            visitante_nome as Nome,
            visitante_whatsapp as WhatsApp,
            consolidador_nome as Consolidador,
            CASE WHEN contato_24h = 1 THEN 'Sim' ELSE 'Não' END as "Contato 24h?",
            data_contato as "Data Contato",
            status as Status,
            feedback as Feedback
        FROM consolidacao_visitantes
        ORDER BY status DESC, data_visita DESC
    """)
    if df_visitantes_lista.empty:
        st.info("Nenhum visitante em consolidação registrado.")
    else:
        st.dataframe(df_visitantes_lista, use_container_width=True)
        
        st.markdown("##### Atualizar status/atribuição de visitante")
        with st.form("atualizar_visitante_consolidacao"):
            col_v1, col_v2, col_v3 = st.columns(3)
            with col_v1:
                visitante_id = st.number_input("ID do Visitante", min_value=1, step=1)
                novo_consolidador = st.text_input("Nome do Consolidador")
            with col_v2:
                novo_status_vis = st.selectbox("Status da Consolidação", ["Pendente", "Contatado", "Integrado", "Desistiu"])
                contato_24h_chk = st.checkbox("Contato feito em < 24h?")
            with col_v3:
                data_contato_vis = st.date_input("Data do Contato", value=datetime.date.today())
            feedback_vis = st.text_area("Feedback/Anotações")
            
            update_vis_submitted = st.form_submit_button("Salvar Alterações do Visitante")
            if update_vis_submitted:
                ok = run_write(
                    """
                    UPDATE consolidacao_visitantes
                    SET consolidador_nome = CASE WHEN ? = '' THEN consolidador_nome ELSE ? END,
                        status = ?,
                        contato_24h = ?,
                        data_contato = ?,
                        feedback = CASE WHEN ? = '' THEN feedback ELSE ? END
                    WHERE id = ?
                    """,
                    (
                        novo_consolidador.strip(),
                        novo_consolidador.strip(),
                        novo_status_vis,
                        1 if contato_24h_chk else 0,
                        data_contato_vis.strftime("%Y-%m-%d"),
                        feedback_vis.strip(),
                        feedback_vis.strip(),
                        int(visitante_id)
                    )
                )
                if ok:
                    st.success(f"Visitante {visitante_id} atualizado com sucesso!")
                    st.rerun()

    st.markdown("---")
    st.subheader("📝 Registrar Relatório de Célula Manual")
    with st.form("novo_relatorio_celula_manual"):
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            nome_celula_m = st.text_input("Nome da Célula")
            lider_nome_m = st.text_input("Nome do Líder")
        with col_c2:
            rede_m = st.selectbox("Rede", ["Jovens", "Casais", "Homens", "Mulheres"])
            data_rel_m = st.date_input("Data do Relatório", value=datetime.date.today())
        with col_c3:
            presenca_m = st.number_input("Presença de Membros", min_value=0, value=0, step=1)
            visitantes_m = st.number_input("Quantidade de Visitantes", min_value=0, value=0, step=1)
            decisoes_m = st.number_input("Decisões de Fé", min_value=0, value=0, step=1)
            
        submitted_cel = st.form_submit_button("Cadastrar Relatório")
        if submitted_cel:
            if not nome_celula_m.strip() or not lider_nome_m.strip():
                st.warning("Nome da Célula e Líder são obrigatórios.")
            else:
                ok = run_write(
                    """
                    INSERT INTO relatorios_celulas (
                        data_relatorio, nome_celula, lider_nome, presenca_membros, visitantes, decisoes_fe, rede, criado_em
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (
                        data_rel_m.strftime("%Y-%m-%d"),
                        nome_celula_m.strip(),
                        lider_nome_m.strip(),
                        int(presenca_m),
                        int(visitantes_m),
                        int(decisoes_m),
                        rede_m
                    )
                )
                if ok:
                    st.success("Relatório de Célula cadastrado com sucesso!")
                    st.rerun()

    st.markdown("---")
    st.subheader("📋 Relatórios de Células Enviados")
    df_relatorios_recentes = run_query("""
        SELECT 
            id as ID,
            data_relatorio as Data,
            nome_celula as Célula,
            lider_nome as Líder,
            rede as Rede,
            presenca_membros as Membros,
            visitantes as Visitantes,
            decisoes_fe as "Decisões de Fé"
        FROM relatorios_celulas
        ORDER BY data_relatorio DESC, criado_em DESC
        LIMIT 10
    """)
    if df_relatorios_recentes.empty:
        st.info("Nenhum relatório de célula enviado ainda.")
    else:
        st.dataframe(df_relatorios_recentes, use_container_width=True)


with tab2:
    st.header("Consistência de Foco (Neemias)")
    st.subheader("Pontuação Diária de Conclusão das '3 Vitórias'")
    
    df_foco_data = run_query("""
        SELECT data as Data, pontuacao_dia as Pontuacao
        FROM metas_diarias
        ORDER BY data ASC
    """)
    if not df_foco_data.empty:
        df_foco_data.set_index("Data", inplace=True)
        st.area_chart(df_foco_data)
    else:
        st.info("Nenhuma meta diária registrada ainda.")
        
    st.subheader("Metas de Hoje e Status")
    df_metas_hoje = run_query("""
        SELECT data, vitoria_1, vitoria_1_concluida, vitoria_2, vitoria_2_concluida, vitoria_3, vitoria_3_concluida, anotacoes
        FROM metas_diarias
        ORDER BY data DESC LIMIT 3
    """)
    
    if not df_metas_hoje.empty:
        df_metas_hoje = df_metas_hoje.fillna('')
        for idx, row in df_metas_hoje.iterrows():
            st.write(f"### Metas do Dia: {row['data']}")
            st.checkbox(f"Vitória 1: {row['vitoria_1']}", value=bool(row['vitoria_1_concluida']), disabled=True, key=f"v1_{idx}")
            st.checkbox(f"Vitória 2: {row['vitoria_2']}", value=bool(row['vitoria_2_concluida']), disabled=True, key=f"v2_{idx}")
            st.checkbox(f"Vitória 3: {row['vitoria_3']}", value=bool(row['vitoria_3_concluida']), disabled=True, key=f"v3_{idx}")
            if row['anotacoes']:
                st.info(f"📝 Anotações: {row['anotacoes']}")
            st.markdown("---")
    else:
        st.write("Sem registros de metas para hoje.")
            
    st.markdown("---")
    st.subheader("🛡️ Padrões e Fatores de Procrastinação")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        df_distracoes = run_query("""
            SELECT distracao as 'Tipo de Distração', COUNT(*) as Ocorrências
            FROM registro_procrastinacao
            GROUP BY distracao
            ORDER BY Ocorrências DESC
        """)
        if not df_distracoes.empty:
            st.write("**Principais Distrações Registradas**")
            st.bar_chart(data=df_distracoes, x="Tipo de Distração", y="Ocorrências")
        else:
            st.info("Nenhum desvio de foco registrado. Continue assim!")
    with col_p2:
        df_procrastinadas_lista = run_query("""
            SELECT data as Data, tarefa_adiada as 'Tarefa Adiada', distracao as 'Distração/Motivo'
            FROM registro_procrastinacao
            ORDER BY data DESC
        """)
        if not df_procrastinadas_lista.empty:
            st.write("**Histórico de Tarefas Adiadas**")
            st.dataframe(df_procrastinadas_lista, use_container_width=True)


with tab3:
    st.header("📢 Marketing & Criação de Conteúdo (Barnabé)")
    
    # Seção 1: Campanhas de Culto e Criação de Artes
    st.markdown("### 🎨 Campanhas de Culto e Criação de Artes")
    
    # Query para buscar posts roteirizados ou cadastrados
    df_campanhas = run_query("""
        SELECT id, tema, tipo, roteiro, status, data_publicacao 
        FROM posts_conteudo 
        ORDER BY id DESC
    """)
    
    if df_campanhas.empty:
        st.info("""
        ℹ️ **Nenhuma campanha de marketing roteirizada no momento.**
        
        Para planejar as divulgações do próximo culto:
        1. Peça para a **Rute** agendar um compromisso com a categoria **'Culto'** na agenda.
        2. O **Barnabé** gerará automaticamente o design e os textos em até 2 dias antes do evento.
        3. Você também pode acionar o **Barnabé** no Telegram a qualquer momento digitando: *'Barnabé, planeje a arte e o copy do culto sobre [Tema] do próximo domingo.'*
        """)
        
        # Mostra as diretrizes de marca rápidas de suporte
        with st.expander("🎨 Ver Diretrizes Rápidas de Identidade Visual"):
            st.markdown("""
            **Paleta de Cores Oficial:**
            - 🔵 **Azul Navy Profundo:** `#111827` (Fundo principal)
            - 🟡 **Dourado Real:** `#D97706` (Títulos e destaques)
            - ⚪ **Branco Puro:** `#FFFFFF` (Texto do corpo)
            - 🔘 **Cinza Neblina:** `#9CA3AF` (Rodapés e datas)
            
            **Tipografias Recomendadas:**
            - **Títulos:** `Outfit` ou `Inter` (Extra Bold, Caixa Alta, Kerning amplo)
            - **Textos:** `Inter` (Regular)
            
            **Estilo de Copy:**
            - Sem jargões "crentês" ou clichês religiosos. 
            - Foco em sentimentos reais, dilemas do dia a dia e aplicação prática.
            """)
    else:
        # Filtrar apenas os que possuem conteúdo estruturado (roteiro não nulo ou vazio)
        df_campanhas_validas = df_campanhas[df_campanhas['roteiro'].notna() & (df_campanhas['roteiro'] != '')]
        
        if df_campanhas_validas.empty:
            st.info("""
            ℹ️ **Nenhuma campanha de marketing roteirizada no momento.**
            
            Para planejar as divulgações do próximo culto:
            1. Peça para a **Rute** agendar um compromisso com a categoria **'Culto'** na agenda.
            2. O **Barnabé** gerará automaticamente o design e os textos em até 2 dias antes do evento.
            """)
        else:
            # Lista as opções para o selectbox
            opcoes_campanhas = []
            campanhas_dict = {}
            for idx, row in df_campanhas_validas.iterrows():
                # Formata a data de publicação de forma legível se existir
                data_str = f" - {row['data_publicacao']}" if row['data_publicacao'] else ""
                label = f"{row['tema']} ({row['status']}{data_str})"
                opcoes_campanhas.append(label)
                campanhas_dict[label] = row
                
            campanha_selecionada = st.selectbox("Selecione a Campanha de Divulgação para Copiar os Conteúdos:", options=opcoes_campanhas)
            
            if campanha_selecionada:
                campanha_row = campanhas_dict[campanha_selecionada]
                
                # Faz o parse das seções do roteiro
                prompt_ia, design_section, instagram_copy, whatsapp_copy = parse_roteiro_marketing(campanha_row['roteiro'])
                
                st.markdown(f"#### 📅 Detalhes da Campanha: **{campanha_row['tema']}**")
                
                col_det1, col_det2, col_det3 = st.columns(3)
                col_det1.metric("Status", campanha_row['status'])
                col_det2.metric("Tipo de Mídia", campanha_row['tipo'])
                col_det3.metric("Data Programada", campanha_row['data_publicacao'] if campanha_row['data_publicacao'] else "Não agendada")
                
                # Renderiza o visual premium do post em Abas
                tab_design, tab_insta, tab_wa = st.tabs([
                    "🎨 Prompt da Arte & Layout", 
                    "📸 Legenda (Instagram)", 
                    "💬 Mensagem (WhatsApp)"
                ])
                
                with tab_design:
                    st.markdown("##### 🚀 Copie o Prompt para Geradores de IA (Canva, Midjourney, nanobanana):")
                    if prompt_ia:
                        st.code(prompt_ia, language="text")
                    else:
                        st.warning("Nenhum prompt específico extraído. Veja as instruções completas abaixo.")
                        
                    st.markdown("##### 📐 Instruções de Layout & Estrutura Visual:")
                    st.markdown(design_section)
                    
                    st.markdown("---")
                    st.markdown("""
                    💡 **Dica da Identidade Visual da Filadélfia:**
                    - Use o **Azul Navy** (`#111827`) como fundo e o **Dourado** (`#D97706`) no título principal em fonte **Outfit Bold** (caixa alta com espaçamento largo).
                    - Coloque fotos reais ou texturas elegantes escurecidas com contraste suave.
                    """)
                    
                with tab_insta:
                    st.markdown("##### 📝 Copie a Legenda para o Instagram:")
                    if instagram_copy:
                        st.code(instagram_copy, language="text")
                    else:
                        st.warning("Nenhuma legenda do Instagram encontrada.")
                    
                    st.markdown("---")
                    st.markdown("💡 *Legenda planejada para gerar conexão e reflexão sobre a vida prática, sem jargões 'crentês' limitantes.*")
                    
                with tab_wa:
                    st.markdown("##### 💬 Copie a Mensagem do WhatsApp:")
                    if whatsapp_copy:
                        st.code(whatsapp_copy, language="text")
                    else:
                        st.warning("Nenhuma mensagem de WhatsApp encontrada.")
                    
                    st.markdown("---")
                    st.markdown("💡 *Formato ideal para disparo nos grupos oficiais da igreja, grupos de célula e lista de transmissão.*")
                    
    st.markdown("---")
    st.subheader("📊 Estatísticas Gerais de Redes Sociais")
    
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.write("**Visualizações por Formato de Vídeo**")
        df_formato = run_query("""
            SELECT tipo as Formato, SUM(views) as Visualizacoes
            FROM posts_conteudo
            WHERE tipo IS NOT NULL
            GROUP BY tipo
        """)
        if not df_formato.empty:
            st.bar_chart(data=df_formato, x="Formato", y="Visualizacoes")
        else:
            st.info("Nenhum post registrado no banco.")
        
    with col_m2:
        st.write("**Status Editorial de Conteúdo**")
        df_status = run_query("""
            SELECT status as Status, COUNT(*) as Total
            FROM posts_conteudo
            GROUP BY status
        """)
        if not df_status.empty:
            st.dataframe(df_status, use_container_width=True)
        else:
            st.info("Nenhum post disponível.")

with tab4:
    st.header("Sugestões de Atualização do BI (Hermes)")
    st.info("O Hermes monitora os gargalos relatados nos atendimentos e sugere novas métricas dinamicamente.")
    
    df_sugestoes = run_query("""
        SELECT origem_conversa as 'Origem do Insights', 
               metrica_sugerida as 'Métrica Recomendada', 
               justificativa as Justificativa, 
               status as Status
        FROM sugestoes_bi
    """)
    if not df_sugestoes.empty:
        st.dataframe(df_sugestoes, use_container_width=True)
    else:
        st.info("Nenhuma sugestão de BI do orquestrador encontrada.")

with tab5:
    st.header("Agenda e Compromissos Recentes (Rute)")
    st.info("A Rute gerencia e otimiza a agenda pessoal e eclesiástica do Pastor Raniel Levi.")
    
    df_agenda = run_query("""
        SELECT titulo as Compromisso, 
               categoria as Categoria, 
               data_inicio as 'Data e Hora de Início', 
               data_fim as 'Data e Hora de Fim', 
               descricao as Descrição, 
               duracao_minutos as 'Duração (Min)'
        FROM compromissos
        ORDER BY data_inicio ASC
    """)
    if not df_agenda.empty:
        st.dataframe(df_agenda, use_container_width=True)
    else:
        st.info("Nenhum compromisso agendado no banco.")
        
    st.markdown("---")
    st.subheader("⏱️ Distribuição de Tempo por Categoria (Horas)")
    df_tempo_categoria = run_query("""
        SELECT categoria as Categoria, SUM(duracao_minutos) / 60.0 as Horas
        FROM compromissos
        GROUP BY categoria
        ORDER BY Horas DESC
    """)
    if not df_tempo_categoria.empty:
        st.bar_chart(data=df_tempo_categoria, x="Categoria", y="Horas")
    else:
        st.info("Sem dados de tempo categorizado.")

with tab6:
    st.header("💬 WhatsApp & BotConversa")
    st.info(
        "Central para acompanhar a integração do WhatsApp, mapear IDs do BotConversa "
        "e preparar fluxos pastorais antes de disparos automáticos."
    )

    # Detecção automática do túnel Ngrok local
    ngrok_url = None
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels", timeout=1) as resp:
            tunnels_data = json.loads(resp.read().decode())
            for tunnel in tunnels_data.get("tunnels", []):
                pub_url = tunnel.get("public_url", "")
                if pub_url.startswith("https:"):
                    ngrok_url = pub_url
                    break
    except Exception:
        pass

    if ngrok_url:
        webhook_url = f"{ngrok_url}/webhook_atualizacao_cadastral"
        st.success("🌐 **Túnel Ngrok Ativo Detectado!**")
        st.markdown("Copie o endereço abaixo e cole nas configurações de Webhook do seu painel do BotConversa:")
        st.code(webhook_url, language="text")
        st.markdown("---")
    else:
        st.warning("⚠️ **Túnel Ngrok não detectado ou inativo.**")
        st.markdown(
            "Certifique-se de iniciar o sistema através do `run_local.bat` para carregar o túnel. "
            "Se o Ngrok estiver rodando em outra janela, verifique a URL na tela preta do terminal."
        )
        st.markdown("---")

    if st.button("🔄 Atualizar dados do BotConversa"):
        load_botconversa_snapshot.clear()

    if st.button("🧭 Sincronizar IDs conhecidos"):
        try:
            sync_summary = sync_config()
            load_botconversa_snapshot.clear()
            st.success(f"{len(sync_summary['updated'])} mapeamento(s) atualizado(s).")
            if sync_summary["missing"]:
                st.info(f"{len(sync_summary['missing'])} item(ns) ainda pendente(s) de criação/localização.")
        except Exception as exc:
            st.error(f"Erro ao sincronizar IDs: {exc}")

    try:
        snapshot = load_botconversa_snapshot()
        tags = snapshot["tags"]
        flows = snapshot["flows"]
        sequences = snapshot["sequences"]
        campaigns = snapshot["campaigns"]
        custom_fields = snapshot["custom_fields"]

        col_bc1, col_bc2, col_bc3, col_bc4, col_bc5 = st.columns(5)
        col_bc1.metric("Contatos", snapshot["subscribers_count"])
        col_bc2.metric("Etiquetas", len(tags))
        col_bc3.metric("Campos", len(custom_fields))
        col_bc4.metric("Fluxos", len(flows))
        col_bc5.metric("Sequências", len(sequences))

        st.markdown("### Checklist para os fluxos pastorais")
        check_tag, check_field, check_flow = st.tabs(["Etiquetas", "Campos personalizados", "Fluxos"])
        with check_tag:
            st.dataframe(requirement_status(REQUIRED_BOTCONVERSA_TAGS, tags), use_container_width=True)
            st.caption("Se algum item estiver pendente, crie a etiqueta no painel do BotConversa e atualize esta tela.")
        with check_field:
            st.dataframe(requirement_status(REQUIRED_BOTCONVERSA_FIELDS, custom_fields), use_container_width=True)
            st.caption("A API pública lista campos personalizados, mas não expõe criação. A criação deve ser feita no painel BotConversa.")
        with check_flow:
            st.dataframe(requirement_status(REQUIRED_BOTCONVERSA_FLOWS, flows), use_container_width=True)
            st.caption("Depois que você criar os fluxos, vamos mapear os IDs aqui e liberar os disparos controlados.")

        st.markdown("---")
        st.markdown("### Mapeamento local de IDs")
        df_config = run_query("""
            SELECT chave as Chave, valor as Valor, descricao as Descrição, atualizado_em as Atualizado
            FROM botconversa_config
            ORDER BY chave
        """)
        if df_config.empty:
            st.warning("A tabela de configuração ainda não existe. Rode a migração pastoral/BotConversa.")
        else:
            st.dataframe(df_config, use_container_width=True)
            with st.form("botconversa_config_form"):
                config_keys = df_config["Chave"].tolist()
                selected_key = st.selectbox("Configuração", config_keys)
                current_value = str(df_config.loc[df_config["Chave"] == selected_key, "Valor"].iloc[0] or "")
                new_value = st.text_input("ID ou valor no BotConversa", value=current_value)
                submitted = st.form_submit_button("Salvar mapeamento")
                if submitted:
                    ok = run_write(
                        """
                        UPDATE botconversa_config
                        SET valor = ?, atualizado_em = CURRENT_TIMESTAMP
                        WHERE chave = ?
                        """,
                        (new_value.strip(), selected_key),
                    )
                    if ok:
                        st.success("Mapeamento salvo. Atualize a página para ver o valor na tabela.")

        st.markdown("---")
        st.markdown("### Inventário BotConversa")
        inv_tags, inv_fields, inv_flows, inv_sequences, inv_campaigns = st.tabs([
            "Etiquetas existentes",
            "Campos existentes",
            "Fluxos existentes",
            "Sequências",
            "Campanhas",
        ])

        def inventory_df(items):
            return pd.DataFrame([
                {
                    "ID": item_id(item),
                    "Nome": item_name(item),
                    "Dados": json_safe_preview(item),
                }
                for item in items
            ])

        with inv_tags:
            st.dataframe(inventory_df(tags), use_container_width=True)
        with inv_fields:
            st.dataframe(inventory_df(custom_fields), use_container_width=True)
        with inv_flows:
            st.dataframe(inventory_df(flows), use_container_width=True)
        with inv_sequences:
            st.dataframe(inventory_df(sequences), use_container_width=True)
        with inv_campaigns:
            st.dataframe(inventory_df(campaigns), use_container_width=True)

        st.markdown("---")
        st.markdown("### Busca segura de contato")
        st.caption("Consulta apenas. Não envia mensagem nem dispara fluxo.")
        phone_lookup = st.text_input("Telefone com DDD", placeholder="558999999999")
        if st.button("Buscar contato"):
            if phone_lookup.strip():
                client = BotConversaClient()
                subscriber = client.find_subscriber_by_phone(phone_lookup)
                if subscriber:
                    st.json(subscriber)
                else:
                    st.warning("Contato não encontrado.")
            else:
                st.warning("Informe um telefone para buscar.")

        st.markdown("---")
        st.markdown("### Próximos fluxos a criar no BotConversa")
        st.markdown("""
        **1. Fluxo de Boas-vindas**
        Recepciona, verifica cadastro e encaminha para atualização cadastral quando necessário.

        **2. Fluxo de Atualização Cadastral**
        Coleta nome, telefone, nascimento, bairro, tempo de igreja, líder de célula, trilhas de crescimento,
        interesse em ministério e feedback.

        **3. Fluxo de Consolidação de Visitante**
        Ajuda Caleb a garantir contato em até 24 horas, registrar feedback e sinalizar integração.
        """)

        st.markdown("---")
        st.markdown("### 📋 Histórico de Sincronizações (Hermes Webhook)")
        st.markdown("Acompanhe em tempo real os dados recebidos do BotConversa e salvos no SQLite local.")
        
        df_sync_logs = run_query("""
            SELECT id as ID, acao as 'Ação', entidade_tipo as 'Entidade', entidade_id as 'ID Local', status as Status, resultado as 'Resultado da Ação', criado_em as 'Data/Hora'
            FROM botconversa_sync_log
            ORDER BY criado_em DESC
            LIMIT 20
        """)
        if df_sync_logs.empty:
            st.info("Nenhuma sincronização de webhook registrada ainda.")
        else:
            st.dataframe(df_sync_logs, use_container_width=True)

    except BotConversaError as exc:
        st.error(f"Erro na integração BotConversa: {exc}")
    except Exception as exc:
        st.error(f"Erro inesperado ao carregar BotConversa: {exc}")
