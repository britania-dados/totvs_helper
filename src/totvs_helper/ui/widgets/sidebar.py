"""Vertical sidebar navigation."""

from __future__ import annotations

from typing import Callable, Dict, Optional

import customtkinter as ctk

from totvs_helper.ui.design_tokens import SPACING, ThemeTokens
from totvs_helper.ui.state import SidebarView


class Sidebar(ctk.CTkFrame):
    """Left navigation rail for wizard and history."""

    NAV_ITEMS = (
        (SidebarView.DSN, "🔌", "Conexão"),
        (SidebarView.TABLE, "📋", "Tabela"),
        (SidebarView.RESULTS, "📄", "Scripts"),
        (SidebarView.HISTORY, "🕘", "Histórico"),
    )

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        tokens: ThemeTokens,
        *,
        on_navigate: Callable[[SidebarView], None],
        on_settings: Callable[[], None],
        app_title: str,
        version: str,
        width: int = 220,
    ) -> None:
        super().__init__(
            master,
            width=width,
            fg_color=tokens.sidebar_bg,
            corner_radius=0,
        )
        self._tokens = tokens
        self._on_navigate = on_navigate
        self._on_settings = on_settings
        self._active = SidebarView.DSN
        self._buttons: Dict[SidebarView, ctk.CTkButton] = {}
        self._states: Dict[SidebarView, str] = {
            v: "disabled" for v, _, _ in self.NAV_ITEMS
        }

        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text=app_title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=tokens.text,
        ).grid(row=0, column=0, sticky="w", padx=SPACING["lg"], pady=(SPACING["xl"], 4))

        ctk.CTkLabel(
            self,
            text=f"v{version}",
            font=ctk.CTkFont(size=11),
            text_color=tokens.text_muted,
        ).grid(row=1, column=0, sticky="w", padx=SPACING["lg"], pady=(0, SPACING["lg"]))

        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.grid(row=2, column=0, sticky="nsew", padx=SPACING["sm"])
        self.grid_rowconfigure(2, weight=1)

        for index, (view, icon, label) in enumerate(self.NAV_ITEMS):
            btn = ctk.CTkButton(
                nav,
                text=f"  {icon}  {label}",
                anchor="w",
                height=40,
                fg_color="transparent",
                hover_color=tokens.surface_alt,
                command=lambda v=view: self._navigate(v),
            )
            btn.pack(fill="x", pady=3)
            self._buttons[view] = btn

        self._connection_badge = ctk.CTkLabel(
            self,
            text="● Desconectado",
            font=ctk.CTkFont(size=11),
            text_color=tokens.text_muted,
        )
        self._connection_badge.grid(
            row=3, column=0, sticky="sw", padx=SPACING["lg"], pady=SPACING["md"]
        )

        ctk.CTkButton(
            self,
            text="⚙ Configurações",
            height=36,
            fg_color="transparent",
            border_width=1,
            border_color=tokens.border,
            hover_color=tokens.surface_alt,
            command=on_settings,
        ).grid(
            row=4, column=0, sticky="sew", padx=SPACING["lg"], pady=(0, SPACING["lg"])
        )

        self.set_active(SidebarView.DSN)

    def _navigate(self, view: SidebarView) -> None:
        if self._states.get(view) == "disabled":
            return
        self._on_navigate(view)

    def set_active(self, view: SidebarView) -> None:
        self._active = view
        self._refresh_styles()

    def set_item_state(self, view: SidebarView, state: str) -> None:
        """state: disabled | idle | active | done"""
        self._states[view] = state
        self._refresh_styles()

    def set_connected(self, connected: bool, dsn: Optional[str] = None) -> None:
        t = self._tokens
        if connected:
            text = "● Conectado"
            if dsn:
                text = f"● {dsn[:18]}"
            self._connection_badge.configure(text=text, text_color=t.success)
        else:
            self._connection_badge.configure(
                text="● Desconectado", text_color=t.text_muted
            )

    def update_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.configure(fg_color=tokens.sidebar_bg)
        self._refresh_styles()

    def _refresh_styles(self) -> None:
        t = self._tokens
        for view, btn in self._buttons.items():
            state = self._states.get(view, "disabled")
            if state == "disabled":
                btn.configure(
                    state="disabled", fg_color="transparent", text_color=t.text_muted
                )
            elif view == self._active:
                btn.configure(
                    state="normal",
                    fg_color=t.sidebar_active,
                    text_color=t.accent,
                    hover_color=t.sidebar_active,
                )
            elif state == "done":
                btn.configure(
                    state="normal",
                    fg_color="transparent",
                    text_color=t.success,
                    hover_color=t.surface_alt,
                )
            else:
                btn.configure(
                    state="normal",
                    fg_color="transparent",
                    text_color=t.text,
                    hover_color=t.surface_alt,
                )
