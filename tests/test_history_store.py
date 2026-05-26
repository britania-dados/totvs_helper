"""Tests for persisted generation history."""

from __future__ import annotations

import json
from datetime import datetime

from totvs_helper.services.script_generator import GeneratedScripts
from totvs_helper.infra.odbc_client import FieldMeta
from totvs_helper.ui.history_store import (
    MAX_PERSISTED_HISTORY,
    _dedupe_entries,
    entry_from_dict,
    entry_to_dict,
    load_history_entries,
    save_history_entries,
)
from totvs_helper.ui.state import HistoryEntry, SessionHistory


def _sample_scripts() -> GeneratedScripts:
    return GeneratedScripts(
        query_etl="SELECT 1",
        ddl_create="CREATE TABLE t (id int)",
        script_delete="DELETE FROM t",
        script_update="UPDATE t SET id=1",
        differential="a || b",
    )


def test_entry_roundtrip() -> None:
    entry = HistoryEntry(
        dsn="EMS2CORP",
        table="emitente",
        include_free_fields=True,
        multi_company=False,
        ecom_keys=True,
        scripts=_sample_scripts(),
        created_at=datetime(2026, 5, 26, 16, 0),
    )
    restored = entry_from_dict(entry_to_dict(entry))
    assert restored is not None
    assert restored.table == "emitente"
    assert restored.ecom_keys is True
    assert restored.scripts.query_etl == "SELECT 1"


def test_dedupe_entries_keeps_newest_per_table() -> None:
    scripts = _sample_scripts()
    older = HistoryEntry(
        dsn="EMS2CORP",
        table="emitente",
        include_free_fields=True,
        multi_company=True,
        scripts=scripts,
        created_at=datetime(2026, 5, 26, 17, 0),
    )
    newer = HistoryEntry(
        dsn="EMS2CORP",
        table="emitente",
        include_free_fields=False,
        multi_company=False,
        scripts=scripts,
        created_at=datetime(2026, 5, 26, 18, 0),
    )
    result = _dedupe_entries([older, newer, older])
    assert len(result) == 1
    assert result[0].include_free_fields is False


def test_entry_roundtrip_with_table_fields() -> None:
    field = FieldMeta("codigo", "integer", 4, 0, "integer")
    entry = HistoryEntry(
        dsn="EMS2CORP",
        table="emitente",
        include_free_fields=True,
        multi_company=True,
        scripts=_sample_scripts(),
        table_fields=[field],
        table_pk_fields=["codigo"],
        created_at=datetime(2026, 5, 26, 18, 0),
    )
    restored = entry_from_dict(entry_to_dict(entry))
    assert restored is not None
    assert len(restored.table_fields) == 1
    assert restored.table_fields[0].name == "codigo"
    assert restored.table_pk_fields == ["codigo"]


def test_save_and_load_history(tmp_path, monkeypatch) -> None:
    path = tmp_path / "history.json"
    monkeypatch.setattr(
        "totvs_helper.ui.history_store.history_path",
        lambda: path,
    )

    history = SessionHistory()
    for index in range(25):
        history.add(
            HistoryEntry(
                dsn="DSN",
                table=f"tab-{index}",
                include_free_fields=False,
                multi_company=True,
                scripts=_sample_scripts(),
            )
        )
    save_history_entries(history.entries)
    loaded = load_history_entries()
    assert len(loaded) == MAX_PERSISTED_HISTORY
    assert loaded[0].table == "tab-24"

    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["version"] == 1
    assert len(raw["entries"]) == MAX_PERSISTED_HISTORY
