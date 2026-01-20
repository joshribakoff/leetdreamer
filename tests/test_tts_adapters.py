"""
Tests for TTS adapters.
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pipeline.adapters.tts import MacOSSayAdapter, TTSError


class TestMacOSSayAdapter:
    """Tests for MacOSSayAdapter."""

    @pytest.fixture
    def adapter(self) -> MacOSSayAdapter:
        """Create a MacOSSayAdapter instance."""
        return MacOSSayAdapter(voice="Samantha")

    @pytest.fixture
    def adapter_custom_voice(self) -> MacOSSayAdapter:
        """Create a MacOSSayAdapter with custom voice."""
        return MacOSSayAdapter(voice="Alex")

    def test_name_property(self, adapter: MacOSSayAdapter):
        """Name should include voice identifier."""
        assert adapter.name == "macos_say_Samantha"

    def test_name_with_custom_voice(self, adapter_custom_voice: MacOSSayAdapter):
        """Name should reflect custom voice."""
        assert adapter_custom_voice.name == "macos_say_Alex"

    def test_default_voice_is_samantha(self):
        """Default voice should be Samantha."""
        adapter = MacOSSayAdapter()
        assert adapter.voice == "Samantha"

    def test_custom_ffprobe_path(self):
        """Should accept custom ffprobe path."""
        adapter = MacOSSayAdapter(ffprobe_path="/custom/path/ffprobe")
        assert adapter._ffprobe_path == "/custom/path/ffprobe"

    def test_default_ffprobe_path(self, adapter: MacOSSayAdapter):
        """Default ffprobe path should be in ~/.local/bin."""
        expected = str(Path.home() / ".local" / "bin" / "ffprobe")
        assert adapter._ffprobe_path == expected


class TestMacOSSayAdapterGenerate:
    """Tests for MacOSSayAdapter.generate()."""

    @pytest.fixture
    def adapter(self) -> MacOSSayAdapter:
        """Create a MacOSSayAdapter instance."""
        return MacOSSayAdapter()

    def test_generate_empty_text_raises_error(self, adapter: MacOSSayAdapter, tmp_path: Path):
        """Should raise TTSError for empty text."""
        output_path = tmp_path / "empty.aiff"
        with pytest.raises(TTSError, match="Text cannot be empty"):
            adapter.generate("", output_path)

    def test_generate_whitespace_only_raises_error(self, adapter: MacOSSayAdapter, tmp_path: Path):
        """Should raise TTSError for whitespace-only text."""
        output_path = tmp_path / "whitespace.aiff"
        with pytest.raises(TTSError, match="Text cannot be empty"):
            adapter.generate("   ", output_path)

    @patch("subprocess.run")
    def test_generate_calls_say_command(self, mock_run: MagicMock, adapter: MacOSSayAdapter, tmp_path: Path):
        """Should call say command with correct arguments."""
        output_path = tmp_path / "test.aiff"
        # Create the file to simulate say command success
        mock_run.return_value = MagicMock(returncode=0)

        # We need the file to exist after the call
        def create_file(*args, **kwargs):
            output_path.touch()
            return MagicMock(returncode=0)

        mock_run.side_effect = create_file

        adapter.generate("Hello world", output_path)

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "say"
        assert "-v" in call_args
        assert "Samantha" in call_args
        assert "-o" in call_args
        assert str(output_path) in call_args
        assert "Hello world" in call_args

    @patch("subprocess.run")
    def test_generate_creates_output_directory(self, mock_run: MagicMock, adapter: MacOSSayAdapter, tmp_path: Path):
        """Should create output directory if it doesn't exist."""
        nested_path = tmp_path / "nested" / "dir" / "output.aiff"

        def create_file(*args, **kwargs):
            nested_path.touch()
            return MagicMock(returncode=0)

        mock_run.side_effect = create_file

        adapter.generate("Test", nested_path)

        assert nested_path.parent.exists()

    @patch("subprocess.run")
    def test_generate_returns_output_path(self, mock_run: MagicMock, adapter: MacOSSayAdapter, tmp_path: Path):
        """Should return the output path on success."""
        output_path = tmp_path / "test.aiff"

        def create_file(*args, **kwargs):
            output_path.touch()
            return MagicMock(returncode=0)

        mock_run.side_effect = create_file

        result = adapter.generate("Test text", output_path)

        assert result == output_path

    @patch("subprocess.run")
    def test_generate_raises_on_say_failure(self, mock_run: MagicMock, adapter: MacOSSayAdapter, tmp_path: Path):
        """Should raise TTSError when say command fails."""
        output_path = tmp_path / "test.aiff"
        mock_run.side_effect = subprocess.CalledProcessError(1, "say", stderr="Voice not found")

        with pytest.raises(TTSError, match="say command failed"):
            adapter.generate("Test", output_path)

    @patch("subprocess.run")
    def test_generate_raises_on_missing_say_command(self, mock_run: MagicMock, adapter: MacOSSayAdapter, tmp_path: Path):
        """Should raise TTSError when say command is not found."""
        output_path = tmp_path / "test.aiff"
        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(TTSError, match="say command not found"):
            adapter.generate("Test", output_path)

    @patch("subprocess.run")
    def test_generate_raises_when_file_not_created(self, mock_run: MagicMock, adapter: MacOSSayAdapter, tmp_path: Path):
        """Should raise TTSError when output file is not created."""
        output_path = tmp_path / "test.aiff"
        mock_run.return_value = MagicMock(returncode=0)
        # Don't create the file - simulates say command bug

        with pytest.raises(TTSError, match="Audio file was not created"):
            adapter.generate("Test", output_path)


class TestMacOSSayAdapterGetDuration:
    """Tests for MacOSSayAdapter.get_duration()."""

    @pytest.fixture
    def adapter(self) -> MacOSSayAdapter:
        """Create a MacOSSayAdapter instance."""
        return MacOSSayAdapter()

    def test_get_duration_file_not_found(self, adapter: MacOSSayAdapter, tmp_path: Path):
        """Should raise TTSError for non-existent file."""
        fake_path = tmp_path / "nonexistent.aiff"
        with pytest.raises(TTSError, match="Audio file not found"):
            adapter.get_duration(fake_path)

    @patch("subprocess.run")
    def test_get_duration_calls_ffprobe(self, mock_run: MagicMock, adapter: MacOSSayAdapter, tmp_path: Path):
        """Should call ffprobe with correct arguments."""
        audio_path = tmp_path / "test.aiff"
        audio_path.touch()

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"format": {"duration": "2.5"}}'
        )

        adapter.get_duration(audio_path)

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert adapter._ffprobe_path in call_args
        assert "-v" in call_args
        assert "quiet" in call_args
        assert "-print_format" in call_args
        assert "json" in call_args
        assert "-show_format" in call_args
        assert str(audio_path) in call_args

    @patch("subprocess.run")
    def test_get_duration_returns_float(self, mock_run: MagicMock, adapter: MacOSSayAdapter, tmp_path: Path):
        """Should return duration as float."""
        audio_path = tmp_path / "test.aiff"
        audio_path.touch()

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"format": {"duration": "3.14159"}}'
        )

        duration = adapter.get_duration(audio_path)

        assert isinstance(duration, float)
        assert duration == pytest.approx(3.14159)

    @patch("subprocess.run")
    def test_get_duration_raises_on_ffprobe_failure(self, mock_run: MagicMock, adapter: MacOSSayAdapter, tmp_path: Path):
        """Should raise TTSError when ffprobe fails."""
        audio_path = tmp_path / "test.aiff"
        audio_path.touch()

        mock_run.side_effect = subprocess.CalledProcessError(1, "ffprobe", stderr="Invalid file")

        with pytest.raises(TTSError, match="ffprobe failed"):
            adapter.get_duration(audio_path)

    @patch("subprocess.run")
    def test_get_duration_raises_on_missing_ffprobe(self, mock_run: MagicMock, adapter: MacOSSayAdapter, tmp_path: Path):
        """Should raise TTSError when ffprobe is not found."""
        audio_path = tmp_path / "test.aiff"
        audio_path.touch()

        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(TTSError, match="ffprobe not found"):
            adapter.get_duration(audio_path)

    @patch("subprocess.run")
    def test_get_duration_raises_on_invalid_json(self, mock_run: MagicMock, adapter: MacOSSayAdapter, tmp_path: Path):
        """Should raise TTSError on invalid JSON output."""
        audio_path = tmp_path / "test.aiff"
        audio_path.touch()

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="not valid json"
        )

        with pytest.raises(TTSError, match="Failed to parse"):
            adapter.get_duration(audio_path)

    @patch("subprocess.run")
    def test_get_duration_raises_on_missing_duration_key(self, mock_run: MagicMock, adapter: MacOSSayAdapter, tmp_path: Path):
        """Should raise TTSError when duration key is missing."""
        audio_path = tmp_path / "test.aiff"
        audio_path.touch()

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"format": {}}'
        )

        with pytest.raises(TTSError, match="Failed to parse"):
            adapter.get_duration(audio_path)


class TestMacOSSayAdapterIntegration:
    """Integration tests that actually call macOS say command.

    These tests are skipped if not running on macOS or if say/ffprobe are unavailable.
    """

    @pytest.fixture
    def adapter(self) -> MacOSSayAdapter:
        """Create a MacOSSayAdapter instance."""
        return MacOSSayAdapter()

    @pytest.fixture
    def skip_if_not_macos(self):
        """Skip test if not running on macOS."""
        import platform
        if platform.system() != "Darwin":
            pytest.skip("macOS only test")

    @pytest.fixture
    def skip_if_no_ffprobe(self, adapter: MacOSSayAdapter):
        """Skip test if ffprobe is not available."""
        if not Path(adapter._ffprobe_path).exists():
            pytest.skip(f"ffprobe not found at {adapter._ffprobe_path}")

    def test_generate_creates_audio_file(
        self,
        skip_if_not_macos,
        adapter: MacOSSayAdapter,
        tmp_path: Path
    ):
        """Integration test: generate() should create an actual audio file."""
        output_path = tmp_path / "integration_test.aiff"

        result = adapter.generate("Hello, this is a test.", output_path)

        assert result.exists()
        assert result.stat().st_size > 0

    def test_get_duration_returns_positive_float(
        self,
        skip_if_not_macos,
        skip_if_no_ffprobe,
        adapter: MacOSSayAdapter,
        tmp_path: Path
    ):
        """Integration test: get_duration() should return a positive float."""
        output_path = tmp_path / "duration_test.aiff"
        adapter.generate("This is a test for duration.", output_path)

        duration = adapter.get_duration(output_path)

        assert isinstance(duration, float)
        assert duration > 0

    def test_full_workflow(
        self,
        skip_if_not_macos,
        skip_if_no_ffprobe,
        adapter: MacOSSayAdapter,
        tmp_path: Path
    ):
        """Integration test: full workflow from text to duration."""
        output_path = tmp_path / "workflow_test.aiff"
        text = "We start with two pointers at each end of the sorted array."

        # Generate audio
        audio_path = adapter.generate(text, output_path)

        # Get duration
        duration = adapter.get_duration(audio_path)

        # Verify
        assert audio_path.exists()
        assert duration > 1.0  # Should be at least a second for this text
        assert duration < 10.0  # But not too long
