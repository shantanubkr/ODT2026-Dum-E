"""Debounced GPIO buttons for optional panel wiring (not used in default build)."""

from machine import Pin
import utime


class Button:
    DEBOUNCE_MS = 50

    def __init__(self, pin_num):
        self.pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        self._last_state = 1
        self._last_time = 0

    def pressed(self):
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
        return self.pin.value() == 0
