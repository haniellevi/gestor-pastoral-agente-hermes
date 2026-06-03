import sqlite3
import os
from datetime import datetime, timedelta

def initialize_database():
    db_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(db_dir, "pastoral.db")
    
    print(f"Inicializando banco de dados SQLite em: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Tabela de Compromissos (Rute)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS compromissos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        categoria TEXT CHECK (categoria IN ('Aconselhamento', 'Culto', 'Reuniao Lideranca', 'Estudo/Sermao', 'Pessoal', 'Outros')),
        data_inicio TEXT NOT NULL,
        data_fim TEXT NOT NULL,
        descricao TEXT,
        duracao_minutos INTEGER,
        google_event_id TEXT UNIQUE,
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 2. Tabela de Relatórios de Células G12 (Caleb)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS relatorios_celulas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_relatorio TEXT NOT NULL,
        nome_celula TEXT NOT NULL,
        lider_nome TEXT NOT NULL,
        presenca_membros INTEGER DEFAULT 0,
        visitantes INTEGER DEFAULT 0,
        decisoes_fe INTEGER DEFAULT 0,
        rede TEXT CHECK (rede IN ('Jovens', 'Casais', 'Homens', 'Mulheres')),
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 3. Tabela de Controle de Foco e Produtividade (Neemias)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS metas_diarias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT UNIQUE DEFAULT (date('now')),
        vitoria_1 TEXT NOT NULL,
        vitoria_1_concluida INTEGER DEFAULT 0,
        vitoria_2 TEXT NOT NULL,
        vitoria_2_concluida INTEGER DEFAULT 0,
        vitoria_3 TEXT NOT NULL,
        vitoria_3_concluida INTEGER DEFAULT 0,
        pontuacao_dia INTEGER DEFAULT 0,
        anotacoes TEXT,
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 4. Tabela de Cadastro de Conteúdo e Marketing (Barnabé)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts_conteudo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tema TEXT NOT NULL,
        tipo TEXT CHECK (tipo IN ('Reels', 'Shorts', 'Carrossel', 'Mensagem Interna', 'Outro')),
        roteiro TEXT,
        status TEXT CHECK (status IN ('Ideia', 'Roteirizado', 'Gravado', 'Postado')) DEFAULT 'Ideia',
        views INTEGER DEFAULT 0,
        engajamento INTEGER DEFAULT 0,
        data_publicacao TEXT,
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 5. Tabela de Sugestões de BI (Hermes Orquestrador)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sugestoes_bi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        origem_conversa TEXT NOT NULL,
        metrica_sugerida TEXT NOT NULL,
        justificativa TEXT NOT NULL,
        status TEXT CHECK (status IN ('Pendente', 'Implementado', 'Rejeitado')) DEFAULT 'Pendente',
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 6. Tabela de Registro de Procrastinação (Neemias)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS registro_procrastinacao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT NOT NULL,
        tarefa_adiada TEXT NOT NULL,
        distracao TEXT NOT NULL,
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 7. Tabela de Consolidação de Visitantes (Caleb)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS consolidacao_visitantes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_visita TEXT NOT NULL,
        visitante_nome TEXT NOT NULL,
        visitante_whatsapp TEXT,
        consolidador_nome TEXT NOT NULL,
        contato_24h INTEGER DEFAULT 0,
        data_contato TEXT,
        feedback TEXT,
        status TEXT CHECK (status IN ('Pendente', 'Contatado', 'Integrado', 'Desistiu')) DEFAULT 'Pendente',
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 8. Central Hermes de Membros e Atendimento (Rute)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS atendimentos_rute (
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
        atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (membro_id) REFERENCES membros(id)
    )
    """)
    
    # Inserção automática de dados de teste (Seed Data) desativada para manter dados 100% reais.
    conn.commit()
    conn.close()
    print("Banco de dados SQLite inicializado com sucesso!")


if __name__ == "__main__":
    initialize_database()
