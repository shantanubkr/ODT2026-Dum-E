#!/usr/bin/env bash
# Flash scope: only ../src/ → MicroPython device filesystem root.
# Not uploaded: desktop_app/, ros2_ws/, calibration/, .env — the laptop app stays on the host.
# USB serial: only one client at a time (mpremote here vs DUM_E_SERIAL_PORT in the desktop app).
# Run: ./upload.sh  (from deploy/)  or: ./sync.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=deploy/common.sh
source "${SCRIPT_DIR}/common.sh"

SRC_DIR="${SCRIPT_DIR}/../src"

# CPython can leave these under src/ during local tests; MicroPython should not receive them.
if [[ -d "${SRC_DIR}" ]]; then
  find "${SRC_DIR}" -type d -name __pycache__ 2>/dev/null | while read -r d; do
    rm -rf "${d}"
  done
fi

echo "DUM-E: uploading $(cd "${SRC_DIR}" && pwd) → device filesystem root …" >&2
cd "${SRC_DIR}"
mpremote_run connect "${PORT}" cp -r . :
echo "DUM-E: upload finished (src/ only; desktop_app/ unchanged on device)." >&2
