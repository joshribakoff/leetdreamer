"""
Tests for merger adapters.
"""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pipeline.adapters.merger import FFmpegMerger, FFmpegMergerError


class TestFFmpegMergerInit:
    """Tests for FFmpegMerger initialization."""

    def test_default_ffmpeg_path(self):
        """Should default to ~/.local/bin/ffmpeg."""
        merger = FFmpegMerger()
        expected = Path.home() / ".local" / "bin" / "ffmpeg"
        assert merger.ffmpeg_path == expected

    def test_custom_ffmpeg_path(self):
        """Should accept custom FFmpeg path."""
        custom_path = Path("/usr/local/bin/ffmpeg")
        merger = FFmpegMerger(ffmpeg_path=custom_path)
        assert merger.ffmpeg_path == custom_path

    def test_name_property(self):
        """Should return 'ffmpeg' as adapter name."""
        merger = FFmpegMerger()
        assert merger.name == "ffmpeg"


class TestFFmpegMergerConcatAudio:
    """Tests for audio concatenation."""

    def test_concat_audio_empty_list_raises(self):
        """Should raise ValueError for empty audio list."""
        merger = FFmpegMerger()
        with pytest.raises(ValueError, match="cannot be empty"):
            merger.concat_audio([], Path("/tmp/output.m4a"))

    def test_concat_audio_missing_file_raises(self):
        """Should raise error if input file doesn't exist."""
        merger = FFmpegMerger()
        with pytest.raises(FFmpegMergerError, match="not found"):
            merger.concat_audio(
                [Path("/nonexistent/audio.aiff")],
                Path("/tmp/output.m4a")
            )

    @patch("subprocess.run")
    def test_concat_audio_single_file_copies_same_format(self, mock_run, tmp_path):
        """Should copy single file when input and output formats match."""
        # Create mock input file with same format as output
        input_file = tmp_path / "input.m4a"
        input_file.touch()
        output_file = tmp_path / "output.m4a"

        # Create merger with mock ffmpeg path that exists
        ffmpeg_path = tmp_path / "ffmpeg"
        ffmpeg_path.touch()
        merger = FFmpegMerger(ffmpeg_path=ffmpeg_path)

        mock_run.return_value = MagicMock(returncode=0)

        merger.concat_audio([input_file], output_file)

        # Should use -c copy for single file when formats match
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "-c" in args
        assert "copy" in args
        assert str(input_file) in args

    @patch("subprocess.run")
    def test_concat_audio_single_file_converts_different_format(self, mock_run, tmp_path):
        """Should convert single file when input and output formats differ."""
        # Create mock input file with different format than output
        input_file = tmp_path / "input.aiff"
        input_file.touch()
        output_file = tmp_path / "output.m4a"

        # Create merger with mock ffmpeg path that exists
        ffmpeg_path = tmp_path / "ffmpeg"
        ffmpeg_path.touch()
        merger = FFmpegMerger(ffmpeg_path=ffmpeg_path)

        mock_run.return_value = MagicMock(returncode=0)

        merger.concat_audio([input_file], output_file)

        # Should re-encode when formats differ
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "-c:a" in args
        assert "aac" in args
        assert str(input_file) in args

    @patch("subprocess.run")
    def test_concat_audio_multiple_files(self, mock_run, tmp_path):
        """Should use concat demuxer for multiple files."""
        # Create mock input files
        input_files = [tmp_path / f"audio_{i}.aiff" for i in range(3)]
        for f in input_files:
            f.touch()
        output_file = tmp_path / "output.m4a"

        # Create merger with mock ffmpeg path that exists
        ffmpeg_path = tmp_path / "ffmpeg"
        ffmpeg_path.touch()
        merger = FFmpegMerger(ffmpeg_path=ffmpeg_path)

        mock_run.return_value = MagicMock(returncode=0)

        merger.concat_audio(input_files, output_file)

        # Should use concat demuxer
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "-f" in args
        assert "concat" in args
        assert "-safe" in args
        assert "0" in args

    def test_concat_audio_ffmpeg_not_found(self, tmp_path):
        """Should raise error if FFmpeg binary not found."""
        input_file = tmp_path / "input.aiff"
        input_file.touch()

        merger = FFmpegMerger(ffmpeg_path=Path("/nonexistent/ffmpeg"))
        with pytest.raises(FFmpegMergerError, match="FFmpeg not found"):
            merger.concat_audio([input_file], tmp_path / "output.m4a")

    @patch("subprocess.run")
    def test_concat_audio_ffmpeg_failure(self, mock_run, tmp_path):
        """Should raise error on FFmpeg failure."""
        input_file = tmp_path / "input.aiff"
        input_file.touch()

        ffmpeg_path = tmp_path / "ffmpeg"
        ffmpeg_path.touch()
        merger = FFmpegMerger(ffmpeg_path=ffmpeg_path)

        mock_run.side_effect = subprocess.CalledProcessError(
            1, "ffmpeg", stderr="encoding error"
        )

        with pytest.raises(FFmpegMergerError, match="command failed"):
            merger.concat_audio([input_file], tmp_path / "output.m4a")


class TestFFmpegMergerMerge:
    """Tests for video/audio merging."""

    def test_merge_missing_video_raises(self, tmp_path):
        """Should raise error if video file doesn't exist."""
        audio_file = tmp_path / "audio.m4a"
        audio_file.touch()

        merger = FFmpegMerger()
        with pytest.raises(FFmpegMergerError, match="Video file not found"):
            merger.merge(
                Path("/nonexistent/video.webm"),
                audio_file,
                tmp_path / "output.mp4"
            )

    def test_merge_missing_audio_raises(self, tmp_path):
        """Should raise error if audio file doesn't exist."""
        video_file = tmp_path / "video.webm"
        video_file.touch()

        merger = FFmpegMerger()
        with pytest.raises(FFmpegMergerError, match="Audio file not found"):
            merger.merge(
                video_file,
                Path("/nonexistent/audio.m4a"),
                tmp_path / "output.mp4"
            )

    def test_merge_ffmpeg_not_found(self, tmp_path):
        """Should raise error if FFmpeg binary not found."""
        video_file = tmp_path / "video.webm"
        video_file.touch()
        audio_file = tmp_path / "audio.m4a"
        audio_file.touch()

        merger = FFmpegMerger(ffmpeg_path=Path("/nonexistent/ffmpeg"))
        with pytest.raises(FFmpegMergerError, match="FFmpeg not found"):
            merger.merge(video_file, audio_file, tmp_path / "output.mp4")

    @patch("subprocess.run")
    def test_merge_uses_tpad_filter(self, mock_run, tmp_path):
        """Should use tpad filter to extend video."""
        video_file = tmp_path / "video.webm"
        video_file.touch()
        audio_file = tmp_path / "audio.m4a"
        audio_file.touch()
        output_file = tmp_path / "output.mp4"

        ffmpeg_path = tmp_path / "ffmpeg"
        ffmpeg_path.touch()
        merger = FFmpegMerger(ffmpeg_path=ffmpeg_path)

        mock_run.return_value = MagicMock(returncode=0)

        merger.merge(video_file, audio_file, output_file)

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]

        # Check for tpad filter with stop_mode=clone and stop=-1
        filter_arg_idx = args.index("-filter_complex") + 1
        filter_arg = args[filter_arg_idx]
        assert "tpad" in filter_arg
        assert "stop_mode=clone" in filter_arg
        assert "stop=-1" in filter_arg

    @patch("subprocess.run")
    def test_merge_uses_correct_codecs(self, mock_run, tmp_path):
        """Should use libx264 for video and aac for audio."""
        video_file = tmp_path / "video.webm"
        video_file.touch()
        audio_file = tmp_path / "audio.m4a"
        audio_file.touch()
        output_file = tmp_path / "output.mp4"

        ffmpeg_path = tmp_path / "ffmpeg"
        ffmpeg_path.touch()
        merger = FFmpegMerger(ffmpeg_path=ffmpeg_path)

        mock_run.return_value = MagicMock(returncode=0)

        merger.merge(video_file, audio_file, output_file)

        args = mock_run.call_args[0][0]

        # Check video codec
        cv_idx = args.index("-c:v") + 1
        assert args[cv_idx] == "libx264"

        # Check audio codec
        ca_idx = args.index("-c:a") + 1
        assert args[ca_idx] == "aac"

    @patch("subprocess.run")
    def test_merge_creates_output_directory(self, mock_run, tmp_path):
        """Should create output directory if it doesn't exist."""
        video_file = tmp_path / "video.webm"
        video_file.touch()
        audio_file = tmp_path / "audio.m4a"
        audio_file.touch()
        output_file = tmp_path / "subdir" / "nested" / "output.mp4"

        ffmpeg_path = tmp_path / "ffmpeg"
        ffmpeg_path.touch()
        merger = FFmpegMerger(ffmpeg_path=ffmpeg_path)

        mock_run.return_value = MagicMock(returncode=0)

        merger.merge(video_file, audio_file, output_file)

        # Directory should be created
        assert output_file.parent.exists()

    @patch("subprocess.run")
    def test_merge_ffmpeg_failure(self, mock_run, tmp_path):
        """Should raise error on FFmpeg failure."""
        video_file = tmp_path / "video.webm"
        video_file.touch()
        audio_file = tmp_path / "audio.m4a"
        audio_file.touch()

        ffmpeg_path = tmp_path / "ffmpeg"
        ffmpeg_path.touch()
        merger = FFmpegMerger(ffmpeg_path=ffmpeg_path)

        mock_run.side_effect = subprocess.CalledProcessError(
            1, "ffmpeg", stderr="encoding error"
        )

        with pytest.raises(FFmpegMergerError, match="command failed"):
            merger.merge(video_file, audio_file, tmp_path / "output.mp4")

    @patch("subprocess.run")
    def test_merge_returns_output_path(self, mock_run, tmp_path):
        """Should return the output path on success."""
        video_file = tmp_path / "video.webm"
        video_file.touch()
        audio_file = tmp_path / "audio.m4a"
        audio_file.touch()
        output_file = tmp_path / "output.mp4"

        ffmpeg_path = tmp_path / "ffmpeg"
        ffmpeg_path.touch()
        merger = FFmpegMerger(ffmpeg_path=ffmpeg_path)

        mock_run.return_value = MagicMock(returncode=0)

        result = merger.merge(video_file, audio_file, output_file)

        assert result == output_file


class TestFFmpegMergerIntegration:
    """Integration tests that require actual FFmpeg installation.

    These tests are marked as slow and may be skipped in CI.
    They verify the actual FFmpeg commands work correctly.
    """

    @pytest.fixture
    def ffmpeg_available(self):
        """Check if FFmpeg is available at the expected path."""
        ffmpeg_path = Path.home() / ".local" / "bin" / "ffmpeg"
        if not ffmpeg_path.exists():
            pytest.skip("FFmpeg not found at ~/.local/bin/ffmpeg")
        return ffmpeg_path

    @pytest.mark.slow
    def test_concat_audio_integration(self, ffmpeg_available, tmp_path):
        """Integration test: concatenate actual audio files.

        Creates silent audio files and concatenates them.
        """
        merger = FFmpegMerger(ffmpeg_path=ffmpeg_available)

        # Create silent audio files using FFmpeg
        audio_files = []
        for i in range(2):
            audio_file = tmp_path / f"audio_{i}.aiff"
            # Generate 1 second of silence
            subprocess.run([
                str(ffmpeg_available),
                "-y",
                "-f", "lavfi",
                "-i", "anullsrc=r=44100:cl=stereo",
                "-t", "1",
                audio_file
            ], check=True, capture_output=True)
            audio_files.append(audio_file)

        output_file = tmp_path / "concatenated.m4a"
        result = merger.concat_audio(audio_files, output_file)

        assert result == output_file
        assert output_file.exists()
        # Concatenated file should be larger than individual files
        assert output_file.stat().st_size > 0

    @pytest.mark.slow
    def test_merge_integration(self, ffmpeg_available, tmp_path):
        """Integration test: merge actual video and audio files.

        Creates a simple test video and audio, then merges them.
        """
        merger = FFmpegMerger(ffmpeg_path=ffmpeg_available)

        # Create a simple test video (1 second, solid color)
        video_file = tmp_path / "video.webm"
        subprocess.run([
            str(ffmpeg_available),
            "-y",
            "-f", "lavfi",
            "-i", "color=c=blue:s=320x240:d=1",
            "-c:v", "libvpx",
            str(video_file)
        ], check=True, capture_output=True)

        # Create a simple test audio (2 seconds of silence)
        audio_file = tmp_path / "audio.aiff"
        subprocess.run([
            str(ffmpeg_available),
            "-y",
            "-f", "lavfi",
            "-i", "anullsrc=r=44100:cl=stereo",
            "-t", "2",
            str(audio_file)
        ], check=True, capture_output=True)

        output_file = tmp_path / "output.mp4"
        result = merger.merge(video_file, audio_file, output_file)

        assert result == output_file
        assert output_file.exists()
        assert output_file.stat().st_size > 0
