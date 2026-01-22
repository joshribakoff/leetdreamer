#!/usr/bin/env python3
"""
Animation Pipeline CLI

Build animated algorithm visualizations from scene specifications.

Usage:
    # Build a single scene
    python build.py scenes/two_pointers/scene.json

    # Build with specific TTS adapter
    python build.py scenes/two_pointers/scene.json --tts macos_say

    # Build all scenes in a directory
    python build.py scenes/ --all

    # Validate only (dry run)
    python build.py scenes/two_pointers/scene.json --dry-run

    # Specify output directory
    python build.py scenes/two_pointers/scene.json -o output/
"""

import argparse
import logging
import sys
from pathlib import Path

# Add the animations directory to path for imports
ANIMATIONS_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(ANIMATIONS_DIR))

from pipeline.orchestrator import PipelineOrchestrator, BuildResult, PipelineError
from pipeline.adapters.tts import MacOSSayAdapter, PiperTTSAdapter
from pipeline.adapters.tts.openai_tts import OpenAITTSAdapter
from pipeline.adapters.animation import HTMLAnimationAdapter
from pipeline.adapters.recorder import PlaywrightRecorder
from pipeline.adapters.merger import FFmpegMerger


def setup_logging(verbose: bool = False):
    """Configure logging for the CLI."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def create_tts_adapter(tts_name: str, voice: str | None = None, model: str = "tts-1-hd"):
    """Create a TTS adapter by name.

    Args:
        tts_name: Name of the TTS adapter to create
        voice: Voice to use (macos_say: Samantha, etc. OpenAI: alloy, echo, fable, onyx, nova, shimmer)
        model: OpenAI model to use (tts-1, tts-1-hd)

    Returns:
        TTS adapter instance
    """
    if tts_name == "macos_say":
        return MacOSSayAdapter(voice=voice or "Samantha")
    elif tts_name == "openai":
        return OpenAITTSAdapter(voice=voice or "onyx", model=model)
    elif tts_name == "piper":
        return PiperTTSAdapter()
    else:
        raise ValueError(f"Unknown TTS adapter: {tts_name}")


def find_scene_files(path: Path) -> list[Path]:
    """Find all scene.json files in a path.

    Args:
        path: Path to a scene.json file or directory containing scenes

    Returns:
        List of paths to scene.json files
    """
    path = Path(path)

    if path.is_file():
        return [path]

    # Search for scene.json files in directory
    scene_files = list(path.glob("**/scene.json"))
    return sorted(scene_files)


def print_result(result: BuildResult):
    """Print build result to console."""
    if result.success:
        print(f"\n{'='*60}")
        print(f"SUCCESS: {result.scene_id}")
        print(f"{'='*60}")
        print(f"Output: {result.output_path}")
        print(f"Duration: {result.total_duration:.2f}s")
        print(f"Steps: {len(result.timing)}")
        if result.timing:
            print(f"Step durations: {', '.join(f'{t:.2f}s' for t in result.timing)}")
        print()
    else:
        print(f"\n{'='*60}")
        print(f"FAILED: {result.scene_id}")
        print(f"{'='*60}")
        print(f"Error: {result.error}")
        print()


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Build animation from scene spec",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "scene",
        type=Path,
        help="Path to scene.json or scenes directory"
    )
    parser.add_argument(
        "--tts",
        default="piper",
        choices=["macos_say", "openai", "piper"],
        help="TTS adapter to use (default: piper)"
    )
    parser.add_argument(
        "--voice",
        default=None,
        help="Voice for TTS (macos: Samantha; openai: onyx, alloy, echo, fable, nova, shimmer)"
    )
    parser.add_argument(
        "--model",
        default="tts-1-hd",
        choices=["tts-1", "tts-1-hd"],
        help="OpenAI TTS model (default: tts-1-hd)"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output directory (default: output/ in animations dir)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate only, don't build"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="build_all",
        help="Build all scenes in directory"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Determine output directory
    output_dir = args.output or (ANIMATIONS_DIR / "output")

    # Find scene files
    scene_path = Path(args.scene)
    if not scene_path.exists():
        print(f"Error: Path not found: {scene_path}")
        sys.exit(1)

    if scene_path.is_dir():
        if not args.build_all:
            print(f"Error: {scene_path} is a directory. Use --all to build all scenes.")
            sys.exit(1)
        scene_files = find_scene_files(scene_path)
        if not scene_files:
            print(f"Error: No scene.json files found in {scene_path}")
            sys.exit(1)
    else:
        scene_files = [scene_path]

    logger.info(f"Found {len(scene_files)} scene(s) to build")
    for sf in scene_files:
        logger.info(f"  - {sf}")

    # Create adapters
    logger.info("Initializing adapters...")
    try:
        tts = create_tts_adapter(args.tts, args.voice, args.model)
        logger.info(f"  TTS: {tts.name}")

        animation = HTMLAnimationAdapter(ANIMATIONS_DIR / "templates")
        logger.info(f"  Animation: {animation.name}")

        recorder = PlaywrightRecorder()
        logger.info(f"  Recorder: {recorder.name}")

        merger = FFmpegMerger()
        logger.info(f"  Merger: {merger.name}")
    except Exception as e:
        print(f"Error initializing adapters: {e}")
        sys.exit(1)

    # Create orchestrator
    orchestrator = PipelineOrchestrator(
        tts=tts,
        animation=animation,
        recorder=recorder,
        merger=merger,
        output_dir=output_dir
    )

    # Build scenes
    results: list[BuildResult] = []

    for scene_file in scene_files:
        logger.info(f"Building: {scene_file}")
        try:
            if args.dry_run:
                result = orchestrator.build_from_file_dry_run(scene_file)
            else:
                result = orchestrator.build_from_file(scene_file)
            results.append(result)
            print_result(result)
        except PipelineError as e:
            print(f"Error: {e}")
            results.append(BuildResult(
                scene_id=scene_file.stem,
                output_path=output_dir / scene_file.stem / "final.mp4",
                timing=[],
                total_duration=0.0,
                success=False,
                error=str(e),
            ))

    # Summary
    successful = sum(1 for r in results if r.success)
    failed = len(results) - successful

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    if failed > 0:
        print("\nFailed scenes:")
        for r in results:
            if not r.success:
                print(f"  - {r.scene_id}: {r.error}")
        sys.exit(1)

    print("\nAll scenes built successfully!")
    sys.exit(0)


if __name__ == "__main__":
    main()
