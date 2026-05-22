"""Tests for in-memory session history."""

from __future__ import annotations

from datetime import datetime

from totvs_helper.services.script_generator import GeneratedScripts
from totvs_helper.ui.state import HistoryEntry, SessionHistory


def _sample_scripts() -> GeneratedScripts:
    return GeneratedScripts(
        query_etl="SELECT 1",
        ddl_create="CREATE TABLE t (id int)",
        script_delete="DELETE FROM t",
        script_update="UPDATE t SET id=1",
        differential="a || b",
    )


def test_session_history_cap() -> None:
    history = SessionHistory(max_entries=3)
    for index in range(5):
        history.add(
            HistoryEntry(
                dsn="DSN",
                table=f"tab-{index}",
                include_free_fields=False,
                multi_company=True,
                scripts=_sample_scripts(),
                created_at=datetime(2026, 1, 1, 10, index),
            )
        )
    assert len(history.entries) == 3
    assert history.entries[0].table == "tab-4"


def test_history_entry_label() -> None:
    entry = HistoryEntry(
        dsn="PROD",
        table="customer",
        include_free_fields=True,
        multi_company=False,
        scripts=_sample_scripts(),
        created_at=datetime(2026, 5, 22, 14, 30),
    )
    assert "customer" in entry.label
    assert "14:30" in entry.label
