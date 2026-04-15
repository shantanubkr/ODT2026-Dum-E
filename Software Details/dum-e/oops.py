"""
Robotic Arm Controller
MicroPython for ESP32 - Direct Servo PWM
---------------------------------------------
Hardware:
  Servo 1 (Base)    -> GPIO 4
  Servo 2 (Joint 1) -> GPIO 22
  Servo 3 (Joint 2) -> GPIO 23

  Buttons (active-low, internal pull-up):
    BTN_J1   -> GPIO 12  (select Base)
    BTN_J2   -> GPIO 13  (select Joint 1)
    BTN_J3   -> GPIO 27  (select Joint 2)
    BTN_UP   -> GPIO 25  (hold to keep moving joint +)
    BTN_DOWN -> GPIO 18  (hold to keep moving joint -)
"""

from machine import Pin, PWM
import utime


# -----------------------------------------
#  SERVO HELPER
# -----------------------------------------

class Servo:
    def __init__(self, pin_num, min_us=500, max_us=2500, freq=50):
        self.pwm = PWM(Pin(pin_num), freq=freq)
        self.min_us = min_us
        self.max_us = max_us
        self.freq = freq
        self._angle = 90
        self.write(90)

    def write(self, angle):
        angle = max(0, min(180, angle))
        self._angle = angle
        pulse_us = self.min_us + (self.max_us - self.min_us) * angle / 180
        period_us = 1_000_000 / self.freq
        duty = int(1023 * pulse_us / period_us)
        self.pwm.duty(duty)

    @property
    def angle(self):
        return self._angle


# -----------------------------------------
#  BUTTON HELPER
# -----------------------------------------

class Button:
    DEBOUNCE_MS = 50

    def __init__(self, pin_num):
        self.pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        self._last_state = 1
        self._last_time = 0

    def pressed(self):
        """Returns True once per physical press (falling edge, debounced)."""
        now = utime.ticks_ms()
        state = self.pin.value()
        if state == 0 and self._last_state == 1:
            if utime.ticks_diff(now, self._last_time) > self.DEBOUNCE_MS:
                self._last_state = 0
                self._last_time = now
                return True
        if state == 1:
            self._last_state = 1
        return False

    def held(self):
        """Returns True every loop iteration while the button is held down."""
        return self.pin.value() == 0


# -----------------------------------------
#  CONFIGURATION
# -----------------------------------------

STEP         = 5      # degrees moved per interval while held
HOLD_DELAY   = 20     # ms between each step while button is held
MIN_ANGLE    = 0
MAX_ANGLE    = 180


# -----------------------------------------
#  SETUP
# -----------------------------------------

servo_base   = Servo(4)
servo_joint1 = Servo(22)
servo_joint2 = Servo(23)

servos      = [servo_base, servo_joint1, servo_joint2]
joint_names = ["Base", "Joint 1", "Joint 2"]

btn_j1   = Button(12)
btn_j2   = Button(13)
btn_j3   = Button(27)
btn_up   = Button(25)
btn_down = Button(18)

selected = None

print("Robotic Arm ready. Press J1 / J2 / J3 to select a servo.")


# -----------------------------------------
#  MAIN LOOP
# -----------------------------------------

while True:

    # -- Joint selection --
    if btn_j1.pressed():
        selected = 0
        print("\n[SELECT] Base  |  Angle: {} deg".format(servos[selected].angle))

    if btn_j2.pressed():
        selected = 1
        print("\n[SELECT] Joint 1  |  Angle: {} deg".format(servos[selected].angle))

    if btn_j3.pressed():
        selected = 2
        print("\n[SELECT] Joint 2  |  Angle: {} deg".format(servos[selected].angle))

    # -- Movement: keeps moving while button is held --
    if selected is not None:

        if btn_up.held():
            new_angle = min(servos[selected].angle + STEP, MAX_ANGLE)
            servos[selected].write(new_angle)
            print("[MOVE +] {}  ->  {} deg".format(joint_names[selected], new_angle))
            utime.sleep_ms(HOLD_DELAY)

        elif btn_down.held():
            new_angle = max(servos[selected].angle - STEP, MIN_ANGLE)
            servos[selected].write(new_angle)
            print("[MOVE -] {}  ->  {} deg".format(joint_names[selected], new_angle))
            utime.sleep_ms(HOLD_DELAY)

    utime.sleep_ms(10)