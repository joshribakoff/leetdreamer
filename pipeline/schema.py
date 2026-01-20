"""
Scene specification schema using Pydantic.

Defines the data models for scene specifications that drive the animation pipeline.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StepState(BaseModel):
    """Visualization state for a single step.

    Attributes:
        left: Left pointer index (for two-pointer visualizations)
        right: Right pointer index (for two-pointer visualizations)
        highlight: Current highlight mode (e.g., "sum", "left_move", "right_move")
        message: Display message for this state
    """
    left: Optional[int] = None
    right: Optional[int] = None
    highlight: Optional[str] = None
    message: Optional[str] = None


class Step(BaseModel):
    """A single step in the animation sequence.

    Attributes:
        id: Unique identifier for this step
        narration: Text to be spoken during this step
        state: Visualization state for this step
    """
    id: str
    narration: str
    state: StepState


class VisualizationConfig(BaseModel):
    """Configuration for the visualization type and parameters.

    Attributes:
        type: Type of visualization (e.g., "array_pointers")
        config: Type-specific configuration dictionary
    """
    type: str
    config: Dict[str, Any] = Field(default_factory=dict)


class SceneSpec(BaseModel):
    """Full scene specification.

    This is the primary data structure that drives the entire animation pipeline.

    Attributes:
        id: Unique identifier for this scene
        title: Human-readable title
        description: Description of what the scene demonstrates
        visualization: Visualization configuration
        steps: List of animation steps with narration
    """
    id: str
    title: str
    description: Optional[str] = None
    visualization: VisualizationConfig
    steps: List[Step]

    def get_narrations(self) -> List[str]:
        """Extract all narration texts from steps."""
        return [step.narration for step in self.steps]

    def get_step_ids(self) -> List[str]:
        """Extract all step IDs."""
        return [step.id for step in self.steps]
