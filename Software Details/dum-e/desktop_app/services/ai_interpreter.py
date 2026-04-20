"""
desktop_app/services/ai_interpreter.py

Rule-based conversational interpreter for DUM-E commands (v2).

Public surface is unchanged — drop-in replacement for any LLM-backed version:

    interp = AIInterpreter()
    result = interp.interpret_text("hey dum-e, can you go home please")
    # -> {"ok": True, "action": "move_home", "target": None}

Matching pipeline (first match wins):
    1. Normalise  — lowercase, strip punctuation, remove robot-name + filler
    2. Exact      — normalised text equals a known phrase
    3. Contains   — normalised text contains a key phrase
    4. Regex      — structured object commands (pick / place)
"""

import re

# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

# Robot name variants to erase before matching
_ROBOT_NAMES = re.compile(
    r"\b(?:dum[-\s]?e)\b",
    re.IGNORECASE,
)

# Conversational filler words/phrases to erase (order matters: longer first)
_FILLER = re.compile(
    r"\b(?:"
    r"could\s+you|can\s+you|will\s+you|would\s+you"
    r"|please|kindly|for\s+me|go\s+ahead\s+and"
    r"|hey|hi\s+there|okay|ok"
    r")\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# 1. Exact-match table
#    Normalised input must equal one of these strings exactly.
# ---------------------------------------------------------------------------
_EXACT_INTENTS: list[tuple[set, str, str | None]] = [
    ({"home", "go home", "move home", "return home"},   "move_home", None),
    ({"hello", "hi", "wave", "greet", "say hello",
      "say hi", "wave hello"},                          "greet",     None),
    ({"stop", "halt", "freeze", "emergency stop"},      "stop",      None),
    ({"reset"},                                         "reset",     None),
    ({"ready", "go ready"},                             "move_to",   "ready"),
    ({"down",  "go down"},                              "move_to",   "down"),
    ({"status"},                                        "status",    None),
]

# ---------------------------------------------------------------------------
# 2. Contains-phrase table
#    Normalised input must CONTAIN one of these substrings.
#    Ordered most-specific → least-specific within each intent.
# ---------------------------------------------------------------------------
_CONTAINS_INTENTS: list[tuple[set, str, str | None]] = [
    # greet — checked before "hi" / "hello" loose matches
    ({"say hello", "say hi", "wave hello", "wave hi",
      "give a wave", "do a wave", "give greeting",
      "greet me", "greet yourself"},                   "greet",     None),
    ({"hello", "hi", "wave", "greet"},                 "greet",     None),

    # move_home
    ({"go home", "move home", "return home",
      "back home", "go back home", "head home",
      "go to home", "move to home"},                   "move_home", None),

    # move_to ready
    ({"go to ready", "move to ready", "ready position",
      "get to ready", "go ready", "move ready"},       "move_to",   "ready"),

    # move_to down
    ({"go to down", "move to down", "down position",
      "get to down", "go down", "move down",
      "lower down", "lower position"},                 "move_to",   "down"),

    # stop — after move phrases to avoid "stop going down" collision
    ({"stop", "halt", "freeze", "emergency stop",
      "shut down", "cut it"},                          "stop",      None),

    # reset
    ({"reset", "restart", "reboot",
      "reset yourself", "start over"},                 "reset",     None),
]

# ---------------------------------------------------------------------------
# 3. Regex pattern table
#    For structured commands that carry a variable object target.
#    Applied to the normalised (filler-stripped) text.
# ---------------------------------------------------------------------------
_PATTERN_INTENTS: list[tuple[re.Pattern, str, int]] = [
    # pick / grab / take — strips leading "up the", "the"
    (re.compile(
        r"^(?:pick(?:\s+up)?|grab|take|lift(?:\s+up)?)\s+"
        r"(?:the\s+|a\s+)?(.+)$"
     ), "pick_object", 1),

    # place / drop / put / set down
    (re.compile(
        r"^(?:place|drop|put(?:\s+down)?|set(?:\s+down)?)\s+"
        r"(?:the\s+|a\s+)?(.+)$"
     ), "place_object", 1),
]


# ---------------------------------------------------------------------------
# Interpreter
# ---------------------------------------------------------------------------

class AIInterpreter:
    """
    Conversational rule-based interpreter for DUM-E v2.

    Handles natural spoken sentences by stripping robot names and filler words
    before matching, so "hey dum-e, can you please go home" normalises to
    "go home" and matches the move_home intent.
    """

    def interpret_text(self, text: str) -> dict:
        """
        Parse *text* and return an intent dict.

        Return shapes:
          {"ok": True,  "action": str, "target": str | None}
          {"ok": False, "error": "empty_input"}
          {"ok": False, "error": "unknown_intent", "raw_text": str}
        """
        if not isinstance(text, str) or not text.strip():
            return {"ok": False, "error": "empty_input"}

        raw = text.strip()
        normalised = self._normalise(raw)

        if not normalised:
            # Input was only filler / robot name (e.g. "hey dum-e")
            # Treat as a greeting so the robot acknowledges the wake phrase.
            return {"ok": True, "action": "greet", "target": None}

        # Pass 1 — exact
        for keywords, action, target in _EXACT_INTENTS:
            if normalised in keywords:
                return {"ok": True, "action": action, "target": target}

        # Pass 2 — contains
        for phrases, action, target in _CONTAINS_INTENTS:
            if any(phrase in normalised for phrase in phrases):
                return {"ok": True, "action": action, "target": target}

        # Pass 3 — regex (pick / place with variable object)
        for pattern, action, group in _PATTERN_INTENTS:
            m = pattern.match(normalised)
            if m:
                return {"ok": True, "action": action,
                        "target": m.group(group).strip()}

        return {"ok": False, "error": "unknown_intent", "raw_text": raw}

    # ------------------------------------------------------------------
    # Normalisation
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise(text: str) -> str:
        """
        Clean raw input into a minimal intent phrase:

          "Hey DUM-E, can you please go home!" -> "go home"
          "dum-e say hello"                    -> "say hello"
          "pick up the red bottle"             -> "pick red bottle"
          "  Can you STOP??  "                 -> "stop"
        """
        t = text.lower()

        # Remove robot name variants first so "dum-e go home" -> "go home"
        t = _ROBOT_NAMES.sub(" ", t)

        # Strip edge punctuation and commas
        t = t.strip(" \t\n\r.,!?;:")

        # Remove filler words / polite wrappers
        t = _FILLER.sub(" ", t)

        # Collapse whitespace and strip again
        t = re.sub(r"\s+", " ", t).strip(" \t\n\r.,!?;:")

        return t
