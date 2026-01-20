# Animation Pipeline Architecture

> **Core Principle**: The *scene specification* is the product. The *engine* is a set of loosely coupled, swappable adapters.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Scene Specification                          │
│  scenes/two_pointers/scene.json                                  │
│  - narration steps (text)                                        │
│  - visualization config (array, pointers, highlights)            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Pipeline Orchestrator                       │
│  build.py                                                        │
│  - Loads scene spec                                              │
│  - Wires adapters together                                       │
│  - Executes build pipeline                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  TTS Adapter │      │  Animation   │      │   Merger     │
│              │      │   Adapter    │      │   Adapter    │
│ - generate() │      │ - render()   │      │ - merge()    │
│ - duration() │      │ - duration() │      │              │
└──────────────┘      └──────────────┘      └──────────────┘
        │                     │                     │
   Implementations:     Implementations:      Implementations:
   - MacOSSay           - HTMLAnimation       - FFmpegMerger
   - Piper              - ManimAnimation
   - OpenAI             (future)
```

---

## Directory Structure

```
animations/
├── ARCHITECTURE.md           # This file
├── build.py                  # Pipeline orchestrator (CLI entry point)
├── pipeline/
│   ├── __init__.py
│   ├── orchestrator.py       # Main pipeline logic
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base.py           # Abstract base classes (interfaces)
│   │   ├── tts/
│   │   │   ├── __init__.py
│   │   │   ├── macos_say.py  # macOS say command
│   │   │   ├── piper.py      # Piper TTS (future)
│   │   │   └── openai.py     # OpenAI TTS (future)
│   │   ├── animation/
│   │   │   ├── __init__.py
│   │   │   ├── html.py       # HTML/CSS/JS renderer
│   │   │   └── manim.py      # Manim renderer (future)
│   │   ├── recorder/
│   │   │   ├── __init__.py
│   │   │   └── playwright.py # Playwright screen recorder
│   │   └── merger/
│   │       ├── __init__.py
│   │       └── ffmpeg.py     # FFmpeg audio/video merger
│   └── schema.py             # Scene spec validation (Pydantic)
├── scenes/                   # Scene specifications (the product)
│   └── two_pointers/
│       ├── scene.json        # Narration + visualization config
│       └── assets/           # Any scene-specific assets
├── templates/                # HTML animation templates
│   └── array_animation.html  # Jinja2 template for array scenes
├── output/                   # Build artifacts (gitignored)
│   └── two_pointers/
│       ├── timing.json       # Auto-generated durations
│       ├── step_*.aiff       # Individual audio segments
│       ├── audio.m4a         # Concatenated audio
│       ├── video.webm        # Recorded animation
│       └── final.mp4         # Merged output
└── tests/
    ├── __init__.py
    ├── test_tts_adapters.py
    ├── test_orchestrator.py
    └── fixtures/
        └── sample_scene.json
```

---

## Scene Specification Schema

```json
{
  "$schema": "scene.schema.json",
  "id": "two_pointers_basic",
  "title": "Two Pointers: O(n)",
  "description": "Demonstrates two pointer technique on sorted array",

  "visualization": {
    "type": "array_pointers",
    "config": {
      "array": [2, 7, 11, 15],
      "target": 9,
      "theme": "dark"
    }
  },

  "steps": [
    {
      "id": "init",
      "narration": "We start with two pointers at each end of the sorted array.",
      "state": {
        "left": 0,
        "right": 3,
        "highlight": null,
        "message": "Initialize pointers"
      }
    },
    {
      "id": "step1",
      "narration": "Two plus fifteen equals seventeen. That's bigger than our target of nine.",
      "state": {
        "left": 0,
        "right": 3,
        "highlight": "sum",
        "message": "2 + 15 = 17 > 9"
      }
    },
    {
      "id": "move_right",
      "narration": "Since the sum is too big, we move the right pointer left.",
      "state": {
        "left": 0,
        "right": 2,
        "highlight": "right_move",
        "message": "Move right pointer"
      }
    }
  ]
}
```

---

## Adapter Interfaces

### TTSAdapter (Abstract Base)

```python
class TTSAdapter(ABC):
    @abstractmethod
    def generate(self, text: str, output_path: Path) -> Path:
        """Generate audio file from text. Returns path to audio file."""
        pass

    @abstractmethod
    def get_duration(self, audio_path: Path) -> float:
        """Get duration of audio file in seconds."""
        pass

    @abstractmethod
    def name(self) -> str:
        """Adapter identifier for logging."""
        pass
```

### AnimationAdapter (Abstract Base)

```python
class AnimationAdapter(ABC):
    @abstractmethod
    def render(self, scene_spec: SceneSpec, timing: List[float], output_path: Path) -> Path:
        """Render animation video. Returns path to video file."""
        pass

    @abstractmethod
    def name(self) -> str:
        """Adapter identifier for logging."""
        pass
```

### MergerAdapter (Abstract Base)

```python
class MergerAdapter(ABC):
    @abstractmethod
    def merge(self, video_path: Path, audio_path: Path, output_path: Path) -> Path:
        """Merge video and audio. Returns path to merged file."""
        pass

    @abstractmethod
    def concat_audio(self, audio_paths: List[Path], output_path: Path) -> Path:
        """Concatenate multiple audio files. Returns path to combined file."""
        pass
```

---

## Implementation Checklist

### Phase 1: Core Infrastructure
- [x] Create directory structure
- [x] Implement `pipeline/schema.py` (Pydantic models for scene spec)
- [x] Implement `pipeline/adapters/base.py` (abstract interfaces)
- [x] Write basic tests for schema validation

### Phase 2: TTS Adapter
- [x] Implement `pipeline/adapters/tts/macos_say.py`
- [x] Add duration extraction using ffprobe
- [x] Write tests for TTS adapter

### Phase 3: Animation Adapter
- [x] Create `templates/array_animation.html` (Jinja2 template)
- [x] Implement `pipeline/adapters/animation/html.py`
- [x] Implement `pipeline/adapters/recorder/playwright.py`
- [x] Write tests for animation rendering

### Phase 4: Merger Adapter
- [x] Implement `pipeline/adapters/merger/ffmpeg.py`
- [x] Add audio concatenation
- [x] Add video/audio merge with proper sync
- [x] Write tests for merger

### Phase 5: Pipeline Orchestrator
- [x] Implement `pipeline/orchestrator.py`
- [x] Wire all adapters together
- [x] Implement `build.py` CLI entry point
- [x] Write integration tests

### Phase 6: Scene Migration
- [ ] Create `scenes/two_pointers/scene.json` from existing narration
- [ ] Test full pipeline end-to-end
- [ ] Generate final synced video

---

## CLI Usage (Target)

```bash
# Build a single scene
python build.py scenes/two_pointers/scene.json

# Build with specific adapters
python build.py scenes/two_pointers/scene.json --tts openai --animation html

# Build all scenes
python build.py scenes/

# Dry run (validate only)
python build.py scenes/two_pointers/scene.json --dry-run

# Watch mode (rebuild on change)
python build.py scenes/two_pointers/scene.json --watch
```

---

## Testing Strategy

1. **Unit tests**: Each adapter in isolation with mock inputs
2. **Integration tests**: Full pipeline with a minimal test scene
3. **Fixtures**: `tests/fixtures/sample_scene.json` with known expected outputs

```bash
# Run tests
pytest animations/tests/ -v

# Run with coverage
pytest animations/tests/ --cov=pipeline
```

---

## Handoff Protocol for Subagents

Each subagent must:
1. Check off completed items in this document
2. Add a summary comment under "Implementation Notes" section
3. Run any relevant tests before handoff
4. Note any issues or decisions made

---

## Implementation Notes

> Subagents add notes here during implementation

### Phase 1 Notes
**Completed 2026-01-19**

**Files Created:**
- `pipeline/__init__.py` - Package init
- `pipeline/schema.py` - Pydantic models: `StepState`, `Step`, `VisualizationConfig`, `SceneSpec`
- `pipeline/adapters/__init__.py` - Package init
- `pipeline/adapters/base.py` - Abstract base classes: `TTSAdapter`, `AnimationAdapter`, `RecorderAdapter`, `MergerAdapter`
- `pipeline/adapters/tts/__init__.py` - Package init
- `pipeline/adapters/animation/__init__.py` - Package init
- `pipeline/adapters/recorder/__init__.py` - Package init
- `pipeline/adapters/merger/__init__.py` - Package init
- `tests/__init__.py` - Package init
- `tests/test_schema.py` - 18 tests for schema validation
- `tests/fixtures/sample_scene.json` - Sample scene fixture

**Decisions:**
1. Used Pydantic v2 for schema validation (installed as dependency)
2. Added helper methods to `SceneSpec`: `get_narrations()` and `get_step_ids()` for convenience
3. Made `name` a property (not method) on all adapters for cleaner access
4. `RecorderAdapter` added as separate interface from `AnimationAdapter` for flexibility (HTML adapter renders template, recorder captures it to video)
5. All `StepState` fields are optional to support various visualization types

**Tests:** 18 tests pass in `tests/test_schema.py`

### Phase 2 Notes
**Completed 2026-01-19**

**Files Created:**
- `pipeline/adapters/tts/macos_say.py` - MacOSSayAdapter implementation
- `tests/test_tts_adapters.py` - 23 tests (21 pass, 2 skipped when ffprobe unavailable)

**Files Modified:**
- `pipeline/adapters/tts/__init__.py` - Exports MacOSSayAdapter and TTSError

**Implementation Details:**
1. `MacOSSayAdapter` class with configurable voice (default: Samantha) and ffprobe path
2. `generate(text, output_path)` - Uses macOS `say -v {voice} -o {path} "{text}"` command
3. `get_duration(audio_path)` - Uses ffprobe with JSON output to extract duration
4. `TTSError` exception class for all TTS-related errors

**Design Decisions:**
1. ffprobe path defaults to `~/.local/bin/ffprobe` but is configurable via constructor
2. Empty/whitespace-only text raises TTSError early (before calling say)
3. Output directories are created automatically if they don't exist
4. Integration tests are skipped gracefully when say or ffprobe are unavailable

**Tests:** 21 unit tests pass, 2 integration tests skipped (ffprobe not installed on test system)

**Usage Example:**
```python
from pipeline.adapters.tts import MacOSSayAdapter

adapter = MacOSSayAdapter(voice="Samantha")
audio_path = adapter.generate("Hello world", Path("output.aiff"))
duration = adapter.get_duration(audio_path)
```

### Phase 3 Notes
**Completed 2026-01-19**

**Files Created:**
- `templates/array_animation.html` - Jinja2 template for array pointer animations
- `pipeline/adapters/animation/html.py` - HTMLAnimationAdapter implementation
- `pipeline/adapters/recorder/playwright.py` - PlaywrightRecorder implementation
- `tests/test_animation_adapters.py` - 16 tests (14 unit tests, 2 integration tests)

**Files Modified:**
- `pipeline/adapters/animation/__init__.py` - Exports HTMLAnimationAdapter
- `pipeline/adapters/recorder/__init__.py` - Exports PlaywrightRecorder
- `pipeline/adapters/__init__.py` - Exports all adapters for easy imports

**Implementation Details:**

1. **HTMLAnimationAdapter** (`pipeline/adapters/animation/html.py`)
   - Renders SceneSpec to HTML using Jinja2 templates
   - `render(spec, timing, output_path)` - Generates HTML file with embedded animation
   - Maps visualization types to templates (array_pointers -> array_animation.html)
   - Validates timing list length matches number of steps
   - Creates parent directories automatically

2. **PlaywrightRecorder** (`pipeline/adapters/recorder/playwright.py`)
   - Records HTML animations to WebM video using Playwright
   - `record(html_path, duration, output_path)` - Captures video of specified duration
   - Configurable viewport size (default: 1280x720)
   - Waits for `window.animationReady` before recording
   - Async implementation with sync wrapper for easy use

3. **array_animation.html** (Jinja2 template)
   - Dark theme with clean design
   - CSS animations for pointer movement and highlights
   - JavaScript timeline that steps through animation states
   - Sets `window.animationDuration` for recorder
   - Supports highlight modes: sum, found, left_move, right_move
   - Responsive array cells with pointer labels (L/R)

**Template Variables:**
- `{{ title }}` - Scene title
- `{{ array }}` - Array values (e.g., [2, 7, 11, 15])
- `{{ target }}` - Target sum
- `{{ steps }}` - List of step objects with state
- `{{ timing }}` - List of durations per step in seconds

**Design Decisions:**
1. HTML adapter only generates HTML; recording is separate (RecorderAdapter)
2. Playwright records to temp directory, then moves to final location
3. WebM format is native Playwright output; format conversion left to merger
4. Animation waits for `window.animationReady = true` before starting
5. Duration buffer of 0.5s added to ensure complete capture

**Tests:** 14 unit tests pass, 2 integration tests pass (require Playwright browsers)
- Unit tests use tempfile for isolated file operations
- Integration tests marked as `slow` for optional skipping
- Integration tests verify actual video file creation

**Usage Example:**
```python
from pathlib import Path
from pipeline.schema import SceneSpec
from pipeline.adapters.animation import HTMLAnimationAdapter
from pipeline.adapters.recorder import PlaywrightRecorder

# Load scene spec
spec = SceneSpec(**scene_data)
timing = [2.0, 3.0, 2.5]  # seconds per step

# Render HTML
html_adapter = HTMLAnimationAdapter(Path("templates"))
html_path = html_adapter.render(spec, timing, Path("output/animation.html"))

# Record to video
recorder = PlaywrightRecorder(viewport_width=1280, viewport_height=720)
total_duration = sum(timing)
video_path = recorder.record(html_path, total_duration, Path("output/video.webm"))
```

### Phase 4 Notes
**Completed 2026-01-19**

**Files Created:**
- `pipeline/adapters/merger/ffmpeg.py` - FFmpegMerger implementation
- `tests/test_merger_adapters.py` - 20 tests for merger adapter

**Files Modified:**
- `pipeline/adapters/merger/__init__.py` - Exports FFmpegMerger and FFmpegMergerError

**Implementation Details:**
1. `FFmpegMerger` class with configurable FFmpeg path (default: `~/.local/bin/ffmpeg`)
2. `concat_audio(audio_paths, output_path)` - Concatenates multiple audio files using FFmpeg concat demuxer
   - Automatically re-encodes when input/output formats differ (e.g., AIFF to M4A)
   - Uses stream copy (`-c copy`) when formats match for efficiency
3. `merge(video_path, audio_path, output_path)` - Merges video and audio streams
   - Uses `tpad` filter with `stop_mode=clone` and `stop=-1` to freeze last frame indefinitely
   - Uses `-shortest` flag so FFmpeg stops when audio ends
   - Output uses H.264 video (`libx264`) and AAC audio for wide compatibility
4. `FFmpegMergerError` exception class for all FFmpeg-related errors

**Design Decisions:**
1. FFmpeg path defaults to `~/.local/bin/ffmpeg` but is configurable via constructor
2. Missing input files raise `FFmpegMergerError` early (before calling FFmpeg)
3. Output directories are created automatically if they don't exist
4. Commands are logged for debugging (using Python logging)
5. When concatenating a single file, copies/converts directly without using concat demuxer (optimization)
6. Format detection based on file extensions to decide between stream copy and re-encoding

**FFmpeg Command Details:**
- Concat: `ffmpeg -f concat -safe 0 -i filelist.txt -c copy output.m4a` (or `-c:a aac` for format conversion)
- Merge: `ffmpeg -i video.webm -i audio.aiff -filter_complex "[0:v]tpad=stop_mode=clone:stop=-1[v]" -map "[v]" -map 1:a -c:v libx264 -c:a aac -shortest output.mp4`

**Tests:** 20 tests pass (18 unit tests with mocked subprocess, 2 integration tests with real FFmpeg)

**Usage Example:**
```python
from pipeline.adapters.merger import FFmpegMerger

merger = FFmpegMerger()

# Concatenate audio segments
audio_path = merger.concat_audio(
    [Path("step_0.aiff"), Path("step_1.aiff"), Path("step_2.aiff")],
    Path("output/audio.m4a")
)

# Merge video and audio (video extended if audio is longer)
final_path = merger.merge(
    Path("output/video.webm"),
    Path("output/audio.m4a"),
    Path("output/final.mp4")
)
```

### Phase 5 Notes
**Completed 2026-01-19**

**Files Created:**
- `pipeline/orchestrator.py` - PipelineOrchestrator class and BuildResult dataclass
- `build.py` - CLI entry point for building scenes
- `tests/test_orchestrator.py` - 22 tests (21 unit tests pass, 1 integration test skipped)

**Implementation Details:**

1. **PipelineOrchestrator** (`pipeline/orchestrator.py`)
   - Wires all adapters together (TTS, Animation, Recorder, Merger)
   - `build(scene_spec, dry_run=False)` - Executes the full 6-step pipeline
   - `build_from_file(scene_path)` - Loads JSON and builds
   - `build_from_file_dry_run(scene_path)` - Validates without building
   - Creates output subdirectory per scene (`output/{scene_id}/`)
   - Saves intermediate files: `step_*.aiff`, `timing.json`, `animation.html`, `video.webm`, `audio.m4a`, `final.mp4`
   - Logs progress at each step using Python logging
   - Returns `BuildResult` with timing info and success status

2. **BuildResult** (dataclass)
   - `scene_id`: Scene identifier
   - `output_path`: Path to final.mp4
   - `timing`: List of step durations in seconds
   - `total_duration`: Sum of all step durations
   - `success`: Boolean success flag
   - `error`: Error message if failed
   - `intermediate_files`: Dict of intermediate file paths for debugging

3. **build.py** (CLI)
   - `python build.py scene.json` - Build single scene
   - `python build.py scenes/ --all` - Build all scenes in directory
   - `--tts macos_say` - Select TTS adapter
   - `--voice Samantha` - Select TTS voice
   - `-o output/` - Specify output directory
   - `--dry-run` - Validate without building
   - `-v` - Verbose logging
   - Prints summary with success/failure counts

**Pipeline Steps:**
1. Generate TTS audio for each narration step (`step_*.aiff`)
2. Extract duration from each audio file
3. Save timing.json for debugging
4. Render animation HTML with timing
5. Record animation to WebM video
6. Concatenate audio segments to M4A
7. Merge video + audio to final MP4

**Error Handling:**
- Each step wrapped in try/except
- Failed builds return `BuildResult(success=False, error=...)`
- Intermediate files preserved for debugging failed builds
- PipelineError raised for file not found or parse errors

**Tests:** 21 unit tests pass, 1 integration test skipped (requires all dependencies)
- Unit tests use mock adapters for isolation
- Integration test marked with `@pytest.mark.slow`
- Integration test checks for real dependencies before running

**Usage Example:**
```bash
# Validate a scene
python build.py tests/fixtures/sample_scene.json --dry-run

# Build a scene
python build.py tests/fixtures/sample_scene.json -o output/

# Build all scenes with verbose logging
python build.py scenes/ --all -v
```

### Phase 6 Notes
_Pending implementation_
