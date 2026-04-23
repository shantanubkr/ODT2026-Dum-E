"""
desktop_app/services/sound_output.py

Plays keyed WAV files (robotic chirps/beeps) in a daemon thread.
Never blocks the UI. Silently skips missing sound files.
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path

# Resolve sounds/ relative to this file: desktop_app/services/ → desktop_app/sounds/
_SOUNDS_DIR = Path(__file__).resolve().parent.parent / "sounds"

_SOUND_FILES: dict[str, str] = {
    "greet":    "greet.wav",
    "happy":    "happy.wav",
    "sad":      "sad.wav",
    "bye":      "bye.wav",
    "confirm":  "confirm.wav",
    "move":     "move.wav",
    "pick":     "pick.wav",
    "error":    "error.wav",
    "thinking": "thinking.wav",
    "curious":  "curious.wav",
}


class SoundOutput:
    """Fire-and-forget WAV playback keyed by action `name."""

    def __init__(self) -> None:
        self._sounds: dict[str, Path] = {
            key: _SOUNDS_DIR / filename
            for key, filename in _SOUND_FILES.items()
        }

    def play(self, key: str, repeat: int = 2) -> None:
        """Start playback in a daemon thread — returns immediately.

        repeat controls how many times the clip plays back-to-back (default 2).
        """
        if not key:
            return
        threading.Thread(target=self._play_sync, args=(key, repeat), daemon=True).start()

    def _play_sync(self, key: str, repeat: int = 2) -> None:
        if not key:
            return
        path = self._sounds.get(key)
        if not path or not path.exists():
            return
        if os.environ.get("DUM_E_NO_SOUND", "").strip().lower() in (
            "1",
            "true",
            "yes",
        ):
            return
        # macOS: simpleaudio often segfaults from a worker thread next to Tk; use afplay.
        if sys.platform == "darwin":
            for _ in range(repeat):
                try:
                    subprocess.run(
                        ["/usr/bin/afplay", str(path)],
                        check=False,
                        capture_output=True,
                        timeout=120,
                    )
                except Exception:  # noqa: BLE001
                    pass
            return
        try:
            import simpleaudio as sa  # type: ignore[import]

            wave = sa.WaveObject.from_wave_file(str(path))
            for _ in range(repeat):
                wave.play().wait_done()
        except Exception:  # noqa: BLE001
            pass
