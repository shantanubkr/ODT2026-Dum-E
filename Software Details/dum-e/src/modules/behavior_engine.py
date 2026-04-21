# High-level personality / motion: idle, greeting, thinking + 5 expression behaviors.
# Expression behaviors own the motion controller for their duration; driven by update() each loop.

import random

from utils.logger import log

from utils.timers import reset_timer, has_elapsed, current_millis, elapsed_ms

from config import (
    DANCE_BEAT_MS,
    DANCE_DURATION_MS,
    GREET_SEQUENCE_TIMEOUT_MS,
    IDLE_INSPECT_NOD_SWING_DEG,
    IDLE_INSPECT_PHASE_MS,
    IDLE_INSPECT_SETTLE_MS,
    IDLE_WANDER_JOINT_DELTA_MAX,
    IDLE_WANDER_MAX_MS,
    IDLE_WANDER_MIN_MS,
    JOINT_ANGLE_MAX_DEG,
    JOINT_ANGLE_MIN_DEG,
    JOINT_HOME_ANGLES,
    SAD_PEAK_HOLD_MS,
    SAD_RETURN_EASE_MS,
    SAD_SLOUCH_FOREARM_DEG,
    SAD_SLOUCH_HAND_DEG,
    SAD_SLOUCH_UPPER_DEG,
    THINKING_DURATION_MS,
)

from modules.state_machine import States

try:
    from robot_kinematics import express_present_firmware_deg
except ImportError:

    def express_present_firmware_deg():
        return [90, 45, 0, JOINT_HOME_ANGLES[3], JOINT_HOME_ANGLES[4]]

# Dance: offsets (waist, upper_arm, forearm) added to JOINT_HOME_ANGLES; hand/ee stay at home.
_DANCE_STEPS = [
    (0, 0, 0),
    (32, -14, 18),
    (-32, -14, 18),
    (32, 12, -12),
    (-32, 12, -12),
    (0, -20, 25),
    (0, 18, -20),
    (22, 8, 10),
    (-22, 8, 10),
]


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

        # Optional: gate idle wander / inspect (firmware + desktop runtime).
        self._state_machine = None
        self._safety_manager = None

        # Idle wander + vision inspect (behavior must be "idle").
        self._wander_deadline_ms = None  # ticks_ms when next wander pose is picked
        self._wander_interval_ms = IDLE_WANDER_MIN_MS
        self._idle_wander_tick = 0
        self._idle_inspect_phase = None  # None = not inspecting; else 0..n
        self._inspect_phase_start_ms = 0
        self._inspect_waist = 90.0
        self._inspect_hand = 90.0
        self._inspect_base = list(JOINT_HOME_ANGLES)

        # Shared state for all expression behaviors.
        # _expr_phase: which sub-step of the active expression we are in.
        # _expr_phase_start: timestamp (ms) when the current phase began.
        # _expr_base: joint angles captured at the moment run_behavior() was called,
        #             used as the "return to" position after the expression ends.
        self._expr_phase = 0
        self._expr_phase_start = 0
        self._expr_base = list(JOINT_HOME_ANGLES)

        # Home pose + hand nod (greeting / express_greet).
        self._greet_seq_phase = None  # None = inactive; 0..6 = FSM
        self._greet_seq_start = 0
        self._greet_return_base = None  # None → stay at home; else joints to restore (express_greet)
        self._dance_last_step = -1

        log("Behavior engine initialized")

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def set_motion_controller(self, mc):
        """Inject MotionController after construction; required for expression behaviors."""
        self._mc = mc
        log("Behavior engine: motion controller linked")

    def set_runtime_guards(self, state_machine, safety_manager):
        """Idle wander runs only in ACTIVE with can_move(); inject from main / dum_e_runtime."""
        self._state_machine = state_machine
        self._safety_manager = safety_manager

    # ------------------------------------------------------------------
    # Core behavior management
    # ------------------------------------------------------------------

    def set_behavior(self, behavior_name):
        """Switch behavior, reset start timer, skip duplicate, log transition."""
        if behavior_name == self.current_behavior:
            return
        old_behavior = self.current_behavior
        if old_behavior == "idle" and behavior_name != "idle":
            self.cancel_idle_inspect()
            self._wander_deadline_ms = None
        elif behavior_name == "idle" and old_behavior != "idle":
            self.cancel_idle_inspect()
            self._wander_deadline_ms = None
        self.current_behavior = behavior_name
        self.behavior_start_ms = reset_timer()
        log("Behavior changed: " + old_behavior + " -> " + behavior_name)

        if behavior_name == "greeting":
            self._greet_return_base = None
            self._greet_seq_phase = 0
            self._greet_seq_start = reset_timer()
        elif behavior_name == "express_greet":
            if self._greet_seq_phase is None:
                self._greet_return_base = list(self._expr_base)
                self._greet_seq_phase = 0
            self._greet_seq_start = reset_timer()
        elif behavior_name == "sad_hold":
            self._move(self._sad_slouch_pose())
        elif behavior_name == "dancing":
            self._dance_last_step = -1
        elif behavior_name not in ("greeting", "express_greet"):
            self._greet_seq_phase = None

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
        if name == "express_greet":
            self._greet_return_base = list(self._expr_base)
            self._greet_seq_phase = 0
        self.set_behavior(name)

    def get_behavior(self):
        """Return current behavior name string."""
        return self.current_behavior

    def get_idle_substate(self):
        """Telemetry: wander vs inspect while curious; 'none' if not in idle behavior."""
        if self.current_behavior != "idle":
            return "none"
        if self._idle_inspect_phase is not None:
            return "inspect"
        return "wander"

    def get_idle_wander_tick(self):
        """Increments when a new wander target is chosen — for desktop sound hooks."""
        return int(self._idle_wander_tick)

    def cancel_idle_inspect(self):
        self._idle_inspect_phase = None

    def begin_idle_inspect(self, waist_deg, hand_deg):
        """Vision / desktop: look toward a blob, nod, then resume wander."""
        if self.current_behavior != "idle":
            return
        if not self._idle_motion_allowed():
            return
        self._inspect_waist = max(0.0, min(180.0, float(waist_deg)))
        self._inspect_hand = max(0.0, min(180.0, float(hand_deg)))
        if self._mc is not None:
            self._inspect_base = [float(x) for x in self._mc.current_angles]
        else:
            self._inspect_base = list(JOINT_HOME_ANGLES)
        self._idle_inspect_phase = 0
        self._inspect_phase_start_ms = reset_timer()

    def _idle_motion_allowed(self):
        if self._state_machine is None:
            return True
        if not self._state_machine.is_state(States.ACTIVE):
            return False
        if self._safety_manager is not None and not self._safety_manager.can_move():
            return False
        return True

    def _clamp_joint_deg(self, joint_idx, angle):
        lo = float(JOINT_ANGLE_MIN_DEG[joint_idx])
        hi = float(JOINT_ANGLE_MAX_DEG[joint_idx])
        a = float(angle)
        return max(lo, min(hi, a))

    def _pick_wander_pose(self):
        base = list(JOINT_HOME_ANGLES)
        if self._mc is not None:
            base = [float(x) for x in self._mc.current_angles]
        d = IDLE_WANDER_JOINT_DELTA_MAX
        target = []
        for i in range(5):
            delta = random.randint(-d, d)
            target.append(self._clamp_joint_deg(i, base[i] + delta))
        self._move(target)
        self._idle_wander_tick += 1

    def _idle_inspect_tick(self):
        if self._idle_inspect_phase is None:
            return

        if self._idle_inspect_phase == 0:
            pose = [
                self._inspect_waist,
                self._inspect_base[1],
                self._inspect_base[2],
                self._inspect_hand,
                self._inspect_base[4],
            ]
            self._move(pose)
            self._idle_inspect_phase = 1
            self._inspect_phase_start_ms = reset_timer()
            return

        if self._idle_inspect_phase == 1:
            if not has_elapsed(self._inspect_phase_start_ms, IDLE_INSPECT_SETTLE_MS):
                return
            self._idle_inspect_phase = 2
            self._inspect_phase_start_ms = reset_timer()

        nod_i = self._idle_inspect_phase - 2
        b_hand = self._inspect_base[3]
        swing = float(IDLE_INSPECT_NOD_SWING_DEG)
        pattern = [b_hand + swing, b_hand - swing, b_hand + swing, b_hand]
        if nod_i < len(pattern):
            if nod_i > 0 and not has_elapsed(self._inspect_phase_start_ms, IDLE_INSPECT_PHASE_MS):
                return
            pose = [
                self._inspect_waist,
                self._inspect_base[1],
                self._inspect_base[2],
                pattern[nod_i],
                self._inspect_base[4],
            ]
            self._move(pose)
            self._idle_inspect_phase += 1
            self._inspect_phase_start_ms = reset_timer()
            return

        if not has_elapsed(self._inspect_phase_start_ms, IDLE_INSPECT_SETTLE_MS):
            return
        self._move(self._inspect_base)
        self._idle_inspect_phase = None
        self._wander_deadline_ms = None

    def _home_pose_deg(self):
        return [float(x) for x in JOINT_HOME_ANGLES]

    def _sad_slouch_pose(self):
        """Sustained sad posture — preserves waist & gripper from pre-expression base."""
        b = self._expr_base
        return [
            self._clamp_joint_deg(0, b[0]),
            self._clamp_joint_deg(1, SAD_SLOUCH_UPPER_DEG),
            self._clamp_joint_deg(2, SAD_SLOUCH_FOREARM_DEG),
            self._clamp_joint_deg(3, SAD_SLOUCH_HAND_DEG),
            self._clamp_joint_deg(4, b[4]),
        ]

    def _tick_greet_home_nod(self):
        """Move to home, nod hand, then idle (or restore pre-expression pose)."""
        if self._greet_seq_phase is None:
            return
        if has_elapsed(self.behavior_start_ms, GREET_SEQUENCE_TIMEOUT_MS):
            self._greet_seq_phase = None
            self.set_behavior("idle")
            log("Greet sequence aborted by timeout")
            return

        home = self._home_pose_deg()
        hb = home[3]
        swing = float(IDLE_INSPECT_NOD_SWING_DEG)
        pattern = [hb + swing, hb - swing, hb + swing, hb]

        if self._greet_seq_phase == 0:
            self._move(home)
            self._greet_seq_phase = 1
            self._greet_seq_start = reset_timer()
            return

        if self._greet_seq_phase == 1:
            if not has_elapsed(self._greet_seq_start, IDLE_INSPECT_SETTLE_MS):
                return
            self._greet_seq_phase = 2
            self._greet_seq_start = reset_timer()
            return

        nod_i = self._greet_seq_phase - 2
        if nod_i < len(pattern):
            if nod_i > 0 and not has_elapsed(self._greet_seq_start, IDLE_INSPECT_PHASE_MS):
                return
            pose = list(home)
            pose[3] = self._clamp_joint_deg(3, pattern[nod_i])
            self._move(pose)
            self._greet_seq_phase += 1
            self._greet_seq_start = reset_timer()
            return

        if not has_elapsed(self._greet_seq_start, IDLE_INSPECT_SETTLE_MS):
            return

        ret = self._greet_return_base
        if ret is not None:
            self._move([self._clamp_joint_deg(i, ret[i]) for i in range(5)])
        self._greet_seq_phase = None
        self.set_behavior("idle")

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
        """Curious wander in ACTIVE; inspect when begin_idle_inspect() is used."""
        if not self._idle_motion_allowed():
            return
        if self._idle_inspect_phase is not None:
            self._idle_inspect_tick()
            return
        if self._wander_deadline_ms is None:
            self._wander_interval_ms = random.randint(IDLE_WANDER_MIN_MS, IDLE_WANDER_MAX_MS)
            self._wander_deadline_ms = reset_timer()
            return
        if has_elapsed(self._wander_deadline_ms, self._wander_interval_ms):
            self._pick_wander_pose()
            self._wander_interval_ms = random.randint(IDLE_WANDER_MIN_MS, IDLE_WANDER_MAX_MS)
            self._wander_deadline_ms = reset_timer()

    def greeting_behavior(self):
        """GREET command / sentiment: home pose, hand nod, then idle."""
        self._tick_greet_home_nod()

    def thinking_behavior(self):
        """Timed 'busy' display; after THINKING_DURATION_MS, return to idle."""
        if has_elapsed(self.behavior_start_ms, THINKING_DURATION_MS):
            self.set_behavior("idle")

    def _dance_pose_for_step(self, step_idx: int) -> list:
        h = [float(x) for x in JOINT_HOME_ANGLES]
        dw, du, df = _DANCE_STEPS[step_idx % len(_DANCE_STEPS)]
        h[0] = self._clamp_joint_deg(0, h[0] + dw)
        h[1] = self._clamp_joint_deg(1, h[1] + du)
        h[2] = self._clamp_joint_deg(2, h[2] + df)
        return h

    def dancing_behavior(self):
        """Rhythmic waist / arm sway from home; ends after DANCE_DURATION_MS."""
        if self._state_machine is not None:
            if self._state_machine.is_state(States.ERROR) or self._state_machine.is_state(
                States.SLEEP
            ):
                self.set_behavior("idle")
                return
        if self._safety_manager is not None and not self._safety_manager.can_move():
            self.set_behavior("idle")
            return

        if has_elapsed(self.behavior_start_ms, DANCE_DURATION_MS):
            self._move(list(JOINT_HOME_ANGLES))
            self.set_behavior("idle")
            return

        beat = elapsed_ms(self.behavior_start_ms) // DANCE_BEAT_MS
        step = int(beat % len(_DANCE_STEPS))
        if step != self._dance_last_step:
            self._dance_last_step = step
            self._move(self._dance_pose_for_step(step))

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
        """Slouch, hold, then sad_hold if state SAD else ease back to pre-expression pose."""

        if self._expr_phase == 0:
            self._move(self._sad_slouch_pose())
            self._next_phase()
        elif self._expr_phase == 1:
            if self._phase_elapsed(SAD_PEAK_HOLD_MS):
                self._next_phase()
        elif self._expr_phase == 2:
            if self._state_machine is not None and self._state_machine.is_state(States.SAD):
                self.set_behavior("sad_hold")
                return
            self._move(self._expr_base)
            self._next_phase()
        elif self._expr_phase == 3:
            if self._phase_elapsed(SAD_RETURN_EASE_MS):
                self.set_behavior("idle")

    def sad_hold_behavior(self):
        """Mood state — pose issued on set_behavior; no motion until next behavior."""
        pass

    def express_greet_behavior(self):
        """Same motion as greeting: go home, nod hand, restore pre-expression pose."""
        self._tick_greet_home_nod()

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
            pose = express_present_firmware_deg()
            self._move([self._clamp_joint_deg(i, pose[i]) for i in range(5)])
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
        elif self.current_behavior == "dancing":
            self.dancing_behavior()
        elif self.current_behavior == "none":
            pass
        elif self.current_behavior == "express_happy":
            self.express_happy_behavior()
        elif self.current_behavior == "express_sad":
            self.express_sad_behavior()
        elif self.current_behavior == "sad_hold":
            self.sad_hold_behavior()
        elif self.current_behavior == "express_greet":
            self.express_greet_behavior()
        elif self.current_behavior == "express_bye":
            self.express_bye_behavior()
        elif self.current_behavior == "express_present":
            self.express_present_behavior()
        else:
            log("Unknown behavior: " + str(self.current_behavior))
