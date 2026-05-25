"""Tests for script option switches on the results screen."""

from __future__ import annotations

import customtkinter as ctk

from totvs_helper.ui.design_tokens import get_tokens
from totvs_helper.ui.screens.results_screen import ResultsScreen


def test_results_screen_script_options_sync_without_callback() -> None:
    root = ctk.CTk()
    calls: list[int] = []
    try:
        tokens = get_tokens("dark")
        screen = ResultsScreen(
            root,
            tokens,
            on_copy_tab=lambda: None,
            on_copy_all=lambda: None,
            on_save=lambda: None,
            on_save_default=lambda: None,
            on_script_options_changed=lambda: calls.append(1),
            on_generate_pentaho=lambda: None,
        )
        screen.set_context(
            "DSN1",
            "customer",
            include_free_fields=False,
            multi_company=True,
        )
        assert screen.get_script_options() == (False, True)
        assert calls == []

        screen.set_script_options(True, False)
        assert screen.get_script_options() == (True, False)
        assert calls == []
    finally:
        root.destroy()
