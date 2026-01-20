"""
Tests for the Pipeline Orchestrator.

Tests the full pipeline with mocked adapters and integration tests
with a minimal scene.
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from pipeline.orchestrator import PipelineOrchestrator, BuildResult, PipelineError
from pipeline.schema import SceneSpec, Step, StepState, VisualizationConfig
from pipeline.adapters.base import TTSAdapter, AnimationAdapter, RecorderAdapter, MergerAdapter


# Fixtures

@pytest.fixture
def sample_scene_spec():
    """Create a minimal scene spec for testing."""
    return SceneSpec(
        id="test_scene",
        title="Test Scene",
        description="A test scene for unit testing",
        visualization=VisualizationConfig(
            type="array_pointers",
            config={"array": [1, 2, 3], "target": 3}
        ),
        steps=[
            Step(
                id="step1",
                narration="This is step one.",
                state=StepState(left=0, right=2, message="Step 1")
            ),
            Step(
                id="step2",
                narration="This is step two.",
                state=StepState(left=1, right=2, message="Step 2")
            ),
        ]
    )


@pytest.fixture
def sample_scene_json(sample_scene_spec):
    """Create a temporary scene.json file."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        delete=False
    ) as f:
        scene_dict = sample_scene_spec.model_dump()
        json.dump(scene_dict, f)
        return Path(f.name)


@pytest.fixture
def mock_tts():
    """Create a mock TTS adapter."""
    mock = Mock(spec=TTSAdapter)
    mock.name = "mock_tts"

    def mock_generate(text, output_path):
        # Create a dummy file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("dummy audio")
        return output_path

    mock.generate.side_effect = mock_generate
    mock.get_duration.return_value = 2.0  # 2 seconds per step
    return mock


@pytest.fixture
def mock_animation():
    """Create a mock animation adapter."""
    mock = Mock(spec=AnimationAdapter)
    mock.name = "mock_animation"

    def mock_render(spec, timing, output_path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("<html>dummy</html>")
        return output_path

    mock.render.side_effect = mock_render
    return mock


@pytest.fixture
def mock_recorder():
    """Create a mock recorder adapter."""
    mock = Mock(spec=RecorderAdapter)
    mock.name = "mock_recorder"

    def mock_record(html_path, duration, output_path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"dummy video")
        return output_path

    mock.record.side_effect = mock_record
    return mock


@pytest.fixture
def mock_merger():
    """Create a mock merger adapter."""
    mock = Mock(spec=MergerAdapter)
    mock.name = "mock_merger"

    def mock_concat(audio_paths, output_path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"dummy concat audio")
        return output_path

    def mock_merge(video_path, audio_path, output_path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"dummy merged video")
        return output_path

    mock.concat_audio.side_effect = mock_concat
    mock.merge.side_effect = mock_merge
    return mock


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestBuildResult:
    """Tests for BuildResult dataclass."""

    def test_build_result_success(self):
        """Test creating a successful build result."""
        result = BuildResult(
            scene_id="test",
            output_path=Path("/output/test/final.mp4"),
            timing=[1.0, 2.0, 3.0],
            total_duration=6.0,
            success=True
        )
        assert result.success
        assert result.scene_id == "test"
        assert result.total_duration == 6.0
        assert len(result.timing) == 3
        assert result.error is None

    def test_build_result_failure(self):
        """Test creating a failed build result."""
        result = BuildResult(
            scene_id="test",
            output_path=Path("/output/test/final.mp4"),
            timing=[],
            total_duration=0.0,
            success=False,
            error="TTS failed"
        )
        assert not result.success
        assert result.error == "TTS failed"


class TestPipelineOrchestrator:
    """Tests for PipelineOrchestrator class."""

    def test_init(self, mock_tts, mock_animation, mock_recorder, mock_merger, temp_output_dir):
        """Test orchestrator initialization."""
        orchestrator = PipelineOrchestrator(
            tts=mock_tts,
            animation=mock_animation,
            recorder=mock_recorder,
            merger=mock_merger,
            output_dir=temp_output_dir
        )
        assert orchestrator.tts == mock_tts
        assert orchestrator.animation == mock_animation
        assert orchestrator.recorder == mock_recorder
        assert orchestrator.merger == mock_merger
        assert orchestrator.output_dir == temp_output_dir

    def test_build_creates_output_directory(
        self, mock_tts, mock_animation, mock_recorder, mock_merger,
        temp_output_dir, sample_scene_spec
    ):
        """Test that build creates the output directory."""
        orchestrator = PipelineOrchestrator(
            tts=mock_tts,
            animation=mock_animation,
            recorder=mock_recorder,
            merger=mock_merger,
            output_dir=temp_output_dir
        )

        result = orchestrator.build(sample_scene_spec)

        scene_dir = temp_output_dir / sample_scene_spec.id
        assert scene_dir.exists()
        assert scene_dir.is_dir()

    def test_build_generates_tts_for_each_step(
        self, mock_tts, mock_animation, mock_recorder, mock_merger,
        temp_output_dir, sample_scene_spec
    ):
        """Test that build generates TTS audio for each step."""
        orchestrator = PipelineOrchestrator(
            tts=mock_tts,
            animation=mock_animation,
            recorder=mock_recorder,
            merger=mock_merger,
            output_dir=temp_output_dir
        )

        result = orchestrator.build(sample_scene_spec)

        # TTS generate called for each step
        assert mock_tts.generate.call_count == len(sample_scene_spec.steps)

        # Check narration texts were passed
        call_args = [call[0][0] for call in mock_tts.generate.call_args_list]
        assert "This is step one." in call_args
        assert "This is step two." in call_args

    def test_build_extracts_durations(
        self, mock_tts, mock_animation, mock_recorder, mock_merger,
        temp_output_dir, sample_scene_spec
    ):
        """Test that build extracts durations from audio files."""
        mock_tts.get_duration.side_effect = [1.5, 2.5]  # Different durations

        orchestrator = PipelineOrchestrator(
            tts=mock_tts,
            animation=mock_animation,
            recorder=mock_recorder,
            merger=mock_merger,
            output_dir=temp_output_dir
        )

        result = orchestrator.build(sample_scene_spec)

        assert result.timing == [1.5, 2.5]
        assert result.total_duration == 4.0

    def test_build_renders_animation(
        self, mock_tts, mock_animation, mock_recorder, mock_merger,
        temp_output_dir, sample_scene_spec
    ):
        """Test that build renders the animation HTML."""
        orchestrator = PipelineOrchestrator(
            tts=mock_tts,
            animation=mock_animation,
            recorder=mock_recorder,
            merger=mock_merger,
            output_dir=temp_output_dir
        )

        result = orchestrator.build(sample_scene_spec)

        mock_animation.render.assert_called_once()
        call_args = mock_animation.render.call_args
        assert call_args[0][0] == sample_scene_spec  # scene spec
        assert call_args[0][1] == [2.0, 2.0]  # timing (mocked)

    def test_build_records_video(
        self, mock_tts, mock_animation, mock_recorder, mock_merger,
        temp_output_dir, sample_scene_spec
    ):
        """Test that build records the animation to video."""
        orchestrator = PipelineOrchestrator(
            tts=mock_tts,
            animation=mock_animation,
            recorder=mock_recorder,
            merger=mock_merger,
            output_dir=temp_output_dir
        )

        result = orchestrator.build(sample_scene_spec)

        mock_recorder.record.assert_called_once()
        call_args = mock_recorder.record.call_args
        assert call_args[0][1] == 4.0  # total duration

    def test_build_concatenates_audio(
        self, mock_tts, mock_animation, mock_recorder, mock_merger,
        temp_output_dir, sample_scene_spec
    ):
        """Test that build concatenates audio segments."""
        orchestrator = PipelineOrchestrator(
            tts=mock_tts,
            animation=mock_animation,
            recorder=mock_recorder,
            merger=mock_merger,
            output_dir=temp_output_dir
        )

        result = orchestrator.build(sample_scene_spec)

        mock_merger.concat_audio.assert_called_once()
        call_args = mock_merger.concat_audio.call_args
        assert len(call_args[0][0]) == 2  # Two audio files

    def test_build_merges_video_and_audio(
        self, mock_tts, mock_animation, mock_recorder, mock_merger,
        temp_output_dir, sample_scene_spec
    ):
        """Test that build merges video and audio."""
        orchestrator = PipelineOrchestrator(
            tts=mock_tts,
            animation=mock_animation,
            recorder=mock_recorder,
            merger=mock_merger,
            output_dir=temp_output_dir
        )

        result = orchestrator.build(sample_scene_spec)

        mock_merger.merge.assert_called_once()

    def test_build_saves_timing_json(
        self, mock_tts, mock_animation, mock_recorder, mock_merger,
        temp_output_dir, sample_scene_spec
    ):
        """Test that build saves timing.json."""
        orchestrator = PipelineOrchestrator(
            tts=mock_tts,
            animation=mock_animation,
            recorder=mock_recorder,
            merger=mock_merger,
            output_dir=temp_output_dir
        )

        result = orchestrator.build(sample_scene_spec)

        timing_path = temp_output_dir / sample_scene_spec.id / "timing.json"
        assert timing_path.exists()

        timing_data = json.loads(timing_path.read_text())
        assert timing_data["scene_id"] == sample_scene_spec.id
        assert timing_data["total_duration"] == 4.0
        assert len(timing_data["steps"]) == 2

    def test_build_returns_success_result(
        self, mock_tts, mock_animation, mock_recorder, mock_merger,
        temp_output_dir, sample_scene_spec
    ):
        """Test that successful build returns success result."""
        orchestrator = PipelineOrchestrator(
            tts=mock_tts,
            animation=mock_animation,
            recorder=mock_recorder,
            merger=mock_merger,
            output_dir=temp_output_dir
        )

        result = orchestrator.build(sample_scene_spec)

        assert result.success
        assert result.scene_id == sample_scene_spec.id
        assert result.error is None
        assert "final" in result.intermediate_files

    def test_build_handles_tts_error(
        self, mock_tts, mock_animation, mock_recorder, mock_merger,
        temp_output_dir, sample_scene_spec
    ):
        """Test that build handles TTS errors gracefully."""
        mock_tts.generate.side_effect = Exception("TTS failed")

        orchestrator = PipelineOrchestrator(
            tts=mock_tts,
            animation=mock_animation,
            recorder=mock_recorder,
            merger=mock_merger,
            output_dir=temp_output_dir
        )

        result = orchestrator.build(sample_scene_spec)

        assert not result.success
        assert "TTS failed" in result.error

    def test_build_handles_recorder_error(
        self, mock_tts, mock_animation, mock_recorder, mock_merger,
        temp_output_dir, sample_scene_spec
    ):
        """Test that build handles recorder errors gracefully."""
        mock_recorder.record.side_effect = Exception("Recording failed")

        orchestrator = PipelineOrchestrator(
            tts=mock_tts,
            animation=mock_animation,
            recorder=mock_recorder,
            merger=mock_merger,
            output_dir=temp_output_dir
        )

        result = orchestrator.build(sample_scene_spec)

        assert not result.success
        assert "Recording failed" in result.error

    def test_build_handles_merger_error(
        self, mock_tts, mock_animation, mock_recorder, mock_merger,
        temp_output_dir, sample_scene_spec
    ):
        """Test that build handles merger errors gracefully."""
        mock_merger.merge.side_effect = Exception("Merge failed")

        orchestrator = PipelineOrchestrator(
            tts=mock_tts,
            animation=mock_animation,
            recorder=mock_recorder,
            merger=mock_merger,
            output_dir=temp_output_dir
        )

        result = orchestrator.build(sample_scene_spec)

        assert not result.success
        assert "Merge failed" in result.error

    def test_dry_run_mode(
        self, mock_tts, mock_animation, mock_recorder, mock_merger,
        temp_output_dir, sample_scene_spec
    ):
        """Test dry run mode validates without building."""
        orchestrator = PipelineOrchestrator(
            tts=mock_tts,
            animation=mock_animation,
            recorder=mock_recorder,
            merger=mock_merger,
            output_dir=temp_output_dir
        )

        result = orchestrator.build(sample_scene_spec, dry_run=True)

        assert result.success
        assert result.timing == []
        assert result.total_duration == 0.0

        # No adapters should be called in dry run
        mock_tts.generate.assert_not_called()
        mock_animation.render.assert_not_called()
        mock_recorder.record.assert_not_called()
        mock_merger.merge.assert_not_called()


class TestBuildFromFile:
    """Tests for build_from_file method."""

    def test_build_from_file_loads_scene(
        self, mock_tts, mock_animation, mock_recorder, mock_merger,
        temp_output_dir, sample_scene_json
    ):
        """Test that build_from_file loads and builds scene."""
        orchestrator = PipelineOrchestrator(
            tts=mock_tts,
            animation=mock_animation,
            recorder=mock_recorder,
            merger=mock_merger,
            output_dir=temp_output_dir
        )

        result = orchestrator.build_from_file(sample_scene_json)

        assert result.success
        assert result.scene_id == "test_scene"

    def test_build_from_file_not_found(
        self, mock_tts, mock_animation, mock_recorder, mock_merger,
        temp_output_dir
    ):
        """Test that build_from_file raises error for missing file."""
        orchestrator = PipelineOrchestrator(
            tts=mock_tts,
            animation=mock_animation,
            recorder=mock_recorder,
            merger=mock_merger,
            output_dir=temp_output_dir
        )

        with pytest.raises(PipelineError, match="not found"):
            orchestrator.build_from_file(Path("/nonexistent/scene.json"))

    def test_build_from_file_invalid_json(
        self, mock_tts, mock_animation, mock_recorder, mock_merger,
        temp_output_dir
    ):
        """Test that build_from_file raises error for invalid JSON."""
        # Create a file with invalid JSON
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json {")
            invalid_path = Path(f.name)

        orchestrator = PipelineOrchestrator(
            tts=mock_tts,
            animation=mock_animation,
            recorder=mock_recorder,
            merger=mock_merger,
            output_dir=temp_output_dir
        )

        with pytest.raises(PipelineError, match="Invalid JSON"):
            orchestrator.build_from_file(invalid_path)

    def test_build_from_file_invalid_schema(
        self, mock_tts, mock_animation, mock_recorder, mock_merger,
        temp_output_dir
    ):
        """Test that build_from_file raises error for invalid schema."""
        # Create a file with valid JSON but invalid schema
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"not": "a valid scene"}, f)
            invalid_path = Path(f.name)

        orchestrator = PipelineOrchestrator(
            tts=mock_tts,
            animation=mock_animation,
            recorder=mock_recorder,
            merger=mock_merger,
            output_dir=temp_output_dir
        )

        with pytest.raises(PipelineError, match="Failed to parse"):
            orchestrator.build_from_file(invalid_path)

    def test_build_from_file_dry_run(
        self, mock_tts, mock_animation, mock_recorder, mock_merger,
        temp_output_dir, sample_scene_json
    ):
        """Test dry run from file."""
        orchestrator = PipelineOrchestrator(
            tts=mock_tts,
            animation=mock_animation,
            recorder=mock_recorder,
            merger=mock_merger,
            output_dir=temp_output_dir
        )

        result = orchestrator.build_from_file_dry_run(sample_scene_json)

        assert result.success
        mock_tts.generate.assert_not_called()


class TestIntegration:
    """Integration tests with real adapters (marked as slow)."""

    @pytest.mark.slow
    def test_full_pipeline_with_fixture(self, temp_output_dir):
        """Test full pipeline with the sample fixture.

        This test requires:
        - macOS (for say command)
        - ffprobe and ffmpeg installed
        - Playwright browsers installed

        Skip if dependencies are not available.
        """
        import subprocess
        import shutil

        # Check for dependencies
        if shutil.which("say") is None:
            pytest.skip("macOS say command not available")

        ffprobe = Path.home() / ".local" / "bin" / "ffprobe"
        if not ffprobe.exists():
            pytest.skip("ffprobe not found at ~/.local/bin/ffprobe")

        ffmpeg = Path.home() / ".local" / "bin" / "ffmpeg"
        if not ffmpeg.exists():
            pytest.skip("ffmpeg not found at ~/.local/bin/ffmpeg")

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            pytest.skip("Playwright not installed")

        # Load fixture
        fixture_path = Path(__file__).parent / "fixtures" / "sample_scene.json"
        if not fixture_path.exists():
            pytest.skip("Sample fixture not found")

        # Import real adapters
        from pipeline.adapters.tts import MacOSSayAdapter
        from pipeline.adapters.animation import HTMLAnimationAdapter
        from pipeline.adapters.recorder import PlaywrightRecorder
        from pipeline.adapters.merger import FFmpegMerger

        # Create adapters
        templates_dir = Path(__file__).parent.parent / "templates"
        tts = MacOSSayAdapter()
        animation = HTMLAnimationAdapter(templates_dir)
        recorder = PlaywrightRecorder()
        merger = FFmpegMerger()

        # Create orchestrator
        orchestrator = PipelineOrchestrator(
            tts=tts,
            animation=animation,
            recorder=recorder,
            merger=merger,
            output_dir=temp_output_dir
        )

        # Build
        result = orchestrator.build_from_file(fixture_path)

        # Verify result
        assert result.success, f"Build failed: {result.error}"
        assert result.output_path.exists()
        assert len(result.timing) == 3  # Sample fixture has 3 steps
        assert result.total_duration > 0

        # Verify intermediate files exist
        scene_dir = temp_output_dir / "two_pointers_basic"
        assert (scene_dir / "timing.json").exists()
        assert (scene_dir / "animation.html").exists()
        assert (scene_dir / "video.webm").exists()
        assert (scene_dir / "audio.m4a").exists()
        assert (scene_dir / "final.mp4").exists()
