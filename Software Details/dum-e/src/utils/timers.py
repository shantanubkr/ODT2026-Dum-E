"""Small time helpers for MicroPython (ticks-based)."""

import time


def current_millis():
    """Milliseconds since boot (wraps per `time.ticks_ms()` rules)."""
    return time.ticks_ms()


def elapsed_ms(start_ticks, now_ticks=None):
    """Elapsed milliseconds from start_ticks to now_ticks (default: current)."""
    if now_ticks is None:
        now_ticks = time.ticks_ms()
    return time.ticks_diff(now_ticks, start_ticks)
