# Laptop / ROS gateway: forwards Command objects to ROS 2 /dum_e_command (or log-only sim).

from __future__ import annotations

import os
import sys

from backend.command_schema import Actions, Command
from utils.logger import log

# Legacy script argv when DUM_E_ROS_BRIDGE_SCRIPT is set and ros2 publish fails.
_SCRIPT_FALLBACK = {
    "idle": "home",
    "hello": "greet",
    "error": "stop",
    "ready": "ready",
    "down": "down",
    "reach": "reach",
    "drop": "place",
}


class RobotBridge:
    """Routes Command objects toward ROS 2 state manager (std_msgs/String on /dum_e_command)."""

    def __init__(self) -> None:
        self._ros_script = os.environ.get("DUM_E_ROS_BRIDGE_SCRIPT", "").strip() or None
        self._ros_topic = os.environ.get("DUM_E_ROS_COMMAND_TOPIC", "/dum_e_command").strip()
        # DUM_E_SKIP_ROS2=1: log only (Mac / tests); unset on WSL with ros2 on PATH for real pub.
        self._skip_ros2 = os.environ.get("DUM_E_SKIP_ROS2", "").lower() in ("1", "true", "yes")
        self.current_state = "IDLE"
        log(
            "[RobotBridge] Initialized (topic="
            + self._ros_topic
            + "; real_ros="
            + ("no" if self._skip_ros2 else "yes")
            + ")"
        )

    @property
    def skip_ros(self) -> bool:
        """True when we only log (ROS) Publishing and do not call the ros2 CLI."""
        return self._skip_ros2

    def send(self, command: Command) -> None:
        """Dispatch by action; extend when real transport exists."""
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
                "[RobotBridge] PLACE_OBJECT (target="
                + str(command.target)
                + ")"
            )
            self._publish_ros_command("drop")
        else:
            log(
                "[RobotBridge] No hardware path yet for action: "
                + str(action)
                + " — TODO: trajectory MOVE_TO, etc."
            )

    def _publish_ros_command(self, command: str) -> None:
        """Dual mode: always log; optionally run `ros2 topic pub` (WSL/Linux)."""
        cmd = (command or "").strip().lower()
        log("[RobotBridge] (ROS) Publishing: " + cmd)

        if self._skip_ros2:
            return

        try:
            import subprocess

            payload = "data: '" + cmd.replace("'", "") + "'"
            subprocess.Popen(
                [
                    "ros2",
                    "topic",
                    "pub",
                    "--once",
                    self._ros_topic,
                    "std_msgs/msg/String",
                    payload,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except Exception as exc:  # noqa: BLE001
            log("[RobotBridge ERROR] " + str(exc))
            self._maybe_subprocess(_SCRIPT_FALLBACK.get(cmd, cmd))

    def _maybe_subprocess(self, label: str) -> None:
        """Optional local script if ros2 publish fails and DUM_E_ROS_BRIDGE_SCRIPT is set."""
        if not self._ros_script:
            return
        try:
            import subprocess
        except ImportError:
            log("[RobotBridge ERROR] subprocess not available on this platform")
            return
        try:
            subprocess.Popen([sys.executable, self._ros_script, label], close_fds=True)
        except Exception as exc:  # noqa: BLE001
            log("[RobotBridge ERROR] " + label + ": " + str(exc))

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
