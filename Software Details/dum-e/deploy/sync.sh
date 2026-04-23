#!/usr/bin/env bash
# Upload src/ (firmware) then soft-reset. Does not touch desktop_app/ — see upload.sh header.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
"${SCRIPT_DIR}/upload.sh"
"${SCRIPT_DIR}/run.sh"
