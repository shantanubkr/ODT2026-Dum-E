# URDF-aligned joint mapping for dum-e (dum_e_description/urdf/dum-e.xacro).
#
# Logical order matches firmware MotionController:
#   waist, upper_arm, forearm, hand
# URDF Revolute mapping (see dum_e_state_manager._logical_to_urdf):
#   Revolute 8 = waist, Revolute 7 = upper_arm, Revolute 10 = forearm,
#   Revolute 9 = hand
#
# Servo "degrees" are 0..180 linear maps of each joint's URDF lower..upper (radians).
#
# UPRIGHT_FIRMWARE_DEG — single mechanical reference: on the built arm, commanding
# these values is the stacked / neutral upright pose (home). Named poses and ROS
# logical radians derive from this via firmware_pose_deg_to_logical_rad.

import math

# Calibrated home / scan default — matches hardware bring-up and config defaults.
UPRIGHT_FIRMWARE_DEG = [110, 110, 115, 105]

# (lower_rad, upper_rad) per logical joint — from dum-e.xacro limits
_URDF_LIMITS_RAD = [
    (-1.570796, 1.570796),   # Revolute 8 waist
    (-0.785398, 1.570796),   # Revolute 7 upper_arm
    (-1.570796, 1.570796),   # Revolute 10 forearm
    (-1.570796, 1.570796),   # Revolute 9 hand
]


def logical_rad_to_firmware_deg(angle_rad, joint_idx):
    lo, hi = _URDF_LIMITS_RAD[joint_idx]
    r = float(angle_rad)
    if r < lo:
        r = lo
    elif r > hi:
        r = hi
    span = hi - lo
    if span <= 0:
        return 90
    return int(round((r - lo) / span * 180.0))


def logical_pose_rad_to_firmware_deg(logical_rad):
    """Tuple/list waist..hand in radians → ints 0..180."""
    return [logical_rad_to_firmware_deg(logical_rad[i], i) for i in range(4)]


def firmware_deg_to_logical_rad(deg, joint_idx):
    lo, hi = _URDF_LIMITS_RAD[joint_idx]
    span = hi - lo
    d = float(deg)
    if d < 0:
        d = 0.0
    elif d > 180:
        d = 180.0
    return lo + (d / 180.0) * span


def firmware_pose_deg_to_logical_rad(degs):
    return [firmware_deg_to_logical_rad(degs[i], i) for i in range(4)]


def neutral_logical_rad():
    """Logical rad pose for mechanical upright (UPRIGHT_FIRMWARE_DEG)."""
    return tuple(firmware_pose_deg_to_logical_rad(UPRIGHT_FIRMWARE_DEG))


def neutral_pose_firmware_deg():
    return list(UPRIGHT_FIRMWARE_DEG)


# Named poses: logical radians (same convention as ROS dum_e_state_manager _publish_logical).
# Tuned to match previous RViz poses; values are clamped by logical_rad_to_firmware_deg.

NAMED_LOGICAL_RAD = {
    "home": neutral_logical_rad(),
    "idle": (0.0, 0.5, 1.0, 0.0),
    "ready": (0.0, 0.55, 1.05, 0.0),
    "down": (0.0, 0.35, 0.75, 0.0),
    "reach": (0.0, 0.52, 1.0, 0.0),
    "error": (0.0, 0.2, 0.5, 0.0),
}

NAMED_POSE_KEYS = ("home", "ready", "down")


def firmware_deg_for_named_pose(name):
    if name not in NAMED_LOGICAL_RAD:
        return list(neutral_pose_firmware_deg())
    return logical_pose_rad_to_firmware_deg(NAMED_LOGICAL_RAD[name])


# Sad slouch: legacy calibrated degrees → URDF-consistent logical pose (waist at upright).
_SAD_LEGACY_DEG = [
    UPRIGHT_FIRMWARE_DEG[0],
    28,
    118,
    72,
]
SAD_SLOUCH_LOGICAL_RAD = tuple(firmware_pose_deg_to_logical_rad(_SAD_LEGACY_DEG))


def sad_slouch_firmware_deg():
    return logical_pose_rad_to_firmware_deg(SAD_SLOUCH_LOGICAL_RAD)


def express_present_firmware_deg():
    """Presentation pose — URDF-consistent mapping from legacy degree targets."""
    u = UPRIGHT_FIRMWARE_DEG
    return logical_pose_rad_to_firmware_deg(
        firmware_pose_deg_to_logical_rad([u[0], 45.0, 0.0, u[3]])
    )
