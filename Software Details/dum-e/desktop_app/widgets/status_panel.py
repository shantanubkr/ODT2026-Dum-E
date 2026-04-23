"""
desktop_app/widgets/status_panel.py

Displays: state, behavior, last command state, output (Serial / ROS / sim), simulation, pose.
"""
from __future__ import annotations

import json
import tkinter as tk

C = {
    "panel":    "#161b22",
    "border":   "#30363d",
    "text":     "#e6edf3",
    "muted":    "#7d8590",
    "success":  "#3fb950",
    "warning":  "#d29922",
    "danger":   "#f85149",
    "accent":   "#58a6ff",
    "purple":   "#bc8cff",
    "bg_chip":  "#21262d",
}

_STATE_COLORS = {
    "ACTIVE": C["success"],
    "SAD":    C["purple"],
    "SLEEP":  C["muted"],
    "BOOT":   C["accent"],
    "ERROR":  C["danger"],
    "STOP_COOLDOWN": C["warning"],
    "DATA_ERROR": C["danger"],
    "WORKING": C["warning"],
    "FAULT":  C["danger"],
}


class StatusPanel(tk.Frame):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(
            parent,
            bg=C["panel"],
            highlightbackground=C["border"],
            highlightthickness=1,
        )
        self._vars: dict[str, tk.StringVar] = {}
        self._dot_labels: dict[str, tk.Label] = {}
        self._build()

    def _build(self) -> None:
        tk.Label(
            self,
            text="STATUS",
            font=("Helvetica", 7, "bold"),
            fg=C["muted"],
            bg=C["panel"],
            anchor="w",
        ).pack(fill=tk.X, padx=12, pady=(10, 6))

        self._add_row("state",      "State",      dot=True)
        self._add_row("behavior",   "Behavior",   dot=False)
        self._add_row("ros_state",  "Last cmd",   dot=True)
        self._add_row("bridge_out", "Output",     dot=True)
        self._add_row("simulation", "Simulation", dot=False)

        # Pose row — wider value
        pose_row = tk.Frame(self, bg=C["panel"])
        pose_row.pack(fill=tk.X, padx=12, pady=3)
        tk.Label(
            pose_row, text="Pose",
            width=10, anchor="w",
            fg=C["muted"], bg=C["panel"],
            font=("Helvetica", 9),
        ).pack(side=tk.LEFT)
        self._pose_var = tk.StringVar(value="—")
        tk.Label(
            pose_row,
            textvariable=self._pose_var,
            anchor="w",
            fg=C["accent"],
            bg=C["panel"],
            font=("Courier", 8),
            wraplength=260,
            justify=tk.LEFT,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Frame(self, bg=C["panel"], height=8).pack()

    def _add_row(self, key: str, label: str, dot: bool) -> None:
        row = tk.Frame(self, bg=C["panel"])
        row.pack(fill=tk.X, padx=12, pady=3)

        tk.Label(
            row, text=label,
            width=10, anchor="w",
            fg=C["muted"], bg=C["panel"],
            font=("Helvetica", 9),
        ).pack(side=tk.LEFT)

        if dot:
            dot_lbl = tk.Label(
                row, text="●",
                fg=C["muted"], bg=C["panel"],
                font=("Helvetica", 9),
            )
            dot_lbl.pack(side=tk.LEFT, padx=(0, 5))
            self._dot_labels[key] = dot_lbl

        var = tk.StringVar(value="—")
        tk.Label(
            row,
            textvariable=var,
            anchor="w",
            fg=C["text"],
            bg=C["panel"],
            font=("Helvetica", 9, "bold"),
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._vars[key] = var

    def update(self, status: dict) -> None:  # type: ignore[override]
        state = str(status.get("state") or "—").upper()
        self._vars["state"].set(state)
        if "state" in self._dot_labels:
            color = _STATE_COLORS.get(state, C["muted"])
            self._dot_labels["state"].config(fg=color)

        self._vars["behavior"].set(str(status.get("behavior") or "—"))

        ros = str(status.get("ros_state") or "—").upper()
        self._vars["ros_state"].set(ros)
        if "ros_state" in self._dot_labels:
            if ros in ("READY", "OK", "CONNECTED"):
                self._dot_labels["ros_state"].config(fg=C["success"])
            elif ros == "—":
                self._dot_labels["ros_state"].config(fg=C["muted"])
            else:
                self._dot_labels["ros_state"].config(fg=C["danger"])

        sim = status.get("simulation", False)
        self._vars["simulation"].set("Yes  (sim mode)" if sim else "No")

        bt = str(status.get("bridge_transport") or "—")
        bser = status.get("bridge_serial")
        if sim or bt == "sim":
            out_s = "Simulation"
            c_out = C["warning"]
        elif bt == "serial":
            out_s = f"Serial  {bser}" if bser else "Serial"
            c_out = C["success"]
        elif bt == "ros":
            out_s = "ROS  /dum_e_command"
            c_out = C["success"]
        elif bt == "ble":
            ble_ok = status.get("ble_connected")
            if ble_ok is True:
                out_s = f"BLE NUS  {bser}" if bser else "BLE NUS  connected"
                c_out = C["success"]
            elif ble_ok is False:
                out_s = "BLE NUS  disconnected"
                c_out = C["danger"]
            else:
                out_s = "BLE NUS"
                c_out = C["warning"]
        elif bt == "log_only":
            out_s = "Log only (set DUM_E_SERIAL_PORT or ROS)"
            c_out = C["warning"]
        else:
            out_s = "—"
            c_out = C["muted"]
        self._vars["bridge_out"].set(out_s)
        if "bridge_out" in self._dot_labels:
            self._dot_labels["bridge_out"].config(fg=c_out)

        pose = status.get("pose")
        if pose is None:
            self._pose_var.set("—")
        elif isinstance(pose, (list, dict)):
            self._pose_var.set(json.dumps(pose))
        else:
            self._pose_var.set(str(pose))
