"""Tests for HistoryPanel entry rendering."""

from __future__ import annotations

from datetime import datetime

import customtkinter as ctk

from totvs_helper.services.script_generator import GeneratedScripts
from totvs_helper.ui.design_tokens import get_tokens
from totvs_helper.ui.screens.history_panel import HistoryPanel
from totvs_helper.ui.state import HistoryEntry


def _sample_scripts() -> GeneratedScripts:
    return GeneratedScripts(
        query_etl="SELECT 1",
        ddl_create="CREATE TABLE t (id int)",
        script_delete="DELETE FROM t",
        script_update="UPDATE t SET id=1",
        differential="a || b",
    )


def test_history_panel_set_entries_cycles() -> None:
    root = ctk.CTk()
    try:
        tokens = get_tokens("dark")
        panel = HistoryPanel(
            root,
            tokens,
            on_restore=lambda _e: None,
            on_clear=lambda: None,
        )
        panel.set_entries([])
        assert panel._empty_label.winfo_exists()

        entry = HistoryEntry(
            dsn="DSN",
            table="customer",
            include_free_fields=False,
            multi_company=True,
            scripts=_sample_scripts(),
            created_at=datetime(2026, 5, 22, 14, 30),
        )
        panel.set_entries([entry])
        assert panel._empty_label.winfo_exists()

        panel.set_entries([])
        assert panel._empty_label.winfo_exists()
    finally:
        root.destroy()
