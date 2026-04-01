"""Application-wide constants. Tune after hardware and behavior testing."""

# --- timing ---
LOOP_DELAY_MS = 1000  # main loop sleep; matches starter 1 s tick

# --- distance thresholds (cm); used by safety / perception later ---
DIST_NEAR_CM = 15
DIST_FAR_CM = 60
OBSTACLE_STOP_CM = 10

# --- idle / command buffering ---
IDLE_TIMEOUT_MS = 30_000
COMMAND_HISTORY_SIZE = 16
