# DUM-E entrypoint: boot → perpetual loop (serial poll, activity timeouts, behaviors).

import time  # sleep_ms for loop pacing (MicroPython)

from config import LOOP_DELAY_MS, IDLE_TIMEOUT_MS, SLEEP_TIMEOUT_MS  # Timing from one place

from utils.logger import log, get_logs  # Log + ring buffer for status_report

from utils.timers import reset_timer, has_elapsed  # Activity stamp + inactivity checks

from modules.state_machine import StateMachine, States  # High-level lifecycle states

from modules.command_parser import CommandParser  # Text → structured commands

from modules.behavior_engine import BehaviorEngine  # Idle / greeting / thinking

from modules.safety_manager import SafetyManager  # Motion permission + faults

from interfaces.serial_interface import SerialInterface  # Raw input bridge (poll/receive)

state_machine = StateMachine()  # Global orchestration state
command_parser = CommandParser()  # Shared parser instance
behavior_engine = BehaviorEngine()  # Shared behavior tick target
safety_manager = SafetyManager()  # Shared safety policy
serial_interface = SerialInterface()  # Input layer (poll stub until UART)
last_activity_ms = reset_timer()  # Last user/sensor activity for idle/sleep


def boot():
    """One-time startup: log, leave BOOT→ACTIVE, start idle behavior."""
    log("DUM-E booting...")  # Human-visible start
    state_machine.change_state(States.ACTIVE)  # Normal runtime (state machine was BOOT at init)
    behavior_engine.set_behavior("idle")  # Default personality baseline


def mark_activity():
    """Reset inactivity clock; if waking from SLEEP, go ACTIVE + idle + log."""
    global last_activity_ms  # Persist across function calls

    last_activity_ms = reset_timer()  # Slides IDLE/SLEEP deadlines forward
    if state_machine.is_state(States.SLEEP):  # Any stimulus ends sleep
        state_machine.change_state(States.ACTIVE)  # Awake again
        behavior_engine.set_behavior("idle")  # Safe post-sleep behavior
        log("System woke up from sleep due to activity")  # Audit trail


def handle_command(raw_command):
    """Parse line, always mark_activity, then branch on structured result."""
    result = command_parser.parse(raw_command)  # dict with type, command, args, ...
    command_type = result["type"]  # empty | unknown | known | move
    mark_activity()  # Commands count as activity (also wakes from sleep)

    if command_type == "empty":  # Nothing to do
        log("Empty command ignored")  # Trace noisy empty lines
        return  # Stop — no routing

    if command_type == "unknown":  # Not in vocabulary
        log("Unknown command: " + result["command"])  # Echo normalized unknown
        return  # Graceful reject

    if result["command"] == "hello":  # Social trigger
        state_machine.change_state(States.ACTIVE)  # Engaged
        behavior_engine.set_behavior("greeting")  # Timed in BehaviorEngine
        return  # Done

    if result["command"] == "stop":  # Software estop
        safety_manager.trigger_emergency_stop()  # Latch motion off
        state_machine.change_state(States.ERROR)  # Fault UI / logic
        return  # Do not process further

    if result["command"] == "reset":  # Operator recovery
        safety_manager.reset_emergency_stop()  # Clear latch
        state_machine.change_state(States.ACTIVE)  # Back to runtime
        behavior_engine.set_behavior("idle")  # Calm baseline
        return  # Done

    if result["command"] == "history":  # Debug: recent normalized commands
        log("Command history: " + str(command_parser.get_history()))  # List dump
        return  # Done

    if result["command"] == "status":  # Full snapshot
        report = status_report()  # Dict: state, behavior, safety, logs
        log("Status report: " + str(report))  # One structured line
        return  # Done

    if result["command"] in ["pick", "drop", "move", "home"]:  # Future motion API
        if not safety_manager.can_move():  # Central safety gate
            log("Movement blocked by safety manager")  # Explain denial
            return  # Abort motion intent

        state_machine.change_state(States.WORKING)  # Busy executing
        behavior_engine.set_behavior("thinking")  # Placeholder until real motion returns
        log("Command accepted for future motion: " + result["command"])  # Ack
        return  # Motion impl hooks in later

    log("Unhandled command path reached")  # Should not hit if parser + branches stay in sync


def update_activity_state():
    """Promote ACTIVE→IDLE on short inactivity, any non-ERROR→SLEEP on long; ERROR skips."""
    if state_machine.is_state(States.ERROR):  # Don't override fault with sleep
        return  # Manual/reset must clear ERROR first

    if has_elapsed(last_activity_ms, SLEEP_TIMEOUT_MS):  # Long quiet period (e.g. 5 min)
        if not state_machine.is_state(States.SLEEP):  # One-shot transition + log
            state_machine.change_state(States.SLEEP)  # Deep rest state
            behavior_engine.set_behavior("none")  # No idle ticks while asleep
            log("System entered sleep mode")  # Visible transition
        return  # Sleep branch takes priority — skip idle check same frame

    if has_elapsed(last_activity_ms, IDLE_TIMEOUT_MS):  # Shorter threshold (e.g. 30 s)
        if state_machine.is_state(States.ACTIVE):  # Only from ACTIVE (not WORKING/ERROR/SLEEP)
            state_machine.change_state(States.IDLE)  # Low-activity OS state
            behavior_engine.set_behavior("idle")  # Align behavior layer
            log("System entered idle state due to inactivity")  # Audit


def status_report():
    """Single dict for REPL/status — easy to extend for BLE/web later."""
    report = {  # Gather subsystems
        "state": state_machine.get_state(),  # States.* string
        "behavior": behavior_engine.get_behavior(),  # Behavior name
        "safety": safety_manager.get_status(),  # Nested flags + can_move
        "recent_logs": get_logs(),  # Ring buffer from logger
    }
    return report  # Caller may str() for one log line


def loop():
    """One iteration: optional serial → command, inactivity FSM, behavior tick, pace."""
    raw_input = serial_interface.poll()  # None until UART implemented
    if raw_input:  # Truthy when a line/bytes arrived
        cleaned_input = serial_interface.receive(raw_input)  # Strip + log
        if cleaned_input:  # Non-empty after sanitize
            handle_command(cleaned_input)  # Routes into state/safety/behavior

    update_activity_state()  # May IDLE or SLEEP based on last_activity_ms
    behavior_engine.update()  # Run current behavior once (always, even if no I/O)
    time.sleep_ms(LOOP_DELAY_MS)  # Yield CPU; set rate in config


boot()  # Initialize states/behaviors once at import/run

while True:  # Never exit on microcontroller
    loop()  # Fixed timestep-style loop body
