# Logical joint poses (waist, upper_arm, forearm, hand) in radians.
# Aligned with firmware `robot_kinematics.NAMED_LOGICAL_RAD` and URDF joint limits.

import math

LOGICAL_IDLE = [0.0, 0.5, 1.0, 0.0]
LOGICAL_READY = [0.0, 0.55, 1.05, 0.0]
LOGICAL_DOWN = [0.0, 0.35, 0.75, 0.0]
LOGICAL_REACH = [0.0, 0.52, 1.0, 0.0]
LOGICAL_ERROR = [0.0, 0.2, 0.5, 0.0]
