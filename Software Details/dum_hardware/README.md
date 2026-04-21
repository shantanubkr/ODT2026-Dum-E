# DUM-E hardware assets

## Canonical ROS package (meshes + URDF for RViz)

The **maintained** copy used for `colcon build` lives here:

`../ros2_ws/src/dum_e_description/`

It contains:

- **`meshes/`** — STLs renamed to match the hardware xacro: `base_link.stl`, `Waist_1.stl`, `Upper_arm_1.stl`, `Forearm_1.stl`, `Hand_1.stl`, plus optional `end_effector.stl`.
- **`urdf/`** — `dum-e.xacro` and includes; uses `$(find dum_e_description)`.

The loose STLs in **this folder** (`Base.stl`, `Waist.stl`, …) are the **same geometry** as in the package; keep them if you want a non-ROS backup, or delete duplicates to avoid confusion.

## Old single-file URDF

`dum_e.urdf` (if present) was an older export — prefer **`dum_e_description/urdf/dum-e.xacro`** from the hardware team.
