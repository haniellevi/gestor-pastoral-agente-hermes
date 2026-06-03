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
    
    # Inserção automática de dados fictícios para teste desativada para manter dados reais.
    conn.commit()
    conn.close()
    print("Migração concluída com sucesso!")

if __name__ == "__main__":
    run_migration()
