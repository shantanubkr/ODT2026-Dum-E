# DUM-E — who does what (after `dum_e_description` setup)

## Done in repo

- **`ros2_ws/src/dum_e_description/`** — ament CMake package with URDF/xacro + `meshes/` (STL filenames aligned with `dum-e.xacro`).
- All `$(find dum-e_description)` strings updated to **`dum_e_description`**.
- **`dum_hardware/urdf/dum-e.xacro`** updated the same way (kept in sync for reference).
- **`dum_hardware/README.md`** — points to the canonical package.

## Shantanu (software)

| Task | Status |
|------|--------|
| `colcon build` on Ubuntu/WSL with ROS 2 Humble | Run locally when you’re at the ROS machine |
| Add **`launch/`**: `robot_state_publisher` + joint source + optional RViz | Pending |
| Map **`JointState` names** (`Revolute 7`–`10` vs `waist` / firmware order) in `dum_e_controller` or a small bridge node | Pending |
| Fifth joint (`end_effector`) in firmware only — publish a constant or extra angle in `/joint_states` if the dashboard needs 5 | Optional |
| Update / test **`dum_e_state_manager`** against 4 joint names from URDF | Pending |
| Gazebo: **`dum-e.trans`** is ROS 1 style — replace with **ros2_control** when you simulate | Future |

## Avyukt (hardware)

| Task | Status |
|------|--------|
| Deliver final STLs / xacro | **Done** — geometry copied into `dum_e_description/meshes/` |
| If CAD changes later | Re-export meshes + xacro and hand off a zip; we merge into `dum_e_description` again |
| Wiring / power | Physical; not tracked in this doc |

## Quick build check (Shantanu)

```bash
cd ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select dum_e_description
source install/setup.bash
```

Then verify:

```bash
ros2 pkg prefix dum_e_description
```

If that prints a path under `install/`, meshes resolve for `xacro` + RViz.
