#!/usr/bin/env bash
# Upload everything under src/ to the MicroPython device filesystem root.
# Run from the deploy/ directory: ./upload.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=deploy/common.sh
source "${SCRIPT_DIR}/common.sh"

SRC_DIR="${SCRIPT_DIR}/../src"
cd "${SRC_DIR}"
mpremote_run connect "${PORT}" cp -r . :
