"""
ROS 2 node: subscribes to /dume/target_coord (geometry_msgs/Point) and steers
DUM-E via dum_e_runtime.send_command (move_to left|right|forward) using simple
P-style rules (image X centering + area in Z).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# desktop_app/ must be importable (ros2 run, or: python3 track_target_node.py)
_APP_DIR = Path(__file__).resolve().parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point

from services import dum_e_runtime as _runtime

# Image X is considered centered on CENTER_X ± TOLERANCE (pixels, e.g. 320-wide frame).
_CENTER_X = 160.0
_TOLERANCE = 15.0
# Point.z carries blob area; above this, stop approaching.
_AREA_GRIP_READY = 12000.0
# Min interval between move commands to avoid flooding the command router (seconds).
_MIN_CMD_INTERVAL_S = 0.15


class TrackTargetNode(Node):
    def __init__(self) -> None:
        super().__init__("track_target_node")
        self._last_cmd_mono: float = 0.0
        self._gripper_in_place: bool = False
        self._sub = self.create_subscription(
            Point,
            "/dume/target_coord",
            self._on_target,
            10,
        )
        self.get_logger().info(
            "TrackTargetNode: subscribed to /dume/target_coord (Point: x,y px; z=area). "
            f"center_x={_CENTER_X}±{_TOLERANCE}, area_stop={_AREA_GRIP_READY}"
        )

    def _can_send_cmd(self) -> bool:
        now = time.monotonic()
        if now - self._last_cmd_mono < _MIN_CMD_INTERVAL_S:
            return False
        self._last_cmd_mono = now
        return True

    def _on_target(self, msg: Point) -> None:
        x = float(msg.x)
        y = float(msg.y)
        z = float(msg.z)  # area

        if z <= 0.0:
            self.get_logger().debug(
                f"Ignoring target (no area / z={z}): x={x:.1f} y={y:.1f}"
            )
            return

        if z >= _AREA_GRIP_READY:
            if not self._gripper_in_place:
                self.get_logger().info("Position reached. Gripper is in place — holding.")
                self._gripper_in_place = True
            return

        if self._gripper_in_place:
            # Target moved away; allow tracking again
            self._gripper_in_place = False
            self.get_logger().info("Target re-acquired — resuming approach.")

        lo = _CENTER_X - _TOLERANCE
        hi = _CENTER_X + _TOLERANCE

        if x < lo:
            if not self._can_send_cmd():
                return
            self.get_logger().info(
                f"Adjusting base: x={x:.0f} < {lo:.0f} — nudging left to center on cup."
            )
            _runtime.send_command(
                action="move_to",
                target="left",
                source="track_target_node",
            )
            return

        if x > hi:
            if not self._can_send_cmd():
                return
            self.get_logger().info(
                f"Adjusting base: x={x:.0f} > {hi:.0f} — nudging right to center on cup."
            )
            _runtime.send_command(
                action="move_to",
                target="right",
                source="track_target_node",
            )
            return

        # X centered, still need to approach (area < threshold)
        if not self._can_send_cmd():
            return
        self.get_logger().info(
            f"Approaching cup: target centered (x={x:.0f} in [{lo:.0f},{hi:.0f}]), "
            f"area z={z:.0f} < {_AREA_GRIP_READY:.0f} — move forward."
        )
        _runtime.send_command(
            action="move_to",
            target="forward",
            source="track_target_node",
        )


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
