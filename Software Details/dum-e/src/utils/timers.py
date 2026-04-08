# MicroPython / ESP32 timing helpers: use ticks_ms + ticks_diff for reliable deltas.

import time  # Provides ticks_ms, ticks_diff, sleep_ms on MicroPython


def current_millis():
    """Return the board's monotonic millisecond counter (wraps eventually)."""
    return time.ticks_ms()  # Raw uptime in ms — good for embedded scheduling


def elapsed_ms(start_ms):
    """Milliseconds from start_ms to now; ticks_diff handles counter wraparound."""
    return time.ticks_diff(time.ticks_ms(), start_ms)  # Never subtract ticks directly on MP


def has_elapsed(start_ms, duration_ms):
    """True if at least duration_ms has passed since start_ms (timeouts, cooldowns)."""
    return elapsed_ms(start_ms) >= duration_ms  # Compare elapsed wall-clock delta to threshold


def reset_timer():
    """Return a new timestamp — call when activity resets an idle/sleep/timer."""
    return current_millis()  # Same as ticks_ms; reads clearly as 'start counting from now'


def sleep_ms(duration_ms):
    """Block for duration_ms — prefer non-blocking has_elapsed in the main loop."""
    time.sleep_ms(duration_ms)  # Busy sleep; use only for short, deliberate delays
