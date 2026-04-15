#!/usr/bin/env bash
# Shared helpers for deploy/*.sh — resolve mpremote from project .venv first.
# shellcheck source=deploy/common.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_BIN="${PROJECT_ROOT}/.venv/bin"

# Pick ESP32 USB serial on macOS: explicit env wins, then default name, then first match.
# Override with: export DUM_E_MPREMOTE_PORT=/dev/cu.usbserial-XXXX
resolve_serial_port() {
  if [[ -n "${DUM_E_MPREMOTE_PORT:-}" ]]; then
    if [[ -e "${DUM_E_MPREMOTE_PORT}" ]]; then
      printf '%s' "${DUM_E_MPREMOTE_PORT}"
      return 0
    fi
    echo "DUM-E: DUM_E_MPREMOTE_PORT=${DUM_E_MPREMOTE_PORT} not found. Fix path or unset for auto-detect." >&2
    return 1
  fi

  local default=/dev/cu.usbserial-0001
  if [[ -e "$default" ]]; then
    printf '%s' "$default"
    return 0
  fi

  local f
  local found=()
  shopt -s nullglob
  for f in /dev/cu.usbserial* /dev/cu.wchusbserial* /dev/cu.SLAB_USBtoUART*; do
    found+=("$f")
  done
  shopt -u nullglob
  if [[ ${#found[@]} -ge 1 ]]; then
    printf '%s' "${found[0]}"
    return 0
  fi

  echo "DUM-E: No USB serial under /dev/cu.* — plug in the ESP32 or set DUM_E_MPREMOTE_PORT." >&2
  return 1
}

PORT="$(resolve_serial_port)" || exit 1
echo "DUM-E: serial port → ${PORT}" >&2

mpremote_run() {
  # Prefer venv "python -m mpremote" over venv/bin/mpremote. Console scripts embed
  # absolute interpreter paths; after moving the project, mpremote may still run
  # but its shebang points at the old .venv location ("bad interpreter").
  local candidate
  for candidate in "${VENV_BIN}/python3" "${VENV_BIN}/python"; do
    if [[ -x "${candidate}" ]] && "${candidate}" -m mpremote --version >/dev/null 2>&1; then
      "${candidate}" -m mpremote "$@"
      return
    fi
  done
  if [[ -x "${VENV_BIN}/mpremote" ]]; then
    "${VENV_BIN}/mpremote" "$@"
    return
  fi
  if command -v mpremote >/dev/null 2>&1; then
    mpremote "$@"
    return
  fi
  for candidate in python3 python; do
    if command -v "${candidate}" >/dev/null 2>&1 && "${candidate}" -m mpremote --version >/dev/null 2>&1; then
      "${candidate}" -m mpremote "$@"
      return
    fi
  done
  echo "DUM-E: mpremote not found. From the project root run:" >&2
  echo "  ./setup-host.sh   # or: python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt" >&2
  exit 1
}
