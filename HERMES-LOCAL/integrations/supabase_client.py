import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SupabaseConfigError(RuntimeError):
    pass


class SupabaseRequestError(RuntimeError):
    pass


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


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


def load_supabase_settings() -> tuple[str, str]:
    env_file_values = _load_env_file(_project_root() / "config" / "integrations.env")

    url = os.getenv("SUPABASE_URL", "").strip() or env_file_values.get("SUPABASE_URL", "").strip()
    service_key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or env_file_values.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )

    if not url or not service_key:
        raise SupabaseConfigError("SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY não configurados.")

    return url.rstrip("/"), service_key


def is_supabase_configured() -> bool:
    try:
        load_supabase_settings()
        return True
    except SupabaseConfigError:
        return False


class SupabaseRestClient:
    def __init__(self, url: str | None = None, service_key: str | None = None):
        loaded_url, loaded_key = load_supabase_settings()
        self.url = (url or loaded_url).rstrip("/")
        self.service_key = service_key or loaded_key

    @property
    def headers(self) -> dict[str, str]:
        return {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        path: str,
        payload: Any | None = None,
        prefer: str | None = "return=representation",
    ) -> Any:
        url = f"{self.url}/rest/v1{path}"
        data = None
        headers = dict(self.headers)
        if prefer:
            headers["Prefer"] = prefer
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else None
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise SupabaseRequestError(f"Supabase HTTP {exc.code}: {body[:1000]}") from exc
        except urllib.error.URLError as exc:
            raise SupabaseRequestError(f"Erro de conexão com Supabase: {exc}") from exc

    def insert(self, table: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        encoded_table = urllib.parse.quote(table, safe="")
        result = self._request("POST", f"/{encoded_table}", payload)
        return result if isinstance(result, list) else []

    def upsert(
        self,
        table: str,
        payload: dict[str, Any],
        on_conflict: str,
    ) -> list[dict[str, Any]]:
        encoded_table = urllib.parse.quote(table, safe="")
        encoded_conflict = urllib.parse.quote(on_conflict, safe=",")
        result = self._request(
            "POST",
            f"/{encoded_table}?on_conflict={encoded_conflict}",
            payload,
            prefer="resolution=merge-duplicates,return=representation",
        )
        return result if isinstance(result, list) else []

    def select(self, table: str, query: str = "select=*") -> list[dict[str, Any]]:
        encoded_table = urllib.parse.quote(table, safe="")
        result = self._request("GET", f"/{encoded_table}?{query}", prefer=None)
        return result if isinstance(result, list) else []

    def patch_by_id(self, table: str, row_id: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        encoded_table = urllib.parse.quote(table, safe="")
        encoded_id = urllib.parse.quote(row_id, safe="")
        result = self._request("PATCH", f"/{encoded_table}?id=eq.{encoded_id}", payload)
        return result if isinstance(result, list) else []


def register_webhook_event(
    provider: str,
    event_type: str,
    payload: dict[str, Any],
    external_id: str | None = None,
) -> str | None:
    client = SupabaseRestClient()
    rows = client.insert(
        "webhook_events",
        {
            "provider": provider,
            "event_type": event_type,
            "external_id": external_id,
            "payload": payload,
            "status": "recebido",
        },
    )
    if rows:
        return str(rows[0].get("id"))
    return None


def update_webhook_event_status(
    event_id: str | None,
    status: str,
    resultado: str | None = None,
) -> None:
    if not event_id:
        return
    payload: dict[str, Any] = {
        "status": status,
        "processado_em": datetime.now(timezone.utc).isoformat(),
    }
    if resultado:
        payload["resultado"] = resultado
    SupabaseRestClient().patch_by_id("webhook_events", event_id, payload)
