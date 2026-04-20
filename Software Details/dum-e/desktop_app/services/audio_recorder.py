"""
desktop_app/services/audio_recorder.py

Records a short audio clip from the default microphone and saves it as a WAV
file in the system temp directory.  Returns the file path so the caller can
pass it on to a transcription service.

No threading — sounddevice.rec() + wait() is synchronous and simple.
No GUI code — this file is pure I/O.
"""
from __future__ import annotations

import logging
import os
import tempfile

import sounddevice as sd
from scipy.io import wavfile

logger = logging.getLogger(__name__)


def _temp_wav_path() -> str:
    return os.path.join(tempfile.gettempdir(), "dum_e_recording.wav")


def record_audio(duration: int = 4, samplerate: int = 16000) -> str:
    """
    Record *duration* seconds of mono 16-bit audio from the default input device.

    Returns the absolute path to the saved WAV file.
    Raises on hardware failure so callers can return a safe error dict.
    """
    path = _temp_wav_path()
    logger.info("[audio_recorder] recording %ds @ %dHz → %s", duration, samplerate, path)
    frames = sd.rec(
        int(duration * samplerate),
        samplerate=samplerate,
        channels=1,
        dtype="int16",
    )
    sd.wait()
    wavfile.write(path, samplerate, frames)
    logger.info("[audio_recorder] saved to %s", path)
    return path
