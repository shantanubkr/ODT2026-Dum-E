"""
desktop_app/ui/main_window.py

Main application window. Composes all panels and drives the polling loop.
"""
from __future__ import annotations

import sys
from pathlib import Path
import tkinter as tk

_DESKTOP_ROOT = Path(__file__).resolve().parent.parent
if str(_DESKTOP_ROOT) not in sys.path:
    sys.path.insert(0, str(_DESKTOP_ROOT))

from services.app_runtime import DesktopAppRuntime  # noqa: E402
from widgets.status_panel import StatusPanel  # noqa: E402
from widgets.logs_panel import LogsPanel  # noqa: E402
from widgets.command_panel import CommandPanel  # noqa: E402
from widgets.ai_debug_panel import AiDebugPanel  # noqa: E402

POLL_MS = 1500

C = {
    "bg":           "#0d1117",
    "header_bg":    "#161b22",
    "panel":        "#161b22",
    "border":       "#30363d",
    "accent":       "#58a6ff",
    "success":      "#3fb950",
    "warning":      "#d29922",
    "danger":       "#f85149",
    "text":         "#e6edf3",
    "muted":        "#7d8590",
}


class MainWindow(tk.Frame):
    def __init__(self, parent: tk.Misc, runtime: DesktopAppRuntime) -> None:
        super().__init__(parent, bg=C["bg"])
        self._runtime = runtime
        self._build()
        self._poll()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build(self) -> None:
        self._build_header()

        content = tk.Frame(self, bg=C["bg"])
        content.pack(fill=tk.BOTH, expand=True, padx=12, pady=(8, 12))

        self._cmd_panel = CommandPanel(
            content,
            on_text=self._handle_text,
            on_action=self._handle_action,
            on_mic=self._runtime.handle_voice_input,  # runs in bg thread — no Tkinter here
            on_mic_done=self._handle_mic_done,
        )
        self._cmd_panel.pack(fill=tk.X, pady=(0, 8))

        middle = tk.Frame(content, bg=C["bg"])
        middle.pack(fill=tk.BOTH, expand=False, pady=(0, 8))
        middle.columnconfigure(0, weight=3)
        middle.columnconfigure(1, weight=2)

        self._status_panel = StatusPanel(middle)
        self._status_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self._ai_panel = AiDebugPanel(middle)
        self._ai_panel.grid(row=0, column=1, sticky="nsew")

        self._logs_panel = LogsPanel(content)
        self._logs_panel.pack(fill=tk.BOTH, expand=True)

    def _build_header(self) -> None:
        header = tk.Frame(self, bg=C["header_bg"], height=52)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        # Left: logo + title
        left = tk.Frame(header, bg=C["header_bg"])
        left.pack(side=tk.LEFT, padx=16, pady=0, fill=tk.Y)

        tk.Label(
            left,
            text="⚙",
            font=("Helvetica", 20),
            fg=C["accent"],
            bg=C["header_bg"],
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(
            left,
            text="DUM-E",
            font=("Helvetica", 16, "bold"),
            fg=C["text"],
            bg=C["header_bg"],
        ).pack(side=tk.LEFT)

        tk.Label(
            left,
            text="  Desktop Controller",
            font=("Helvetica", 11),
            fg=C["muted"],
            bg=C["header_bg"],
        ).pack(side=tk.LEFT)

        # Right: connection dot + label
        right = tk.Frame(header, bg=C["header_bg"])
        right.pack(side=tk.RIGHT, padx=16, fill=tk.Y)

        self._conn_dot = tk.Label(
            right,
            text="●",
            font=("Helvetica", 12),
            fg=C["warning"],
            bg=C["header_bg"],
        )
        self._conn_dot.pack(side=tk.LEFT, padx=(0, 4))

        self._conn_label = tk.Label(
            right,
            text="Connecting…",
            font=("Helvetica", 9),
            fg=C["muted"],
            bg=C["header_bg"],
        )
        self._conn_label.pack(side=tk.LEFT)

        # Separator line
        tk.Frame(self, bg=C["border"], height=1).pack(fill=tk.X)

    def _update_connection_indicator(self, status: dict) -> None:
        ros = str(status.get("ros_state", "")).upper()
        sim = status.get("simulation", False)
        if sim:
            self._conn_dot.config(fg=C["warning"])
            self._conn_label.config(text="Simulation mode", fg=C["warning"])
        elif ros in ("READY", "CONNECTED", "OK"):
            self._conn_dot.config(fg=C["success"])
            self._conn_label.config(text=f"ROS {ros}", fg=C["success"])
        elif ros:
            self._conn_dot.config(fg=C["danger"])
            self._conn_label.config(text=f"ROS {ros}", fg=C["danger"])
        else:
            self._conn_dot.config(fg=C["muted"])
            self._conn_label.config(text="No connection", fg=C["muted"])

    # ------------------------------------------------------------------
    # Command handlers
    # ------------------------------------------------------------------

    def _handle_text(self, text: str) -> None:
        result = self._runtime.send_text_command(text)
        if "ai" in result:
            self._ai_panel.update(result["ai"])
        self._refresh()

    def _handle_action(self, action: str, target: str | None = None) -> None:
        self._runtime.send_action(action, target)
        self._refresh()

    def _handle_mic_done(self, result: dict) -> None:
        """Called on the main thread after recording+transcription finishes."""
        # Always update AI panel if we have interpretation data (ok or not).
        if "ai" in result:
            self._ai_panel.update(result["ai"])

        error = result.get("error", "")
        if error and error not in ("unknown_intent",):
            # Hard failures (no_speech, mic_error) — show in log.
            # unknown_intent means Whisper worked but the phrase wasn't a command;
            # the transcript is already in the input box for the user to edit.
            self._logs_panel.append(f"[mic] {error}")

        self._refresh()

    # ------------------------------------------------------------------
    # Polling loop
    # ------------------------------------------------------------------

    def _refresh(self) -> None:
        try:
            status = self._runtime.get_status()
            self._status_panel.update(status)
            self._logs_panel.set_logs(status.get("recent_logs") or [])
            self._update_connection_indicator(status)
        except Exception as exc:  # noqa: BLE001
            self._logs_panel.append(f"[refresh error] {exc}")

    def _poll(self) -> None:
        self._refresh()
        self.after(POLL_MS, self._poll)
