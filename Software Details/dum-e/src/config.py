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

# Activity / idle timing
IDLE_TIMEOUT_MS = 30_000  # ms without activity before ACTIVE → IDLE
SLEEP_TIMEOUT_MS = 300_000  # ms without activity before → SLEEP (e.g. 5 minutes)

# Reserved (no distance sensors in current build)
DIST_NEAR_CM = 20
DIST_FAR_CM = 80
OBSTACLE_STOP_CM = 10
SENSOR_TIMEOUT_MS = 2_000

# Motion / behavior timing
GREETING_DURATION_MS = 2_000  # ms greeting_behavior runs before auto-idle
THINKING_DURATION_MS = 1_500  # ms thinking_behavior runs before auto-idle
WAKE_COOLDOWN_MS = 3_000  # ms reserved for post-wake debounce (future use)

# Kinematics — CAD names (base = mechanical only, no servo)
# Order: waist → upper_arm → forearm → hand → end_effector (gripper)
NUM_JOINTS = 5
JOINT_HOME_ANGLES = [90, 90, 90, 90, 90]

# Software joint limits (degrees) — set to match mechanical stops after assembly.
JOINT_ANGLE_MIN_DEG = [0, 0, 0, 0, 0]
JOINT_ANGLE_MAX_DEG = [180, 180, 180, 180, 180]

# Per-joint PWM pulse width calibration (µs) — tune so 0°/180° match mechanics.
# Defaults are typical hobby servos; measure each joint after wiring (see docs/firmware_setup.md).
SERVO_PWM_MIN_US = [500, 500, 500, 500, 500]
SERVO_PWM_MAX_US = [2500, 2500, 2500, 2500, 2500]

# Debug
DEBUG = True
