#!/usr/bin/env bash
# One-time (or after moving the repo): create .venv and install mpremote for deploy/*.sh.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "${ROOT}"

if [[ ! -x "${ROOT}/.venv/bin/python" ]]; then
  echo "DUM-E: creating .venv …"
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source "${ROOT}/.venv/bin/activate"
python -m pip install --upgrade pip >/dev/null 2>&1 || true
python -m pip install -r "${ROOT}/requirements.txt"

echo ""
echo "DUM-E: host setup OK."
echo "  Upload + reset:  cd deploy && ./sync.sh"
echo "  REPL:            cd deploy && ./repl.sh"
echo "  (activate venv for manual mpremote:  source .venv/bin/activate)"
echo ""
