# System-wide discrete states and transitions; always use change_state() — never assign raw strings.

from utils.logger import log  # Log every transition for debuggability


class States:
    """Named state constants — single source of truth for state string values."""

    BOOT = "BOOT"  # Power-on / init before normal runtime
    ACTIVE = "ACTIVE"  # Awake and engaged (default running state; curious wander uses behavior idle)
    SAD = "SAD"  # Low mood — slouch hold after express_sad; no wander until exited
    WORKING = "WORKING"  # Executing a command or motion sequence
    ERROR = "ERROR"  # Fault / estop — higher priority than sleep automation
    SLEEP = "SLEEP"  # Inactivity timeout — minimal behavior, no wander


class StateMachine:
    """Tracks current_state and logs transitions; guards duplicate changes."""

    def __init__(self):
        self.current_state = States.BOOT  # First state until boot() moves us
        log("State machine initialized in BOOT")  # Confirm constructor ran

    def get_state(self):
        """Return the current state string (compare to States.*)."""
        return self.current_state  # Read-only view of internal state

    def change_state(self, new_state):
        """Move to new_state if different; log BOOT -> IDLE style transitions."""
        if new_state == self.current_state:  # No-op avoids duplicate logs
            return  # Idempotent transition

        old_state = self.current_state  # Preserve for log message
        self.current_state = new_state  # Apply new state
        log("State changed: " + old_state + " -> " + new_state)  # Audit trail

    def is_state(self, state):
        """True if current_state equals the given States.* value."""
        return self.current_state == state  # Convenience for if-statements

    def reset(self):
        """Soft-reset machine back to BOOT (testing or recovery)."""
        self.current_state = States.BOOT  # Known baseline
        log("State machine reset to BOOT")  # Visible reset marker
