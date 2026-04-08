# Gate motion: estop and sensor fault blocks can_move(); all actuators should check can_move() first.

from utils.logger import log  # Safety events must be visible in logs


class SafetyManager:
    """Boolean latches for estop / sensor fault; central permission for movement."""

    def __init__(self):
        self.emergency_stop_active = False  # True = motion forbidden until reset
        self.sensor_error_active = False  # True = unsafe to trust sensors / motion
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
        """Latch sensor fault — timeouts, invalid readings, fallback mode."""
        if self.sensor_error_active:  # Idempotent
            return  # Already in fault

        self.sensor_error_active = True  # Blocks can_move until clear
        log("Sensor error activated")  # Debug visibility

    def clear_sensor_error(self):
        """Recover from sensor fault when readings are trusted again."""
        if not self.sensor_error_active:  # Idempotent
            return  # Already healthy

        self.sensor_error_active = False  # May allow motion if estop clear
        log("Sensor error cleared")  # Audit

    def can_move(self):
        """Single API for motion layer — True only if no estop and no sensor fault."""
        if self.emergency_stop_active:  # Estop wins
            return False  # Never move under estop

        if self.sensor_error_active:  # Conservative: no motion until cleared
            return False  # Later: allow limited fallback if policy changes

        return True  # Safe to attempt motion

    def get_status(self):
        """Snapshot dict for status command / remote telemetry."""
        return {
            "emergency_stop_active": self.emergency_stop_active,  # Raw latch
            "sensor_error_active": self.sensor_error_active,  # Raw latch
            "can_move": self.can_move(),  # Effective permission
        }
