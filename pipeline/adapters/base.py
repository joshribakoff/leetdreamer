"""
Abstract base classes for pipeline adapters.

Defines the interfaces that all adapter implementations must follow.
This enables swappable implementations for TTS, animation, recording, and merging.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from ..schema import SceneSpec


class TTSAdapter(ABC):
    """Abstract base class for text-to-speech adapters.

    Implementations:
        - MacOSSay: Uses macOS `say` command
        - Piper: Uses Piper TTS (future)
        - OpenAI: Uses OpenAI TTS API (future)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Adapter identifier for logging."""
        pass

    @abstractmethod
    def generate(self, text: str, output_path: Path) -> Path:
        """Generate audio file from text.

        Args:
            text: The text to convert to speech
            output_path: Path where the audio file should be saved

        Returns:
            Path to the generated audio file
        """
        pass

    @abstractmethod
    def get_duration(self, audio_path: Path) -> float:
        """Get duration of audio file in seconds.

        Args:
            audio_path: Path to the audio file

        Returns:
            Duration in seconds
        """
        pass


class AnimationAdapter(ABC):
    """Abstract base class for animation rendering adapters.

    Implementations:
        - HTMLAnimation: Renders using HTML/CSS/JS with Playwright
        - ManimAnimation: Renders using Manim (future)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Adapter identifier for logging."""
        pass

    @abstractmethod
    def render(self, spec: SceneSpec, timing: List[float], output_path: Path) -> Path:
        """Render animation video from scene specification.

        Args:
            spec: The scene specification
            timing: List of durations in seconds for each step
            output_path: Path where the video should be saved

        Returns:
            Path to the rendered video file
        """
        pass


class RecorderAdapter(ABC):
    """Abstract base class for screen recording adapters.

    Used to capture HTML animations as video files.

    Implementations:
        - PlaywrightRecorder: Uses Playwright for headless recording
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Adapter identifier for logging."""
        pass

    @abstractmethod
    def record(self, html_path: Path, duration: float, output_path: Path) -> Path:
        """Record an HTML animation to video.

        Args:
            html_path: Path to the HTML file to record
            duration: Total duration to record in seconds
            output_path: Path where the video should be saved

        Returns:
            Path to the recorded video file
        """
        pass


class MergerAdapter(ABC):
    """Abstract base class for audio/video merging adapters.

    Implementations:
        - FFmpegMerger: Uses FFmpeg for merging and concatenation
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Adapter identifier for logging."""
        pass

    @abstractmethod
    def merge(self, video_path: Path, audio_path: Path, output_path: Path) -> Path:
        """Merge video and audio into a single file.

        Args:
            video_path: Path to the video file
            audio_path: Path to the audio file
            output_path: Path where the merged file should be saved

        Returns:
            Path to the merged video file
        """
        pass

    @abstractmethod
    def concat_audio(self, audio_paths: List[Path], output_path: Path) -> Path:
        """Concatenate multiple audio files into one.

        Args:
            audio_paths: List of paths to audio files to concatenate
            output_path: Path where the combined audio should be saved

        Returns:
            Path to the concatenated audio file
        """
        pass
