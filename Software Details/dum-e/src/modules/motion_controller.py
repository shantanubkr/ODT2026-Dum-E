from drivers.stepper import Servo

from utils.logger import log

from utils.timers import current_millis


class MotionController:
    def __init__(self):
        self.servos = [
            Servo(4),   # base
            Servo(22),  # shoulder
            Servo(23),  # elbow
        ]
        self.joint_names = ["Base", "Shoulder", "Elbow"]
        self.current_angles = [90, 90, 90]
        self.target_angles = [90, 90, 90]
        self.poses = {
            "home": [90, 90, 90],
            "ready": [90, 60, 120],
            "down": [90, 120, 140],
        }
        self.selected_joint = None
        log("Motion controller initialized")

    def select_joint(self, joint_id):
        self.selected_joint = joint_id
        log("Selected joint: " + self.joint_names[joint_id])

    def nudge_joint(self, direction, step=5):
        if self.selected_joint is None:
            return
        idx = self.selected_joint
        new_angle = self.current_angles[idx] + (step * direction)
        new_angle = max(0, min(180, new_angle))
        self.current_angles[idx] = new_angle
        self.target_angles[idx] = new_angle
        self.servos[idx].write(new_angle)
        log("[NUDGE] " + self.joint_names[idx] + " -> " + str(new_angle))

    def move_to_pose(self, angles):
        if len(angles) != 3:
            return
        self.target_angles = angles
        log("Moving to pose: " + str(angles))

    def move_to_named_pose(self, name):
        if name not in self.poses:
            log("Unknown pose: " + str(name))
            return
        angles = self.poses[name]
        log("Moving to named pose: " + name)
        self.move_to_pose(angles)

    def update(self):
        for i in range(3):
            current = self.current_angles[i]
            target = self.target_angles[i]
            if current == target:
                continue
            if current < target:
                current += 1
            else:
                current -= 1
            self.current_angles[i] = current
            self.servos[i].write(current)

    def get_pose(self):
        return self.current_angles
