"""Live MJPEG stream + color detection (OpenCV).

    python vision_preview.py [stream_url] [color]

Defaults:
    stream_url  http://192.168.1.100:81/stream
    color       red

Controls:
    q           quit
    1-4         switch detection color  (1=red  2=blue  3=green  4=yellow)
"""

import sys
import cv2

# Allow running from repo root or from desktop_app/
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.vision_runtime import VisionRuntime

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_URL = "http://192.168.1.100:81/stream"
COLORS = {ord("1"): "red", ord("2"): "blue", ord("3"): "green", ord("4"): "yellow"}

# Drawing constants
BOX_COLOR = (0, 255, 0)       # green bounding box
DOT_COLOR = (0, 0, 255)       # red centroid dot
TEXT_COLOR = (255, 255, 255)
FONT = cv2.FONT_HERSHEY_SIMPLEX


# ---------------------------------------------------------------------------
# Overlay helpers
# ---------------------------------------------------------------------------

def draw_result(frame, result: dict, color: str):
    """Draw bounding box, centroid dot, and status label onto frame in-place."""
    h, w = frame.shape[:2]

    if result["found"]:
        x, y, bw, bh = result["bbox"]
        cx, cy = result["pixel_center"]
        area = result["area"]

        cv2.rectangle(frame, (x, y), (x + bw, y + bh), BOX_COLOR, 2)
        cv2.circle(frame, (cx, cy), 6, DOT_COLOR, -1)

        label = f"{color}  ({cx}, {cy})  area={int(area)}"
        cv2.putText(frame, label, (x, max(y - 8, 16)), FONT, 0.55, TEXT_COLOR, 1, cv2.LINE_AA)
    else:
        error = result.get("error", "unknown")
        cv2.putText(frame, f"[{color}] {error}", (10, h - 12), FONT, 0.5, (0, 80, 255), 1, cv2.LINE_AA)

    # Always show the active color in the top-left corner
    cv2.putText(frame, f"detecting: {color}  (1=red 2=blue 3=green 4=yellow  q=quit)",
                (8, 20), FONT, 0.45, TEXT_COLOR, 1, cv2.LINE_AA)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    active_color = sys.argv[2] if len(sys.argv) > 2 else "red"

    print(f"Connecting to {url}")
    print(f"Detecting: {active_color}")
    print("Press 1-4 to switch color, q to quit.")

    vision = VisionRuntime(url)

    try:
        while True:
            result = vision.find_color(active_color)
            frame = result.get("frame")

            if frame is None:
                print("No frame received — retrying...")
                cv2.waitKey(200)
                continue

            draw_result(frame, result, active_color)
            cv2.imshow("DUM-E Vision", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key in COLORS:
                active_color = COLORS[key]
                print(f"Switched to: {active_color}")

    finally:
        vision.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
