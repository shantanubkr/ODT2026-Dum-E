"""
ROS 2 node: /dume/target_coord (geometry_msgs/Point) -> dum_e_runtime.send_command

Uses :mod:`services.track_target_core` for behavior (same logic as
:mod:`services.local_target_tracker` when not using ROS).

Do not run with DUM_E_LOCAL_TARGET_TRACK=1 on the same machine — both would drive
the arm. Use either ROS + this node, or no-ROS + local tracker, not both.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point

from services import dum_e_runtime as _runtime
from services.track_target_core import (
    _AREA_GRIP_READY,
    _CENTER_X,
    _GRIP_READY_STREAK,
    _POST_PICK_PLACE_DELAY_S,
    _RANDOM_PLACE_POSES,
    _TOLERANCE,
    TrackTargetController,
)

# Timer period to check 5s elapsed (s) — should match or exceed local tracker cadence.
_PLACE_CHECK_PERIOD_S = 0.2


class TrackTargetNode(Node):
    def __init__(self) -> None:
        super().__init__("track_target_node")
        self._ctrl = TrackTargetController(
            _runtime.send_command,
            log_info=self.get_logger().info,
            log_debug=self.get_logger().debug,
        )
        self._place_timer = self.create_timer(
            _PLACE_CHECK_PERIOD_S, self._on_place_spin
        )
        self._sub = self.create_subscription(
            Point,
            "/dume/target_coord",
            self._on_target,
            10,
        )
        self.get_logger().info(
            f"TrackTargetNode: /dume/target_coord | center={_CENTER_X}±{_TOLERANCE} | "
            f"area>={_AREA_GRIP_READY} (streak={_GRIP_READY_STREAK}) | "
            f"post-pick place after {_POST_PICK_PLACE_DELAY_S}s in poses {_RANDOM_PLACE_POSES}"
        )

    def _on_place_spin(self) -> None:
        self._ctrl.tick_place(time.monotonic())

    def _on_target(self, msg: Point) -> None:
        self._ctrl.on_target(float(msg.x), float(msg.y), float(msg.z))


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = TrackTargetNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
