import cv2


# Prefer FFmpeg for HTTP/MJPEG: fewer stuck buffers and cleaner recovery on bad chunks.
# See: https://docs.opencv.org/4.x/d4/d15/group__videoio__flags__base.html
try:
    _DEFAULT_HTTP_BACKEND = cv2.CAP_FFMPEG
except AttributeError:  # rare minimal builds
    _DEFAULT_HTTP_BACKEND = 0


class CameraStream:
    """Reads frames from an MJPEG stream URL (e.g. ESP32-CAM http://ip:81/stream).

    Uses CAP_FFMPEG to reduce multi-second lag and to tolerate stream hiccups.
    CAP_PROP_BUFFERSIZE=1 keeps the latest frame (drops backlog).

    On corrupt JPEG (Huffman / DHT warnings from FFmpeg, bad decode), read() returns
    None so upstream logic can skip the frame.
    """

    def __init__(
        self,
        url: str,
        *,
        backend: int | None = None,
        buffer_size: int = 1,
    ):
        self.url = url
        self._backend = _DEFAULT_HTTP_BACKEND if backend is None else backend
        self._buffer_size = max(1, int(buffer_size))
        self.cap: cv2.VideoCapture | None = None

    def connect(self) -> bool:
        """Open the stream with FFmpeg; set minimal buffer. Returns True if opened."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        try:
            self.cap = cv2.VideoCapture(self.url, self._backend)
        except cv2.error:
            self.cap = None
            return False
        except Exception:
            self.cap = None
            return False

        if not self.cap.isOpened():
            self.cap = None
            return False

        try:
            # Drop stale frames (fixes long latency on bursty Wi‑Fi)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self._buffer_size)
        except (cv2.error, Exception):
            pass
        return True

    def read(self):
        """Return the next BGR frame, or None on failure / corrupt / empty frame."""
        if self.cap is None or not self.cap.isOpened():
            if not self.connect():
                return None

        try:
            ret, frame = self.cap.read()
        except cv2.error:
            return None
        except Exception:
            return None

        if not ret or frame is None:
            return None
        if getattr(frame, "size", 0) == 0 or frame.shape[0] < 2 or frame.shape[1] < 2:
            return None

        return frame

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
