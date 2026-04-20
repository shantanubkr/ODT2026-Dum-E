# Single parsing pipeline: typed text -> structured dict for build_command_from_parse_result.
# Sentiment detection runs on every parse() call; result["sentiment"] is always present.

from modules.command_parser import CommandParser

# Pattern lists for detect_sentiment(); checked in priority order: GREET > BYE > HAPPY > SAD.
_GREET_PATTERNS = ["hello", "hi", "hey", "sup", "what's up", "howdy", "yo"]
_BYE_PATTERNS   = ["bye", "goodbye", "see you", "later", "see ya",
                    "take care", "good night", "cya"]
_HAPPY_PATTERNS = ["good job", "well done", "nice", "great", "perfect",
                    "love you", "amazing", "awesome", "proud of you",
                    "good boy", "bravo", "excellent", "fantastic"]
_SAD_PATTERNS   = ["bad", "useless", "stupid", "idiot", "terrible",
                    "you suck", "worst", "hate you", "dumb", "pathetic",
                    "garbage", "horrible", "disappointing", "failure"]


def _word_match(pattern, text):
    """True if pattern appears in text with word boundaries on both sides.

    Avoids false positives like 'yo' inside 'you're' or 'hi' inside 'this'.
    No regex — safe on MicroPython. Scans all occurrences of pattern in text.
    """
    idx = text.find(pattern)
    while idx != -1:
        start_ok = (idx == 0) or not text[idx - 1].isalpha()
        end_idx = idx + len(pattern)
        end_ok = (end_idx == len(text)) or not text[end_idx].isalpha()
        if start_ok and end_ok:
            return True
        idx = text.find(pattern, idx + 1)
    return False


class IntentParser(CommandParser):
    """Same keyword rules as CommandParser; adds sentiment detection on every parse call."""

    def detect_sentiment(self, text):
        """Return one of GREET / BYE / HAPPY / SAD / NEUTRAL via word-boundary scan.

        Checked in priority order so greetings/farewells beat emotional words.
        Returns NEUTRAL when no pattern matches.
        """
        lowered = text.lower() if text else ""
        for p in _GREET_PATTERNS:
            if _word_match(p, lowered):
                return "GREET"
        for p in _BYE_PATTERNS:
            if _word_match(p, lowered):
                return "BYE"
        for p in _HAPPY_PATTERNS:
            if _word_match(p, lowered):
                return "HAPPY"
        for p in _SAD_PATTERNS:
            if _word_match(p, lowered):
                return "SAD"
        return "NEUTRAL"

    def parse(self, raw_command):
        """Delegate to CommandParser then attach sentiment key to every result dict."""
        result = super().parse(raw_command)
        result["sentiment"] = self.detect_sentiment(raw_command or "")
        return result
