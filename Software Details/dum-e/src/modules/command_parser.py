"""Turn raw text into simple command tokens — no NLP."""


class CommandParser:
    """Normalize strings and map to a small command vocabulary later."""

    def __init__(self):
        self._aliases = {
            "stop": "STOP",
            "home": "HOME",
            "status": "STATUS",
        }

    def parse(self, line):
        """Strip, upper-case token, optional alias lookup."""
        if not line:
            return None
        cleaned = " ".join(line.split()).strip()
        if not cleaned:
            return None
        first = cleaned.split(maxsplit=1)[0].upper()
        return self._aliases.get(first.lower(), first)
