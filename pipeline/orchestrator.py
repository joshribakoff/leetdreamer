"""
Pipeline Orchestrator.

Wires all adapters together and executes the build pipeline:
1. Generate TTS audio for each narration step
2. Extract duration from each audio file
3. Render animation HTML with timing
4. Record animation to video
5. Concatenate audio segments
6. Merge video + audio
7. Return result with output path
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .schema import SceneSpec
from .adapters.base import TTSAdapter, AnimationAdapter, RecorderAdapter, MergerAdapter

logger = logging.getLogger(__name__)


class PipelineError(Exception):
    """Exception raised when the pipeline fails."""
    pass


@dataclass
class BuildResult:
    """Result of building a scene.

    Attributes:
        scene_id: Unique identifier of the scene
        output_path: Path to the final merged video
        timing: List of durations for each step (in seconds)
        total_duration: Total duration of the animation
        success: Whether the build succeeded
        error: Error message if build failed
        intermediate_files: Paths to intermediate files (audio, html, video)
    """
    scene_id: str
    output_path: Path
    timing: List[float]
    total_duration: float
    success: bool
    error: Optional[str] = None
    intermediate_files: dict = field(default_factory=dict)


class PipelineOrchestrator:
    """Orchestrates the animation pipeline by wiring adapters together.

    The orchestrator coordinates the following steps:
    1. Generate TTS audio for each narration step
    2. Extract duration from each audio file
    3. Render animation HTML with timing
    4. Record animation to video
    5. Concatenate audio segments
    6. Merge video + audio

    Args:
        tts: Text-to-speech adapter for generating narration audio
        animation: Animation adapter for rendering HTML
        recorder: Recorder adapter for capturing video from HTML
        merger: Merger adapter for combining audio and video
        output_dir: Base directory for build outputs
    """

    def __init__(
        self,
        tts: TTSAdapter,
        animation: AnimationAdapter,
        recorder: RecorderAdapter,
        merger: MergerAdapter,
        output_dir: Path
    ):
        self.tts = tts
        self.animation = animation
        self.recorder = recorder
        self.merger = merger
        self.output_dir = Path(output_dir)

    def build(self, scene_spec: SceneSpec, dry_run: bool = False) -> BuildResult:
        """Execute the full pipeline to build a scene.

        Args:
            scene_spec: The scene specification to build
            dry_run: If True, validate only without building

        Returns:
            BuildResult with output path and timing information

        Raises:
            PipelineError: If any step in the pipeline fails
        """
        scene_id = scene_spec.id
        scene_output_dir = self.output_dir / scene_id
        scene_output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"[{scene_id}] Starting pipeline build")
        logger.info(f"[{scene_id}] Output directory: {scene_output_dir}")

        # Initialize result tracking
        intermediate_files = {}
        timing: List[float] = []
        audio_paths: List[Path] = []

        if dry_run:
            logger.info(f"[{scene_id}] Dry run mode - validating only")
            # Validate scene spec
            narrations = scene_spec.get_narrations()
            logger.info(f"[{scene_id}] Scene has {len(narrations)} steps")
            for i, narration in enumerate(narrations):
                logger.info(f"[{scene_id}]   Step {i}: {narration[:50]}...")

            return BuildResult(
                scene_id=scene_id,
                output_path=scene_output_dir / "final.mp4",
                timing=[],
                total_duration=0.0,
                success=True,
                intermediate_files=intermediate_files,
            )

        try:
            # Step 1: Generate TTS audio for each narration step
            logger.info(f"[{scene_id}] Step 1: Generating TTS audio")
            narrations = scene_spec.get_narrations()

            for i, narration in enumerate(narrations):
                audio_path = scene_output_dir / f"step_{i}{self.tts.output_extension}"
                logger.info(f"[{scene_id}]   Generating audio for step {i}: {narration[:50]}...")

                self.tts.generate(narration, audio_path)
                audio_paths.append(audio_path)
                logger.info(f"[{scene_id}]   Created: {audio_path}")

            intermediate_files["audio_steps"] = [str(p) for p in audio_paths]

            # Step 2: Extract duration from each audio file
            logger.info(f"[{scene_id}] Step 2: Extracting audio durations")
            for i, audio_path in enumerate(audio_paths):
                duration = self.tts.get_duration(audio_path)
                timing.append(duration)
                logger.info(f"[{scene_id}]   Step {i} duration: {duration:.2f}s")

            total_duration = sum(timing)
            logger.info(f"[{scene_id}]   Total duration: {total_duration:.2f}s")

            # Save timing.json for debugging
            timing_path = scene_output_dir / "timing.json"
            timing_data = {
                "scene_id": scene_id,
                "step_durations": timing,
                "total_duration": total_duration,
                "steps": [
                    {"id": step.id, "duration": dur, "narration": step.narration}
                    for step, dur in zip(scene_spec.steps, timing)
                ]
            }
            timing_path.write_text(json.dumps(timing_data, indent=2))
            intermediate_files["timing"] = str(timing_path)
            logger.info(f"[{scene_id}]   Saved timing to: {timing_path}")

            # Step 3: Render animation HTML with timing
            logger.info(f"[{scene_id}] Step 3: Rendering animation HTML")
            html_path = scene_output_dir / "animation.html"
            self.animation.render(scene_spec, timing, html_path)
            intermediate_files["html"] = str(html_path)
            logger.info(f"[{scene_id}]   Created: {html_path}")

            # Step 4: Record animation to video
            logger.info(f"[{scene_id}] Step 4: Recording animation to video")
            video_path = scene_output_dir / "video.webm"
            self.recorder.record(html_path, total_duration, video_path)
            intermediate_files["video"] = str(video_path)
            logger.info(f"[{scene_id}]   Created: {video_path}")

            # Step 5: Concatenate audio segments
            logger.info(f"[{scene_id}] Step 5: Concatenating audio segments")
            audio_concat_path = scene_output_dir / "audio.m4a"
            self.merger.concat_audio(audio_paths, audio_concat_path)
            intermediate_files["audio_concat"] = str(audio_concat_path)
            logger.info(f"[{scene_id}]   Created: {audio_concat_path}")

            # Step 6: Merge video + audio
            logger.info(f"[{scene_id}] Step 6: Merging video and audio")
            final_path = scene_output_dir / "final.mp4"
            self.merger.merge(video_path, audio_concat_path, final_path)
            intermediate_files["final"] = str(final_path)
            logger.info(f"[{scene_id}]   Created: {final_path}")

            logger.info(f"[{scene_id}] Pipeline complete!")
            logger.info(f"[{scene_id}] Final output: {final_path}")

            return BuildResult(
                scene_id=scene_id,
                output_path=final_path,
                timing=timing,
                total_duration=total_duration,
                success=True,
                intermediate_files=intermediate_files,
            )

        except Exception as e:
            error_msg = f"Pipeline failed: {e}"
            logger.error(f"[{scene_id}] {error_msg}")
            return BuildResult(
                scene_id=scene_id,
                output_path=scene_output_dir / "final.mp4",
                timing=timing,
                total_duration=sum(timing) if timing else 0.0,
                success=False,
                error=error_msg,
                intermediate_files=intermediate_files,
            )

    def build_from_file(self, scene_path: Path) -> BuildResult:
        """Load scene spec from JSON file and build.

        Args:
            scene_path: Path to the scene.json file

        Returns:
            BuildResult with output path and timing information

        Raises:
            PipelineError: If the file cannot be loaded or parsed
        """
        scene_path = Path(scene_path)

        if not scene_path.exists():
            raise PipelineError(f"Scene file not found: {scene_path}")

        logger.info(f"Loading scene from: {scene_path}")

        try:
            scene_data = json.loads(scene_path.read_text())
            scene_spec = SceneSpec(**scene_data)
        except json.JSONDecodeError as e:
            raise PipelineError(f"Invalid JSON in scene file: {e}") from e
        except Exception as e:
            raise PipelineError(f"Failed to parse scene spec: {e}") from e

        return self.build(scene_spec)

    def build_from_file_dry_run(self, scene_path: Path) -> BuildResult:
        """Load scene spec and validate without building.

        Args:
            scene_path: Path to the scene.json file

        Returns:
            BuildResult with validation status
        """
        scene_path = Path(scene_path)

        if not scene_path.exists():
            raise PipelineError(f"Scene file not found: {scene_path}")

        logger.info(f"Loading scene from: {scene_path}")

        try:
            scene_data = json.loads(scene_path.read_text())
            scene_spec = SceneSpec(**scene_data)
        except json.JSONDecodeError as e:
            raise PipelineError(f"Invalid JSON in scene file: {e}") from e
        except Exception as e:
            raise PipelineError(f"Failed to parse scene spec: {e}") from e

        return self.build(scene_spec, dry_run=True)
