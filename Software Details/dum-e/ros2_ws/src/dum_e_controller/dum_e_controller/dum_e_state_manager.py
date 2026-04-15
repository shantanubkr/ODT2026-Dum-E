#!/usr/bin/env python3
"""DUM-E state manager: subscribes to /dum_e_command, publishes /joint_states at 10 Hz."""

import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import String


class DumEStateManager(Node):
    """Phase 1 states: IDLE, HELLO, ERROR; plus READY/DOWN fixed poses for dashboard."""

    def __init__(self) -> None:
        super().__init__("dum_e_state_manager")
        self._pub = self.create_publisher(JointState, "/joint_states", 10)
        self.create_timer(0.1, self._loop)
        self._state = "IDLE"
        self.create_subscription(
            String,
            "/dum_e_command",
            self._command_callback,
            10,
        )
        self.get_logger().info("DUM-E State Manager started (subscribe /dum_e_command)")

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
        else:
            self.get_logger().warn("Unknown command: " + command)

    def _idle(self) -> None:
        self._publish_pose([0.0, 0.5, 1.0, 0.0])

    def _hello(self) -> None:
        t = time.time()
        wave = 0.3 * (1 if int(t * 2) % 2 == 0 else -1)
        self._publish_pose([0.0, 0.5, 1.0 + wave, 0.0])

    def _error(self) -> None:
        self._publish_pose([0.0, 0.2, 0.5, 0.0])

    def _ready(self) -> None:
        self._publish_pose([0.0, 0.55, 1.05, 0.0])

    def _down(self) -> None:
        self._publish_pose([0.0, 0.35, 0.75, 0.0])

    def _reach(self) -> None:
        """Pre-pick / reach pose (fixed; replace with IK later)."""
        self._publish_pose([0.0, 0.52, 1.0, 0.0])

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

    def _publish_pose(self, joints: list) -> None:
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = ["base", "shoulder", "elbow", "wrist"]
        msg.position = [float(x) for x in joints]
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
