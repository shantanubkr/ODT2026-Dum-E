"""Vendored from desktop_app/services/color_detector.py (keep in sync for tuning)."""
import cv2
import numpy as np

_DEFAULT_RANGES: dict[str, list[tuple[tuple, tuple]]] = {
    "red": [
        ((0, 120, 70), (10, 255, 255)),
        ((170, 120, 70), (180, 255, 255)),
    ],
    "blue": [((100, 150, 0), (140, 255, 255))],
    "green": [((40, 70, 70), (80, 255, 255))],
    "yellow": [((20, 100, 100), (30, 255, 255))],
}

_MIN_AREA = 500
_KERNEL = np.ones((5, 5), np.uint8)


class ColorDetector:
    def __init__(self, ranges: dict | None = None):
        self.ranges = ranges if ranges is not None else _DEFAULT_RANGES

    def detect(self, frame, color: str) -> dict:
        color_ranges = self.ranges.get(color.lower())
        if not color_ranges:
            return {"found": False, "error": "invalid_color"}
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        combined = None
        for lower, upper in color_ranges:
            m = cv2.inRange(hsv, np.array(lower), np.array(upper))
            combined = m if combined is None else cv2.bitwise_or(combined, m)
        combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, _KERNEL)
        combined = cv2.morphologyEx(combined, cv2.MORPH_DILATE, _KERNEL)
        contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return {"found": False, "error": "not_found"}
        largest = max(contours, key=cv2.contourArea)
        area = float(cv2.contourArea(largest))
        if area < _MIN_AREA:
            return {"found": False, "error": "too_small"}
        x, y, w, h = cv2.boundingRect(largest)
        return {
            "found": True,
            "pixel_center": (int(x + w / 2), int(y + h / 2)),
            "bbox": (x, y, w, h),
            "area": area,
        }
