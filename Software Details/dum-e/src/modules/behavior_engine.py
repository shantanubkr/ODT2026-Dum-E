# High-level personality / motion placeholders: idle, greeting, thinking; driven by update() each loop.

from utils.logger import log  # Log behavior transitions and tick noise (tune later)

from utils.timers import reset_timer, has_elapsed  # Start times + duration checks

from config import GREETING_DURATION_MS, THINKING_DURATION_MS  # Centralized ms durations


class BehaviorEngine:
    """One active behavior name; timed greeting/thinking return to idle automatically."""

    def __init__(self):
        self.current_behavior = "none"  # Until boot sets idle
        self.behavior_start_ms = reset_timer()  # Anchor for duration checks
        log("Behavior engine initialized")  # Boot confirmation

    def set_behavior(self, behavior_name):
        """Switch behavior, reset start timer, skip duplicate, log transition."""
        if behavior_name == self.current_behavior:  # Avoid spam / duplicate timers
            return  # No change

        old_behavior = self.current_behavior  # For log message
        self.current_behavior = behavior_name  # New mode
        self.behavior_start_ms = reset_timer()  # Duration counts from transition
        log("Behavior changed: " + old_behavior + " -> " + behavior_name)  # Audit

    def get_behavior(self):
        """Return current behavior name string."""
        return self.current_behavior  # e.g. "idle", "greeting"

    def idle_behavior(self):
        """Placeholder: low-energy / background idle actions go here later."""
        log("Idle behavior running")  # Loud today — rate-limit when idle gets real motion

    def greeting_behavior(self):
        """Timed greeting; after GREETING_DURATION_MS, return to idle."""
        log("Greeting behavior running")  # Placeholder for wave / sound
        if has_elapsed(self.behavior_start_ms, GREETING_DURATION_MS):  # Config-driven length
            self.set_behavior("idle")  # End greeting

    def thinking_behavior(self):
        """Timed 'busy' display; after THINKING_DURATION_MS, return to idle."""
        log("Thinking behavior running")  # Placeholder for LEDs / motion
        if has_elapsed(self.behavior_start_ms, THINKING_DURATION_MS):  # Pretend processing window
            self.set_behavior("idle")  # Back to baseline

    def update(self):
        """Dispatch one tick of the current behavior (call every main loop)."""
        if self.current_behavior == "idle":  # Default ambient mode
            self.idle_behavior()  # Run idle tick
        elif self.current_behavior == "greeting":  # Social / detect sequence
            self.greeting_behavior()  # May self-transition to idle
        elif self.current_behavior == "thinking":  # Command processing facade
            self.thinking_behavior()  # May self-transition to idle
        elif self.current_behavior == "none":  # Sleep / uninitialized — no work
            pass  # Explicit no-op
        else:  # Typo or future behavior not handled
            log("Unknown behavior: " + str(self.current_behavior))  # Catch mistakes early
