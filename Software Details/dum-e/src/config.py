"""DUM-E System Configuration. Tune after hardware and behavior testing."""

# =========================
# DUM-E System Configuration
# MicroPython-only constants
# =========================

# Main loop
LOOP_DELAY_MS = 50

# Command system
COMMAND_HISTORY_SIZE = 5
MAX_LOG_ENTRIES = 10

# Activity / idle timing
IDLE_TIMEOUT_MS = 30_000
SLEEP_TIMEOUT_MS = 300_000

# Distance thresholds
DIST_NEAR_CM = 20
DIST_FAR_CM = 80
OBSTACLE_STOP_CM = 10

# Sensor timeout / fallback
SENSOR_TIMEOUT_MS = 2_000

# Motion / behavior timing
GREETING_DURATION_MS = 2_000
THINKING_DURATION_MS = 1_500
WAKE_COOLDOWN_MS = 3_000

# Debug
DEBUG = True
