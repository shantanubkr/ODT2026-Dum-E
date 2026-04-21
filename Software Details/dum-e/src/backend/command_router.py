from backend.command_schema import Actions, Command

from modules.state_machine import States

from utils.logger import log


class CommandRouter:
    def __init__(
        self,
        motion_controller,
        state_machine,
        safety_manager=None,
        behavior_engine=None,
        status_provider=None,
        history_provider=None,
    ):
        self.motion_controller = motion_controller
        self.state_machine = state_machine
        self.safety_manager = safety_manager
        self.behavior_engine = behavior_engine
        self.status_provider = status_provider
        self.history_provider = history_provider

        log("Command Router initialized")

    def _maybe_exit_sad_mood(self, action):
        """Any substantive command leaves SAD (status/history are passive)."""
        if action in (Actions.STATUS, Actions.HISTORY):
            return
        if not self.state_machine.is_state(States.SAD):
            return
        self.state_machine.change_state(States.ACTIVE)
        if self.behavior_engine is not None:
            b = self.behavior_engine.get_behavior()
            if b in ("express_sad", "sad_hold"):
                self.behavior_engine.set_behavior("idle")

    def _can_move(self):
        if self.safety_manager is None:
            return True
        return self.safety_manager.can_move()

    def route(self, command):
        action = command.action
        log("Routing command: " + str(command.to_dict()))

        self._maybe_exit_sad_mood(action)

        if action == Actions.MOVE_HOME:
            if not self._can_move():
                log("Movement blocked by safety manager")
                return
            self.motion_controller.move_to_named_pose("home")
            return

        if action == Actions.STATUS:
            if self.status_provider is not None:
                log("Status report: " + str(self.status_provider()))
            else:
                log("Status requested")
            return

        if action == Actions.HISTORY:
            if self.history_provider is not None:
                log("Command history: " + str(self.history_provider()))
            else:
                log("Command history: (no provider)")
            return

        if action == Actions.STOP:
            log("STOP command received")
            if self.safety_manager is not None:
                self.safety_manager.trigger_emergency_stop()
            self.state_machine.change_state(States.ERROR)
            if self.behavior_engine is not None:
                self.behavior_engine.set_behavior("none")
                self.behavior_engine.cancel_idle_inspect()
            return

        if action == Actions.RESET:
            log("RESET command received")
            if self.safety_manager is not None:
                self.safety_manager.reset_emergency_stop()
            self.state_machine.change_state(States.ACTIVE)
            if self.behavior_engine is not None:
                self.behavior_engine.set_behavior("idle")
            self.motion_controller.move_to_named_pose("home")
            return

        if action == Actions.PICK_OBJECT:
            log("Pick object requested: " + str(command.target))
            if not self._can_move():
                log("Movement blocked by safety manager")
                return
            self.motion_controller.move_to_named_pose("ready")
            return

        if action == Actions.PLACE_OBJECT:
            log("Place object requested: " + str(command.target))
            if not self._can_move():
                log("Movement blocked by safety manager")
                return
            self.motion_controller.move_to_named_pose("down")
            return

        if action == Actions.MOVE_TO:
            pose = (command.metadata or {}).get("pose")
            if pose is not None:
                if not self._can_move():
                    log("Movement blocked by safety manager")
                    return
                self.motion_controller.move_to_named_pose(pose)
                return
            if not self._can_move():
                log("Movement blocked by safety manager")
                return
            self.state_machine.change_state(States.WORKING)
            if self.behavior_engine is not None:
                self.behavior_engine.set_behavior("thinking")
            log("MOVE_TO (trajectory TBD): " + str(command.target or command.location))
            return

        if action == Actions.GREET:
            self.state_machine.change_state(States.ACTIVE)
            if self.behavior_engine is not None:
                self.behavior_engine.set_behavior("greeting")
            return

        if action == Actions.DANCE:
            if not self._can_move():
                log("DANCE blocked by safety manager")
                return
            self.state_machine.change_state(States.ACTIVE)
            if self.behavior_engine is not None:
                self.behavior_engine.set_behavior("dancing")
            return

        if action == Actions.IDLE_LOOK_AT:
            if not self._can_move():
                log("IDLE_LOOK_AT blocked by safety manager")
                return
            if self.behavior_engine is None:
                return
            if self.behavior_engine.get_behavior() != "idle":
                log("IDLE_LOOK_AT ignored (behavior is not idle)")
                return
            md = command.metadata or {}
            w = md.get("waist")
            h = md.get("hand")
            if w is None or h is None:
                log("IDLE_LOOK_AT missing waist/hand in metadata")
                return
            self.behavior_engine.begin_idle_inspect(float(w), float(h))
            return

        log("Unhandled command: " + str(action))


def build_command_from_parse_result(result, source="debug"):
    """Map CommandParser dict → schema Command. Returns None if caller should handle separately (e.g. history)."""
    command_type = result.get("type")
    word = result.get("command")

    if command_type == "known":
        if word == "history":
            return Command(Actions.HISTORY, source=source)
        if word == "home":
            return Command(Actions.MOVE_HOME, source=source)
        if word == "ready":
            return Command(Actions.MOVE_TO, metadata={"pose": "ready"}, source=source)
        if word == "down":
            return Command(Actions.MOVE_TO, metadata={"pose": "down"}, source=source)
        if word == "pick":
            return Command(Actions.PICK_OBJECT, target=None, source=source)
        if word == "drop":
            return Command(Actions.PLACE_OBJECT, target=None, source=source)
        if word == "stop":
            return Command(Actions.STOP, source=source)
        if word == "hello":
            return Command(Actions.GREET, source=source)
        if word == "status":
            return Command(Actions.STATUS, source=source)
        if word == "reset":
            return Command(Actions.RESET, source=source)
        if word == "dance":
            return Command(Actions.DANCE, source=source)

    if command_type == "move":
        args = result.get("args") or []
        direction = args[0] if len(args) >= 1 else None
        return Command(Actions.MOVE_TO, target=direction, source=source)

    return None
