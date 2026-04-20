"""
desktop_app/services/speech_to_text.py

Local, offline speech-to-text using faster-whisper.

Architecture:
    audio file → LocalSpeechToText.transcribe() → plain transcript string

This file is ONLY responsible for audio → text.
No command parsing, no robot logic, no network calls.

The model is loaded once in __init__ and reused on every call.
On first use, faster-whisper will download the requested model (~150 MB for
"base") into ~/.cache/huggingface/hub — subsequent runs use the cache.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class LocalSpeechToText:
    """
    Wraps a faster-whisper WhisperModel for local, CPU-friendly transcription.

    Usage:
        stt = LocalSpeechToText(model_size="base")
        text = stt.transcribe("/tmp/dum_e_recording.wav")
    """

    def __init__(self, model_size: str = "base") -> None:
        self._model = None
        self._model_size = model_size
        self._load_model()

    def _load_model(self) -> None:
        try:
            from faster_whisper import WhisperModel  # type: ignore[import]
            logger.info("[stt] loading Whisper model '%s' on CPU …", self._model_size)
            self._model = WhisperModel(
                self._model_size,
                device="cpu",
                compute_type="int8",  # smallest memory / CPU footprint
            )
            logger.info("[stt] model ready")
        except ImportError:
            logger.error(
                "[stt] faster-whisper not installed — "
                "run: pip install faster-whisper"
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("[stt] failed to load model: %s", exc)

    def transcribe(self, file_path: str) -> str:
        """
        Transcribe *file_path* and return the full transcript as a single string.
        Returns "" if the model is not loaded or transcription fails.
        """
        if self._model is None:
            logger.error("[stt] model not loaded — transcription skipped")
            return ""

        try:
            segments, info = self._model.transcribe(file_path, beam_size=5)
            logger.info(
                "[stt] detected language '%s' (%.0f%%)",
                info.language,
                info.language_probability * 100,
            )
            transcript = " ".join(seg.text.strip() for seg in segments).strip()
            logger.info("[stt] transcript: %r", transcript)
            return transcript
        except Exception as exc:  # noqa: BLE001
            logger.error("[stt] transcription failed: %s", exc)
            return ""
