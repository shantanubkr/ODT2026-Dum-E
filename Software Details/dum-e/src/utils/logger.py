from config import DEBUG, MAX_LOG_ENTRIES

_logs = []  # List of log entries


def log(message):
    global _logs
    entry = "[DUM-E] " + str(message)
    if DEBUG:
        print(entry)
        _logs.append(entry)
    if len(_logs) > MAX_LOG_ENTRIES:
        _logs.pop(0)


def get_logs():
    return _logs


def clear_logs():
    global _logs
    _logs = []
