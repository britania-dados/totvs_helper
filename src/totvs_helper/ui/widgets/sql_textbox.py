"""Read-only SQL text area with Pygments highlighting."""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional

import customtkinter as ctk
from pygments import lex
from pygments.lexers import TransactSqlLexer
from pygments.token import Comment, Keyword, Name, String

from totvs_helper.ui.design_tokens import FONT_MONO, ThemeTokens


class SqlTextbox(ctk.CTkFrame):
    """Syntax-highlighted read-only SQL viewer."""

    def __init__(self, master: ctk.CTkBaseClass, tokens: ThemeTokens, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._tokens = tokens
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        scrollbar = ctk.CTkScrollbar(self, orientation="vertical")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self._text = tk.Text(
            self,
            wrap="none",
            font=FONT_MONO,
            bg=tokens.list_bg,
            fg=tokens.sql_default,
            insertbackground=tokens.text,
            selectbackground=tokens.list_select_bg,
            selectforeground=tokens.list_select_fg,
            relief="flat",
            borderwidth=0,
            # Force grid weight to dictate size; default 24x80 forces the
            # surrounding card to grow and pushes the layout downwards.
            height=1,
            width=1,
            yscrollcommand=scrollbar.set,
        )
        self._text.grid(row=0, column=0, sticky="nsew")
        scrollbar.configure(command=self._text.yview)

        self._configure_tags()
        self._block_edits()

    def bind_tab_cycle(
        self,
        on_next: Callable[[], None],
        on_prev: Callable[[], None],
    ) -> None:
        """Bind Ctrl+Tab / Ctrl+Shift+Tab on the inner Text widget.

        The Tk Text class registers its own ``<Control-Tab>`` binding that
        moves focus and stops propagation, so ``root.bind_all`` never fires
        for Ctrl+Tab. Binding directly on the widget overrides that.
        """

        def _wrap(callback: Callable[[], None]) -> Callable[[tk.Event], str]:
            def _handler(_event: tk.Event) -> str:
                callback()
                return "break"

            return _handler

        self._text.bind("<Control-Tab>", _wrap(on_next))
        self._text.bind("<Control-Shift-Tab>", _wrap(on_prev))
        self._text.bind("<Control-Key-Tab>", _wrap(on_next))
        self._text.bind("<Control-Shift-Key-Tab>", _wrap(on_prev))

    def _configure_tags(self) -> None:
        t = self._tokens
        self._text.tag_configure("keyword", foreground=t.sql_keyword)
        self._text.tag_configure("string", foreground=t.sql_string)
        self._text.tag_configure("comment", foreground=t.sql_comment)
        self._text.tag_configure("name", foreground=t.sql_name)
        self._text.tag_configure("default", foreground=t.sql_default)

    def _block_edits(self) -> None:
        def handler(event: tk.Event) -> Optional[str]:
            state = int(getattr(event, "state", 0))
            if state & 0x4 and event.keysym.lower() in ("c", "a"):
                return None
            if state & 0x4 and event.keysym == "Tab":
                return None
            if event.keysym in (
                "Left",
                "Right",
                "Up",
                "Down",
                "Home",
                "End",
                "Prior",
                "Next",
            ):
                return None
            return "break"

        self._text.bind("<Key>", handler)

    def set_text(self, content: str) -> None:
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        if not content:
            self._text.configure(state="disabled")
            return

        lexer = TransactSqlLexer()
        for token_type, value in lex(content, lexer):
            if token_type in Comment:
                tag = "comment"
            elif token_type in String:
                tag = "string"
            elif token_type in Keyword:
                tag = "keyword"
            elif token_type in Name:
                tag = "name"
            else:
                tag = "default"
            self._text.insert("end", value, (tag,))

        self._text.configure(state="disabled")

    def get_text(self) -> str:
        return self._text.get("1.0", "end").strip()

    def update_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self._text.configure(bg=tokens.list_bg, fg=tokens.sql_default)
        self._configure_tags()
