"""STOP cooldown (10s hold at home) and DATA_ERROR (5s then home + idle) — shared by main + desktop runtime."""

from config import DATA_ERROR_RECOVERY_MS, STOP_COOLDOWN_MS

from modules.state_machine import States

from utils.logger import log
from utils.timers import has_elapsed, reset_timer


def update_stop_recovery(state_machine, safety_manager, motion_controller, behavior_engine):
    """STOP_COOLDOWN: at home → estop + 10s hold → clear estop → ACTIVE idle."""
    if not state_machine.is_state(States.STOP_COOLDOWN):
        return
    if not motion_controller.is_at_target():
        return
    if not safety_manager.emergency_stop_active:
        safety_manager.trigger_emergency_stop()
        safety_manager.stop_cooldown_hold_deadline_ms = reset_timer()
        return
    if safety_manager.stop_cooldown_hold_deadline_ms is None:
        return
    if not has_elapsed(safety_manager.stop_cooldown_hold_deadline_ms, STOP_COOLDOWN_MS):
        return
    safety_manager.reset_emergency_stop()
    safety_manager.clear_stop_cooldown_timers()
    state_machine.change_state(States.ACTIVE)
    behavior_engine.set_behavior("idle")
    log("STOP cooldown complete — ACTIVE + idle (wander enabled)")


def update_data_error_recovery(state_machine, safety_manager, motion_controller, behavior_engine):
    """DATA_ERROR: after DATA_ERROR_RECOVERY_MS → home + ACTIVE idle."""
    if not state_machine.is_state(States.DATA_ERROR):
        return
    if safety_manager.data_error_deadline_ms is None:
        return
    if not has_elapsed(safety_manager.data_error_deadline_ms, DATA_ERROR_RECOVERY_MS):
        return
    safety_manager.clear_sensor_error()
    safety_manager.clear_data_error_timers()
    motion_controller.move_to_named_pose("home")
    state_machine.change_state(States.ACTIVE)
    behavior_engine.set_behavior("idle")
    log("DATA_ERROR recovery — home + ACTIVE idle")
