"""PCA9685 16-channel PWM driver (I2C) for hobby servos at ~50 Hz."""

import time


class PCA9685:
    MODE1 = 0x00
    PRESCALE = 0xFE
    LED0_ON_L = 0x06

    def __init__(self, i2c, addr=0x40):
        self.i2c = i2c
        self.addr = addr
        self.i2c.writeto_mem(self.addr, self.MODE1, b"\x00")
        self.set_pwm_freq(50)

    def set_pwm_freq(self, hz):
        hz = max(40, min(1000, int(hz)))
        prescale = int(round(25_000_000.0 / (4096.0 * hz)) - 1)
        prescale = max(3, min(255, prescale))
        oldmode = self.i2c.readfrom_mem(self.addr, self.MODE1, 1)[0]
        newmode = (oldmode & 0x7F) | 0x10
        self.i2c.writeto_mem(self.addr, self.MODE1, bytes([newmode]))
        self.i2c.writeto_mem(self.addr, self.PRESCALE, bytes([prescale]))
        self.i2c.writeto_mem(self.addr, self.MODE1, bytes([oldmode]))
        time.sleep_ms(5)
        self.i2c.writeto_mem(self.addr, self.MODE1, bytes([oldmode | 0x80]))

    def set_pwm(self, channel, on, off):
        if not 0 <= channel <= 15:
            raise ValueError("channel must be 0..15")
        on = int(on) & 0xFFFF
        off = int(off) & 0xFFFF
        reg = self.LED0_ON_L + 4 * channel
        buf = bytes([on & 0xFF, (on >> 8) & 0x0F, off & 0xFF, (off >> 8) & 0x0F])
        self.i2c.writeto_mem(self.addr, reg, buf)

    def set_servo_pulse_us(self, channel, pulse_us, period_us=20_000):
        # Same mapping as 500 + (angle/180)*2000 µs at 50 Hz when span is 500–2500.
        pulse_us = max(0, min(float(pulse_us), float(period_us)))
        off = int(pulse_us / float(period_us) * 4096.0)
        off = max(0, min(4095, off))
        self.set_pwm(channel, 0, off)
