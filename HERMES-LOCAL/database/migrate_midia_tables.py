"""
Migração: Cria as tabelas de eventos de mídia, áudio e documento.
Executar: python database/migrate_midia_tables.py
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "database" / "pastoral.db"


def criar_tabelas():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabela: eventos_midia
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eventos_midia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscriber_id INTEGER,
            telefone TEXT,
            nome TEXT,
            tipo_midia TEXT,
            acao TEXT,
            ultima_intencao TEXT,
            ultimo_fluxo_encaminhado TEXT,
            resumo_ia TEXT,
            nivel_urgencia TEXT DEFAULT 'Normal',
            status_atendimento TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabela: eventos_audio
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eventos_audio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscriber_id INTEGER,
            nome TEXT,
            texto_original TEXT,
            provider TEXT DEFAULT 'elevenlabs',
            duracao_segundos INTEGER,
            status TEXT DEFAULT 'pendente',
            erro TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabela: eventos_documento
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eventos_documento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscriber_id INTEGER,
            nome TEXT,
            telefone TEXT,
            tipo_documento TEXT,
            total_chars INTEGER,
            status TEXT DEFAULT 'pendente',
            erro TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Índices
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eventos_midia_subscriber ON eventos_midia(subscriber_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eventos_midia_data ON eventos_midia(criado_em)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eventos_midia_tipo ON eventos_midia(tipo_midia)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eventos_audio_subscriber ON eventos_audio(subscriber_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eventos_documento_subscriber ON eventos_documento(subscriber_id)")

    conn.commit()

    # Lista todas as tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    return tables


if __name__ == "__main__":
    print("Criando tabelas de mídia...")
    tables = criar_tabelas()
    print("Tabelas existentes:")
    for t in tables:
        print(f"  - {t}")
    print("\nMigração concluída com sucesso!")
