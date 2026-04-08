# Bridge from raw transport bytes/lines to cleaned text; CommandParser owns case/keyword rules.

from utils.logger import log  # Trace empty vs non-empty receive paths


class SerialInterface:
    """Sanitize + log input; poll() placeholder until UART/REPL is wired."""

    def __init__(self):
        log("Serial interface initialized")  # Confirms layer is alive

    def sanitize_input(self, raw_text):
        """Strip ends, coerce str; None → '' — do not lowercase (parser does that)."""
        if raw_text is None:  # No data this tick
            return ""  # Consistent empty token

        return str(raw_text).strip()  # Remove \r\n and outer spaces only

    def receive(self, raw_text):
        """Clean raw_text, log result, return string for handle_command(...)."""
        cleaned_text = self.sanitize_input(raw_text)  # Normalize whitespace
        if not cleaned_text:  # Empty after strip
            log("Serial input empty")  # Distinguish 'no line' from real cmds
            return ""  # Skip parser / mark_activity path in caller

        log("Serial input received: " + cleaned_text)  # Debug serial path
        return cleaned_text  # Caller passes to CommandParser

    def poll(self):
        """Future: non-blocking read from UART/sys.stdin; today always no data."""
        return None  # main loop treats falsy as 'no input this iteration'
