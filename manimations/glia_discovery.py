# Render: uv run manim -pqh glia_discovery.py GliaDiscovery
#
# Glia Section 3.3 visualization: KV-cache memory exhaustion -> evictions
# vs. Head-Room Admission (HRA).
#
# Reuses the layout from llm_router.py (router box, 4 GPU bars with
# Queue/Processing zones, connection lines) and adds one new element:
# a thin memory-pressure bar under each GPU that fills green -> yellow
# -> red as KV-cache memory fills up.
#
# Act 1 (~15s): naive router. Memory bars fill, hit 100%, requests get
#               evicted (slide back, lose progress).
# Transition (~2s): "Glia's Discovery: Head-Room Admission".
# Act 2 (~13s): HRA router. Threshold line on each memory bar; router
#               holds requests in the pre-queue when the target GPU is
#               above headroom. No evictions.
#
# Schedules are hardcoded -- this is a storytelling scene, not a generic
# scheduler. Each beat (arrival, eviction, hold, drain) is scripted.

from manim import *
import numpy as np

config.pixel_height = 1080
config.pixel_width = 1920
config.frame_rate = 30

# ---------------------------------------------------------------------- palette
BG_COLOR = "#FFFFFF"
REQUEST_COLORS = [
    ("#B4C7E7", "#5E7AA0"),  # blue
    ("#F5D5A8", "#B58447"),  # orange
    ("#CCD5C5", "#75876C"),  # green
    ("#F0B8B8", "#A36363"),  # rose
    ("#D6C7E8", "#5A2D82"),  # purple
    ("#FFE082", "#B8941F"),  # gold
]
ROUTER_STROKE = "#5A2D82"
ROUTER_FILL = "#F5F0F8"
GPU_STROKE = "#444444"
GPU_QUEUE_FILL = "#F2F2F4"
GPU_PROC_FILL = "#E6E6EE"
LINE_COLOR = "#A0A0A8"
LABEL_COLOR = "#333333"
SUBLABEL_COLOR = "#888888"
TEXT_FONT = "Arial"

MEM_BG = "#EEEEEE"
MEM_GREEN = "#4CAF50"
MEM_YELLOW = "#FFC107"
MEM_RED = "#B71C1C"
EVICTED_GRAY = "#9E9E9E"
HEADROOM_LINE = "#5A2D82"

# ---------------------------------------------------------------------- geometry
ROUTER_CENTER = np.array([-1.7, 0.0, 0.0])
ROUTER_W, ROUTER_H = 2.6, 1.3

# Global queue: every request lands here first, then advances to the
# router. Evicted (restarted) requests slide back into the BACK slot.
GLOBAL_QUEUE_CENTER_X = -4.6
GLOBAL_QUEUE_W = 2.6
GLOBAL_QUEUE_H = 0.7
GLOBAL_QUEUE_FRONT_X = -3.55   # closest to the router
GLOBAL_QUEUE_BACK_X = -5.55    # back of the line; evicted chips land here

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


def slide_to(mob, dest_xyz, run_time, rate_func=smooth, opacity=REQ_OPACITY):
    target = mob.copy()
    target.move_to(dest_xyz)
    target.set_opacity(opacity)
    return Transform(mob, target, run_time=run_time, rate_func=rate_func)


def proc_slot_y_offset(slot, n_slots):
    """Per-chip y offset inside a GPU's proc zone, so multiple
    concurrent chips on the same GPU stack vertically instead of
    overlapping. slot 0 = top lane."""
    if n_slots <= 1:
        return 0.0, REQ_HEIGHT
    slot_height = 0.30  # thinner so two fit
    slot_pitch = slot_height + 0.04
    top_y = (n_slots - 1) / 2 * slot_pitch
    return top_y - slot * slot_pitch, slot_height


def grow_into_proc(mob, gy, target_width, run_time, slot=0, n_slots=1):
    target = mob.copy()
    target.stretch_to_fit_width(target_width)
    y_offset, slot_height = proc_slot_y_offset(slot, n_slots)
    if n_slots > 1:
        target.stretch_to_fit_height(slot_height)
    target.move_to([PROC_LEFT_X + target_width / 2, gy + y_offset, 0])
    target.set_opacity(REQ_OPACITY)
    return Transform(mob, target, run_time=run_time, rate_func=linear)


def shrink_and_return(mob, dest_xyz, run_time, restart_width=0.45):
    """Eviction visual: shrink the chip back to its original chip width
    and slide it to dest -- color is preserved so the audience can
    follow the *same* request as it goes back through the queue."""
    target = mob.copy()
    target.stretch_to_fit_width(restart_width)
    target.move_to(dest_xyz)
    return Transform(mob, target, run_time=run_time, rate_func=smooth)


def tracker_set(tracker, value, run_time, rate_func=smooth):
    target = tracker.copy()
    target.set_value(value)
    return Transform(tracker, target, run_time=run_time, rate_func=rate_func)


def make_hatch_lines(width, height, color, spacing=0.10):
    """45 degree diagonal lines clipped to a width x height rect."""
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


def attach_hatch(scene, bar, stroke_c):
    """Add an always_redraw hatch overlay that follows bar's current bbox.
    Returns (hatch_mobject, opacity_tracker). Animate the tracker to
    fade the hatch in/out."""
    tracker = ValueTracker(0.0)

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
class GliaDiscovery(Scene):
    def construct(self):
        self.camera.background_color = BG_COLOR

        self.build_layout()
        self.act_1()
        self.transition()
        self.act_2()

    # ----- static layout ----------------------------------------------------
    def build_layout(self):
        # Global queue box: every request sits here briefly before it
        # reaches the router. Restarted requests come back here too.
        self.global_queue_box = RoundedRectangle(
            width=GLOBAL_QUEUE_W, height=GLOBAL_QUEUE_H, corner_radius=0.10,
            stroke_color=GPU_STROKE, stroke_width=1.4,
            fill_color=GPU_QUEUE_FILL, fill_opacity=0.6,
        ).move_to([GLOBAL_QUEUE_CENTER_X, 0, 0])
        self.global_queue_label = MathTex(
            r"\text{\textbf{Global Queue}}", color=BLACK, font_size=18,
        ).next_to(self.global_queue_box, UP, buff=0.05)

        # Thin connector line from the queue's right edge to the router.
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
            outer = RoundedRectangle(
                width=GPU_BAR_W, height=GPU_BAR_H, corner_radius=0.12,
                stroke_color=GPU_STROKE, stroke_width=1.6,
                fill_color=BG_COLOR, fill_opacity=1.0,
            ).move_to([GPU_CENTER_X, y, 0])
            queue_zone = Rectangle(
                width=QUEUE_W - 0.04, height=GPU_BAR_H - 0.08,
                stroke_width=0, fill_color=GPU_QUEUE_FILL, fill_opacity=1.0,
            ).move_to([QUEUE_CENTER_X, y, 0])
            proc_zone = Rectangle(
                width=PROC_W - 0.04, height=GPU_BAR_H - 0.08,
                stroke_width=0, fill_color=GPU_PROC_FILL, fill_opacity=1.0,
            ).move_to([PROC_CENTER_X, y, 0])
            divider = DashedLine(
                start=[PROC_LEFT_X, y - 0.35, 0],
                end=[PROC_LEFT_X, y + 0.35, 0],
                color=GPU_STROKE, stroke_width=1.0, dash_length=0.06,
            )
            name_label = MathTex(
                r"\text{\textbf{GPU " + str(i) + "}}", color=BLACK, font_size=18,
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
            ).set_opacity(0)

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
            Line(
                start=router_right_pt,
                end=[GPU_LEFT_EDGE, g['y'], 0],
                stroke_color=LINE_COLOR, stroke_width=1.2,
            )
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

        # Tiny legend, placed at the LEFT of the top GPU's memory bar
        # (right side would clip off-frame).
        self.mem_legend = MathTex(
            r"\text{\textbf{KV-cache memory}}", color=BLACK, font_size=14,
        ).next_to(self.gpus[0]['mem_bg'], LEFT, buff=0.15)
        self.add(self.mem_legend)

        # Column labels above the top GPU bar -- they read for every GPU
        # below since the layout is consistent across rows.
        top_y = GPU_YS[0]
        col_label_y = top_y + GPU_BAR_H / 2 + 0.18
        self.queue_col_label = MathTex(
            r"\text{\textbf{Queue}}",
            color=SUBLABEL_COLOR, font_size=14,
        ).move_to([QUEUE_CENTER_X, col_label_y, 0])
        self.proc_col_label = MathTex(
            r"\text{\textbf{Processing}}",
            color=SUBLABEL_COLOR, font_size=14,
        ).move_to([PROC_CENTER_X, col_label_y, 0])
        self.add(self.queue_col_label, self.proc_col_label)

    # ========================================================================
    # ACT 1 -- naive router; memory fills; evictions happen
    # ========================================================================
    def act_1(self):
        title = MathTex(
            r"\text{\textbf{Naive routing --- least-loaded Queue (LLQ)}}",
            color=BLACK, font_size=30,
        ).to_corner(UL, buff=0.4)
        self.play(FadeIn(title, run_time=0.5))

        # We'll keep two parallel streams: the "filler" requests that
        # establish the layout, and one extra request per GPU that
        # triggers the eviction beat. Hardcoded for clarity.

        # ---- Phase A (~6.5s): bring GPU 0 and GPU 1 close to full ----
        fill_chips = []
        fill_anims = []
        # (arrival, gpu, width, mem_cost, proc_run_time, slot, n_slots)
        # slot/n_slots tell grow_into_proc to stack co-resident chips
        # vertically inside the same GPU's proc zone (no overlap).
        fill_specs = [
            (0.3, 0, 0.50, 0.30, 1.8, 0, 2),
            (0.9, 1, 0.55, 0.32, 1.9, 0, 2),
            (1.6, 2, 0.45, 0.28, 1.8, 0, 1),
            (2.2, 3, 0.40, 0.25, 1.8, 0, 1),
            (2.9, 0, 0.55, 0.34, 1.9, 1, 2),
            (3.6, 1, 0.50, 0.30, 1.8, 1, 2),
        ]
        # Hand-picked color indices into REQUEST_COLORS, chosen so that
        # the two chips co-resident on the same GPU contrast clearly:
        #   GPU 0: blue (0) + purple (4)
        #   GPU 1: rose (3) + gold (5)   <- previously orange+gold (too similar)
        #   GPU 2: green (2)
        #   GPU 3: orange (1)
        fill_color_indices = [0, 3, 2, 1, 4, 5]
        gpu_mem_running = [0.0] * 4
        for i, (arr, g_idx, w, mc, proc_t, slot, n_slots) in enumerate(fill_specs):
            fill_c, stroke_c = REQUEST_COLORS[fill_color_indices[i]]
            chip = make_request(w, fill_c, stroke_c)
            chip.move_to([-9.5, 0, 0])
            self.add(chip)
            # Per-chip hatch overlay (regenerated every frame at 45 deg
            # from the chip's current bbox). Opacity is 0 until proc.
            _, hatch_op = attach_hatch(self, chip, stroke_c)
            fill_chips.append((chip, g_idx, hatch_op))

            gy = self.gpus[g_idx]['y']
            mem_tracker = self.gpus[g_idx]['mem_level']
            new_level = min(0.95, gpu_mem_running[g_idx] + mc)

            ops = [
                Wait(arr),
                # Off-screen -> Global Queue (front slot)
                slide_to(chip, [GLOBAL_QUEUE_FRONT_X, 0, 0], 0.55),
                # Invariant: while the queue holds a task, GPUs must not
                # idle. With a free GPU available, the chip continues
                # straight to the router -- no dwell at the queue.
                slide_to(chip, ROUTER_CENTER, 0.30),
                Wait(0.12),
                # Router -> GPU's local queue zone
                slide_to(chip, [QUEUE_CENTER_X + 0.3, gy, 0], 0.30),
                # Proc: bar expands + memory rises + hatch fades in.
                # Co-resident chips on the same GPU use distinct slots
                # so they stack vertically inside proc instead of
                # overlapping each other.
                AnimationGroup(
                    grow_into_proc(chip, gy, PROC_W * 0.94, proc_t,
                                   slot=slot, n_slots=n_slots),
                    tracker_set(mem_tracker, new_level, proc_t,
                                rate_func=linear),
                    tracker_set(hatch_op, HATCH_OPACITY, proc_t,
                                rate_func=linear),
                ),
            ]
            gpu_mem_running[g_idx] = new_level
            fill_anims.append(Succession(*ops))

        self.play(AnimationGroup(*fill_anims, lag_ratio=0))

        # ---- Phase A.5: simulate chips 0..3 "naturally completing" ----
        # This frees up GPU 2 and GPU 3 entirely, and partially drains
        # GPU 0 / GPU 1 -- so the upcoming eviction + restart cycle has
        # clean proc zones to land in.
        natural_done = [fill_chips[i][0] for i in (0, 1, 2, 3)]
        natural_hatches = [fill_chips[i][2] for i in (0, 1, 2, 3)]
        natural_mem = [
            (0, max(0.0, gpu_mem_running[0] - fill_specs[0][3])),
            (1, max(0.0, gpu_mem_running[1] - fill_specs[1][3])),
            (2, 0.0),
            (3, 0.0),
        ]
        self.play(
            *[FadeOut(c) for c in natural_done],
            *[tracker_set(h, 0.0, 0.5, rate_func=smooth)
              for h in natural_hatches],
            *[tracker_set(self.gpus[g]['mem_level'], v, 0.5,
                          rate_func=smooth)
              for g, v in natural_mem],
            run_time=0.5,
        )
        for g, v in natural_mem:
            gpu_mem_running[g] = v

        # ---- Phase B: EVICTION on GPU 0 ----
        # Pick the youngest chip on GPU 0 (the one we dispatched most
        # recently to it -- spec index 4, color purple).
        evicted_chip_a, _, hatch_op_a = fill_chips[4]  # GPU 0
        # Restart re-dispatches to a *free* GPU (GPU 2, idle after the
        # Phase A.5 natural completions). Sending the chip back to the
        # same overloaded GPU would leave GPU 2/3 idle while a task sat
        # in the queue -- which violates "no idle GPU when queue has
        # work".
        # First eviction holds on the "Memory full" label for a beat
        # so the presenter can explain the eviction.
        self.eviction_sequence(
            gpu_idx=0,
            victim=evicted_chip_a,
            victim_hatch_op=hatch_op_a,
            mem_before=gpu_mem_running[0],
            mem_after=0.05,
            label_text="Memory full -> restart!",
            restart_gpu_idx=2,
            pause_after_label=2.5,
        )
        gpu_mem_running[0] = 0.05

        # ---- Phase C: EVICTION on GPU 1 ----
        evicted_chip_b, _, hatch_op_b = fill_chips[5]  # GPU 1
        self.eviction_sequence(
            gpu_idx=1,
            victim=evicted_chip_b,
            victim_hatch_op=hatch_op_b,
            mem_before=gpu_mem_running[1],
            mem_after=0.05,
            label_text="Memory full -> restart!",
            restart_gpu_idx=3,
        )
        gpu_mem_running[1] = 0.05

        # ---- Stat flash ----
        stat = MathTex(
            r"\text{\textbf{26\% of requests restarted --- $\sim$11s wasted per restart}}",
            color=MEM_RED, font_size=28,
        ).to_edge(DOWN, buff=0.6)
        self.play(FadeIn(stat, run_time=0.5))
        self.wait(1.2)

        # Clean up Act 1: fade out the stat/title and drain the residual
        # memory on GPUs 0 / 1 (left over from the post-restart drops).
        # We deliberately do NOT re-FadeOut the workload chips here:
        # Manim's FadeOut.clean_up_from_scene resets the mobject back to
        # its pre-FadeOut state (full opacity, at proc-zone position),
        # so re-fading already-removed chips makes them pop in for a
        # frame -- exactly the "lot of stuff in the GPUs" artifact.
        # The chips have already been faded out + removed by their own
        # eviction / natural-completion sequences.
        all_chips = [c for c, _, _ in fill_chips]
        all_hatch_ops = [h for _, _, h in fill_chips]
        self.play(
            FadeOut(stat),
            FadeOut(title),
            *[tracker_set(g['mem_level'], 0.0, 0.5, rate_func=smooth)
              for g in self.gpus],
            *[tracker_set(h, 0.0, 0.4, rate_func=smooth)
              for h in all_hatch_ops],
            run_time=0.5,
        )
        # Belt-and-braces: ensure no chip mobject lingers in scene state.
        for c in all_chips:
            self.remove(c)

    def eviction_sequence(self, gpu_idx, victim, mem_before, mem_after,
                          label_text, restart_gpu_idx=None,
                          restart_mem_cost=0.30, restart_proc_t=1.4,
                          victim_hatch_op=None,
                          pause_after_label=0.0):
        """Dramatic eviction + full restart: GPU border flashes red, the
        victim chip shrinks (color preserved) and slides back to the
        Global Queue, memory drops, then the chip re-routes through the
        router to a GPU and processes again."""
        gpu = self.gpus[gpu_idx]
        gy = gpu['y']

        # ---- eviction beat ----
        gpu['mem_override_color'][0] = MEM_RED
        flash_target_outer = gpu['outer'].copy()
        flash_target_outer.set_stroke(MEM_RED, width=3.5)

        push_to_full = tracker_set(gpu['mem_level'], 1.0, 0.25,
                                   rate_func=smooth)
        flash_border = Transform(gpu['outer'], flash_target_outer,
                                 rate_func=there_and_back, run_time=0.5)

        label = MathTex(
            r"\text{\textbf{Memory full} $\rightarrow$ \textbf{restart!}}",
            color=MEM_RED, font_size=18,
        ).next_to(gpu['outer'], UP, buff=0.08)

        self.play(
            push_to_full,
            flash_border,
            FadeIn(label, shift=RIGHT * 0.1),
            run_time=0.5,
        )

        # Optional pause for the presenter to explain what's happening.
        if pause_after_label > 0:
            self.wait(pause_after_label)

        # Shake the victim
        self.play(
            victim.animate(rate_func=there_and_back, run_time=0.20).shift(
                LEFT * 0.08
            ),
        )

        # Shrink + slide back to the BACK of the Global Queue.
        # Color is intentionally PRESERVED so the audience can track this
        # same request through its restart. The hatch fades to 0 because
        # the chip is no longer being processed. Slide is brisk -- the
        # invariant says we shouldn't dwell in the queue while a free
        # GPU is available.
        evict_dest = [GLOBAL_QUEUE_BACK_X, 0, 0]
        evict_anims = [
            shrink_and_return(victim, evict_dest, 0.45),
            tracker_set(gpu['mem_level'], mem_after, 0.45, rate_func=smooth),
        ]
        if victim_hatch_op is not None:
            evict_anims.append(
                tracker_set(victim_hatch_op, 0.0, 0.45, rate_func=smooth)
            )
        self.play(*evict_anims)
        gpu['mem_override_color'][0] = None

        # ---- restart beat ----
        # No pause between "evicted into the queue" and "attempting to
        # serve again". The label fades out in parallel with the chip's
        # first restart slide; the chip never sits idle.
        target_gpu_idx = restart_gpu_idx if restart_gpu_idx is not None else gpu_idx
        target_gpu = self.gpus[target_gpu_idx]
        target_gy = target_gpu['y']
        target_mem = target_gpu['mem_level']
        cur_mem = target_mem.get_value()
        new_peak = min(0.95, cur_mem + restart_mem_cost)

        # Restart traversal: back slot -> front slot -> router -> target
        # GPU, with the eviction label fading in parallel with the first
        # slide. No internal pauses -- chip flows continuously through
        # the queue so the target GPU is filled as soon as possible.
        proc_anims = [
            grow_into_proc(victim, target_gy, PROC_W * 0.94, restart_proc_t),
            tracker_set(target_mem, new_peak, restart_proc_t,
                        rate_func=linear),
        ]
        if victim_hatch_op is not None:
            proc_anims.append(
                tracker_set(victim_hatch_op, HATCH_OPACITY, restart_proc_t,
                            rate_func=linear)
            )
        fade_anims = [
            FadeOut(victim, run_time=0.4),
            tracker_set(target_mem, max(0.05, new_peak - 0.35),
                        0.5, rate_func=smooth),
        ]
        if victim_hatch_op is not None:
            fade_anims.append(
                tracker_set(victim_hatch_op, 0.0, 0.4, rate_func=smooth)
            )
        self.play(
            FadeOut(label, run_time=0.3),
            Succession(
                slide_to(victim, [GLOBAL_QUEUE_FRONT_X, 0, 0], 0.25),
                slide_to(victim, ROUTER_CENTER, 0.22),
                slide_to(victim, [QUEUE_CENTER_X + 0.3, target_gy, 0], 0.25),
                AnimationGroup(*proc_anims),
                AnimationGroup(*fade_anims),
            ),
        )

    # ========================================================================
    # TRANSITION
    # ========================================================================
    def transition(self):
        # Drop memory bars to zero AND fade out the static layout, so the
        # discovery title has a clean canvas to land on.
        layout_mobs = (
            list(self.connection_lines)
            + [self.router, self.router_label, self.mem_legend,
               self.queue_col_label, self.proc_col_label,
               self.global_queue_box, self.global_queue_label,
               self.queue_to_router_line]
        )
        for g in self.gpus:
            layout_mobs += [
                g['outer'], g['queue_zone'], g['proc_zone'],
                g['divider'], g['name_label'],
                g['mem_bg'], g['mem_fill'],
            ]

        zero_anims = [
            tracker_set(g['mem_level'], 0.0, 0.6, rate_func=smooth)
            for g in self.gpus
        ]
        self.play(*zero_anims, run_time=0.6)
        self.play(*[FadeOut(m) for m in layout_mobs], run_time=0.5)

        discovery = VGroup(
            Text("Glia's Discovery", font=TEXT_FONT, weight=BOLD,
                 color=ROUTER_STROKE, font_size=54),
            Text("Head-Room Admission", font=TEXT_FONT, weight=BOLD,
                 color=LABEL_COLOR, font_size=36),
        ).arrange(DOWN, buff=0.3).move_to(ORIGIN)
        self.play(FadeIn(discovery, shift=UP * 0.2), run_time=0.6)
        self.wait(1.2)
        self.play(FadeOut(discovery), run_time=0.4)

        # Fade the layout back in for Act 2.
        self.play(*[FadeIn(m) for m in layout_mobs], run_time=0.5)

    # ========================================================================
    # ACT 2 -- HRA: router checks headroom, holds when needed
    # ========================================================================
    def act_2(self):
        title = MathTex(
            r"\text{\textbf{HRA --- check headroom before admitting}}",
            color=BLACK, font_size=30,
        ).to_corner(UL, buff=0.4)
        # Reveal headroom lines on every GPU
        self.play(
            FadeIn(title, run_time=0.4),
            *[g['headroom_line'].animate.set_opacity(1.0) for g in self.gpus],
        )

        # Small annotation pointing at the headroom dashed line
        head_label = MathTex(
            r"\text{\textbf{headroom}}", color=HEADROOM_LINE, font_size=14,
        ).next_to(self.gpus[0]['headroom_line'], DOWN, buff=0.05)
        self.play(FadeIn(head_label, run_time=0.3))

        # The same kind of workload as Act 1 but with HRA-style routing.
        # When a GPU is above HRA_THRESHOLD, the chip is "held" just left
        # of the router until that GPU's memory drains. After proc, chips
        # fade and memory drops.
        chips = []
        all_anims = []
        # (arrival, gpu, width, mem_cost, proc_time, drain_amt, hold_extra)
        specs = [
            (0.3, 0, 0.50, 0.30, 1.6, 0.32, 0.0),
            (0.9, 1, 0.55, 0.32, 1.7, 0.34, 0.0),
            (1.5, 2, 0.45, 0.28, 1.5, 0.30, 0.0),
            (2.1, 3, 0.40, 0.25, 1.5, 0.27, 0.0),
            # Now memory on GPUs 0/1 is near threshold; HRA holds these:
            (2.7, 0, 0.55, 0.34, 1.6, 0.36, 1.8),  # held
            (3.3, 1, 0.50, 0.30, 1.5, 0.32, 1.8),  # held
            (5.5, 2, 0.45, 0.28, 1.4, 0.30, 0.0),
        ]
        # Same hand-picked palette as Act 1: consecutive chips on the
        # same GPU contrast clearly (GPU 1 gets rose then gold, not
        # orange then gold).
        act2_color_indices = [0, 3, 2, 1, 4, 5, 2]
        gpu_mem_running = [0.0] * 4

        for i, (arr, g_idx, w, mc, proc_t, drain, hold) in enumerate(specs):
            fill_c, stroke_c = REQUEST_COLORS[act2_color_indices[i]]
            chip = make_request(w, fill_c, stroke_c)
            chip.move_to([-9.5, 0, 0])
            self.add(chip)
            chips.append(chip)
            _, hatch_op = attach_hatch(self, chip, stroke_c)

            gy = self.gpus[g_idx]['y']
            mem_tracker = self.gpus[g_idx]['mem_level']

            peak = min(HRA_THRESHOLD, gpu_mem_running[g_idx] + mc)
            after_drain = max(0.05, peak - drain)

            ops = [Wait(arr)]
            # Off-screen -> Global Queue
            ops.append(slide_to(chip, [GLOBAL_QUEUE_FRONT_X, 0, 0], 0.6))
            if hold > 0:
                # HRA: target GPU is above headroom; hold the request in
                # the global queue instead of admitting it. (Just sit at
                # the front slot until memory drains below the line.)
                ops.append(Wait(hold))
            else:
                ops.append(Wait(0.15))
            # Global Queue -> Router
            ops.append(slide_to(chip, ROUTER_CENTER, 0.35))
            ops.append(Wait(0.15))
            # Router -> GPU's local queue
            ops.append(slide_to(chip, [QUEUE_CENTER_X + 0.3, gy, 0], 0.35))
            ops.append(Wait(0.10))
            ops.append(AnimationGroup(
                grow_into_proc(chip, gy, PROC_W * 0.94, proc_t),
                tracker_set(mem_tracker, peak, proc_t, rate_func=linear),
                tracker_set(hatch_op, HATCH_OPACITY, proc_t,
                            rate_func=linear),
            ))
            # Drain phase: chip fades, memory drops, hatch fades.
            ops.append(Wait(0.3))
            ops.append(AnimationGroup(
                FadeOut(chip, run_time=0.5),
                tracker_set(mem_tracker, after_drain, 0.6, rate_func=smooth),
                tracker_set(hatch_op, 0.0, 0.5, rate_func=smooth),
            ))
            gpu_mem_running[g_idx] = after_drain

            all_anims.append(Succession(*ops))

        self.play(AnimationGroup(*all_anims, lag_ratio=0))

        # Final stat
        stat = MathTex(
            r"\text{\textbf{0 restarts --- 42\% faster (vs. LLQ)}}",
            color=MEM_GREEN, font_size=28,
        ).to_edge(DOWN, buff=0.6)
        self.play(FadeIn(stat, run_time=0.5))
        self.wait(1.2)
        self.play(FadeOut(stat), FadeOut(title), FadeOut(head_label),
                  run_time=0.5)
