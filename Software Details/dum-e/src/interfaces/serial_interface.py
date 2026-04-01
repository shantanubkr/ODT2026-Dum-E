"""Serial / REPL-side command intake — placeholder.

Later: non-blocking reads from `sys.stdin`, line buffering, or UART if you
dedicate a hardware serial port. For now, commands are often typed in the REPL.
"""


class SerialInterface:
    def __init__(self, command_parser=None):
        self._parser = command_parser

    def poll_line(self):
        # TODO: read a line when UART or stdin integration is defined
        return None
