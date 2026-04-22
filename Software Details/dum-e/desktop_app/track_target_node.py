"""
ROS 2 node: /dume/target_coord (geometry_msgs/Point) -> dum_e_runtime.send_command

Phases
------
1) TRACKING — center X (left/right), then approach (forward) using z as area proxy.
2) GRIP ready — debounced: centered X and z >= threshold for N frames -> latch "picked up"
   (vision no longer issues approach jogs; blob motion after latch is ignored).
3) 5 s after latch — one random *named pose* in the workspace (empty-area proxy); then back to
   tracking for the next object.

Tweak RANDOM_PLACE_POSES, _AREA_GRIP_READY, and POST_PICK_PLACE_DELAY_S to match your rig.
"""
from __future__ import annotations

import random
import sys
import time
from enum import IntEnum, auto
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point

from services import dum_e_runtime as _runtime

# Image X: center of frame ± tol (px), typical 320-wide QVGA.
_CENTER_X = 160.0
_TOLERANCE = 15.0
# Point.z = blob area; above this, object is "close enough" in image to count as pre-pick.
_AREA_GRIP_READY = 12000.0
# Consecutive OK frames (centered + area) before latching.
_GRIP_READY_STREAK = 5
# After latch, wait this long, then place at a random safe pose.
_POST_PICK_PLACE_DELAY_S = 5.0
# Random drop / workspace poses (must exist on motion controller: home, ready, down, …).
_RANDOM_PLACE_POSES = ("down", "ready", "home")
# Move command throttle.
_MIN_CMD_INTERVAL_S = 0.15
# Timer period to check 5s elapsed (s).
_PLACE_CHECK_PERIOD_S = 0.2


class _Phase(IntEnum):
    TRACKING = auto()
    HELD_PICKED = auto()  # Latched: waiting POST_PICK_PLACE_DELAY_S, vision tracking disabled


class TrackTargetNode(Node):
    def __init__(self) -> None:
        super().__init__("track_target_node")
        self._phase = _Phase.TRACKING
        self._last_cmd_mono: float = 0.0
        self._grip_ok_streak: int = 0
        self._pick_latch_mono: float | None = None
        # One-shot: after latch, set True; cleared when random place is sent
        self._place_pending: bool = False
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

    def _can_send_cmd(self) -> bool:
        now = time.monotonic()
        if now - self._last_cmd_mono < _MIN_CMD_INTERVAL_S:
            return False
        self._last_cmd_mono = now
        return True

    def _on_place_spin(self) -> None:
        if self._phase is not _Phase.HELD_PICKED or self._pick_latch_mono is None:
            return
        if not self._place_pending:
            return
        elapsed = time.monotonic() - self._pick_latch_mono
        if elapsed < _POST_PICK_PLACE_DELAY_S:
            return

        self._place_pending = False
        pose = random.choice(_RANDOM_PLACE_POSES)
        self.get_logger().info(
            f"5s after pick: placing in workspace — move_to named pose \"{pose}\" (random empty-area slot)."
        )
        _runtime.send_command(
            action="move_to",
            target=pose,
            source="track_target_node",
        )
        self._pick_latch_mono = None
        self._grip_ok_streak = 0
        self._phase = _Phase.TRACKING
        self.get_logger().info("Returned to TRACKING — ready for next target.")

    def _on_target(self, msg: Point) -> None:
        if self._phase is not _Phase.TRACKING:
            return

        x = float(msg.x)
        y = float(msg.y)
        z = float(msg.z)

        if z <= 0.0:
            self.get_logger().debug(
                f"Ignoring (no area z={z}): x={x:.1f} y={y:.1f}"
            )
            self._grip_ok_streak = 0
            return

        lo = _CENTER_X - _TOLERANCE
        hi = _CENTER_X + _TOLERANCE
        centered = lo <= x <= hi

        # Debounced "grip ready": centered in X and object looks large (close) in Z
        if centered and z >= _AREA_GRIP_READY:
            self._grip_ok_streak += 1
        else:
            self._grip_ok_streak = 0

        if self._grip_ok_streak >= _GRIP_READY_STREAK:
            self.get_logger().info(
                f"Object picked (vision): centered x={x:.0f}, area z={z:.0f} — "
                f"holding. Ignoring vision nudges for {_POST_PICK_PLACE_DELAY_S}s, then random place."
            )
            self._phase = _Phase.HELD_PICKED
            self._pick_latch_mono = time.monotonic()
            self._place_pending = True
            self._grip_ok_streak = 0
            return

        # Still approaching (TRACKING, not yet debounced)
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

        if not self._can_send_cmd():
            return
        self.get_logger().info(
            f"Approaching cup: centered (x={x:.0f} in [{lo:.0f},{hi:.0f}]), "
            f"area z={z:.0f} < threshold — move forward."
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
