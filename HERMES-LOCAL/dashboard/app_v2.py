import os
import sys
from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from hermes_v2.db import adapt_query, get_connection, is_postgres
from hermes_v2.schema import ensure_sqlite_schema


st.set_page_config(
    page_title="Hermes 2.0 - Operação Pastoral",
    page_icon="H2",
    layout="wide",
    initial_sidebar_state="expanded",
)


def prepare_connection():
    conn = get_connection()
    ensure_sqlite_schema(conn)
    return conn


def run_query(query: str, params=()) -> pd.DataFrame:
    conn = None
    try:
        conn = prepare_connection()
        return pd.read_sql_query(adapt_query(conn, query), conn, params=params)
    except Exception as exc:
        st.error(f"Erro ao consultar dados da v2: {exc}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def run_write(query: str, params=()) -> bool:
    conn = None
    try:
        conn = prepare_connection()
        cursor = conn.cursor()
        cursor.execute(adapt_query(conn, query), params)
        conn.commit()
        return True
    except Exception as exc:
        st.error(f"Erro ao salvar dados da v2: {exc}")
        return False
    finally:
        if conn:
            conn.close()


def db_label() -> str:
    conn = None
    try:
        conn = prepare_connection()
        return "Supabase/Postgres" if is_postgres(conn) else "SQLite local"
    except Exception:
        return "indisponível"
    finally:
        if conn:
            conn.close()


def metric_count(query: str, params=()) -> int:
    df = run_query(query, params)
    if df.empty:
        return 0
    return int(df.iloc[0, 0] or 0)


st.title("Hermes 2.0 - Operação Pastoral")
st.caption("Painel enxuto para a transição da v1 para o webhook único do BotConversa.")

with st.sidebar:
    st.subheader("Status")
    st.write(f"Banco ativo: **{db_label()}**")
    st.write("Webhook v2: `/webhook/botconversa`")
    st.write("Legado: rotas antigas ainda ativas")

open_inbox = metric_count("SELECT COUNT(*) FROM inbox_pastoral WHERE status IN ('Novo', 'Em triagem')")
open_tasks = metric_count("SELECT COUNT(*) FROM tarefas_pastorais WHERE status IN ('Pendente', 'Em andamento')")
late_tasks = metric_count("""
    SELECT COUNT(*) FROM tarefas_pastorais
    WHERE status IN ('Pendente', 'Em andamento') AND prazo_para < CURRENT_TIMESTAMP
""")
visitors_24h = metric_count("""
    SELECT COUNT(*) FROM tarefas_pastorais
    WHERE tipo = 'followup_visitante_24h' AND status IN ('Pendente', 'Em andamento')
""")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Inbox aberta", open_inbox)
col2.metric("Tarefas abertas", open_tasks)
col3.metric("Tarefas vencidas", late_tasks)
col4.metric("Consolidação 24h", visitors_24h)

tab_inbox, tab_visitantes, tab_celulas, tab_tarefas, tab_bi = st.tabs([
    "Inbox",
    "Visitantes 24h",
    "Células",
    "Agenda/Tarefas",
    "BI Semanal",
])

with tab_inbox:
    st.header("Inbox Pastoral")
    inbox_df = run_query("""
        SELECT id, criado_em, status, papel_responsavel, intencao, nivel_urgencia,
               prioridade, nome, telefone, fluxo_origem, mensagem
        FROM inbox_pastoral
        ORDER BY criado_em DESC
        LIMIT 100
    """)
    st.dataframe(inbox_df, use_container_width=True, hide_index=True)

    st.subheader("Atualizar atendimento")
    with st.form("update_inbox_status"):
        inbox_id = st.text_input("ID do atendimento")
        status = st.selectbox("Novo status", ["Novo", "Em triagem", "Encaminhado", "Resolvido", "Arquivado"])
        submitted = st.form_submit_button("Atualizar")
        if submitted and inbox_id:
            if run_write(
                "UPDATE inbox_pastoral SET status = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
                (status, inbox_id),
            ):
                st.success("Atendimento atualizado.")

with tab_visitantes:
    st.header("Visitantes e Consolidação 24h")
    tasks_df = run_query("""
        SELECT id, prazo_para, status, prioridade, titulo, responsavel, criado_em
        FROM tarefas_pastorais
        WHERE tipo = 'followup_visitante_24h'
        ORDER BY status ASC, prazo_para ASC
        LIMIT 100
    """)
    st.dataframe(tasks_df, use_container_width=True, hide_index=True)

    consol_df = run_query("""
        SELECT criado_em, data_visita, visitante_nome, visitante_whatsapp,
               consolidador_nome, contato_24h, status, feedback
        FROM consolidacao_visitantes
        ORDER BY criado_em DESC
        LIMIT 100
    """)
    st.dataframe(consol_df, use_container_width=True, hide_index=True)

with tab_celulas:
    st.header("Relatórios de Células")
    relatorios_df = run_query("""
        SELECT data_relatorio, nome_celula, lider_nome, presenca_membros,
               visitantes, decisoes_fe, rede, criado_em
        FROM relatorios_celulas
        ORDER BY data_relatorio DESC, criado_em DESC
        LIMIT 100
    """)
    st.dataframe(relatorios_df, use_container_width=True, hide_index=True)

    por_rede_df = run_query("""
        SELECT rede,
               COUNT(*) AS relatorios,
               SUM(presenca_membros) AS membros,
               SUM(visitantes) AS visitantes,
               SUM(decisoes_fe) AS decisoes_fe
        FROM relatorios_celulas
        GROUP BY rede
        ORDER BY relatorios DESC
    """)
    st.dataframe(por_rede_df, use_container_width=True, hide_index=True)

with tab_tarefas:
    st.header("Agenda e Tarefas Pastorais")
    tarefas_df = run_query("""
        SELECT id, status, prioridade, prazo_para, responsavel, tipo, titulo, criado_em
        FROM tarefas_pastorais
        ORDER BY
            CASE status
                WHEN 'Pendente' THEN 1
                WHEN 'Em andamento' THEN 2
                ELSE 3
            END,
            prazo_para ASC,
            prioridade ASC
        LIMIT 150
    """)
    st.dataframe(tarefas_df, use_container_width=True, hide_index=True)

    with st.form("update_task_status"):
        task_id = st.text_input("ID da tarefa")
        task_status = st.selectbox("Status da tarefa", ["Pendente", "Em andamento", "Concluida", "Cancelada", "Arquivada"])
        submitted = st.form_submit_button("Salvar status")
        if submitted and task_id:
            concluded_at = datetime.now(timezone.utc).isoformat() if task_status == "Concluida" else None
            if run_write(
                "UPDATE tarefas_pastorais SET status = ?, concluido_em = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
                (task_status, concluded_at, task_id),
            ):
                st.success("Tarefa atualizada.")

with tab_bi:
    st.header("BI Semanal")
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    by_intent_df = run_query("""
        SELECT intencao, COUNT(*) AS total
        FROM inbox_pastoral
        WHERE criado_em >= ?
        GROUP BY intencao
        ORDER BY total DESC
    """, (since,))
    st.subheader("Entradas por intenção")
    st.dataframe(by_intent_df, use_container_width=True, hide_index=True)

    by_role_df = run_query("""
        SELECT papel_responsavel, COUNT(*) AS total
        FROM inbox_pastoral
        WHERE criado_em >= ?
        GROUP BY papel_responsavel
        ORDER BY total DESC
    """, (since,))
    st.subheader("Carga por papel lógico")
    st.dataframe(by_role_df, use_container_width=True, hide_index=True)

    task_status_df = run_query("""
        SELECT status, COUNT(*) AS total
        FROM tarefas_pastorais
        WHERE criado_em >= ?
        GROUP BY status
        ORDER BY total DESC
    """, (since,))
    st.subheader("Tarefas por status")
    st.dataframe(task_status_df, use_container_width=True, hide_index=True)

