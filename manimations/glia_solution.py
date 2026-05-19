# Render: uv run manim -pqh glia_solution.py GliaSolution
#
# THE SOLUTION half of the Glia Section 3.3 story: Head-Room Admission
# (HRA) + shortest-prefill-first.
#
# Opens mid-action: 4 GPUs already running real workloads, 3 requests
# already sitting in the Global Queue. From there the scene shows:
#   1. Sort: the queue reorders shortest-prefill-first.
#   2. Dispatch the small chip -- its target GPU has headroom -> admitted.
#   3. Try to dispatch the medium chip -- its target GPU is too full ->
#      HRA HOLDS the chip in the queue. A "HOLD" callout pops up.
#   4. Two more requests arrive in the queue behind the held one.
#   5. The target GPU's existing chip finishes -> memory drops below the
#      headroom line -> the held chip is finally admitted.
#   6. Remaining queued chips dispatch as GPUs free up.

from manim import *
import numpy as np

config.pixel_height = 1080
config.pixel_width = 1920
config.frame_rate = 30

# ---------------------------------------------------------------------- palette
BG_COLOR = "#FFFFFF"
REQUEST_COLORS = [
    ("#B4C7E7", "#5E7AA0"),  # 0 blue
    ("#F5D5A8", "#B58447"),  # 1 orange
    ("#CCD5C5", "#75876C"),  # 2 green
    ("#F0B8B8", "#A36363"),  # 3 rose
    ("#D6C7E8", "#5A2D82"),  # 4 purple
    ("#FFE082", "#B8941F"),  # 5 gold
]
ROUTER_STROKE = "#5B2C8E"
ROUTER_FILL = "#F5F0F8"
GPU_STROKE = "#444444"
GPU_QUEUE_FILL = "#F2F2F4"
LINE_COLOR = "#A0A0A8"
LABEL_COLOR = "#333333"
SUBLABEL_COLOR = "#888888"
TEXT_FONT = "Arial"

MEM_BG = "#EEEEEE"
MEM_GREEN = "#4CAF50"
MEM_YELLOW = "#FFC107"
MEM_RED = "#B71C1C"
HEADROOM_LINE = "#5A2D82"
HOLD_COLOR = "#C84B00"

# ---------------------------------------------------------------------- geometry
ROUTER_CENTER = np.array([-1.7, 0.0, 0.0])
ROUTER_W, ROUTER_H = 2.6, 1.3

GLOBAL_QUEUE_CENTER_X = -4.6
GLOBAL_QUEUE_W = 2.6
GLOBAL_QUEUE_H = 0.7
GLOBAL_QUEUE_FRONT_X = -3.66
GLOBAL_QUEUE_BACK_X = -5.55
QUEUE_SLOT_XS = [GLOBAL_QUEUE_FRONT_X,
                 (GLOBAL_QUEUE_FRONT_X + GLOBAL_QUEUE_BACK_X) / 2,
                 GLOBAL_QUEUE_BACK_X]

GPU_YS = [2.3, 0.8, -0.8, -2.3]
GPU_BAR_W = 4.4
GPU_BAR_H = 0.9
GPU_CENTER_X = 4.6
QUEUE_FRAC = 0.4

GPU_LEFT_EDGE = GPU_CENTER_X - GPU_BAR_W / 2
QUEUE_W = GPU_BAR_W * QUEUE_FRAC
PROC_W = GPU_BAR_W - QUEUE_W
PROC_LEFT_X = GPU_LEFT_EDGE + QUEUE_W
QUEUE_CENTER_X = GPU_LEFT_EDGE + QUEUE_W / 2
PROC_CENTER_X = PROC_LEFT_X + PROC_W / 2

MEM_BAR_W = PROC_W - 0.1
MEM_BAR_H = 0.10
MEM_BAR_DY = -(GPU_BAR_H / 2 + 0.18)

REQ_HEIGHT = 0.40
REQ_OPACITY = 0.95
HATCH_OPACITY = 0.55
HRA_THRESHOLD = 0.72

DECODE_RATE = 1.55


# ---------------------------------------------------------------------- helpers
def mem_color_for(level):
    if level < 0.5:
        return MEM_GREEN
    if level < 0.82:
        return MEM_YELLOW
    return MEM_RED


def make_mem_fill(level, bar_left_x, bar_y, override_color=None):
    if level < 0.005:
        return VGroup()
    width = MEM_BAR_W * min(level, 1.0)
    color = override_color if override_color else mem_color_for(level)
    fill = Rectangle(
        width=width, height=MEM_BAR_H * 0.78,
        stroke_width=0,
        fill_color=color, fill_opacity=0.92,
    ).move_to([bar_left_x + width / 2, bar_y, 0])
    return fill


def make_request(req_width, fill_c, stroke_c, opacity=REQ_OPACITY):
    return RoundedRectangle(
        width=req_width, height=REQ_HEIGHT, corner_radius=0.08,
        stroke_color=stroke_c, stroke_width=1.8,
        fill_color=fill_c, fill_opacity=opacity,
    )


def make_open_gpu_bar(width, height, center, stroke_color, stroke_width=1.6):
    cx, cy = center[0], center[1]
    left = cx - width / 2
    right = cx + width / 2
    top = cy + height / 2
    bottom = cy - height / 2
    return VGroup(
        Line([left, top, 0], [right, top, 0],
             color=stroke_color, stroke_width=stroke_width),
        Line([left, bottom, 0], [right, bottom, 0],
             color=stroke_color, stroke_width=stroke_width),
        Line([left, top, 0], [left, bottom, 0],
             color=stroke_color, stroke_width=stroke_width),
    )


def decode_width(proc_time, min_req_width=0.0):
    return max(min_req_width + 0.05, min(2.85, proc_time * DECODE_RATE))


def slide_to(mob, dest_xyz, run_time, rate_func=smooth, opacity=REQ_OPACITY):
    target = mob.copy()
    target.move_to(dest_xyz)
    target.set_opacity(opacity)
    return Transform(mob, target, run_time=run_time, rate_func=rate_func)


def grow_into_proc(mob, gy, target_width, run_time):
    target = mob.copy()
    target.stretch_to_fit_width(target_width)
    target.move_to([PROC_LEFT_X + target_width / 2, gy, 0])
    target.set_opacity(REQ_OPACITY)
    return Transform(mob, target, run_time=run_time, rate_func=linear)


def tracker_set(tracker, value, run_time, rate_func=smooth):
    target = tracker.copy()
    target.set_value(value)
    return Transform(tracker, target, run_time=run_time, rate_func=rate_func)


def two_phase_mem_rise(tracker, final_level, total_time, prefill_frac=0.6):
    prefill_level = final_level * prefill_frac
    return Succession(
        tracker_set(tracker, prefill_level, total_time * 0.3,
                    rate_func=smooth),
        tracker_set(tracker, final_level, total_time * 0.7,
                    rate_func=linear),
    )


def router_pulse(router, run_time=0.4, width=3.5):
    target = router.copy()
    target.set_stroke(width=width)
    return Transform(router, target,
                     rate_func=there_and_back, run_time=run_time)


def make_hatch_lines(width, height, color, spacing=0.10):
    lines = VGroup()
    c_min = -height / 2 - width / 2
    c_max = height / 2 + width / 2
    c = c_min + spacing
    while c < c_max:
        x_start = max(-width / 2, -height / 2 - c)
        x_end = min(width / 2, height / 2 - c)
        if x_end > x_start + 1e-3:
            p1 = np.array([x_start, x_start + c, 0])
            p2 = np.array([x_end, x_end + c, 0])
            lines.add(Line(p1, p2,
                           color=color,
                           stroke_width=1.2,
                           stroke_opacity=HATCH_OPACITY))
        c += spacing
    return lines


def attach_hatch(scene, bar, stroke_c, initial_op=0.0):
    tracker = ValueTracker(initial_op)

    def build(b=bar, t=tracker, col=stroke_c):
        op = t.get_value()
        if op < 5e-3:
            return VGroup()
        w = b.get_width()
        h = b.get_height()
        if w < 1e-2 or h < 1e-2:
            return VGroup()
        lines = make_hatch_lines(w * 0.88, h * 0.6,
                                 col, spacing=0.10)
        lines.move_to([b.get_x(), b.get_y(), 0])
        lines.set_opacity(op)
        return lines

    hatch = always_redraw(build)
    hatch.set_z_index(10)
    scene.add(hatch)
    return hatch, tracker


# ---------------------------------------------------------------------- scene
class GliaSolution(Scene):
    def construct(self):
        self.camera.background_color = BG_COLOR
        self.build_layout()
        self.preload_workload()
        self.play_solution()

    # ----- static layout ----------------------------------------------------
    def build_layout(self):
        self.global_queue_box = RoundedRectangle(
            width=GLOBAL_QUEUE_W, height=GLOBAL_QUEUE_H, corner_radius=0.10,
            stroke_color=GPU_STROKE, stroke_width=1.4,
            fill_color=GPU_QUEUE_FILL, fill_opacity=0.6,
        ).move_to([GLOBAL_QUEUE_CENTER_X, 0, 0])
        self.global_queue_label = MathTex(
            r"\text{\textbf{Global Queue}}", color=BLACK, font_size=18,
        ).next_to(self.global_queue_box, UP, buff=0.05)

        self.queue_to_router_line = Line(
            start=[self.global_queue_box.get_right()[0], 0, 0],
            end=[ROUTER_CENTER[0] - ROUTER_W / 2, 0, 0],
            stroke_color=LINE_COLOR, stroke_width=1.2,
        )

        self.router = RoundedRectangle(
            width=ROUTER_W, height=ROUTER_H, corner_radius=0.18,
            stroke_color=ROUTER_STROKE, stroke_width=2.2,
            fill_color=ROUTER_FILL, fill_opacity=0.85,
        ).move_to(ROUTER_CENTER)
        self.router_label = MathTex(
            r"\text{\textbf{Request Router}}", color=BLACK, font_size=30,
        ).move_to(self.router.get_center())

        self.gpus = []
        for i, y in enumerate(GPU_YS):
            outer = make_open_gpu_bar(
                GPU_BAR_W, GPU_BAR_H, [GPU_CENTER_X, y, 0],
                stroke_color=GPU_STROKE, stroke_width=1.6,
            )
            queue_zone = Rectangle(
                width=QUEUE_W - 0.04, height=GPU_BAR_H - 0.08,
                stroke_width=0, fill_color=GPU_QUEUE_FILL, fill_opacity=1.0,
            ).move_to([QUEUE_CENTER_X, y, 0])
            proc_zone = Rectangle(
                width=PROC_W - 0.04, height=GPU_BAR_H - 0.08,
                stroke_width=0, fill_color=BG_COLOR, fill_opacity=1.0,
            ).move_to([PROC_CENTER_X, y, 0])
            divider = DashedLine(
                start=[PROC_LEFT_X, y - 0.35, 0],
                end=[PROC_LEFT_X, y + 0.35, 0],
                color=GPU_STROKE, stroke_width=1.0, dash_length=0.06,
            )
            name_label = MathTex(
                r"\text{\textbf{GPU " + str(i) + "}}",
                color=BLACK, font_size=18,
            ).next_to(outer, LEFT, buff=0.22)

            mem_bar_y = y + MEM_BAR_DY
            mem_bar_left_x = PROC_CENTER_X - MEM_BAR_W / 2
            mem_bg = Rectangle(
                width=MEM_BAR_W, height=MEM_BAR_H,
                stroke_color=GPU_STROKE, stroke_width=0.6,
                fill_color=MEM_BG, fill_opacity=1.0,
            ).move_to([PROC_CENTER_X, mem_bar_y, 0])
            mem_level = ValueTracker(0.0)
            override_color = [None]
            mem_fill = always_redraw(
                lambda lv=mem_level, lx=mem_bar_left_x, by=mem_bar_y,
                       oc=override_color:
                    make_mem_fill(lv.get_value(), lx, by, oc[0])
            )

            headroom_x = mem_bar_left_x + MEM_BAR_W * HRA_THRESHOLD
            headroom_line = DashedLine(
                start=[headroom_x, mem_bar_y - MEM_BAR_H / 2 - 0.05, 0],
                end=[headroom_x, mem_bar_y + MEM_BAR_H / 2 + 0.05, 0],
                color=HEADROOM_LINE, stroke_width=2.0,
                dash_length=0.04,
            )

            self.gpus.append({
                'outer': outer, 'queue_zone': queue_zone, 'proc_zone': proc_zone,
                'divider': divider, 'name_label': name_label,
                'mem_bg': mem_bg, 'mem_fill': mem_fill, 'mem_level': mem_level,
                'mem_override_color': override_color,
                'mem_bar_y': mem_bar_y, 'mem_bar_left_x': mem_bar_left_x,
                'headroom_line': headroom_line,
                'y': y,
            })

        router_right_pt = np.array([self.router.get_right()[0], 0.0, 0.0])
        self.connection_lines = [
            Line(start=router_right_pt, end=[GPU_LEFT_EDGE, g['y'], 0],
                 stroke_color=LINE_COLOR, stroke_width=1.2)
            for g in self.gpus
        ]

        self.add(*self.connection_lines)
        for g in self.gpus:
            self.add(g['outer'], g['queue_zone'], g['proc_zone'],
                     g['divider'], g['name_label'],
                     g['mem_bg'], g['mem_fill'], g['headroom_line'])
        self.add(self.queue_to_router_line,
                 self.global_queue_box, self.global_queue_label,
                 self.router, self.router_label)

        self.mem_legend = MathTex(
            r"\text{\textbf{KV-cache memory}}", color=BLACK, font_size=14,
        ).next_to(self.gpus[0]['mem_bg'], LEFT, buff=0.15)
        self.add(self.mem_legend)

        top_y = GPU_YS[0]
        col_label_y = top_y + GPU_BAR_H / 2 + 0.18
        self.queue_col_label = MathTex(
            r"\text{\textbf{Queue}}", color=BLACK, font_size=14,
        ).move_to([QUEUE_CENTER_X, col_label_y, 0])
        self.proc_col_label = MathTex(
            r"\text{\textbf{Decoding}}", color=BLACK, font_size=14,
        ).move_to([PROC_CENTER_X, col_label_y, 0])
        self.add(self.queue_col_label, self.proc_col_label)

        self.title = MathTex(
            r"\text{\textbf{Head-Room Admission (HRA)}}",
            color=ROUTER_STROKE, font_size=30,
        ).to_corner(UL, buff=0.4)
        self.add(self.title)

        # Headroom annotation under the top GPU's threshold line.
        self.head_label = MathTex(
            r"\text{\textbf{headroom}}", color=HEADROOM_LINE, font_size=14,
        ).next_to(self.gpus[0]['headroom_line'], DOWN, buff=0.05)
        self.add(self.head_label)

    # ----- pre-populate initial state --------------------------------------
    def preload_workload(self):
        """Place 4 chips already in proc on the four GPUs and 3 chips
        already in the Global Queue, so the scene opens mid-action."""
        # Per-GPU state. GPU 0 is the busiest (will be the would-overflow
        # GPU for the medium chip's dispatch attempt); GPU 2 has plenty
        # of headroom (will receive the small chip).
        # (gpu, color_idx, current_bar_width, mem_level)
        proc_data = [
            (0, 0, 2.30, 0.62),  # blue,   GPU 0 -- HIGH mem (near threshold)
            (1, 3, 2.10, 0.55),  # rose,   GPU 1 -- mid-high
            (2, 2, 1.20, 0.22),  # green,  GPU 2 -- low (has plenty of room)
            (3, 1, 1.80, 0.45),  # orange, GPU 3 -- mid
        ]
        self.proc_chips = {}  # gpu_idx -> (chip, hatch_tracker)
        for gi, ci, cw, ml in proc_data:
            fill_c, stroke_c = REQUEST_COLORS[ci]
            chip = make_request(REQ_HEIGHT, fill_c, stroke_c)  # initial w doesn't matter
            chip.stretch_to_fit_width(cw)
            gy = self.gpus[gi]['y']
            chip.move_to([PROC_LEFT_X + cw / 2, gy, 0])
            self.add(chip)
            _, hatch_op = attach_hatch(self, chip, stroke_c,
                                       initial_op=HATCH_OPACITY)
            self.gpus[gi]['mem_level'].set_value(ml)
            self.proc_chips[gi] = (chip, hatch_op)

        # Three queue chips (arrival order: LARGE -> MEDIUM -> SMALL).
        # The medium chip is the one HRA will hold. Its target is GPU 0,
        # which is near the threshold.
        # (slot, target_gpu, width, color_idx, label) -- label is for refs
        queue_data = [
            (0, 1, 0.70, 4, 'large'),   # LARGE,  purple -> GPU 1
            (1, 0, 0.45, 5, 'medium'),  # MEDIUM, gold   -> GPU 0 (will be HELD)
            (2, 2, 0.25, 5, 'small'),   # SMALL,  gold   -> GPU 2 (has headroom)
        ]
        # Color collision check: small uses gold, but GPU 2's proc chip
        # is green -- they're on different parts of the screen so it's OK.
        # Re-pick small's color to be distinct from anything else on screen:
        # blue is taken (GPU 0 proc), rose taken (GPU 1), green taken
        # (GPU 2 proc), orange taken (GPU 3), purple taken (large queue),
        # gold taken (medium queue). All six colors are used; for SMALL
        # we reuse green but in the queue it sits left of GPU 2 so
        # visually distinct enough.
        queue_data = [
            (0, 1, 0.70, 4, 'large'),   # purple
            (1, 0, 0.45, 5, 'medium'),  # gold
            (2, 2, 0.25, 0, 'small'),   # blue (queue-side, distinct from green proc)
        ]
        self.queue_chips = {}  # label -> dict with chip, hatch_op, target, width, color
        for slot, tg, w, ci, lbl in queue_data:
            fill_c, stroke_c = REQUEST_COLORS[ci]
            chip = make_request(w, fill_c, stroke_c)
            chip.move_to([QUEUE_SLOT_XS[slot], 0, 0])
            self.add(chip)
            _, hatch_op = attach_hatch(self, chip, stroke_c)
            self.queue_chips[lbl] = {
                'chip': chip, 'hatch_op': hatch_op,
                'target_gpu': tg, 'width': w, 'stroke_c': stroke_c,
            }

    # ----- main story ------------------------------------------------------
    def play_solution(self):
        # Longer settle so the presenter can name the opening state.
        self.wait(2.0)

        # =================================================================
        # Step 1: SORT shortest-first.
        # Queue is currently large -> medium -> small (slots 0..2). The
        # shortest-first sort reverses this: small -> medium -> large.
        # =================================================================
        shortest_first_label = MathTex(
            r"\text{\textbf{Shortest first}}",
            color="#5A2D82", font_size=22,
        ).next_to(self.global_queue_label, UP, buff=0.18)

        sort_anims = [
            Transform(
                self.queue_chips['small']['chip'],
                self.queue_chips['small']['chip'].copy()
                    .move_to([QUEUE_SLOT_XS[0], 0, 0]),
                run_time=1.0, rate_func=smooth,
            ),
            Transform(
                self.queue_chips['large']['chip'],
                self.queue_chips['large']['chip'].copy()
                    .move_to([QUEUE_SLOT_XS[2], 0, 0]),
                run_time=1.0, rate_func=smooth,
            ),
            # medium stays put
        ]
        self.play(
            FadeIn(shortest_first_label, shift=UP * 0.1, run_time=0.4),
            *sort_anims,
        )
        # Long beat: this is a key moment to explain shortest-prefill-first.
        self.wait(2.0)
        self.play(FadeOut(shortest_first_label, run_time=0.4))

        # =================================================================
        # Step 2: Dispatch SMALL chip -> GPU 2 (has headroom, admitted).
        # =================================================================
        small = self.queue_chips['small']
        gpu_small = self.gpus[small['target_gpu']]
        gy_small = gpu_small['y']
        mem_small = gpu_small['mem_level']
        # The small chip's mem cost on top of current 0.22 baseline
        # would still leave room (well under HRA_THRESHOLD).
        small_proc_t = 1.6
        small_peak = min(HRA_THRESHOLD,
                         mem_small.get_value() + 0.18)

        # First, the existing GPU 2 proc chip finishes (frees the slot),
        # then the small SPF chip is admitted.
        p2_chip, p2_hatch = self.proc_chips[2]
        self.play(
            FadeOut(p2_chip, run_time=0.50),
            tracker_set(p2_hatch, 0.0, 0.50, rate_func=smooth),
            tracker_set(mem_small, 0.05, 0.55, rate_func=smooth),
            run_time=0.55,
        )
        self.play(
            router_pulse(self.router, run_time=0.55),
            Succession(
                slide_to(small['chip'], ROUTER_CENTER, 0.45),
                slide_to(small['chip'],
                         [QUEUE_CENTER_X + 0.3, gy_small, 0], 0.45),
                AnimationGroup(
                    grow_into_proc(small['chip'], gy_small,
                                   decode_width(small_proc_t, small['width']),
                                   small_proc_t),
                    two_phase_mem_rise(mem_small, small_peak, small_proc_t),
                    tracker_set(small['hatch_op'], HATCH_OPACITY,
                                small_proc_t, rate_func=linear),
                ),
            ),
        )
        # Beat after small chip lands so the audience sees the green
        # admit, then the presenter can pivot to the medium chip.
        self.wait(1.2)

        # =================================================================
        # Step 3: Try to dispatch MEDIUM chip -> GPU 0.
        # GPU 0's memory is currently 0.62. Medium's mem cost is 0.22, so
        # admitting would push to 0.84 -- past the 0.72 headroom line.
        # HRA holds the chip in the queue. A "HOLD" callout pops up.
        # =================================================================
        medium = self.queue_chips['medium']
        gpu0 = self.gpus[0]

        # Router pulses while it "checks" memory on GPU 0.
        checking_label = MathTex(
            r"\text{\textit{Checking memory on GPUs\ldots}}",
            color=BLACK, font_size=20,
        ).next_to(self.router, DOWN, buff=0.2)

        # Briefly flash GPU 0's memory bar yellow-to-red boundary to
        # signal "would overflow if admitted".
        would_overflow_target = gpu0['outer'].copy()
        would_overflow_target.set_stroke(HOLD_COLOR, width=3.0)

        self.play(
            router_pulse(self.router, run_time=0.8),
            FadeIn(checking_label, run_time=0.45),
            Transform(gpu0['outer'], would_overflow_target,
                      rate_func=there_and_back, run_time=1.0),
        )
        # Hold a moment on the "checking memory" beat before the verdict.
        self.wait(0.8)

        # HRA decides to hold. "HOLD" plus the reason are stacked as a
        # single two-line annotation sitting above the held chip:
        #   HOLD
        #   would exceed headroom on GPU 0
        # The whole group is anchored above the "Global Queue" label so
        # the reason text doesn't collide with that caption.
        hold_label = MathTex(
            r"\text{\textbf{HOLD}}",
            color=HOLD_COLOR, font_size=32,
        )
        hold_reason = MathTex(
            r"\text{\textit{would exceed headroom on GPUs}}",
            color=BLACK, font_size=28,
        )
        hold_group = VGroup(hold_label, hold_reason).arrange(DOWN, buff=0.15)
        hold_group.next_to(self.global_queue_label, UP, buff=0.3)

        self.play(
            FadeIn(hold_label, shift=UP * 0.1, run_time=0.45),
            FadeIn(hold_reason, run_time=0.45),
            FadeOut(checking_label, run_time=0.4),
        )
        # Long beat for the presenter to explain the HOLD -- the
        # centerpiece of HRA. New requests arrive shortly after but the
        # held chip sits visible.
        self.wait(4.0)

        # =================================================================
        # Step 4: Two more requests arrive in the queue behind medium.
        # =================================================================
        new_arrivals_specs = [
            # (width, color_idx, target_gpu, proc_t)
            (0.40, 3, 3, 1.1),   # rose,  -> GPU 3
            (0.55, 2, 1, 1.3),   # green, -> GPU 1 (after large goes)
        ]
        new_chips = []
        for w, ci, tg, pt in new_arrivals_specs:
            fill_c, stroke_c = REQUEST_COLORS[ci]
            chip = make_request(w, fill_c, stroke_c)
            chip.move_to([-9.5, 0, 0])
            self.add(chip)
            _, hatch_op = attach_hatch(self, chip, stroke_c)
            new_chips.append({
                'chip': chip, 'hatch_op': hatch_op,
                'target_gpu': tg, 'width': w, 'proc_t': pt,
            })

        # They arrive into the queue. Slot 2 is occupied by LARGE
        # (after sort), so new arrivals stack behind it. We don't have
        # explicit slots beyond 2 in our 3-slot model, so we shift
        # everything one slot left to make room, OR we treat the back as
        # an expanding line. For visual simplicity we line them up at
        # extra positions to the LEFT of slot 2.
        # New positions: -5.55 (existing large) -> shift to give room
        # We'll move large back to slot 2 (-5.55) -- already there. The
        # two newcomers slide to positions to the left of the box (just
        # outside) and visually "queue up" along the connector line.
        # Simpler: stack them at slots beyond 2 (further left); the
        # global queue box is wide enough since we widened it for the
        # large chip.
        # Cleanest: just have them arrive and sit at slot positions
        # extending leftward (a wider perceived queue).
        EXTRA_SLOT_XS = [
            GLOBAL_QUEUE_BACK_X - 0.85,  # just outside box on left
            GLOBAL_QUEUE_BACK_X - 1.65,
        ]

        arrival_anims = []
        for i, nc in enumerate(new_chips):
            arrival_anims.append(Succession(
                Wait(0.4 * i),
                slide_to(nc['chip'],
                         [EXTRA_SLOT_XS[i], 0, 0], 1.0),
            ))
        self.play(AnimationGroup(*arrival_anims, lag_ratio=0))
        # Brief pause so the held + queued state is visible.
        self.wait(1.0)

        # =================================================================
        # Step 5: GPU 0's existing chip finishes -> memory drops below
        # the headroom line -> HRA admits the held MEDIUM chip.
        # =================================================================
        p0_chip, p0_hatch = self.proc_chips[0]
        gy_medium = self.gpus[0]['y']
        mem0 = self.gpus[0]['mem_level']
        medium_proc_t = 1.8
        medium_peak = min(HRA_THRESHOLD, 0.05 + 0.22)

        # GPU 0 chip finishes, memory drains. Slower so the audience
        # sees the yellow bar shrink toward green and connect the dots
        # to the headroom unlocking.
        self.play(
            FadeOut(p0_chip, run_time=0.6),
            tracker_set(p0_hatch, 0.0, 0.6, rate_func=smooth),
            tracker_set(mem0, 0.05, 0.85, rate_func=smooth),
        )
        # Beat: GPU 0 is now visibly green, headroom is available.
        self.wait(0.6)

        # The HOLD label fades; the held chip is admitted.
        self.play(
            FadeOut(hold_label, run_time=0.4),
            FadeOut(hold_reason, run_time=0.4),
            router_pulse(self.router, run_time=0.55),
        )
        self.play(Succession(
            slide_to(medium['chip'], ROUTER_CENTER, 0.45),
            slide_to(medium['chip'],
                     [QUEUE_CENTER_X + 0.3, gy_medium, 0], 0.45),
            AnimationGroup(
                grow_into_proc(medium['chip'], gy_medium,
                               decode_width(medium_proc_t, medium['width']),
                               medium_proc_t),
                two_phase_mem_rise(mem0, medium_peak, medium_proc_t),
                tracker_set(medium['hatch_op'], HATCH_OPACITY,
                            medium_proc_t, rate_func=linear),
            ),
        ))
        self.wait(0.6)

        # =================================================================
        # Step 6: Remaining queued chips dispatch as their GPUs free up.
        # Large -> GPU 1, then the two newcomers to GPUs 3 and back to 1.
        # =================================================================
        large = self.queue_chips['large']
        gpu1 = self.gpus[1]
        gy1 = gpu1['y']
        mem1 = gpu1['mem_level']
        p1_chip, p1_hatch = self.proc_chips[1]
        large_proc_t = 2.0
        large_peak = min(HRA_THRESHOLD, 0.05 + 0.28)

        self.play(
            FadeOut(p1_chip, run_time=0.55),
            tracker_set(p1_hatch, 0.0, 0.55, rate_func=smooth),
            tracker_set(mem1, 0.05, 0.7, rate_func=smooth),
        )
        self.play(Succession(
            slide_to(large['chip'], ROUTER_CENTER, 0.45),
            slide_to(large['chip'],
                     [QUEUE_CENTER_X + 0.3, gy1, 0], 0.45),
            AnimationGroup(
                grow_into_proc(large['chip'], gy1,
                               decode_width(large_proc_t, large['width']),
                               large_proc_t),
                two_phase_mem_rise(mem1, large_peak, large_proc_t),
                tracker_set(large['hatch_op'], HATCH_OPACITY,
                            large_proc_t, rate_func=linear),
            ),
        ))

        # Newcomer 0 -> GPU 3 (whose existing chip finishes first).
        nc0 = new_chips[0]
        gpu3 = self.gpus[3]
        gy3 = gpu3['y']
        mem3 = gpu3['mem_level']
        p3_chip, p3_hatch = self.proc_chips[3]
        peak3 = min(HRA_THRESHOLD, 0.05 + 0.22)
        nc0_proc_t = max(1.6, nc0['proc_t'])  # bump shortest to 1.6s min

        self.play(
            FadeOut(p3_chip, run_time=0.50),
            tracker_set(p3_hatch, 0.0, 0.50, rate_func=smooth),
            tracker_set(mem3, 0.05, 0.65, rate_func=smooth),
            slide_to(nc0['chip'], [QUEUE_SLOT_XS[0], 0, 0], 0.55),
        )
        self.play(Succession(
            slide_to(nc0['chip'], ROUTER_CENTER, 0.45),
            slide_to(nc0['chip'], [QUEUE_CENTER_X + 0.3, gy3, 0], 0.45),
            AnimationGroup(
                grow_into_proc(nc0['chip'], gy3,
                               decode_width(nc0_proc_t, nc0['width']),
                               nc0_proc_t),
                two_phase_mem_rise(mem3, peak3, nc0_proc_t),
                tracker_set(nc0['hatch_op'], HATCH_OPACITY,
                            nc0_proc_t, rate_func=linear),
            ),
        ))

        # =================================================================
        # Closing beat: longer hold on a clean state so the talk can wrap.
        # =================================================================
        self.wait(2.5)
