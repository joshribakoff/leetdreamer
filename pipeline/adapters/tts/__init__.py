"""
TTS (Text-to-Speech) adapters.

Available adapters:
    - MacOSSayAdapter: Uses macOS `say` command (default)
    - OpenAITTSAdapter: Uses OpenAI TTS API
    - PiperTTSAdapter: Local Piper TTS (free, good quality)
"""

from .macos_say import MacOSSayAdapter, TTSError
from .openai_tts import OpenAITTSAdapter, OpenAITTSError
from .piper_tts import PiperTTSAdapter, PiperTTSError

__all__ = ["MacOSSayAdapter", "TTSError", "OpenAITTSAdapter", "OpenAITTSError", "PiperTTSAdapter", "PiperTTSError"]
