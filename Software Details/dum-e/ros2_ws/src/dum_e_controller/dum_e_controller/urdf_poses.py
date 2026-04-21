# Logical joint poses (waist, upper_arm, forearm, hand, end_effector) in radians.
# Keep in sync with dum-e/src/robot_kinematics.py NAMED_LOGICAL_RAD and viz helpers.

import math

_EE = math.pi / 2  # gripper logical mid — matches firmware 90° (0..pi → 0..180°)

LOGICAL_IDLE = [0.0, 0.5, 1.0, 0.0, _EE]
LOGICAL_READY = [0.0, 0.55, 1.05, 0.0, _EE]
LOGICAL_DOWN = [0.0, 0.35, 0.75, 0.0, _EE]
LOGICAL_REACH = [0.0, 0.52, 1.0, 0.0, _EE]
LOGICAL_ERROR = [0.0, 0.2, 0.5, 0.0, _EE]
