"""DUM-E System Configuration. Tune after hardware and behavior testing."""

# =========================
# DUM-E System Configuration
# MicroPython-only constants
# =========================

# Main loop — ~0.04 s matches hardware “smooth scan” (30–50 ms).
LOOP_DELAY_MS = 40

# Physical panel buttons — current hardware has none; control via dashboard / USB serial / REPL.
USE_PHYSICAL_BUTTONS = False

# All arm joints: PCA9685 (I2C) when True, or four GPIOs when False — see pins.py.
USE_PCA9685 = True

# Nordic UART Service (BLE) for commands from laptop — set True only if you use BLE.
# False: USB/serial only (no bluetooth import; avoids OSError on builds/boards with flaky BLE).
USE_BLE_NUS = False
BLE_DEVICE_NAME = "DUM-E"

# Motion: exponential smoothing per loop — current += (target - current) * k (see motion_controller).
MOTION_SMOOTHING = 0.10
# Jitter: within this many ° of target, treat as reached (avoids micro-twitch).
MOTION_DEADZONE_DEG = 1.0
# On boot, ease from this pose to JOINT_HOME_ANGLES (set False to start already at home).
USE_BOOT_MOTION_SMOOTH = True
BOOT_MOTION_FROM_DEG = [90, 90, 90, 90]

# Command system
COMMAND_HISTORY_SIZE = 5  # Rolling window of normalized commands for 'history'
MAX_LOG_ENTRIES = 10  # Ring buffer depth in utils.logger

# Activity / sleep timing (single tier: inactivity → SLEEP, no IDLE state)
SLEEP_TIMEOUT_MS = 300_000  # ms without activity before ACTIVE → SLEEP (e.g. 5 minutes)

# Idle "look around" — new random targets every few seconds (behavior "idle", state ACTIVE)
IDLE_WANDER_MIN_MS = 3_000
IDLE_WANDER_MAX_MS = 6_000
# Per-joint (waist, upper, forearm, hand) random target ranges in ° — bias upward, hardware ref.
IDLE_LOOK_JOINT_RANGES = (
    (100, 130),  # base
    (100, 125),  # shoulder
    (105, 135),  # elbow
    (95, 115),   # head
)
IDLE_INSPECT_NOD_SWING_DEG = 15
IDLE_INSPECT_PHASE_MS = 280
IDLE_INSPECT_SETTLE_MS = 400

# STOP: move home → estop hold at home → auto clear after this (ms)
STOP_COOLDOWN_MS = 10_000

# Bad data / fault: error nod then auto home + idle after this (ms) from fault entry
DATA_ERROR_RECOVERY_MS = 5_000

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
NUM_JOINTS = 4

# Mechanical home / default scan pose (°) — hardware reference: [110, 110, 115, 105].
# Single source: `robot_kinematics.UPRIGHT_FIRMWARE_DEG` (re-imported below).
UPRIGHT_POSE_DEG = [110, 110, 115, 105]
JOINT_HOME_ANGLES = list(UPRIGHT_POSE_DEG)
SAD_SLOUCH_UPPER_DEG = 28
SAD_SLOUCH_FOREARM_DEG = 118
SAD_SLOUCH_HAND_DEG = 72

try:
    from robot_kinematics import UPRIGHT_FIRMWARE_DEG, sad_slouch_firmware_deg

    UPRIGHT_POSE_DEG = list(UPRIGHT_FIRMWARE_DEG)
    JOINT_HOME_ANGLES = list(UPRIGHT_FIRMWARE_DEG)
    _sad_slouch = sad_slouch_firmware_deg()
    SAD_SLOUCH_UPPER_DEG = _sad_slouch[1]
    SAD_SLOUCH_FOREARM_DEG = _sad_slouch[2]
    SAD_SLOUCH_HAND_DEG = _sad_slouch[3]
except (ImportError, Exception):
    pass

# Software joint limits (degrees) — set to match mechanical stops after assembly.
JOINT_ANGLE_MIN_DEG = [0, 0, 0, 0]
JOINT_ANGLE_MAX_DEG = [180, 180, 180, 180]

# Per-joint PWM pulse width calibration (µs) — tune so 0°/180° match mechanics.
# Defaults are typical hobby servos; measure each joint after wiring (see docs/firmware_setup.md).
SERVO_PWM_MIN_US = [500, 500, 500, 500]
SERVO_PWM_MAX_US = [2500, 2500, 2500, 2500]

# Debug
DEBUG = True
