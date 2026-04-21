import cv2


class CameraStream:
    """Reads frames from an MJPEG stream URL (e.g. ESP32-CAM http://ip:81/stream).

    Lazy-connects on first read so construction never blocks.
    Returns None on any frame failure instead of raising.
    """

    def __init__(self, url: str):
        self.url = url
        self.cap: cv2.VideoCapture | None = None

    def connect(self) -> bool:
        """Open the stream. Returns True if the capture opened successfully."""
        self.cap = cv2.VideoCapture(self.url)
        return self.cap.isOpened()

    def read(self):
        """Return the next BGR frame, or None if unavailable."""
        if self.cap is None or not self.cap.isOpened():
            self.connect()

        if self.cap is None or not self.cap.isOpened():
            return None

        ret, frame = self.cap.read()
        if not ret or frame is None:
            return None

        return frame

    def release(self):
        """Release the capture handle."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
