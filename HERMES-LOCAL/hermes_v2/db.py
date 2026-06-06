from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Iterable

import psycopg2


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "database" / "pastoral.db"


def _load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def load_settings() -> dict[str, str]:
    values: dict[str, str] = {}
    values.update(_load_env_file(PROJECT_ROOT / ".env"))
    values.update(_load_env_file(PROJECT_ROOT / "config" / "integrations.env"))
    values.update({key: value for key, value in os.environ.items() if key.startswith(("SUPABASE_", "HERMES_"))})
    return values


def get_connection():
    settings = load_settings()
    db_url = settings.get("SUPABASE_DB_URL", "").strip()
    if db_url and "SUA_SENHA_AQUI" not in db_url and "SENHA_DO_BANCO" not in db_url:
        return psycopg2.connect(db_url)

    sqlite_path = settings.get("HERMES_SQLITE_DB_PATH", "").strip()
    conn = sqlite3.connect(sqlite_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def is_postgres(conn) -> bool:
    return not isinstance(conn, sqlite3.Connection)


def adapt_query(conn, query: str) -> str:
    if is_postgres(conn):
        return query.replace("?", "%s")
    return query.replace("%s", "?")


def execute(conn, query: str, params: Iterable[Any] = ()):
    cursor = conn.cursor()
    cursor.execute(adapt_query(conn, query), tuple(params))
    return cursor


def fetch_one(conn, query: str, params: Iterable[Any] = ()) -> dict[str, Any] | None:
    cursor = execute(conn, query, params)
    row = cursor.fetchone()
    if not row:
        return None
    if isinstance(row, sqlite3.Row):
        return dict(row)
    cols = [desc[0] for desc in cursor.description]
    return dict(zip(cols, row))


def fetch_all(conn, query: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    cursor = execute(conn, query, params)
    rows = cursor.fetchall()
    if not rows:
        return []
    if isinstance(rows[0], sqlite3.Row):
        return [dict(row) for row in rows]
    cols = [desc[0] for desc in cursor.description]
    return [dict(zip(cols, row)) for row in rows]
