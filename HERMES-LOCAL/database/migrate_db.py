import sqlite3
import os

def run_migration():
    db_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(db_dir, "pastoral.db")
    
    print(f"Executando migração no banco de dados SQLite: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Criar tabela de registro de procrastinação (Neemias)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS registro_procrastinacao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT NOT NULL,
        tarefa_adiada TEXT NOT NULL,
        distracao TEXT NOT NULL,
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("Tabela 'registro_procrastinacao' verificada/criada.")
    
    # 2. Criar tabela de consolidação de visitantes (Caleb)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS consolidacao_visitantes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_visita TEXT NOT NULL,
        visitante_nome TEXT NOT NULL,
        visitante_whatsapp TEXT,
        consolidador_nome TEXT NOT NULL,
        contato_24h INTEGER DEFAULT 0, -- 0 = Não, 1 = Sim
        data_contato TEXT,
        feedback TEXT,
        status TEXT CHECK (status IN ('Pendente', 'Contatado', 'Integrado', 'Desistiu')) DEFAULT 'Pendente',
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("Tabela 'consolidacao_visitantes' verificada/criada.")
    
    # Adicionar dados fictícios para teste se estiverem vazias
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
        print("Dados fictícios de procrastinação semeados.")
        
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
        print("Dados fictícios de consolidação de visitantes semeados.")
        
    conn.commit()
    conn.close()
    print("Migração concluída com sucesso!")

if __name__ == "__main__":
    run_migration()
