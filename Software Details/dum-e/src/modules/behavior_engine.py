# High-level personality / motion: idle, greeting, thinking + 5 expression behaviors.
# Expression behaviors own the motion controller for their duration; driven by update() each loop.

from utils.logger import log

from utils.timers import reset_timer, has_elapsed, current_millis

from config import GREETING_DURATION_MS, JOINT_HOME_ANGLES, THINKING_DURATION_MS


class BehaviorEngine:
    """One active behavior name; timed greeting/thinking return to idle automatically.

    Expression behaviors (express_*) require a MotionController reference.
    Call set_motion_controller(mc) once from main.py after both objects exist.
    """

    def __init__(self):
        self.current_behavior = "none"
        self.behavior_start_ms = reset_timer()

        # Motion controller reference — injected after construction to avoid ordering
        # constraints at module level in main.py.
        self._mc = None

        # Shared state for all expression behaviors.
        # _expr_phase: which sub-step of the active expression we are in.
        # _expr_phase_start: timestamp (ms) when the current phase began.
        # _expr_base: joint angles captured at the moment run_behavior() was called,
        #             used as the "return to" position after the expression ends.
        self._expr_phase = 0
        self._expr_phase_start = 0
        self._expr_base = list(JOINT_HOME_ANGLES)

        log("Behavior engine initialized")

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def set_motion_controller(self, mc):
        """Inject MotionController after construction; required for expression behaviors."""
        self._mc = mc
        log("Behavior engine: motion controller linked")

    # ------------------------------------------------------------------
    # Core behavior management
    # ------------------------------------------------------------------

    def set_behavior(self, behavior_name):
        """Switch behavior, reset start timer, skip duplicate, log transition."""
        if behavior_name == self.current_behavior:
            return
        old_behavior = self.current_behavior
        self.current_behavior = behavior_name
        self.behavior_start_ms = reset_timer()
        log("Behavior changed: " + old_behavior + " -> " + behavior_name)

    def run_behavior(self, name):
        """Start a named expression behavior.

        Saves the arm's current angles as the return position, resets the
        per-expression phase counter and timer, then delegates to set_behavior().
        Safe to call even without a motion controller — phases will still tick
        but no servo movement will occur.
        """
        if self._mc is not None:
            self._expr_base = list(self._mc.current_angles)
        self._expr_phase = 0
        self._expr_phase_start = current_millis()
        self.set_behavior(name)

    def get_behavior(self):
        """Return current behavior name string."""
        return self.current_behavior

    # ------------------------------------------------------------------
    # Internal motion helper
    # ------------------------------------------------------------------

    def _move(self, angles):
        """Set target angles on the motion controller if one is linked."""
        if self._mc is not None:
            self._mc.move_to_pose(list(angles))

    def _phase_elapsed(self, duration_ms):
        """True when the current expression phase has run for at least duration_ms."""
        return has_elapsed(self._expr_phase_start, duration_ms)

    def _next_phase(self):
        """Advance to the next expression phase and reset its timer."""
        self._expr_phase += 1
        self._expr_phase_start = current_millis()

    def _pose_waist(self, waist_deg):
        """Copy _expr_base with waist (index 0) replaced."""
        p = list(self._expr_base)
        p[0] = max(0, min(180, waist_deg))
        return p

    def _pose_upper_arm(self, ua_deg):
        """Copy _expr_base with upper_arm (index 1) replaced."""
        p = list(self._expr_base)
        p[1] = max(0, min(180, ua_deg))
        return p

    # ------------------------------------------------------------------
    # Existing timed behaviors
    # ------------------------------------------------------------------

    def idle_behavior(self):
        """Placeholder low-energy idle — no per-tick log (would flood the REPL)."""
        pass

    def greeting_behavior(self):
        """Timed greeting; after GREETING_DURATION_MS, return to idle."""
        if has_elapsed(self.behavior_start_ms, GREETING_DURATION_MS):
            self.set_behavior("idle")

    def thinking_behavior(self):
        """Timed 'busy' display; after THINKING_DURATION_MS, return to idle."""
        if has_elapsed(self.behavior_start_ms, THINKING_DURATION_MS):
            self.set_behavior("idle")

    # ------------------------------------------------------------------
    # Expression behaviors — each is a small phase-state-machine.
    # Phase transitions fire on elapsed-time checks; actual smooth motion
    # is carried out by MotionController.update() in the main loop.
    # _expr_base holds the arm angles at the moment run_behavior() was called
    # so the arm can return to its pre-expression position.
    # ------------------------------------------------------------------

    def express_happy_behavior(self):
        """Rapid small oscillation of the waist ±10°, 3 full swings, ~1.5 s total.

        6 half-swing phases × 250 ms each, then a return phase → idle.
        """
        b0 = self._expr_base[0]
        offsets = [+10, -10, +10, -10, +10, -10]

        if self._expr_phase < len(offsets):
            angle = max(0, min(180, b0 + offsets[self._expr_phase]))
            self._move(self._pose_waist(angle))
            if self._phase_elapsed(250):
                self._next_phase()
        elif self._expr_phase == len(offsets):
            self._move(self._expr_base)
            if self._phase_elapsed(400):
                self.set_behavior("idle")

    def express_sad_behavior(self):
        """Slow droop: lower upper_arm joint to minimum, hold 1 s, return slowly."""

        if self._expr_phase == 0:
            self._move(self._pose_upper_arm(0))
            self._next_phase()
        elif self._expr_phase == 1:
            if self._phase_elapsed(5000):
                self._next_phase()
        elif self._expr_phase == 2:
            if self._phase_elapsed(1000):
                self._move(self._expr_base)
                self._next_phase()
        elif self._expr_phase == 3:
            if self._phase_elapsed(5000):
                self.set_behavior("idle")

    def express_greet_behavior(self):
        """Wave: swing waist left/right ±30°, then center. 4 phases × 700 ms."""
        b0 = self._expr_base[0]
        swing_targets = [
            max(0, min(180, b0 - 30)),
            max(0, min(180, b0 + 30)),
            max(0, min(180, b0 - 30)),
            b0,
        ]
        PHASE_MS = 700

        if self._expr_phase < len(swing_targets):
            self._move(self._pose_waist(swing_targets[self._expr_phase]))
            if self._phase_elapsed(PHASE_MS):
                self._next_phase()
        else:
            self.set_behavior("idle")

    def express_bye_behavior(self):
        """Slow wave on waist (1200 ms/phase), then move to JOINT_HOME_ANGLES."""
        b0 = self._expr_base[0]
        swing_targets = [
            max(0, min(180, b0 - 30)),
            max(0, min(180, b0 + 30)),
            max(0, min(180, b0 - 30)),
            b0,
        ]
        PHASE_MS = 1200

        if self._expr_phase < len(swing_targets):
            self._move(self._pose_waist(swing_targets[self._expr_phase]))
            if self._phase_elapsed(PHASE_MS):
                self._next_phase()
        elif self._expr_phase == len(swing_targets):
            if self._phase_elapsed(PHASE_MS):
                self._move(list(JOINT_HOME_ANGLES))
                self._next_phase()
        else:
            if self._phase_elapsed(3000):
                self.set_behavior("idle")

    def express_present_behavior(self):
        """Forward presentation pose: waist center, upper_arm 45°, forearm level, hand open.

        Does NOT auto-transition.
        """
        if self._expr_phase == 0:
            self._move(
                [90, 45, 0, JOINT_HOME_ANGLES[3], JOINT_HOME_ANGLES[4]]
            )
            self._next_phase()
        # Phase 1+: hold until externally interrupted.

    # ------------------------------------------------------------------
    # Main dispatch
    # ------------------------------------------------------------------

    def update(self):
        """Dispatch one tick of the current behavior (called every main loop iteration)."""
        if self.current_behavior == "idle":
            self.idle_behavior()
        elif self.current_behavior == "greeting":
            self.greeting_behavior()
        elif self.current_behavior == "thinking":
            self.thinking_behavior()
        elif self.current_behavior == "none":
            pass
        elif self.current_behavior == "express_happy":
            self.express_happy_behavior()
        elif self.current_behavior == "express_sad":
            self.express_sad_behavior()
        elif self.current_behavior == "express_greet":
            self.express_greet_behavior()
        elif self.current_behavior == "express_bye":
            self.express_bye_behavior()
        elif self.current_behavior == "express_present":
            self.express_present_behavior()
        else:
            log("Unknown behavior: " + str(self.current_behavior))
