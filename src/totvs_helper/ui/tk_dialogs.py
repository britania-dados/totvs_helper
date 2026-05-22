"""Tk dialogs bound to the application root (avoids orphan 'tk' windows)."""

from __future__ import annotations

from tkinter import filedialog, messagebox
from typing import Optional

import customtkinter as ctk


def _tk_parent(master: ctk.CTk) -> ctk.CTk:
    return master


def ask_ok_cancel(title: str, message: str, *, parent: ctk.CTk) -> bool:
    return bool(messagebox.askokcancel(title, message, parent=_tk_parent(parent)))


def ask_yes_no(title: str, message: str, *, parent: ctk.CTk) -> bool:
    return bool(messagebox.askyesno(title, message, parent=_tk_parent(parent)))


def show_error(title: str, message: str, *, parent: Optional[ctk.CTk] = None) -> None:
    if parent is not None:
        messagebox.showerror(title, message, parent=_tk_parent(parent))
    else:
        messagebox.showerror(title, message)


def ask_save_filename(
    *,
    parent: ctk.CTk,
    title: str,
    defaultextension: str,
    initialdir: str,
    initialfile: str,
    filetypes: list[tuple[str, str]],
) -> str:
    return filedialog.asksaveasfilename(
        parent=_tk_parent(parent),
        title=title,
        defaultextension=defaultextension,
        initialdir=initialdir,
        initialfile=initialfile,
        filetypes=filetypes,
    )


def ask_directory(
    *,
    parent: ctk.CTk,
    title: str,
    initialdir: str,
) -> str:
    return filedialog.askdirectory(
        parent=_tk_parent(parent),
        title=title,
        initialdir=initialdir,
    )
