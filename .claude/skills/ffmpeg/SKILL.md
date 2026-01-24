# FFmpeg Video/Audio Processing

## Video Concatenation

**Never use concat demuxer for videos with audio.** It corrupts audio timestamps at segment boundaries.

### ❌ Broken (concat demuxer)
```bash
# Creates file list then:
ffmpeg -f concat -safe 0 -i filelist.txt -c copy output.mp4
# Audio cuts out or stutters on second+ segments
```

### ✅ Fixed (filter_complex)
```bash
ffmpeg -y \
  -i video1.mp4 \
  -i video2.mp4 \
  -i video3.mp4 \
  -filter_complex "[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1[outv][outa]" \
  -map "[outv]" -map "[outa]" \
  -c:v libx264 -c:a aac -ar 44100 \
  output.mp4
```

**Why it works**: filter_complex fully decodes and re-encodes all streams, ensuring proper timestamp synchronization. The demuxer just copies bytes and can't fix timestamp discontinuities.

## Audio Concatenation

For audio-only files, concat demuxer is fine:
```bash
ffmpeg -f concat -safe 0 -i filelist.txt -c:a aac output.m4a
```

## Merging Video + Audio

When video and audio have different durations:
```bash
ffmpeg -y \
  -i video.webm \
  -i audio.m4a \
  -filter_complex "[0:v]tpad=stop_mode=clone:stop=-1[v]" \
  -map "[v]" -map "1:a" \
  -c:v libx264 -c:a aac \
  -shortest \
  output.mp4
```

`tpad=stop_mode=clone:stop=-1` extends video by cloning last frame if audio is longer.
`-shortest` trims to shorter stream.

## Common Issues

1. **"Unable to choose output format"** - Output path is empty or malformed
2. **Audio stuttering after concat** - Use filter_complex, not concat demuxer
3. **Video/audio desync** - Check sample rates match, use `-ar 44100` to normalize
