"""
TTS (Text-to-Speech) adapters.

Available adapters:
    - MacOSSayAdapter: Uses macOS `say` command (default)
"""

from .macos_say import MacOSSayAdapter, TTSError

__all__ = ["MacOSSayAdapter", "TTSError"]
