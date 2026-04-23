"""
No-ROS color-blob track target: VisionRuntime + :class:`TrackTargetController` in
a background thread.

Set ``DUM_E_VISION_URL`` (and optionally ``DUM_E_VISION_COLOR``) and
``DUM_E_LOCAL_TARGET_TRACK=1`` to enable. Requires ``dum_e_runtime`` to be
imported first (desktop app, or any entry that has set ``sys.path``).

**Do not** run together with the ROS :mod:`track_target_node` or another driver
on the same serial link.

Optional: ``DUM_E_LOCAL_TARGET_HZ`` (default ``8``) — vision poll rate.
"""
from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path

_started = False
_start_lock = threading.Lock()

_SRC = Path(__file__).resolve().parent.parent.parent / "src"


def _log(msg: str) -> None:
    try:
        if str(_SRC) not in sys.path:
            sys.path.insert(0, str(_SRC))
        from utils.logger import log  # type: ignore[import-not-found]

        log(msg)
    except Exception:  # noqa: BLE001
        print(msg, flush=True)


def _run() -> None:
    from . import dum_e_runtime as dr
    from .track_target_core import TrackTargetController
    from .vision_runtime import VisionRuntime

    if str(_SRC) not in sys.path:
        sys.path.insert(0, str(_SRC))
    from utils.logger import log  # type: ignore[import-not-found]

    url = (os.environ.get("DUM_E_VISION_URL") or "").strip()
    if not url:
        _log("[local_target_tracker] DUM_E_VISION_URL is not set — exiting")
        return

    color = (os.environ.get("DUM_E_VISION_COLOR") or "red").strip().lower()
    try:
        hz = float(os.environ.get("DUM_E_LOCAL_TARGET_HZ") or "8")
    except ValueError:
        hz = 8.0
    period = 1.0 / max(1.0, hz)

    try:
        vm = VisionRuntime(url)
    except Exception as exc:  # noqa: BLE001
        _log("[local_target_tracker] Vision init failed: " + str(exc))
        return

    ctrl = TrackTargetController(
        dr.send_command,
        log_info=log,
        log_debug=lambda s: None,
    )

    _log(
        f"[local_target_tracker] started url={url!r} color={color!r} hz={hz:.1f}"
    )
    while True:
        t0 = time.monotonic()
        try:
            res = vm.find_color(color)
            if not res.get("found") or res.get("frame") is None:
                ctrl.on_target(0.0, 0.0, 0.0)
            else:
                area = float(res.get("area") or 0.0)
                cx, cy = res["pixel_center"]
                ctrl.on_target(float(cx), float(cy), area)
            ctrl.tick_place(time.monotonic())
        except Exception as exc:  # noqa: BLE001
            log("[local_target_tracker] loop error: " + str(exc))
        elapsed = time.monotonic() - t0
        sleep_for = max(0.0, period - elapsed)
        if sleep_for > 0:
            time.sleep(sleep_for)


def start_if_enabled() -> None:
    """Idempotent: start the daemon thread when env is set (desktop app)."""
    global _started
    with _start_lock:
        if _started:
            return
        if os.environ.get("DUM_E_LOCAL_TARGET_TRACK", "").lower() not in (
            "1",
            "true",
            "yes",
        ):
            return
        t = threading.Thread(
            target=_run,
            name="local_target_tracker",
            daemon=True,
        )
        t.start()
        _started = True
