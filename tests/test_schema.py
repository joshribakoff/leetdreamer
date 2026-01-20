"""
Tests for scene specification schema validation.
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from pipeline.schema import SceneSpec, Step, StepState, VisualizationConfig


class TestStepState:
    """Tests for StepState model."""

    def test_all_fields_optional(self):
        """StepState should work with no fields."""
        state = StepState()
        assert state.left is None
        assert state.right is None
        assert state.highlight is None
        assert state.message is None

    def test_with_pointer_values(self):
        """StepState should accept pointer indices."""
        state = StepState(left=0, right=3)
        assert state.left == 0
        assert state.right == 3

    def test_with_all_fields(self):
        """StepState should accept all fields."""
        state = StepState(
            left=1,
            right=2,
            highlight="sum",
            message="Test message"
        )
        assert state.left == 1
        assert state.right == 2
        assert state.highlight == "sum"
        assert state.message == "Test message"


class TestStep:
    """Tests for Step model."""

    def test_required_fields(self):
        """Step requires id and narration."""
        with pytest.raises(ValidationError):
            Step(id="test")  # missing narration and state

    def test_valid_step(self):
        """Step should accept valid data."""
        step = Step(
            id="test_step",
            narration="This is a test narration.",
            state=StepState(left=0, right=3)
        )
        assert step.id == "test_step"
        assert step.narration == "This is a test narration."
        assert step.state.left == 0

    def test_step_from_dict(self):
        """Step should parse from dictionary."""
        data = {
            "id": "init",
            "narration": "Initialize the array.",
            "state": {
                "left": 0,
                "right": 5,
                "highlight": None,
                "message": "Starting"
            }
        }
        step = Step(**data)
        assert step.id == "init"
        assert step.state.right == 5


class TestVisualizationConfig:
    """Tests for VisualizationConfig model."""

    def test_type_required(self):
        """VisualizationConfig requires type."""
        with pytest.raises(ValidationError):
            VisualizationConfig()

    def test_config_defaults_to_empty_dict(self):
        """Config should default to empty dict."""
        viz = VisualizationConfig(type="array_pointers")
        assert viz.type == "array_pointers"
        assert viz.config == {}

    def test_with_config(self):
        """VisualizationConfig should accept config dict."""
        viz = VisualizationConfig(
            type="array_pointers",
            config={"array": [1, 2, 3], "target": 5}
        )
        assert viz.config["array"] == [1, 2, 3]
        assert viz.config["target"] == 5


class TestSceneSpec:
    """Tests for SceneSpec model."""

    def test_required_fields(self):
        """SceneSpec requires id, title, visualization, and steps."""
        with pytest.raises(ValidationError):
            SceneSpec(id="test", title="Test")  # missing visualization and steps

    def test_minimal_scene(self):
        """SceneSpec should work with minimal valid data."""
        spec = SceneSpec(
            id="test_scene",
            title="Test Scene",
            visualization=VisualizationConfig(type="array_pointers"),
            steps=[
                Step(
                    id="step1",
                    narration="First step",
                    state=StepState()
                )
            ]
        )
        assert spec.id == "test_scene"
        assert spec.title == "Test Scene"
        assert len(spec.steps) == 1

    def test_description_optional(self):
        """Description should be optional."""
        spec = SceneSpec(
            id="test",
            title="Test",
            visualization=VisualizationConfig(type="test"),
            steps=[Step(id="s1", narration="text", state=StepState())]
        )
        assert spec.description is None

    def test_get_narrations(self):
        """get_narrations should extract all narration texts."""
        spec = SceneSpec(
            id="test",
            title="Test",
            visualization=VisualizationConfig(type="test"),
            steps=[
                Step(id="s1", narration="First narration", state=StepState()),
                Step(id="s2", narration="Second narration", state=StepState()),
                Step(id="s3", narration="Third narration", state=StepState()),
            ]
        )
        narrations = spec.get_narrations()
        assert narrations == ["First narration", "Second narration", "Third narration"]

    def test_get_step_ids(self):
        """get_step_ids should extract all step IDs."""
        spec = SceneSpec(
            id="test",
            title="Test",
            visualization=VisualizationConfig(type="test"),
            steps=[
                Step(id="init", narration="text", state=StepState()),
                Step(id="middle", narration="text", state=StepState()),
                Step(id="end", narration="text", state=StepState()),
            ]
        )
        step_ids = spec.get_step_ids()
        assert step_ids == ["init", "middle", "end"]


class TestSampleSceneFixture:
    """Tests using the sample scene fixture file."""

    @pytest.fixture
    def sample_scene_path(self) -> Path:
        """Path to the sample scene fixture."""
        return Path(__file__).parent / "fixtures" / "sample_scene.json"

    @pytest.fixture
    def sample_scene_data(self, sample_scene_path: Path) -> dict:
        """Load sample scene as dictionary."""
        with open(sample_scene_path) as f:
            return json.load(f)

    def test_sample_scene_parses(self, sample_scene_data: dict):
        """Sample scene fixture should parse as valid SceneSpec."""
        spec = SceneSpec(**sample_scene_data)
        assert spec.id == "two_pointers_basic"
        assert spec.title == "Two Pointers: O(n)"

    def test_sample_scene_visualization(self, sample_scene_data: dict):
        """Sample scene visualization config should be correct."""
        spec = SceneSpec(**sample_scene_data)
        assert spec.visualization.type == "array_pointers"
        assert spec.visualization.config["array"] == [2, 7, 11, 15]
        assert spec.visualization.config["target"] == 9
        assert spec.visualization.config["theme"] == "dark"

    def test_sample_scene_steps(self, sample_scene_data: dict):
        """Sample scene should have expected steps."""
        spec = SceneSpec(**sample_scene_data)
        assert len(spec.steps) == 3

        # Check first step
        init_step = spec.steps[0]
        assert init_step.id == "init"
        assert "two pointers" in init_step.narration.lower()
        assert init_step.state.left == 0
        assert init_step.state.right == 3

        # Check second step
        step1 = spec.steps[1]
        assert step1.id == "step1"
        assert step1.state.highlight == "sum"

        # Check third step
        move_step = spec.steps[2]
        assert move_step.id == "move_right"
        assert move_step.state.right == 2  # Right pointer moved

    def test_sample_scene_narrations(self, sample_scene_data: dict):
        """Sample scene narrations should be extractable."""
        spec = SceneSpec(**sample_scene_data)
        narrations = spec.get_narrations()
        assert len(narrations) == 3
        assert "sorted array" in narrations[0].lower()
        assert "seventeen" in narrations[1].lower()
        assert "right pointer" in narrations[2].lower()
