"""WSL / Ubuntu: same as :class:`vision_runtime.VisionRuntime` (FFmpeg + low latency).

Re-export for WSL-tagged imports; use when mirroring a ROS/vision “node” on WSL.
"""
from .vision_runtime import VisionRuntime

__all__ = ["VisionRuntime"]
