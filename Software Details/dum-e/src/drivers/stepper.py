"""DRV8825 / step-dir stepper driver — API placeholder until pins and timing are tuned."""


class StepperDriver:
    """Minimal stepper interface; wire to GPIO and pulse timing later."""

    def __init__(self, name, step_pin, dir_pin, enable_pin):
        self._name = name
        self._step_pin = step_pin
        self._dir_pin = dir_pin
        self._enable_pin = enable_pin
        # TODO: configure Pin objects, enable polarity, microstep mode via hardware

    def enable(self):
        # TODO: drive ENABLE pin
        pass

    def disable(self):
        # TODO: drive ENABLE pin
        pass

    def set_direction(self, forward=True):
        # TODO: set DIR line
        pass

    def step(self):
        # TODO: pulse STEP; tune delay for driver/motor combo
        pass

    def move_steps(self, count, forward=True):
        # TODO: loop step() with acceleration limits if needed
        self.set_direction(forward)
        for _ in range(abs(count)):
            self.step()
