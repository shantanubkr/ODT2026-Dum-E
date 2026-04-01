"""
GPIO and bus assignments for DUM-E.

**PLACEHOLDERS ONLY** — update every value after hardware is finalized and
document the same mapping in docs/pin_map.md.
"""

# --- steppers (DRV8825: STEP, DIR, ENABLE per axis) ---
STEPPER_0_STEP = None  # TODO
STEPPER_0_DIR = None
STEPPER_0_ENABLE = None
STEPPER_1_STEP = None
STEPPER_1_DIR = None
STEPPER_1_ENABLE = None

# --- ultrasonic (HC-SR04) ---
ULTRASONIC_TRIG = None  # TODO
ULTRASONIC_ECHO = None

# --- VL53L0X (I2C; pins are ESP32 I2C SDA/SCL) ---
I2C_SDA = None  # TODO
I2C_SCL = None

# --- buzzer ---
BUZZER = None  # TODO

# --- emergency stop (active level TBD in driver/safety) ---
EMERGENCY_STOP = None  # TODO
