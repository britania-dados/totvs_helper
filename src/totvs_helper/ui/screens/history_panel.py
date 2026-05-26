"""Session history screen."""

from __future__ import annotations

from typing import Callable, List

import customtkinter as ctk

from totvs_helper.ui.design_tokens import SPACING, ThemeTokens
from totvs_helper.ui.state import HistoryEntry
from totvs_helper.ui.theme import subtitle_font
from totvs_helper.ui.widgets.card import Card
from totvs_helper.ui.widgets.icon_button import IconButton


class HistoryPanel(ctk.CTkFrame):
    """Lists session generations with restore action."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        tokens: ThemeTokens,
        *,
        on_restore: Callable[[HistoryEntry], None],
        on_clear: Callable[[], None],
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._tokens = tokens
        self._on_restore = on_restore
        self._on_clear = on_clear
        self._entries: List[HistoryEntry] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, SPACING["md"]))
        header.grid_columnconfigure(0, weight=1)

        self._title = ctk.CTkLabel(
            header,
            text="Histórico",
            font=subtitle_font(),
            text_color=tokens.text,
        )
        self._title.grid(row=0, column=0, sticky="w")

        IconButton(
            header,
            tokens,
            text="Limpar",
            icon="🗑",
            variant="ghost",
            command=on_clear,
            width=100,
        ).grid(row=0, column=1)

        self._card = Card(self, tokens, title="Gerações recentes")
        self._card.grid(row=1, column=0, sticky="nsew")
        card = self._card
        card.body.grid_columnconfigure(0, weight=1)
        card.body.grid_rowconfigure(0, weight=1)

        self._scroll = ctk.CTkScrollableFrame(card.body, label_text="")
        self._scroll.grid(row=0, column=0, sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

        self._empty_label = ctk.CTkLabel(
            self._scroll,
            text="Nenhuma geração salva ainda.",
            text_color=tokens.text_muted,
        )

    def set_entries(self, entries: List[HistoryEntry]) -> None:
        self._entries = entries
        for child in self._scroll.winfo_children():
            if child is self._empty_label:
                continue
            child.destroy()

        if not entries:
            self._empty_label.grid(row=0, column=0, sticky="w", pady=SPACING["md"])
            return

        self._empty_label.grid_remove()

        for index, entry in enumerate(entries):
            row = ctk.CTkFrame(
                self._scroll, fg_color=self._tokens.surface_alt, corner_radius=8
            )
            row.grid(row=index, column=0, sticky="ew", pady=4)
            row.grid_columnconfigure(0, weight=1)

            time_str = entry.created_at.strftime("%d/%m %H:%M")
            ctk.CTkLabel(
                row,
                text=f"{entry.table}",
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w",
            ).grid(
                row=0, column=0, sticky="w", padx=SPACING["md"], pady=(SPACING["sm"], 0)
            )

            ctk.CTkLabel(
                row,
                text=f"DSN: {entry.dsn} | {time_str}",
                text_color=self._tokens.text_muted,
                font=ctk.CTkFont(size=11),
                anchor="w",
            ).grid(
                row=1, column=0, sticky="w", padx=SPACING["md"], pady=(0, SPACING["sm"])
            )

            ctk.CTkButton(
                row,
                text="Restaurar",
                width=90,
                height=28,
                fg_color=self._tokens.accent,
                hover_color=self._tokens.accent_hover,
                command=lambda e=entry: self._on_restore(e),
            ).grid(row=0, column=1, rowspan=2, padx=SPACING["md"])

    def update_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self._title.configure(text_color=tokens.text)
        self._card.update_tokens(tokens)
        self._empty_label.configure(text_color=tokens.text_muted)
        if self._entries:
            self.set_entries(self._entries)
