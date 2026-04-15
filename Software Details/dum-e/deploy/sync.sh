#!/usr/bin/env bash
# Upload src/ then soft-reset — one command for “flash latest firmware files”.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
"${SCRIPT_DIR}/upload.sh"
"${SCRIPT_DIR}/run.sh"
