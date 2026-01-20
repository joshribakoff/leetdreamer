"""Pipeline adapters for TTS, animation, recording, and merging."""

from .base import TTSAdapter, AnimationAdapter, RecorderAdapter, MergerAdapter
from .animation import HTMLAnimationAdapter
from .recorder import PlaywrightRecorder

__all__ = [
    # Base classes
    "TTSAdapter",
    "AnimationAdapter",
    "RecorderAdapter",
    "MergerAdapter",
    # Animation adapters
    "HTMLAnimationAdapter",
    # Recorder adapters
    "PlaywrightRecorder",
]
