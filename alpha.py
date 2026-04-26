"""
Vidaptive Alpha Animation: Controlling Tail Frame Transmission Times

This animation explains how Vidaptive adjusts the encoder rate (α) so that
the tail of the frame transmission-time distribution fits within a latency budget P.

Duration: ~12-15 seconds
Render with: manim -pqh alpha.py AlphaControlAnimation
"""

from manim import *
import numpy as np
import math


# ============================================================================
# CONFIGURATION
# ============================================================================

config.frame_rate = 30
config.frame_width = 16
config.frame_height = 9

# Color palette (clean, conference-style)
DISTRIBUTION_COLOR = "#3498db"  # Blue for normal frames
TAIL_COLOR = "#e74c3c"  # Red for tail/violation
SAFE_COLOR = "#2ecc71"  # Green for safe
BUDGET_COLOR = "#f39c12"  # Orange for P
ALPHA_COLOR = "#9b59b6"  # Purple for α
BACKGROUND_COLOR = "#FFFFFF"  # White background for conference style
TEXT_COLOR = "#2c3e50"  # Dark text


# ============================================================================
# MAIN ANIMATION
# ============================================================================

class AlphaControlAnimation(Scene):
    """
    Complete animation showing how α controls tail frame transmission times.
    
    Scenes:
    1. Show the distribution (3s)
    2. Highlight the tail (2s)
    3. Tail exceeds P (2s)
    4. Introduce α (2s)
    5. Shrink the distribution (3s)
    6. Tail matches P (2-3s)
    """
    
    def construct(self):
        # Set background
        self.camera.background_color = BACKGROUND_COLOR
        
        # Scene 1: Show the distribution (3s)
        self.scene_1_show_distribution()
        
        # Scene 2: Highlight the tail (2s)
        self.scene_2_highlight_tail()
        
        # Scene 3: Tail exceeds P (2s)
        self.scene_3_tail_exceeds_budget()
        
        # Scene 4: Introduce α (2s)
        self.scene_4_introduce_alpha()
        
        # Scene 5: Shrink the distribution (3s)
        self.scene_5_shrink_distribution()
        
        # Scene 6: Tail matches P (2-3s)
        self.scene_6_tail_matches_budget()
    
    def scene_1_show_distribution(self):
        """Scene 1: Show the distribution (~3 seconds)"""
        
        # Create axes
        self.axes = Axes(
            x_range=[0, 50, 10],
            y_range=[0, 0.1, 0.02],
            x_length=10,
            y_length=5,
            axis_config={
                "color": TEXT_COLOR,
                "stroke_width": 2,
                "font_size": 24,
            },
            tips=False,
        ).shift(DOWN * 0.5)
        
        # Axis labels
        x_label = Text(
            "Frame transmission time (ms)",
            font_size=30,
            color=TEXT_COLOR,
        ).next_to(self.axes.x_axis, DOWN, buff=0.4)
        
        y_label = Text(
            "Distribution",
            font_size=30,
            color=TEXT_COLOR,
        ).next_to(self.axes.y_axis, LEFT, buff=0.4).rotate(PI / 2)
        
        # Create distribution (gamma-like distribution)
        # Initial distribution: mean around 20ms, some tail
        def initial_dist(x):
            if x <= 0:
                return 0
            # Gamma-like shape
            k = 3.5  # shape
            theta = 6.0  # scale
            return (x ** (k - 1) * np.exp(-x / theta)) / (theta ** k * math.gamma(k))
        
        self.distribution_curve = self.axes.plot(
            initial_dist,
            x_range=[0.1, 50],
            color=DISTRIBUTION_COLOR,
            stroke_width=4,
        )
        
        # Fill under curve
        self.distribution_fill = self.axes.get_area(
            self.distribution_curve,
            x_range=[0.1, 50],
            color=DISTRIBUTION_COLOR,
            opacity=0.3,
        )
        
        # Latency budget P line (at 33ms)
        self.P_value = 33
        self.P_line = DashedLine(
            start=self.axes.c2p(self.P_value, 0),
            end=self.axes.c2p(self.P_value, 0.08),
            color=BUDGET_COLOR,
            stroke_width=3,
            dash_length=0.15,
        )
        
        self.P_label = Text(
            "Target Latency (P = 33 ms)",
            font_size=28,
            color=BUDGET_COLOR,
            weight=BOLD,
        ).next_to(self.P_line, UP, buff=0.2)
        
        # Initial tail line (at 40ms) - shown without text
        self.initial_tail_x = 40
        self.initial_tail_line = DashedLine(
            start=self.axes.c2p(self.initial_tail_x, 0),
            end=self.axes.c2p(self.initial_tail_x, 0.05),
            color=TAIL_COLOR,
            stroke_width=3,
            dash_length=0.1,
        )
        
        # Animate
        self.play(
            Create(self.axes),
            Write(x_label),
            Write(y_label),
            run_time=1,
        )
        # Removed dist_label animation per user request
        self.play(
            Create(self.distribution_curve),
            FadeIn(self.distribution_fill),
            run_time=1.5,
        )
        self.play(
            Create(self.P_line),
            Write(self.P_label),
            Create(self.initial_tail_line),
            run_time=0.5,
        )
        
        # Store objects for later scenes
        # self.dist_label = dist_label  # Removed
        self.x_label = x_label
        self.y_label = y_label
    
    def scene_2_highlight_tail(self):
        """Scene 2: Highlight the tail (~2 seconds)"""
        
        # Create tail highlight (area beyond the initial tail at 40ms, not from P)
        tail_start = self.initial_tail_x  # Use 40ms, not 33ms
        
        def initial_dist(x):
            if x <= 0:
                return 0
            k = 3.5
            theta = 6.0
            return (x ** (k - 1) * np.exp(-x / theta)) / (theta ** k * math.gamma(k))
        
        self.tail_fill = self.axes.get_area(
            self.distribution_curve,
            x_range=[tail_start, 50],
            color=TAIL_COLOR,
            opacity=0.5,
        )
        
        # Animate
        self.play(
            FadeIn(self.tail_fill),
            run_time=1,
        )
        # Removed tail_label animation
        
        # Subtle pulse effect
        self.play(
            self.tail_fill.animate.set_opacity(0.7),
            rate_func=there_and_back,
            run_time=1,
        )
    
    def scene_3_tail_exceeds_budget(self):
        """Scene 3: Tail exceeds P (~2 seconds)"""
        
        # Warning text only (no icon) - moved to the left
        warning_text = Text(
            "Very slow frames",
            font_size=30,
            color=TAIL_COLOR,
            weight=BOLD,
        ).move_to(self.axes.c2p(50, 0.035))
        
        # Animate
        self.play(
            Write(warning_text),
            run_time=1,
        )
        self.wait(1)
        
        # Store for cleanup
        self.warning_text = warning_text
    
    def scene_4_introduce_alpha(self):
        """Scene 4: Introduce α (~2 seconds)"""
        
        # Alpha slider
        slider_y = -3.5
        
        slider_line = Line(
            LEFT * 3, RIGHT * 3,
            color=ALPHA_COLOR,
            stroke_width=4,
        ).shift(DOWN * slider_y)
        
        slider_label = Text(
            "α (traget bitrate)",
            font_size=30,
            color=ALPHA_COLOR,
            weight=BOLD,
        ).next_to(slider_line, LEFT, buff=0.5)
        
        # Slider dot (starting high)
        self.alpha_position = 0.6  # 0 to 1, where 1 is high
        slider_dot = Dot(
            slider_line.point_from_proportion(self.alpha_position),
            color=ALPHA_COLOR,
            radius=0.15,
        )
        
        alpha_value_text = Text(
            "α high",
            font_size=26,
            color=ALPHA_COLOR,
        ).next_to(slider_dot, DOWN, buff=0.3)
        
        # Animate
        self.play(
            Create(slider_line),
            Write(slider_label),
            run_time=0.8,
        )
        self.play(
            FadeIn(slider_dot, scale=1.2),
            Write(alpha_value_text),
            run_time=1.2,
        )
        
        # Store for next scene
        self.slider_line = slider_line
        self.slider_dot = slider_dot
        self.alpha_value_text = alpha_value_text
        # self.control_arrow = control_arrow  # Removed
        # self.control_label = control_label  # Removed
    
    def scene_5_shrink_distribution(self):
        """Scene 5: Shrink the distribution (~3 seconds)"""
        
        # Tail line already exists from scene_1 as self.initial_tail_line
        # No need to create it again
        
        # New distribution (compressed - lower mean, less variance)
        def compressed_dist(x):
            if x <= 0:
                return 0
            # Shifted and compressed
            k = 4.0  # slightly more peaked
            theta = 4.5  # lower scale = shift left
            return (x ** (k - 1) * np.exp(-x / theta)) / (theta ** k * math.gamma(k))
        
        new_distribution_curve = self.axes.plot(
            compressed_dist,
            x_range=[0.1, 40],
            color=DISTRIBUTION_COLOR,
            stroke_width=4,
        )
        
        new_distribution_fill = self.axes.get_area(
            new_distribution_curve,
            x_range=[0.1, 40],
            color=DISTRIBUTION_COLOR,
            opacity=0.3,
        )
        
        # New tail (should be smaller and within P)
        new_tail_fill = self.axes.get_area(
            new_distribution_curve,
            x_range=[self.P_value, 40],
            color=SAFE_COLOR,  # Green now
            opacity=0.5,
        )
        
        # New tail line position (at x=32, just before P)
        new_tail_x = 32
        new_tail_line = DashedLine(
            start=self.axes.c2p(new_tail_x, 0),
            end=self.axes.c2p(new_tail_x, 0.05),
            color=SAFE_COLOR,
            stroke_width=3,
            dash_length=0.1,
        )
        
        # Update slider
        new_alpha_position = 0.3
        new_slider_dot_pos = self.slider_line.point_from_proportion(new_alpha_position)
        
        new_alpha_value_text = Text(
            "α decreased",
            font_size=26,
            color=ALPHA_COLOR,
        ).next_to(new_slider_dot_pos, DOWN, buff=0.3)
        
        # Animate the key moment
        self.play(
            # Move slider left
            self.slider_dot.animate.move_to(new_slider_dot_pos),
            Transform(self.alpha_value_text, new_alpha_value_text),
            run_time=1,
        )
        
        self.play(
            # Shrink distribution
            Transform(self.distribution_curve, new_distribution_curve),
            Transform(self.distribution_fill, new_distribution_fill),
            Transform(self.tail_fill, new_tail_fill),
            # Move tail line
            Transform(self.initial_tail_line, new_tail_line),
            # Fade out warning
            FadeOut(self.warning_text),
            run_time=1.5,
        )
        
        # Store new objects
        self.new_tail_fill = self.tail_fill  # It's been transformed
    
    def scene_6_tail_matches_budget(self):
        """Scene 6: Tail matches P (~2-3 seconds)"""
        
        # New tail label (green)
        tail_safe_label = Text(
            "Tail meets latency budget ✓",
            font_size=28,
            color=SAFE_COLOR,
            weight=BOLD,
        ).move_to(self.axes.c2p(46, 0.03))

        # Animate
        self.play(
            Write(tail_safe_label),
            run_time=1,
        )
        # Removed caption animation
        self.wait(2)


# ============================================================================
# RENDERING INSTRUCTIONS
# ============================================================================
"""
TO RENDER:
    manim -pqh alpha.py AlphaControlAnimation

For lower quality (faster):
    manim -pql alpha.py AlphaControlAnimation

For GIF export (add after rendering):
    ffmpeg -i media/videos/alpha/1080p60/AlphaControlAnimation.mp4 -vf "fps=15,scale=1080:-1:flags=lanczos" -loop 0 alpha.gif

NOTES:
- Duration: ~12-15 seconds
- Clean, conference-style design
- White background, professional colors
- No equations, just intuition
"""
