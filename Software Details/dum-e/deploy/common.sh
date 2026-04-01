#!/usr/bin/env bash
# Shared helpers for deploy/*.sh — resolve mpremote from project .venv first.
# shellcheck source=deploy/common.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_BIN="${PROJECT_ROOT}/.venv/bin"

# Override with: export DUM_E_MPREMOTE_PORT=/dev/cu.usbserial-XXXX
: "${DUM_E_MPREMOTE_PORT:=/dev/cu.usbserial-0001}"
PORT="${DUM_E_MPREMOTE_PORT}"

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
  echo "  python3 -m venv .venv && . .venv/bin/activate && python -m pip install -r requirements.txt" >&2
  exit 1
}
