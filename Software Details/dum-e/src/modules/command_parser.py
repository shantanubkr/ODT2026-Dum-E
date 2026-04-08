# Text commands → structured dicts; normalization + history; no NLP — explicit keywords only.

from utils.logger import log  # Trace each parsed command

from config import COMMAND_HISTORY_SIZE  # Max length of rolling history (from config)


class CommandParser:
    """Normalize input, keep last N commands, return {type, command, args, ...}."""

    def __init__(self):
        self.history = []  # FIFO of normalized command strings
        self.valid_commands = ["pick", "drop", "move", "stop", "hello", "home", "status", "history", "reset"]  # Exact-match vocabulary
        log("Command parser initialized")  # Startup visibility

    def normalize(self, raw_command):
        """Strip whitespace, lowercase, coerce to str; None → empty string."""
        if raw_command is None:  # Guard REPL / serial gaps
            return ""  # parse() will classify as empty

        return str(raw_command).strip().lower()  # Stable token form for matching

    def add_to_history(self, command):
        """Append non-empty normalized command; drop oldest if over COMMAND_HISTORY_SIZE."""
        if not command:  # Skip blanks — no noise in history
            return  # Nothing to store

        self.history.append(command)  # Newest at end
        if len(self.history) > COMMAND_HISTORY_SIZE:  # Ring buffer behavior
            self.history.pop(0)  # Remove oldest

    def get_history(self):
        """Return the live history list (newest last)."""
        return self.history  # Used by 'history' command

    def parse(self, raw_command):
        """Main entry: normalize, maybe history, classify into structured result dict."""
        command = self.normalize(raw_command)  # Always parse clean text
        if not command:  # Nothing useful after normalize
            return {"type": "empty", "raw": raw_command, "normalized": ""}  # No history for pure empty

        self.add_to_history(command)  # Record only non-empty normalized lines
        log("Command received: " + command)  # Debug trace

        if command in self.valid_commands:  # Exact keyword match
            return {"type": "known", "command": command, "args": []}  # args reserved for extensions

        if command.startswith("move "):  # Pattern: move <direction>
            parts = command.split()  # Whitespace tokens
            if len(parts) >= 2:  # Need verb + direction
                direction = parts[1]  # e.g. "left", "up"
                return {"type": "move", "command": "move", "args": [direction]}  # Structured move

        return {"type": "unknown", "command": command, "args": []}  # Graceful fallback
