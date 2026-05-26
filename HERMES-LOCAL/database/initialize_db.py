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
    
    # Inserindo dados iniciais (Seed Data) se as tabelas estiverem vazias
    
    # Seed Compromissos
    cursor.execute("SELECT COUNT(*) FROM compromissos")
    if cursor.fetchone()[0] == 0:
        hoje = datetime.now()
        amanha = hoje + timedelta(days=1)
        dados_compromissos = [
            ('Aconselhamento Lucas e Ana', 'Aconselhamento', hoje.strftime('%Y-%m-%d 14:00:00'), hoje.strftime('%Y-%m-%d 15:30:00'), 'Aconselhamento sobre vida familiar e liderança de célula.', 90),
            ('Reunião de Liderança G12', 'Reuniao Lideranca', hoje.strftime('%Y-%m-%d 19:30:00'), hoje.strftime('%Y-%m-%d 21:00:00'), 'Reunião mensal com os 12 da primeira geração.', 90),
            ('Estudo da Palavra e Esboço', 'Estudo/Sermao', amanha.strftime('%Y-%m-%d 09:00:00'), amanha.strftime('%Y-%m-%d 11:30:00'), 'Preparação do esboço para o culto de Domingo.', 150),
            ('Culto de Celebração Domingo', 'Culto', (hoje + timedelta(days=5)).strftime('%Y-%m-%d 18:00:00'), (hoje + timedelta(days=5)).strftime('%Y-%m-%d 20:00:00'), 'Pregação principal da série sobre Neemias.', 120)
        ]
        cursor.executemany("""
        INSERT INTO compromissos (titulo, categoria, data_inicio, data_fim, descricao, duracao_minutos)
        VALUES (?, ?, ?, ?, ?, ?)
        """, dados_compromissos)
        print("Dados iniciais de compromissos inseridos.")
        
    # Seed Relatorios Celulas
    cursor.execute("SELECT COUNT(*) FROM relatorios_celulas")
    if cursor.fetchone()[0] == 0:
        dados_celulas = [
            ('2026-05-18', 'Shammah', 'Lucas Silva', 10, 1, 1, 'Jovens'),
            ('2026-05-19', 'Ebenézer', 'Ana Santos', 8, 2, 0, 'Casais'),
            ('2026-05-20', 'Peniel', 'Marcos Oliveira', 12, 0, 2, 'Homens'),
            ('2026-05-21', 'Manassés', 'Gabriel Souza', 7, 3, 1, 'Jovens'),
            ('2026-05-22', 'Sara', 'Carla Lima', 9, 2, 0, 'Mulheres'),
            ('2026-05-25', 'Shammah', 'Lucas Silva', 12, 2, 1, 'Jovens'),
            ('2026-05-25', 'Ebenézer', 'Ana Santos', 9, 1, 0, 'Casais')
        ]
        cursor.executemany("""
        INSERT INTO relatorios_celulas (data_relatorio, nome_celula, lider_nome, presenca_membros, visitantes, decisoes_fe, rede)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, dados_celulas)
        print("Dados iniciais de relatórios de células inseridos.")
        
    # Seed Metas Diarias (Neemias)
    cursor.execute("SELECT COUNT(*) FROM metas_diarias")
    if cursor.fetchone()[0] == 0:
        dados_metas = [
            ((datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'), 'Gravar Reels sobre G12', 1, 'Visitar célula dos Jovens', 1, 'Estudar 1h livro de Castellanos', 1, 100, 'Dia excelente e focado.'),
            ((datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'), 'Preparar esboço da mensagem', 1, 'Aconselhar casal Marcos e Júlia', 0, 'Ler 30min sobre liderança', 1, 60, 'O aconselhamento foi adiado pelo casal.'),
            (datetime.now().strftime('%Y-%m-%d'), 'Fazer caminhada matinal', 1, 'Reunião com liderança de rede', 1, 'Finalizar roteiros com Barnabé', 1, 100, 'Meta de saúde e ministério batidas.')
        ]
        cursor.executemany("""
        INSERT INTO metas_diarias (data, vitoria_1, vitoria_1_concluida, vitoria_2, vitoria_2_concluida, vitoria_3, vitoria_3_concluida, pontuacao_dia, anotacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, dados_metas)
        print("Dados iniciais de metas diárias inseridos.")
        
    # Seed Posts Conteudo (Barnabe)
    cursor.execute("SELECT COUNT(*) FROM posts_conteudo")
    if cursor.fetchone()[0] == 0:
        dados_posts = [
            ('Por que líderes G12 não agem sozinhos?', 'Reels', 'Roteiro pronto sobre descentralização e delegação baseado em Jesus e seus 12.', 'Postado', 15200, 480, '2026-05-15'),
            ('O que a muralha de Neemias nos ensina sobre limites?', 'Shorts', 'Vídeo rápido sobre foco e dizer não para distrações.', 'Postado', 8400, 230, '2026-05-18'),
            ('Os 3 segredos para um aconselhamento pastoral eficaz', 'Carrossel', 'Infográfico detalhado contendo pautas de aconselhamento.', 'Roteirizado', 0, 0, None),
            ('Como vencer o desânimo espiritual na segunda-feira', 'Mensagem Interna', 'Texto motivacional curto para grupos de WhatsApp.', 'Postado', 400, 50, '2026-05-25'),
            ('Princípios bíblicos da Conquista Financeira', 'Reels', 'Roteiro sobre mordomia cristã e metas financeiras.', 'Ideia', 0, 0, None)
        ]
        cursor.executemany("""
        INSERT INTO posts_conteudo (tema, tipo, roteiro, status, views, engajamento, data_publicacao)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, dados_posts)
        print("Dados iniciais de conteúdo editorial inseridos.")
        
    # Seed Sugestoes BI (Hermes)
    cursor.execute("SELECT COUNT(*) FROM sugestoes_bi")
    if cursor.fetchone()[0] == 0:
        dados_sugestoes = [
            ('Aconselhamentos sobre casais', 'Índice de Saúde Familiar (Frequência em Casais)', 'Detecção de aumento de 40% nas menções de problemas conjugais nos aconselhamentos.', 'Pendente'),
            ('Reuniões de Jovens', 'Taxa de Retenção de Jovens (Batismos/Célula)', 'Queda de 15% na retenção de jovens convertidos nas primeiras 4 semanas.', 'Implementado'),
            ('Escola de Líderes', 'Tempo Médio para Formação de Líder (Meses)', 'Análise de gargalo no tempo de conclusão do módulo 3 da Escola.', 'Pendente')
        ]
        cursor.executemany("""
        INSERT INTO sugestoes_bi (origem_conversa, metrica_sugerida, justificativa, status)
        VALUES (?, ?, ?, ?)
        """, dados_sugestoes)
        print("Dados iniciais de sugestões de BI inseridos.")
        
    # Seed Registro Procrastinação (Neemias)
    cursor.execute("SELECT COUNT(*) FROM registro_procrastinacao")
    if cursor.fetchone()[0] == 0:
        dados_procrastinacao = [
            ('2026-05-22', 'Preparar sermão de Domingo', 'Redes Sociais e e-mails administrativos'),
            ('2026-05-24', 'Gravação dos Reels semanais', 'Urgência administrativa na secretaria'),
            ('2026-05-25', 'Estudo inegociável de 1h', 'Cansaço físico e reuniões prolongadas')
        ]
        cursor.executemany("""
        INSERT INTO registro_procrastinacao (data, tarefa_adiada, distracao)
        VALUES (?, ?, ?)
        """, dados_procrastinacao)
        print("Dados iniciais de procrastinação inseridos.")
        
    # Seed Consolidação Visitantes (Caleb)
    cursor.execute("SELECT COUNT(*) FROM consolidacao_visitantes")
    if cursor.fetchone()[0] == 0:
        dados_visitantes = [
            ('2026-05-23', 'Roberto Medeiros', '11999998888', 'Discipulo Thiago', 1, '2026-05-24', 'Ficou muito feliz com o contato rápido, prometeu ir na célula amanhã', 'Contatado'),
            ('2026-05-24', 'Juliana Rezende', '11988887777', 'Líder Patrícia', 1, '2026-05-25', 'Contato feito dentro do prazo. Pediu oração pela mãe doente.', 'Contatado'),
            ('2026-05-25', 'Lucas Nogueira', '11977776666', 'Discipulo Carlos', 0, None, 'Aguardando contato do consolidador', 'Pendente')
        ]
        cursor.executemany("""
        INSERT INTO consolidacao_visitantes (data_visita, visitante_nome, visitante_whatsapp, consolidador_nome, contato_24h, data_contato, feedback, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, dados_visitantes)
        print("Dados iniciais de consolidação de visitantes inseridos.")
        
    conn.commit()
    conn.close()
    print("Banco de dados SQLite inicializado com sucesso!")


if __name__ == "__main__":
    initialize_database()
