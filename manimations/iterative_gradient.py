# Render: manim -pqh iterative_gradient.py IterativeGradientAscentScene
#
# Slide: "Iterative Gradient Ascent in MetaEase"
# Companion to gp_surrogate.py. Three iterations of path-aware gradient
# ascent: at each step compute Opt + Heuristic gradients, combine
# into Gap, advance.
#
# ============================================================================
# Style summary -- extracted from gp_surrogate.py and reused below
# ============================================================================
# Colors:
#   PURPLE_ACCENT = "#5A2D82"   -- title, point I, kernel/grad equations
#   SAMPLE_GRAY   = "#808080"   -- sample dots (the file calls this
#                                  SAMPLE_RED, but the value is gray;
#                                  preserved here)
#   BLACK_ACCENT  = "#444444"   -- subtle dark gray
#   BLACK         -- axes, axis labels, "Input Space" caption
#   Surface colormap: [BLUE, TEAL, GREEN, YELLOW, ORANGE, RED] axis=2
# Fonts:
#   TEXT_FONT = "Arial" for Text(); MathTex defaults
#   Axis labels (MathTex) font_size 32 -> 28 here (smaller plane on right)
#   Title font_size 30; equation strip font_size 26
# Box: Polygon stroke=PURPLE_ACCENT width=2, fill PURPLE_ACCENT opacity=0.08
# Surface:
#   gp_func(u,v) = sin(0.5*u)*cos(0.5*v) + 0.3*sin(u*v/3)   [reused verbatim]
#   z_offset = 1.0 (vs 1.2 in original; smaller plane here)
#   resolution=(36, 36), fill_opacity=0.8, stroke_width=0.4 white
# Camera: phi=58 deg, theta=-78 deg (oblique tilt) -- same as gp_surrogate
# Sample dots: Dot3D radius=0.06 (in 3D); 2D Dot radius=0.05 here
# Animation timing: FadeIn 0.8-1.2s for headers; Create 1.5-2.5s; surface
#                   FadeIn ~2s; arrow GrowArrow ~1.0-1.3s
#
# Note: the spec mentions samples in #D62728 and I in "bright red", but
# gp_surrogate.py actually uses gray samples and a PURPLE I. Per the
# instruction to match the file exactly, this script uses the file's
# values. Flip I_COLOR -> POINT_RED below if you want a red I instead.

from manim import *
import numpy as np

# Palette imported from gp_surrogate.py
PURPLE_ACCENT = "#5A2D82"
SAMPLE_GRAY = "#808080"
BLACK_ACCENT = "#444444"
TEXT_FONT = "Arial"

# New constants for this video (harmonize with the deck)
Opt_BLUE = "#1F77B4"
HEURISTIC_GREEN = "#2CA02C"
GAP_ORANGE = "#F39C12"
POINT_RED = "#D62728"

I_COLOR = PURPLE_ACCENT  # match gp_surrogate.py; swap to POINT_RED for red I


class IterativeGradientAscentScene(ThreeDScene):
    def construct(self):
        self.camera.background_color = WHITE
        # Oblique camera so the LEFT 3D surface looks 3D from t=0. The
        # RIGHT-side 2D grid is fixed_in_frame so it stays flat.
        self.set_camera_orientation(phi=58 * DEGREES, theta=-78 * DEGREES)

        # ------------------------------------------------------------------
        # Shared helpers + trajectory pre-computation
        # ------------------------------------------------------------------
        def gp_func(u, v):
            return np.sin(0.5 * u) * np.cos(0.5 * v) + 0.3 * np.sin(u * v / 3.0)

        def gp_grad(u, v):
            dfdx = (0.5 * np.cos(0.5 * u) * np.cos(0.5 * v)
                    + 0.3 * np.cos(u * v / 3) * (v / 3))
            dfdy = (-0.5 * np.sin(0.5 * u) * np.sin(0.5 * v)
                    + 0.3 * np.cos(u * v / 3) * (u / 3))
            return dfdx, dfdy

        z_offset = 1.0

        # Trajectory: blue + green chosen per iteration; orange = blue - green;
        # I_{n+1} = I_n + orange.
        I0_data = (-1.5, -2.0)
        iter_specs = []
        I_curr = I0_data
        for blue, green in [
            ((1.2, 1.5), (0.6, 0.4)),
            ((1.4, 1.3), (0.7, 0.3)),
            ((1.5, 1.2), (0.5, 0.2)),
        ]:
            orange = (blue[0] - green[0], blue[1] - green[1])
            iter_specs.append({"I": I_curr, "blue": blue,
                               "green": green, "orange": orange})
            I_curr = (I_curr[0] + orange[0], I_curr[1] + orange[1])
        I_final = I_curr  # I_3 position

        # ==================================================================
        # Step 0 (0-3s): title + equation strip + 2D grid + 3D axes
        # ==================================================================
        eq_strip = MathTex(
            r"\nabla\,\mathrm{Gap}(I)",          # [0]
            r"=",                                  # [1]
            r"\nabla\,\mathrm{Opt}(I)",     # [2]
            r"-",                                  # [3]
            r"\nabla\,\mathrm{Heuristic}(I)",     # [4]
            color=PURPLE_ACCENT,
            font_size=32,
        ).to_edge(UP, buff=0.4)
        eq_strip[0].set_color(GAP_ORANGE)
        eq_strip[2].set_color(Opt_BLUE)
        eq_strip[4].set_color(HEURISTIC_GREEN)

        self.add_fixed_in_frame_mobjects(eq_strip)
        self.remove(eq_strip)

        # RIGHT-half 2D grid (fixed_in_frame)
        plane = NumberPlane(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            x_length=5,
            y_length=5,
            background_line_style={
                "stroke_color": GRAY_B,
                "stroke_width": 0.6,
                "stroke_opacity": 0.18,
            },
            axis_config={
                "color": BLACK,
                "stroke_width": 2,
                "include_tip": True,
                "include_ticks": False,
            },
            faded_line_ratio=0,
        ).shift(RIGHT * 3.7 + DOWN * 0.5)

        x1_label = MathTex("x_1", color=BLACK, font_size=34).next_to(
            plane.y_axis.get_end(), LEFT, buff=0.15,
        )
        x2_label = MathTex("x_2", color=BLACK, font_size=34).next_to(
            plane.x_axis.get_end(), DOWN, buff=0.15,
        )
        self.add_fixed_in_frame_mobjects(plane, x1_label, x2_label)
        self.remove(plane, x1_label, x2_label)

        # LEFT-half 3D axes (live in 3D world space)
        gp_axes = ThreeDAxes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            z_range=[-2, 2, 1],
            x_length=5.8,
            y_length=5.8,
            z_length=2.8,
            axis_config={"color": BLACK, "stroke_width": 2, "include_ticks": False},
        ).shift(LEFT * 3.5 + DOWN * 0.6)

        # "Gap" label sits at the top of the GP's z-axis (the function value)
        gap_label = MathTex(r"\mathrm{Heuristic}", color=BLACK, font_size=28)
        gap_label.move_to(gp_axes.c2p(0, 0, 2.4))
        self.add_fixed_orientation_mobjects(gap_label)
        self.remove(gap_label)

        # x_1 / x_2 labels for the 3D axes
        gp_x1_label = MathTex("x_1", color=BLACK, font_size=28)
        gp_x1_label.move_to(gp_axes.c2p(3.5, 0, 0))
        gp_x2_label = MathTex("x_2", color=BLACK, font_size=28)
        gp_x2_label.move_to(gp_axes.c2p(0, 3.5, 0))
        self.add_fixed_orientation_mobjects(gp_x1_label, gp_x2_label)
        self.remove(gp_x1_label, gp_x2_label)

        self.play(FadeIn(eq_strip), run_time=1.0)
        self.play(
            Create(plane),
            FadeIn(x1_label),
            FadeIn(x2_label),
            Create(gp_axes.x_axis),
            Create(gp_axes.y_axis),
            FadeIn(gp_x1_label),
            FadeIn(gp_x2_label),
            run_time=1.6,
        )
        self.wait(0.4)

        # ==================================================================
        # Step 1 (3-8s): I_0 + Delta-box + samples on the right grid
        # ==================================================================
        spec0 = iter_specs[0]
        I_data = spec0["I"]
        I_pos = plane.c2p(*I_data)
        I_dot = Dot(I_pos, color=I_COLOR, radius=0.09)
        I_label = MathTex("I_0", color=I_COLOR, font_size=34).next_to(
            I_dot, UL, buff=0.05,
        )

        half_d = 0.7
        box_corners = [
            plane.c2p(I_data[0] - half_d, I_data[1] - half_d),
            plane.c2p(I_data[0] + half_d, I_data[1] - half_d),
            plane.c2p(I_data[0] + half_d, I_data[1] + half_d),
            plane.c2p(I_data[0] - half_d, I_data[1] + half_d),
        ]
        delta_box = Polygon(
            *box_corners, color=PURPLE_ACCENT, stroke_width=2,
        ).set_fill(PURPLE_ACCENT, opacity=0.08)

        self.add_fixed_in_frame_mobjects(I_dot, I_label, delta_box)
        self.remove(I_dot, I_label, delta_box)

        n_samples = 10
        rng = np.random.default_rng(7)
        offsets = rng.uniform(-half_d * 0.85, half_d * 0.85,
                              size=(n_samples, 2))
        sample_dots = [
            Dot(plane.c2p(I_data[0] + dx, I_data[1] + dy),
                color=SAMPLE_GRAY, radius=0.05)
            for dx, dy in offsets
        ]
        self.add_fixed_in_frame_mobjects(*sample_dots)
        self.remove(*sample_dots)

        self.play(FadeIn(I_dot), FadeIn(I_label), run_time=0.8)
        self.play(Create(delta_box), run_time=0.8)
        self.play(
            LaggedStart(
                *[FadeIn(d, scale=0.5) for d in sample_dots],
                lag_ratio=0.1,
            ),
            run_time=1.6,
        )
        self.wait(0.5)

        # ==================================================================
        # Step 2 (8-13s): GP fit on the LEFT (compressed)
        # ==================================================================
        gp_caption = MathTex(
            r"\mathrm{GP\;Fit\;to\;Local\;Samples}",
            font_size=36, color=BLACK_ACCENT,
        ).move_to([-3.7, 2.5, 0])
        self.add_fixed_in_frame_mobjects(gp_caption)
        self.remove(gp_caption)

        # The GP is a *local* fit -- restrict the surface domain to the
        # Delta-box around I_0 so it visually matches the sampling region.
        gp_u_min, gp_u_max = I_data[0] - half_d, I_data[0] + half_d
        gp_v_min, gp_v_max = I_data[1] - half_d, I_data[1] + half_d
        gp_surface = Surface(
            lambda u, v: gp_axes.c2p(u, v, gp_func(u, v) + z_offset),
            u_range=[gp_u_min, gp_u_max],
            v_range=[gp_v_min, gp_v_max],
            resolution=(24, 24),
            fill_opacity=0.85,
            stroke_width=0.4,
            stroke_color=WHITE,
        )
        gp_surface.set_fill_by_value(
            axes=gp_axes,
            colorscale=[BLUE, TEAL, GREEN, YELLOW, ORANGE, RED],
            axis=2,
        )

        self.play(FadeIn(gp_caption), run_time=0.5)
        self.play(
            FadeIn(gp_surface),
            Create(gp_axes.z_axis),
            FadeIn(gap_label),
            run_time=2.0,
        )
        self.wait(0.5)
        self.play(FadeOut(gp_caption), run_time=0.4)

        # ==================================================================
        # Step 3 (13-18s): Opt (blue) + Heuristic (green) gradients at I_0
        # ==================================================================
        def make_arrow(I_d, vec_d, color):
            start = plane.c2p(*I_d)
            end_d = (I_d[0] + vec_d[0], I_d[1] + vec_d[1])
            end = plane.c2p(*end_d)
            return Arrow(
                start=start, end=end, color=color,
                stroke_width=5, buff=0, tip_length=0.2,
                max_tip_length_to_length_ratio=0.2,
            )

        blue_arrow = make_arrow(spec0["I"], spec0["blue"], Opt_BLUE)
        green_arrow = make_arrow(spec0["I"], spec0["green"], HEURISTIC_GREEN)
        blue_label = MathTex(
            r"\nabla \mathrm{Opt}",
            color=Opt_BLUE, font_size=26,
        ).next_to(blue_arrow.get_end(), UR, buff=0.06)
        green_label = MathTex(
            r"\nabla \mathrm{Heuristic} \approx \nabla H_G",
            color=HEURISTIC_GREEN, font_size=24,
        ).next_to(green_arrow.get_end(), DR, buff=0.06)

        self.add_fixed_in_frame_mobjects(
            blue_arrow, green_arrow, blue_label, green_label,
        )
        self.remove(blue_arrow, green_arrow, blue_label, green_label)

        # Surface gradient arrow (small, green) at the corresponding (x, y)
        gx, gy = max(min(I_data[0], 3), -3), max(min(I_data[1], 3), -3)
        dfdx, dfdy = gp_grad(gx, gy)
        gmag = np.hypot(dfdx, dfdy) or 1.0
        dx_n, dy_n = dfdx / gmag, dfdy / gmag
        z_at_I = gp_func(gx, gy) + z_offset
        surf_grad_base = gp_axes.c2p(gx, gy, z_at_I + 0.05)
        surf_grad_tip = gp_axes.c2p(gx + 0.7 * dx_n, gy + 0.7 * dy_n,
                                    z_at_I + 0.45)
        surf_grad_arrow = Arrow3D(
            start=surf_grad_base, end=surf_grad_tip,
            color=HEURISTIC_GREEN,
            thickness=0.025, height=0.16, base_radius=0.06,
        )

        self.play(GrowArrow(blue_arrow), FadeIn(blue_label), run_time=1.2)
        self.play(
            GrowArrow(green_arrow),
            FadeIn(green_label),
            FadeIn(surf_grad_arrow, shift=0.1 * OUT),
            run_time=1.2,
        )
        self.wait(0.9)

        # ==================================================================
        # Step 4 (18-22s): combine into Gap arrow (orange)
        # ==================================================================
        orange_arrow = make_arrow(spec0["I"], spec0["orange"], GAP_ORANGE)
        orange_label = MathTex(
            r"\nabla \mathrm{Gap}",
            color=GAP_ORANGE, font_size=28,
        ).next_to(orange_arrow.get_end(), UR, buff=0.08)
        self.add_fixed_in_frame_mobjects(orange_arrow, orange_label)
        self.remove(orange_arrow, orange_label)

        # Clean up the GP visuals on the LEFT (surface + 3D axes) -- once the
        # heuristic gradient is in hand, the surrogate has done its job.
        self.play(
            FadeOut(green_arrow), FadeOut(green_label),
            FadeOut(blue_arrow), FadeOut(blue_label),
            FadeOut(surf_grad_arrow),
            FadeOut(gp_surface),
            FadeOut(gp_axes.x_axis),
            FadeOut(gp_axes.y_axis),
            FadeOut(gp_axes.z_axis),
            FadeOut(gp_x1_label),
            FadeOut(gp_x2_label),
            FadeOut(gap_label),
            run_time=0.8,
        )
        self.play(GrowArrow(orange_arrow), FadeIn(orange_label), run_time=1.0)
        # Pulse the Gap term in the equation strip
        self.play(
            eq_strip[0].animate.scale(1.15),
            rate_func=there_and_back,
            run_time=0.8,
        )
        self.wait(0.4)

        # ==================================================================
        # Step 5 (22-27s): take the step -- I_0 -> I_1
        # ==================================================================
        spec1 = iter_specs[1]
        new_I_pos = plane.c2p(*spec1["I"])
        delta_screen = new_I_pos - plane.c2p(*spec0["I"])

        offsets1 = rng.uniform(-half_d * 0.85, half_d * 0.85,
                               size=(n_samples, 2))
        new_sample_dots = [
            Dot(plane.c2p(spec1["I"][0] + dx, spec1["I"][1] + dy),
                color=SAMPLE_GRAY, radius=0.05)
            for dx, dy in offsets1
        ]
        I_label_1 = MathTex("I_1", color=I_COLOR, font_size=34).move_to(
            new_I_pos + UL * 0.22,
        )
        self.add_fixed_in_frame_mobjects(*new_sample_dots, I_label_1)
        self.remove(*new_sample_dots, I_label_1)

        self.play(
            I_dot.animate.move_to(new_I_pos),
            delta_box.animate.shift(delta_screen),
            FadeOut(I_label),
            FadeOut(orange_arrow), FadeOut(orange_label),
            FadeOut(VGroup(*sample_dots)),
            run_time=1.5,
        )
        self.play(FadeIn(I_label_1), run_time=0.4)
        self.play(
            LaggedStart(
                *[FadeIn(d, scale=0.5) for d in new_sample_dots],
                lag_ratio=0.07,
            ),
            run_time=1.2,
        )
        self.wait(0.4)

        # ==================================================================
        # Step 6 (27-35s): second iteration at I_1
        # ==================================================================
        # GP surface was cleared in step 4 -- iterations 2 and 3 are pure
        # input-space animations.

        blue_arrow1 = make_arrow(spec1["I"], spec1["blue"], Opt_BLUE)
        green_arrow1 = make_arrow(spec1["I"], spec1["green"], HEURISTIC_GREEN)
        orange_arrow1 = make_arrow(spec1["I"], spec1["orange"], GAP_ORANGE)
        self.add_fixed_in_frame_mobjects(blue_arrow1, green_arrow1, orange_arrow1)
        self.remove(blue_arrow1, green_arrow1, orange_arrow1)

        self.play(
            GrowArrow(blue_arrow1),
            GrowArrow(green_arrow1),
            run_time=1.0,
        )
        self.wait(0.4)
        self.play(
            FadeOut(blue_arrow1), FadeOut(green_arrow1),
            GrowArrow(orange_arrow1),
            run_time=0.8,
        )
        self.wait(0.4)

        # Step I_1 -> I_2
        spec2 = iter_specs[2]
        new_I_pos2 = plane.c2p(*spec2["I"])
        delta_screen2 = new_I_pos2 - plane.c2p(*spec1["I"])

        offsets2 = rng.uniform(-half_d * 0.85, half_d * 0.85,
                               size=(n_samples, 2))
        new_sample_dots2 = [
            Dot(plane.c2p(spec2["I"][0] + dx, spec2["I"][1] + dy),
                color=SAMPLE_GRAY, radius=0.05)
            for dx, dy in offsets2
        ]
        I_label_2 = MathTex("I_2", color=I_COLOR, font_size=34).move_to(
            new_I_pos2 + UL * 0.22,
        )
        self.add_fixed_in_frame_mobjects(*new_sample_dots2, I_label_2)
        self.remove(*new_sample_dots2, I_label_2)

        self.play(
            I_dot.animate.move_to(new_I_pos2),
            delta_box.animate.shift(delta_screen2),
            FadeOut(I_label_1),
            FadeOut(orange_arrow1),
            FadeOut(VGroup(*new_sample_dots)),
            run_time=1.3,
        )
        self.play(FadeIn(I_label_2), run_time=0.4)
        self.play(
            LaggedStart(
                *[FadeIn(d, scale=0.5) for d in new_sample_dots2],
                lag_ratio=0.05,
            ),
            run_time=0.9,
        )
        self.wait(0.3)

        # ==================================================================
        # Step 7 (35-40s): third iteration at I_2 (compressed)
        # ==================================================================
        blue_arrow2 = make_arrow(spec2["I"], spec2["blue"], Opt_BLUE)
        green_arrow2 = make_arrow(spec2["I"], spec2["green"], HEURISTIC_GREEN)
        orange_arrow2 = make_arrow(spec2["I"], spec2["orange"], GAP_ORANGE)
        self.add_fixed_in_frame_mobjects(blue_arrow2, green_arrow2, orange_arrow2)
        self.remove(blue_arrow2, green_arrow2, orange_arrow2)

        # All three arrows flash together
        self.play(
            GrowArrow(blue_arrow2),
            GrowArrow(green_arrow2),
            GrowArrow(orange_arrow2),
            run_time=0.9,
        )
        self.wait(0.5)

        # Step I_2 -> I_3
        new_I_pos3 = plane.c2p(*I_final)
        delta_screen3 = new_I_pos3 - plane.c2p(*spec2["I"])
        I_label_3 = MathTex("I_3", color=I_COLOR, font_size=34).move_to(
            new_I_pos3 + UL * 0.22,
        )
        self.add_fixed_in_frame_mobjects(I_label_3)
        self.remove(I_label_3)

        self.play(
            I_dot.animate.move_to(new_I_pos3),
            delta_box.animate.shift(delta_screen3),
            FadeOut(I_label_2),
            FadeOut(blue_arrow2),
            FadeOut(green_arrow2),
            FadeOut(orange_arrow2),
            FadeOut(VGroup(*new_sample_dots2)),
            run_time=1.2,
        )
        self.play(FadeIn(I_label_3), run_time=0.4)

        # Polish: dotted trajectory trail through I_0..I_3
        trail_pts = [
            plane.c2p(*spec0["I"]),
            plane.c2p(*spec1["I"]),
            plane.c2p(*spec2["I"]),
            plane.c2p(*I_final),
        ]
        trail = VGroup(*[
            DashedLine(
                trail_pts[i], trail_pts[i + 1],
                color=GRAY, stroke_width=1.5, dash_length=0.08,
            ).set_opacity(0.5)
            for i in range(len(trail_pts) - 1)
        ])
        self.add_fixed_in_frame_mobjects(trail)
        self.remove(trail)
        self.play(Create(trail), run_time=0.9)
        self.wait(0.4)

        # ==================================================================
        # Step 8: hold final state, then fade to white
        # ==================================================================
        self.wait(2.5)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.2)
