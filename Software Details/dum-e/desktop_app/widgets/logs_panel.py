"""
desktop_app/widgets/logs_panel.py

Scrollable log viewer with color-coded lines by severity.
"""
from __future__ import annotations

import tkinter as tk

C = {
    "panel":   "#161b22",
    "border":  "#30363d",
    "log_bg":  "#0d1117",
    "text":    "#8b949e",
    "muted":   "#484f58",
    "success": "#3fb950",
    "warning": "#d29922",
    "danger":  "#f85149",
    "accent":  "#58a6ff",
}

_TAG_RULES: list[tuple[str, list[str], str]] = [
    ("error",   ["ERROR", "error", "FAULT", "fault"],       C["danger"]),
    ("warn",    ["WARNING", "warning", "WARN", "warn"],     C["warning"]),
    ("bridge",  ["RobotBridge", "serial", "ROS", "BLE", "ble"], C["accent"]),
    ("state",   ["State changed", "Behavior changed"],      "#bc8cff"),
    ("ok",      ["GREET", "HELLO", "triggered", "READY"],   C["success"]),
]


class LogsPanel(tk.Frame):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(
            parent,
            bg=C["panel"],
            highlightbackground=C["border"],
            highlightthickness=1,
        )
        self._build()

    def _build(self) -> None:
        tk.Label(
            self,
            text="LOGS",
            font=("Helvetica", 7, "bold"),
            fg=C["muted"],
            bg=C["panel"],
            anchor="w",
        ).pack(fill=tk.X, padx=12, pady=(10, 4))

        frame = tk.Frame(self, bg=C["panel"])
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        scroll = tk.Scrollbar(frame)
        self._text = tk.Text(
            frame,
            height=10,
            bg=C["log_bg"],
            fg=C["text"],
            font=("Menlo", 9) if tk.TkVersion >= 8.6 else ("Courier", 9),
            state=tk.DISABLED,
            wrap=tk.WORD,
            relief=tk.FLAT,
            bd=0,
            padx=8,
            pady=6,
            yscrollcommand=scroll.set,
            selectbackground="#264f78",
        )
        scroll.config(command=self._text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure color tags
        self._text.tag_configure("default", foreground=C["text"])
        self._text.tag_configure("error",   foreground=C["danger"])
        self._text.tag_configure("warn",    foreground=C["warning"])
        self._text.tag_configure("bridge",  foreground=C["accent"])
        self._text.tag_configure("state",   foreground="#bc8cff")
        self._text.tag_configure("ok",      foreground=C["success"])
        self._text.tag_configure("muted",   foreground=C["muted"])

    def _classify(self, line: str) -> str:
        for tag, keywords, _ in _TAG_RULES:
            if any(kw in line for kw in keywords):
                return tag
        return "default"

    def set_logs(self, lines: list) -> None:
        self._text.configure(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        for line in lines:
            s = str(line)
            tag = self._classify(s)
            self._text.insert(tk.END, s + "\n", tag)
        self._text.see(tk.END)
        self._text.configure(state=tk.DISABLED)

    def append(self, line: str) -> None:
        self._text.configure(state=tk.NORMAL)
        tag = self._classify(line)
        self._text.insert(tk.END, "\n" + line, tag)
        self._text.see(tk.END)
        self._text.configure(state=tk.DISABLED)
