"""
Desktop-safe bridge to DUM-E src/ (CPython). Does not import src/main.py.
"""
from __future__ import annotations

import os
import sys
import time as _stdlib_time
from pathlib import Path

_SHIM_DONE = False


def _ensure_mp_time_shim() -> None:
    """One-time: MicroPython time helpers on CPython for utils.timers / behavior_engine."""
    global _SHIM_DONE
    if _SHIM_DONE:
        return
    t = __import__("time")
    if hasattr(t, "ticks_ms"):
        _SHIM_DONE = True
        return

    _t0 = _stdlib_time.monotonic()

    def ticks_ms() -> int:
        return int((_stdlib_time.monotonic() - _t0) * 1000) & 0x7FFFFFFF

    def ticks_diff(a: int, b: int) -> int:
        return a - b

    def sleep_ms(ms: int) -> None:
        _stdlib_time.sleep(ms / 1000.0)

    t.ticks_ms = ticks_ms  # type: ignore[attr-defined]
    t.ticks_diff = ticks_diff  # type: ignore[attr-defined]
    t.sleep_ms = sleep_ms  # type: ignore[attr-defined]
    _SHIM_DONE = True


def _src_root() -> Path:
    # desktop_app/services/dum_e_runtime.py -> dum-e root is parents[2]
    return Path(__file__).resolve().parent.parent.parent


def _ensure_src_path() -> None:
    src = _src_root() / "src"
    s = str(src)
    if s not in sys.path:
        sys.path.insert(0, s)


_ensure_mp_time_shim()
_ensure_src_path()

from backend.command_router import CommandRouter, build_command_from_parse_result
from backend.command_schema import Actions, Command
from interfaces.robot_bridge import RobotBridge
from modules.behavior_engine import BehaviorEngine
from modules.intent_parser import IntentParser
from modules.safety_manager import SafetyManager
from modules.state_machine import StateMachine
from utils.logger import get_logs, log

# Set DUM_E_SIM_MOTION=1 to use LaptopMotionController instead of RobotBridge + adapter.
USE_SIM_MOTION = os.environ.get("DUM_E_SIM_MOTION", "").lower() in ("1", "true", "yes")


class LaptopMotionController:
    """Fallback / simulation only: same API as firmware MotionController for CommandRouter."""

    def __init__(self) -> None:
        # Order: waist, upper_arm, forearm, hand, end_effector
        self.poses = {
            "home": [90, 90, 90, 90, 90],
            "ready": [90, 60, 120, 90, 90],
            "down": [90, 120, 140, 90, 90],
        }
        self.current_angles = list(self.poses["home"])
        self.target_angles = list(self.poses["home"])
        log("LaptopMotionController initialized (simulation)")

    def move_to_named_pose(self, name: str) -> None:
        if name not in self.poses:
            log("Unknown pose: " + str(name))
            return
        self.move_to_pose(list(self.poses[name]))

    def move_to_pose(self, angles: list) -> None:
        if len(angles) != 5:
            return
        self.target_angles = [int(angles[i]) for i in range(5)]
        log("Sim move target: " + str(self.target_angles))

    def update(self) -> None:
        self.current_angles = list(self.target_angles)

    def get_pose(self) -> list:
        return list(self.current_angles)


class BridgeMotionAdapter:
    """Presents MotionController-shaped API to CommandRouter; forwards motion to RobotBridge."""

    poses = {
        "home": [90, 90, 90, 90, 90],
        "ready": [90, 60, 120, 90, 90],
        "down": [90, 120, 140, 90, 90],
    }

    def __init__(self, robot_bridge: RobotBridge) -> None:
        self._bridge = robot_bridge
        self._pose = list(self.poses["home"])

    def move_to_named_pose(self, name: str) -> None:
        if name == "home":
            self._bridge.send(Command(Actions.MOVE_HOME, source="adapter"))
            self._pose = list(self.poses["home"])
        elif name == "ready":
            self._bridge.send(
                Command(Actions.MOVE_TO, metadata={"pose": "ready"}, source="adapter")
            )
            self._pose = list(self.poses["ready"])
        elif name == "down":
            self._bridge.send(
                Command(Actions.MOVE_TO, metadata={"pose": "down"}, source="adapter")
            )
            self._pose = list(self.poses["down"])
        else:
            log("[BridgeMotionAdapter] Unknown pose: " + str(name))

    def move_to_pose(self, angles: list) -> None:
        log("[BridgeMotionAdapter] move_to_pose not implemented for hardware bridge yet")
        if len(angles) == 5:
            self._pose = [int(angles[i]) for i in range(5)]

    def update(self) -> None:
        pass

    def get_pose(self) -> dict:
        """No live telemetry yet — avoid fake joint angles in the UI."""
        return {
            "mode": "bridge",
            "note": "pose unavailable until telemetry added",
            "last_target": list(self._pose),
        }


class _RouterWithBridgeNotify:
    """CommandRouter is unchanged; this facade notifies RobotBridge for STOP/GREET/RESET."""

    def __init__(self, inner: CommandRouter, bridge: RobotBridge) -> None:
        self._inner = inner
        self._bridge = bridge

    def route(self, cmd: Command) -> None:
        if cmd.action == Actions.RESET:
            self._bridge.send(cmd)
        self._inner.route(cmd)
        if cmd.action == Actions.STOP:
            self._bridge.send(cmd)
        elif cmd.action == Actions.GREET:
            self._bridge.send(cmd)


state_machine = StateMachine()
safety_manager = SafetyManager()
behavior_engine = BehaviorEngine()
intent_parser = IntentParser()

robot_bridge: RobotBridge | None = None
if USE_SIM_MOTION:
    motion_controller: LaptopMotionController | BridgeMotionAdapter = LaptopMotionController()
else:
    robot_bridge = RobotBridge()
    motion_controller = BridgeMotionAdapter(robot_bridge)


def status_report() -> dict:
    out = {
        "state": state_machine.get_state(),
        "behavior": behavior_engine.get_behavior(),
        "safety": safety_manager.get_status(),
        "pose": motion_controller.get_pose(),
        "recent_logs": get_logs(),
    }
    if robot_bridge is not None:
        out["ros_state"] = robot_bridge.current_state
    else:
        out["ros_state"] = None
    return out


_command_router_core = CommandRouter(
    motion_controller,
    state_machine,
    safety_manager=safety_manager,
    behavior_engine=behavior_engine,
    status_provider=status_report,
    history_provider=intent_parser.get_history,
)

if USE_SIM_MOTION or robot_bridge is None:
    command_router = _command_router_core
else:
    command_router = _RouterWithBridgeNotify(_command_router_core, robot_bridge)


def _command_from_action_string(action: str, target: str | None, source: str) -> Command | None:
    a = (action or "").strip().lower()
    if not a:
        return None
    if a == Actions.MOVE_HOME:
        return Command(Actions.MOVE_HOME, source=source)
    if a == Actions.STOP:
        return Command(Actions.STOP, source=source)
    if a == Actions.RESET:
        return Command(Actions.RESET, source=source)
    if a == Actions.GREET:
        return Command(Actions.GREET, source=source)
    if a == Actions.STATUS:
        return Command(Actions.STATUS, source=source)
    if a == Actions.HISTORY:
        return Command(Actions.HISTORY, source=source)
    if a == Actions.PICK_OBJECT:
        return Command(Actions.PICK_OBJECT, target=target, source=source)
    if a == Actions.PLACE_OBJECT:
        return Command(Actions.PLACE_OBJECT, target=target, source=source)
    if a == Actions.MOVE_TO:
        poses = getattr(motion_controller, "poses", {})
        if target and target in poses:
            return Command(Actions.MOVE_TO, metadata={"pose": target}, source=source)
        return Command(Actions.MOVE_TO, target=target, source=source)
    return None


def send_command(action: str, target: str | None = None, source: str = "web") -> dict:
    """Build a Command from structured action name and route via src CommandRouter."""
    try:
        cmd = _command_from_action_string(action, target, source)
        if cmd is None:
            return {
                "ok": False,
                "error": "unknown_or_invalid_action",
                "action": action,
            }
        command_router.route(cmd)
        return {"ok": True, "command": cmd.to_dict()}
    except Exception as exc:  # noqa: BLE001
        log("send_command error: " + str(exc))
        return {"ok": False, "error": str(exc), "action": action}


def parse_and_send_text(text: str, source: str = "web") -> dict:
    """Parse user text with IntentParser + build_command_from_parse_result, then route."""
    raw = (text or "").strip()
    if not raw:
        return {"ok": False, "error": "empty_text"}

    parts = raw.lower().split()
    if len(parts) >= 2 and parts[0] == "pick":
        try:
            cmd = Command(Actions.PICK_OBJECT, target=parts[-1], source=source)
            command_router.route(cmd)
            return {"ok": True, "command": cmd.to_dict(), "via": "text_adaptation"}
        except Exception as exc:  # noqa: BLE001
            log("parse_and_send_text error: " + str(exc))
            return {"ok": False, "error": str(exc)}
    if len(parts) >= 2 and parts[0] in ("drop", "place"):
        try:
            cmd = Command(Actions.PLACE_OBJECT, target=parts[-1], source=source)
            command_router.route(cmd)
            return {"ok": True, "command": cmd.to_dict(), "via": "text_adaptation"}
        except Exception as exc:  # noqa: BLE001
            log("parse_and_send_text error: " + str(exc))
            return {"ok": False, "error": str(exc)}

    try:
        result = intent_parser.parse(raw)
        ctype = result.get("type")
        if ctype == "empty":
            return {"ok": False, "error": "empty_after_parse"}
        if ctype == "unknown":
            return {"ok": False, "error": "unknown_command", "detail": result.get("command")}
        cmd = build_command_from_parse_result(result, source=source)
        if cmd is None:
            return {"ok": False, "error": "unhandled_parse_result", "result": result}
        command_router.route(cmd)
        return {"ok": True, "command": cmd.to_dict()}
    except Exception as exc:  # noqa: BLE001
        log("parse_and_send_text error: " + str(exc))
        return {"ok": False, "error": str(exc)}


def get_status() -> dict:
    """JSON-serializable snapshot for GET /status."""
    try:
        behavior_engine.update()
        motion_controller.update()
        out = dict(status_report())
        out["simulation"] = USE_SIM_MOTION
        return out
    except Exception as exc:  # noqa: BLE001
        log("get_status error: " + str(exc))
        return {
            "state": None,
            "behavior": None,
            "safety": {},
            "pose": [],
            "recent_logs": [],
            "simulation": USE_SIM_MOTION,
            "ros_state": None,
            "error": str(exc),
        }


def get_logs_only() -> list:
    try:
        return get_logs()
    except Exception:  # noqa: BLE001
        return []
