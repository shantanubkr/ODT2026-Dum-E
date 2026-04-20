"""
desktop_app/widgets/ai_debug_panel.py

Shows the last AI interpretation result: input text, resolved action, target.
"""
from __future__ import annotations

import tkinter as tk

C = {
    "panel":    "#161b22",
    "border":   "#30363d",
    "text":     "#e6edf3",
    "muted":    "#7d8590",
    "accent":   "#58a6ff",
    "success":  "#3fb950",
    "purple":   "#bc8cff",
    "chip_bg":  "#21262d",
    "input_fg": "#e6edf3",
}

_ACTION_COLORS = {
    "greet":     "#bc8cff",
    "move_to":   "#58a6ff",
    "move_home": "#58a6ff",
    "stop":      "#f85149",
    "reset":     "#d29922",
}


class AiDebugPanel(tk.Frame):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(
            parent,
            bg=C["panel"],
            highlightbackground=C["border"],
            highlightthickness=1,
        )
        self._vars: dict[str, tk.StringVar] = {}
        self._action_lbl: tk.Label | None = None
        self._build()

    def _build(self) -> None:
        tk.Label(
            self,
            text="AI INTERPRETATION",
            font=("Helvetica", 7, "bold"),
            fg=C["muted"],
            bg=C["panel"],
            anchor="w",
        ).pack(fill=tk.X, padx=12, pady=(10, 6))

        # Input row
        self._add_row("input", "Input", C["text"])

        # Action row — value gets a colored chip
        row = tk.Frame(self, bg=C["panel"])
        row.pack(fill=tk.X, padx=12, pady=3)
        tk.Label(
            row, text="Action",
            width=8, anchor="w",
            fg=C["muted"], bg=C["panel"],
            font=("Helvetica", 9),
        ).pack(side=tk.LEFT)

        self._action_chip = tk.Label(
            row,
            text="—",
            fg=C["muted"],
            bg=C["chip_bg"],
            font=("Helvetica", 9, "bold"),
            padx=8, pady=2,
        )
        self._action_chip.pack(side=tk.LEFT)

        # Target row
        self._add_row("target", "Target", C["purple"])

        tk.Frame(self, bg=C["panel"], height=8).pack()

    def _add_row(self, key: str, label: str, fg: str) -> None:
        row = tk.Frame(self, bg=C["panel"])
        row.pack(fill=tk.X, padx=12, pady=3)
        tk.Label(
            row, text=label,
            width=8, anchor="w",
            fg=C["muted"], bg=C["panel"],
            font=("Helvetica", 9),
        ).pack(side=tk.LEFT)
        var = tk.StringVar(value="—")
        tk.Label(
            row,
            textvariable=var,
            anchor="w",
            fg=fg,
            bg=C["panel"],
            font=("Helvetica", 9, "bold"),
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._vars[key] = var

    def update(self, ai: dict) -> None:  # type: ignore[override]
        self._vars["input"].set(str(ai.get("input") or "—"))

        action = str(ai.get("action") or "")
        if action and action != "None":
            chip_color = _ACTION_COLORS.get(action, C["accent"])
            self._action_chip.config(text=action, fg="#0d1117", bg=chip_color)
        else:
            self._action_chip.config(text="—", fg=C["muted"], bg=C["chip_bg"])

        target = str(ai.get("target") or "")
        self._vars["target"].set(target if target and target != "None" else "—")
