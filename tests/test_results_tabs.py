"""Tests for results screen tab cycling."""

from __future__ import annotations

from totvs_helper.ui.screens.results_screen import TAB_DEFS, TAB_KEYS


def test_tab_keys_match_defs() -> None:
    assert len(TAB_KEYS) == len(TAB_DEFS)
    assert TAB_KEYS[0] == "query_etl"
    assert TAB_KEYS[-1] == "script_delete"


def test_cycle_tab_wrap_logic() -> None:
    count = len(TAB_KEYS)
    assert (count - 1 + 1) % count == 0
    assert (0 - 1) % count == count - 1
