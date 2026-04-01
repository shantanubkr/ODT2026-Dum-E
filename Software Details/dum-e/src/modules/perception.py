"""Sensor fusion and world model — placeholders only.

Future: combine ESP32-CAM output, VL53L0X / HC-SR04 distances, and object /
obstacle awareness. No fusion logic yet.
"""


class Perception:
    def __init__(self):
        pass

    def update(self):
        # TODO: poll drivers, merge readings
        pass

    def nearest_obstacle_cm(self):
        # TODO: min of ToF / ultrasonic / future sources
        return None
