"""Scrollable tabular preview for sample rows (browser-style grid)."""

from __future__ import annotations

from tkinter import ttk
from typing import List, Optional, Sequence, Tuple

import customtkinter as ctk

from totvs_helper.infra.odbc_client import FieldMeta, TableIndexRow
from totvs_helper.ui.design_tokens import FONT_MONO, ThemeTokens

INDEX_COLUMN = "#"
DEFAULT_COL_WIDTH = 120
COMPACT_COL_WIDTH = 88
INDEX_COL_WIDTH = 52
MAX_CELL_LEN = 200


def format_cell(value: object) -> str:
    if value is None:
        return "NULL"
    text = str(value).replace("\n", " ").replace("\r", " ")
    if len(text) > MAX_CELL_LEN:
        return text[: MAX_CELL_LEN - 1] + "…"
    return text


class SampleDataGrid(ctk.CTkFrame):
    """Treeview grid with horizontal and vertical scrollbars."""

    _style_counter = 0

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        tokens: ThemeTokens,
        *,
        compact: bool = False,
        preview: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._tokens = tokens
        self._compact = compact
        self._preview = preview
        if preview:
            self._col_width = 72 if compact else 96
            self._row_height = 22 if compact else 24
        else:
            self._col_width = COMPACT_COL_WIDTH if compact else DEFAULT_COL_WIDTH
            self._row_height = 20 if compact else 24
        SampleDataGrid._style_counter += 1
        self._style = f"TotvsHelper.Sample.Treeview.{self._style_counter}"
        self._apply_style()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._container = ctk.CTkFrame(self, fg_color=tokens.list_bg, corner_radius=8)
        self._container.grid(row=0, column=0, sticky="nsew")
        self._container.grid_columnconfigure(0, weight=1)
        self._container.grid_rowconfigure(0, weight=1)

        self._tree = ttk.Treeview(
            self._container,
            show="headings",
            selectmode="browse",
            style=self._style,
        )
        self._tree.grid(row=0, column=0, sticky="nsew")

        y_scroll = ctk.CTkScrollbar(
            self._container, orientation="vertical", command=self._tree.yview
        )
        y_scroll.grid(row=0, column=1, sticky="ns")

        x_scroll = ctk.CTkScrollbar(
            self._container, orientation="horizontal", command=self._tree.xview
        )
        x_scroll.grid(row=1, column=0, sticky="ew")

        self._tree.configure(
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
        )

        self._message = ctk.CTkLabel(
            self,
            text="",
            text_color=tokens.text_muted,
            font=ctk.CTkFont(size=12),
            anchor="w",
            justify="left",
        )
        self._message.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        self._message.grid_remove()

        self._column_signature: Optional[Tuple[str, ...]] = None
        self._ensure_stripe_tags()

    @staticmethod
    def stripe_tags_for_groups(group_keys: Sequence[str]) -> List[str]:
        """Alternate stripe tag each time the group key (e.g. index name) changes."""
        tags: List[str] = []
        current_group: Optional[str] = None
        stripe = 0
        for key in group_keys:
            if current_group is not None and key != current_group:
                stripe = 1 - stripe
            current_group = key
            tags.append("stripe_even" if stripe == 0 else "stripe_odd")
        return tags

    def _ensure_stripe_tags(self) -> None:
        t = self._tokens
        self._tree.tag_configure(
            "stripe_even",
            background=t.list_bg,
            foreground=t.list_fg,
        )
        self._tree.tag_configure(
            "stripe_odd",
            background=t.surface_alt,
            foreground=t.list_fg,
        )

    def _apply_style(self) -> None:
        t = self._tokens
        style = ttk.Style(self)
        style.theme_use("clam")
        tree_layout = style.layout("Treeview")
        if tree_layout:
            style.layout(self._style, tree_layout)
        body_font_size = 10 if (self._preview and self._compact) else (
            11 if self._compact else FONT_MONO[1]
        )
        heading_font_size = 10 if self._compact else 11
        style.configure(
            self._style,
            background=t.list_bg,
            foreground=t.list_fg,
            fieldbackground=t.list_bg,
            bordercolor=t.border,
            lightcolor=t.border,
            darkcolor=t.border,
            rowheight=self._row_height,
            font=(FONT_MONO[0], body_font_size),
        )
        style.configure(
            f"{self._style}.Heading",
            background=t.surface_alt,
            foreground=t.text,
            relief="flat",
            font=(FONT_MONO[0], heading_font_size, "bold"),
        )
        style.map(
            self._style,
            background=[("selected", t.list_select_bg)],
            foreground=[("selected", t.list_select_fg)],
        )

    def scroll_to_start(self) -> None:
        self._tree.yview_moveto(0)
        self._tree.xview_moveto(0)

    def clear(self) -> None:
        self._tree.delete(*self._tree.get_children())
        for col in self._tree["columns"]:
            self._tree.heading(col, text="")
            self._tree.column(col, width=0)
        self._tree.configure(columns=())
        self._column_signature = None
        self._hide_message()

    def show_message(self, text: str, *, error: bool = False) -> None:
        self.clear()
        self._container.grid_remove()
        self._message.configure(
            text=text,
            text_color=self._tokens.danger if error else self._tokens.text_muted,
        )
        self._message.grid()

    def _hide_message(self) -> None:
        self._message.grid_remove()
        self._container.grid()

    def _configure_columns(self, display_columns: List[str]) -> None:
        self._tree.configure(columns=display_columns)
        for name in display_columns:
            if name == INDEX_COLUMN:
                self._tree.heading(INDEX_COLUMN, text=INDEX_COLUMN, anchor="center")
                self._tree.column(
                    INDEX_COLUMN,
                    width=INDEX_COL_WIDTH,
                    minwidth=INDEX_COL_WIDTH,
                    stretch=False,
                    anchor="center",
                )
            else:
                self._tree.heading(name, text=name, anchor="w")
                self._tree.column(
                    name,
                    width=self._col_width,
                    minwidth=56 if self._compact else 72,
                    stretch=False,
                    anchor="w",
                )

    def set_data(
        self,
        columns: List[str],
        rows: List[Tuple],
        *,
        row_offset: int = 0,
        scroll_to_top: bool = True,
        stripe_groups: Optional[Sequence[str]] = None,
    ) -> None:
        if not columns:
            self.show_message("Nenhuma coluna disponível para exibir.")
            return

        self._hide_message()
        display_columns = [INDEX_COLUMN, *columns]
        signature = tuple(display_columns)
        values = self._build_row_values(columns, rows, row_offset)

        if stripe_groups is not None and len(stripe_groups) != len(rows):
            stripe_groups = None

        if stripe_groups is None and signature == self._column_signature:
            children = self._tree.get_children()
            if len(children) == len(values):
                for item_id, row_values in zip(children, values):
                    self._tree.item(item_id, values=row_values)
                if scroll_to_top:
                    self.scroll_to_start()
                return

        self._column_signature = signature
        self._tree.delete(*self._tree.get_children())
        self._configure_columns(display_columns)
        self._ensure_stripe_tags()
        row_tags: List[Tuple[str, ...]] = [()] * len(values)
        if stripe_groups is not None:
            row_tags = [(tag,) for tag in self.stripe_tags_for_groups(stripe_groups)]

        for row_values, tags in zip(values, row_tags):
            self._tree.insert("", "end", values=row_values, tags=tags)

        if scroll_to_top:
            self.scroll_to_start()

    @staticmethod
    def _build_row_values(
        columns: List[str],
        rows: List[Tuple],
        row_offset: int,
    ) -> List[Tuple[str, ...]]:
        values: List[Tuple[str, ...]] = []
        for index, row in enumerate(rows):
            row_values: List[str] = [str(row_offset + index + 1)]
            for col_index, _name in enumerate(columns):
                cell = row[col_index] if col_index < len(row) else None
                row_values.append(format_cell(cell))
            values.append(tuple(row_values))
        return values

    def set_metadata(
        self,
        fields: List[FieldMeta],
        pk_fields: List[str],
    ) -> None:
        """Populate grid with ODBC field metadata (all columns)."""
        if not fields:
            self.show_message("Nenhum campo encontrado.")
            return

        pk_set = {str(name) for name in pk_fields}
        columns = ["Campo", "Tipo", "Largura", "Decimais", "Fetch", "PK"]
        rows: List[Tuple] = []
        for field in fields:
            rows.append(
                (
                    field.name,
                    field.data_type,
                    str(field.width),
                    str(field.decimals),
                    field.fetch_datatype,
                    "sim" if field.name in pk_set else "",
                )
            )
        self.set_data(columns, rows, scroll_to_top=True)

    def set_indexes(self, index_rows: List[TableIndexRow]) -> None:
        """Populate grid with index name, field, order, unique and primary flags."""
        if not index_rows:
            self.show_message("Nenhum índice encontrado.")
            return

        columns = ["Índice", "Campo", "Ordem", "Único", "Primário"]
        rows: List[Tuple] = []
        for row in index_rows:
            rows.append(
                (
                    row.index_name,
                    row.field_name,
                    str(row.field_order),
                    "sim" if row.is_unique else "",
                    "sim" if row.is_primary else "",
                )
            )
        stripe_groups = [row.index_name for row in index_rows]
        self.set_data(columns, rows, scroll_to_top=True, stripe_groups=stripe_groups)

    def update_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self._container.configure(fg_color=tokens.list_bg)
        self._apply_style()
        self._ensure_stripe_tags()
