from .camera_stream import CameraStream
from .color_detector import ColorDetector


class VisionRuntime:
    """Ties CameraStream and ColorDetector together into a single call.

    Typical usage:
        vision = VisionRuntime("http://192.168.1.100:81/stream")
        result = vision.find_color("red")
        if result["found"]:
            cx, cy = result["pixel_center"]

    The "frame" key is always included in the result so callers can
    display or debug the raw image without a second camera.read() call.
    """

    def __init__(self, stream_url: str):
        self.camera = CameraStream(stream_url)
        self.detector = ColorDetector()

    def find_color(self, color: str) -> dict:
        """Capture one frame and run color detection on it.

        Returns a result dict from ColorDetector, augmented with:
            frame   numpy.ndarray | None   — the raw BGR frame (None on read failure)
        """
        frame = self.camera.read()

        if frame is None:
            return {"found": False, "error": "no_frame", "frame": None}

        result = self.detector.detect(frame, color)
        result["frame"] = frame
        return result

    def release(self):
        """Release the underlying camera resource."""
        self.camera.release()
