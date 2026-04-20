# Laptop / ROS gateway: Dashboard → /dum_e_command (std_msgs/String). Mac: log only when DUM_E_SKIP_ROS2=1.

from __future__ import annotations

import os

from backend.command_schema import Actions, Command
from utils.logger import log

# Contract: dum_e_state_manager must accept these command strings.
# MOVE_HOME → idle | GREET → hello | STOP → error | RESET → idle
# MOVE_TO ready → ready | MOVE_TO down → down | PICK_OBJECT → reach | PLACE_OBJECT → drop


class RobotBridge:
    """Publishes high-level commands to ROS 2 as std_msgs/String on /dum_e_command."""

    def __init__(self) -> None:
        self.skip_ros = os.getenv("DUM_E_SKIP_ROS2") == "1"
        self.last_command: str | None = None
        self.current_state = "IDLE"
        log(
            "[RobotBridge] Initialized (/dum_e_command; real_ros="
            + ("no" if self.skip_ros else "yes")
            + ")"
        )

    def send(self, command: Command) -> None:
        action = command.action
        if action == Actions.MOVE_HOME:
            self._send_home(command)
        elif action == Actions.GREET:
            self._send_greet(command)
        elif action == Actions.STOP:
            self._send_stop(command)
        elif action == Actions.RESET:
            self._send_reset(command)
        elif action == Actions.MOVE_TO:
            pose = (command.metadata or {}).get("pose")
            if pose == "ready":
                self._send_ready(command)
            elif pose == "down":
                self._send_down(command)
            else:
                log("[RobotBridge] MOVE_TO unknown pose: " + str(pose))
        elif action == Actions.PICK_OBJECT:
            self.current_state = "REACH"
            log(
                "[RobotBridge] PICK_OBJECT (target="
                + str(command.target)
                + ") — REACH state"
            )
            self._publish_ros_command("reach")
        elif action == Actions.PLACE_OBJECT:
            self.current_state = "DOWN"
            log(
                "[RobotBridge] PLACE_OBJECT (target=" + str(command.target) + ")"
            )
            self._publish_ros_command("drop")
        else:
            log(
                "[RobotBridge] No hardware path yet for action: "
                + str(action)
                + " — TODO: trajectory MOVE_TO, etc."
            )

    def _publish_ros_command(self, command: str) -> None:
        cmd = (command or "").strip().lower()
        self.last_command = cmd
        log("[RobotBridge] (ROS) Publishing: " + cmd)

        if self.skip_ros:
            return

        try:
            import subprocess

            # --once: single publish. CLI type is std_msgs/msg/String on ROS 2.
            subprocess.Popen(
                [
                    "ros2",
                    "topic",
                    "pub",
                    "--once",
                    "/dum_e_command",
                    "std_msgs/msg/String",
                    "data: '" + cmd.replace("'", "") + "'",
                ]
            )
        except Exception as exc:  # noqa: BLE001
            log("[RobotBridge ERROR] " + str(exc))

    def _send_home(self, _command: Command) -> None:
        self.current_state = "IDLE"
        log("[RobotBridge] HOME triggered")
        self._publish_ros_command("idle")

    def _send_greet(self, _command: Command) -> None:
        self.current_state = "HELLO"
        log("[RobotBridge] GREET / HELLO triggered")
        self._publish_ros_command("hello")

    def _send_stop(self, _command: Command) -> None:
        self.current_state = "ERROR"
        log("[RobotBridge] STOP triggered")
        self._publish_ros_command("error")

    def _send_reset(self, _command: Command) -> None:
        self.current_state = "IDLE"
        log("[RobotBridge] RESET triggered")
        self._publish_ros_command("idle")

    def _send_ready(self, _command: Command) -> None:
        self.current_state = "READY"
        log("[RobotBridge] READY pose triggered")
        self._publish_ros_command("ready")

    def _send_down(self, _command: Command) -> None:
        self.current_state = "DOWN"
        log("[RobotBridge] DOWN pose triggered")
        self._publish_ros_command("down")
