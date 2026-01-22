"""
OpenAI TTS adapter using the OpenAI TTS API.

Uses the OpenAI text-to-speech API for high-quality audio generation
and ffmpeg for duration extraction.

Requires:
    - openai package: pip install openai
    - OPEN_API_KEY in ~/Projects/.env
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

from ..base import TTSAdapter

# Load .env from Projects root
load_dotenv(Path.home() / "Projects" / ".env")


class OpenAITTSError(Exception):
    """Exception raised when OpenAI TTS generation fails."""
    pass


Voice = Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
Model = Literal["tts-1", "tts-1-hd"]


class OpenAITTSAdapter(TTSAdapter):
    """TTS adapter using OpenAI TTS API.

    Args:
        voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer). Default: onyx
        model: Model to use (tts-1 for speed, tts-1-hd for quality). Default: tts-1-hd
        ffmpeg_path: Path to ffmpeg binary (default: ~/.local/bin/ffmpeg)
    """

    def __init__(
        self,
        voice: Voice = "onyx",
        model: Model = "tts-1-hd",
        ffmpeg_path: str | None = None
    ):
        self.voice = voice
        self.model = model
        self._ffmpeg_path = ffmpeg_path or str(Path.home() / ".local" / "bin" / "ffmpeg")
        self._client = None

    def _get_client(self):
        """Lazy-load OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise OpenAITTSError("openai package not installed. Run: pip install openai")

            api_key = os.environ.get("OPEN_API_KEY") or os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise OpenAITTSError("OPEN_API_KEY environment variable not set")

            self._client = OpenAI(api_key=api_key)
        return self._client

    @property
    def name(self) -> str:
        return f"openai_{self.model}_{self.voice}"

    def generate(self, text: str, output_path: Path) -> Path:
        """Generate audio file from text using OpenAI TTS API."""
        if not text or not text.strip():
            raise OpenAITTSError("Text cannot be empty")

        output_path = Path(output_path)
        # Force .mp3 extension for OpenAI output
        if output_path.suffix != ".mp3":
            output_path = output_path.with_suffix(".mp3")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        client = self._get_client()

        try:
            response = client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text
            )
            response.stream_to_file(output_path)
        except Exception as e:
            raise OpenAITTSError(f"OpenAI TTS API failed: {e}") from e

        if not output_path.exists():
            raise OpenAITTSError(f"Audio file was not created at {output_path}")

        return output_path

    def get_duration(self, audio_path: Path) -> float:
        """Get duration of audio file in seconds using ffmpeg."""
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise OpenAITTSError(f"Audio file not found: {audio_path}")

        cmd = [self._ffmpeg_path, "-i", str(audio_path), "-f", "null", "-"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            output = result.stderr
        except FileNotFoundError:
            raise OpenAITTSError(f"ffmpeg not found at {self._ffmpeg_path}")

        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", output)
        if not match:
            raise OpenAITTSError("Could not parse duration from ffmpeg output")

        hours, minutes, seconds = match.groups()
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
