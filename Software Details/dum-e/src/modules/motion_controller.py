# Future: joint / stepper orchestration — home, move_to, stop; inject real drivers later.

"""Coordinates stepper drivers into arm motion — skeleton only."""


class MotionController:
    """High-level motion; inject real `StepperDriver` instances when wiring."""

    def __init__(self, steppers):
        self._steppers = steppers  # e.g. list or dict of StepperDriver instances per joint
        # TODO: kinematics / joint limits — enforce before move_to

    def home(self):
        """Seek endstops or timed home sequence — not implemented."""
        # TODO: iterate steppers / read limit pins / backoff
        pass  # Placeholder until hardware path exists

    def move_to(self, target):
        """Interpret target (angles, steps, named pose) — not implemented."""
        # TODO: map target to per-motor step counts; respect SafetyManager externally
        pass  # Placeholder for planner + executor

    def stop(self):
        """Halt all motors quickly and safely — not implemented."""
        # TODO: disable drivers or decelerate profile
        pass  # Placeholder for e-stop integration
