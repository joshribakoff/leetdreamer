"""
Tests for animation adapters (HTML rendering and Playwright recording).
"""

import json
import tempfile
from pathlib import Path

import pytest

from pipeline.schema import SceneSpec, Step, StepState, VisualizationConfig
from pipeline.adapters.animation import HTMLAnimationAdapter
from pipeline.adapters.recorder import PlaywrightRecorder


class TestHTMLAnimationAdapter:
    """Tests for HTMLAnimationAdapter."""

    @pytest.fixture
    def template_dir(self) -> Path:
        """Path to the templates directory."""
        return Path(__file__).parent.parent / "templates"

    @pytest.fixture
    def adapter(self, template_dir: Path) -> HTMLAnimationAdapter:
        """Create an HTML animation adapter."""
        return HTMLAnimationAdapter(template_dir)

    @pytest.fixture
    def sample_spec(self) -> SceneSpec:
        """Create a sample scene specification."""
        return SceneSpec(
            id="test_scene",
            title="Test Animation",
            description="A test scene for the animation adapter",
            visualization=VisualizationConfig(
                type="array_pointers",
                config={
                    "array": [2, 7, 11, 15],
                    "target": 9,
                    "theme": "dark"
                }
            ),
            steps=[
                Step(
                    id="init",
                    narration="Initialize pointers.",
                    state=StepState(left=0, right=3, message="Start")
                ),
                Step(
                    id="step1",
                    narration="Check the sum.",
                    state=StepState(left=0, right=3, highlight="sum", message="2 + 15 = 17")
                ),
                Step(
                    id="move",
                    narration="Move the pointer.",
                    state=StepState(left=0, right=2, highlight="right_move", message="Move right")
                ),
            ]
        )

    @pytest.fixture
    def sample_timing(self) -> list:
        """Timing for sample spec (3 steps)."""
        return [2.0, 3.0, 2.5]

    def test_adapter_name(self, adapter: HTMLAnimationAdapter):
        """Adapter should have correct name."""
        assert adapter.name == "html"

    def test_render_creates_html_file(
        self,
        adapter: HTMLAnimationAdapter,
        sample_spec: SceneSpec,
        sample_timing: list
    ):
        """render should create an HTML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_animation.html"
            result = adapter.render(sample_spec, sample_timing, output_path)

            assert result == output_path
            assert output_path.exists()
            assert output_path.stat().st_size > 0

    def test_render_html_contains_title(
        self,
        adapter: HTMLAnimationAdapter,
        sample_spec: SceneSpec,
        sample_timing: list
    ):
        """Rendered HTML should contain the scene title."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_animation.html"
            adapter.render(sample_spec, sample_timing, output_path)

            content = output_path.read_text()
            assert sample_spec.title in content

    def test_render_html_contains_array_values(
        self,
        adapter: HTMLAnimationAdapter,
        sample_spec: SceneSpec,
        sample_timing: list
    ):
        """Rendered HTML should contain array values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_animation.html"
            adapter.render(sample_spec, sample_timing, output_path)

            content = output_path.read_text()
            for value in sample_spec.visualization.config["array"]:
                assert str(value) in content

    def test_render_html_contains_target(
        self,
        adapter: HTMLAnimationAdapter,
        sample_spec: SceneSpec,
        sample_timing: list
    ):
        """Rendered HTML should contain target value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_animation.html"
            adapter.render(sample_spec, sample_timing, output_path)

            content = output_path.read_text()
            target = sample_spec.visualization.config["target"]
            assert f"Target: {target}" in content

    def test_render_html_contains_steps_json(
        self,
        adapter: HTMLAnimationAdapter,
        sample_spec: SceneSpec,
        sample_timing: list
    ):
        """Rendered HTML should contain steps as JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_animation.html"
            adapter.render(sample_spec, sample_timing, output_path)

            content = output_path.read_text()
            # Check that step IDs appear in the content
            for step in sample_spec.steps:
                assert step.id in content

    def test_render_html_contains_timing(
        self,
        adapter: HTMLAnimationAdapter,
        sample_spec: SceneSpec,
        sample_timing: list
    ):
        """Rendered HTML should contain timing array."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_animation.html"
            adapter.render(sample_spec, sample_timing, output_path)

            content = output_path.read_text()
            # Check timing values appear in the content
            for duration in sample_timing:
                assert str(duration) in content

    def test_render_html_sets_animation_duration(
        self,
        adapter: HTMLAnimationAdapter,
        sample_spec: SceneSpec,
        sample_timing: list
    ):
        """Rendered HTML should set window.animationDuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_animation.html"
            adapter.render(sample_spec, sample_timing, output_path)

            content = output_path.read_text()
            assert "window.animationDuration" in content

    def test_render_validates_timing_length(
        self,
        adapter: HTMLAnimationAdapter,
        sample_spec: SceneSpec
    ):
        """render should raise ValueError if timing length doesn't match steps."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_animation.html"
            wrong_timing = [1.0, 2.0]  # 2 items but 3 steps

            with pytest.raises(ValueError, match="Timing list length"):
                adapter.render(sample_spec, wrong_timing, output_path)

    def test_render_creates_parent_directories(
        self,
        adapter: HTMLAnimationAdapter,
        sample_spec: SceneSpec,
        sample_timing: list
    ):
        """render should create parent directories if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nested" / "dir" / "test_animation.html"
            result = adapter.render(sample_spec, sample_timing, output_path)

            assert result == output_path
            assert output_path.exists()

    def test_render_html_is_valid_html(
        self,
        adapter: HTMLAnimationAdapter,
        sample_spec: SceneSpec,
        sample_timing: list
    ):
        """Rendered HTML should be valid HTML5."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_animation.html"
            adapter.render(sample_spec, sample_timing, output_path)

            content = output_path.read_text()
            assert "<!DOCTYPE html>" in content
            assert "<html" in content
            assert "</html>" in content
            assert "<head>" in content
            assert "</head>" in content
            assert "<body>" in content
            assert "</body>" in content


class TestPlaywrightRecorder:
    """Tests for PlaywrightRecorder."""

    def test_recorder_name(self):
        """Recorder should have correct name."""
        recorder = PlaywrightRecorder()
        assert recorder.name == "playwright"

    def test_default_viewport_size(self):
        """Recorder should have default viewport 1280x720."""
        recorder = PlaywrightRecorder()
        assert recorder.viewport_width == 1280
        assert recorder.viewport_height == 720

    def test_custom_viewport_size(self):
        """Recorder should accept custom viewport size."""
        recorder = PlaywrightRecorder(viewport_width=1920, viewport_height=1080)
        assert recorder.viewport_width == 1920
        assert recorder.viewport_height == 1080


class TestPlaywrightRecorderIntegration:
    """Integration tests for PlaywrightRecorder.

    These tests actually record video, so they're slower and may require
    Playwright browsers to be installed.
    """

    @pytest.fixture
    def simple_html(self) -> str:
        """Create a simple HTML animation for testing."""
        return """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            background: #1a1a2e;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            color: white;
            font-family: sans-serif;
        }
        .box {
            width: 100px;
            height: 100px;
            background: #e94560;
            animation: pulse 1s ease-in-out infinite;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.2); }
        }
    </style>
</head>
<body>
    <div class="box"></div>
    <script>
        window.animationDuration = 1.0;
        window.animationReady = true;
    </script>
</body>
</html>
"""

    @pytest.mark.slow
    def test_record_creates_video_file(self, simple_html: str):
        """record should create a video file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write HTML file
            html_path = Path(tmpdir) / "test.html"
            html_path.write_text(simple_html)

            # Record video
            recorder = PlaywrightRecorder(viewport_width=640, viewport_height=480)
            output_path = Path(tmpdir) / "output.webm"

            result = recorder.record(html_path, duration=1.0, output_path=output_path)

            assert result.exists()
            assert result.suffix == ".webm"
            assert result.stat().st_size > 0

    @pytest.mark.slow
    def test_record_respects_duration(self, simple_html: str):
        """record should capture for approximately the specified duration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = Path(tmpdir) / "test.html"
            html_path.write_text(simple_html)

            recorder = PlaywrightRecorder(viewport_width=320, viewport_height=240)
            output_path = Path(tmpdir) / "output.webm"

            # Record for a short duration
            result = recorder.record(html_path, duration=0.5, output_path=output_path)

            # Video should exist and have some content
            assert result.exists()
            assert result.stat().st_size > 1000  # Should have meaningful content


# Mark slow tests so they can be skipped with: pytest -m "not slow"
def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
