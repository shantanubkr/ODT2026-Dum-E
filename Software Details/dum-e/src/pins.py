"""Hardware pins — four arm servos: PCA9685 (I2C) or direct GPIO.

Dashboard / USB serial / REPL for commands; no physical control buttons wired.

Firmware joint order (motion_controller, servos[0]..[3]): waist, upper_arm,
forearm, hand.

# PCA9685: servos on channels 0–3 in joint order (waist → hand), per hardware bring-up.

When config.USE_PCA9685 is False, motion_controller uses SERVO_WAIST … SERVO_HAND
GPIOs — do not use the same pins as the I2C bus to the PCA in that mode.
"""

# --- PCA9685 (I2C) ---
PCA9685_I2C_ID = 0
PCA9685_SDA = 21
PCA9685_SCL = 22
PCA9685_ADDR = 0x40

# Logical joint index → PCA9685 channel (0..3).
PCA9685_CH_WAIST = 0
PCA9685_CH_UPPER_ARM = 1
PCA9685_CH_FOREARM = 2
PCA9685_CH_HAND = 3

# --- Legacy: all servos on GPIO when USE_PCA9685 is False ---
SERVO_WAIST = 4
SERVO_UPPER_ARM = 22
SERVO_FOREARM = 23
SERVO_HAND = 21

# Optional manual buttons — only used if config.USE_PHYSICAL_BUTTONS is True.
BTN_J1 = 12
BTN_J2 = 13
BTN_J3 = 27
BTN_J4 = 32
BTN_UP = 25
BTN_DOWN = 18
