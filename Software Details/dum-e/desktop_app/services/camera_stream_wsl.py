"""WSL / Ubuntu: same implementation as :mod:`camera_stream` (FFmpeg, buffer=1, safe read).

Use this import path in WSL-only deployments or to avoid path confusion; behavior is identical.
"""
from .camera_stream import CameraStream

__all__ = ["CameraStream"]
