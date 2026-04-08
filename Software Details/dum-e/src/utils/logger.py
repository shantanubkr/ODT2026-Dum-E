# Central logging: print when DEBUG is on and keep a small ring buffer of recent lines.

from config import DEBUG, MAX_LOG_ENTRIES  # DEBUG toggles output; cap log list size

_logs = []  # In-memory list of recent formatted log strings (for status / debug)


def log(message):
    """Format message, optionally print, append to ring buffer, trim oldest if over cap."""
    global _logs  # Modify module-level list from inside function
    entry = "[DUM-E] " + str(message)  # Uniform prefix so serial grep is easy
    if DEBUG:  # On device, flip DEBUG in config to silence prints
        print(entry)  # Immediate feedback on REPL / UART
        _logs.append(entry)  # Store for status_report / post-mortem
    if len(_logs) > MAX_LOG_ENTRIES:  # Prevent unbounded RAM growth
        _logs.pop(0)  # Drop oldest entry (FIFO)


def get_logs():
    """Return a copy of the recent log buffer (same list reference — read-only use)."""
    return _logs  # Caller sees stored strings including [DUM-E] prefix


def clear_logs():
    """Empty the in-memory log history (e.g. after reset or test)."""
    global _logs  # Replace entire list
    _logs = []  # Fresh buffer
