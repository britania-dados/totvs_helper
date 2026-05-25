"""Generated scripts results screen."""

from __future__ import annotations

from typing import Callable, Dict, List, Tuple

import customtkinter as ctk

from totvs_helper.ui.design_tokens import RADIUS, SPACING, ThemeTokens
from totvs_helper.ui.theme import subtitle_font
from totvs_helper.ui.widgets.icon_button import IconButton
from totvs_helper.ui.widgets.sql_textbox import SqlTextbox

TAB_DEFS: List[Tuple[str, str]] = [
    ("Query ETL", "query_etl"),
    ("Diferencial SSIS", "differential"),
    ("DDL CREATE", "ddl_create"),
    ("UPDATE", "script_update"),
    ("DELETE", "script_delete"),
]

TAB_LABELS = [label for label, _ in TAB_DEFS]
TAB_KEYS = [key for _, key in TAB_DEFS]
TAB_BY_LABEL = {label: key for label, key in TAB_DEFS}


class ResultsScreen(ctk.CTkFrame):
    """Script viewer with segmented tabs and full-height editor."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        tokens: ThemeTokens,
        *,
        on_copy_tab: Callable[[], None],
        on_copy_all: Callable[[], None],
        on_save: Callable[[], None],
        on_save_default: Callable[[], None],
        on_script_options_changed: Callable[[], None],
        on_generate_pentaho: Callable[[], None],
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._tokens = tokens
        self._on_script_options_changed = on_script_options_changed
        self._on_generate_pentaho = on_generate_pentaho
        self._updating_options = False
        self._active_key = "query_etl"
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        page_header = ctk.CTkFrame(self, fg_color="transparent")
        page_header.grid(row=0, column=0, sticky="ew", padx=4, pady=(12, 8))
        page_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            page_header,
            text="Scripts gerados",
            font=subtitle_font(),
            text_color=tokens.text,
            anchor="w",
            height=36,
        ).grid(row=0, column=0, sticky="w")

        actions = ctk.CTkFrame(page_header, fg_color="transparent")
        actions.grid(row=0, column=1, sticky="e")

        IconButton(
            actions,
            tokens,
            text="Copiar aba",
            icon="📋",
            variant="ghost",
            command=on_copy_tab,
            width=118,
        ).pack(side="left", padx=3)
        IconButton(
            actions,
            tokens,
            text="Copiar tudo",
            icon="📑",
            variant="ghost",
            command=on_copy_all,
            width=118,
        ).pack(side="left", padx=3)
        IconButton(
            actions,
            tokens,
            text="Salvar TXT",
            icon="💾",
            variant="primary",
            command=on_save,
            width=118,
        ).pack(side="left", padx=3)
        IconButton(
            actions,
            tokens,
            text="Pasta padrão",
            icon="📁",
            variant="secondary",
            command=on_save_default,
            width=130,
        ).pack(side="left", padx=3)

        self._context_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._context_frame.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 8))
        self._context_frame.grid_columnconfigure(4, weight=1)

        self._dsn_chip = ctk.CTkLabel(
            self._context_frame,
            text="",
            fg_color=tokens.surface_alt,
            corner_radius=6,
            font=ctk.CTkFont(size=11),
            height=26,
        )
        self._dsn_chip.grid(row=0, column=0, padx=(0, 6), pady=4, sticky="w")

        self._table_chip = ctk.CTkLabel(
            self._context_frame,
            text="",
            fg_color=tokens.surface_alt,
            corner_radius=6,
            font=ctk.CTkFont(size=11),
            height=26,
        )
        self._table_chip.grid(row=0, column=1, padx=(0, SPACING["lg"]), pady=4, sticky="w")

        self._switch_free_fields = ctk.CTkSwitch(
            self._context_frame,
            text="Campos livres",
            font=ctk.CTkFont(size=12),
            command=self._on_script_option_changed,
        )
        self._switch_free_fields.grid(row=0, column=2, padx=(0, SPACING["lg"]), pady=4, sticky="w")

        self._switch_multi_company = ctk.CTkSwitch(
            self._context_frame,
            text="Multi-empresa",
            font=ctk.CTkFont(size=12),
            command=self._on_script_option_changed,
        )
        self._switch_multi_company.grid(row=0, column=3, pady=4, sticky="w")

        self._export_bar = ctk.CTkFrame(
            self,
            fg_color=tokens.surface,
            border_color=tokens.border,
            border_width=1,
            corner_radius=RADIUS["md"],
        )
        self._export_bar.grid(row=2, column=0, sticky="ew", padx=4, pady=(0, 12))
        self._export_bar.grid_columnconfigure(0, weight=1)

        self._pentaho_btn = ctk.CTkButton(
            self._export_bar,
            text="Gerar carga Pentaho (PDI)",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=52,
            fg_color=tokens.accent,
            hover_color=tokens.accent_hover,
            text_color="#ffffff",
            corner_radius=RADIUS["md"],
            command=on_generate_pentaho,
        )
        self._pentaho_btn.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=SPACING["md"],
            pady=SPACING["md"],
        )

        self._script_card = ctk.CTkFrame(
            self,
            fg_color=tokens.surface,
            border_color=tokens.border,
            border_width=1,
            corner_radius=RADIUS["lg"],
        )
        self._script_card.grid(row=3, column=0, sticky="nsew", padx=4, pady=(0, 4))
        self._script_card.grid_columnconfigure(0, weight=1)
        self._script_card.grid_rowconfigure(2, weight=1)

        self._segmented = ctk.CTkSegmentedButton(
            self._script_card,
            values=TAB_LABELS,
            command=self._on_segment_changed,
            height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
            selected_color=tokens.accent,
            selected_hover_color=tokens.accent_hover,
            unselected_color=tokens.surface_alt,
            unselected_hover_color=tokens.border,
        )
        self._segmented.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=SPACING["md"],
            pady=(SPACING["md"], SPACING["sm"]),
        )
        self._segmented.set("Query ETL")

        ctk.CTkFrame(
            self._script_card,
            height=1,
            fg_color=tokens.border,
        ).grid(row=1, column=0, sticky="ew", padx=SPACING["md"])

        self._editor_host = ctk.CTkFrame(
            self._script_card,
            fg_color=tokens.list_bg,
            corner_radius=RADIUS["md"],
        )
        self._editor_host.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=SPACING["md"],
            pady=(SPACING["sm"], SPACING["md"]),
        )
        self._editor_host.grid_columnconfigure(0, weight=1)
        self._editor_host.grid_rowconfigure(0, weight=1)

        self._editors: Dict[str, SqlTextbox] = {}
        for label, key in TAB_DEFS:
            editor = SqlTextbox(self._editor_host, tokens)
            editor.grid(row=0, column=0, sticky="nsew")
            editor.bind_tab_cycle(
                on_next=lambda: self.cycle_tab(1),
                on_prev=lambda: self.cycle_tab(-1),
            )
            self._editors[key] = editor

        self._show_tab("query_etl")

    def _on_script_option_changed(self) -> None:
        if self._updating_options:
            return
        self._on_script_options_changed()

    def _on_segment_changed(self, value: str) -> None:
        key = TAB_BY_LABEL.get(value)
        if key:
            self._show_tab(key)

    def _show_tab(self, key: str) -> None:
        self._active_key = key
        for editor_key, editor in self._editors.items():
            if editor_key == key:
                editor.grid(row=0, column=0, sticky="nsew")
            else:
                editor.grid_remove()

    def cycle_tab(self, delta: int) -> None:
        """Select next (1) or previous (-1) script tab."""
        try:
            index = TAB_KEYS.index(self._active_key)
        except ValueError:
            index = 0
        new_index = (index + delta) % len(TAB_KEYS)
        label, key = TAB_DEFS[new_index]
        self._segmented.set(label)
        self._show_tab(key)

    def set_context(
        self,
        dsn: str,
        table: str,
        *,
        include_free_fields: bool,
        multi_company: bool,
    ) -> None:
        """Show DSN/table chips and sync option switches without firing callbacks."""
        self._dsn_chip.configure(text=f"  DSN: {dsn}  ")
        self._table_chip.configure(text=f"  Tabela: {table}  ")
        self.set_script_options(include_free_fields, multi_company)

    def set_script_options(
        self, include_free_fields: bool, multi_company: bool
    ) -> None:
        """Update switches without triggering regeneration."""
        self._updating_options = True
        try:
            if include_free_fields:
                self._switch_free_fields.select()
            else:
                self._switch_free_fields.deselect()
            if multi_company:
                self._switch_multi_company.select()
            else:
                self._switch_multi_company.deselect()
        finally:
            self._updating_options = False

    def get_script_options(self) -> Tuple[bool, bool]:
        return (
            bool(self._switch_free_fields.get()),
            bool(self._switch_multi_company.get()),
        )

    def set_scripts(self, mapping: Dict[str, str]) -> None:
        for key, editor in self._editors.items():
            editor.set_text(mapping.get(key, ""))

    def get_active_text(self) -> str:
        editor = self._editors.get(self._active_key)
        return editor.get_text() if editor else ""

    def get_active_label(self) -> str:
        for label, key in TAB_DEFS:
            if key == self._active_key:
                return label
        return ""

    def get_all_text(self) -> Dict[str, str]:
        return {key: editor.get_text() for key, editor in self._editors.items()}

    def update_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self._export_bar.configure(
            fg_color=tokens.surface,
            border_color=tokens.border,
        )
        self._pentaho_btn.configure(
            fg_color=tokens.accent,
            hover_color=tokens.accent_hover,
        )
        self._script_card.configure(
            fg_color=tokens.surface,
            border_color=tokens.border,
        )
        self._editor_host.configure(fg_color=tokens.list_bg)
        for chip in (self._dsn_chip, self._table_chip):
            chip.configure(fg_color=tokens.surface_alt)
        for editor in self._editors.values():
            editor.update_tokens(tokens)
