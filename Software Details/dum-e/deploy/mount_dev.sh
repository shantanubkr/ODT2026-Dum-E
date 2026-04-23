#!/usr/bin/env bash
# Development: make the *laptop* copy of `src/` visible to MicroPython on the ESP32
# (mpremote "mount" — no permanent copy to the device flash).
#
# After this runs, the REPL opens (mount adds an implicit `repl`); cwd on-device is /remote.
# If the board has a `main.py` on flash that autostarts, press Ctrl-D (soft reset) so the
# mount can work as documented, then: import main
# Stop this script (Ctrl+C) before opening the desktop app on the *same* USB port.
#
# Usage: from repo root,  ./deploy/mount_dev.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=deploy/common.sh
source "${SCRIPT_DIR}/common.sh"

SRC_DIR="${SCRIPT_DIR}/../src"
cd "${SRC_DIR}"
echo "DUM-E: mounting ${SRC_DIR} on the device (quit this before desktop_app uses the port)…" >&2
mpremote_run connect "${PORT}" mount .
