"""
Shared track-target state machine: blob (x, y, area) → move_to nudges / pick / place.

Used by :mod:`track_target_node` (ROS) and :mod:`local_target_tracker` (no ROS).
Do not run both at once with the same robot.
"""
from __future__ import annotations

import random
import time
from enum import IntEnum, auto
from typing import Callable

# Image X: center of frame ± tol (px), typical 320-wide QVGA.
_CENTER_X = 160.0
_TOLERANCE = 15.0
# z = blob area; above this, object is "close enough" in image to count as pre-pick.
_AREA_GRIP_READY = 12000.0
_GRIP_READY_STREAK = 5
_POST_PICK_PLACE_DELAY_S = 5.0
_RANDOM_PLACE_POSES = ("down", "ready", "home")
_MIN_CMD_INTERVAL_S = 0.15


class _Phase(IntEnum):
    TRACKING = auto()
    HELD_PICKED = auto()


class TrackTargetController:
    def __init__(
        self,
        send_command: Callable[..., object],
        *,
        log_info: Callable[[str], None] | None = None,
        log_debug: Callable[[str], None] | None = None,
    ) -> None:
        self._send = send_command
        self._log_info = log_info or (lambda s: None)
        self._log_debug = log_debug or (lambda s: None)
        self._phase = _Phase.TRACKING
        self._last_cmd_mono: float = 0.0
        self._grip_ok_streak: int = 0
        self._pick_latch_mono: float | None = None
        self._place_pending: bool = False

    def on_target(self, x: float, y: float, z: float) -> None:
        """x,y = pixel center; z = blob area (0 = no object)."""
        if self._phase is not _Phase.TRACKING:
            return

        if z <= 0.0:
            self._log_debug(
                f"Ignoring (no area z={z}): x={x:.1f} y={y:.1f}"
            )
            self._grip_ok_streak = 0
            return

        lo = _CENTER_X - _TOLERANCE
        hi = _CENTER_X + _TOLERANCE
        centered = lo <= x <= hi

        if centered and z >= _AREA_GRIP_READY:
            self._grip_ok_streak += 1
        else:
            self._grip_ok_streak = 0

        if self._grip_ok_streak >= _GRIP_READY_STREAK:
            self._log_info(
                f"Object picked (vision): centered x={x:.0f}, area z={z:.0f} — "
                f"holding. Ignoring vision nudges for {_POST_PICK_PLACE_DELAY_S}s, then random place."
            )
            self._phase = _Phase.HELD_PICKED
            self._pick_latch_mono = time.monotonic()
            self._place_pending = True
            self._grip_ok_streak = 0
            return

        if x < lo:
            if not self._can_send_cmd():
                return
            self._log_info(
                f"Adjusting base: x={x:.0f} < {lo:.0f} — nudging left to center on cup."
            )
            self._send(
                action="move_to",
                target="left",
                source="track_target",
            )
            return

        if x > hi:
            if not self._can_send_cmd():
                return
            self._log_info(
                f"Adjusting base: x={x:.0f} > {hi:.0f} — nudging right to center on cup."
            )
            self._send(
                action="move_to",
                target="right",
                source="track_target",
            )
            return

        if not self._can_send_cmd():
            return
        self._log_info(
            f"Approaching: centered (x={x:.0f} in [{lo:.0f},{hi:.0f}]), "
            f"area z={z:.0f} < threshold — move forward."
        )
        self._send(
            action="move_to",
            target="forward",
            source="track_target",
        )

    def tick_place(self, now: float) -> None:
        """Call periodically (e.g. 5+ Hz) while running; places after latch delay."""
        if self._phase is not _Phase.HELD_PICKED or self._pick_latch_mono is None:
            return
        if not self._place_pending:
            return
        elapsed = now - self._pick_latch_mono
        if elapsed < _POST_PICK_PLACE_DELAY_S:
            return

        self._place_pending = False
        pose = random.choice(_RANDOM_PLACE_POSES)
        self._log_info(
            f"5s after pick: random place — move_to {pose!r}."
        )
        self._send(
            action="move_to",
            target=pose,
            source="track_target",
        )
        self._send(
            action="resume_idle",
            source="track_target",
        )
        self._pick_latch_mono = None
        self._grip_ok_streak = 0
        self._phase = _Phase.TRACKING
        self._log_info(
            "Place done: resume_idle — TRACKING re-armed for next object."
        )

    def _can_send_cmd(self) -> bool:
        now = time.monotonic()
        if now - self._last_cmd_mono < _MIN_CMD_INTERVAL_S:
            return False
        self._last_cmd_mono = now
        return True
