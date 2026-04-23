#!/usr/bin/env bash
# Launch the DUM-E desktop app with USB serial to the ESP32 (no BLE).
# Prereqs: ./setup-host.sh, copy .env.example → .env, set DUM_E_SERIAL_PORT and DUM_E_BLE=0.
# Close mpremote/Thonny on the same port before running.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "${ROOT}"

if [[ -f "${ROOT}/.venv/bin/python3" ]]; then
  PY="${ROOT}/.venv/bin/python3"
elif [[ -f "${ROOT}/.venv/bin/python" ]]; then
  PY="${ROOT}/.venv/bin/python"
else
  echo "DUM-E: no .venv — run:  ./setup-host.sh" >&2
  exit 1
fi

# Defaults for USB control (overridden by .env when app loads it)
export DUM_E_BLE="${DUM_E_BLE:-0}"
export DUM_E_SKIP_ROS2="${DUM_E_SKIP_ROS2:-1}"

echo "DUM-E: starting desktop app (USB; BLE transport off via DUM_E_BLE=${DUM_E_BLE})." >&2
echo "DUM-E: ensure .env has DUM_E_SERIAL_PORT=/dev/cu.usbserial-… and firmware on the ESP is listening for text lines." >&2

exec "${PY}" "${ROOT}/desktop_app/app.py"
