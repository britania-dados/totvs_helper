"""Persist script generation history under %APPDATA%/TotvsHelper."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from totvs_helper.infra.odbc_client import FieldMeta
from totvs_helper.services.script_generator import GeneratedScripts
from totvs_helper.ui.preferences import preferences_path
from totvs_helper.ui.state import HistoryEntry

logger = logging.getLogger(__name__)

MAX_PERSISTED_HISTORY = 20
_HISTORY_VERSION = 1


def history_path() -> Path:
    return preferences_path().parent / "history.json"


def _scripts_to_dict(scripts: GeneratedScripts) -> dict[str, str]:
    return {
        "query_etl": scripts.query_etl,
        "ddl_create": scripts.ddl_create,
        "script_delete": scripts.script_delete,
        "script_update": scripts.script_update,
        "differential": scripts.differential,
    }


def _field_to_dict(field: FieldMeta) -> dict[str, Any]:
    return {
        "name": field.name,
        "data_type": field.data_type,
        "width": field.width,
        "decimals": field.decimals,
        "fetch_datatype": field.fetch_datatype,
    }


def _field_from_dict(data: dict[str, Any]) -> Optional[FieldMeta]:
    try:
        return FieldMeta(
            name=str(data["name"]),
            data_type=str(data.get("data_type", "")),
            width=int(data.get("width", 0) or 0),
            decimals=int(data.get("decimals", 0) or 0),
            fetch_datatype=str(data.get("fetch_datatype", "")),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _fields_from_dict_list(items: Any) -> list[FieldMeta]:
    if not isinstance(items, list):
        return []
    fields: list[FieldMeta] = []
    for item in items:
        if isinstance(item, dict):
            field = _field_from_dict(item)
            if field is not None:
                fields.append(field)
    return fields


def _scripts_from_dict(data: dict[str, Any]) -> GeneratedScripts:
    return GeneratedScripts(
        query_etl=str(data.get("query_etl", "")),
        ddl_create=str(data.get("ddl_create", "")),
        script_delete=str(data.get("script_delete", "")),
        script_update=str(data.get("script_update", "")),
        differential=str(data.get("differential", "")),
    )


def entry_to_dict(entry: HistoryEntry) -> dict[str, Any]:
    return {
        "dsn": entry.dsn,
        "table": entry.table,
        "include_free_fields": entry.include_free_fields,
        "multi_company": entry.multi_company,
        "ecom_keys": entry.ecom_keys,
        "created_at": entry.created_at.isoformat(),
        "scripts": _scripts_to_dict(entry.scripts),
        "table_fields": [_field_to_dict(f) for f in entry.table_fields],
        "table_pk_fields": list(entry.table_pk_fields),
    }


def entry_from_dict(data: dict[str, Any]) -> Optional[HistoryEntry]:
    try:
        created_raw = data.get("created_at")
        if isinstance(created_raw, str):
            created_at = datetime.fromisoformat(created_raw)
        else:
            created_at = datetime.now()
        scripts_raw = data.get("scripts")
        if not isinstance(scripts_raw, dict):
            return None
        return HistoryEntry(
            dsn=str(data.get("dsn", "")),
            table=str(data.get("table", "")),
            include_free_fields=bool(data.get("include_free_fields", True)),
            multi_company=bool(data.get("multi_company", True)),
            ecom_keys=bool(data.get("ecom_keys", False)),
            scripts=_scripts_from_dict(scripts_raw),
            table_fields=_fields_from_dict_list(data.get("table_fields")),
            table_pk_fields=[
                str(pk) for pk in data.get("table_pk_fields", []) if pk
            ],
            created_at=created_at,
        )
    except (TypeError, ValueError, KeyError):
        return None


def load_history_entries() -> List[HistoryEntry]:
    path = history_path()
    if not path.exists():
        return []

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning("Historico invalido; ignorando.", exc_info=True)
        return []

    items = raw.get("entries", []) if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        return []

    entries: List[HistoryEntry] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        entry = entry_from_dict(item)
        if entry is not None and entry.table:
            entries.append(entry)

    return _dedupe_entries(entries)


def _dedupe_entries(entries: List[HistoryEntry]) -> List[HistoryEntry]:
    """Keep one entry per DSN+table (newest timestamp)."""
    by_key: dict[tuple[str, str], HistoryEntry] = {}
    for entry in entries:
        key = entry.history_key
        current = by_key.get(key)
        if current is None or entry.created_at > current.created_at:
            by_key[key] = entry
    ordered = sorted(by_key.values(), key=lambda e: e.created_at, reverse=True)
    return ordered[:MAX_PERSISTED_HISTORY]


def save_history_entries(entries: List[HistoryEntry]) -> None:
    path = history_path()
    payload = {
        "version": _HISTORY_VERSION,
        "entries": [entry_to_dict(entry) for entry in entries[:MAX_PERSISTED_HISTORY]],
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError:
        logger.warning("Nao foi possivel salvar historico.", exc_info=True)
