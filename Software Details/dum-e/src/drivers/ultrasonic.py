"""HC-SR04 ultrasonic — stub until TRIG/ECHO timing is implemented."""


class UltrasonicDriver:
    def __init__(self, trig_pin, echo_pin):
        self._trig_pin = trig_pin
        self._echo_pin = echo_pin
        # TODO: configure pins

    def read_distance_cm(self):
        # TODO: pulse TRIG, measure ECHO width, convert to cm
        return None
