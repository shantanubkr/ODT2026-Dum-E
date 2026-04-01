"""Safety policy and emergency stop coordination."""


class SafetyManager:
    def __init__(self):
        self.emergency_stop = False

    def trigger_emergency_stop(self):
        self.emergency_stop = True

    def reset_emergency_stop(self):
        self.emergency_stop = False

    def can_move(self):
        return not self.emergency_stop
