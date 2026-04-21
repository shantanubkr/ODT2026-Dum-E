from machine import Pin, PWM


class Servo:
    """PWM hobby servo. Calibrate min_us / max_us per joint in config."""

    def __init__(self, pin_num, min_us=500, max_us=2500, freq=50):
        self.pwm = PWM(Pin(pin_num), freq=freq)
        self.min_us = min_us
        self.max_us = max_us
        self.freq = freq
        self._angle = 90
        self.write(90)

    def write(self, angle):
        angle = max(0.0, min(180.0, float(angle)))
        self._angle = angle
        pulse_us = self.min_us + (self.max_us - self.min_us) * angle / 180.0
        period_us = 1_000_000 / self.freq
        duty = int(1023 * pulse_us / period_us)
        self.pwm.duty(duty)

    @property
    def angle(self):
        return self._angle
