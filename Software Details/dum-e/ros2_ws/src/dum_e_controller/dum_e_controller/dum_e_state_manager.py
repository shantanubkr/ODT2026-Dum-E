#!/usr/bin/env python3
"""DUM-E state manager: subscribes to /dum_e_command, publishes /joint_states at 10 Hz.

Joint names match dum_e_description URDF (Revolute 7–10) plus firmware-only gripper:
  Revolute 8  ← logical waist (base→Waist_1, yaw)
  Revolute 7  ← logical upper_arm (Waist→Upper_arm)
  Revolute 10 ← logical forearm (Upper_arm→Forearm)
  Revolute 9  ← logical hand (Forearm→Hand)
  end_effector ← fifth servo (not in URDF; RViz ignores unknown joint)
"""

import math
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import String

from .urdf_poses import (
    LOGICAL_DOWN,
    LOGICAL_ERROR,
    LOGICAL_IDLE,
    LOGICAL_REACH,
    LOGICAL_READY,
)

# Order and names must stay in sync with URDF joint names (spaces preserved).
_JOINT_NAMES = [
    "Revolute 7",
    "Revolute 8",
    "Revolute 9",
    "Revolute 10",
    "end_effector",
]


def _logical_to_urdf(
    waist: float,
    upper_arm: float,
    forearm: float,
    hand: float,
    end_effector: float,
) -> list[float]:
    """Map firmware [waist, upper_arm, forearm, hand, end_effector] to URDF joint order."""
    return [
        float(upper_arm),   # Revolute 7
        float(waist),      # Revolute 8
        float(hand),       # Revolute 9
        float(forearm),    # Revolute 10
        float(end_effector),
    ]


class DumEStateManager(Node):
    """Phase 1 states: IDLE, HELLO, ERROR; plus READY/DOWN fixed poses for dashboard."""

    def __init__(self) -> None:
        super().__init__("dum_e_state_manager")
        self._pub = self.create_publisher(JointState, "/joint_states", 10)
        self.create_timer(0.1, self._loop)
        self._state = "IDLE"
        self._pose_deg_rad: list[float] = [0.0, 0.5, 1.0, 0.0, math.pi / 2]
        self.create_subscription(
            String,
            "/dum_e_command",
            self._command_callback,
            10,
        )
        self.get_logger().info(
            "DUM-E State Manager started — /joint_states uses URDF names "
            + str(_JOINT_NAMES)
        )

    def _command_callback(self, msg: String) -> None:
        command = (msg.data or "").strip().lower()
        self.get_logger().info("Received command: " + command)
        if command == "idle":
            self._state = "IDLE"
        elif command == "hello":
            self._state = "HELLO"
        elif command == "error":
            self._state = "ERROR"
        elif command == "ready":
            self._state = "READY"
        elif command == "down":
            self._state = "DOWN"
        elif command == "reach":
            self._state = "REACH"
        elif command == "drop":
            self._state = "DOWN"
        elif command == "dance":
            self._state = "DANCE"
        else:
            parts = command.split()
            if len(parts) == 6 and parts[0] == "pose_deg":
                try:
                    degs = [float(parts[i]) for i in range(1, 6)]
                    self._pose_deg_rad = [d * math.pi / 180.0 for d in degs]
                    self._state = "POSE_DEG"
                    self.get_logger().info("pose_deg (logical joints deg→rad): " + str(degs))
                except ValueError:
                    self.get_logger().warn("pose_deg parse error: " + command)
            else:
                self.get_logger().warn("Unknown command: " + command)

    def _idle(self) -> None:
        self._publish_logical(list(LOGICAL_IDLE))

    def _hello(self) -> None:
        t = time.time()
        wave = 0.3 * (1 if int(t * 2) % 2 == 0 else -1)
        p = list(LOGICAL_IDLE)
        p[2] = p[2] + wave
        self._publish_logical(p)

    def _error(self) -> None:
        self._publish_logical(list(LOGICAL_ERROR))

    def _ready(self) -> None:
        self._publish_logical(list(LOGICAL_READY))

    def _down(self) -> None:
        self._publish_logical(list(LOGICAL_DOWN))

    def _reach(self) -> None:
        self._publish_logical(list(LOGICAL_REACH))

    def _dance(self) -> None:
        t = time.time()
        wobble_w = 0.35 * math.sin(t * 4.2)
        wobble_f = 0.22 * math.sin(t * 4.2 + 0.8)
        wobble_h = 0.08 * math.sin(t * 3.1)
        self._publish_logical([wobble_w, 0.48, 1.02 + wobble_f, wobble_h, math.pi / 2])

    def _loop(self) -> None:
        if self._state == "IDLE":
            self._idle()
        elif self._state == "HELLO":
            self._hello()
        elif self._state == "ERROR":
            self._error()
        elif self._state == "READY":
            self._ready()
        elif self._state == "DOWN":
            self._down()
        elif self._state == "REACH":
            self._reach()
        elif self._state == "DANCE":
            self._dance()
        elif self._state == "POSE_DEG":
            self._publish_logical(list(self._pose_deg_rad))

    def _publish_logical(self, joints: list) -> None:
        """joints order: waist, upper_arm, forearm, hand, end_effector (radians-ish)."""
        if len(joints) != 5:
            return
        w, ua, f, h, ee = joints
        self._publish_pose(_logical_to_urdf(w, ua, f, h, ee))

    def _publish_pose(self, positions: list) -> None:
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = list(_JOINT_NAMES)
        msg.position = [float(x) for x in positions]
        self._pub.publish(msg)


def main(args: list | None = None) -> None:
    rclpy.init(args=args)
    node = DumEStateManager()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
