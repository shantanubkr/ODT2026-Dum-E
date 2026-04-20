"""
desktop_app/widgets/command_panel.py

Text entry + Send + Mic (push-to-talk) + quick action buttons.
Recording runs in a background thread so the UI never freezes.
"""
from __future__ import annotations

import logging
import threading
from typing import Callable
import tkinter as tk

logger = logging.getLogger(__name__)

C = {
    "bg":           "#0d1117",
    "panel":        "#161b22",
    "border":       "#30363d",
    "input_bg":     "#0d1117",
    "accent":       "#58a6ff",
    "accent_hover": "#388bfd",
    "success":      "#3fb950",
    "danger":       "#f85149",
    "danger_hover": "#da3633",
    "warning":      "#d29922",
    "purple":       "#bc8cff",
    "text":         "#e6edf3",
    "muted":        "#7d8590",
    "btn_bg":       "#21262d",
    "btn_hover":    "#30363d",
}

_QUICK_ACTIONS: list[tuple[str, str, str | None, str, str]] = [
    # label,  action,      target,   bg,           hover
    ("Home",  "move_home", None,     C["btn_bg"],  C["btn_hover"]),
    ("Ready", "move_to",   "ready",  C["btn_bg"],  C["btn_hover"]),
    ("Down",  "move_to",   "down",   C["btn_bg"],  C["btn_hover"]),
    ("Stop",  "stop",      None,     "#3d1a1a",    C["danger_hover"]),
    ("Reset", "reset",     None,     "#2d2208",    "#4a3810"),
    ("Hello", "greet",     None,     "#1a1f3d",    "#252d5c"),
]


def _make_btn(
    parent: tk.Widget,
    text: str,
    command: Callable,
    bg: str,
    hover: str,
    fg: str = C["text"],
    font: tuple = ("Helvetica", 9, "bold"),
    padx: int = 14,
    pady: int = 5,
) -> tk.Label:
    """Label-based button with hover highlight."""
    btn = tk.Label(
        parent,
        text=text,
        bg=bg,
        fg=fg,
        font=font,
        padx=padx,
        pady=pady,
        cursor="hand2",
    )
    btn.bind("<Button-1>", lambda _: command())
    btn.bind("<Enter>", lambda _: btn.config(bg=hover))
    btn.bind("<Leave>", lambda _: btn.config(bg=bg))
    return btn


class CommandPanel(tk.Frame):
    def __init__(
        self,
        parent: tk.Misc,
        on_text: Callable[[str], None],
        on_action: Callable[[str, str | None], None],
        on_mic: Callable[[], dict],
        on_mic_done: Callable[[dict], None],
    ) -> None:
        super().__init__(parent, bg=C["panel"])
        self._on_text = on_text
        self._on_action = on_action
        self._on_mic = on_mic
        self._on_mic_done = on_mic_done
        self._mic_recording = False
        self._build()
        self.config(highlightbackground=C["border"], highlightthickness=1)

    def _build(self) -> None:
        tk.Label(
            self,
            text="COMMAND",
            font=("Helvetica", 7, "bold"),
            fg=C["muted"],
            bg=C["panel"],
            anchor="w",
        ).pack(fill=tk.X, padx=12, pady=(10, 4))

        # --- input row ------------------------------------------------
        input_row = tk.Frame(self, bg=C["panel"])
        input_row.pack(fill=tk.X, padx=12, pady=(0, 8))

        entry_frame = tk.Frame(input_row, bg=C["border"])
        entry_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        self._entry = tk.Entry(
            entry_frame,
            bg=C["input_bg"],
            fg=C["text"],
            insertbackground=C["accent"],
            font=("Helvetica", 12),
            relief=tk.FLAT,
            bd=0,
        )
        self._entry.pack(fill=tk.X, expand=True, padx=10, pady=8)
        self._entry.bind("<Return>", lambda _: self._submit())
        self._entry.bind("<FocusIn>",  lambda _: entry_frame.config(bg=C["accent"]))
        self._entry.bind("<FocusOut>", lambda _: entry_frame.config(bg=C["border"]))

        _make_btn(
            input_row, "Send", self._submit,
            bg=C["accent"], hover=C["accent_hover"],
            fg="#0d1117", font=("Helvetica", 10, "bold"),
            padx=18, pady=8,
        ).pack(side=tk.LEFT, padx=(0, 6))

        self._mic_btn = _make_btn(
            input_row, "🎤  Mic", self._handle_mic_click,
            bg=C["btn_bg"], hover=C["btn_hover"],
            fg=C["text"], font=("Helvetica", 10),
            padx=12, pady=8,
        )
        self._mic_btn.pack(side=tk.LEFT)

        # --- divider --------------------------------------------------
        tk.Frame(self, bg=C["border"], height=1).pack(fill=tk.X, padx=12, pady=(0, 8))

        # --- quick action buttons ------------------------------------
        btn_row = tk.Frame(self, bg=C["panel"])
        btn_row.pack(fill=tk.X, padx=12, pady=(0, 10))

        tk.Label(
            btn_row,
            text="Quick:",
            font=("Helvetica", 9),
            fg=C["muted"],
            bg=C["panel"],
        ).pack(side=tk.LEFT, padx=(0, 8))

        for label, action, target, bg, hover in _QUICK_ACTIONS:
            _make_btn(
                btn_row, label,
                lambda a=action, t=target: self._on_action(a, t),
                bg=bg, hover=hover,
                fg=C["text"], font=("Helvetica", 9, "bold"),
                padx=12, pady=4,
            ).pack(side=tk.LEFT, padx=3)

    def _submit(self) -> None:
        text = self._entry.get().strip()
        if not text:
            return
        self._on_text(text)
        self._entry.delete(0, tk.END)

    # ------------------------------------------------------------------
    # Mic — threaded so the UI never freezes during recording
    # ------------------------------------------------------------------

    def _handle_mic_click(self) -> None:
        if self._mic_recording:
            return
        self._mic_recording = True
        # Unbind hover so recording state can't be overwritten by mouse events
        self._mic_btn.unbind("<Enter>")
        self._mic_btn.unbind("<Leave>")
        self._mic_btn.config(text="⏺  Recording…", bg="#3d1a1a", fg=C["danger"])

        def _worker() -> None:
            try:
                result = self._on_mic()
            except Exception as exc:  # noqa: BLE001
                result = {"ok": False, "error": str(exc)}
            # All Tkinter calls must happen on the main thread
            self.after(0, lambda: self._finish_mic(result))

        threading.Thread(target=_worker, daemon=True).start()

    def _finish_mic(self, result: dict) -> None:
        try:
            # Always show the transcript in the input box so the user can see
            # what was heard — even if the interpreter didn't recognise it.
            transcript = (result or {}).get("voice_input", "")
            if transcript:
                self._entry.delete(0, tk.END)
                self._entry.insert(0, transcript)

            error = (result or {}).get("error", "")
            if error and error not in ("unknown_intent",):
                # unknown_intent is normal — transcript is shown for the user to edit.
                # Only log hard failures (no_speech, mic_error, etc.).
                logger.warning("[command_panel] voice input: %s", error)

            self._on_mic_done(result)
        except Exception as exc:  # noqa: BLE001
            logger.error("[command_panel] mic finish error: %s", exc)
        finally:
            self._mic_recording = False
            self._mic_btn.config(text="🎤  Mic", bg=C["btn_bg"], fg=C["text"])
            self._mic_btn.bind("<Enter>", lambda _: self._mic_btn.config(bg=C["btn_hover"]))
            self._mic_btn.bind("<Leave>", lambda _: self._mic_btn.config(bg=C["btn_bg"]))
