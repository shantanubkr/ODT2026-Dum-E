"""DUM-E System Configuration. Tune after hardware and behavior testing."""

# =========================
# DUM-E System Configuration
# MicroPython-only constants
# =========================

# Main loop
LOOP_DELAY_MS = 50  # ms sleep per loop iteration — sets max poll/update rate

# Command system
COMMAND_HISTORY_SIZE = 5  # Rolling window of normalized commands for 'history'
MAX_LOG_ENTRIES = 10  # Ring buffer depth in utils.logger

# Activity / idle timing
IDLE_TIMEOUT_MS = 30_000  # ms without activity before ACTIVE → IDLE
SLEEP_TIMEOUT_MS = 300_000  # ms without activity before → SLEEP (e.g. 5 minutes)

# Distance thresholds
DIST_NEAR_CM = 20  # "close" for future PIR / ultrasonic behavior
DIST_FAR_CM = 80  # "far" threshold
OBSTACLE_STOP_CM = 10  # Hard stop distance if sensor says obstacle

# Sensor timeout / fallback
SENSOR_TIMEOUT_MS = 2_000  # ms without valid reading → fault / fallback path

# Motion / behavior timing
GREETING_DURATION_MS = 2_000  # ms greeting_behavior runs before auto-idle
THINKING_DURATION_MS = 1_500  # ms thinking_behavior runs before auto-idle
WAKE_COOLDOWN_MS = 3_000  # ms reserved for post-wake debounce (future use)

# Debug
DEBUG = True
