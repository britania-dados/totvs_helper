"""Table selection and options screen."""

from __future__ import annotations

from typing import Callable, List, Optional

import customtkinter as ctk

from totvs_helper.ui.design_tokens import SPACING, ThemeTokens
from totvs_helper.ui.theme import subtitle_font
from totvs_helper.ui.widgets.card import Card
from totvs_helper.ui.widgets.searchable_list import SearchableList
from totvs_helper.ui.widgets.table_preview import TablePreviewPanel


class TableScreen(ctk.CTkFrame):
    """Table picker with options and overlay preview."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        tokens: ThemeTokens,
        appearance_mode: str,
        *,
        on_select_table: Callable[[str], None],
        on_generate: Callable[[], None],
        on_preview: Callable[[int], None],
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._tokens = tokens
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._title = ctk.CTkLabel(
            self,
            text="Tabela e opções",
            font=subtitle_font(),
            text_color=tokens.text,
        )
        self._title.grid(row=0, column=0, sticky="w", pady=(0, SPACING["md"]))

        self._card = Card(self, tokens, title="Seleção de tabela")
        self._card.grid(row=1, column=0, sticky="nsew")
        card = self._card
        card.body.grid_columnconfigure(0, weight=1)
        card.body.grid_rowconfigure(3, weight=1)
        card.body.grid_rowconfigure(4, weight=0)

        self._dsn_badge = ctk.CTkLabel(
            card.body,
            text="",
            fg_color=tokens.surface_alt,
            corner_radius=8,
            text_color=tokens.text_muted,
            font=ctk.CTkFont(size=12),
        )
        self._dsn_badge.grid(row=0, column=0, sticky="ew", pady=(0, SPACING["sm"]))

        options = ctk.CTkFrame(card.body, fg_color="transparent")
        options.grid(row=1, column=0, sticky="ew", pady=(0, SPACING["sm"]))

        self.chk_free_fields = ctk.CTkCheckBox(
            options,
            text="Campos livres (char-1, int-1, ...)",
        )
        self.chk_free_fields.grid(row=0, column=0, padx=(0, SPACING["lg"]), sticky="w")

        self.chk_multi_company = ctk.CTkCheckBox(options, text="Multi-empresa")
        self.chk_multi_company.grid(row=0, column=1, sticky="w")

        self.apply_option_defaults(include_free_fields=True, multi_company=True)

        self._recent_frame = ctk.CTkFrame(card.body, fg_color="transparent")
        self._recent_frame.grid(row=2, column=0, sticky="ew", pady=(0, SPACING["sm"]))
        self._recent_buttons: List[ctk.CTkButton] = []

        self._list = SearchableList(
            card.body,
            label="Tabelas",
            placeholder="Buscar tabela... (duplo clique para gerar)",
            appearance_mode=appearance_mode,
            on_select=on_select_table,
            on_activate=on_generate,
        )
        self._list.grid(row=3, column=0, sticky="nsew")

        self.preview = TablePreviewPanel(
            card.body,
            tokens,
            on_fetch=on_preview,
            on_expanded_changed=self._on_preview_overlay,
        )
        self.preview.set_collapsed_grid_row(4)
        self.preview.grid(row=4, column=0, sticky="ew", pady=(SPACING["sm"], 0))

    def _on_preview_overlay(self, active: bool) -> None:
        self.set_table_picker_enabled(not active)

    def set_table_picker_enabled(self, enabled: bool) -> None:
        """Disable list/search while the preview overlay is open."""
        state = "normal" if enabled else "disabled"
        self._list.set_interactive(enabled)
        self.chk_free_fields.configure(state=state)
        self.chk_multi_company.configure(state=state)
        for btn in self._recent_buttons:
            btn.configure(state=state)

    def apply_option_defaults(
        self, *, include_free_fields: bool, multi_company: bool
    ) -> None:
        """Sync Campos livres / Multi-empresa checkboxes."""
        if include_free_fields:
            self.chk_free_fields.select()
        else:
            self.chk_free_fields.deselect()
        if multi_company:
            self.chk_multi_company.select()
        else:
            self.chk_multi_company.deselect()

    def set_dsn_context(self, dsn: str) -> None:
        self._dsn_badge.configure(text=f"  Conectado: {dsn}  ")

    def set_items(self, items: List[str], selected: Optional[str] = None) -> None:
        self._list.set_items(items, selected=selected)

    def get_selected(self) -> Optional[str]:
        return self._list.get_selected()

    def select_value(self, value: str) -> None:
        self._list.select_value(value)

    def search_widget(self) -> ctk.CTkEntry:
        return self._list.search_widget()

    def update_appearance(self, mode: str) -> None:
        self._list.update_appearance(mode)

    def update_tokens(self, tokens: ThemeTokens, mode: str) -> None:
        self._tokens = tokens
        self._title.configure(text_color=tokens.text)
        self._card.update_tokens(tokens)
        self._dsn_badge.configure(
            fg_color=tokens.surface_alt,
            text_color=tokens.text_muted,
        )
        self._list.update_tokens(tokens, mode)
        self.preview.update_tokens(tokens)
        for btn in self._recent_buttons:
            btn.configure(
                border_color=tokens.border,
                hover_color=tokens.surface_alt,
            )

    def render_recent(self, tables: List[str], on_pick: Callable[[str], None]) -> None:
        for btn in self._recent_buttons:
            btn.destroy()
        self._recent_buttons.clear()
        if not tables:
            self._recent_frame.grid_remove()
            return
        self._recent_frame.grid()
        ctk.CTkLabel(
            self._recent_frame,
            text="Recentes:",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).grid(row=0, column=0, padx=(0, 8))
        for index, name in enumerate(tables[:5]):
            btn = ctk.CTkButton(
                self._recent_frame,
                text=name,
                height=26,
                fg_color="transparent",
                border_width=1,
                border_color=self._tokens.border,
                hover_color=self._tokens.surface_alt,
                command=lambda n=name: on_pick(n),
            )
            btn.grid(row=0, column=index + 1, padx=3)
            self._recent_buttons.append(btn)
        if self.preview.is_expanded:
            self.set_table_picker_enabled(False)
