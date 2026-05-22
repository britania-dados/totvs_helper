"""Toast notification manager."""

from __future__ import annotations

import customtkinter as ctk

from totvs_helper.ui.design_tokens import ThemeTokens

TOAST_DURATION_MS = 3000


class ToastManager:
    """Stack toasts at bottom-right of root window."""

    def __init__(self, root: ctk.CTk, tokens: ThemeTokens) -> None:
        self._root = root
        self._tokens = tokens
        self._toasts: list[ctk.CTkFrame] = []

    def update_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens

    def show(self, message: str, kind: str = "info") -> None:
        colors = {
            "info": (self._tokens.surface_alt, self._tokens.text),
            "success": ("#14532d", self._tokens.success),
            "warning": ("#422006", self._tokens.warning),
            "error": ("#450a0a", self._tokens.danger),
        }
        bg, fg = colors.get(kind, colors["info"])

        frame = ctk.CTkFrame(
            self._root,
            fg_color=bg,
            corner_radius=8,
            border_width=1,
            border_color=self._tokens.border,
        )
        ctk.CTkLabel(
            frame,
            text=message,
            text_color=fg,
            font=ctk.CTkFont(size=12),
            wraplength=320,
        ).pack(padx=14, pady=10)

        self._toasts.append(frame)
        self._reposition()

        frame.after(TOAST_DURATION_MS, lambda: self._dismiss(frame))

    def _dismiss(self, frame: ctk.CTkFrame) -> None:
        if frame in self._toasts:
            self._toasts.remove(frame)
            frame.destroy()
            self._reposition()

    def _reposition(self) -> None:
        self._root.update_idletasks()
        x_base = self._root.winfo_width() - 340
        y_base = self._root.winfo_height() - 48
        for index, toast in enumerate(reversed(self._toasts)):
            toast.place(x=x_base, y=y_base - index * 56, width=320, height=48)
