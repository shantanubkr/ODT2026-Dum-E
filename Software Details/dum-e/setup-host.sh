#!/usr/bin/env bash
# One-time (or after moving the repo): create .venv and install mpremote for deploy/*.sh.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "${ROOT}"

if [[ ! -x "${ROOT}/.venv/bin/python" ]]; then
  echo "DUM-E: creating .venv …"
  # macOS: Homebrew python@3.12 + python-tk@3.12 gives a working tkinter (desktop app).
  _venv_py="python3"
  if [[ -x "/opt/homebrew/opt/python@3.12/bin/python3.12" ]]; then
    _venv_py="/opt/homebrew/opt/python@3.12/bin/python3.12"
  elif [[ -x "/usr/local/opt/python@3.12/bin/python3.12" ]]; then
    _venv_py="/usr/local/opt/python@3.12/bin/python3.12"
  fi
  "${_venv_py}" -m venv .venv
fi

# shellcheck disable=SC1091
source "${ROOT}/.venv/bin/activate"
python -m pip install --upgrade pip >/dev/null 2>&1 || true
python -m pip install -r "${ROOT}/requirements.txt"
python -m pip install -r "${ROOT}/desktop_app/requirements.txt"

echo ""
echo "DUM-E: host setup OK."
echo "  Desktop app (USB to ESP, no BLE):  ./run_desktop_usb.sh"
echo "  Dev — mount src/ from laptop:        ./deploy/mount_dev.sh  (close before run_desktop_usb)"
echo "  Upload + reset:                     cd deploy && ./sync.sh"
echo "  REPL:                               cd deploy && ./repl.sh"
echo "  (activate venv:  source .venv/bin/activate)"
echo ""
