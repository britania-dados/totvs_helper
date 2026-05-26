"""Toast notification manager."""

from __future__ import annotations

import customtkinter as ctk

from totvs_helper.ui.design_tokens import ThemeTokens

TOAST_DURATION_MS = 3500
TOAST_GAP = 8
TOAST_WRAP = 420
TOAST_FONT_SIZE = 18
TOAST_ICON_FONT_SIZE = 20
# Nudge from geometric center of Sair…Continuar gap (position only).
TOAST_SHIFT_X_RATIO = 0.175
TOAST_SHIFT_Y_RATIO = -0.10
TOAST_LIFT_PX = 8
TOAST_CHROME_WIDTH = 52


class ToastManager:
    """Footer toasts between anchor widgets (Sair … Continuar); click to dismiss."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        tokens: ThemeTokens,
        *,
        anchor_left: ctk.CTkBaseClass,
        anchor_right: ctk.CTkBaseClass,
    ) -> None:
        self._parent = parent
        self._tokens = tokens
        self._anchor_left = anchor_left
        self._anchor_right = anchor_right
        self._toasts: list[ctk.CTkFrame] = []
        parent.bind("<Configure>", self._on_parent_configure, add="+")

    def update_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens

    def _on_parent_configure(self, _event: object = None) -> None:
        if self._toasts:
            self._reposition()

    def show(self, message: str, kind: str = "info") -> None:
        while self._toasts:
            self._dismiss(self._toasts[0])

        style = _style_for_kind(kind, self._tokens)

        frame = ctk.CTkFrame(
            self._parent,
            fg_color=style["bg"],
            corner_radius=8,
            border_width=1,
            border_color=style["border"],
            cursor="hand2",
        )

        stripe = ctk.CTkFrame(
            frame,
            width=3,
            height=1,
            corner_radius=0,
            fg_color=style["stripe"],
        )
        stripe.pack(side="left", fill="y", padx=(0, 0), pady=0)
        stripe.pack_propagate(False)

        body = ctk.CTkFrame(frame, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=(10, 12), pady=11)

        bind_targets = [frame, stripe, body]
        if style["icon"]:
            icon = ctk.CTkLabel(
                body,
                text=style["icon"],
                font=ctk.CTkFont(size=TOAST_ICON_FONT_SIZE, weight="bold"),
                text_color=style["stripe"],
                width=18,
            )
            icon.pack(side="left", padx=(0, 6))
            bind_targets.append(icon)

        wrap = self._wraplength_for_gap()
        label = ctk.CTkLabel(
            body,
            text=message,
            text_color=style["fg"],
            font=ctk.CTkFont(size=TOAST_FONT_SIZE),
            wraplength=wrap,
            justify="left",
            anchor="w",
        )
        label.pack(side="left", fill="x", expand=True)
        bind_targets.append(label)

        for widget in bind_targets:
            widget.bind("<Button-1>", lambda _e, f=frame: self._dismiss(f))

        self._toasts.append(frame)
        frame.update_idletasks()
        self._reposition()
        self._parent.after_idle(self._reposition)

        timer_id = frame.after(TOAST_DURATION_MS, lambda f=frame: self._dismiss(f))
        frame._toast_timer_id = timer_id  # type: ignore[attr-defined]

    def _dismiss(self, frame: ctk.CTkFrame) -> None:
        if frame not in self._toasts:
            return
        timer_id = getattr(frame, "_toast_timer_id", None)
        if timer_id is not None:
            try:
                frame.after_cancel(timer_id)
            except Exception:
                pass
        self._toasts.remove(frame)
        frame.destroy()
        self._reposition()

    def _gap_metrics(self) -> tuple[int, int, int, int, int, int] | None:
        self._parent.update_idletasks()
        self._anchor_left.update_idletasks()
        self._anchor_right.update_idletasks()
        try:
            px = self._parent.winfo_rootx()
            py = self._parent.winfo_rooty()
            gap_left = self._anchor_left.winfo_rootx() + self._anchor_left.winfo_width()
            gap_right = self._anchor_right.winfo_rootx()
            row_top = self._anchor_left.winfo_rooty()
            row_height = self._anchor_left.winfo_height()
        except Exception:
            return None
        if gap_right <= gap_left:
            return None
        return gap_left, gap_right, row_top, row_height, px, py

    def _wraplength_for_gap(self) -> int:
        metrics = self._gap_metrics()
        if metrics is None:
            return TOAST_WRAP
        gap_left, gap_right, _, _, _, _ = metrics
        gap_width = gap_right - gap_left
        return max(280, min(TOAST_WRAP, gap_width - TOAST_CHROME_WIDTH))

    def _footer_center(self) -> tuple[int, int] | None:
        metrics = self._gap_metrics()
        if metrics is None:
            return None
        gap_left, gap_right, row_top, row_height, px, py = metrics
        gap_width = gap_right - gap_left
        anchor_x = 0.5 + TOAST_SHIFT_X_RATIO
        anchor_y = 0.5 + TOAST_SHIFT_Y_RATIO
        center_x = gap_left + int(gap_width * anchor_x) - px
        center_y = row_top + int(row_height * anchor_y) - py - TOAST_LIFT_PX
        return center_x, center_y

    def _reposition(self) -> None:
        point = self._footer_center()
        if point is None:
            return
        center_x, center_y = point
        y_offset = 0
        for toast in reversed(self._toasts):
            toast.update_idletasks()
            toast.place(x=center_x, y=center_y + y_offset, anchor="center")
            toast.lift()
            height = max(toast.winfo_reqheight(), 32)
            y_offset -= height + TOAST_GAP


def _style_for_kind(kind: str, tokens: ThemeTokens) -> dict[str, str]:
    """Neutral info uses border/text — not brand red (reserved for errors)."""
    styles = {
        "info": {
            "bg": tokens.surface_alt,
            "border": tokens.border,
            "stripe": "#94a3b8",
            "fg": tokens.text,
            "icon": "",
        },
        "success": {
            "bg": tokens.surface_alt,
            "border": tokens.border,
            "stripe": tokens.success,
            "fg": tokens.text,
            "icon": "✓",
        },
        "warning": {
            "bg": tokens.surface_alt,
            "border": tokens.border,
            "stripe": tokens.warning,
            "fg": tokens.text,
            "icon": "!",
        },
        "error": {
            "bg": tokens.surface_alt,
            "border": tokens.border,
            "stripe": tokens.danger,
            "fg": tokens.text,
            "icon": "×",
        },
    }
    return styles.get(kind, styles["info"])
