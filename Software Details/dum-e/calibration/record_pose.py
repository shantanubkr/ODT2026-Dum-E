#!/usr/bin/env python3
"""Append a labeled pose record to recorded_poses.jsonl (one JSON object per line)."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_DIR = Path(__file__).resolve().parent
_DEFAULT_LAST = _DIR / ".last_pose.json"


def _parse_angles(s: str) -> list[int]:
    s = s.strip()
    if re.match(r"^[\d,\s\-]+$", s):
        return [int(x.strip()) for x in s.split(",") if x.strip()]
    raise ValueError(
        "Expected four comma-separated integers (waist..hand), "
        "e.g. upright 90,90,90,90 or ready-style 90,60,120,90"
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--label",
        "-l",
        required=True,
        help="Name for this snapshot (e.g. grasp_cup, hover_above_table)",
    )
    p.add_argument(
        "--angles",
        "-a",
        help="Four comma-separated degrees, or omit with --from-last",
    )
    p.add_argument(
        "--from-last",
        action="store_true",
        help="Read pose from calibration/.last_pose.json (from jog_pose.py)",
    )
    p.add_argument(
        "--last-file",
        type=Path,
        default=_DEFAULT_LAST,
    )
    p.add_argument(
        "--out",
        "-o",
        type=Path,
        default=_DIR / "recorded_poses.jsonl",
        help="Output JSONL path",
    )
    p.add_argument(
        "--note",
        "-n",
        default="",
        help="Optional note string",
    )
    args = p.parse_args()

    if args.from_last:
        if not args.last_file.is_file():
            print("Not found:", args.last_file, file=sys.stderr)
            return 1
        data = json.loads(args.last_file.read_text(encoding="utf-8"))
        pdeg = data.get("pose_deg")
        if not (isinstance(pdeg, list) and len(pdeg) == 4):
            print("Invalid pose in", args.last_file, file=sys.stderr)
            return 1
        pose = [int(x) for x in pdeg]
    elif args.angles:
        parts = [x for x in args.angles.split(",") if x.strip()]
        if len(parts) != 4:
            print("Need exactly 4 joint values", file=sys.stderr)
            return 1
        pose = [int(p.strip()) for p in parts]
    else:
        print("Use --angles 'w,u,f,h' or --from-last", file=sys.stderr)
        return 1

    rec = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "label": args.label,
        "pose_deg": {
            "waist": pose[0],
            "upper_arm": pose[1],
            "forearm": pose[2],
            "hand": pose[3],
        },
        "line": "pose_deg " + " ".join(str(x) for x in pose),
    }
    if args.note:
        rec["note"] = args.note

    line = json.dumps(rec, ensure_ascii=False) + "\n"
    with open(args.out, "a", encoding="utf-8") as f:
        f.write(line)
    print("Appended to", args.out)
    print(rec["line"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
