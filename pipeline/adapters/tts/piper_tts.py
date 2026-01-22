"""
Piper TTS adapter using local piper-tts.

Free, local, high-quality TTS. Good for development iteration.

Requires:
    - piper-tts package: pip install piper-tts
    - ONNX model file (e.g., en_US-lessac-medium.onnx)
"""

import re
import subprocess
from pathlib import Path

from ..base import TTSAdapter


class PiperTTSError(Exception):
    """Exception raised when Piper TTS fails."""
    pass


class PiperTTSAdapter(TTSAdapter):
    """TTS adapter using local Piper TTS.

    Args:
        model_path: Path to .onnx model file
        ffmpeg_path: Path to ffmpeg binary (default: ~/.local/bin/ffmpeg)
    """

    def __init__(
        self,
        model_path: str | Path | None = None,
        ffmpeg_path: str | None = None
    ):
        # Default to bundled model
        if model_path is None:
            model_path = Path(__file__).parent.parent.parent.parent / "piper" / "piper" / "en_US-lessac-medium.onnx"
        self.model_path = Path(model_path)
        self._ffmpeg_path = ffmpeg_path or str(Path.home() / ".local" / "bin" / "ffmpeg")

        if not self.model_path.exists():
            raise PiperTTSError(f"Model not found: {self.model_path}")

    @property
    def name(self) -> str:
        return f"piper_{self.model_path.stem}"

    @property
    def output_extension(self) -> str:
        return ".wav"

    def generate(self, text: str, output_path: Path) -> Path:
        """Generate audio file from text using Piper."""
        if not text or not text.strip():
            raise PiperTTSError("Text cannot be empty")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "piper",
            "--model", str(self.model_path),
            "--output_file", str(output_path)
        ]

        try:
            result = subprocess.run(
                cmd,
                input=text,
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise PiperTTSError(f"Piper failed: {e.stderr}") from e
        except FileNotFoundError:
            raise PiperTTSError("piper command not found. Run: pip install piper-tts")

        if not output_path.exists():
            raise PiperTTSError(f"Audio file was not created at {output_path}")

        return output_path

    def get_duration(self, audio_path: Path) -> float:
        """Get duration of audio file in seconds using ffmpeg."""
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise PiperTTSError(f"Audio file not found: {audio_path}")

        cmd = [self._ffmpeg_path, "-i", str(audio_path), "-f", "null", "-"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            output = result.stderr
        except FileNotFoundError:
            raise PiperTTSError(f"ffmpeg not found at {self._ffmpeg_path}")

        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", output)
        if not match:
            raise PiperTTSError("Could not parse duration from ffmpeg output")

        hours, minutes, seconds = match.groups()
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
