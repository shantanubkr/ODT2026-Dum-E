"""Higher-level behaviors — skeletal hooks for idle / greeting / future traits."""


class BehaviorEngine:
    def __init__(self):
        pass

    def update(self, dt_ms):
        # TODO: periodic behavior tick
        pass

    def idle_behavior(self):
        # TODO: subtle motion or LED patterns when idle
        pass

    def greeting_behavior(self):
        # TODO: short acknowledge motion/sound
        pass
