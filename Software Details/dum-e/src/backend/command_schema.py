class Actions:
    PICK_OBJECT = "pick_object"
    PLACE_OBJECT = "place_object"
    MOVE_HOME = "move_home"
    MOVE_TO = "move_to"
    STOP = "stop"
    RESET = "reset"
    STATUS = "status"
    HISTORY = "history"
    GREET = "greet"
    DANCE = "dance"
    IDLE_LOOK_AT = "idle_look_at"


class Command:
    def __init__(self, action, target=None, location=None, metadata=None, source="unknown"):
        self.action = action
        self.target = target
        self.location = location
        self.metadata = metadata or {}
        self.source = source

    def to_dict(self):
        return {
            "action": self.action,
            "target": self.target,
            "location": self.location,
            "metadata": self.metadata,
            "source": self.source,
        }
