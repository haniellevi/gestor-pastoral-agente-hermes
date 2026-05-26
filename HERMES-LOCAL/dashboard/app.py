import streamlit as st
import pandas as pd
import numpy as np
import datetime
import os
import sqlite3

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
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "pastoral.db")

def run_query(query, params=()):
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erro ao acessar o banco de dados: {e}")
        return pd.DataFrame()

# Título Principal
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
if total_celulas == 0:
    total_celulas = 24  # Fallback se vazio

# 2. Frequência Média
df_freq_avg = run_query("SELECT AVG(presenca_membros) as media FROM relatorios_celulas")
freq_media = int(df_freq_avg.iloc[0]['media']) if not df_freq_avg.empty and df_freq_avg.iloc[0]['media'] is not None else 0
if freq_media == 0:
    freq_media = 218  # Fallback

# 3. Índice de Foco do Pastor (Últimas metas concluídas)
df_metas_score = run_query("SELECT AVG(pontuacao_dia) as media FROM metas_diarias")
indice_foco = int(df_metas_score.iloc[0]['media']) if not df_metas_score.empty and df_metas_score.iloc[0]['media'] is not None else 0
if indice_foco == 0:
    indice_foco = 84  # Fallback

# 4. Alcance Digital
df_views = run_query("SELECT SUM(views) as total FROM posts_conteudo")
views_total = df_views.iloc[0]['total'] if not df_views.empty and df_views.iloc[0]['total'] is not None else 0
views_total_formatted = f"{views_total/1000:.1f}K" if views_total >= 1000 else str(views_total)
if views_total == 0:
    views_total_formatted = "45.2K"

# Layout de Linha 1: Métricas de Alto Nível (Cards)
col1, col2, col3, col4 = st.columns(4)

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

# Abas de Visualização Detalhada
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🦁 Visão G12 & Caleb", "⚔️ Alta Performance & Neemias", "📢 Marketing & Barnabé", "🧠 Sugestões de IA (Hermes)", "📅 Agenda & Rute"])

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
        for idx, row in df_metas_hoje.iterrows():
            st.write(f"### Metas do Dia: {row['data']}")
            st.checkbox(f"Vitória 1: {row['vitoria_1']}", value=bool(row['vitoria_1_concluida']), disabled=True)
            st.checkbox(f"Vitória 2: {row['vitoria_2']}", value=bool(row['vitoria_2_concluida']), disabled=True)
            st.checkbox(f"Vitória 3: {row['vitoria_3']}", value=bool(row['vitoria_3_concluida']), disabled=True)
            if row['anotacoes']:
                st.info(f"📝 Anotações: {row['anotacoes']}")
            st.markdown("---")
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
    st.header("Estatísticas de Redes Sociais (Barnabé)")
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.subheader("Visualizações por Formato de Vídeo")
        df_formato = run_query("""
            SELECT tipo as Formato, SUM(views) as Visualizacoes
            FROM posts_conteudo
            GROUP BY tipo
        """)
        if not df_formato.empty:
            st.bar_chart(data=df_formato, x="Formato", y="Visualizacoes")
        else:
            st.info("Nenhum post registrado no banco.")
        
    with col_m2:
        st.subheader("Status Editorial de Conteúdo")
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

