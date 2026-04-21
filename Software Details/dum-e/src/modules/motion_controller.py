from drivers.stepper import Servo

from utils.logger import log

from config import (
    JOINT_ANGLE_MAX_DEG,
    JOINT_ANGLE_MIN_DEG,
    JOINT_HOME_ANGLES,
    MOTION_STEP_DEG_PER_TICK,
    NUM_JOINTS,
    SERVO_PWM_MAX_US,
    SERVO_PWM_MIN_US,
)

from pins import (
    SERVO_END_EFFECTOR,
    SERVO_FOREARM,
    SERVO_HAND,
    SERVO_UPPER_ARM,
    SERVO_WAIST,
)

try:
    from robot_kinematics import firmware_deg_for_named_pose, NAMED_POSE_KEYS
except ImportError:
    firmware_deg_for_named_pose = None
    NAMED_POSE_KEYS = ("home", "ready", "down")


class MotionController:
    """Five-DOF arm + gripper. Joint order: waist, upper_arm, forearm, hand, end_effector."""

    def __init__(self):
        pins = [
            SERVO_WAIST,
            SERVO_UPPER_ARM,
            SERVO_FOREARM,
            SERVO_HAND,
            SERVO_END_EFFECTOR,
        ]
        self.servos = []
        for i in range(NUM_JOINTS):
            self.servos.append(
                Servo(
                    pins[i],
                    min_us=SERVO_PWM_MIN_US[i],
                    max_us=SERVO_PWM_MAX_US[i],
                )
            )
        self.joint_names = [
            "waist",
            "upper_arm",
            "forearm",
            "hand",
            "end_effector",
        ]
        self.current_angles = [self._clamp_joint(i, a) for i, a in enumerate(JOINT_HOME_ANGLES)]
        self.target_angles = list(self.current_angles)
        self.poses = {}
        for name in NAMED_POSE_KEYS:
            if firmware_deg_for_named_pose is not None:
                raw = firmware_deg_for_named_pose(name)
            elif name == "home":
                raw = list(JOINT_HOME_ANGLES)
            elif name == "ready":
                raw = [90, 60, 120, 90, 90]
            else:
                raw = [90, 120, 140, 90, 90]
            self.poses[name] = [self._clamp_joint(i, raw[i]) for i in range(NUM_JOINTS)]
        self.selected_joint = None
        self._step = max(1, int(MOTION_STEP_DEG_PER_TICK))
        log("Motion controller initialized")

    def _clamp_joint(self, joint_idx, angle):
        lo = JOINT_ANGLE_MIN_DEG[joint_idx]
        hi = JOINT_ANGLE_MAX_DEG[joint_idx]
        a = float(angle)
        if a < lo:
            return lo
        if a > hi:
            return hi
        return a

    def select_joint(self, joint_id):
        if joint_id < 0 or joint_id >= NUM_JOINTS:
            log("Invalid joint_id: " + str(joint_id))
            return
        self.selected_joint = joint_id
        log("Selected joint: " + self.joint_names[joint_id])

    def nudge_joint(self, direction, step=5):
        if self.selected_joint is None:
            return
        idx = self.selected_joint
        new_angle = self.current_angles[idx] + (step * direction)
        new_angle = self._clamp_joint(idx, new_angle)
        self.current_angles[idx] = new_angle
        self.target_angles[idx] = new_angle
        self.servos[idx].write(new_angle)
        log("[NUDGE] " + self.joint_names[idx] + " -> " + str(new_angle))

    def move_to_pose(self, angles):
        if len(angles) != NUM_JOINTS:
            return
        self.target_angles = [self._clamp_joint(i, angles[i]) for i in range(NUM_JOINTS)]
        log("Moving to pose: " + str(self.target_angles))

    def move_to_named_pose(self, name):
        if name not in self.poses:
            log("Unknown pose: " + str(name))
            return
        angles = self.poses[name]
        log("Moving to named pose: " + name)
        self.move_to_pose(angles)

    def update(self):
        step = self._step
        for i in range(NUM_JOINTS):
            current = self.current_angles[i]
            target = self.target_angles[i]
            if current == target:
                continue
            if current < target:
                current = min(current + step, target)
            else:
                current = max(current - step, target)
            current = self._clamp_joint(i, current)
            self.current_angles[i] = current
            self.servos[i].write(current)

    def get_pose(self):
        return self.current_angles
