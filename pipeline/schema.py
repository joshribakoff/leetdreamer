"""
Scene specification schema using Pydantic.

Defines the data models for scene specifications that drive the animation pipeline.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# Preset theme definitions
PRESET_THEMES = {
    "dark": {
        "background": "#1a1a2e",
        "text": "#eee",
        "title": "#e94560",
        "target": "#16c79a",
        "cell_bg": "#0f3460",
        "cell_border": "#16c79a",
        "cell_text": "#eee",
        "pointer_left": "#e94560",
        "pointer_right": "#00b4d8",
        "highlight_found": "#16c79a",
        "highlight_sum": "#f7d716",
        "message": "#f7d716",
        "index_label": "#888",
        "step_indicator": "#666",
    },
    "light": {
        "background": "#f5f5f5",
        "text": "#333",
        "title": "#d63384",
        "target": "#198754",
        "cell_bg": "#ffffff",
        "cell_border": "#198754",
        "cell_text": "#333",
        "pointer_left": "#d63384",
        "pointer_right": "#0d6efd",
        "highlight_found": "#198754",
        "highlight_sum": "#ffc107",
        "message": "#fd7e14",
        "index_label": "#6c757d",
        "step_indicator": "#adb5bd",
    },
    "neetcode": {
        "background": "#0a0a0f",
        "text": "#e5e5e5",
        "title": "#ff6b6b",
        "target": "#51cf66",
        "cell_bg": "#1a1a2e",
        "cell_border": "#4dabf7",
        "cell_text": "#e5e5e5",
        "pointer_left": "#ff6b6b",
        "pointer_right": "#4dabf7",
        "highlight_found": "#51cf66",
        "highlight_sum": "#ffd43b",
        "message": "#ffd43b",
        "index_label": "#868e96",
        "step_indicator": "#495057",
    },
}


class ThemeColors(BaseModel):
    """Custom color overrides for theming.

    All colors are optional. Unspecified colors fall back to the base preset.
    """
    background: Optional[str] = None
    text: Optional[str] = None
    title: Optional[str] = None
    target: Optional[str] = None
    cell_bg: Optional[str] = None
    cell_border: Optional[str] = None
    cell_text: Optional[str] = None
    pointer_left: Optional[str] = None
    pointer_right: Optional[str] = None
    highlight_found: Optional[str] = None
    highlight_sum: Optional[str] = None
    message: Optional[str] = None
    index_label: Optional[str] = None
    step_indicator: Optional[str] = None


class ThemeConfig(BaseModel):
    """Theme configuration for visualization colors.

    Attributes:
        preset: Base preset theme ("dark", "light", "neetcode")
        colors: Custom color overrides
    """
    preset: Literal["dark", "light", "neetcode"] = "dark"
    colors: Optional[ThemeColors] = None

    def resolve_colors(self) -> Dict[str, str]:
        """Resolve final colors by merging preset with overrides."""
        base = PRESET_THEMES[self.preset].copy()
        if self.colors:
            for key, value in self.colors.model_dump().items():
                if value is not None:
                    base[key] = value
        return base


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
        theme: Optional theme configuration
    """
    type: str
    config: Dict[str, Any] = Field(default_factory=dict)
    theme: ThemeConfig = Field(default_factory=ThemeConfig)

    def get_resolved_theme(self) -> Dict[str, str]:
        """Get fully resolved theme colors."""
        return self.theme.resolve_colors()


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
