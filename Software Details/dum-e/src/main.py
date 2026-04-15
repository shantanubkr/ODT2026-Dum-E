# DUM-E entrypoint: live loop = buttons + activity/state + motion + behavior.
# Text commands: handle_command() + router/parser kept for REPL / future console or serial (not called from loop).

import time

from config import LOOP_DELAY_MS, IDLE_TIMEOUT_MS, SLEEP_TIMEOUT_MS

from utils.logger import log, get_logs

from utils.timers import reset_timer, has_elapsed

from modules.state_machine import StateMachine, States

from modules.intent_parser import IntentParser

from modules.behavior_engine import BehaviorEngine

from modules.safety_manager import SafetyManager

from drivers.pir import Button

from modules.motion_controller import MotionController

from backend.command_router import CommandRouter, build_command_from_parse_result

state_machine = StateMachine()
intent_parser = IntentParser()
behavior_engine = BehaviorEngine()
safety_manager = SafetyManager()
motion_controller = MotionController()
last_activity_ms = reset_timer()

btn_j1 = Button(12)
btn_j2 = Button(13)
btn_j3 = Button(27)
btn_up = Button(25)
btn_down = Button(18)


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


def handle_command(raw_command):
    """Parse intent → Command → router only (no motion/status/safety branches here)."""
    result = intent_parser.parse(raw_command)
    command_type = result["type"]

    if command_type == "empty":
        log("Empty command ignored")
        return
    if command_type == "unknown":
        log("Unknown command: " + result["command"])
        return

    mark_activity()
    cmd = build_command_from_parse_result(result, source="repl")
    if cmd is None:
        log("Unhandled command path: " + str(result))
        return
    command_router.route(cmd)


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


def handle_buttons():
    """Manual mode only: joint select + nudge (no poses, no router)."""
    if btn_j1.pressed():
        motion_controller.select_joint(0)
        mark_activity()
    if btn_j2.pressed():
        motion_controller.select_joint(1)
        mark_activity()
    if btn_j3.pressed():
        motion_controller.select_joint(2)
        mark_activity()

    if btn_up.held():
        motion_controller.nudge_joint(+1)
        mark_activity()
    elif btn_down.held():
        motion_controller.nudge_joint(-1)
        mark_activity()


def loop():
    handle_buttons()
    update_activity_state()
    motion_controller.update()
    behavior_engine.update()
    time.sleep_ms(LOOP_DELAY_MS)


boot()

while True:
    loop()
