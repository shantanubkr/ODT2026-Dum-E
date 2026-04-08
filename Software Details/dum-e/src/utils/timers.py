import time


# Current board uptime in milliseconds (for timeouts, cooldowns, and durations).
def current_millis():
    return time.ticks_ms()


# Milliseconds since start_ms, using ticks_diff so wraparound is handled correctly.
def elapsed_ms(start_ms):
    return time.ticks_diff(time.ticks_ms(), start_ms)


# True if at least duration_ms has passed since start_ms (idle, sensor timeout, etc.).
def has_elapsed(start_ms, duration_ms):
    return elapsed_ms(start_ms) >= duration_ms


# Returns a fresh timestamp; use when resetting activity, wake, or sensor timers.
def reset_timer():
    return current_millis()


# Blocks for duration_ms; use sparingly—prefer non-blocking has_elapsed in the main loop.
def sleep_ms(duration_ms):
    time.sleep_ms(duration_ms)
