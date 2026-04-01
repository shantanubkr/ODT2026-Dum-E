#!/usr/bin/env bash
# Soft-reset the ESP32 via mpremote.
# Run from the deploy/ directory: ./run.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=deploy/common.sh
source "${SCRIPT_DIR}/common.sh"

cd "${SCRIPT_DIR}/.."
mpremote_run connect "${PORT}" reset
