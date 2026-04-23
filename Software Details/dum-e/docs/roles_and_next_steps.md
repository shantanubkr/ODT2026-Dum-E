# DUM-E — repo map & follow-ups

## In repo today

| Area | Contents |
|------|----------|
| **`ros2_ws/src/dum_e_description/`** | ROS 2 package: URDF/xacro, meshes, **`launch/view_robot.launch.py`** (`robot_state_publisher` + joint GUI + RViz — see package README). |
| **`ros2_ws/src/dum_e_vision/`** | **`vision_node`**: Gazebo **`Image`** or real **HTTP MJPEG** → **`/dume/target_coord`** (`Point`: x,y,z=area). See package **README**. |
| **`src/`** | ESP32 MicroPython firmware: servos, parser, router, behaviors, safety. |
| **`desktop_app/`** | Dashboard + CPython runtime bridging **`CommandRouter`** and optional **`RobotBridge`** (ROS 2). |

## ROS / simulation follow-ups (software)

| Task | Notes |
|------|--------|
| Joint name mapping | URDF uses names like **`Revolute 7`–`10`**; firmware uses **`waist`**, **`upper_arm`**, etc. Bridge or rename in **`dum_e_controller`** / RViz as needed. |
| `/joint_states` vs firmware | **`dum_e_state_manager`** publishes four URDF joints; names map from logical waist/upper/forearm/hand (see package). |
| **`dum_e_state_manager`** | Align with live topic names and **`dum_e_description`** after testing on a ROS machine. |
| Gazebo / **ros2_control** | **`dum-e.trans`** is legacy-style; replace when you add proper simulation. |

## Hardware / CAD (coordination)

| Task | Notes |
|------|--------|
| STLs / meshes | **Done** in **`dum_e_description/meshes/`** per current CAD. |
| Future CAD changes | Re-export meshes + xacro and merge into **`dum_e_description`**. |
| Wiring / power | Physical; tracked in **`docs/hardware.md`**. |

## Quick build check (ROS 2 Humble)

```bash
cd ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select dum_e_description
source install/setup.bash
ros2 pkg prefix dum_e_description
```

Optional visualization:

```bash
source install/setup.bash
ros2 launch dum_e_description view_robot.launch.py
```

Do **not** run that launch at the same time as another node that also publishes **`/joint_states`** unless you intend to (see **`dum_e_description/README.md`**).
