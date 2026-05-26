"""Keyboard shortcut bindings for the main window."""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Dict, List, Tuple

# (key sequence, description for docs)
APP_SHORTCUTS: List[Tuple[str, str]] = [
    ("<Return>", "Confirmar / ação principal"),
    ("<Escape>", "Fechar overlay ou voltar"),
    ("<Control-c>", "Copiar aba ativa"),
    ("<Control-C>", "Copiar aba ativa"),
    ("<Control-s>", "Salvar como…"),
    ("<Control-S>", "Salvar como…"),
    ("<Control-Shift-C>", "Copiar todas as abas"),
    ("<Control-Shift-c>", "Copiar todas as abas"),
    ("<F5>", "Testar conexão DSN"),
    ("<Control-comma>", "Abrir configurações"),
    ("<Control-Tab>", "Próxima aba (resultados)"),
    ("<Control-Shift-Tab>", "Aba anterior (resultados)"),
]


def bind_app_shortcuts(root: tk.Misc, handlers: Dict[str, Callable]) -> None:
    """Register handlers; keys without handler are skipped."""
    global_bindings = {"<Control-Tab>", "<Control-Shift-Tab>"}
    for sequence, _label in APP_SHORTCUTS:
        handler = handlers.get(sequence)
        if handler is None:
            continue
        if sequence in global_bindings:
            root.bind_all(sequence, handler)
        else:
            root.bind(sequence, handler)
