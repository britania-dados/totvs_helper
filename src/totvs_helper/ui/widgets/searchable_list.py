"""Performant searchable list using tk.Listbox."""

from __future__ import annotations

import tkinter as tk
from typing import Callable, List, Optional

import customtkinter as ctk

from totvs_helper.ui.theme import listbox_colors

# mov2unit_* / ems2unit_* databases expose 1000+ tables.
_LARGE_LIST_THRESHOLD = 400
_INITIAL_PREVIEW_COUNT = 300
_MIN_SEARCH_LEN = 2
_MAX_FILTER_RESULTS = 500


def resolve_visible_items(
    all_items: List[str],
    query: str,
) -> tuple[List[str], str]:
    """Choose which table names to render and the caption for the counter label."""
    total = len(all_items)
    normalized = query.strip().lower()

    if total == 0:
        return [], "0 itens"

    if total <= _LARGE_LIST_THRESHOLD:
        if normalized:
            filtered = [
                item for item in all_items if normalized in item.lower()
            ]
            return filtered, f"{len(filtered)} de {total} itens"

        return list(all_items), f"{total} itens"

    if not normalized:
        preview = all_items[:_INITIAL_PREVIEW_COUNT]
        return (
            preview,
            (
                f"Mostrando {len(preview)} de {total} tabelas — "
                "use a busca para refinar"
            ),
        )

    if len(normalized) < _MIN_SEARCH_LEN:
        return (
            [],
            (
                f"{total} tabelas — digite ao menos "
                f"{_MIN_SEARCH_LEN} caracteres na busca"
            ),
        )

    filtered = [item for item in all_items if normalized in item.lower()]
    if len(filtered) > _MAX_FILTER_RESULTS:
        visible = filtered[:_MAX_FILTER_RESULTS]
        return (
            visible,
            f"Mostrando {len(visible)} de {len(filtered)} "
            f"resultados ({total} no banco)",
        )

    return filtered, f"{len(filtered)} de {total} tabelas"


class SearchableList(ctk.CTkFrame):
    """Search field + scrollable listbox for large item sets."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        *,
        label: str,
        placeholder: str,
        appearance_mode: str,
        on_select: Callable[[str], None],
        on_activate: Optional[Callable[[], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._on_select = on_select
        self._on_activate = on_activate
        self._all_items: List[str] = []
        self._selected: Optional[str] = None
        self._appearance_mode = appearance_mode

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text=label, font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )

        self._search = ctk.CTkEntry(self, placeholder_text=placeholder)
        self._search.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self._search.bind("<KeyRelease>", self._on_search_changed)

        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=2, column=0, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)

        scrollbar = ctk.CTkScrollbar(list_frame, orientation="vertical")
        scrollbar.grid(row=0, column=1, sticky="ns")

        colors = listbox_colors(appearance_mode)
        self._listbox = tk.Listbox(
            list_frame,
            activestyle="none",
            exportselection=False,
            yscrollcommand=scrollbar.set,
            bg=colors["bg"],
            fg=colors["fg"],
            selectbackground=colors["selectbackground"],
            selectforeground=colors["selectforeground"],
        )
        self._listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar.configure(command=self._listbox.yview)

        self._listbox.bind("<<ListboxSelect>>", self._handle_select)
        if on_activate:
            self._listbox.bind("<Double-Button-1>", lambda _e: on_activate())
            self._listbox.bind("<Return>", lambda _e: on_activate())

        self._count_label = ctk.CTkLabel(
            self,
            text="0 itens",
            text_color="#9ca3af",
            font=ctk.CTkFont(size=11),
        )
        self._count_label.grid(row=3, column=0, sticky="w", pady=(6, 0))

    def set_interactive(self, enabled: bool) -> None:
        """Enable or disable search and list selection."""
        state = "normal" if enabled else "disabled"
        self._search.configure(state=state)
        self._listbox.configure(state=state)

    def clear_search(self) -> None:
        self._search.delete(0, "end")

    def set_items(self, items: List[str], *, selected: Optional[str] = None) -> None:
        self.clear_search()
        self._all_items = sorted(items, key=str.lower)
        self._selected = selected
        self._apply_filter()
        self._listbox.update_idletasks()

    def get_selected(self) -> Optional[str]:
        return self._selected

    def select_value(self, value: str) -> None:
        self._selected = value
        self.clear_search()
        self._apply_filter()

    def search_widget(self) -> ctk.CTkEntry:
        return self._search

    def update_appearance(self, mode: str) -> None:
        self._appearance_mode = mode
        colors = listbox_colors(mode)
        self._listbox.configure(
            bg=colors["bg"],
            fg=colors["fg"],
            selectbackground=colors["selectbackground"],
            selectforeground=colors["selectforeground"],
        )

    def _on_search_changed(self, _event: object = None) -> None:
        self._apply_filter()

    def _apply_filter(self) -> None:
        query = self._search.get()
        visible, caption = resolve_visible_items(self._all_items, query)

        if (
            self._selected
            and self._selected in self._all_items
            and self._selected not in visible
        ):
            visible = [self._selected, *visible]

        self._listbox.delete(0, tk.END)
        for item in visible:
            self._listbox.insert(tk.END, item)

        self._count_label.configure(text=caption)

        if self._selected and self._selected in visible:
            index = visible.index(self._selected)
            self._listbox.selection_set(index)
            self._listbox.see(index)
        elif self._selected and self._selected in self._all_items and not visible:
            self._selected = None

    def _handle_select(self, _event: object = None) -> None:
        selection = self._listbox.curselection()
        if not selection:
            return
        value = self._listbox.get(selection[0])
        self._selected = value
        self._on_select(value)
