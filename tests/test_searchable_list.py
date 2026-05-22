"""Tests for searchable list filtering helpers."""

from __future__ import annotations

from totvs_helper.ui.widgets.searchable_list import resolve_visible_items


def test_resolve_visible_items_small_list() -> None:
    items = ["b", "a", "ab"]
    visible, caption = resolve_visible_items(items, "")
    assert visible == ["b", "a", "ab"]
    assert "3 itens" in caption


def test_resolve_visible_items_large_list_without_search() -> None:
    items = [f"table-{index:04d}" for index in range(500)]
    visible, caption = resolve_visible_items(items, "")
    assert len(visible) == 300
    assert "500" in caption
    assert "busca" in caption.lower()


def test_resolve_visible_items_large_list_short_search() -> None:
    items = [f"table-{index:04d}" for index in range(500)]
    visible, caption = resolve_visible_items(items, "t")
    assert visible == []
    assert "2 caracteres" in caption


def test_resolve_visible_items_large_list_filtered_search() -> None:
    items = ["item", "item-aux", "outro", "x-item"]
    visible, caption = resolve_visible_items(items, "item")
    assert visible == ["item", "item-aux", "x-item"]
    assert "3 de 4" in caption
