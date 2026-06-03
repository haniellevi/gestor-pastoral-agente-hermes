import psycopg2
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_env_value(key):
    env_value = os.getenv(key)
    if env_value:
        return env_value

    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return None

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() == key:
            return value.strip().strip('"').strip("'")
    return None

def main():
    db_url = load_env_value("SUPABASE_DB_URL")
    if not db_url:
        print("SUPABASE_DB_URL não configurada no ambiente ou no arquivo .env.")
        sys.exit(1)

    safe_url = db_url.split("@", 1)[-1] if "@" in db_url else "URL configurada"
    print(f"Testando conexão PostgreSQL/Supabase em: {safe_url}")

    try:
        conn = psycopg2.connect(db_url, connect_timeout=10)
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        conn.close()
        print("--> CONEXÃO OK.")
    except Exception as e:
        print(f"--> FALHA na conexão Supabase/PostgreSQL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
