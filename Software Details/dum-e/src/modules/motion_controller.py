"""Coordinates stepper drivers into arm motion — skeleton only."""


class MotionController:
    """High-level motion; inject real `StepperDriver` instances when wiring."""

    def __init__(self, steppers):
        self._steppers = steppers  # e.g. list or dict of StepperDriver
        # TODO: kinematics / joint limits

    def home(self):
        # TODO: seek endstops or timed home sequence
        pass

    def move_to(self, target):
        # TODO: interpret target (joint angles, steps, named pose)
        pass

    def stop(self):
        # TODO: halt all steppers cleanly
        pass
