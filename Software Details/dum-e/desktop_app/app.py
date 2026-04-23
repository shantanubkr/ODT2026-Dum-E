"""
desktop_app/app.py

Entry point for the DUM-E desktop application.

Run from the dum-e/ directory:
    source .venv/bin/activate
    python3 desktop_app/app.py
"""
from __future__ import annotations

# -----------------------------------------------------------------------
# Parse .env and set os.environ BEFORE any other imports so that
# dum_e_runtime and robot_bridge see the correct env vars.
# Uses only stdlib — no dotenv dependency required at this stage.
# -----------------------------------------------------------------------
import os as _os
import pathlib as _pathlib

_env_path = _pathlib.Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            _os.environ[_k.strip()] = _v.strip()

# -----------------------------------------------------------------------
import sys
from pathlib import Path
import tkinter as tk

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent

# Ensure desktop_app/ sub-packages are importable regardless of cwd.
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from services.app_runtime import DesktopAppRuntime  # noqa: E402
from services import local_target_tracker  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402

# No-ROS track loop (DUM_E_LOCAL_TARGET_TRACK=1 + DUM_E_VISION_URL) — not used with ROS node.
local_target_tracker.start_if_enabled()


def main() -> None:
    runtime = DesktopAppRuntime()

    root = tk.Tk()
    root.title("DUM-E Desktop")
    root.minsize(820, 660)
    root.geometry("980x720")
    root.configure(bg="#0d1117")

    MainWindow(root, runtime, env_path=_env_path).pack(fill=tk.BOTH, expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
