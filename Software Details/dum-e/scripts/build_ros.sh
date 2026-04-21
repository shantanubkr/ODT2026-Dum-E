#!/usr/bin/env bash
# Build ROS 2 workspace (run on Ubuntu / WSL2 with ROS 2 Humble sourced).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS="${SCRIPT_DIR}/../ros2_ws"
if [[ ! -d "$WS/src" ]]; then
  echo "Expected $WS/src — run from dum-e repo root context."
  exit 1
fi
# shellcheck disable=SC1091
source /opt/ros/humble/setup.bash
cd "$WS"
colcon build --symlink-install "$@"
echo "Done. Run: source $WS/install/setup.bash"
