"""
Vidaptive Talk 2: Video Conferencing Issues (Title + Source Overlay)

This Manim script creates an overlay scene with:
- Title: "Issues in Video Conferencing" at the top
- Source: YouTube link at the bottom

You then composite this overlay on top of the real video
`example_1_15_to_1_50.mp4` using ffmpeg.
"""

from manim import *


class VideoConferencingIssues(Scene):
    """Overlay scene: title + source, sized for 16:9 video."""

    def construct(self):
        # Match your main project's style
        self.camera.background_color = "#000000"

        # Title at top
        title = Text(
            "Issues in Video Conferencing",
            font_size=60,
            color=WHITE,
            weight=BOLD,
        ).to_edge(UP, buff=0.3)

        # Source at bottom in small italic font
        source = Text(
            "source: https://www.youtube.com/watch?v=JMOOG7rWTPg",
            font_size=20,
            color=GREY_B,
            slant=ITALIC,
        ).to_edge(DOWN, buff=0.3)

        self.add(title, source)

        # Hold for the duration of your clip.
        # `example_1_15_to_1_50.mp4` is ~23.015 seconds
        self.wait(23.015)
