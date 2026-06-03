import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


DEFAULT_BASE_URL = "https://backend.botconversa.com.br/api/v1/webhook"


class BotConversaError(RuntimeError):
    pass


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_botconversa_settings() -> tuple[str, str]:
    api_key = os.getenv("BOTCONVERSA_API_KEY", "").strip()
    base_url = os.getenv("BOTCONVERSA_BASE_URL", "").strip() or DEFAULT_BASE_URL

    env_path = _project_root() / "config" / "integrations.env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key == "BOTCONVERSA_API_KEY" and not api_key:
                api_key = value
            elif key == "BOTCONVERSA_BASE_URL" and value:
                base_url = value.rstrip("/")

    if not api_key:
        raise BotConversaError("BOTCONVERSA_API_KEY não configurada.")

    return api_key, base_url.rstrip("/")


class BotConversaClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        loaded_key, loaded_base = load_botconversa_settings()
        self.api_key = api_key or loaded_key
        self.base_url = (base_url or loaded_base).rstrip("/")

    @property
    def headers(self) -> dict[str, str]:
        return {"API-KEY": self.api_key}

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict | list:
        url = f"{self.base_url}{path}"
        data = None
        headers = dict(self.headers)
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = resp.read().decode("utf-8")
                if not body:
                    return {}
                return json.loads(body)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise BotConversaError(f"BotConversa HTTP {exc.code}: {body[:500]}") from exc
        except urllib.error.URLError as exc:
            raise BotConversaError(f"Erro de conexão com BotConversa: {exc}") from exc

    def _get(self, path: str) -> dict | list:
        return self._request("GET", path)

    def _post(self, path: str, payload: dict | None = None) -> dict | list:
        return self._request("POST", path, payload or {})

    def _delete(self, path: str, payload: dict | None = None) -> dict | list:
        return self._request("DELETE", path, payload or {})

    def list_paginated(self, path: str) -> list[dict]:
        results: list[dict] = []
        page = 1
        while True:
            separator = "&" if "?" in path else "?"
            data = self._get(f"{path}{separator}page={page}")
            if isinstance(data, list):
                results.extend(data)
                break
            results.extend(data.get("results", []))
            if not data.get("next"):
                break
            page += 1
        return results

    def list_subscribers(self) -> list[dict]:
        return self.list_paginated("/subscribers/")

    def list_tags(self) -> list[dict]:
        data = self._get("/tags/")
        return data if isinstance(data, list) else data.get("results", [])

    def list_flows(self) -> list[dict]:
        data = self._get("/flows/")
        return data if isinstance(data, list) else data.get("results", [])

    def list_sequences(self) -> list[dict]:
        data = self._get("/sequences/")
        return data if isinstance(data, list) else data.get("results", [])

    def list_campaigns(self) -> list[dict]:
        data = self._get("/campaigns/")
        return data if isinstance(data, list) else data.get("results", [])

    def list_custom_fields(self) -> list[dict]:
        data = self._get("/custom_fields/")
        return data if isinstance(data, list) else data.get("results", [])

    def find_subscriber_by_phone(self, phone: str) -> dict:
        phone_digits = "".join(ch for ch in str(phone) if ch.isdigit())
        encoded = urllib.parse.quote(phone_digits)
        data = self._get(f"/subscriber/get_by_phone/{encoded}/")
        return data if isinstance(data, dict) else {}

    def create_subscriber(
        self,
        phone: str,
        first_name: str,
        last_name: str = "",
        has_opt_in_whatsapp: bool = True,
    ) -> dict:
        payload = {
            "phone": "".join(ch for ch in str(phone) if ch.isdigit()),
            "first_name": first_name,
            "last_name": last_name,
            "has_opt_in_whatsapp": has_opt_in_whatsapp,
        }
        data = self._post("/subscriber/", payload)
        return data if isinstance(data, dict) else {}

    def send_message(self, subscriber_id: int, message: str, message_type: str = "text") -> dict:
        data = self._post(
            f"/subscriber/{subscriber_id}/send_message/",
            {"type": message_type, "value": message},
        )
        return data if isinstance(data, dict) else {}

    def send_flow(self, subscriber_id: int, flow_id: int) -> dict:
        data = self._post(f"/subscriber/{subscriber_id}/send_flow/", {"flow": int(flow_id)})
        return data if isinstance(data, dict) else {}

    def add_tag(self, subscriber_id: int, tag_id: int) -> dict:
        data = self._post(f"/subscriber/{subscriber_id}/tags/{tag_id}/")
        return data if isinstance(data, dict) else {}

    def remove_tag(self, subscriber_id: int, tag_id: int) -> dict:
        data = self._delete(f"/subscriber/{subscriber_id}/tags/{tag_id}/")
        return data if isinstance(data, dict) else {}

    def set_custom_field(self, subscriber_id: int, custom_field_id: int, value: str) -> dict:
        data = self._post(
            f"/subscriber/{subscriber_id}/custom_fields/{custom_field_id}/",
            {"value": str(value)},
        )
        return data if isinstance(data, dict) else {}

    def clear_custom_field(self, subscriber_id: int, custom_field_id: int) -> dict:
        data = self._delete(f"/subscriber/{subscriber_id}/custom_fields/{custom_field_id}/")
        return data if isinstance(data, dict) else {}

    def add_to_sequence(self, subscriber_id: int, sequence_id: int) -> dict:
        data = self._post(f"/subscriber/{subscriber_id}/sequences/{sequence_id}/")
        return data if isinstance(data, dict) else {}

    def remove_from_sequence(self, subscriber_id: int, sequence_id: int) -> dict:
        data = self._delete(f"/subscriber/{subscriber_id}/sequences/{sequence_id}/")
        return data if isinstance(data, dict) else {}

    def add_to_campaign(self, subscriber_id: int, campaign_id: int) -> dict:
        data = self._post(f"/subscriber/{subscriber_id}/campaigns/{campaign_id}/")
        return data if isinstance(data, dict) else {}

    def remove_from_campaign(self, subscriber_id: int, campaign_id: int) -> dict:
        data = self._delete(f"/subscriber/{subscriber_id}/campaigns/{campaign_id}/")
        return data if isinstance(data, dict) else {}

    def change_conversation_status(
        self,
        subscriber_id: int,
        open_conversation: bool,
        manager: int | None = None,
    ) -> dict:
        payload: dict[str, object] = {"open_conversation": bool(open_conversation)}
        if manager is not None:
            payload["manager"] = int(manager)
        data = self._post(f"/subscriber/{subscriber_id}/change_conversation_status/", payload)
        return data if isinstance(data, dict) else {}


if __name__ == "__main__":
    client = BotConversaClient()
    print(json.dumps({
        "tags": len(client.list_tags()),
        "flows": len(client.list_flows()),
        "sequences": len(client.list_sequences()),
        "custom_fields": len(client.list_custom_fields()),
        "subscribers": len(client.list_subscribers()),
    }, ensure_ascii=False, indent=2))
