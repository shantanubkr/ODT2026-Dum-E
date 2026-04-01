"""Buzzer — stub (active vs passive determines implementation)."""


class BuzzerDriver:
    def __init__(self, pin):
        self._pin = pin
        # TODO: Pin vs PWM depending on buzzer type

    def beep(self, duration_ms=100):
        # TODO: drive pin or PWM for duration_ms
        pass
