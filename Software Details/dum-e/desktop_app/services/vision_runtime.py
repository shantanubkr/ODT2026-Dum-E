from .camera_stream import CameraStream
from .color_detector import ColorDetector

import cv2

try:
    _DEFAULT_BACKEND = cv2.CAP_FFMPEG
except AttributeError:
    _DEFAULT_BACKEND = 0


class VisionRuntime:
    """Ties CameraStream and ColorDetector together into a single call.

    Passes through FFmpeg backend and buffer size to :class:`CameraStream` to keep
    MJPEG latency low and skip bad frames (Huffman / partial JPEG) gracefully.

    Typical usage:
        vision = VisionRuntime("http://192.168.1.100:81/stream")
        result = vision.find_color("red")
        if result["found"]:
            cx, cy = result["pixel_center"]
    """

    def __init__(
        self,
        stream_url: str,
        *,
        camera_backend: int | None = None,
        buffer_size: int = 1,
    ):
        _backend = _DEFAULT_BACKEND if camera_backend is None else camera_backend
        self.camera = CameraStream(
            stream_url,
            backend=_backend,
            buffer_size=buffer_size,
        )
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
        self.camera.release()
