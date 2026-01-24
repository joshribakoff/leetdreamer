"""
Scene specification schema using Pydantic.

Defines the data models for scene specifications that drive the animation pipeline.
"""

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class StepState(BaseModel):
    """Visualization state for a single step.

    Uses extra="allow" to support arbitrary pointer names (i, j, left, right, etc.)
    without requiring schema changes for each new visualization type.

    Common fields are typed for IDE support, but any additional fields
    will pass through to templates.
    """
    model_config = ConfigDict(extra="allow")

    # Common fields (typed for convenience, but not exhaustive)
    left: Optional[int] = None
    right: Optional[int] = None
    highlight: Optional[Union[str, List[int]]] = None
    message: Optional[str] = None
    reveal: Optional[List[str]] = None
    # Hash table visualization fields
    current_index: Optional[int] = None
    stored_indices: Optional[List[int]] = None
    hashmap_entries: Optional[List[Dict[str, Any]]] = None
    lookup_value: Optional[int] = None
    found_pair: Optional[List[int]] = None
    complement: Optional[int] = None


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


class ChildSceneRef(BaseModel):
    """Reference to a child scene in a composite.

    Attributes:
        ref: Relative path to the child scene JSON file
    """
    ref: str


class CompositeSceneSpec(BaseModel):
    """Composite scene specification for stitching multiple scenes.

    Attributes:
        id: Unique identifier for this composite scene
        type: Must be "composite" to identify this as a composite scene
        children: List of references to child scenes
        transitions: Transition type between scenes ("cut" or "fade")
    """
    id: str
    type: Literal["composite"] = "composite"
    children: List[ChildSceneRef]
    transitions: Literal["cut", "fade"] = "cut"
