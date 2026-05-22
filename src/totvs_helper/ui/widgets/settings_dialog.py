"""Settings modal dialog."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import customtkinter as ctk

from totvs_helper.ui.design_tokens import SPACING, ThemeTokens
from totvs_helper.ui.preferences import UserPreferences
from totvs_helper.ui.tk_dialogs import ask_directory


class SettingsDialog(ctk.CTkToplevel):
    """Modal preferences editor."""

    def __init__(
        self,
        parent: ctk.CTk,
        tokens: ThemeTokens,
        prefs: UserPreferences,
        *,
        on_save: Callable[[UserPreferences], None],
    ) -> None:
        super().__init__(parent)
        self._tokens = tokens
        self._prefs = prefs
        self._on_save = on_save

        self.title("Configurações")
        self.geometry("480x420")
        self.transient(parent)
        self.grab_set()

        body = ctk.CTkFrame(self, fg_color=tokens.surface)
        body.pack(fill="both", expand=True, padx=SPACING["lg"], pady=SPACING["lg"])
        body.grid_columnconfigure(1, weight=1)

        row = 0
        ctk.CTkLabel(
            body,
            text="Configurações",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=tokens.text,
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, SPACING["lg"]))
        row += 1

        ctk.CTkLabel(body, text="Aparência", text_color=tokens.text_muted).grid(
            row=row, column=0, sticky="w"
        )
        self._appearance = ctk.CTkOptionMenu(
            body,
            values=["dark", "light", "system"],
        )
        self._appearance.set(prefs.appearance_mode)
        self._appearance.grid(row=row, column=1, sticky="ew", pady=SPACING["sm"])
        row += 1

        ctk.CTkLabel(
            body, text="Pasta padrão de exportação", text_color=tokens.text_muted
        ).grid(row=row, column=0, sticky="w", pady=(SPACING["md"], 0))
        export_row = ctk.CTkFrame(body, fg_color="transparent")
        export_row.grid(row=row, column=1, sticky="ew", pady=(SPACING["md"], 0))
        export_row.grid_columnconfigure(0, weight=1)

        self._export_dir = ctk.CTkEntry(export_row)
        self._export_dir.insert(0, prefs.default_export_dir or prefs.export_directory())
        self._export_dir.grid(row=0, column=0, sticky="ew", padx=(0, SPACING["sm"]))

        ctk.CTkButton(
            export_row,
            text="...",
            width=40,
            command=self._browse_export_dir,
        ).grid(row=0, column=1)
        row += 1

        self._ask_open = ctk.CTkCheckBox(
            body,
            text="Perguntar antes de abrir pasta após salvar",
        )
        if prefs.ask_open_folder:
            self._ask_open.select()
        self._ask_open.grid(
            row=row, column=0, columnspan=2, sticky="w", pady=SPACING["lg"]
        )
        row += 1

        actions = ctk.CTkFrame(body, fg_color="transparent")
        actions.grid(
            row=row, column=0, columnspan=2, sticky="e", pady=(SPACING["lg"], 0)
        )

        ctk.CTkButton(
            actions,
            text="Cancelar",
            fg_color="transparent",
            border_width=1,
            border_color=tokens.border,
            command=self.destroy,
        ).pack(side="left", padx=(0, SPACING["sm"]))

        ctk.CTkButton(
            actions,
            text="Salvar",
            fg_color=tokens.accent,
            hover_color=tokens.accent_hover,
            command=self._save,
        ).pack(side="left")

    def _browse_export_dir(self) -> None:
        parent = self.winfo_toplevel()
        folder = ask_directory(
            parent=parent,
            title="Pasta padrão de exportação",
            initialdir=self._export_dir.get() or str(Path.home()),
        )
        if folder:
            self._export_dir.delete(0, "end")
            self._export_dir.insert(0, folder)

    def _save(self) -> None:
        self._prefs.appearance_mode = self._appearance.get()
        export = self._export_dir.get().strip()
        self._prefs.default_export_dir = export or None
        self._prefs.ask_open_folder = bool(self._ask_open.get())
        self._on_save(self._prefs)
        self.destroy()
