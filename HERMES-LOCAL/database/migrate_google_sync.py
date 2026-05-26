import sqlite3
import os
import shutil

def run_migration():
    db_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(db_dir, "pastoral.db")
    backup_path = os.path.join(db_dir, "pastoral.db.bak")
    
    print(f"Iniciando migração no banco de dados SQLite em: {db_path}")
    
    # 1. Fazer backup físico antes de qualquer alteração
    print(f"Fazendo backup físico preventivo em: {backup_path}")
    shutil.copy2(db_path, backup_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 2. Verificar se a coluna google_event_id já existe
    cursor.execute("PRAGMA table_info(compromissos)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "google_event_id" in columns:
        print("A coluna 'google_event_id' já existe na tabela 'compromissos'. Nenhuma alteração é necessária.")
    else:
        print("Adicionando coluna 'google_event_id' à tabela 'compromissos'...")
        try:
            # Em SQLite, adicionar uma coluna UNIQUE diretamente com ALTER TABLE pode ter limitações
            # se já houver dados. Mas como a coluna aceita NULL (é opcional), isso é válido.
            cursor.execute("ALTER TABLE compromissos ADD COLUMN google_event_id TEXT")
            # Adiciona índice único para garantir unicidade
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_compromissos_google_event_id ON compromissos(google_event_id)")
            conn.commit()
            print("Coluna 'google_event_id' e índice único criados com sucesso!")
        except Exception as e:
            conn.rollback()
            print(f"Erro ao executar a migração: {e}")
            raise e
            
    conn.close()
    print("Migração concluída com sucesso!")

if __name__ == "__main__":
    run_migration()
