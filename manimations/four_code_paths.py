# Render: manim -pqh four_code_paths.py FourCodePathsScene
#
# Slide: "Why MetaEase Uses KLEE Instead of Random Seeds"
#
# ============================================================================
# Style summary -- extracted from gp_surrogate.py, path_aware.py,
# iterative_gradient.py
# ============================================================================
# Colors:
#   PURPLE_ACCENT = "#5A2D82"    -- title, point I, kernel/grad equations
#                                   (gp_surrogate.py / path_aware.py / iterative)
#   BLACK_ACCENT  = "#444444"    -- subtle dark gray (gp_surrogate.py)
#   SAMPLE_GRAY   = "#808080"    -- sample dots (gp_surrogate.py SAMPLE_RED)
#   POINT_RED     = "#D62728"    -- "invalid" indicator (path_aware.py)
#   SOFT_BLUE     = "#B4C7E7"    -- focus class pastel (path_aware.py)
#   SOFT_GREEN    = "#C5E0B4"    -- (path_aware.py; reused as inspiration)
#   SOFT_YELLOW   = "#FFE699"    -- (path_aware.py)
#   GAP_ORANGE    = "#F39C12"    -- (path_aware.py / iterative)
# Background: WHITE (all three files)
# TEXT_FONT  : "Arial"          (all three)
# Camera     : phi=58 deg, theta=-78 deg (gp_surrogate / iterative); spec
#              for this video uses phi=65/theta=-45 for 3D, 70/-90 for the
#              cliff view, 20/-90 for top-down inspection
# Surface    : resolution=(36,36), fill_opacity=0.8, stroke_width=0.4 white
#              (gp_surrogate). This file uses resolution=(20,20) per spec
#              since we render four small patches.
# Box stroke = PURPLE_ACCENT, stroke_width=2, fill PURPLE_ACCENT @ 0.08
# Axes       : BLACK, stroke_width=2, include_ticks=False (iterative_gradient)
# MathTex    : 22-40 range across the three files (axis labels 28-34, eq 32-40)

from manim import *
import numpy as np

# --- Style constants imported from existing files ---
PURPLE_ACCENT = "#5A2D82"
BLACK_ACCENT = "#444444"
TEXT_FONT = "Arial"

# --- Region pastels (per spec; BLUE matches path_aware.py SOFT_BLUE) ---
BLUE_REGION = "#B4C7E7"
GREEN_REGION = "#CCD5C5"
ORANGE_REGION = "#F5D5A8"
RED_REGION = "#F0B8B8"

# Side-wall colors -- noticeably DARKER than the top-face colors so the
# vertical cliff faces clearly read as 3D depth rather than blending into
# the slanted tops.
BLUE_TONAL = "#5E7AA0"
GREEN_TONAL = "#75876C"
ORANGE_TONAL = "#B58447"
RED_TONAL = "#A36363"

SEED_RANDOM_COLOR = "#444444"

# --- Tunable durations (named so timing is easy to tweak) ---
SCENE_0_DURATION = 8
SCENE_1_REGION_REVEAL = 3
SCENE_2_SURFACE_REVEAL = 5
SCENE_3_CLIMB = 5
SCENE_5_CLIMB = 4

# --- Geometry ---
P = 2.0
DOMAIN_MAX = 2 * P  # axes go 0 -> 4 in d1, d2


class FourCodePathsScene(ThreeDScene):
    def construct(self):
        self.camera.background_color = WHITE
        # Start top-down so the 2D regions read as 2D in Scene 1
        self.set_camera_orientation(phi=0, theta=-90 * DEGREES)

        # ==============================================================
        # SCENE 0 (0-8s): code reveal
        # ==============================================================
        # Step 0.1: full code in center
        code_text = (
            "void demand_pinning(Demand d, double P) {\n"
            "    for (each demand d_i) {\n"
            "        if (d_i <= P) {\n"
            "            pin_to_shortest_path(d_i);\n"
            "        } else {\n"
            "            route_optimally(d_i);\n"
            "        }\n"
            "    }\n"
            "}"
        )
        # Manim CE 0.19 API: code_string / formatter_style / paragraph_config.
        # If you're on 0.18, swap to code=, style=, font=, font_size=,
        # insert_line_no=, background_stroke_color=, margin= as kwargs.
        code_obj = Code(
            code_string=code_text,
            language="c",
            formatter_style="default",
            add_line_numbers=False,
            background="rectangle",
            background_config={
                "color": "#FFFFFF",
                "stroke_color": BLACK_ACCENT,
                "stroke_width": 1,
                "buff": 0.25,
            },
            paragraph_config={
                "font": "Monospace",
                "font_size": 18,
            },
        )
        code_obj.move_to(ORIGIN)
        self.add_fixed_in_frame_mobjects(code_obj)
        self.remove(code_obj)

        self.play(FadeIn(code_obj), run_time=1.2)
        self.wait(0.3)

        # Step 0.2: pulse a rectangle outline around the if-line
        # (the if line sits ~third line, slightly above the code center)
        if_pulse_box = Rectangle(
            width=code_obj.width * 0.78,
            height=0.36,
            color=PURPLE_ACCENT,
            stroke_width=3,
            fill_opacity=0,
        )
        if_pulse_box.move_to(code_obj.get_center() + UP * 0.55)
        self.add_fixed_in_frame_mobjects(if_pulse_box)
        self.remove(if_pulse_box)
        self.play(Create(if_pulse_box), run_time=0.5)
        self.play(if_pulse_box.animate.scale(1.08),
                  rate_func=there_and_back, run_time=0.6)
        self.play(FadeOut(if_pulse_box), run_time=0.4)

        # Step 0.3: shrink + push code into the far top-left corner so the
        # Gap (z) axis doesn't pass behind it when the camera tilts.
        small_code_pos = np.array([-5.7, 3.05, 0])
        self.play(
            code_obj.animate.scale(0.5).move_to(small_code_pos),
            run_time=1.4,
        )

        # Step 0.4: title fades in
        title = MathTex(
            r"\text{Two demands: } d_1 \text{ and } d_2",
            color=PURPLE_ACCENT, font_size=34,
        ).to_edge(UP, buff=0.35).shift(RIGHT * 1.5)
        self.add_fixed_in_frame_mobjects(title)
        self.remove(title)
        self.play(FadeIn(title), run_time=1.0)
        self.wait(0.5)

        # ==============================================================
        # SCENE 1 (8-25s): 2D regions
        # ==============================================================
        # Step 1.1: axes appear (code stays small in corner).
        # MUST be ThreeDAxes -- 2D Axes silently drops the z component when
        # we later call axes.c2p(d_1, d_2, gap), which would render every
        # 3D surface flat at z=0.
        axes = ThreeDAxes(
            x_range=[0, DOMAIN_MAX, 0.5],
            y_range=[0, DOMAIN_MAX, 0.5],
            z_range=[0, DOMAIN_MAX, 1],
            x_length=6,
            y_length=6,
            z_length=2.4,  # short Gap axis -- fits within the camera frame
            axis_config={
                "color": BLACK,
                "stroke_width": 2,
                "include_tip": True,
                "include_ticks": False,
                "include_numbers": False,
            },
        ).shift(DOWN * 0.3 + RIGHT * 1.4)
        # Hide the z-axis (we never want to see it -- the prisms convey z).
        axes.z_axis.set_opacity(0)

        d1_label = MathTex("d_1", color=BLACK, font_size=32).next_to(
            axes.x_axis.get_end(), DR, buff=0.1,
        )
        d2_label = MathTex("d_2", color=BLACK, font_size=32).next_to(
            axes.y_axis.get_end(), UL, buff=0.1,
        )
        # Mark P on each axis
        P_x_label = MathTex("P", color=BLACK, font_size=26).next_to(
            axes.c2p(P, 0), DOWN, buff=0.12,
        )
        P_y_label = MathTex("P", color=BLACK, font_size=26).next_to(
            axes.c2p(0, P), LEFT, buff=0.12,
        )
        P_x_tick = Line(
            axes.c2p(P, -0.07, 0), axes.c2p(P, 0.07, 0),
            color=BLACK, stroke_width=2,
        )
        P_y_tick = Line(
            axes.c2p(-0.07, P, 0), axes.c2p(0.07, P, 0),
            color=BLACK, stroke_width=2,
        )

        self.play(
            FadeOut(title),
            Create(axes),
            FadeIn(d1_label), FadeIn(d2_label),
            FadeIn(P_x_label), FadeIn(P_y_label),
            FadeIn(P_x_tick), FadeIn(P_y_tick),
            run_time=2.4,
        )
        self.wait(0.3)

        # Step 1.2: threshold dashed lines (drawn in 3D at z=0)
        thresh_v = DashedLine(
            axes.c2p(P, 0, 0), axes.c2p(P, DOMAIN_MAX, 0),
            color=BLACK, stroke_width=3, dash_length=0.15,
        )
        thresh_h = DashedLine(
            axes.c2p(0, P, 0), axes.c2p(DOMAIN_MAX, P, 0),
            color=BLACK, stroke_width=3, dash_length=0.15,
        )
        self.play(Create(thresh_v), Create(thresh_h), run_time=1.4)
        self.wait(0.3)

        # Step 1.3: four colored regions, ~1.5s reveal + 0.5s hold each.
        # Each caption is a valid MathTex string -- math symbols are bare,
        # English words are wrapped in \text{...}.
        region_specs = [
            (BLUE_REGION,
             [(0, 0), (P, 0), (P, P), (0, P)],
             r"\text{Both pinned}",
             (P * 0.5, P * 0.5)),
            (GREEN_REGION,
             [(P, 0), (DOMAIN_MAX, 0), (DOMAIN_MAX, P), (P, P)],
             r"d_2\ \text{pinned}",
             (P * 1.5, P * 0.5)),
            (ORANGE_REGION,
             [(0, P), (P, P), (P, DOMAIN_MAX), (0, DOMAIN_MAX)],
             r"d_1\ \text{pinned}",
             (P * 0.5, P * 1.5)),
            (RED_REGION,
             [(P, P), (DOMAIN_MAX, P),
              (DOMAIN_MAX, DOMAIN_MAX), (P, DOMAIN_MAX)],
             r"\text{Both optimal}",
             (P * 1.5, P * 1.5)),
        ]
        regions = []
        captions = []
        for color, corners, caption_tex, caption_pos in region_specs:
            poly = Polygon(
                *[axes.c2p(*c, 0) for c in corners],
                color=color, fill_color=color,
                fill_opacity=0.6, stroke_width=0,
            )
            regions.append(poly)
            cap = MathTex(caption_tex, color=BLACK_ACCENT, font_size=24)
            cap.move_to(axes.c2p(*caption_pos, 0))
            captions.append(cap)

        for poly, cap in zip(regions, captions):
            self.play(FadeIn(poly), FadeIn(cap), run_time=1.4)
            self.wait(0.4)

        self.wait(0.6)
        # Fade just the captions, keep the colored fills
        self.play(*[FadeOut(c) for c in captions], run_time=0.9)

        # Step 1.4: top overlay caption (the title slot is empty since the
        # original title was removed; this avoids the bottom-of-frame
        # collision with the x-axis).
        s1_caption =MathTex(
            r"\mathrm{Each\;region\;=\;one\;code\;path.}",
            font_size=32, color=PURPLE_ACCENT,
        ).to_edge(UP, buff=0.3).shift(RIGHT * 1.4)
        self.add_fixed_in_frame_mobjects(s1_caption)
        self.remove(s1_caption)
        self.play(FadeIn(s1_caption), run_time=0.9)
        self.wait(1.0)
        self.play(FadeOut(s1_caption), run_time=0.7)

        # ==============================================================
        # SCENE 2 (25-42s): 3D gap surface with cliffs
        # ==============================================================
        # Step 2.1: tilt camera to 3D and reveal the Gap axis (z).
        gap_axis_label = MathTex(
            r"\mathrm{Gap}", color=BLACK, font_size=30,
        ).move_to(axes.c2p(0, 0, 4.4))
        self.add_fixed_orientation_mobjects(gap_axis_label)
        self.remove(gap_axis_label)

        self.move_camera(
            phi=65 * DEGREES, theta=-45 * DEGREES,
            added_anims=[
                axes.z_axis.animate.set_opacity(1),
                FadeIn(gap_axis_label),
            ],
            run_time=3,
        )

        # Step 2.2: 3D Gap surface, one Surface per region (so each piece is
        # smooth) + explicit vertical cliff walls between them (so the
        # non-differentiability is visible).
        #
        #     BLUE   (both pinned)        z = d_1 + d_2   (steepest -- worst)
        #     GREEN  (d_2 pinned)         z = d_2
        #     ORANGE (d_1 pinned)         z = d_1
        #     RED    (both optimized)     z = 0           (flat floor)
        #
        # Raw gap functions exactly as specified. With P=2, max blue corner
        # value is 2P=4, which is why the ThreeDAxes z_range above goes to 4.
        def gap_blue(d1, d2):
            return d1 + d2

        def gap_green(d1, d2):
            return d2

        def gap_orange(d1, d2):
            return d1

        def gap_red(d1, d2):
            return 0.0

        eps = 0.005  # tiny buffer so adjacent prisms appear to meet exactly
        # at the boundaries -- cliffs are then the height jump between
        # coincident walls at d_1=P and d_2=P.

        def make_top(gap_fn, u_lo, u_hi, v_lo, v_hi, color):
            """Slanted top face. Single fill color, no checkerboard, no
            patch seams."""
            surf = Surface(
                lambda u, v: axes.c2p(u, v, gap_fn(u, v)),
                u_range=[u_lo, u_hi],
                v_range=[v_lo, v_hi],
                resolution=(2, 2),
                fill_opacity=1.0,
                checkerboard_colors=[color, color],
                stroke_width=0,
            )
            surf.set_fill(color, opacity=1.0)
            surf.set_stroke(width=0)
            return surf

        def make_wall(p_a, p_b, h_a, h_b, color):
            """Vertical wall: bottom edge p_a->p_b on the floor, top edge
            at heights h_a, h_b. Single fill color, no patch seams."""
            x_a, y_a = p_a
            x_b, y_b = p_b
            surf = Surface(
                lambda s, t: axes.c2p(
                    x_a + t * (x_b - x_a),
                    y_a + t * (y_b - y_a),
                    s * (h_a + t * (h_b - h_a)),
                ),
                u_range=[0, 1],
                v_range=[0, 1],
                resolution=(2, 2),
                fill_opacity=1.0,
                checkerboard_colors=[color, color],
                stroke_width=0,
            )
            surf.set_fill(color, opacity=1.0)
            surf.set_stroke(width=0)
            return surf

        # --- Tops ---
        blue_top = make_top(
            gap_blue, eps, P - eps, eps, P - eps, BLUE_REGION,
        )
        green_top = make_top(
            gap_green, P + eps, DOMAIN_MAX - eps, eps, P - eps, GREEN_REGION,
        )
        orange_top = make_top(
            gap_orange, eps, P - eps, P + eps, DOMAIN_MAX - eps, ORANGE_REGION,
        )
        red_top = make_top(
            gap_red, P + eps, DOMAIN_MAX - eps, P + eps, DOMAIN_MAX - eps, RED_REGION,
        )

        # --- Walls (every edge of every prism, so the boxes look closed
        # from any camera angle and the cliffs are visible from both sides) ---
        walls = []

        # Blue prism walls (rectangle in floor: [eps, P-eps] x [eps, P-eps])
        walls.append(make_wall((eps,     eps),     (P - eps, eps),
                               gap_blue(eps, eps), gap_blue(P - eps, eps),
                               BLUE_TONAL))   # front (low d_2)
        walls.append(make_wall((P - eps, eps),     (P - eps, P - eps),
                               gap_blue(P - eps, eps), gap_blue(P - eps, P - eps),
                               BLUE_TONAL))   # right (high d_1) -- faces green
        walls.append(make_wall((P - eps, P - eps), (eps,     P - eps),
                               gap_blue(P - eps, P - eps), gap_blue(eps, P - eps),
                               BLUE_TONAL))   # back (high d_2) -- faces orange
        walls.append(make_wall((eps,     P - eps), (eps,     eps),
                               gap_blue(eps, P - eps), gap_blue(eps, eps),
                               BLUE_TONAL))   # left

        # Green prism walls
        walls.append(make_wall((P + eps, eps),     (DOMAIN_MAX - eps, eps),
                               gap_green(P + eps, eps), gap_green(DOMAIN_MAX - eps, eps),
                               GREEN_TONAL))   # front
        walls.append(make_wall((DOMAIN_MAX - eps, eps), (DOMAIN_MAX - eps, P - eps),
                               gap_green(DOMAIN_MAX - eps, eps), gap_green(DOMAIN_MAX - eps, P - eps),
                               GREEN_TONAL))   # right
        walls.append(make_wall((DOMAIN_MAX - eps, P - eps), (P + eps, P - eps),
                               gap_green(DOMAIN_MAX - eps, P - eps), gap_green(P + eps, P - eps),
                               GREEN_TONAL))   # back -- faces red
        walls.append(make_wall((P + eps, P - eps), (P + eps, eps),
                               gap_green(P + eps, P - eps), gap_green(P + eps, eps),
                               GREEN_TONAL))   # left -- faces blue

        # Orange prism walls
        walls.append(make_wall((eps, P + eps), (P - eps, P + eps),
                               gap_orange(eps, P + eps), gap_orange(P - eps, P + eps),
                               ORANGE_TONAL))   # front -- faces blue
        walls.append(make_wall((P - eps, P + eps), (P - eps, DOMAIN_MAX - eps),
                               gap_orange(P - eps, P + eps), gap_orange(P - eps, DOMAIN_MAX - eps),
                               ORANGE_TONAL))   # right -- faces red
        walls.append(make_wall((P - eps, DOMAIN_MAX - eps), (eps, DOMAIN_MAX - eps),
                               gap_orange(P - eps, DOMAIN_MAX - eps), gap_orange(eps, DOMAIN_MAX - eps),
                               ORANGE_TONAL))   # back
        walls.append(make_wall((eps, DOMAIN_MAX - eps), (eps, P + eps),
                               gap_orange(eps, DOMAIN_MAX - eps), gap_orange(eps, P + eps),
                               ORANGE_TONAL))   # left

        # Red has gap=0 everywhere, so its prism is degenerate (no walls).

        all_surfaces = [blue_top, green_top, orange_top, red_top] + walls

        # All four hyperplanes + their cliff walls appear at once, no slow
        # build-up.
        self.play(
            FadeIn(blue_top),
            FadeIn(green_top),
            FadeIn(orange_top),
            FadeIn(red_top),
            *[FadeIn(w) for w in walls],
            run_time=0.6,
        )

        # Step 2.3: cliff view -- look down d_1=P boundary
        self.move_camera(phi=70 * DEGREES, theta=-90 * DEGREES, run_time=3)
        self.wait(2)

        # Step 2.4: caption
        cliff_caption = MathTex(
            r"\mathrm{Smooth\;within\; code\;paths. \;Cliffs\;between.}",
            font_size=30, color=PURPLE_ACCENT,
        ).to_edge(DOWN, buff=0.4)
        self.add_fixed_in_frame_mobjects(cliff_caption)
        self.remove(cliff_caption)
        self.play(FadeIn(cliff_caption), run_time=0.7)
        self.wait(0.8)
        self.play(FadeOut(cliff_caption), run_time=0.5)

        # ==============================================================
        # SCENE 3 (42-55s): random seeds fail
        # ==============================================================
        # Step 3.1: camera back toward top-down; surfaces become semi-transparent
        self.move_camera(phi=20 * DEGREES, theta=-90 * DEGREES, run_time=2)
        self.play(
            *[s.animate.set_opacity(0.3) for s in all_surfaces],
            run_time=0.4,
        )

        # Step 3.2: hardcoded random seed positions. NO seeds in BLUE so
        # the random sampler misses the worst-case region (where the gap
        # = d_1 + d_2 reaches 2P at the corner (P, P)).
        random_seeds = [
            (3.2, 0.6, "green"),
            (2.6, 1.4, "green"),
            (3.6, 1.0, "green"),
            (0.5, 2.6, "orange"),
            (1.4, 3.4, "orange"),
            (2.5, 2.5, "red"),
            (3.5, 3.4, "red"),
        ]
        random_dots = []
        for d1, d2, region in random_seeds:
            dot = Dot3D(
                axes.c2p(d1, d2, 0),
                color=SEED_RANDOM_COLOR, radius=0.06,
            )
            random_dots.append((dot, d1, d2, region))

        self.play(
            LaggedStart(
                *[FadeIn(d[0], scale=0.4) for d in random_dots],
                lag_ratio=0.15,
            ),
            run_time=2.4,
        )
        self.wait(0.4)

        # Step 3.3: each seed climbs to the MAX-z point of its hyperplane.
        #   green  z = d_2          -> max at d_2 = P (top edge of green)
        #   orange z = d_1          -> max at d_1 = P (right edge of orange)
        #   red    z = 0            -> flat (no climb)
        # (No blue seeds since random sampling missed the worst-case region.)
        region_to_peak = {
            "green":  (P * 1.5, P, P),                        # z = P
            "orange": (P,       P * 1.5, P),                  # z = P
            "red":    (P * 1.5, P * 1.5, 0.0),
        }
        region_to_color = {
            "green":  GREEN_REGION,
            "orange": ORANGE_REGION,
            "red":    RED_REGION,
        }

        climb_anims = []
        random_trails = []
        for dot, d1, d2, region in random_dots:
            peak = region_to_peak[region]
            target = axes.c2p(*peak)
            climb_anims.append(dot.animate.move_to(target))
            traj = Line(
                axes.c2p(d1, d2, 0), target,
                color=region_to_color[region], stroke_width=2,
            )
            random_trails.append(traj)

        self.play(
            *climb_anims,
            *[Create(t) for t in random_trails],
            run_time=SCENE_3_CLIMB,
        )

        # Step 3.4: pulse the UNTOUCHED BLUE peak (the worst case at corner
        # (P, P) where z = 2P). Blue is the missed region.
        blue_peak_pos = axes.c2p(P, P, gap_blue(P, P))    # (P, P, 2P)
        blue_pulse = Circle(
            radius=0.4, color=BLUE_REGION, stroke_width=4,
        ).move_to(blue_peak_pos)
        self.add_fixed_orientation_mobjects(blue_pulse)
        self.remove(blue_pulse)
        self.play(FadeIn(blue_pulse, scale=0.5), run_time=0.4)
        self.play(blue_pulse.animate.scale(1.5),
                  rate_func=there_and_back, run_time=0.7)

        random_caption = MathTex(
            r"\mathrm{Random\;seeds\;miss\;the\;worst\;case.}",
            font_size=32, color=PURPLE_ACCENT,
        ).to_edge(UP, buff=0.3).shift(RIGHT * 1.4)
        self.add_fixed_in_frame_mobjects(random_caption)
        self.remove(random_caption)
        self.play(FadeIn(random_caption), FadeOut(blue_pulse), run_time=0.7)
        self.wait(0.6)

        # ==============================================================
        # SCENE 4 (55-63s): KLEE seeds appear
        # ==============================================================
        # Step 4.1: clear random seeds + trails, pulse the code, add KLEE label
        random_objs = [d[0] for d in random_dots] + random_trails
        self.play(
            *[FadeOut(o) for o in random_objs],
            FadeOut(random_caption),
            run_time=0.9,
        )

        klee_label = MathTex(
            r"\mathrm{Symbolic\;Execution}",
            font_size=24, color=PURPLE_ACCENT,
        ).next_to(code_obj, DOWN, buff=0.18)
        self.add_fixed_in_frame_mobjects(klee_label)
        self.remove(klee_label)
        self.play(
            code_obj.animate.scale(1.12),
            FadeIn(klee_label),
            run_time=0.5,
        )
        self.play(code_obj.animate.scale(1 / 1.12), run_time=0.4)

        # Step 4.2: four KLEE seeds, one per quadrant center
        klee_positions = [
            (P * 0.5, P * 0.5),
            (P * 1.5, P * 0.5),
            (P * 0.5, P * 1.5),
            (P * 1.5, P * 1.5),
        ]
        klee_dots = [
            Dot3D(axes.c2p(d1, d2, 0), color=PURPLE_ACCENT, radius=0.09)
            for d1, d2 in klee_positions
        ]
        for dot in klee_dots:
            self.play(FadeIn(dot, scale=0.5), run_time=0.25)
            self.play(dot.animate.scale(1.25),
                      rate_func=there_and_back, run_time=0.3)

        klee_caption = MathTex(
            r"\mathrm{One\;seed\;per\;code\;path.}",
            font_size=28, color=PURPLE_ACCENT,
        ).to_edge(UP, buff=0.3).shift(RIGHT * 1.4)
        self.add_fixed_in_frame_mobjects(klee_caption)
        self.remove(klee_caption)
        self.play(FadeIn(klee_caption), run_time=0.7)
        self.wait(0.8)
        self.play(FadeOut(klee_caption), run_time=0.5)

        # ==============================================================
        # SCENE 5 (63-75s): KLEE seeds succeed
        # ==============================================================
        # Step 5.1: tilt camera back to 3D, restore surface opacity
        self.move_camera(phi=65 * DEGREES, theta=-45 * DEGREES, run_time=1.5)
        self.play(
            *[s.animate.set_opacity(0.85) for s in all_surfaces],
            run_time=0.4,
        )

        # Step 5.2: KLEE seeds climb to the MAX-z point of each hyperplane.
        #   blue   z = d_1 + d_2  -> max at corner (P, P), z = 2P
        #   green  z = d_2        -> max at d_2 = P,         z = P
        #   orange z = d_1        -> max at d_1 = P,         z = P
        #   red    z = 0          -> flat
        peaks = [
            (P,       P,       gap_blue(P, P),         BLUE_REGION),   # 2P
            (P * 1.5, P,       gap_green(P * 1.5, P),  GREEN_REGION),  # P
            (P,       P * 1.5, gap_orange(P, P * 1.5), ORANGE_REGION), # P
            (P * 1.5, P * 1.5, 0.0,                    RED_REGION),    # 0
        ]
        klee_climb_anims = []
        klee_trails = []
        for dot, (px, py, pz, color) in zip(klee_dots, peaks):
            target = axes.c2p(px, py, pz)
            klee_climb_anims.append(dot.animate.move_to(target))
            traj = Line(
                axes.c2p(px, py, 0), target,
                color=color, stroke_width=2,
            )
            klee_trails.append(traj)
        self.play(
            *klee_climb_anims,
            *[Create(t) for t in klee_trails],
            run_time=SCENE_5_CLIMB,
        )

        # Step 5.3: peak labels show the GAP FUNCTION for each region,
        # so the viewer reads the non-differentiable structure directly.
        peak_values = [r"d_1 + d_2", r"d_2", r"d_1", r"0"]
        peak_labels = []
        for (px, py, pz, color), val in zip(peaks, peak_values):
            label = MathTex(val, color=BLACK, font_size=28)
            label.move_to(axes.c2p(px, py, pz + 0.3))
            self.add_fixed_orientation_mobjects(label)
            self.remove(label)
            # peak_labels.append(label)

        # The "worst case" is now BLUE (d_1 + d_2 is the steepest function),
        # so the purple ring + callout move from orange to blue.
        orange_idx = 0
        opx, opy, opz, _ = peaks[orange_idx]
        orange_ring = Circle(
            radius=0.35, color=PURPLE_ACCENT, stroke_width=4,
        ).move_to(axes.c2p(opx, opy, opz))
        self.add_fixed_orientation_mobjects(orange_ring)
        self.remove(orange_ring)

        worst_label = MathTex(
            r"\mathrm{Worst\;case\;found}",
            font_size=28, color=PURPLE_ACCENT,
        )
        worst_label.move_to(axes.c2p(opx - 0.6, opy + 0.4, opz + 0.7))
        self.add_fixed_orientation_mobjects(worst_label)
        self.remove(worst_label)

        self.play(
            *[FadeIn(lbl) for lbl in peak_labels],
            FadeIn(orange_ring),
            FadeIn(worst_label),
            run_time=1.0,
        )
        self.wait(0.8)

        # Step 5.4: tilt to top-down for final beauty shot
        self.move_camera(phi=15 * DEGREES, theta=-90 * DEGREES, run_time=1.5)

        # Step 5.5: final caption -- purple rounded rect with white text
        final_text = MathTex(
            r"\mathrm{Different\;code\;paths\;\rightarrow\;different\;behaviors.\;Search\;each\;one.}",
            font_size=28, color=WHITE,
        )
        final_box = SurroundingRectangle(
            final_text,
            color=PURPLE_ACCENT,
            fill_color=PURPLE_ACCENT,
            fill_opacity=1,
            stroke_width=0,
            buff=0.3,
            corner_radius=0.18,
        )
        final_group = VGroup(final_box, final_text).to_edge(DOWN, buff=0.4)
        self.add_fixed_in_frame_mobjects(final_group)
        self.remove(final_group)
        self.play(FadeIn(final_group), run_time=0.9)
        self.wait(2.2)

        # Fade everything to white
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.0)


# =============================================================================
# 1. STYLE EXTRACTED
# -----------------------------------------------------------------------------
# - PURPLE_ACCENT = "#5A2D82"   from gp_surrogate.py / iterative_gradient.py /
#                                    path_aware.py
# - BLACK_ACCENT  = "#444444"   from gp_surrogate.py
# - SAMPLE/SEED gray = "#808080"/"#444444"  from gp_surrogate.py
# - POINT_RED     = "#D62728"   from path_aware.py (kept here for reference;
#                                    not used directly because seeds are gray
#                                    and KLEE seeds are purple)
# - SOFT_BLUE     = "#B4C7E7"   from path_aware.py (reused as BLUE_REGION)
# - GREEN/YELLOW pastels        from path_aware.py informed the new
#                                    GREEN_REGION/ORANGE_REGION/RED_REGION hex
# - GAP_ORANGE    = "#F39C12"   from path_aware.py (not used here; kept for
#                                    palette reference)
# - TEXT_FONT     = "Arial"     from gp_surrogate.py / path_aware.py
# - Background    = WHITE        consistent across files
# - Camera angles               spec values 65/-45, 70/-90, 20/-90, 15/-90
#                                    (gp_surrogate uses 58/-78)
# - Surface params              resolution=(20,20) per spec (vs (36,36) in
#                                    gp_surrogate); fill_opacity=0.85;
#                                    stroke_width=0.3 white
# - Axes config                 BLACK, stroke_width=2, include_ticks=False
#                                    (matches iterative_gradient's right plane)
# - Box stroke=PURPLE_ACCENT, width=2, fill=PURPLE_ACCENT @ 0.08
#                                    (gp_surrogate); not used here directly
# - MathTex font_size           22-34 in this file; matches the 26-40 range
#                                    used across the previous scripts
#
# 2. TIMING TWEAKS (most likely to need adjustment when narration is added)
# -----------------------------------------------------------------------------
# - SCENE_2_SURFACE_REVEAL (4 surfaces simultaneously, currently 5s). If
#   narration explains the cliffs verbally, bump to 7s and add a `self.wait(1)`
#   after the Create to let viewers absorb.
# - The cliff camera move (Scene 2, phi=70/theta=-90) plus the 2s hold at the
#   end (line: `self.wait(2)`). The hold is the place where the cliff between
#   blue and green should "land" for the viewer; lengthen if narration is slow.
# - Scene 4 KLEE seeds appear with 0.25s + 0.3s per seed (~2.2s total). If you
#   want to land the "deliberately placed by symbolic execution" line, slow
#   each seed to 0.4s + 0.5s.
#
# 3. COORDINATE ADJUSTMENTS
# -----------------------------------------------------------------------------
# - P=2 at top of file. Changing P rescales all of input space:
#     DOMAIN_MAX = 2 * P (auto-updated)
#     bump centers and seed positions are written as multiples of P, so they
#     follow automatically. The hardcoded random seed coords in
#     `random_seeds` are absolute (e.g. (0.6, 0.5)); if you change P, scale
#     each as `(0.6/2 * P, 0.5/2 * P)` etc.
# - axes.x_length=6, y_length=6  -- if you want a wider floor, scale these
#   together. The 3D camera angles assume roughly square axes.
# - Surface peak heights: blue=0.5, green=1.2, orange=2.5, red=1.0. The 2.5
#   on orange is the dramatic "tall" peak; if it clips the top of the frame
#   at your camera angle, drop to 2.0 (and update the "2.5" peak label too).
# - small_code_pos = (-5.3, 2.6, 0). If the corner code label collides with
#   the title or the d_2 axis label at your aspect ratio, adjust this single
#   constant.
# - The `code_obj` parameter is `code=` (Manim CE 0.18). On 0.19+, switch to
#   `code_string=`.
