"""
Migração: Cria as tabelas de eventos de mídia, áudio e documento no Supabase (Postgres).
"""
import os
import psycopg2
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


def load_env() -> dict[str, str]:
    values = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip()
    return values


def migrate_supabase():
    env_vars = load_env()
    db_url = env_vars.get("SUPABASE_DB_URL")
    if not db_url or "SUA_SENHA_AQUI" in db_url:
        print("SUPABASE_DB_URL não configurada no .env. Ignorando migração do Supabase.")
        return

    print("Conectando ao Supabase (Postgres)...")
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    # Habilita uuid-ossp se não estiver habilitado
    print("Habilitando extensão uuid-ossp...")
    cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")

    print("Criando tabela public.eventos_midia...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.eventos_midia (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
            criado_em TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    print("Criando tabela public.eventos_audio...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.eventos_audio (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            subscriber_id INTEGER,
            nome TEXT,
            texto_original TEXT,
            provider TEXT DEFAULT 'elevenlabs',
            duracao_segundos INTEGER,
            status TEXT DEFAULT 'pendente',
            erro TEXT,
            criado_em TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    print("Criando tabela public.eventos_documento...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.eventos_documento (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            subscriber_id INTEGER,
            nome TEXT,
            telefone TEXT,
            tipo_documento TEXT,
            total_chars INTEGER,
            status TEXT DEFAULT 'pendente',
            erro TEXT,
            criado_em TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    # Índices
    print("Criando índices de mídia...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eventos_midia_subscriber ON public.eventos_midia(subscriber_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eventos_midia_data ON public.eventos_midia(criado_em);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eventos_midia_tipo ON public.eventos_midia(tipo_midia);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eventos_audio_subscriber ON public.eventos_audio(subscriber_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eventos_documento_subscriber ON public.eventos_documento(subscriber_id);")

    conn.commit()
    conn.close()
    print("Tabelas de mídia criadas com sucesso no Supabase!")


if __name__ == "__main__":
    migrate_supabase()
