"""Smoke test: custom Treeview style must define layout before widget creation."""

from __future__ import annotations

from tkinter import ttk

import customtkinter as ctk

from totvs_helper.ui.theme import apply_appearance, resolve_appearance, tokens
from totvs_helper.ui.widgets.sample_data_grid import SampleDataGrid


def test_sample_data_grid_registers_treeview_layout() -> None:
    root = ctk.CTk()
    root.withdraw()
    appearance = apply_appearance(resolve_appearance("System"))
    frame = ctk.CTkFrame(root)

    grid = SampleDataGrid(frame, tokens(appearance), compact=True)
    style = ttk.Style(grid)
    assert style.layout(grid._style)

    grid.destroy()
    root.destroy()
