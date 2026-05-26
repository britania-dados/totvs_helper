"""Lightweight startup splash (tk only).

Avoids loading CustomTkinter before the main UI is ready.
"""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from totvs_helper.version import __version__

_BG = "#141414"
_SURFACE = "#1f1f1f"
_TEXT = "#f3f4f6"
_MUTED = "#9ca3af"
_ACCENT = "#c8102e"
_WINDOW_SIZE = (520, 340)


def resolve_assets_dir() -> Path:
    """Return directory containing bundled icons and logos."""
    from totvs_helper.paths import assets_dir

    return assets_dir()


def close_pyinstaller_splash() -> None:
    """Close PyInstaller bootloader splash; it stays open until this runs."""
    if not getattr(sys, "frozen", False):
        return
    try:
        import pyi_splash
    except ImportError:
        return
    try:
        if pyi_splash.is_alive():
            pyi_splash.close()
    except (AttributeError, OSError):
        pass


class StartupSplash:
    """Borderless splash shown while the main UI loads."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.configure(bg=_BG)
        self.root.resizable(False, False)
        self._apply_icon()

        outer = tk.Frame(self.root, bg=_BG)
        outer.pack(fill="both", expand=True)

        tk.Frame(outer, bg=_ACCENT, height=4).pack(fill="x")

        card = tk.Frame(
            outer,
            bg=_SURFACE,
            highlightbackground="#3a3a3a",
            highlightthickness=1,
        )
        card.pack(fill="both", expand=True, padx=16, pady=16)

        logo_path = resolve_assets_dir() / "splash_logo_ui.png"
        if not logo_path.exists():
            logo_path = resolve_assets_dir() / "totvs_helper_logo.png"

        self._logo_photo = None
        if logo_path.exists():
            try:
                self._logo_photo = tk.PhotoImage(file=str(logo_path))
                subsample = max(1, self._logo_photo.width() // 220)
                if subsample > 1:
                    self._logo_photo = self._logo_photo.subsample(subsample, subsample)
                tk.Label(card, image=self._logo_photo, bg=_SURFACE).pack(pady=(20, 8))
            except tk.TclError:
                pass

        tk.Label(
            card,
            text="Totvs Helper",
            font=("Segoe UI", 16, "bold"),
            fg=_TEXT,
            bg=_SURFACE,
        ).pack()

        tk.Label(
            card,
            text=f"Versão {__version__}",
            font=("Segoe UI", 10),
            fg=_MUTED,
            bg=_SURFACE,
        ).pack(pady=(2, 16))

        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Splash.Horizontal.TProgressbar",
            troughcolor="#2a2a2a",
            background=_ACCENT,
            bordercolor="#2a2a2a",
            lightcolor=_ACCENT,
            darkcolor=_ACCENT,
        )
        self._progress = ttk.Progressbar(
            card,
            mode="indeterminate",
            length=360,
            style="Splash.Horizontal.TProgressbar",
        )
        self._progress.pack(padx=32, pady=(0, 10))
        self._progress.start(12)

        self._status = tk.Label(
            card,
            text="Iniciando...",
            font=("Segoe UI", 10),
            fg=_MUTED,
            bg=_SURFACE,
        )
        self._status.pack(pady=(0, 20))

        self._center_window()

    def _center_window(self) -> None:
        width, height = _WINDOW_SIZE
        self.root.update_idletasks()
        x = max(0, (self.root.winfo_screenwidth() - width) // 2)
        y = max(0, (self.root.winfo_screenheight() - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _apply_icon(self) -> None:
        ico = resolve_assets_dir() / "totvs_helper.ico"
        if ico.exists():
            try:
                self.root.iconbitmap(str(ico))
            except tk.TclError:
                pass

    def set_message(self, message: str) -> None:
        self._status.configure(text=message)
        self.pump()

    def pump(self) -> None:
        self.root.update_idletasks()
        self.root.update()

    def show(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.pump()
        self.root.after(200, lambda: self.root.attributes("-topmost", False))

    def close(self) -> None:
        try:
            self._progress.stop()
        except tk.TclError:
            pass
        # If another Tk root already exists (the app), make sure it stays as
        # the tkinter default; otherwise destroying this root would leave
        # _default_root = None and break later CTkFont/widget creations.
        previous_default = getattr(tk, "_default_root", None)
        try:
            self.root.destroy()
        except tk.TclError:
            pass
        if previous_default is not None and previous_default is not self.root:
            tk._default_root = previous_default
