from machine import Pin, PWM


class Servo:
    """PWM hobby servo. Calibrate min_us / max_us per joint in config.

    Either drive a GPIO with :class:`PWM`, or a :class:`PCA9685` channel (I2C).

    ESP32 LEDC: prefer duty_u16 (high-time as fraction of period); then duty_ns;
    last resort duty(0..1023). PWM is created with freq set after init — more reliable
    than passing freq= in the constructor on some MicroPython builds.
    """

    def __init__(
        self,
        pin_num=None,
        min_us=500,
        max_us=2500,
        freq=50,
        pca9685=None,
        channel=None,
    ):
        self.min_us = int(min_us)
        self.max_us = int(max_us)
        self.freq = int(freq)
        self._angle = 90.0
        self._pca = pca9685
        self._ch = int(channel) if channel is not None else None
        self.pwm = None
        if self._pca is not None:
            if self._ch is None:
                raise ValueError("Servo: channel is required when using pca9685")
        else:
            if pin_num is None:
                raise ValueError("Servo: pin_num is required without pca9685")
            self.pwm = PWM(Pin(int(pin_num)))
            self.pwm.freq(self.freq)
        self.write(90.0)

    def write(self, angle):
        angle = max(0.0, min(180.0, float(angle)))
        self._angle = angle
        pulse_us = float(
            self.min_us + (self.max_us - self.min_us) * angle / 180.0
        )
        period_us = 1_000_000.0 / float(self.freq)

        if self._pca is not None:
            self._pca.set_servo_pulse_us(self._ch, pulse_us, period_us)
            return

        pwm = self.pwm

        # 1) duty_u16: ratio = pulse_width / period → value / 65535 (ESP32 quickref).
        if hasattr(pwm, "duty_u16"):
            try:
                ratio = pulse_us / period_us
                d = int(max(0, min(65535, round(ratio * 65535))))
                pwm.duty_u16(d)
                return
            except Exception:
                pass

        # 2) duty_ns: pulse high time in ns.
        if hasattr(pwm, "duty_ns"):
            try:
                pulse_ns = int(round(pulse_us * 1000.0))
                max_ns = int(1_000_000_000 // max(1, self.freq))
                pulse_ns = max(0, min(max_ns, pulse_ns))
                pwm.duty_ns(pulse_ns)
                return
            except Exception:
                pass

        # 3) Legacy 10-bit duty (often inaccurate for servos on ESP32).
        duty = int(max(0, min(1023, round(1023 * pulse_us / period_us))))
        pwm.duty(duty)

    @property
    def angle(self):
        return self._angle
