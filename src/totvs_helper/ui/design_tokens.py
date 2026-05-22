"""Design tokens for Totvs Helper UI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ThemeTokens:
    bg: str
    surface: str
    surface_alt: str
    border: str
    text: str
    text_muted: str
    accent: str
    accent_hover: str
    success: str
    warning: str
    danger: str
    sidebar_bg: str
    sidebar_active: str
    list_bg: str
    list_fg: str
    list_select_bg: str
    list_select_fg: str
    sql_keyword: str
    sql_string: str
    sql_comment: str
    sql_name: str
    sql_default: str


SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "xxl": 32,
}

RADIUS = {
    "sm": 6,
    "md": 10,
    "lg": 14,
}

FONT_TITLE = ("Segoe UI", 22, "bold")
FONT_SUBTITLE = ("Segoe UI", 16, "bold")
FONT_BODY = ("Segoe UI", 13)
FONT_CAPTION = ("Segoe UI", 11)
FONT_MONO: Tuple[str, int] = ("Consolas", 12)

ERROR = "#ef4444"
WARNING_BG_DARK = "#3f1d1d"
WARNING_BG_LIGHT = "#fde8e8"

DARK = ThemeTokens(
    bg="#141414",
    surface="#1f1f1f",
    surface_alt="#2a2a2a",
    border="#3a3a3a",
    text="#f3f4f6",
    text_muted="#9ca3af",
    accent="#c8102e",
    accent_hover="#9e0c24",
    success="#22c55e",
    warning="#f59e0b",
    danger="#ef4444",
    sidebar_bg="#181818",
    sidebar_active="#2d1519",
    list_bg="#1e1e1e",
    list_fg="#e5e7eb",
    list_select_bg="#c8102e",
    list_select_fg="#ffffff",
    sql_keyword="#7dd3fc",
    sql_string="#86efac",
    sql_comment="#9ca3af",
    sql_name="#fbbf24",
    sql_default="#e5e7eb",
)

LIGHT = ThemeTokens(
    bg="#f5f5f5",
    surface="#ffffff",
    surface_alt="#f3f4f6",
    border="#d1d5db",
    text="#111827",
    text_muted="#6b7280",
    accent="#c8102e",
    accent_hover="#9e0c24",
    success="#16a34a",
    warning="#d97706",
    danger="#dc2626",
    sidebar_bg="#ebebeb",
    sidebar_active="#fde8e8",
    list_bg="#f9fafb",
    list_fg="#111827",
    list_select_bg="#c8102e",
    list_select_fg="#ffffff",
    sql_keyword="#0369a1",
    sql_string="#15803d",
    sql_comment="#6b7280",
    sql_name="#b45309",
    sql_default="#111827",
)


def get_tokens(mode: str) -> ThemeTokens:
    return LIGHT if mode == "light" else DARK
