"""
desktop_app/services/app_runtime.py

Thin bridge between the Tkinter UI and the existing DUM-E runtime.

Single source of truth:
  AI interpretation  -> desktop_app/services/ai_interpreter.py
  Command routing    -> src/backend/command_router.py  (via dum_e_runtime)
  Robot bridge       -> src/interfaces/robot_bridge.py (via dum_e_runtime)
  Runtime state      -> desktop_app/services/dum_e_runtime.py
"""
from __future__ import annotations

from . import dum_e_runtime as _runtime
from .ai_interpreter import AIInterpreter

_interpreter = AIInterpreter()

# Maps routed action names → sound keys.
_ACTION_SOUND: dict[str, str] = {
    "greet":        "greet",
    "move_home":    "move",
    "move_to":      "move",
    "pick_object":  "pick",
    "place_object": "pick",
    "stop":         "error",
    "reset":        "confirm",
    "dance":        "happy",
}

# Maps sentiment buckets → sound keys.
# NEUTRAL is absent intentionally — falls back to the action sound.
_SENTIMENT_SOUND: dict[str, str] = {
    "GREET": "greet",
    "HAPPY": "happy",
    "SAD":   "sad",
    "BYE":   "bye",
}

# One-shot when `behavior` changes (UI poll) — matches firmware/desktop behaviors to clips.
_BEHAVIOR_ENTER_SOUND: dict[str, str] = {
    "thinking": "thinking",
    "express_happy": "happy",
    "express_sad": "sad",
    "sad_hold": "sad",
    "express_bye": "bye",
    "express_present": "pick",
    "express_greet": "greet",
    "greeting": "greet",
    "dancing": "happy",
}

class DesktopAppRuntime:
    """
    Clean interface for the Tkinter UI.

    All command routing, AI interpretation, and robot-bridge logic live in
    desktop_app/services — this class is just a thin facade.
    """

    def __init__(self) -> None:
        from .speech_to_text import LocalSpeechToText
        from .sound_output import SoundOutput
        self._stt = LocalSpeechToText(model_size="base")
        self.sound = SoundOutput()
        # Ambient sound tracking — updated by get_status() on every UI poll.
        self._last_behavior: str = ""
        self._last_idle_substate: str = ""
        self._last_idle_wander_tick: int = 0

    def get_sound(self, action: str) -> str:
        """Map a routed action name to a sound key."""
        return _ACTION_SOUND.get(action, "")

    # ------------------------------------------------------------------
    # Text command (AI interpreter first, then route)
    # ------------------------------------------------------------------

    def send_text_command(self, text: str) -> dict:
        """
        Interpret free text, route the resulting command, and return a dict
        containing: ok, ai debug info (input/action/target), and result.
        """
        raw = (text or "").strip()
        if not raw:
            return {"ok": False, "error": "empty_input", "ai": {}}

        _runtime.mark_activity()

        ai_result = _interpreter.interpret_text(raw)
        ai_debug = {
            "input": raw,
            "action": ai_result.get("action"),
            "target": ai_result.get("target"),
        }

        # Detect emotional tone; sentiment sound takes priority over action sound
        # so e.g. "good job" plays "happy" even though there is no routed action.
        # NEUTRAL falls through to the action sound below.
        sentiment = _runtime.intent_parser.detect_sentiment(raw)
        sentiment_key = _SENTIMENT_SOUND.get(sentiment, "")

        if not ai_result.get("ok"):
            if sentiment == "GREET":
                _runtime.state_machine.change_state(_runtime.States.ACTIVE)
                _runtime.behavior_engine.set_behavior("greeting")
            elif sentiment == "SAD":
                _runtime.state_machine.change_state(_runtime.States.SAD)
                _runtime.behavior_engine.run_behavior("express_sad")
            if sentiment_key:
                self.sound.play(sentiment_key)
            return {
                "ok": False,
                "error": ai_result.get("error", "unknown_intent"),
                "ai": ai_debug,
            }

        if sentiment == "GREET":
            _runtime.state_machine.change_state(_runtime.States.ACTIVE)
        elif sentiment == "SAD":
            _runtime.state_machine.change_state(_runtime.States.SAD)
            _runtime.behavior_engine.run_behavior("express_sad")
        elif sentiment in ("HAPPY", "BYE"):
            _runtime.state_machine.change_state(_runtime.States.ACTIVE)

        result = _runtime.send_command(
            action=ai_result["action"],
            target=ai_result.get("target"),
            source="desktop_ai",
        )
        # Play sentiment sound when available; fall back to action sound for NEUTRAL.
        combined = sentiment_key or self.get_sound(ai_result["action"])
        if combined:
            self.sound.play(combined)
        result["ai"] = ai_debug
        return result

    # ------------------------------------------------------------------
    # Direct action (quick buttons — skip AI interpretation)
    # ------------------------------------------------------------------

    def send_action(self, action: str, target: str | None = None) -> dict:
        """Route a structured action directly, bypassing AI interpretation."""
        result = _runtime.send_command(action=action, target=target, source="desktop")
        sk = self.get_sound(action)
        if sk:
            self.sound.play(sk)
        return result

    # ------------------------------------------------------------------
    # Voice input (push-to-talk: record → transcribe → send_text_command)
    # ------------------------------------------------------------------

    def handle_voice_input(self) -> dict:
        """
        Record audio → transcribe locally (Whisper) → send through the normal
        text-command pipeline (AIInterpreter → router → bridge).

        Flow:
            Mic → audio_recorder → LocalSpeechToText → send_text_command()

        Returns the same dict as send_text_command(), plus:
            voice_input: str  — the raw Whisper transcript
        """
        from .audio_recorder import record_audio

        try:
            file_path = record_audio()
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": "mic_error", "detail": str(exc)}

        transcript = self._stt.transcribe(file_path)
        if not transcript:
            return {"ok": False, "error": "no_speech"}

        result = self.send_text_command(transcript)
        result["voice_input"] = transcript
        return result

    # ------------------------------------------------------------------
    # Status / logs
    # ------------------------------------------------------------------

    def get_status(self) -> dict:
        """Return a JSON-serialisable status snapshot and fire ambient sounds."""
        status = _runtime.get_status()
        self._check_ambient_sounds(status)
        return status

    def get_logs(self) -> list:
        """Return the current log ring-buffer as a list of strings."""
        return _runtime.get_logs_only()

    # ------------------------------------------------------------------
    # Ambient sound triggers (driven by the 1.5 s UI status poll)
    # ------------------------------------------------------------------

    def _check_ambient_sounds(self, status: dict) -> None:
        """Laptop speaker: thinking on new wander step; curious when inspecting a blob.

        Called on every get_status() poll (≈1.5 s interval from the UI).
        """
        behavior = status.get("behavior", "")
        sub = str(status.get("idle_substate") or "")
        tick = int(status.get("idle_wander_tick") or 0)

        if behavior == "idle" and sub == "wander" and tick != self._last_idle_wander_tick:
            self.sound.play("thinking", repeat=1)
            self._last_idle_wander_tick = tick

        if sub == "inspect" and self._last_idle_substate != "inspect":
            self.sound.play("curious", repeat=1)

        if behavior != self._last_behavior:
            bkey = _BEHAVIOR_ENTER_SOUND.get(behavior)
            if bkey:
                self.sound.play(bkey, repeat=1)

        self._last_behavior = behavior
        self._last_idle_substate = sub
