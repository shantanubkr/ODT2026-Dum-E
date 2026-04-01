"""Application states — provisional names match docs/state_machine.md."""


class States:
    BOOT = "BOOT"
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    WORKING = "WORKING"
    ERROR = "ERROR"
    SLEEP = "SLEEP"


class StateMachine:
    def __init__(self, initial=States.BOOT):
        self.current_state = initial

    def change_state(self, new_state):
        self.current_state = new_state

    def get_state(self):
        return self.current_state
