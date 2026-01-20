# LeetDreamer - Algorithm Visualization Pipeline

## What This Is
A modular pipeline for generating narrated algorithm visualization videos. The system uses an audio-first approach: generate TTS audio, extract durations, then drive animation timing from those durations.

## Quick Start
```bash
python build.py scenes/two_pointers/scene.json -v
```

## Key Directories
- `scenes/` - Scene specifications (the product - narration + visualization state)
- `pipeline/` - Core pipeline code and adapters
- `templates/` - Jinja2 HTML animation templates
- `output/` - Generated videos (gitignored)

## Local Tools (not in PATH)
- **FFmpeg**: `~/.local/bin/ffmpeg` - video/audio processing

## Architecture
See ARCHITECTURE.md for full documentation. Key concepts:
- Adapter pattern for swappable TTS, animation, recording, merging
- Pydantic schema validation for scene specs
- Single source of truth (scene.json) controls both animation and narration

## Narration Guidelines
- One small phrase per step
- Be specific: "move the right pointer left" not "move right again"
- Brief pauses between phrases
- Keep pace comfortable for comprehension
