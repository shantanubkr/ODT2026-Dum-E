# DUM-E entrypoint: activity/state + motion + behavior + serial input.
# Commands: dashboard / USB serial / REPL — no physical buttons by default.

import time
import select
import sys

from config import (
    BLE_DEVICE_NAME,
    LOOP_DELAY_MS,
    SLEEP_TIMEOUT_MS,
    USE_BLE_NUS,
    USE_PHYSICAL_BUTTONS,
)

from modules.recovery_timers import update_data_error_recovery, update_stop_recovery

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

_ble_nus = None
if USE_BLE_NUS:
    try:
        import bluetooth

        from drivers.ble_uart_nus import BleUartNus

        _ble_nus = BleUartNus(bluetooth.BLE(), name=BLE_DEVICE_NAME)
        log("BLE NUS advertising as: " + BLE_DEVICE_NAME)
    except Exception as exc:
        log("BLE NUS init failed: " + str(exc))
        _ble_nus = None

# Give behavior engine access to servo control for expression behaviors.
behavior_engine.set_motion_controller(motion_controller)
behavior_engine.set_runtime_guards(state_machine, safety_manager)

if USE_PHYSICAL_BUTTONS:
    from drivers.panel_button import Button
    from pins import BTN_DOWN, BTN_J1, BTN_J2, BTN_J3, BTN_J4, BTN_UP

    btn_j1 = Button(BTN_J1)
    btn_j2 = Button(BTN_J2)
    btn_j3 = Button(BTN_J3)
    btn_j4 = Button(BTN_J4)
    btn_up = Button(BTN_UP)
    btn_down = Button(BTN_DOWN)
else:
    btn_j1 = btn_j2 = btn_j3 = btn_j4 = btn_up = btn_down = None

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


# Sentiment → expression behavior mapping (GREET uses home + hand nod via set_behavior("greeting")).
_SENTIMENT_BEHAVIOR = {
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
    if sentiment == "GREET":
        state_machine.change_state(States.ACTIVE)
        behavior_engine.set_behavior("greeting")
    elif sentiment == "SAD":
        state_machine.change_state(States.SAD)
        behavior_engine.run_behavior("express_sad")
    elif expr_name is not None:
        if sentiment in ("HAPPY", "BYE"):
            state_machine.change_state(States.ACTIVE)
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
    if state_machine.is_state(States.STOP_COOLDOWN):
        return
    if state_machine.is_state(States.DATA_ERROR):
        return

    if has_elapsed(last_activity_ms, SLEEP_TIMEOUT_MS):
        if not state_machine.is_state(States.SLEEP):
            state_machine.change_state(States.SLEEP)
            behavior_engine.set_behavior("none")
            log("System entered sleep mode due to inactivity")
        return


def status_report():
    return {
        "state": state_machine.get_state(),
        "behavior": behavior_engine.get_behavior(),
        "idle_substate": behavior_engine.get_idle_substate(),
        "idle_wander_tick": behavior_engine.get_idle_wander_tick(),
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
    """Read one complete line from USB stdin within ~LOOP_DELAY_MS.

    A zero-timeout poll often misses USB CDC input on some ESP32 MicroPython
    builds; blocking for short slices lets the REPL/VCP driver deliver bytes.
    """
    global _serial_buf

    deadline = time.ticks_add(time.ticks_ms(), LOOP_DELAY_MS)
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        wait_ms = time.ticks_diff(deadline, time.ticks_ms())
        if wait_ms > 50:
            wait_ms = 50
        if wait_ms <= 0:
            break
        events = _serial_poll.poll(wait_ms)
        if not events:
            continue
        while True:
            char = sys.stdin.read(1)
            if not char:
                break
            if char in ("\n", "\r"):
                if _serial_buf:
                    line = "".join(_serial_buf)
                    _serial_buf = []
                    return line
            else:
                _serial_buf.append(char)
            if not _serial_poll.poll(0):
                break
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

    if btn_up.held():
        motion_controller.nudge_joint(+1)
        mark_activity()
    elif btn_down.held():
        motion_controller.nudge_joint(-1)
        mark_activity()


def loop():
    t0 = time.ticks_ms()
    if _ble_nus is not None:
        for ln in _ble_nus.pull_lines():
            handle_command(ln)
    line = poll_serial()
    if line:
        handle_command(line)

    handle_buttons()
    update_stop_recovery(state_machine, safety_manager, motion_controller, behavior_engine)
    update_data_error_recovery(state_machine, safety_manager, motion_controller, behavior_engine)
    update_activity_state()
    motion_controller.update()
    behavior_engine.update()
    elapsed = time.ticks_diff(time.ticks_ms(), t0)
    rest = LOOP_DELAY_MS - elapsed
    if rest > 0:
        time.sleep_ms(rest)


boot()

while True:
    loop()
