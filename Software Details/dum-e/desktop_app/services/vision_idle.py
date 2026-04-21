"""Optional idle-time vision: poll camera when DUM_E_VISION_URL is set.

Maps largest color blob → waist / hand angles and calls send_idle_look_at.
Requires OpenCV (same stack as VisionRuntime).
"""
from __future__ import annotations

import os
import time

_MIN_SEND_INTERVAL_SEC = 2.0
_DEFAULT_MIN_AREA = 800.0

_vision = None
_last_send_mono: float = 0.0


def _vision_runtime():
    global _vision
    if _vision is None:
        url = (os.environ.get("DUM_E_VISION_URL") or "").strip()
        if not url:
            return None
        from .vision_runtime import VisionRuntime

        _vision = VisionRuntime(url)
    return _vision


def tick_idle_vision() -> None:
    global _last_send_mono
    if not (os.environ.get("DUM_E_VISION_URL") or "").strip():
        return

    from . import dum_e_runtime as dr

    if dr.state_machine.get_state() != "ACTIVE":
        return
    if dr.behavior_engine.get_behavior() != "idle":
        return
    if dr.behavior_engine.get_idle_substate() == "inspect":
        return

    now = time.monotonic()
    if now - _last_send_mono < _MIN_SEND_INTERVAL_SEC:
        return

    try:
        min_area = float(os.environ.get("DUM_E_VISION_MIN_AREA", str(_DEFAULT_MIN_AREA)))
    except ValueError:
        min_area = _DEFAULT_MIN_AREA
    color = (os.environ.get("DUM_E_VISION_COLOR") or "red").strip().lower()

    vm = _vision_runtime()
    if vm is None:
        return

    result = vm.find_color(color)
    frame = result.get("frame")
    if not result.get("found") or frame is None:
        return
    area = float(result.get("area") or 0.0)
    if area < min_area:
        return

    cx, cy = result["pixel_center"]
    h, w = frame.shape[0], frame.shape[1]
    if w <= 0 or h <= 0:
        return

    err_x = (cx - w * 0.5) / (w * 0.5)
    err_y = (cy - h * 0.5) / (h * 0.5)
    waist = 90.0 + err_x * 55.0
    hand = 90.0 - err_y * 40.0
    waist = max(0.0, min(180.0, waist))
    hand = max(0.0, min(180.0, hand))

    dr.send_idle_look_at(waist, hand, source="vision_idle")
    _last_send_mono = now
