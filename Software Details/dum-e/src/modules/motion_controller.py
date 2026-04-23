from drivers.servo import Servo

from utils.logger import log

from config import (
    BOOT_MOTION_FROM_DEG,
    JOINT_ANGLE_MAX_DEG,
    JOINT_ANGLE_MIN_DEG,
    JOINT_HOME_ANGLES,
    MOTION_DEADZONE_DEG,
    MOTION_SMOOTHING,
    NUM_JOINTS,
    SERVO_PWM_MAX_US,
    SERVO_PWM_MIN_US,
    UPRIGHT_POSE_DEG,
    USE_BOOT_MOTION_SMOOTH,
    USE_PCA9685,
)

from pins import (
    PCA9685_ADDR,
    PCA9685_CH_FOREARM,
    PCA9685_CH_HAND,
    PCA9685_CH_UPPER_ARM,
    PCA9685_CH_WAIST,
    PCA9685_I2C_ID,
    PCA9685_SCL,
    PCA9685_SDA,
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
    """Four-DOF arm. Joint order: waist, upper_arm, forearm, hand."""

    def __init__(self):
        self.servos = []
        if USE_PCA9685:
            from machine import I2C, Pin

            from drivers.pca9685 import PCA9685

            _i2c = I2C(
                PCA9685_I2C_ID,
                scl=Pin(PCA9685_SCL),
                sda=Pin(PCA9685_SDA),
                freq=400_000,
            )
            _pca = PCA9685(_i2c, PCA9685_ADDR)
            pca_channels = [
                PCA9685_CH_WAIST,
                PCA9685_CH_UPPER_ARM,
                PCA9685_CH_FOREARM,
                PCA9685_CH_HAND,
            ]
            for i in range(NUM_JOINTS):
                self.servos.append(
                    Servo(
                        pca9685=_pca,
                        channel=pca_channels[i],
                        min_us=SERVO_PWM_MIN_US[i],
                        max_us=SERVO_PWM_MAX_US[i],
                    )
                )
        else:
            pins = [
                SERVO_WAIST,
                SERVO_UPPER_ARM,
                SERVO_FOREARM,
                SERVO_HAND,
            ]
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
        ]
        home = [self._clamp_joint(i, a) for i, a in enumerate(JOINT_HOME_ANGLES)]
        if USE_BOOT_MOTION_SMOOTH and len(BOOT_MOTION_FROM_DEG) == NUM_JOINTS:
            self.current_angles = [self._clamp_joint(i, BOOT_MOTION_FROM_DEG[i]) for i in range(NUM_JOINTS)]
        else:
            self.current_angles = list(home)
        self.target_angles = list(home)
        self._smooth = float(MOTION_SMOOTHING)
        self._deadzone = float(MOTION_DEADZONE_DEG)
        self.poses = {}
        for name in NAMED_POSE_KEYS:
            if firmware_deg_for_named_pose is not None:
                raw = firmware_deg_for_named_pose(name)
            elif name == "home":
                raw = list(UPRIGHT_POSE_DEG)
            elif name == "ready":
                u = UPRIGHT_POSE_DEG
                raw = [u[0], 60, 120, u[3]]
            else:
                u = UPRIGHT_POSE_DEG
                raw = [u[0], 120, 140, u[3]]
            self.poses[name] = [self._clamp_joint(i, raw[i]) for i in range(NUM_JOINTS)]
        self.selected_joint = None
        for i in range(NUM_JOINTS):
            self.servos[i].write(self.current_angles[i])
        log("Motion controller initialized (smooth k=" + str(self._smooth) + " deadzone=" + str(self._deadzone) + "°)")

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
        k = self._smooth
        dz = self._deadzone
        for i in range(NUM_JOINTS):
            c = float(self.current_angles[i])
            t = float(self.target_angles[i])
            err = t - c
            if abs(err) <= dz:
                if abs(c - t) > 1e-6:
                    c = t
                    self.current_angles[i] = c
                    self.servos[i].write(c)
                continue
            c = c + err * k
            if abs(t - c) <= dz:
                c = t
            c = self._clamp_joint(i, c)
            self.current_angles[i] = c
            self.servos[i].write(c)

    def is_at_target(self):
        """True when every joint has reached its commanded target (for STOP cooldown / recovery)."""
        dz = self._deadzone
        for i in range(NUM_JOINTS):
            if abs(float(self.current_angles[i]) - float(self.target_angles[i])) > dz:
                return False
        return True

    def get_pose(self):
        return self.current_angles
