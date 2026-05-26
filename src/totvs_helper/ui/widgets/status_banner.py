"""Top status line with optional auto-dismiss and close button."""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from totvs_helper.ui.design_tokens import ThemeTokens
from totvs_helper.ui.widgets.toast import TOAST_DURATION_MS


class StatusBanner(ctk.CTkFrame):
    """Inline status above main content; transient messages match toast lifetime."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        tokens: ThemeTokens,
        *,
        on_dismiss: Optional[Callable[[], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._tokens = tokens
        self._on_dismiss = on_dismiss
        self._timer_id: Optional[str] = None
        self.grid_columnconfigure(0, weight=1)

        self._label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=tokens.text_muted,
            anchor="w",
        )
        self._label.grid(row=0, column=0, sticky="ew")

        self._close = ctk.CTkButton(
            self,
            text="✕",
            width=28,
            height=28,
            fg_color="transparent",
            hover_color=tokens.surface_alt,
            text_color=tokens.text_muted,
            command=self.dismiss,
        )
        self._close.grid(row=0, column=1, padx=(8, 0))
        self._close.grid_remove()

    def update_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self._close.configure(
            hover_color=tokens.surface_alt,
            text_color=tokens.text_muted,
        )

    def show(self, message: str, *, color: str, transient: bool = False) -> None:
        self._cancel_timer()
        self._label.configure(text=message, text_color=color)
        if transient and message:
            self._close.grid()
            self._timer_id = self.after(TOAST_DURATION_MS, self.dismiss)
        else:
            self._close.grid_remove()

    def dismiss(self) -> None:
        self._cancel_timer()
        self._close.grid_remove()
        self._label.configure(text="", text_color=self._tokens.text_muted)
        if self._on_dismiss is not None:
            self._on_dismiss()

    def _cancel_timer(self) -> None:
        if self._timer_id is not None:
            self.after_cancel(self._timer_id)
            self._timer_id = None
