from __future__ import annotations

from .db import execute, is_postgres


def ensure_sqlite_schema(conn) -> None:
    """Create the v2 local-dev schema when the app falls back to SQLite."""
    if is_postgres(conn):
        return

    execute(conn, """
    CREATE TABLE IF NOT EXISTS pessoas (
        id TEXT PRIMARY KEY,
        nome_completo TEXT NOT NULL,
        nome_preferido TEXT,
        tipo TEXT NOT NULL DEFAULT 'outro',
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    execute(conn, """
    CREATE TABLE IF NOT EXISTS pessoa_contatos (
        id TEXT PRIMARY KEY,
        pessoa_id TEXT NOT NULL,
        canal TEXT NOT NULL,
        valor TEXT NOT NULL,
        principal INTEGER DEFAULT 1,
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (canal, valor)
    )
    """)

    execute(conn, """
    CREATE TABLE IF NOT EXISTS event_logs (
        id TEXT PRIMARY KEY,
        provider TEXT NOT NULL DEFAULT 'botconversa',
        event_type TEXT NOT NULL DEFAULT 'mensagem',
        idempotency_key TEXT NOT NULL UNIQUE,
        external_id TEXT,
        payload TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'recebido',
        resultado TEXT,
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
        processado_em TEXT
    )
    """)

    execute(conn, """
    CREATE TABLE IF NOT EXISTS inbox_pastoral (
        id TEXT PRIMARY KEY,
        event_log_id TEXT,
        pessoa_id TEXT,
        subscriber_id INTEGER,
        nome TEXT,
        telefone TEXT,
        origem TEXT NOT NULL DEFAULT 'BotConversa',
        fluxo_origem TEXT,
        tipo_evento TEXT,
        papel_responsavel TEXT NOT NULL DEFAULT 'Rute',
        intencao TEXT NOT NULL DEFAULT 'outro',
        status TEXT NOT NULL DEFAULT 'Novo',
        nivel_urgencia TEXT NOT NULL DEFAULT 'Normal',
        prioridade INTEGER NOT NULL DEFAULT 5,
        mensagem TEXT,
        resumo TEXT,
        campos TEXT NOT NULL DEFAULT '{}',
        prazo_resposta TEXT,
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    execute(conn, """
    CREATE TABLE IF NOT EXISTS tarefas_pastorais (
        id TEXT PRIMARY KEY,
        inbox_id TEXT,
        pessoa_id TEXT,
        titulo TEXT NOT NULL,
        tipo TEXT NOT NULL,
        responsavel TEXT NOT NULL DEFAULT 'Rute',
        status TEXT NOT NULL DEFAULT 'Pendente',
        prioridade INTEGER NOT NULL DEFAULT 5,
        prazo_para TEXT,
        payload TEXT NOT NULL DEFAULT '{}',
        concluido_em TEXT,
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    execute(conn, """
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

    execute(conn, """
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

    conn.commit()
