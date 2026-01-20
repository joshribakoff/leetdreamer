"""
macOS TTS adapter using the `say` command.

Uses the built-in macOS `say` command for text-to-speech generation
and ffmpeg for duration extraction.
"""

import re
import subprocess
from pathlib import Path

from ..base import TTSAdapter


class TTSError(Exception):
    """Exception raised when TTS generation fails."""
    pass


class MacOSSayAdapter(TTSAdapter):
    """TTS adapter using macOS `say` command.

    Generates audio files using the built-in macOS text-to-speech engine.

    Args:
        voice: The voice to use (default: "Samantha")
        ffmpeg_path: Path to ffmpeg binary (default: ~/.local/bin/ffmpeg)

    Example:
        >>> adapter = MacOSSayAdapter(voice="Samantha")
        >>> audio_path = adapter.generate("Hello world", Path("output.aiff"))
        >>> duration = adapter.get_duration(audio_path)
    """

    def __init__(self, voice: str = "Samantha", ffmpeg_path: str | None = None):
        self.voice = voice
        self._ffmpeg_path = ffmpeg_path or str(Path.home() / ".local" / "bin" / "ffmpeg")

    @property
    def name(self) -> str:
        """Adapter identifier for logging."""
        return f"macos_say_{self.voice}"

    def generate(self, text: str, output_path: Path) -> Path:
        """Generate audio file from text using macOS say command.

        Args:
            text: The text to convert to speech
            output_path: Path where the audio file should be saved (should end in .aiff)

        Returns:
            Path to the generated audio file

        Raises:
            TTSError: If text is empty or audio generation fails
        """
        if not text or not text.strip():
            raise TTSError("Text cannot be empty")

        # Ensure output directory exists
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build the say command
        cmd = [
            "say",
            "-v", self.voice,
            "-o", str(output_path),
            text
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise TTSError(f"say command failed: {e.stderr}") from e
        except FileNotFoundError:
            raise TTSError("macOS say command not found. This adapter requires macOS.")

        # Verify the file was created
        if not output_path.exists():
            raise TTSError(f"Audio file was not created at {output_path}")

        return output_path

    def get_duration(self, audio_path: Path) -> float:
        """Get duration of audio file in seconds using ffmpeg.

        Args:
            audio_path: Path to the audio file

        Returns:
            Duration in seconds

        Raises:
            TTSError: If the file doesn't exist or ffmpeg fails
        """
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise TTSError(f"Audio file not found: {audio_path}")

        # Use ffmpeg -i to get duration from stderr
        cmd = [
            self._ffmpeg_path,
            "-i", str(audio_path),
            "-f", "null", "-"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            # ffmpeg outputs info to stderr
            output = result.stderr
        except FileNotFoundError:
            raise TTSError(f"ffmpeg not found at {self._ffmpeg_path}")

        # Parse duration from output: "Duration: 00:00:05.46, start: ..."
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", output)
        if not match:
            raise TTSError(f"Could not parse duration from ffmpeg output")

        hours, minutes, seconds = match.groups()
        duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)

        return duration
