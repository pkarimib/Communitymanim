# Render: manim -pqh gp_surrogate.py GPSurrogateScene
#
# Slide: "MetaEase Uses GP Surrogate For Heuristic"
# Layout: one 3D coordinate system. The x1,x2 input space is the tilted
#         floor, the GP surrogate surface is built on top of it.

from manim import *
import numpy as np

PURPLE_ACCENT = "#5A2D82"
SAMPLE_RED = "#808080" #"#D62728"
BLACK_ACCENT = "#444444"
TEXT_FONT = "Arial"  # sans-serif; requires Calibri installed, else Pango falls back


class GPSurrogateScene(ThreeDScene):
    def construct(self):
        self.camera.background_color = WHITE
        # Start top-down so the input space reads as 2D in steps 1-3.
        self.set_camera_orientation(phi=0, theta=-90 * DEGREES)

        # --- Shared 3D axes (x1, x2 in-plane; z for the GP surface) ---
        axes = ThreeDAxes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            z_range=[-2, 2, 1],
            x_length=6,
            y_length=6,
            z_length=3,
            axis_config={"color": BLACK, "stroke_width": 2},
        )

        x1_label = MathTex("x_1", color=BLACK, font_size=32)
        x2_label = MathTex("x_2", color=BLACK, font_size=32)
        x1_label.move_to(axes.c2p(3.3, 0, 0))
        x2_label.move_to(axes.c2p(0, 3.3, 0))
        self.add_fixed_orientation_mobjects(x1_label, x2_label)
        self.remove(x1_label, x2_label)

        input_space_label = Text(
            "Input Space", font=TEXT_FONT, font_size=22, color=BLACK,
        ).to_edge(DOWN, buff=0.4)
        self.add_fixed_in_frame_mobjects(input_space_label)
        self.remove(input_space_label)

        # ==================================================================
        # Step 1 (0-3s): reveal the x1,x2 input space
        # ==================================================================
        self.play(
            Create(axes.x_axis),
            Create(axes.y_axis),
            FadeIn(x1_label),
            FadeIn(x2_label),
            FadeIn(input_space_label),
            run_time=2.5,
        )
        self.wait(0.3)

        # ==================================================================
        # Step 2 (3-6s): point I + Delta-neighborhood box (both on z=0 plane)
        # ==================================================================
        I_pt = axes.c2p(0.5, 0.5, 0)
        I_dot = Dot3D(point=I_pt, color=PURPLE_ACCENT, radius=0.08)
        I_label = MathTex("I", color=PURPLE_ACCENT, font_size=32)
        I_label.move_to(axes.c2p(0.85, 0.85, 0))
        self.add_fixed_orientation_mobjects(I_label)
        self.remove(I_label)

        half_d = 1.0
        box_pts = [
            axes.c2p(0.5 - half_d, 0.5 - half_d, 0),
            axes.c2p(0.5 + half_d, 0.5 - half_d, 0),
            axes.c2p(0.5 + half_d, 0.5 + half_d, 0),
            axes.c2p(0.5 - half_d, 0.5 + half_d, 0),
        ]
        delta_box = Polygon(
            *box_pts, color=PURPLE_ACCENT, stroke_width=2,
        ).set_fill(PURPLE_ACCENT, opacity=0.08)
        delta_label = MathTex(r"\Delta", color=PURPLE_ACCENT, font_size=30)
        delta_label.move_to(axes.c2p(0.5, 0.5 - half_d - 0.4, 0))
        self.add_fixed_orientation_mobjects(delta_label)
        self.remove(delta_label)

        self.play(FadeIn(I_dot), FadeIn(I_label), run_time=1.0)
        self.play(Create(delta_box), FadeIn(delta_label), run_time=1.3)
        self.wait(0.4)
        self.play(FadeOut(delta_label), run_time=0.4)

        # ==================================================================
        # Step 3 (6-9s): ~9 red sample points inside the box
        # ==================================================================
        rng = np.random.default_rng(7)
        n_samples = 20
        offsets = rng.uniform(-half_d * 0.9, half_d * 0.9, size=(n_samples, 2))
        sample_dots = [
            Dot3D(point=axes.c2p(0.5 + dx, 0.5 + dy, 0),
                  color=SAMPLE_RED, radius=0.06)
            for dx, dy in offsets
        ]
        sample_group = VGroup(*sample_dots)
        self.play(
            LaggedStart(
                *[FadeIn(d, scale=0.4) for d in sample_dots],
                lag_ratio=0.15,
            ),
            run_time=2.2,
        )
        self.wait(0.3)

        # ==================================================================
        # Step 4 (9-11s): tilt the input plane to reveal depth
        # ==================================================================
        def gp_func(u, v):
            return np.sin(0.5 * u) * np.cos(0.5 * v) + 0.3 * np.sin(u * v / 3.0)

        z_offset = 1.2  # lifts GP surface above the input plane

        self.move_camera(
            phi=58 * DEGREES,
            theta=-78 * DEGREES,
            run_time=2.0,
        )

        # ==================================================================
        # Step 4.5: Performance Gap axis + sample GP-value dots
        # ==================================================================
        perf_axis = Arrow(
            axes.c2p(-3.5, 0, 0),
            axes.c2p(-3.5, 0, 2.2),
            color=BLACK,
            buff=0,
            stroke_width=2,
            tip_length=0.2,
        )
        perf_label = Text(
            "Performance Gap", font=TEXT_FONT, font_size=18, color=BLACK,
        ).rotate(PI / 2)
        perf_label.move_to(axes.c2p(-4.1, 0, 1.1))
        self.add_fixed_orientation_mobjects(perf_label)
        self.remove(perf_label)

        self.play(
            Create(perf_axis),
            FadeIn(perf_label),
            run_time=1.2,
        )

        # Raised dots showing each sample's GP-predicted value
        elevated_dots = [
            Dot3D(
                point=axes.c2p(0.5 + dx, 0.5 + dy, gp_func(0.5 + dx, 0.5 + dy) + z_offset),
                color=BLACK_ACCENT,
                radius=0.02,
            )
            for dx, dy in offsets
        ]
        self.play(
            LaggedStart(
                *[FadeIn(d, scale=0.3) for d in elevated_dots],
                lag_ratio=0.12,
            ),
            run_time=2.0,
        )
        self.wait(0.5)
        self.play(
            LaggedStart(
                *[FadeOut(d) for d in elevated_dots],
                lag_ratio=0.08,
            ),
            run_time=1.2,
        )

        feed_label = Text(
            "Fit Gaussian Process",
            font=TEXT_FONT, font_size=24, color=BLACK,
        ).to_edge(UP, buff=0.4)
        self.add_fixed_in_frame_mobjects(feed_label)
        self.remove(feed_label)

        self.play(FadeIn(feed_label), run_time=1.0)
        self.wait(0.5)

        # ==================================================================
        # Step 5 (13-20s): build the GP surrogate surface on top of the grid
        # ==================================================================
        kernel_eq = MathTex(
            r"GP(x, x') = \sigma^2 \exp\!\left("
            r"-\frac{(x_1 - x'_1)^2}{2\ell_1^2}"
            r"-\frac{(x_2 - x'_2)^2}{2\ell_2^2}\right)",
            color=PURPLE_ACCENT,
            font_size=22,
        ).set_opacity(0.65).to_corner(UL, buff=0.35)
        self.add_fixed_in_frame_mobjects(kernel_eq)
        self.remove(kernel_eq)

        gp_surface = Surface(
            lambda u, v: axes.c2p(u, v, gp_func(u, v) + z_offset),
            u_range=[-1, 3],
            v_range=[-1, 3],
            resolution=(36, 36),
            fill_opacity=0.8,
            stroke_width=0.4,
            stroke_color=WHITE,
        )
        gp_surface.set_fill_by_value(
            axes=axes,
            colorscale=[BLUE, TEAL, GREEN, YELLOW, ORANGE, RED],
            axis=2,
        )

        # Caption clears; floor elements fade to a ghost so the input plane
        # remains visible beneath the raised GP surface.
        floor = VGroup(
            axes.x_axis, axes.y_axis,
            x1_label, x2_label,
            I_dot, I_label,
            delta_box, sample_group,
            input_space_label,
        )
        self.play(
            FadeOut(feed_label),
            floor.animate.set_opacity(0.15),
            FadeIn(kernel_eq),
            run_time=1.0,
        )
        self.play(FadeIn(gp_surface), run_time=2.5)
        self.wait(0.6)

        # ==================================================================
        # Step 6 (20-25s): gradient arrow at I, with I re-shown on the surface
        # ==================================================================
        gx, gy = 0.5, 0.5  # same I as on the floor
        dfdx = (
            0.5 * np.cos(0.5 * gx) * np.cos(0.5 * gy)
            + 0.3 * np.cos(gx * gy / 3.0) * (gy / 3.0)
        )
        dfdy = (
            -0.5 * np.sin(0.5 * gx) * np.sin(0.5 * gy)
            + 0.3 * np.cos(gx * gy / 3.0) * (gx / 3.0)
        )
        mag = np.hypot(dfdx, dfdy)
        dx_n, dy_n = dfdx / mag, dfdy / mag
        z0 = gp_func(gx, gy) + z_offset

        # I lifted up onto the surface, re-labeled so it's visible next to the gradient
        I_on_surface = Dot3D(axes.c2p(gx, gy, z0), color=PURPLE_ACCENT, radius=0.09)
        I_surface_label = MathTex("I", color=PURPLE_ACCENT, font_size=30)
        I_surface_label.move_to(axes.c2p(gx - 0.55, gy - 0.7, z0 + 0.15))
        self.add_fixed_orientation_mobjects(I_surface_label)
        self.remove(I_surface_label)
        # A dashed vertical segment tying I on the floor to I on the surface
        I_connector = DashedLine(
            I_pt, axes.c2p(gx, gy, z0),
            color=PURPLE_ACCENT, stroke_width=2, dash_length=0.12,
        ).set_opacity(0.55)

        grad_base = axes.c2p(gx, gy, z0 + 0.08)
        grad_tip = axes.c2p(gx + 0.9 * dx_n, gy + 0.9 * dy_n, z0 + 0.75)
        grad_arrow = Arrow3D(
            start=grad_base,
            end=grad_tip,
            color=PURPLE_ACCENT,
            thickness=0.03,
            height=0.2,
            base_radius=0.07,
        )

        # Combined equation: first piece appears in step 6 with the gradient;
        # the approximation piece appears inline (to its right) in step 7.
        grad_eq = MathTex(
            r"\nabla H_G(I)",
            r"\approx \nabla \mathrm{Heuristic}(I)",
            color=PURPLE_ACCENT,
            font_size=40,
        ).to_corner(UR, buff=0.4).shift(LEFT * 1.0 + DOWN * 0.5)
        grad_eq[0].set_opacity(0)
        grad_eq[1].set_opacity(0)
        self.add_fixed_in_frame_mobjects(grad_eq)

        self.play(
            FadeIn(I_on_surface),
            FadeIn(I_surface_label),
            Create(I_connector),
            run_time=0.9,
        )
        self.play(FadeIn(grad_arrow, shift=0.15 * OUT), run_time=1.3)
        self.play(grad_eq[0].animate.set_opacity(1), run_time=0.6)
        self.wait(1.2)

        # ==================================================================
        # Step 7 (25-30s): reveal "approx Heuristic(I)" inline after H_G(I)
        # ==================================================================
        self.play(grad_eq[1].animate.set_opacity(1), run_time=1.0)
        self.wait(2.5)

        # Clean fade-out. Floor elements were already faded in step 5; no
        # surface_label or z-axis in this version.
        everything = VGroup(
            kernel_eq, gp_surface,
            I_on_surface, I_surface_label, I_connector,
            grad_arrow, grad_eq,
            floor, perf_axis, perf_label,
        )
        self.play(FadeOut(everything), run_time=1.0)
