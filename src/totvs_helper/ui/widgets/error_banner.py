"""Inline error/warning banner."""

from __future__ import annotations

import customtkinter as ctk

from totvs_helper.ui.design_tokens import ERROR, WARNING_BG_DARK, WARNING_BG_LIGHT


class ErrorBanner(ctk.CTkFrame):
    """Dismissible banner for non-blocking error messages."""

    def __init__(
        self, master: ctk.CTkBaseClass, appearance_mode: str = "dark", **kwargs
    ) -> None:
        bg = WARNING_BG_LIGHT if appearance_mode == "light" else WARNING_BG_DARK
        super().__init__(master, fg_color=bg, corner_radius=8, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self._label = ctk.CTkLabel(
            self,
            text="",
            text_color=ERROR,
            anchor="w",
            justify="left",
            wraplength=900,
        )
        self._label.grid(row=0, column=0, sticky="ew", padx=12, pady=10)

        self._close = ctk.CTkButton(
            self,
            text="✕",
            width=28,
            height=28,
            fg_color="transparent",
            hover_color="#5c1a1a",
            command=self.hide,
        )
        self._close.grid(row=0, column=1, padx=(0, 8))

        self.grid_remove()

    def show(self, message: str) -> None:
        self._label.configure(text=message)
        self.grid()

    def hide(self) -> None:
        self.grid_remove()

    def update_mode(self, appearance_mode: str) -> None:
        bg = WARNING_BG_LIGHT if appearance_mode == "light" else WARNING_BG_DARK
        self.configure(fg_color=bg)
