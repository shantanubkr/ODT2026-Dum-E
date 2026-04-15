#!/usr/bin/env bash
# Open MicroPython REPL on the board (close other apps using the same serial port first).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=deploy/common.sh
source "${SCRIPT_DIR}/common.sh"

echo "DUM-E: REPL on ${PORT} — exit with Ctrl-] or quit mpremote help for your version." >&2
mpremote_run connect "${PORT}" repl
