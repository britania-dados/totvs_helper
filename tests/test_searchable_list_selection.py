"""Tests for table list selection with large catalogs."""

from __future__ import annotations

from totvs_helper.ui.widgets.searchable_list import resolve_visible_items


def test_large_list_preview_keeps_selected_when_pinned() -> None:
    all_items = [f"table-{i:04d}" for i in range(500)]
    visible, _ = resolve_visible_items(all_items, "")
    assert len(visible) == 300

    selected = "table-0499"
    assert selected in all_items
    assert selected not in visible
    visible = [selected, *visible]
    assert visible[0] == selected
    assert len(visible) == 301
