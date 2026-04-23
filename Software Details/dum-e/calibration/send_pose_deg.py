#!/usr/bin/env python3
"""Send a single 'pose_deg w u f h' line to the motor ESP (USB serial)."""
from __future__ import annotations

import argparse
import os
import sys


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--port",
        "-p",
        default=os.environ.get("DUM_E_SERIAL_PORT", ""),
        help="Serial device (or set DUM_E_SERIAL_PORT)",
    )
    p.add_argument(
        "--baud",
        type=int,
        default=int(os.environ.get("DUM_E_SERIAL_BAUD", "115200")),
    )
    p.add_argument(
        "joints",
        nargs=4,
        type=int,
        metavar=("W", "U", "F", "H"),
        help="Four joint angles in degrees (firmware order)",
    )
    args = p.parse_args()
    if not args.port.strip():
        print("Set DUM_E_SERIAL_PORT or use --port", file=sys.stderr)
        return 1

    try:
        import serial
    except ImportError as e:
        print("Install: pip install -r calibration/requirements.txt", file=sys.stderr)
        raise e

    parts = " ".join(str(x) for x in args.joints)
    text = f"pose_deg {parts}\n"
    with serial.Serial(args.port, args.baud, timeout=0.3) as ser:
        ser.write(text.encode("utf-8"))
        ser.flush()
    print("OK", text.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
