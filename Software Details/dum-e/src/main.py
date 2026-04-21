# DUM-E entrypoint: activity/state + motion + behavior + serial input.
# Commands: dashboard / USB serial / REPL — no physical buttons by default.

import time
import select
import sys

from config import LOOP_DELAY_MS, IDLE_TIMEOUT_MS, SLEEP_TIMEOUT_MS, USE_PHYSICAL_BUTTONS

from utils.logger import log, get_logs

from utils.timers import reset_timer, has_elapsed

from modules.state_machine import StateMachine, States

from modules.intent_parser import IntentParser

from modules.behavior_engine import BehaviorEngine

from modules.safety_manager import SafetyManager

from modules.motion_controller import MotionController

from backend.command_router import CommandRouter, build_command_from_parse_result

from backend.command_schema import Actions

state_machine = StateMachine()
intent_parser = IntentParser()
behavior_engine = BehaviorEngine()
safety_manager = SafetyManager()
motion_controller = MotionController()
last_activity_ms = reset_timer()

# Give behavior engine access to servo control for expression behaviors.
behavior_engine.set_motion_controller(motion_controller)

if USE_PHYSICAL_BUTTONS:
    from drivers.pir import Button
    from pins import BTN_DOWN, BTN_J1, BTN_J2, BTN_J3, BTN_J4, BTN_J5, BTN_UP

    btn_j1 = Button(BTN_J1)
    btn_j2 = Button(BTN_J2)
    btn_j3 = Button(BTN_J3)
    btn_j4 = Button(BTN_J4)
    btn_j5 = Button(BTN_J5)
    btn_up = Button(BTN_UP)
    btn_down = Button(BTN_DOWN)
else:
    btn_j1 = btn_j2 = btn_j3 = btn_j4 = btn_j5 = btn_up = btn_down = None

# Non-blocking serial line reader: accumulates chars until \n or \r.
_serial_poll = select.poll()
_serial_poll.register(sys.stdin, select.POLLIN)
_serial_buf = []


def boot():
    log("DUM-E booting...")
    state_machine.change_state(States.ACTIVE)
    behavior_engine.set_behavior("idle")


def mark_activity():
    global last_activity_ms

    last_activity_ms = reset_timer()
    if state_machine.is_state(States.SLEEP):
        state_machine.change_state(States.ACTIVE)
        behavior_engine.set_behavior("idle")
        log("System woke up from sleep due to activity")


# Sentiment → expression behavior mapping; NEUTRAL is intentionally absent (no reaction).
_SENTIMENT_BEHAVIOR = {
    "GREET": "express_greet",
    "BYE":   "express_bye",
    "HAPPY": "express_happy",
    "SAD":   "express_sad",
}


def handle_command(raw_command):
    """Parse intent → optional sentiment expression → Command → router."""
    result = intent_parser.parse(raw_command)
    command_type = result["type"]

    if command_type == "empty":
        log("Empty command ignored")
        return

    sentiment = result.get("sentiment", "NEUTRAL")
    expr_name = _SENTIMENT_BEHAVIOR.get(sentiment)
    if expr_name is not None:
        behavior_engine.run_behavior(expr_name)

    if command_type == "unknown":
        log("Unknown command: " + result["command"])
        return

    mark_activity()
    cmd = build_command_from_parse_result(result, source="repl")
    if cmd is None:
        log("Unhandled command path: " + str(result))
        return

    command_router.route(cmd)

    if cmd.action in (Actions.PICK_OBJECT, Actions.PLACE_OBJECT):
        behavior_engine.run_behavior("express_present")


def update_activity_state():
    if state_machine.is_state(States.ERROR):
        return

    if has_elapsed(last_activity_ms, SLEEP_TIMEOUT_MS):
        if not state_machine.is_state(States.SLEEP):
            state_machine.change_state(States.SLEEP)
            behavior_engine.set_behavior("none")
            log("System entered sleep mode")
        return

    if has_elapsed(last_activity_ms, IDLE_TIMEOUT_MS):
        if state_machine.is_state(States.ACTIVE):
            state_machine.change_state(States.IDLE)
            behavior_engine.set_behavior("idle")
            log("System entered idle state due to inactivity")


def status_report():
    return {
        "state": state_machine.get_state(),
        "behavior": behavior_engine.get_behavior(),
        "safety": safety_manager.get_status(),
        "recent_logs": get_logs(),
    }


command_router = CommandRouter(
    motion_controller,
    state_machine,
    safety_manager=safety_manager,
    behavior_engine=behavior_engine,
    status_provider=status_report,
    history_provider=intent_parser.get_history,
)


def poll_serial():
    """Non-blocking read of one character from stdin; return a complete line or None."""
    global _serial_buf

    events = _serial_poll.poll(0)
    if not events:
        return None

    char = sys.stdin.read(1)
    if char in ('\n', '\r'):
        if _serial_buf:
            line = ''.join(_serial_buf)
            _serial_buf = []
            return line
        return None
    else:
        _serial_buf.append(char)
        return None


def handle_buttons():
    """Manual joint select + nudge — only when USE_PHYSICAL_BUTTONS is True."""
    if not USE_PHYSICAL_BUTTONS:
        return

    if btn_j1.pressed():
        motion_controller.select_joint(0)
        mark_activity()
    if btn_j2.pressed():
        motion_controller.select_joint(1)
        mark_activity()
    if btn_j3.pressed():
        motion_controller.select_joint(2)
        mark_activity()
    if btn_j4.pressed():
        motion_controller.select_joint(3)
        mark_activity()
    if btn_j5.pressed():
        motion_controller.select_joint(4)
        mark_activity()

    if btn_up.held():
        motion_controller.nudge_joint(+1)
        mark_activity()
    elif btn_down.held():
        motion_controller.nudge_joint(-1)
        mark_activity()


def loop():
    line = poll_serial()
    if line:
        handle_command(line)

    handle_buttons()
    update_activity_state()
    motion_controller.update()
    behavior_engine.update()
    time.sleep_ms(LOOP_DELAY_MS)


boot()

while True:
    loop()
