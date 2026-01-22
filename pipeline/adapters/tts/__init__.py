"""
TTS (Text-to-Speech) adapters.

Available adapters:
    - MacOSSayAdapter: Uses macOS `say` command (default)
    - OpenAITTSAdapter: Uses OpenAI TTS API
"""

from .macos_say import MacOSSayAdapter, TTSError
from .openai_tts import OpenAITTSAdapter, OpenAITTSError

__all__ = ["MacOSSayAdapter", "TTSError", "OpenAITTSAdapter", "OpenAITTSError"]
