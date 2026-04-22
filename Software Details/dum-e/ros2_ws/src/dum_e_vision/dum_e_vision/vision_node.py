"""
ROS 2 node: color blob in frame -> geometry_msgs/Point on /dume/target_coord.

- use_simulation:=true: subscribe to sensor_msgs/Image (Gazebo: /camera/image_raw, …).
- use_simulation:=false: read MJPEG/HTTP (ESP32-CAM) with OpenCV + CAP_FFMPEG.

Point: x, y = pixel center; z = contour area (same contract as track_target_node).
"""
from __future__ import annotations

import rclpy
from rclpy.node import Node
from cv_bridge import CvBridge, CvBridgeError
from geometry_msgs.msg import Point
from sensor_msgs.msg import Image
import cv2

from dum_e_vision.color_detector import ColorDetector

try:
    _FF = cv2.CAP_FFMPEG
except AttributeError:
    _FF = 0


class VisionNode(Node):
    def __init__(self) -> None:
        super().__init__("dum_e_vision")

        self.declare_parameter("use_simulation", False)
        self.declare_parameter("camera_image_topic", "/camera/image_raw")
        self.declare_parameter("stream_url", "http://127.0.0.1:81/stream")
        self.declare_parameter("target_color", "red")
        self.declare_parameter("publish_rate_hz", 10.0)
        self.declare_parameter("output_topic", "/dume/target_coord")

        use_sim = self.get_parameter("use_simulation").get_parameter_value().bool_value
        img_topic = self.get_parameter("camera_image_topic").get_parameter_value().string_value
        self._url = self.get_parameter("stream_url").get_parameter_value().string_value
        self._color = self.get_parameter("target_color").get_parameter_value().string_value
        rate = max(0.5, self.get_parameter("publish_rate_hz").get_parameter_value().double_value)
        out_name = self.get_parameter("output_topic").get_parameter_value().string_value

        self._bridge = CvBridge()
        self._detector = ColorDetector()
        self._pub = self.create_publisher(Point, out_name, 10)
        self._cap: cv2.VideoCapture | None = None
        self._cap_warned: bool = False
        self._timer = None
        self._sub = None

        if use_sim:
            self._sub = self.create_subscription(
                Image,
                img_topic,
                self._on_image,
                10,
            )
            self.get_logger().info(
                f"Vision: SIMULATION — subscribing to {img_topic} -> {out_name} (color={self._color})"
            )
        else:
            self.get_logger().info(
                f"Vision: REAL camera — {self._url} @ {rate:.1f} Hz -> {out_name} (color={self._color})"
            )
            period = 1.0 / rate
            self._timer = self.create_timer(period, self._on_timer_harvest)

    def _publish_point(self, frame) -> None:
        if frame is None or frame.size == 0:
            self._pub.publish(Point(x=0.0, y=0.0, z=0.0))
            return
        r = self._detector.detect(frame, self._color)
        if not r.get("found"):
            self._pub.publish(Point(x=0.0, y=0.0, z=0.0))
            return
        cx, cy = r["pixel_center"]
        z = float(r["area"])
        self._pub.publish(Point(x=float(cx), y=float(cy), z=z))

    def _on_image(self, msg: Image) -> None:
        try:
            frame = self._bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except CvBridgeError as e:
            self.get_logger().warning(f"cv_bridge: {e}")
            return
        self._publish_point(frame)

    def _ensure_cap(self) -> bool:
        if self._cap is not None and self._cap.isOpened():
            return True
        if self._cap is not None:
            self._cap.release()
        self._cap = cv2.VideoCapture(self._url, _FF)
        if self._cap.isOpened():
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return self._cap.isOpened() if self._cap else False

    def _on_timer_harvest(self) -> None:
        if not self._ensure_cap():
            if not self._cap_warned:
                self.get_logger().warn("Vision: could not open stream_url — publishing z=0")
                self._cap_warned = True
            self._pub.publish(Point(x=0.0, y=0.0, z=0.0))
            return
        self._cap_warned = False
        try:
            ok, frame = self._cap.read()
        except cv2.error:
            self._pub.publish(Point(x=0.0, y=0.0, z=0.0))
            return
        if not ok or frame is None:
            self._pub.publish(Point(x=0.0, y=0.0, z=0.0))
            return
        self._publish_point(frame)

    def destroy_node(self) -> bool:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        return super().destroy_node()  # type: ignore[return-value]


def main() -> None:
    rclpy.init()
    node = VisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
