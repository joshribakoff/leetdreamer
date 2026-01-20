"""
Merger adapters for combining audio and video.
"""

from .ffmpeg import FFmpegMerger, FFmpegMergerError

__all__ = ["FFmpegMerger", "FFmpegMergerError"]
