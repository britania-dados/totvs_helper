"""Collapsible table preview: one-line bar or full overlay with metadata tabs."""

from __future__ import annotations

from typing import Callable, List, Optional, Sequence, Tuple

import customtkinter as ctk

from totvs_helper.infra.odbc_client import TableIndexRow
from totvs_helper.ui.design_tokens import SPACING, ThemeTokens
from totvs_helper.ui.widgets.sample_data_grid import SampleDataGrid

SAMPLE_PAGE_SIZE = 10
_COLLAPSED_HEIGHT = 34
_HEADER_BTN_HEIGHT = 26
_META_TAB_FIELDS = "Campos"
_META_TAB_INDEXES = "Índices"


class TablePreviewPanel(ctk.CTkFrame):
    """Collapsed strip or overlay with fields/indexes tabs and sample data."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        tokens: ThemeTokens,
        *,
        on_fetch: Callable[[int], None],
        on_expanded_changed: Optional[Callable[[bool], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            fg_color=tokens.surface_alt,
            border_color=tokens.border,
            border_width=1,
            corner_radius=10,
            **kwargs,
        )
        self._tokens = tokens
        self._on_fetch = on_fetch
        self._on_expanded_changed = on_expanded_changed
        self._expanded = False
        self._meta_tab = _META_TAB_FIELDS
        self._sample_offset = 0
        self._has_more = False
        self._row_count = 0
        self._cached_fields: List[Sequence] = []
        self._cached_pk_fields: List[str] = []
        self._cached_indexes: List[TableIndexRow] = []
        self._overlay_master = master
        self._collapsed_grid_row = 4

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)

        header = ctk.CTkFrame(self, fg_color="transparent", height=_COLLAPSED_HEIGHT)
        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=SPACING["sm"],
            pady=SPACING["xs"],
        )
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Pré-visualização da tabela",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=tokens.text,
        ).grid(row=0, column=0, sticky="w")

        self._toggle_btn = ctk.CTkButton(
            header,
            text="Expandir",
            width=86,
            height=_HEADER_BTN_HEIGHT,
            fg_color="transparent",
            border_width=1,
            border_color=tokens.border,
            command=self._toggle,
        )
        self._toggle_btn.grid(row=0, column=1, padx=(8, 0))

        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.grid_columnconfigure(0, weight=1)
        self._body.grid_rowconfigure(1, weight=1)
        self._body.grid_rowconfigure(3, weight=1)

        self._meta_tabs = ctk.CTkSegmentedButton(
            self._body,
            values=[_META_TAB_FIELDS, _META_TAB_INDEXES],
            command=self._switch_meta_tab,
            height=28,
            font=ctk.CTkFont(size=11),
        )
        self._meta_tabs.set(_META_TAB_FIELDS)
        self._meta_tabs.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, SPACING["xs"]),
        )

        self._meta_stack = ctk.CTkFrame(self._body, fg_color="transparent")
        self._meta_stack.grid(row=1, column=0, sticky="nsew", pady=(0, SPACING["xs"]))
        self._meta_stack.grid_columnconfigure(0, weight=1)
        self._meta_stack.grid_rowconfigure(0, weight=1)

        self._metadata_grid = SampleDataGrid(
            self._meta_stack, tokens, compact=True, preview=True
        )
        self._metadata_grid.grid(row=0, column=0, sticky="nsew")

        self._indexes_grid = SampleDataGrid(
            self._meta_stack, tokens, compact=True, preview=True
        )

        sample_section = ctk.CTkFrame(self._body, fg_color="transparent")
        sample_section.grid(row=2, column=0, sticky="nsew")
        sample_section.grid_columnconfigure(0, weight=1)
        sample_section.grid_rowconfigure(1, weight=1)

        sample_header = ctk.CTkFrame(sample_section, fg_color="transparent")
        sample_header.grid(row=0, column=0, sticky="ew", pady=(0, 2))
        sample_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            sample_header,
            text="Dados da tabela",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=tokens.text,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        nav = ctk.CTkFrame(sample_header, fg_color="transparent")
        nav.grid(row=0, column=1, sticky="e")

        self._page_label = ctk.CTkLabel(
            nav,
            text="",
            font=ctk.CTkFont(size=10),
            text_color=tokens.text_muted,
        )
        self._page_label.pack(side="left", padx=(0, 6))

        self._btn_prev = ctk.CTkButton(
            nav,
            text="◀ Anterior",
            width=92,
            height=_HEADER_BTN_HEIGHT,
            fg_color="transparent",
            border_width=1,
            border_color=tokens.border,
            command=self._prev_page,
        )
        self._btn_prev.pack(side="left", padx=2)

        self._btn_next = ctk.CTkButton(
            nav,
            text="Próximos 10 ▶",
            width=108,
            height=_HEADER_BTN_HEIGHT,
            fg_color=tokens.surface,
            border_width=1,
            border_color=tokens.border,
            command=self._next_page,
        )
        self._btn_next.pack(side="left", padx=2)

        self._sample_grid = SampleDataGrid(
            sample_section, tokens, compact=True, preview=True
        )
        self._sample_grid.grid(row=1, column=0, sticky="nsew")

        self._update_nav_buttons()
        self._collapse()

    def get_field_cache(self) -> Tuple[List[Sequence], List[str]]:
        return self._cached_fields, self._cached_pk_fields

    @property
    def is_expanded(self) -> bool:
        return self._expanded

    def _notify_overlay(self, expanded: bool) -> None:
        if self._on_expanded_changed is not None:
            self._on_expanded_changed(expanded)

    def _switch_meta_tab(self, value: str) -> None:
        self._meta_tab = value
        self._show_meta_tab()

    def _show_meta_tab(self) -> None:
        self._metadata_grid.grid_remove()
        self._indexes_grid.grid_remove()
        if self._meta_tab == _META_TAB_INDEXES:
            self._indexes_grid.grid(row=0, column=0, sticky="nsew")
        else:
            self._metadata_grid.grid(row=0, column=0, sticky="nsew")

    def _prev_page(self) -> None:
        if self._sample_offset <= 0:
            return
        self._on_fetch(max(0, self._sample_offset - SAMPLE_PAGE_SIZE))

    def _next_page(self) -> None:
        if not self._has_more:
            return
        self._on_fetch(self._sample_offset + SAMPLE_PAGE_SIZE)

    def _update_nav_buttons(self) -> None:
        if self._row_count > 0:
            start = self._sample_offset + 1
            end = self._sample_offset + self._row_count
            self._page_label.configure(text=f"Registros {start}–{end}")
        else:
            self._page_label.configure(text="")

        self._btn_prev.configure(
            state="normal" if self._sample_offset > 0 else "disabled"
        )
        self._btn_next.configure(state="normal" if self._has_more else "disabled")

    def _layout_collapsed(self) -> None:
        self.place_forget()
        self.grid(
            row=self._collapsed_grid_row,
            column=0,
            sticky="ew",
            padx=0,
            pady=(SPACING["sm"], 0),
        )
        self.configure(height=_COLLAPSED_HEIGHT)
        self.grid_propagate(False)
        self._body.grid_remove()
        self.grid_rowconfigure(0, weight=0)

    def _layout_expanded(self) -> None:
        self.grid_forget()
        self.grid_propagate(True)
        self.configure(height=0)
        self._body.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=SPACING["md"],
            pady=(0, SPACING["sm"]),
        )
        self.grid_rowconfigure(1, weight=1)
        self._body.grid_rowconfigure(1, weight=1)
        self._body.grid_rowconfigure(2, weight=1)
        self._show_meta_tab()
        self.place(
            in_=self._overlay_master,
            relx=0,
            rely=0,
            relwidth=1,
            relheight=1,
        )
        self.lift()

    def set_collapsed_grid_row(self, row: int) -> None:
        """Row index in the parent grid used when the panel is collapsed."""
        self._collapsed_grid_row = row

    def _collapse(self) -> None:
        if not self._expanded:
            self._layout_collapsed()
            return
        self._expanded = False
        self._toggle_btn.configure(text="Expandir")
        self._layout_collapsed()
        self._notify_overlay(False)

    def _expand(self) -> None:
        if self._expanded:
            return
        self._expanded = True
        self._toggle_btn.configure(text="Recolher")
        self._layout_expanded()
        self._notify_overlay(True)

    def _toggle(self) -> None:
        if self._expanded:
            self._collapse()
            return
        self._expand()
        self._on_fetch(0)

    def set_loading(self) -> None:
        if not self._expanded:
            self._expand()
        self._metadata_grid.show_message("Carregando campos...")
        self._indexes_grid.show_message("Carregando índices...")
        self._sample_grid.show_message("Carregando registros...")
        self._sample_offset = 0
        self._has_more = False
        self._update_nav_buttons()

    def set_sample_loading(self) -> None:
        self._page_label.configure(text="Carregando registros...")
        self._btn_prev.configure(state="disabled")
        self._btn_next.configure(state="disabled")

    def set_error(self, message: str) -> None:
        if not self._expanded:
            self._expand()
        self._metadata_grid.show_message(message, error=True)
        self._indexes_grid.show_message(message, error=True)
        self._sample_grid.show_message(message, error=True)
        self._has_more = False
        self._update_nav_buttons()

    def set_data(
        self,
        table: str,
        fields: List[Sequence],
        pk_fields: List[str],
        *,
        index_rows: Optional[List[TableIndexRow]] = None,
        sample_columns: Optional[List[str]] = None,
        sample_rows: Optional[List[Tuple]] = None,
        sample_error: Optional[str] = None,
        sample_offset: int = 0,
        reload_metadata: bool = True,
    ) -> None:
        del table  # reserved for future header/status use
        self._sample_offset = sample_offset
        row_count = len(sample_rows) if sample_rows is not None else 0
        self._row_count = row_count
        self._has_more = (
            sample_error is None
            and sample_rows is not None
            and row_count >= SAMPLE_PAGE_SIZE
        )

        if reload_metadata:
            self._cached_fields = list(fields)
            self._cached_pk_fields = list(pk_fields)
            self._cached_indexes = list(index_rows or [])
            self._metadata_grid.set_metadata(fields, pk_fields)
            if self._cached_indexes:
                self._indexes_grid.set_indexes(self._cached_indexes)
            else:
                self._indexes_grid.show_message("Nenhum índice encontrado.")

        if sample_error:
            self._sample_grid.show_message(sample_error, error=True)
        elif sample_columns is not None and sample_rows is not None:
            if not sample_rows:
                self._sample_grid.show_message(
                    "Nenhum registro retornado nesta página."
                )
            else:
                self._sample_grid.set_data(
                    sample_columns,
                    sample_rows,
                    row_offset=sample_offset,
                    scroll_to_top=True,
                )
        else:
            self._sample_grid.show_message("Sem dados de amostra.")

        self._update_nav_buttons()

    def clear(self) -> None:
        self._metadata_grid.clear()
        self._indexes_grid.clear()
        self._sample_grid.clear()
        self._cached_fields = []
        self._cached_pk_fields = []
        self._cached_indexes = []
        self._sample_offset = 0
        self._has_more = False
        self._update_nav_buttons()

    def reset(self) -> None:
        """Clear content and return to the one-line collapsed bar."""
        self.clear()
        self._collapse()
