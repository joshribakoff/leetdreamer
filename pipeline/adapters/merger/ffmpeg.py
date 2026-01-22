"""
FFmpeg-based merger adapter for combining audio and video.

Uses FFmpeg for:
- Concatenating multiple audio files into one
- Merging video and audio with proper synchronization
- Extending video with frozen frames if audio is longer
"""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

from ..base import MergerAdapter

logger = logging.getLogger(__name__)


class FFmpegMergerError(Exception):
    """Exception raised when FFmpeg operations fail."""

    pass


class FFmpegMerger(MergerAdapter):
    """FFmpeg-based implementation of MergerAdapter.

    Uses FFmpeg to concatenate audio files and merge audio/video streams.
    If audio is longer than video, the video is extended by freezing the last frame.

    Args:
        ffmpeg_path: Path to the FFmpeg binary. Defaults to ~/.local/bin/ffmpeg
    """

    def __init__(self, ffmpeg_path: Optional[Path] = None):
        self._ffmpeg = ffmpeg_path or Path.home() / ".local" / "bin" / "ffmpeg"

    @property
    def name(self) -> str:
        """Adapter identifier for logging."""
        return "ffmpeg"

    @property
    def ffmpeg_path(self) -> Path:
        """Path to the FFmpeg binary."""
        return self._ffmpeg

    def _run_ffmpeg(self, args: List[str], description: str) -> subprocess.CompletedProcess:
        """Run an FFmpeg command with error handling.

        Args:
            args: List of arguments to pass to FFmpeg (not including ffmpeg itself)
            description: Human-readable description of the operation for logging

        Returns:
            CompletedProcess result

        Raises:
            FFmpegMergerError: If FFmpeg is not found or the command fails
        """
        if not self._ffmpeg.exists():
            raise FFmpegMergerError(f"FFmpeg not found at {self._ffmpeg}")

        cmd = [str(self._ffmpeg)] + args
        logger.info(f"{description}: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed: {e.stderr}")
            raise FFmpegMergerError(f"FFmpeg command failed: {e.stderr}") from e

    def _needs_encoding(self, input_paths: List[Path], output_path: Path) -> bool:
        """Check if encoding is needed based on file extensions.

        Stream copy (-c copy) only works when input and output formats are compatible.
        If the input format differs from the output format, we need to re-encode.

        Args:
            input_paths: List of input file paths
            output_path: Output file path

        Returns:
            True if re-encoding is needed, False if stream copy is possible
        """
        output_ext = output_path.suffix.lower()
        input_exts = {p.suffix.lower() for p in input_paths}

        # If all inputs have the same extension as output, try stream copy
        if len(input_exts) == 1 and input_exts.pop() == output_ext:
            return False

        # Different formats - need to encode
        return True

    def concat_audio(self, audio_paths: List[Path], output_path: Path) -> Path:
        """Concatenate multiple audio files into one.

        Uses FFmpeg's concat demuxer with a file list for efficient concatenation.
        If input and output formats differ, re-encodes to the output format.

        Args:
            audio_paths: List of paths to audio files to concatenate (in order)
            output_path: Path where the combined audio should be saved

        Returns:
            Path to the concatenated audio file

        Raises:
            FFmpegMergerError: If FFmpeg fails or input files don't exist
            ValueError: If audio_paths is empty
        """
        if not audio_paths:
            raise ValueError("audio_paths cannot be empty")

        # Validate all input files exist
        for path in audio_paths:
            if not path.exists():
                raise FFmpegMergerError(f"Audio file not found: {path}")

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine if we need to re-encode
        needs_encoding = self._needs_encoding(audio_paths, output_path)

        # If only one file, convert or copy it
        if len(audio_paths) == 1:
            if needs_encoding:
                logger.info(f"Single audio file, converting: {audio_paths[0]} -> {output_path}")
                args = [
                    "-y",  # Overwrite output
                    "-i", str(audio_paths[0]),
                    "-c:a", "aac",  # Re-encode to AAC for m4a output
                    str(output_path),
                ]
                self._run_ffmpeg(args, "Converting single audio file")
            else:
                logger.info(f"Single audio file, copying: {audio_paths[0]} -> {output_path}")
                args = [
                    "-y",  # Overwrite output
                    "-i", str(audio_paths[0]),
                    "-c", "copy",  # Stream copy (no re-encoding)
                    str(output_path),
                ]
                self._run_ffmpeg(args, "Copying single audio file")
            return output_path

        # Create a temporary file list for concat demuxer
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            filelist_path = Path(f.name)
            for path in audio_paths:
                # FFmpeg concat demuxer requires paths to be escaped
                escaped_path = str(path).replace("'", "'\\''")
                f.write(f"file '{escaped_path}'\n")

        try:
            # Use concat demuxer
            # -f concat: Use concat demuxer
            # -safe 0: Allow absolute paths
            if needs_encoding:
                # Re-encode when converting between formats
                args = [
                    "-y",  # Overwrite output
                    "-f", "concat",
                    "-safe", "0",
                    "-i", str(filelist_path),
                    "-c:a", "aac",  # Re-encode to AAC for m4a output
                    str(output_path),
                ]
            else:
                # Stream copy when formats match
                args = [
                    "-y",  # Overwrite output
                    "-f", "concat",
                    "-safe", "0",
                    "-i", str(filelist_path),
                    "-c", "copy",
                    str(output_path),
                ]
            self._run_ffmpeg(args, "Concatenating audio files")
        finally:
            # Clean up temp file
            filelist_path.unlink(missing_ok=True)

        return output_path

    def merge(self, video_path: Path, audio_path: Path, output_path: Path) -> Path:
        """Merge video and audio into a single file.

        If the audio is longer than the video, the video is extended by
        freezing (cloning) the last frame until the audio ends.

        Args:
            video_path: Path to the video file (e.g., .webm)
            audio_path: Path to the audio file (e.g., .m4a, .aiff)
            output_path: Path where the merged file should be saved (e.g., .mp4)

        Returns:
            Path to the merged video file

        Raises:
            FFmpegMergerError: If FFmpeg fails or input files don't exist
        """
        # Validate input files
        if not video_path.exists():
            raise FFmpegMergerError(f"Video file not found: {video_path}")
        if not audio_path.exists():
            raise FFmpegMergerError(f"Audio file not found: {audio_path}")

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Use tpad filter to extend video if audio is longer
        # stop_mode=clone: Freeze (clone) the last frame
        # stop=-1: Extend indefinitely (FFmpeg stops when shortest stream ends,
        #          which will be audio since we're extending video)
        #
        # The filter_complex:
        # [0:v]tpad=stop_mode=clone:stop=-1[v]
        # - [0:v]: Take video stream from first input
        # - tpad: Apply temporal padding
        # - [v]: Label the output as "v"
        #
        # Then we map:
        # - [v]: The padded video
        # - 1:a: Audio from second input
        #
        # Output codecs:
        # - libx264: H.264 video codec (widely compatible)
        # - aac: AAC audio codec (widely compatible)
        args = [
            "-y",  # Overwrite output
            "-i", str(video_path),
            "-i", str(audio_path),
            "-filter_complex", "[0:v]tpad=stop_mode=clone:stop=-1[v]",
            "-map", "[v]",
            "-map", "1:a",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",  # Stop when the shortest stream ends (audio, since video is extended indefinitely)
            str(output_path),
        ]
        self._run_ffmpeg(args, "Merging video and audio")

        return output_path

    def concat_videos(
        self,
        video_paths: List[Path],
        output_path: Path,
        transition: str = "cut"
    ) -> Path:
        """Concatenate multiple video files into one.

        Uses FFmpeg's concat demuxer for cuts or filter_complex for fades.

        Args:
            video_paths: List of paths to video files to concatenate (in order)
            output_path: Path where the combined video should be saved
            transition: Transition type ("cut" or "fade")

        Returns:
            Path to the concatenated video file

        Raises:
            FFmpegMergerError: If FFmpeg fails or input files don't exist
            ValueError: If video_paths is empty or transition is invalid
        """
        if not video_paths:
            raise ValueError("video_paths cannot be empty")

        if transition not in ("cut", "fade"):
            raise ValueError(f"Invalid transition: {transition}. Must be 'cut' or 'fade'")

        # Validate all input files exist
        for path in video_paths:
            if not path.exists():
                raise FFmpegMergerError(f"Video file not found: {path}")

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Single file - just copy/re-encode
        if len(video_paths) == 1:
            logger.info(f"Single video file, copying: {video_paths[0]} -> {output_path}")
            args = [
                "-y",
                "-i", str(video_paths[0]),
                "-c:v", "libx264",
                "-c:a", "aac",
                str(output_path),
            ]
            self._run_ffmpeg(args, "Copying single video file")
            return output_path

        if transition == "cut":
            return self._concat_videos_cut(video_paths, output_path)
        else:
            return self._concat_videos_fade(video_paths, output_path)

    def _concat_videos_cut(self, video_paths: List[Path], output_path: Path) -> Path:
        """Concatenate videos with hard cuts using concat demuxer."""
        # Create a temporary file list for concat demuxer
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            filelist_path = Path(f.name)
            for path in video_paths:
                escaped_path = str(path).replace("'", "'\\''")
                f.write(f"file '{escaped_path}'\n")

        try:
            args = [
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(filelist_path),
                "-c:v", "libx264",
                "-c:a", "aac",
                str(output_path),
            ]
            self._run_ffmpeg(args, "Concatenating videos with cut transition")
        finally:
            filelist_path.unlink(missing_ok=True)

        return output_path

    def _concat_videos_fade(
        self,
        video_paths: List[Path],
        output_path: Path,
        fade_duration: float = 0.5
    ) -> Path:
        """Concatenate videos with crossfade transitions using filter_complex."""
        n = len(video_paths)

        # Build input arguments
        input_args = []
        for path in video_paths:
            input_args.extend(["-i", str(path)])

        # Build filter_complex for crossfades
        # Each video gets labeled [v0], [a0], [v1], [a1], etc.
        # Then we chain xfade filters between consecutive clips
        filter_parts = []

        # For 2 videos: [0:v][1:v]xfade=transition=fade:duration=0.5[vout];[0:a][1:a]acrossfade=d=0.5[aout]
        # For 3+ videos: chain them together
        if n == 2:
            filter_complex = (
                f"[0:v][1:v]xfade=transition=fade:duration={fade_duration}[vout];"
                f"[0:a][1:a]acrossfade=d={fade_duration}[aout]"
            )
        else:
            # Chain multiple clips
            # Video chain
            v_filter = f"[0:v][1:v]xfade=transition=fade:duration={fade_duration}[v1]"
            for i in range(2, n):
                prev_label = f"v{i-1}"
                next_label = f"v{i}" if i < n - 1 else "vout"
                v_filter += f";[{prev_label}][{i}:v]xfade=transition=fade:duration={fade_duration}[{next_label}]"

            # Audio chain
            a_filter = f"[0:a][1:a]acrossfade=d={fade_duration}[a1]"
            for i in range(2, n):
                prev_label = f"a{i-1}"
                next_label = f"a{i}" if i < n - 1 else "aout"
                a_filter += f";[{prev_label}][{i}:a]acrossfade=d={fade_duration}[{next_label}]"

            filter_complex = f"{v_filter};{a_filter}"

        args = [
            "-y",
            *input_args,
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-map", "[aout]",
            "-c:v", "libx264",
            "-c:a", "aac",
            str(output_path),
        ]
        self._run_ffmpeg(args, "Concatenating videos with fade transition")

        return output_path
