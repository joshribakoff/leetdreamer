# 🎬 LeetDreamer

> *"What if algorithm explanations didn't put you to sleep?"*

A pipeline that generates narrated algorithm visualization videos. Because staring at code for 3 hours is less effective than watching a robot explain Two Pointers in 37 seconds.

### 🎥 See it in action

[![Two Pointers Animation - Click to Watch](https://img.youtube.com/vi/6jwh-N3D8l4/maxresdefault.jpg)](https://www.youtube.com/watch?v=6jwh-N3D8l4)

*👆 Click to watch the generated video on YouTube*

## The Problem

- **VisuAlgo**: Great for bubble sort. Useless for LeetCode 42.
- **YouTube tutorials**: 20 minutes of "hey guys" before any content
- **Static diagrams**: Can't show *when* things happen
- **Your own explanations**: You understand it until you try to explain it

## The Solution

Write a scene spec → Get a narrated video. That's it.

```bash
python build.py scenes/two_pointers/scene.json -v
```

Output: A video where a robot voice explains the algorithm while colorful boxes do the thinking for you.

## How It Works

1. **You write**: A JSON scene spec with narration text and visualization state
2. **Pipeline generates**: TTS audio for each step
3. **Pipeline renders**: HTML animation timed to the audio
4. **Pipeline merges**: Audio + video = learning material

```
scene.json → 🎤 TTS → 🎨 Animation → 🎬 Final Video
                ↓
           Extract durations → Drive animation timing
```

The secret sauce: **audio-first sync**. Generate the voice track first, measure how long each phrase takes, then make the animation match. No more desynced disasters.

## Installation

```bash
# Clone it
git clone https://github.com/joshribakoff/leetdreamer.git
cd leetdreamer

# Install dependencies
pip install playwright pydantic jinja2
playwright install chromium

# You'll also need FFmpeg somewhere
```

## Creating a Scene

Scenes live in `scenes/<name>/scene.json`:

```json
{
  "id": "my_algorithm",
  "title": "My Algorithm: O(magic)",
  "steps": [
    {
      "id": "step1",
      "narration": "First, we do the thing.",
      "state": {"highlight": "thing"}
    }
  ]
}
```

The narration becomes audio. The state drives the visualization. Simple.

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full nerd version. Key points:

- **Adapters** for everything (TTS, animation, recording, merging)
- **Pydantic** validation so your scene spec can't be wrong
- **Jinja2** templates for HTML animations

Want to swap macOS `say` for OpenAI TTS? Change one adapter. Want Manim instead of HTML? Change one adapter. The dream is modularity.

## Requirements

- Python 3.10+
- Playwright (for screen recording)
- FFmpeg (for audio/video merging)
- macOS (for the `say` TTS adapter... for now)

## Status

🚧 **Early days** - The bones work, the flesh is still forming.

Currently renders: Two Pointers (Two Sum II)

Coming eventually: Sliding Window, Binary Search, DP visualizations, maybe your algorithm if you ask nicely.

## Related Projects

| Project | What It Does |
|---------|--------------|
| [LeetDeeper](https://github.com/joshribakoff/leetdeeper) | The study workspace where I actually solve problems. LeetDreamer exists because I got tired of explaining Two Pointers to myself. |

*LeetDeeper is the brain. LeetDreamer is the mouth. Together they form one very nerdy Voltron.*

## License

MIT - Do whatever you want, just don't blame me when the robot voice mispronounces "deque".
