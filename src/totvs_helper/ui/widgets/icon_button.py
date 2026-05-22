"""Styled button with optional glyph."""

from __future__ import annotations

from typing import Optional

import customtkinter as ctk

from totvs_helper.ui.design_tokens import ThemeTokens


class IconButton(ctk.CTkButton):
    """Button with variant styles."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        tokens: ThemeTokens,
        *,
        text: str,
        icon: str = "",
        variant: str = "secondary",
        command: Optional[object] = None,
        width: int = 120,
        **kwargs,
    ) -> None:
        label = f"{icon} {text}".strip() if icon else text
        fg, hover, border = self._colors(tokens, variant)
        super().__init__(
            master,
            text=label,
            width=width,
            height=34,
            fg_color=fg,
            hover_color=hover,
            border_width=1 if variant in ("secondary", "ghost") else 0,
            border_color=tokens.border,
            text_color=tokens.text if variant != "primary" else "#ffffff",
            command=command,
            **kwargs,
        )

    @staticmethod
    def _colors(tokens: ThemeTokens, variant: str) -> tuple:
        if variant == "primary":
            return tokens.accent, tokens.accent_hover, tokens.accent
        if variant == "danger":
            return tokens.danger, "#b91c1c", tokens.danger
        if variant == "ghost":
            return "transparent", tokens.surface_alt, tokens.border
        return tokens.surface_alt, tokens.border, tokens.border
