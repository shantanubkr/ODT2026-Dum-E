from utils.logger import log


class States:
    BOOT = "BOOT"
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    WORKING = "WORKING"
    ERROR = "ERROR"
    SLEEP = "SLEEP"


class StateMachine:
    def __init__(self):
        self.current_state = States.BOOT
        log("State machine initialized in BOOT")

    def get_state(self):
        return self.current_state

    def change_state(self, new_state):
        if new_state == self.current_state:
            return

        old_state = self.current_state
        self.current_state = new_state
        log("State changed: " + old_state + " -> " + new_state)

    def is_state(self, state):
        return self.current_state == state

    def reset(self):
        self.current_state = States.BOOT
        log("State machine reset to BOOT")
