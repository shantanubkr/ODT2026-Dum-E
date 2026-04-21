"""DUM-E System Configuration. Tune after hardware and behavior testing."""

# =========================
# DUM-E System Configuration
# MicroPython-only constants
# =========================

# Main loop
LOOP_DELAY_MS = 50  # ms sleep per loop iteration — sets max poll/update rate

# Physical panel buttons — current hardware has none; control via dashboard / USB serial / REPL.
USE_PHYSICAL_BUTTONS = False

# Motion: degrees moved per loop tick toward target (1 = slower/smoother; 2–3 = faster).
MOTION_STEP_DEG_PER_TICK = 1

# Command system
COMMAND_HISTORY_SIZE = 5  # Rolling window of normalized commands for 'history'
MAX_LOG_ENTRIES = 10  # Ring buffer depth in utils.logger

# Activity / sleep timing (single tier: inactivity → SLEEP, no IDLE state)
SLEEP_TIMEOUT_MS = 300_000  # ms without activity before ACTIVE → SLEEP (e.g. 5 minutes)

# Curious idle wander (behavior "idle" while state ACTIVE)
IDLE_WANDER_MIN_MS = 2_000
IDLE_WANDER_MAX_MS = 5_000
IDLE_WANDER_JOINT_DELTA_MAX = 25  # max ° from home per joint for random wander targets
IDLE_INSPECT_NOD_SWING_DEG = 15
IDLE_INSPECT_PHASE_MS = 280
IDLE_INSPECT_SETTLE_MS = 400

# Reserved (no distance sensors in current build)
DIST_NEAR_CM = 20
DIST_FAR_CM = 80
OBSTACLE_STOP_CM = 10
SENSOR_TIMEOUT_MS = 2_000

# Motion / behavior timing
GREET_SEQUENCE_TIMEOUT_MS = 12_000  # safety cap for home + hand-nod greet FSM
THINKING_DURATION_MS = 1_500  # ms thinking_behavior runs before auto-idle

# Dance behavior: beat length × steps loops until DANCE_DURATION_MS
DANCE_BEAT_MS = 320
DANCE_DURATION_MS = 10_000

# Sad expression: droop → hold → either sad_hold (if state SAD) or recover to pre-expression pose
SAD_PEAK_HOLD_MS = 2_500
SAD_RETURN_EASE_MS = 1_200
WAKE_COOLDOWN_MS = 3_000  # ms reserved for post-wake debounce (future use)

# Kinematics — aligned with dum_e_description/urdf/dum-e.xacro via robot_kinematics
NUM_JOINTS = 5

try:
    from robot_kinematics import neutral_pose_firmware_deg, sad_slouch_firmware_deg

    JOINT_HOME_ANGLES = neutral_pose_firmware_deg()
    _sad_slouch = sad_slouch_firmware_deg()
    SAD_SLOUCH_UPPER_DEG = _sad_slouch[1]
    SAD_SLOUCH_FOREARM_DEG = _sad_slouch[2]
    SAD_SLOUCH_HAND_DEG = _sad_slouch[3]
except ImportError:
    JOINT_HOME_ANGLES = [90, 90, 90, 90, 90]
    SAD_SLOUCH_UPPER_DEG = 28
    SAD_SLOUCH_FOREARM_DEG = 118
    SAD_SLOUCH_HAND_DEG = 72

# Software joint limits (degrees) — set to match mechanical stops after assembly.
JOINT_ANGLE_MIN_DEG = [0, 0, 0, 0, 0]
JOINT_ANGLE_MAX_DEG = [180, 180, 180, 180, 180]

# Per-joint PWM pulse width calibration (µs) — tune so 0°/180° match mechanics.
# Defaults are typical hobby servos; measure each joint after wiring (see docs/firmware_setup.md).
SERVO_PWM_MIN_US = [500, 500, 500, 500, 500]
SERVO_PWM_MAX_US = [2500, 2500, 2500, 2500, 2500]

# Debug
DEBUG = True
