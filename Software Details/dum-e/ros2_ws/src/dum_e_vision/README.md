# `dum_e_vision` (ROS 2)

Publishes **`geometry_msgs/Point`** on **`/dume/target_coord`**: **x, y** = blob centroid (px), **z** = contour area. Consumed by `desktop_app/track_target_node.py`.

## Modes

| Param | Gazebo / sim | Real ESP32-CAM (OpenCV) |
|-------|----------------|------------------------|
| `use_simulation` | `true` | `false` (default) |
| Input | `camera_image_topic` (default `/camera/image_raw`) | `stream_url` (e.g. `http://<ip>:81/stream`) |
| Drive | one callback per `sensor_msgs/Image` | timer at `publish_rate_hz` (default 10) |

## Build (ROS 2 Humble)

```bash
cd ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select dum_e_vision
source install/setup.bash
```

## Run

**Real camera:**

```bash
ros2 run dum_e_vision vision_node --ros-args \
  -p use_simulation:=false \
  -p stream_url:=http://192.168.1.100:81/stream \
  -p target_color:=red
```

**Gazebo (example):**

```bash
ros2 run dum_e_vision vision_node --ros-args \
  -p use_simulation:=true \
  -p camera_image_topic:=/camera/image_raw
```

Requires: **OpenCV** (`python3-opencv` / `cv_bridge`).
