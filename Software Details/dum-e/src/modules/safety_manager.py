# Gate motion: estop (and optional fault latch) blocks can_move(); actuators should check can_move() first.

from utils.logger import log  # Safety events must be visible in logs


class SafetyManager:
    """Emergency stop latch; optional fault latch for future extensions. Central permission for movement."""

    def __init__(self):
        self.emergency_stop_active = False  # True = motion forbidden until reset
        self.sensor_error_active = False  # Set during DATA_ERROR recovery path
        # STOP_COOLDOWN: set when home reached; timer for 10s hold (see main.update_stop_recovery)
        self.stop_cooldown_hold_deadline_ms = None
        # DATA_ERROR: wall-clock start for 5s auto recovery (see main.update_data_error_recovery)
        self.data_error_deadline_ms = None
        log("Safety manager initialized")  # Startup marker

    def trigger_emergency_stop(self):
        """Latch estop ON once; log — hardware or software may call this."""
        if self.emergency_stop_active:  # Idempotent
            return  # Already stopped

        self.emergency_stop_active = True  # Hard lock
        log("EMERGENCY STOP activated")  # Loud audit message

    def reset_emergency_stop(self):
        """Clear estop deliberately (e.g. operator reset command); idempotent."""
        if not self.emergency_stop_active:  # Nothing to clear
            return  # Avoid duplicate 'cleared' logs

        self.emergency_stop_active = False  # Allow motion if sensor_error also clear
        log("EMERGENCY STOP cleared")  # Audit

    def set_sensor_error(self):
        """Latch generic fault (reserved for future use)."""
        if self.sensor_error_active:  # Idempotent
            return  # Already in fault

        self.sensor_error_active = True  # Blocks can_move until clear
        log("Sensor error activated")  # Debug visibility

    def clear_sensor_error(self):
        """Clear generic fault latch."""
        if not self.sensor_error_active:  # Idempotent
            return  # Already healthy

        self.sensor_error_active = False  # May allow motion if estop clear
        log("Sensor error cleared")  # Audit

    def can_move(self):
        """True only if no estop and no active fault latch."""
        if self.emergency_stop_active:  # Estop wins
            return False  # Never move under estop

        if self.sensor_error_active:
            return False

        return True  # Safe to attempt motion

    def clear_stop_cooldown_timers(self):
        """RESET or recovery: drop STOP_COOLDOWN hold tracking."""
        self.stop_cooldown_hold_deadline_ms = None

    def clear_data_error_timers(self):
        """RESET or recovery: drop DATA_ERROR deadline."""
        self.data_error_deadline_ms = None

    def get_status(self):
        """Snapshot dict for status command / remote telemetry."""
        return {
            "emergency_stop_active": self.emergency_stop_active,  # Raw latch
            "sensor_error_active": self.sensor_error_active,  # Raw latch
            "can_move": self.can_move(),  # Effective permission
            "stop_cooldown_hold_deadline_ms": self.stop_cooldown_hold_deadline_ms,
            "data_error_deadline_ms": self.data_error_deadline_ms,
        }
