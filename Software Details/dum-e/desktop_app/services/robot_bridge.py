# Laptop gateway: dashboard → motor ESP (BLE NUS or USB serial) or /dum_e_command (ROS 2).
# Lives under desktop_app only — not flashed to the ESP32.

from __future__ import annotations

import os
import threading

from backend.command_schema import Actions, Command
from utils.logger import log

# Contract: MicroPython stdin / BLE NUS accept these command strings.
# MOVE_HOME → idle | GREET → hello | DANCE → dance | STOP → error | RESET / RESUME_IDLE → idle
# MOVE_TO ready → ready | MOVE_TO down → down | PICK_OBJECT → reach | PLACE_OBJECT → drop
# pose_deg W UA F H → four joint angles (degrees), waist→upper→forearm→hand


class RobotBridge:
    """High-level commands → BLE NUS, USB serial (ESP stdin), ROS, or log-only (one path)."""

    def __init__(self) -> None:
        self._serial = None
        self._serial_lock = threading.Lock()
        self._bridge_lock = threading.RLock()
        self._serial_path: str | None = None
        self._ble_client = None
        self._baud: int = 115200
        self.last_command: str | None = None
        self.current_state = "IDLE"
        self._last_ble_link_ok: bool | None = None
        # transport: "ble" | "serial" | "ros" | "log_only"
        self.transport, self._use_ros_subprocess = self._configure_transport()
        self.skip_ros = not self._use_ros_subprocess
        log(
            "[RobotBridge] transport="
            + self.transport
            + (f" port={self._serial_path}" if self._serial_path else "")
        )

    @property
    def serial_path(self) -> str | None:
        return self._serial_path

    def _try_serial_then_ros(self, want_skip_ros: bool) -> tuple[str, bool]:
        """Open DUM_E_SERIAL_PORT if set; else ROS or log-only."""
        ble_wanted = os.getenv("DUM_E_BLE", "").strip().lower() in ("1", "true", "yes")
        port = (os.getenv("DUM_E_SERIAL_PORT") or "").strip()
        try:
            self._baud = int(os.getenv("DUM_E_SERIAL_BAUD") or "115200")
        except ValueError:
            self._baud = 115200

        if port:
            if not ble_wanted:
                log(
                    "[RobotBridge] USB serial (DUM_E_BLE unset/false — set DUM_E_BLE=1 "
                    "and comment out DUM_E_SERIAL_PORT for Bluetooth NUS)"
                )
            try:
                import serial  # type: ignore[import-untyped]

                self._serial = serial.Serial(port, self._baud, timeout=0.25)
                self._serial_path = port
                return ("serial", False)
            except Exception as exc:  # noqa: BLE001
                log(
                    "[RobotBridge] Could not open serial "
                    + repr(port)
                    + ": "
                    + str(exc)
                    + " — trying ROS or log only"
                )
                self._serial = None
                self._serial_path = None

        if not want_skip_ros:
            return ("ros", True)
        return ("log_only", False)

    def _configure_transport(self) -> tuple[str, bool]:
        """One hardware path: BLE (DUM_E_BLE=1) else serial else ROS else log only."""
        want_skip_ros = os.getenv("DUM_E_SKIP_ROS2") == "1"
        ble_on = os.getenv("DUM_E_BLE", "").strip().lower() in ("1", "true", "yes")
        if ble_on:
            # BLE scan+connect can take tens of seconds — must not block Tk import/main thread.
            ble_name = (os.getenv("DUM_E_BLE_NAME") or "DUM-E").strip()
            self._serial_path = "ble:" + ble_name
            self._ble_client = None

            def _ble_worker() -> None:
                try:
                    from .robot_bridge_ble_client import BleNusClient

                    client = BleNusClient()
                    with self._bridge_lock:
                        self._ble_client = client
                    self._last_ble_link_ok = True
                    log("[RobotBridge] BLE NUS connected (" + ble_name + ")")
                    log(
                        "[RobotBridge] Bluetooth: working — Nordic UART (NUS) session ready; "
                        "writes go to RX characteristic"
                    )
                except Exception as exc:  # noqa: BLE001
                    log("[RobotBridge] BLE init failed: " + str(exc) + " — falling back")
                    with self._bridge_lock:
                        self._ble_client = None
                        self._serial_path = None
                    t, use_ros = self._try_serial_then_ros(want_skip_ros)
                    with self._bridge_lock:
                        self.transport = t
                        self._use_ros_subprocess = use_ros
                        self.skip_ros = not use_ros
                    log(
                        "[RobotBridge] transport="
                        + self.transport
                        + (f" port={self._serial_path}" if self._serial_path else "")
                    )

            threading.Thread(target=_ble_worker, daemon=True, name="dum-e-ble-init").start()
            log(
                "[RobotBridge] BLE: connecting in background (scan often 20–60s). "
                "The window opens immediately; watch for [BleNus] connected or a fallback line."
            )
            return ("ble", False)

        return self._try_serial_then_ros(want_skip_ros)

    def ble_is_connected(self) -> bool:
        """True if BLE transport and NUS client reports connected."""
        if self.transport != "ble" or self._ble_client is None:
            return False
        return self._ble_client.is_connected_safe()

    def tick_ble_link_log(self) -> None:
        """Call from periodic status tick: log when BLE link goes up/down."""
        if self.transport != "ble" or self._ble_client is None:
            return
        ok = self.ble_is_connected()
        if self._last_ble_link_ok is None:
            self._last_ble_link_ok = ok
            return
        if ok == self._last_ble_link_ok:
            return
        self._last_ble_link_ok = ok
        if ok:
            log("[RobotBridge] Bluetooth: link restored — NUS connected again")
        else:
            log(
                "[RobotBridge] Bluetooth: link LOST — NUS disconnected "
                "(range/power/ESP32 USE_BLE_NUS?); commands may fail until reconnect"
            )

    def close(self) -> None:
        """Close BLE client and/or USB serial; safe to call more than once."""
        if self._ble_client is not None:
            try:
                self._ble_client.close()
            except Exception:  # noqa: BLE001
                pass
            self._ble_client = None
        with self._serial_lock:
            if self._serial is not None:
                try:
                    self._serial.close()
                except Exception:  # noqa: BLE001
                    pass
                self._serial = None

    def send(self, command: Command) -> None:
        action = command.action
        if action == Actions.MOVE_HOME:
            self._send_home(command)
        elif action == Actions.GREET:
            self._send_greet(command)
        elif action == Actions.DANCE:
            self._send_dance(command)
        elif action == Actions.STOP:
            self._send_stop(command)
        elif action == Actions.RESET:
            self._send_reset(command)
        elif action == Actions.RESUME_IDLE:
            self._send_resume_idle(command)
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
            self._dispatch_command("reach")
        elif action == Actions.PLACE_OBJECT:
            self.current_state = "DOWN"
            log(
                "[RobotBridge] PLACE_OBJECT (target=" + str(command.target) + ")"
            )
            self._dispatch_command("drop")
        else:
            log(
                "[RobotBridge] No hardware path yet for action: "
                + str(action)
                + " — TODO: trajectory MOVE_TO, etc."
            )

    def send_pose_degrees(self, angles_deg: list) -> None:
        """Send four joint angles (waist, upper_arm, forearm, hand) in degrees."""
        if len(angles_deg) != 4:
            log("[RobotBridge] send_pose_degrees: need 4 angles")
            return
        parts = " ".join(str(int(round(float(a)))) for a in angles_deg)
        self.current_state = "POSE_DEG"
        self._dispatch_command("pose_deg " + parts)

    def _dispatch_command(self, command: str) -> None:
        cmd = (command or "").strip().lower()
        self.last_command = cmd
        if self._ble_client is not None:
            try:
                self._ble_client.write_line(cmd)
                log("[RobotBridge] (ble) → " + cmd)
            except Exception as exc:  # noqa: BLE001
                log("[RobotBridge ERROR] BLE write: " + str(exc))
            return

        if self.transport == "ble" and self._ble_client is None:
            log("[RobotBridge] BLE still connecting — not sent: " + cmd)
            return

        if self._serial is not None:
            line = (cmd + "\n").encode("utf-8")
            try:
                with self._serial_lock:
                    self._serial.write(line)
                    self._serial.flush()
                log("[RobotBridge] (serial) → " + cmd)
            except Exception as exc:  # noqa: BLE001
                log("[RobotBridge ERROR] serial write: " + str(exc))
            return

        if not self._use_ros_subprocess:
            log("[RobotBridge] (log only) " + cmd)
            return

        try:
            import subprocess

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
            log("[RobotBridge] (ROS) → " + cmd)
        except Exception as exc:  # noqa: BLE001
            log("[RobotBridge ERROR] " + str(exc))

    def _send_home(self, _command: Command) -> None:
        self.current_state = "IDLE"
        log("[RobotBridge] HOME triggered")
        self._dispatch_command("idle")

    def _send_greet(self, _command: Command) -> None:
        self.current_state = "HELLO"
        log("[RobotBridge] GREET / HELLO triggered")
        self._dispatch_command("hello")

    def _send_dance(self, _command: Command) -> None:
        self.current_state = "DANCE"
        log("[RobotBridge] DANCE triggered")
        self._dispatch_command("dance")

    def _send_stop(self, _command: Command) -> None:
        self.current_state = "ERROR"
        log("[RobotBridge] STOP triggered")
        self._dispatch_command("error")

    def _send_reset(self, _command: Command) -> None:
        self.current_state = "IDLE"
        log("[RobotBridge] RESET triggered")
        self._dispatch_command("idle")

    def _send_resume_idle(self, _command: Command) -> None:
        self.current_state = "IDLE"
        log("[RobotBridge] RESUME_IDLE (task done — idle wander) triggered")
        self._dispatch_command("idle")

    def _send_ready(self, _command: Command) -> None:
        self.current_state = "READY"
        log("[RobotBridge] READY pose triggered")
        self._dispatch_command("ready")

    def _send_down(self, _command: Command) -> None:
        self.current_state = "DOWN"
        log("[RobotBridge] DOWN pose triggered")
        self._dispatch_command("down")
