"""
HTML Animation Adapter.

Renders scene specifications to HTML files using Jinja2 templates.
The rendered HTML can then be recorded to video using a RecorderAdapter.
"""

from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader

from ..base import AnimationAdapter
from ...schema import SceneSpec


class HTMLAnimationAdapter(AnimationAdapter):
    """Adapter that renders scene specs to HTML using Jinja2 templates.

    This adapter generates an HTML file with embedded JavaScript that
    animates through the scene steps. The HTML file sets window.animationDuration
    so the recorder knows how long to capture.

    Attributes:
        template_dir: Directory containing Jinja2 templates
        env: Jinja2 environment for template loading
    """

    def __init__(self, template_dir: Path):
        """Initialize the HTML animation adapter.

        Args:
            template_dir: Path to directory containing Jinja2 templates
        """
        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )

    @property
    def name(self) -> str:
        """Adapter identifier for logging."""
        return "html"

    def _get_template_name(self, viz_type: str) -> str:
        """Map visualization type to template filename.

        Args:
            viz_type: The visualization type from the scene spec

        Returns:
            Template filename
        """
        # Map visualization types to templates
        template_map = {
            "array_pointers": "array_animation.html",
            "array": "array_animation.html",
            "problem_statement": "problem_statement.html",
        }
        return template_map.get(viz_type, "array_animation.html")

    def render(self, spec: SceneSpec, timing: List[float], output_path: Path) -> Path:
        """Render scene specification to HTML file.

        Args:
            spec: The scene specification to render
            timing: List of durations in seconds for each step
            output_path: Path where the HTML file should be saved

        Returns:
            Path to the rendered HTML file

        Raises:
            ValueError: If timing list length doesn't match steps
            FileNotFoundError: If template doesn't exist
        """
        if len(timing) != len(spec.steps):
            raise ValueError(
                f"Timing list length ({len(timing)}) must match "
                f"number of steps ({len(spec.steps)})"
            )

        # Get the appropriate template
        template_name = self._get_template_name(spec.visualization.type)
        template = self.env.get_template(template_name)

        # Extract visualization config
        viz_config = spec.visualization.config

        # Convert steps to serializable format
        steps_data = [
            {
                "id": step.id,
                "narration": step.narration,
                "state": {
                    "left": step.state.left,
                    "right": step.state.right,
                    "highlight": step.state.highlight,
                    "message": step.state.message,
                    "reveal": step.state.reveal,
                }
            }
            for step in spec.steps
        ]

        # Build template context based on visualization type
        if spec.visualization.type == "problem_statement":
            html_content = template.render(
                title=spec.title,
                problem_title=viz_config.get("problem_title", spec.title),
                difficulty=viz_config.get("difficulty", "medium"),
                description=viz_config.get("description", ""),
                constraints=viz_config.get("constraints", []),
                examples=viz_config.get("examples", []),
                steps=steps_data,
                timing=timing,
            )
        else:
            # Array-based visualizations
            array = viz_config.get("array", [])
            target = viz_config.get("target", 0)
            html_content = template.render(
                title=spec.title,
                array=array,
                target=target,
                steps=steps_data,
                timing=timing,
            )

        # Ensure output directory exists
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write HTML file
        output_path.write_text(html_content)

        return output_path

    def render_html_only(self, spec: SceneSpec, timing: List[float], output_path: Path) -> Path:
        """Render to HTML without video recording (alias for render).

        This method exists for clarity when you only want the HTML file
        and will use a separate RecorderAdapter for video capture.

        Args:
            spec: The scene specification to render
            timing: List of durations in seconds for each step
            output_path: Path where the HTML file should be saved

        Returns:
            Path to the rendered HTML file
        """
        return self.render(spec, timing, output_path)
