"""DSN selection screen."""

from __future__ import annotations

from typing import Callable, List, Optional

import customtkinter as ctk

from totvs_helper.ui.design_tokens import SPACING, ThemeTokens
from totvs_helper.ui.theme import subtitle_font
from totvs_helper.ui.widgets.card import Card
from totvs_helper.ui.widgets.icon_button import IconButton
from totvs_helper.ui.widgets.searchable_list import SearchableList


class DsnScreen(ctk.CTkFrame):
    """OpenEdge DSN picker."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        tokens: ThemeTokens,
        appearance_mode: str,
        *,
        on_test: Callable[[], None],
        on_select: Callable[[str], None],
        on_connect: Callable[[], None],
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self,
            text="Conexão ODBC",
            font=subtitle_font(),
            text_color=tokens.text,
        ).grid(row=0, column=0, sticky="w", pady=(0, SPACING["md"]))

        card = Card(self, tokens, title="DSNs OpenEdge")
        card.grid(row=1, column=0, sticky="nsew")
        card.body.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            card.body,
            text="Selecione o DSN configurado no ODBC. Use a busca para filtrar.",
            text_color=tokens.text_muted,
            font=ctk.CTkFont(size=12),
        ).grid(row=0, column=0, sticky="w", pady=(0, SPACING["sm"]))

        self._list = SearchableList(
            card.body,
            label="",
            placeholder="Buscar DSN...",
            appearance_mode=appearance_mode,
            on_select=on_select,
            on_activate=on_connect,
        )
        self._list.grid(row=1, column=0, sticky="nsew")

        actions = ctk.CTkFrame(card.body, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="e", pady=(SPACING["md"], 0))

        IconButton(
            actions,
            tokens,
            text="Testar conexão",
            icon="⚡",
            variant="secondary",
            command=on_test,
            width=150,
        ).pack(side="left", padx=(0, SPACING["sm"]))

        IconButton(
            actions,
            tokens,
            text="Conectar",
            icon="→",
            variant="primary",
            command=on_connect,
            width=130,
        ).pack(side="left")

    def set_items(self, items: List[str], selected: Optional[str] = None) -> None:
        self._list.set_items(items, selected=selected)

    def select_value(self, value: str) -> None:
        self._list.select_value(value)

    def search_widget(self) -> ctk.CTkEntry:
        return self._list.search_widget()

    def update_appearance(self, mode: str) -> None:
        self._list.update_appearance(mode)
