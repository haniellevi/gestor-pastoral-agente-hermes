import argparse
import os
import time
from dataclasses import dataclass
from typing import Any

from googleapiclient.discovery import build

from google_auth import get_credentials
from supabase_client import SupabaseRestClient


FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
DEFAULT_ROOT_NAME = "IGREJA - BASE HERMES"

AREA_BY_FOLDER_NAME = {
    "00_INBOX_HERMES": "inbox",
    "01_CONHECIMENTO_OFICIAL": "conhecimento_oficial",
    "02_AGENDA_EVENTOS": "agenda_eventos",
    "03_CELULAS_G12": "celulas_g12",
    "04_FINANCEIRO": "financeiro",
    "05_SERMOES_ESTUDOS": "sermoes_estudos",
    "06_MARKETING_COMUNICACAO": "marketing_comunicacao",
    "07_ADMINISTRATIVO": "administrativo",
    "99_ARQUIVO_BRUTO": "arquivo_bruto",
}


@dataclass
class SyncStats:
    folders_seen: int = 0
    files_seen: int = 0
    sources_upserted: int = 0
    files_upserted: int = 0
    skipped: int = 0


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def build_drive_service():
    creds = get_credentials()
    return build("drive", "v3", credentials=creds)


def _escape_query_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def find_root_folder_id(service, root_name: str) -> str:
    query = (
        "mimeType = 'application/vnd.google-apps.folder' "
        f"and name = '{_escape_query_value(root_name)}' "
        "and trashed = false"
    )
    result = (
        service.files()
        .list(
            q=query,
            spaces="drive",
            pageSize=10,
            fields="files(id,name,webViewLink)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute()
    )
    folders = result.get("files", [])
    if not folders:
        raise RuntimeError(f"Pasta raiz do Drive não encontrada: {root_name}")
    if len(folders) > 1:
        print(f"Aviso: encontrei {len(folders)} pastas chamadas '{root_name}'. Usando a primeira.")
    return folders[0]["id"]


def list_children(service, folder_id: str) -> list[dict[str, Any]]:
    children: list[dict[str, Any]] = []
    page_token = None
    fields = (
        "nextPageToken,files("
        "id,name,mimeType,parents,modifiedTime,size,md5Checksum,webViewLink,trashed"
        ")"
    )
    while True:
        result = (
            service.files()
            .list(
                q=f"'{folder_id}' in parents and trashed = false",
                spaces="drive",
                pageSize=1000,
                pageToken=page_token,
                fields=fields,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        children.extend(result.get("files", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            return children


def upsert_source(
    client: SupabaseRestClient | None,
    folder: dict[str, Any],
    area: str,
    dry_run: bool,
) -> str | None:
    payload = {
        "nome": folder["name"],
        "drive_folder_id": folder["id"],
        "area": area,
        "ativo": True,
    }
    if dry_run:
        print(f"[dry-run] fonte: {payload}")
        return None
    if client is None:
        raise RuntimeError("Cliente Supabase indisponivel fora do modo dry-run.")
    rows = client.upsert("drive_sources", payload, on_conflict="drive_folder_id")
    return str(rows[0]["id"]) if rows else None


def upsert_drive_file(
    client: SupabaseRestClient | None,
    file_item: dict[str, Any],
    source_id: str | None,
    dry_run: bool,
) -> None:
    payload = {
        "drive_file_id": file_item["id"],
        "source_id": source_id,
        "nome": file_item.get("name", "sem_nome"),
        "mime_type": file_item.get("mimeType"),
        "web_view_link": file_item.get("webViewLink"),
        "modified_time": file_item.get("modifiedTime"),
        "size_bytes": int(file_item["size"]) if file_item.get("size") else None,
        "checksum": file_item.get("md5Checksum"),
    }
    if dry_run:
        print(f"[dry-run] arquivo: {payload}")
        return
    if client is None:
        raise RuntimeError("Cliente Supabase indisponivel fora do modo dry-run.")
    client.upsert("drive_files", payload, on_conflict="drive_file_id")


def register_log(
    client: SupabaseRestClient | None,
    status: str,
    stats: SyncStats,
    details: str | None = None,
) -> None:
    client.insert(
        "integration_logs",
        {
            "integracao": "google_drive",
            "acao": "sync_index",
            "payload": {
                "folders_seen": stats.folders_seen,
                "files_seen": stats.files_seen,
                "sources_upserted": stats.sources_upserted,
                "files_upserted": stats.files_upserted,
                "skipped": stats.skipped,
            },
            "status": status,
            "resultado": details,
        },
    )


def sync_folder_tree(
    service,
    client: SupabaseRestClient,
    folder_id: str,
    active_source_id: str | None,
    stats: SyncStats,
    dry_run: bool,
) -> None:
    for item in list_children(service, folder_id):
        if item.get("mimeType") == FOLDER_MIME_TYPE:
            stats.folders_seen += 1
            area = AREA_BY_FOLDER_NAME.get(item.get("name", ""))
            next_source_id = active_source_id
            if area:
                next_source_id = upsert_source(client, item, area, dry_run)
                stats.sources_upserted += 1
            sync_folder_tree(service, client, item["id"], next_source_id, stats, dry_run)
            continue

        stats.files_seen += 1
        if not active_source_id:
            stats.skipped += 1
            print(f"Arquivo fora de uma pasta de área mapeada, ignorado: {item.get('name')}")
            continue
        upsert_drive_file(client, item, active_source_id, dry_run)
        stats.files_upserted += 1


def run_once(dry_run: bool = False) -> SyncStats:
    root_id = _env("GOOGLE_DRIVE_ROOT_FOLDER_ID") or _env("HERMES_DRIVE_ROOT_ID")
    root_name = _env("HERMES_DRIVE_ROOT_NAME", DEFAULT_ROOT_NAME)

    service = build_drive_service()
    client = None if dry_run else SupabaseRestClient()

    if not root_id:
        root_id = find_root_folder_id(service, root_name)

    stats = SyncStats()
    try:
        sync_folder_tree(service, client, root_id, None, stats, dry_run)
        if not dry_run:
            register_log(client, "sucesso", stats, "Índice do Google Drive sincronizado.")
    except Exception as exc:
        if not dry_run:
            register_log(client, "erro", stats, str(exc))
        raise

    print(
        "Sync Drive concluído: "
        f"{stats.folders_seen} pastas, "
        f"{stats.files_upserted}/{stats.files_seen} arquivos indexados, "
        f"{stats.skipped} ignorados."
    )
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Sincroniza o índice do Google Drive com o Supabase.")
    parser.add_argument("--dry-run", action="store_true", help="Mostra o que seria sincronizado sem gravar.")
    parser.add_argument("--loop", action="store_true", help="Executa em loop para uso como worker.")
    parser.add_argument("--interval-minutes", type=int, default=15, help="Intervalo do loop em minutos.")
    args = parser.parse_args()

    while True:
        run_once(dry_run=args.dry_run)
        if not args.loop:
            break
        time.sleep(max(1, args.interval_minutes) * 60)


if __name__ == "__main__":
    main()
