"""VL53L0X time-of-flight — stub until I2C init and driver are added."""


class VL53L0XDriver:
    """Placeholder for VL53L0X distance readings (mm)."""

    def __init__(self, i2c, address=0x29):
        self._i2c = i2c
        self._address = address
        # TODO: init sensor, configure range profile

    def read_mm(self):
        # TODO: I2C read / library call
        return None
