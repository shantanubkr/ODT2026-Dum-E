"""PIR motion sensor — stub."""


class PIRDriver:
    def __init__(self, pin):
        self._pin = pin
        # TODO: configure input, pull if needed

    def is_motion_detected(self):
        # TODO: read digital level
        return False
