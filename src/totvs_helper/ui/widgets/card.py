"""Card container widget."""

from __future__ import annotations

import customtkinter as ctk

from totvs_helper.ui.design_tokens import RADIUS, SPACING, ThemeTokens


class Card(ctk.CTkFrame):
    """Rounded surface container with optional title."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        tokens: ThemeTokens,
        *,
        title: str = "",
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            fg_color=tokens.surface,
            border_color=tokens.border,
            border_width=1,
            corner_radius=RADIUS["lg"],
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)

        row = 0
        if title:
            ctk.CTkLabel(
                self,
                text=title,
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color=tokens.text,
            ).grid(
                row=row,
                column=0,
                sticky="w",
                padx=SPACING["lg"],
                pady=(SPACING["lg"], SPACING["sm"]),
            )
            row += 1

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(
            row=row,
            column=0,
            sticky="nsew",
            padx=SPACING["lg"],
            pady=(0, SPACING["lg"]),
        )
        self.body.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(row, weight=1)
