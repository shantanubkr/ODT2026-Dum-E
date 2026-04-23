#!/usr/bin/env python3
"""
Interactive pose_deg jog over USB serial. Maintains calibration/.last_pose.json

Commands (type then Enter):
  j 1|2|3|4     — select joint 1..4 (waist..hand)
  + [n]          — nudge selected joint by +n degrees (default: step)
  - [n]          — nudge by -n
  s | send      — send current pose line to the ESP
  p | show      — print current four angles
  ready         — load "ready" named pose from robot_kinematics
  home          — load "home" named pose
  step N        — set nudge step (e.g. step 2)
  q | quit      — exit
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

_DIR = Path(__file__).resolve().parent
_LAST = _DIR / ".last_pose.json"


def _src_root() -> Path:
    return _DIR.parent / "src"


def _load_named(name: str) -> list[int]:
    src = str(_src_root())
    if src not in sys.path:
        sys.path.insert(0, src)
    from robot_kinematics import firmware_deg_for_named_pose  # noqa: E402

    return [int(x) for x in firmware_deg_for_named_pose(name)]


def _read_pose() -> list[int]:
    if _LAST.exists():
        data = json.loads(_LAST.read_text(encoding="utf-8"))
        p = data.get("pose_deg")
        if isinstance(p, list) and len(p) == 4:
            return [int(x) for x in p]
    return _load_named("ready")


def _write_pose(pose: list[int]) -> None:
    _LAST.write_text(
        json.dumps({"pose_deg": pose}, indent=2) + "\n",
        encoding="utf-8",
    )


def _send(pose: list[int], port: str, baud: int) -> None:
    import serial

    parts = " ".join(str(x) for x in pose)
    line = f"pose_deg {parts}\n"
    with serial.Serial(port, baud, timeout=0.3) as ser:
        ser.write(line.encode("utf-8"))
        ser.flush()
    print("→ sent", line.strip())


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--port",
        "-p",
        default=os.environ.get("DUM_E_SERIAL_PORT", ""),
    )
    p.add_argument(
        "--baud",
        type=int,
        default=int(os.environ.get("DUM_E_SERIAL_BAUD", "115200")),
    )
    p.add_argument(
        "--step",
        type=int,
        default=2,
        help="Default degrees per +/- (default: 2)",
    )
    args = p.parse_args()
    if not args.port.strip():
        print("Note: use --port or DUM_E_SERIAL_PORT for the send command. Other commands work without.", file=sys.stderr)

    try:
        import serial  # noqa: F401
    except ImportError as e:
        print("Install: pip install -r calibration/requirements.txt", file=sys.stderr)
        raise e

    pose = _read_pose()
    sel = 0
    step = args.step
    print(__doc__)
    print("Current", pose, "| joint", sel + 1, "| step", step)

    while True:
        try:
            raw = input("jog> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not raw:
            continue
        lo = raw.lower()
        if lo in ("q", "quit", "exit"):
            _write_pose(pose)
            print("Saved", _LAST)
            break
        if lo in ("p", "show"):
            print("pose_deg", " ".join(str(x) for x in pose))
            continue
        m = re.match(r"^j\s*([1-4])$", lo)
        if m:
            sel = int(m.group(1)) - 1
            print("Selected joint", sel + 1)
            continue
        m = re.match(r"^step\s+(\d+)$", lo)
        if m:
            step = max(1, int(m.group(1)))
            print("Step =", step)
            continue
        if lo == "ready":
            pose = _load_named("ready")
            _write_pose(pose)
            print("Loaded ready", pose)
            continue
        if lo == "home":
            pose = _load_named("home")
            _write_pose(pose)
            print("Loaded home", pose)
            continue
        m = re.match(r"^\+(\d+)?$", lo)
        if m or lo == "+":
            delta = int(m.group(1)) if m and m.group(1) else step
            pose[sel] = max(0, min(180, pose[sel] + delta))
            print(pose)
            _write_pose(pose)
            continue
        m = re.match(r"^-(\d+)?$", lo)
        if m or lo == "-":
            delta = int(m.group(1)) if m and m.group(1) else step
            pose[sel] = max(0, min(180, pose[sel] - delta))
            print(pose)
            _write_pose(pose)
            continue
        if lo in ("s", "send"):
            if not args.port.strip():
                print("No --port / DUM_E_SERIAL_PORT; cannot send", file=sys.stderr)
                continue
            _send(pose, args.port, args.baud)
            continue
        print("Unknown command. Try: j 1, +, -, s, p, ready, home, step 2, q")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
