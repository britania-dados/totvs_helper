"""Visual theme helpers for CustomTkinter UI."""

from __future__ import annotations

import sys

import customtkinter as ctk

from totvs_helper.ui.design_tokens import (
    FONT_BODY,
    FONT_CAPTION,
    FONT_MONO,
    FONT_SUBTITLE,
    FONT_TITLE,
    ThemeTokens,
    get_tokens,
)

APP_TITLE = "Totvs Helper"
COLOR_THEME = "blue"
WINDOW_MIN_SIZE = (1024, 680)
WINDOW_DEFAULT_SIZE = (1280, 800)
SIDEBAR_WIDTH = 220

STEP_KEYS = ("dsn", "table", "results")
STEP_LABELS = {
    "dsn": "Conexão ODBC",
    "table": "Tabela",
    "results": "Scripts",
}


def resolve_appearance(pref_mode: str) -> str:
    """Resolve system/dark/light preference to concrete mode."""
    if pref_mode == "light":
        return "light"
    if pref_mode == "system" and sys.platform == "win32":
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "light" if int(value) == 1 else "dark"
        except OSError:
            return "dark"
    return "dark"


def apply_appearance(mode: str) -> str:
    normalized = "light" if mode == "light" else "dark"
    ctk.set_appearance_mode(normalized)
    ctk.set_default_color_theme(COLOR_THEME)
    return normalized


def tokens(mode: str) -> ThemeTokens:
    return get_tokens(mode)


def title_font() -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_TITLE[0], size=FONT_TITLE[1], weight="bold")


def subtitle_font() -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_SUBTITLE[0], size=FONT_SUBTITLE[1], weight="bold")


def body_font() -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_BODY[0], size=FONT_BODY[1])


def caption_font() -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_CAPTION[0], size=FONT_CAPTION[1])


def mono_font() -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_MONO[0], size=FONT_MONO[1])


def listbox_colors(mode: str) -> dict[str, str]:
    t = get_tokens(mode)
    return {
        "bg": t.list_bg,
        "fg": t.list_fg,
        "selectbackground": t.list_select_bg,
        "selectforeground": t.list_select_fg,
    }
