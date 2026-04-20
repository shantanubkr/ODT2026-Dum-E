# High-level personality / motion: idle, greeting, thinking + 5 expression behaviors.
# Expression behaviors own the motion controller for their duration; driven by update() each loop.

from utils.logger import log

from utils.timers import reset_timer, has_elapsed, current_millis

from config import GREETING_DURATION_MS, THINKING_DURATION_MS


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
        self._expr_base = [90, 90, 90]

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
        """Rapid small oscillation of the base joint ±10°, 3 full swings, ~1.5 s total.

        6 half-swing phases × 250 ms each, then a return phase → idle.
        Each phase calls _move() every tick (idempotent: just sets target_angles)
        and advances when the phase timer elapses.
        """
        b0, b1, b2 = self._expr_base[0], self._expr_base[1], self._expr_base[2]
        # Alternating ±10° offsets from base, 6 half-swings = 3 full oscillations.
        offsets = [+10, -10, +10, -10, +10, -10]

        if self._expr_phase < len(offsets):
            angle = max(0, min(180, b0 + offsets[self._expr_phase]))
            self._move([angle, b1, b2])
            if self._phase_elapsed(250):
                self._next_phase()
        elif self._expr_phase == len(offsets):
            # Return to the position the arm was in before the expression.
            self._move(self._expr_base)
            if self._phase_elapsed(400):
                self.set_behavior("idle")

    def express_sad_behavior(self):
        """Slow droop: lower shoulder joint to minimum, hold 1 s, return slowly.

        Phase 0: set shoulder target to 0° (droop down), wait for travel (up to 5 s).
        Phase 1: hold at low position for 1 s.
        Phase 2: set shoulder back to saved angle, wait for travel (up to 5 s).
        Phase 3: transition to idle.
        Travel time depends on how far the joint has to move at 1°/50 ms.
        """
        b0, b1, b2 = self._expr_base[0], self._expr_base[1], self._expr_base[2]

        if self._expr_phase == 0:
            # Kick off the droop to shoulder minimum on first entry.
            self._move([b0, 0, b2])
            self._next_phase()
        elif self._expr_phase == 1:
            # Wait long enough for the droop to complete (max 180° × 50 ms = 9 s).
            if self._phase_elapsed(5000):
                self._next_phase()
        elif self._expr_phase == 2:
            # Hold at the low position for 1 s, then start returning.
            if self._phase_elapsed(1000):
                self._move(self._expr_base)
                self._next_phase()
        elif self._expr_phase == 3:
            # Wait for return travel to complete.
            if self._phase_elapsed(5000):
                self.set_behavior("idle")

    def express_greet_behavior(self):
        """Wave: swing base joint left 30°, right 30°, left 30°, back to center. Moderate speed.

        4 swing phases × 700 ms; arm returns to its saved base angle at the end.
        Each phase sets its target every tick (idempotent) and advances when the timer elapses.
        """
        b0, b1, b2 = self._expr_base[0], self._expr_base[1], self._expr_base[2]
        swing_targets = [
            max(0, min(180, b0 - 30)),  # phase 0: left
            max(0, min(180, b0 + 30)),  # phase 1: right
            max(0, min(180, b0 - 30)),  # phase 2: left again
            b0,                          # phase 3: back to center
        ]
        PHASE_MS = 700

        if self._expr_phase < len(swing_targets):
            self._move([swing_targets[self._expr_phase], b1, b2])
            if self._phase_elapsed(PHASE_MS):
                self._next_phase()
        else:
            self.set_behavior("idle")

    def express_bye_behavior(self):
        """Slow wave (same pattern as greet but 1200 ms/phase), then rest at home.

        After the wave returns to center the arm moves all joints to [90, 90, 90]
        to signal a proper sleep/rest posture before transitioning to idle.
        Phases 0-3: slow wave. Phase 4: move to home. Phase 5: wait for travel → idle.
        """
        b0, b1, b2 = self._expr_base[0], self._expr_base[1], self._expr_base[2]
        swing_targets = [
            max(0, min(180, b0 - 30)),  # phase 0: left
            max(0, min(180, b0 + 30)),  # phase 1: right
            max(0, min(180, b0 - 30)),  # phase 2: left again
            b0,                          # phase 3: back to center
        ]
        PHASE_MS = 1200

        if self._expr_phase < len(swing_targets):
            self._move([swing_targets[self._expr_phase], b1, b2])
            if self._phase_elapsed(PHASE_MS):
                self._next_phase()
        elif self._expr_phase == len(swing_targets):
            # Wave complete — move all joints to home/rest position.
            if self._phase_elapsed(PHASE_MS):
                self._move([90, 90, 90])
                self._next_phase()
        else:
            # Wait for home travel to complete (max 90° × 50 ms = 4.5 s), then idle.
            if self._phase_elapsed(3000):
                self.set_behavior("idle")

    def express_present_behavior(self):
        """Extend arm to a forward-facing presentation pose and hold indefinitely.

        Pose: base = 90° (center), shoulder = 45° (mid height), elbow = 0° (level).
        This behavior does NOT auto-transition; it holds until the next command
        explicitly calls set_behavior() or run_behavior().
        """
        if self._expr_phase == 0:
            self._move([90, 45, 0])
            self._next_phase()
        # Phase 1+: do nothing — hold until externally interrupted.

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
