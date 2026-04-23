#!/usr/bin/env python3
"""Print pose_deg lines for home / ready / down from src/robot_kinematics.py (CPython on host)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _src_root() -> Path:
    return Path(__file__).resolve().parent.parent / "src"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "names",
        nargs="*",
        default=["home", "ready", "down"],
        help="Named poses (default: home ready down)",
    )
    args = p.parse_args()

    src = str(_src_root())
    if src not in sys.path:
        sys.path.insert(0, src)

    from robot_kinematics import firmware_deg_for_named_pose  # noqa: E402

    for name in args.names:
        name = str(name).strip().lower()
        try:
            deg = firmware_deg_for_named_pose(name)
        except (KeyError, TypeError) as e:
            print("skip unknown:", name, e, file=sys.stderr)
            continue
        part = " ".join(str(int(x)) for x in deg)
        print(f"# {name}")
        print(f"pose_deg {part}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
