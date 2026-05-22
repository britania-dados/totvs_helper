"""Tests for sample grid cell formatting."""

from __future__ import annotations

from totvs_helper.ui.widgets.sample_data_grid import format_cell


def test_format_cell_null() -> None:
    assert format_cell(None) == "NULL"


def test_format_cell_truncates_long_text() -> None:
    text = "x" * 300
    assert len(format_cell(text)) == 200
    assert format_cell(text).endswith("…")
