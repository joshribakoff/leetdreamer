"""
Playwright Recorder Adapter.

Records HTML animations to video files using Playwright's screen recording.
"""

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

from ..base import RecorderAdapter


class PlaywrightRecorder(RecorderAdapter):
    """Adapter that records HTML animations to video using Playwright.

    Uses Playwright's built-in video recording capability to capture
    HTML animations. The HTML page should set window.animationDuration
    to indicate the total animation length.

    Attributes:
        viewport_width: Width of the recording viewport
        viewport_height: Height of the recording viewport
    """

    def __init__(self, viewport_width: int = 1280, viewport_height: int = 720):
        """Initialize the Playwright recorder.

        Args:
            viewport_width: Width of the recording viewport in pixels
            viewport_height: Height of the recording viewport in pixels
        """
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

    @property
    def name(self) -> str:
        """Adapter identifier for logging."""
        return "playwright"

    def record(self, html_path: Path, duration: float, output_path: Path) -> Path:
        """Record an HTML animation to video.

        Args:
            html_path: Path to the HTML file to record
            duration: Total duration to record in seconds
            output_path: Path where the video should be saved

        Returns:
            Path to the recorded video file
        """
        return asyncio.run(self._record_async(html_path, duration, output_path))

    async def _record_async(self, html_path: Path, duration: float, output_path: Path) -> Path:
        """Async implementation of video recording.

        Args:
            html_path: Path to the HTML file to record
            duration: Total duration to record in seconds
            output_path: Path where the video should be saved

        Returns:
            Path to the recorded video file
        """
        html_path = Path(html_path).resolve()
        output_path = Path(output_path)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Playwright records to a directory, then we rename the file
        video_dir = output_path.parent / "_video_temp"
        video_dir.mkdir(parents=True, exist_ok=True)

        async with async_playwright() as p:
            browser = await p.chromium.launch()

            context = await browser.new_context(
                viewport={
                    "width": self.viewport_width,
                    "height": self.viewport_height
                },
                record_video_dir=str(video_dir),
                record_video_size={
                    "width": self.viewport_width,
                    "height": self.viewport_height
                }
            )

            page = await context.new_page()

            # Navigate to the HTML file
            await page.goto(f"file://{html_path}")

            # Wait for animation to be ready
            await page.wait_for_function("window.animationReady === true", timeout=10000)

            # Wait for animation duration plus a small buffer
            # The buffer accounts for initial render and any transition effects
            wait_time = (duration + 0.5) * 1000  # Convert to milliseconds
            await page.wait_for_timeout(wait_time)

            # Close context to finalize video
            await context.close()
            await browser.close()

        # Find the recorded video file (Playwright names it randomly)
        video_files = list(video_dir.glob("*.webm"))
        if not video_files:
            raise RuntimeError("No video file was recorded")

        recorded_video = video_files[0]

        # Move to final location
        if output_path.suffix.lower() == ".webm":
            recorded_video.rename(output_path)
        else:
            # If a different format is requested, just rename with warning
            # (actual conversion would require ffmpeg, which is handled by merger)
            output_path = output_path.with_suffix(".webm")
            recorded_video.rename(output_path)

        # Clean up temp directory
        try:
            video_dir.rmdir()
        except OSError:
            pass  # Directory not empty or other issue, leave it

        return output_path

    async def record_async(self, html_path: Path, duration: float, output_path: Path) -> Path:
        """Public async interface for recording.

        Use this if you're already in an async context.

        Args:
            html_path: Path to the HTML file to record
            duration: Total duration to record in seconds
            output_path: Path where the video should be saved

        Returns:
            Path to the recorded video file
        """
        return await self._record_async(html_path, duration, output_path)
