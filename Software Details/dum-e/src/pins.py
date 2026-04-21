"""GPIO assignments — servos only for current hardware.

Dashboard / USB serial / REPL for commands; no physical control buttons wired.

Servo order matches CAD / motion_controller: waist, upper_arm, forearm, hand,
end_effector. Base is mechanical only (no GPIO).

Hardware brief alignment: GPIO 4, 22, 23 for the first three joints; hand and
end_effector use the pins below — change here when your wiring is final.
"""

# Servo joints (PWM, 50 Hz) — see motion_controller.py
SERVO_WAIST = 4
SERVO_UPPER_ARM = 22
SERVO_FOREARM = 23
SERVO_HAND = 21
SERVO_END_EFFECTOR = 19

# Optional manual buttons — only used if config.USE_PHYSICAL_BUTTONS is True.
BTN_J1 = 12
BTN_J2 = 13
BTN_J3 = 27
BTN_J4 = 32
BTN_J5 = 33
BTN_UP = 25
BTN_DOWN = 18
