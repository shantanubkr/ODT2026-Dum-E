# dum_e_description

ROS 2 Humble package: **URDF/xacro**, **meshes**, and Gazebo extras for DUM-E (4 revolute joints; matches firmware four-DOF arm).

## Contents

| Path | Purpose |
|------|---------|
| `urdf/dum-e.xacro` | Main robot (Revolute 7–10); includes materials, transmissions, Gazebo |
| `urdf/*.xacro` | Includes |
| `meshes/*.stl` | Visual/collision meshes (mm STLs, scale 0.001 in xacro) |

## Build

From repo root on Ubuntu / WSL2 (ROS 2 Humble sourced):

```bash
./scripts/build_ros.sh
```

Or from `ros2_ws/`:

```bash
source /opt/ros/humble/setup.bash
colcon build --packages-select dum_e_description
source install/setup.bash
```

## Visualize (`robot_state_publisher` + sliders + RViz)

Do **not** run this at the same time as `dum_e_state_manager` — both publish `/joint_states`.

```bash
source install/setup.bash
ros2 launch dum_e_description view_robot.launch.py
```

## Manual RViz (no launch file)

```bash
ros2 run xacro xacro $(ros2 pkg prefix dum_e_description)/share/dum_e_description/urdf/dum-e.xacro > /tmp/dum_e.urdf
ros2 run robot_state_publisher robot_state_publisher --ros-args -p robot_description:="$(cat /tmp/dum_e.urdf)"
```

## Joint ↔ mesh filenames

Meshes were renamed from informal CAD STL filenames to match the xacro:

- `Base.stl` → `base_link.stl`
- `Waist.stl` → `Waist_1.stl`
- `Upper_arm.stl` → `Upper_arm_1.stl`
- `Forearm.stl` → `Forearm_1.stl`
- `Hand.stl` → `Hand_1.stl`
- `end_effector.stl` — unused in current `dum-e.xacro` (reserved for a future tool)

## Note on ROS 1 transmissions

`dum-e.trans` uses ROS 1 `hardware_interface` names. For real Gazebo / ros2_control you’ll need to update or replace transmissions later.
