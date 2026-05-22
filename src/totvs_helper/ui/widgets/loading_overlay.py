"""Loading overlay placed on top of content area."""

from __future__ import annotations

import customtkinter as ctk


class LoadingOverlay(ctk.CTkFrame):
    """Semi-transparent overlay with indeterminate progress."""

    def __init__(self, parent: ctk.CTkBaseClass, **kwargs) -> None:
        super().__init__(parent, corner_radius=0, **kwargs)
        self.place_forget()

        panel = ctk.CTkFrame(self, corner_radius=12)
        panel.place(relx=0.5, rely=0.5, anchor="center")

        self._label = ctk.CTkLabel(
            panel,
            text="Aguarde...",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self._label.pack(padx=40, pady=(24, 12))

        self._progress = ctk.CTkProgressBar(panel, mode="indeterminate", width=280)
        self._progress.pack(padx=40, pady=(0, 24))

    def show(self, message: str) -> None:
        self._label.configure(text=message)
        self._progress.start()
        self.lift()
        self.place(relx=0, rely=0, relwidth=1, relheight=1)

    def hide(self) -> None:
        self._progress.stop()
        self.place_forget()
