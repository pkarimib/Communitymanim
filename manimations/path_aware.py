# Render: manim -pqh path_aware.py PathAwareGradientScene
#
# Slide: "MetaEase's Idea To Handle Non-Differentiability."
# Companion to gp_surrogate.py -- same visual language (white bg, purple
# accent, academic / clean). This one is purely 2D input-space geometry.

from manim import *
import numpy as np

# Palette matched to the deck + the previous animation
PURPLE_ACCENT = "#5A2D82"
SOFT_GREEN = "#C5E0B4"
SOFT_BLUE = "#B4C7E7"    # focus class
SOFT_YELLOW = "#FFE699"  # "other" class
POINT_RED = "#D62728"    # reserved for the "invalid" X indicator only
GRADIENT_ORANGE = "#F39C12"
PROJECTION_GREEN = "#2E86AB"
SAMPLE_GRAY = "#808080"  # match gp_surrogate.py sample color
BOUNDARY_COLOR = BLACK
TEXT_FONT = "Arial"


class PathAwareGradientScene(Scene):
    def construct(self):
        self.camera.background_color = WHITE

        # ==================================================================
        # Step 1 (0-3s): title + 2D input-space grid with axes
        # ==================================================================
        # title = Text(
        #     "Path-Aware Gradient Ascent",
        #     font=TEXT_FONT, font_size=34, color=PURPLE_ACCENT, weight=BOLD,
        # ).to_edge(UP, buff=0.3)

        plane = NumberPlane(
            x_range=[-5, 5, 1],
            y_range=[-3, 3, 1],
            x_length=9.0,
            y_length=5.4,
            background_line_style={
                "stroke_color": GRAY_B,
                "stroke_width": 1,
                "stroke_opacity": 0.3,
            },
            axis_config={
                "color": BLACK,
                "stroke_width": 2,
                "include_tip": True,
            },
            faded_line_ratio=0,
        ).shift(DOWN * 0.25)

        # c2p shortcut for data -> screen coords
        def c2p(x, y):
            return plane.c2p(x, y)

        x_ax_label = MathTex(
            r"x_1", color=BLACK, font_size=28,
        ).next_to(plane.x_axis.get_end(), DOWN, buff=0.15)
        y_ax_label = MathTex(
            r"x_2", color=BLACK, font_size=28,
        ).next_to(plane.y_axis.get_end(), LEFT, buff=0.15)

        # self.play(FadeIn(title), run_time=0.8)
        self.play(
            Create(plane),
            FadeIn(x_ax_label),
            FadeIn(y_ax_label),
            run_time=1.6,
        )
        self.wait(0.3)

        # ==================================================================
        # Step 2 (3-7s): equivalence class regions
        # ==================================================================
        # Two classes only: a blue focus strip in the middle, yellow on either
        # side. Two straight-line boundaries.
        green_left_pts = [(-5, 3), (-1, 3), (0.5, -3), (-5, -3)]
        blue_pts = [(-1, 3), (2, 3), (2.5, -3), (0.5, -3)]          # focus
        yellow_right_pts = [(2, 3), (5, 3), (5, -3), (2.5, -3)]

        green_left = Polygon(*[c2p(*p) for p in green_left_pts],
                              color=SOFT_GREEN, fill_opacity=0.45, stroke_width=0)
        blue_region = Polygon(*[c2p(*p) for p in blue_pts],
                              color=SOFT_BLUE, fill_opacity=0.45, stroke_width=0)
        yellow_right = Polygon(*[c2p(*p) for p in yellow_right_pts],
                               color=SOFT_YELLOW, fill_opacity=0.45, stroke_width=0)
        regions = VGroup(green_left, blue_region, yellow_right)

        boundary_left = Line(c2p(-1, 3), c2p(0.5, -3),
                             color=BOUNDARY_COLOR, stroke_width=1.8)
        boundary_right = Line(c2p(2, 3), c2p(2.5, -3),
                              color=BOUNDARY_COLOR, stroke_width=1.8)
        boundaries = VGroup(boundary_left, boundary_right)

        class_label = MathTex(
            r"\text{Class} = \text{code-path}(I)",
            color=PURPLE_ACCENT, font_size=26,
        ).to_edge(DOWN, buff=0.15)

        self.play(FadeIn(regions), run_time=1.0)
        self.play(
            Create(boundaries),
            FadeIn(class_label),
            run_time=1.3,
        )
        self.wait(1.0)

        # ==================================================================
        # Step 3 (7-10s): fade other classes; focus on the blue strip
        # ==================================================================
        gap_nonzero_label = MathTex(
            r"\text{Gap} \ne 0",
            color=PURPLE_ACCENT, font_size=26,
        ).move_to(c2p(0.75, 2.4))

        gap_zero_label_left = MathTex(
            r"\text{Gap} \ne 0",
            color=GRAY, font_size=22,
        ).move_to(c2p(-3, 2.4))

        gap_zero_label_right = MathTex(
            r"\text{Gap} = 0",
            color=GRAY, font_size=22,
        ).move_to(c2p(3.8, 2.4))

        self.play(
            green_left.animate.set_fill(opacity=0.15),
            yellow_right.animate.set_fill(opacity=0.15),
            blue_region.animate.set_fill(opacity=0.55),
            FadeOut(class_label),
            FadeIn(gap_nonzero_label),
            FadeIn(gap_zero_label_left),
            FadeIn(gap_zero_label_right),
            run_time=1.6,
        )
        self.wait(1.2)

        # ==================================================================
        # Step 4 (10-14s): point I + Delta-box + 10 samples
        # ==================================================================
        I_data = (1.8, 0.3)
        I_pos = c2p(*I_data)
        I_dot = Dot(I_pos, color=PURPLE_ACCENT, radius=0.1)
        I_label = MathTex("I", color=PURPLE_ACCENT, font_size=32).next_to(
            I_dot, UL, buff=0.05,
        )

        half_d = 0.7  # in data coords
        box = Polygon(
            c2p(I_data[0] - half_d, I_data[1] - half_d),
            c2p(I_data[0] + half_d, I_data[1] - half_d),
            c2p(I_data[0] + half_d, I_data[1] + half_d),
            c2p(I_data[0] - half_d, I_data[1] + half_d),
            color=BLACK, stroke_width=2, fill_opacity=0,
        )

        # Hand-picked samples -- 7 in-class (left of the blue/green boundary),
        # 3 out-of-class (right of it). Chosen so the gradient-aligned pick
        # is visually clear in step 7.
        in_class_samples = [
            (1.3, 0.8), (1.7, 0.9), (2.1, 0.6),
            (1.2, 0.1), (1.5, -0.3), (1.9, -0.2), (2.1, 0.2),
        ]
        out_class_samples = [
            (2.4, 0.5), (2.5, 0.85), (2.3, -0.3),
        ]

        in_dots = [Dot(c2p(*p), color=SAMPLE_GRAY, radius=0.055)
                   for p in in_class_samples]
        out_dots = [Dot(c2p(*p), color=SAMPLE_GRAY, radius=0.055)
                    for p in out_class_samples]
        all_sample_dots = in_dots + out_dots

        self.play(
            FadeIn(I_dot), FadeIn(I_label), Create(box),
            run_time=1.2,
        )
        self.play(
            LaggedStart(
                *[FadeIn(d, scale=0.6) for d in all_sample_dots],
                lag_ratio=0.1,
            ),
            run_time=1.8,
        )
        self.wait(0.6)

        # ==================================================================
        # Step 5 (14-18s): filter samples by code path
        # ==================================================================
        # Small shake on each invalid sample, then fade.
        shake_then_fade = []
        for d in out_dots:
            shake_then_fade.append(
                Succession(
                    d.animate(run_time=0.08).shift(LEFT * 0.05),
                    d.animate(run_time=0.08).shift(RIGHT * 0.1),
                    d.animate(run_time=0.08).shift(LEFT * 0.05),
                    FadeOut(d, run_time=0.4),
                )
            )
        self.play(
            LaggedStart(*shake_then_fade, lag_ratio=0.1),
            run_time=1.4,
        )

        filter_caption = MathTex(
            r"Class(I) = \{\, x \in \text{box} \;\mid\; \text{code-path}(x) = \text{code-path}(I)\,\}",
            color=PURPLE_ACCENT, font_size=24,
        ).to_edge(DOWN, buff=0.35)
        self.play(FadeIn(filter_caption), run_time=0.8)
        self.wait(0.8)

        # ==================================================================
        # Step 6 (18-23s): proposed gradient step -- lands outside the class
        # ==================================================================
        grad_dir = np.array([0.5, 1.0])
        grad_dir = grad_dir / np.linalg.norm(grad_dir)
        grad_len = 1.7  # in data coords; long enough to exit the blue strip
        grad_end_data = (I_data[0] + grad_dir[0] * grad_len,
                         I_data[1] + grad_dir[1] * grad_len)

        grad_arrow = Arrow(
            start=I_pos,
            end=c2p(*grad_end_data),
            color=GRADIENT_ORANGE,
            stroke_width=5,
            buff=0.1,
            max_tip_length_to_length_ratio=0.14,
        )
        grad_arrow_label = MathTex(
            r"I + \eta\,\nabla \text{Gap}(I)",
            color=GRADIENT_ORANGE, font_size=26,
        ).next_to(grad_arrow.get_end(), UR, buff=0.08)

        self.play(GrowArrow(grad_arrow), run_time=1.1)
        self.play(FadeIn(grad_arrow_label), run_time=0.5)
        self.wait(0.3)

        # Red X at the tip: "invalid, crosses the boundary"
        x_size = 0.13
        red_x = VGroup(
            Line(UP * x_size + LEFT * x_size,
                 DOWN * x_size + RIGHT * x_size,
                 color=POINT_RED, stroke_width=5),
            Line(UP * x_size + RIGHT * x_size,
                 DOWN * x_size + LEFT * x_size,
                 color=POINT_RED, stroke_width=5),
        ).move_to(grad_arrow.get_end())

        self.play(FadeIn(red_x, scale=0.6), run_time=0.4)
        self.play(red_x.animate.scale(1.25),
                  rate_func=there_and_back, run_time=0.6)
        self.wait(0.4)

        # ==================================================================
        # Step 7 (23-28s): project back -- find best-aligned in-class sample
        # ==================================================================
        # Fade the orange arrow down (keep visible as "wanted direction")
        self.play(
            grad_arrow.animate.set_opacity(0.35),
            grad_arrow_label.animate.set_opacity(0.35),
            FadeOut(red_x),
            run_time=0.5,
        )

        # Dotted lines from I to each in-class sample
        dotted_lines = [
            DashedLine(
                I_pos, c2p(*p),
                color=SAMPLE_GRAY, stroke_width=1.5, dash_length=0.07,
            ).set_opacity(0.55)
            for p in in_class_samples
        ]
        self.play(
            LaggedStart(*[Create(dl) for dl in dotted_lines],
                        lag_ratio=0.07),
            run_time=1.2,
        )
        self.wait(0.4)

        # Winner = sample most aligned with the gradient direction.
        winner_idx = 2  # (2.1, 0.6) -- highest cosine with grad_dir
        winner_data = in_class_samples[winner_idx]
        winner_pos = c2p(*winner_data)

        winner_dot = Dot(winner_pos, color=PROJECTION_GREEN, radius=0.09)
        winner_label = MathTex(
            r"\text{Most\;Aligned\;Sample}", color=PROJECTION_GREEN, font_size=28,
        ).next_to(winner_dot, UR, buff=0.08)

        proj_arrow = Arrow(
            start=I_pos, end=winner_pos,
            color=PROJECTION_GREEN,
            stroke_width=5,
            buff=0.12,
            max_tip_length_to_length_ratio=0.18,
        )

        non_winner_dls = [dl for i, dl in enumerate(dotted_lines)
                          if i != winner_idx]
        self.play(
            FadeOut(VGroup(*non_winner_dls)),
            FadeOut(in_dots[winner_idx]),
            FadeIn(winner_dot),
            FadeIn(winner_label),
            run_time=0.8,
        )
        self.play(
            FadeOut(dotted_lines[winner_idx]),
            GrowArrow(proj_arrow),
            run_time=0.8,
        )
        self.wait(1.2)

        # ==================================================================
        # Step 8 (28-32s): take the step -- I slides to m_i, box follows
        # ==================================================================
        shift_delta = winner_pos - I_pos
        other_in_dots = [d for i, d in enumerate(in_dots) if i != winner_idx]

        self.play(
            I_dot.animate.move_to(winner_pos),
            I_label.animate.shift(shift_delta),
            box.animate.shift(shift_delta),
            FadeOut(winner_dot),
            FadeOut(winner_label),
            FadeOut(proj_arrow),
            FadeOut(grad_arrow),
            FadeOut(grad_arrow_label),
            FadeOut(VGroup(*other_in_dots)),
            FadeOut(filter_caption),
            run_time=2.0,
        )
        self.wait(0.8)

        # ==================================================================
        # Step 9 (32-38s): punchline
        # ==================================================================
        punchline_text = Text(
            "Path-aware gradient ascent: stay within the equivalence class",
            font=TEXT_FONT, font_size=26, color=WHITE,
        )
        punch_box = SurroundingRectangle(
            punchline_text,
            color=PURPLE_ACCENT,
            fill_color=PURPLE_ACCENT,
            fill_opacity=1.0,
            stroke_width=0,
            buff=0.25,
        )
        punchline_group = VGroup(punch_box, punchline_text).to_edge(
            DOWN, buff=0.35,
        )

        self.play(FadeIn(punchline_group), run_time=1.2)
        self.wait(3.0)

        # Fade to white
        self.play(
            FadeOut(Group(*self.mobjects)),
            run_time=1.2,
        )
