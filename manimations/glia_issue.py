# Render: uv run manim -pqh glia_issue.py GliaIssue
#
# THE PROBLEM half of the Glia Section 3.3 story: KV-cache memory
# exhaustion under naive routing causes evictions and restarts.
# (Companion file: glia_solution.py shows HRA + shortest-prefill-first.)

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
EVICTED_GRAY = "#9E9E9E"
HEADROOM_LINE = "#5A2D82"

# ---------------------------------------------------------------------- geometry
ROUTER_CENTER = np.array([-1.7, 0.0, 0.0])
ROUTER_W, ROUTER_H = 2.6, 1.3

GLOBAL_QUEUE_CENTER_X = -4.6
GLOBAL_QUEUE_W = 2.6
GLOBAL_QUEUE_H = 0.7
GLOBAL_QUEUE_FRONT_X = -3.66
GLOBAL_QUEUE_BACK_X = -5.55

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

# Bar width = proc_time * DECODE_RATE; longer decodes -> longer bars.
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


def proc_slot_y_offset(slot, n_slots):
    if n_slots <= 1:
        return 0.0, REQ_HEIGHT
    slot_height = 0.30
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
    target = mob.copy()
    target.stretch_to_fit_width(restart_width)
    target.move_to(dest_xyz)
    return Transform(mob, target, run_time=run_time, rate_func=smooth)


def tracker_set(tracker, value, run_time, rate_func=smooth):
    target = tracker.copy()
    target.set_value(value)
    return Transform(tracker, target, run_time=run_time, rate_func=rate_func)


def two_phase_mem_rise(tracker, final_level, total_time, prefill_frac=0.6):
    """KV-cache memory rises in two phases: a fast jump for the prefill
    allocation (predictable) and a slow creeping climb for decode growth
    (unpredictable -- this is what causes the eviction crisis)."""
    prefill_level = final_level * prefill_frac
    return Succession(
        tracker_set(tracker, prefill_level, total_time * 0.3,
                    rate_func=smooth),
        tracker_set(tracker, final_level, total_time * 0.7,
                    rate_func=linear),
    )


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


def attach_hatch(scene, bar, stroke_c):
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
class GliaIssue(Scene):
    def construct(self):
        self.camera.background_color = BG_COLOR
        self.build_layout()
        self.run_workload()

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

            self.gpus.append({
                'outer': outer, 'queue_zone': queue_zone, 'proc_zone': proc_zone,
                'divider': divider, 'name_label': name_label,
                'mem_bg': mem_bg, 'mem_fill': mem_fill, 'mem_level': mem_level,
                'mem_override_color': override_color,
                'mem_bar_y': mem_bar_y, 'mem_bar_left_x': mem_bar_left_x,
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
                     g['mem_bg'], g['mem_fill'])
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

    # ----- workload --------------------------------------------------------
    def run_workload(self):
        title = MathTex(
            r"\text{\textbf{Glia discovers the bottleneck.}}",
            color=MEM_RED, font_size=32,
        ).to_corner(UL, buff=0.4)
        self.play(FadeIn(title, run_time=0.5))

        fill_chips = []
        fill_anims = []
        # Arrivals spaced wider and proc_t bumped up so each beat has
        # more time to breathe. Roughly +35% slower than the original.
        fill_specs = [
            (0.4, 0, 0.30, 0.30, 2.6, 0, 2),   # small
            (1.2, 1, 0.68, 0.32, 2.8, 0, 2),   # large
            (2.1, 2, 0.45, 0.28, 2.6, 0, 1),   # medium
            (2.9, 3, 0.65, 0.25, 2.6, 0, 1),   # large
            (3.8, 0, 0.48, 0.34, 2.8, 1, 2),   # medium
            (4.7, 1, 0.28, 0.30, 2.6, 1, 2),   # small
        ]
        fill_color_indices = [0, 3, 2, 1, 4, 5]
        gpu_mem_running = [0.0] * 4
        for i, (arr, g_idx, w, mc, proc_t, slot, n_slots) in enumerate(fill_specs):
            fill_c, stroke_c = REQUEST_COLORS[fill_color_indices[i]]
            chip = make_request(w, fill_c, stroke_c)
            chip.move_to([-9.5, 0, 0])
            self.add(chip)
            _, hatch_op = attach_hatch(self, chip, stroke_c)
            fill_chips.append((chip, g_idx, hatch_op))

            gy = self.gpus[g_idx]['y']
            mem_tracker = self.gpus[g_idx]['mem_level']
            new_level = min(0.95, gpu_mem_running[g_idx] + mc)

            ops = [
                Wait(arr),
                slide_to(chip, [GLOBAL_QUEUE_FRONT_X, 0, 0], 0.80),
                slide_to(chip, ROUTER_CENTER, 0.45),
                Wait(0.20),
                slide_to(chip, [QUEUE_CENTER_X + 0.3, gy, 0], 0.45),
                AnimationGroup(
                    grow_into_proc(chip, gy, decode_width(proc_t, w),
                                   proc_t, slot=slot, n_slots=n_slots),
                    two_phase_mem_rise(mem_tracker, new_level, proc_t),
                    tracker_set(hatch_op, HATCH_OPACITY, proc_t,
                                rate_func=linear),
                ),
            ]
            gpu_mem_running[g_idx] = new_level
            fill_anims.append(Succession(*ops))

        decode_label = MathTex(
            r"\text{\textbf{Decode growth (unknown at admission)}}",
            color="#C84B00", font_size=22,
        ).move_to([PROC_CENTER_X - 0.6, GPU_YS[0] + GPU_BAR_H / 2 + 0.55, 0])
        right_edge = decode_label.get_right()[0]
        if right_edge > 6.95:
            decode_label.shift(LEFT * (right_edge - 6.95))

        decode_callout = Succession(
            Wait(5.6),
            FadeIn(decode_label, run_time=0.4),
            Wait(2.2),
            FadeOut(decode_label, run_time=0.4),
        )
        self.play(
            AnimationGroup(*fill_anims, lag_ratio=0),
            decode_callout,
        )

        # Phase A.5: naturally complete chips 0..3
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

        # Eviction 1 on GPU 0
        evicted_chip_a, _, hatch_op_a = fill_chips[4]
        self.eviction_sequence(
            gpu_idx=0,
            victim=evicted_chip_a,
            victim_hatch_op=hatch_op_a,
            mem_before=gpu_mem_running[0],
            mem_after=0.05,
            label_text="Memory full -> restart!",
            restart_gpu_idx=2,
            pause_after_label=3.5,
        )
        gpu_mem_running[0] = 0.05

        # Eviction 2 on GPU 1
        evicted_chip_b, _, hatch_op_b = fill_chips[5]
        self.eviction_sequence(
            gpu_idx=1,
            victim=evicted_chip_b,
            victim_hatch_op=hatch_op_b,
            mem_before=gpu_mem_running[1],
            mem_after=0.05,
            label_text="Memory full -> restart!",
            restart_gpu_idx=3,
            pause_after_label=1.5,
        )
        gpu_mem_running[1] = 0.05

        stat = MathTex(
            r"\text{\textbf{26\% of requests restarted --- $\sim$11s wasted per restart}}",
            color=MEM_RED, font_size=28,
        ).to_edge(DOWN, buff=0.6)
        self.play(FadeIn(stat, run_time=0.7))
        self.wait(5.0)

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
        for c in all_chips:
            self.remove(c)

    def eviction_sequence(self, gpu_idx, victim, mem_before, mem_after,
                          label_text, restart_gpu_idx=None,
                          restart_mem_cost=0.30, restart_proc_t=1.9,
                          victim_hatch_op=None,
                          pause_after_label=0.0):
        gpu = self.gpus[gpu_idx]
        gy = gpu['y']

        gpu['mem_override_color'][0] = MEM_RED
        flash_target_outer = gpu['outer'].copy()
        flash_target_outer.set_stroke(MEM_RED, width=3.5)

        push_to_full = tracker_set(gpu['mem_level'], 1.0, 0.25,
                                   rate_func=smooth)
        flash_border = Transform(gpu['outer'], flash_target_outer,
                                 rate_func=there_and_back, run_time=0.5)

        label = MathTex(
            r"\text{\textbf{Memory full} $\rightarrow$ \textbf{restart!}}",
            color=MEM_RED, font_size=22,
        )
        if gpu_idx == 0:
            label.next_to(self.proc_col_label, UP, buff=0.18)
            label.set_x(gpu['outer'].get_center()[0])
        else:
            label.next_to(gpu['outer'], UP, buff=0.08)

        self.play(
            push_to_full,
            flash_border,
            FadeIn(label, shift=RIGHT * 0.1),
            run_time=0.5,
        )

        if pause_after_label > 0:
            self.wait(pause_after_label)

        self.play(
            victim.animate(rate_func=there_and_back, run_time=0.20).shift(
                LEFT * 0.08
            ),
        )

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

        queue_restart_label = MathTex(
            r"\text{\textbf{Restart!}}",
            color=MEM_RED, font_size=28,
        ).next_to(self.global_queue_label, UP, buff=0.1)
        self.play(FadeIn(queue_restart_label, run_time=0.25))

        progress_lost = MathTex(
            r"\text{\textit{Progress lost}}",
            color=BLACK, font_size=14,
        ).next_to(self.global_queue_box, DOWN, buff=0.08)
        self.add(progress_lost)
        progress_lost.set_opacity(0)
        self.play(FadeIn(progress_lost, run_time=0.25))
        progress_fadeout = Succession(
            Wait(1.0),
            FadeOut(progress_lost, run_time=0.3),
        )

        target_gpu_idx = restart_gpu_idx if restart_gpu_idx is not None else gpu_idx
        target_gpu = self.gpus[target_gpu_idx]
        target_gy = target_gpu['y']
        target_mem = target_gpu['mem_level']
        cur_mem = target_mem.get_value()
        new_peak = min(0.95, cur_mem + restart_mem_cost)

        proc_anims = [
            grow_into_proc(victim, target_gy,
                           decode_width(restart_proc_t),
                           restart_proc_t),
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
        restart_labels_fade = AnimationGroup(FadeOut(queue_restart_label, run_time=0.25))
        self.play(
            FadeOut(label, run_time=0.4),
            progress_fadeout,
            Succession(
                AnimationGroup(
                    restart_labels_fade,
                    slide_to(victim, [GLOBAL_QUEUE_FRONT_X, 0, 0], 0.40),
                ),
                slide_to(victim, ROUTER_CENTER, 0.35),
                slide_to(victim, [QUEUE_CENTER_X + 0.3, target_gy, 0], 0.40),
                AnimationGroup(*proc_anims),
                AnimationGroup(*fade_anims),
            ),
        )
