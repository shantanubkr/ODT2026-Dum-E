import cv2
import numpy as np


# HSV ranges per color. Red wraps around 0°/180° so it has two ranges.
_DEFAULT_RANGES: dict[str, list[tuple[tuple, tuple]]] = {
    "red": [
        ((0, 120, 70), (10, 255, 255)),
        ((170, 120, 70), (180, 255, 255)),
    ],
    "blue": [
        ((100, 150, 0), (140, 255, 255)),
    ],
    "green": [
        ((40, 70, 70), (80, 255, 255)),
    ],
    "yellow": [
        ((20, 100, 100), (30, 255, 255)),
    ],
}

# Contours below this pixel area are treated as noise.
_MIN_AREA = 500

# Morphology kernel — removes speckle noise and fills small gaps.
_KERNEL = np.ones((5, 5), np.uint8)


class ColorDetector:
    """HSV-based color detection. Returns pixel centroid + bounding box.

    Result dict always contains "found" (bool).
    On success it also contains:
        pixel_center  (cx, cy)   — centroid of the largest matching contour
        bbox          (x, y, w, h)
        area          float      — contour area in pixels²

    On failure it also contains:
        error   "invalid_color" | "not_found" | "too_small"
    """

    def __init__(self, ranges: dict | None = None):
        self.ranges = ranges if ranges is not None else _DEFAULT_RANGES

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, frame, color: str) -> dict:
        """Detect `color` in `frame` (BGR numpy array).

        Returns a result dict as described in the class docstring.
        Never raises — returns {"found": False, "error": ...} on all failures.
        """
        color_ranges = self.ranges.get(color.lower())
        if not color_ranges:
            return {"found": False, "error": "invalid_color"}

        mask = self._build_mask(frame, color_ranges)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return {"found": False, "error": "not_found"}

        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)

        if area < _MIN_AREA:
            return {"found": False, "error": "too_small"}

        x, y, w, h = cv2.boundingRect(largest)
        cx = int(x + w / 2)
        cy = int(y + h / 2)

        return {
            "found": True,
            "pixel_center": (cx, cy),
            "bbox": (x, y, w, h),
            "area": float(area),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_mask(self, frame, color_ranges: list) -> np.ndarray:
        """Convert frame to HSV, union all range masks, apply morphology."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        combined = None
        for lower, upper in color_ranges:
            m = cv2.inRange(hsv, np.array(lower), np.array(upper))
            combined = m if combined is None else cv2.bitwise_or(combined, m)

        # Remove speckle noise, then dilate to fill small gaps inside the object.
        combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, _KERNEL)
        combined = cv2.morphologyEx(combined, cv2.MORPH_DILATE, _KERNEL)

        return combined
