# Render: uv run manim -pqh llm_router.py LLMRouterScene
#
# Slide-embed: LLM-inference request routing across a small GPU cluster
# (Glia Figure 1 style).
#
# The queueing is the centerpiece. Three queue families are visible:
#   - pre-router queue, left of the Request Router box
#   - one queue zone per GPU (left half of each GPU bar)
#   - one processing zone per GPU (right half), which fills like a
#     progress bar while a request is "computing"
#
# A small discrete-event simulator computes the exact times each
# request enters each stage. Per-request animations then read off those
# timestamps so the visual queueing matches a real FIFO schedule.

from manim import *
import numpy as np

config.pixel_height = 1080
config.pixel_width = 1920
config.frame_rate = 30

# ---------------------------------------------------------------------- palette
# White-background academic style, matching the other manimations in this repo.
BG_COLOR = "#FFFFFF"
# Pastel fills paired with a slightly darker stroke for contrast on white.
REQUEST_COLORS = [
    ("#B4C7E7", "#5E7AA0"),  # blue
    ("#F5D5A8", "#B58447"),  # orange
    ("#CCD5C5", "#75876C"),  # green
    ("#F0B8B8", "#A36363"),  # rose
    ("#D6C7E8", "#5A2D82"),  # purple
    ("#FFE082", "#B8941F"),  # gold
]
ROUTER_STROKE = "#5A2D82"   # PURPLE_ACCENT
ROUTER_FILL = "#F5F0F8"
GPU_STROKE = "#444444"
GPU_QUEUE_FILL = "#F2F2F4"
GPU_PROC_FILL = "#E6E6EE"
GPU_PROC_PULSE = "#B6B3D8"
LINE_COLOR = "#A0A0A8"
LABEL_COLOR = "#333333"
SUBLABEL_COLOR = "#888888"
TEXT_FONT = "Arial"

# ---------------------------------------------------------------------- timing
T_SLIDE = 0.55         # off-screen -> pre-queue slot
T_QUEUE_SHIFT = 0.20   # one-slot shift inside pre-queue
T_TO_ROUTER = 0.30     # pre-queue slot 0 -> router center
T_PULSE = 0.25         # held inside the router (decision time)
T_EMIT = 0.50          # router right edge -> GPU queue back slot
T_GPU_SHIFT = 0.18     # one-slot shift inside a GPU queue
T_TO_PROC = 0.25       # GPU queue slot 0 -> proc-zone left edge
T_PROC = 2.80          # fallback / mean expand-fill duration. Individual
                       # requests use PROC_TIMES[i] -- some finish earlier
                       # than others so processing visibly varies.
T_FADE = 0.30          # post-proc fade-out

# ---------------------------------------------------------------------- schedule
# Faster arrival than the router/GPUs can drain, so queues fill before
# they empty. The first GPU is intentionally hammered with four requests
# back-to-back so its queue builds to depth ~3 (visible for ~1.5s).
N_REQUESTS = 11
ARRIVAL_INTERVAL = 0.40
FIRST_ARRIVAL = 0.30
GPU_ASSIGNMENT = [0, 0, 0, 0, 1, 1, 1, 2, 2, 3, 3]

# Per-request processing duration (seconds). Mixed so the audience sees
# some chips finish quickly while others linger -- conveying that prompts
# do different amounts of work.
PROC_TIMES = [2.4, 3.2, 1.8, 2.6, 2.0, 3.4, 1.6, 2.8, 2.2, 3.0, 1.4]

# Request appearance: each request has its own width (suggesting prompt
# length). The same width is used for both the pre-router chip and the
# GPU-queue chip so the size stays constant as it passes through the
# router. Max width 0.55 fits inside the queue-zone slots (gap 0.62)
# without adjacent chips touching.
REQ_HEIGHT = 0.42
REQ_WIDTHS = [0.40, 0.55, 0.35, 0.50, 0.45, 0.55, 0.40, 0.52, 0.55, 0.45, 0.38]


def simulate_schedule():
    """Compute absolute-time event dicts for each request.

    Routes through: arrival -> pre-queue (with shifts) -> router pulse ->
    GPU queue (with shifts) -> processing -> fade.
    """
    arrivals = [FIRST_ARRIVAL + i * ARRIVAL_INTERVAL for i in range(N_REQUESTS)]

    # Pre-queue / router pass:
    # at_slot_0_i is the time request i begins sliding from slot 0 of the
    # pre-queue into the router center.
    all_at_slot_0 = []
    all_enter_router = []
    enter_router_prev = -1e9
    for i in range(N_REQUESTS):
        slide_done = arrivals[i] + T_SLIDE
        if i == 0:
            at_slot_0 = slide_done
        else:
            # Either we are limited by our own slide-in (router was idle),
            # or by the router not yet being free for the next pull.
            at_slot_0 = max(slide_done, enter_router_prev + T_PULSE)
        enter_router = at_slot_0 + T_TO_ROUTER
        enter_router_prev = enter_router
        all_at_slot_0.append(at_slot_0)
        all_enter_router.append(enter_router)

    # Build per-request event records.
    events = []
    gpu_proc_free_at = [-1e9, -1e9, -1e9, -1e9]

    for i in range(N_REQUESTS):
        slide_done = arrivals[i] + T_SLIDE
        # Pre-queue shifts: each request j<i that is still ahead (its
        # at_slot_0 hasn't fired yet) triggers a shift when it leaves
        # slot 0.
        ahead_pre = [j for j in range(i) if all_at_slot_0[j] > slide_done]
        initial_pre_slot = len(ahead_pre)
        ahead_pre_sorted = sorted(ahead_pre, key=lambda j: all_at_slot_0[j])
        pre_shifts = []
        cur = initial_pre_slot
        for j in ahead_pre_sorted:
            cur -= 1
            pre_shifts.append((all_at_slot_0[j], cur))

        enter_router = all_enter_router[i]
        exit_router_pulse = enter_router + T_PULSE
        emit_end = exit_router_pulse + T_EMIT  # request copy reaches GPU queue back

        g = GPU_ASSIGNMENT[i]
        gpu_at_back = emit_end
        # Cannot start sliding to proc until the proc zone is free AND we
        # are at slot 0.
        gpu_at_slot_0 = max(gpu_at_back, gpu_proc_free_at[g])
        proc_start = gpu_at_slot_0 + T_TO_PROC
        proc_time = PROC_TIMES[i]
        proc_end = proc_start + proc_time
        gpu_proc_free_at[g] = proc_end

        events.append({
            'id': i,
            'gpu': g,
            'fill': REQUEST_COLORS[i % len(REQUEST_COLORS)][0],
            'stroke': REQUEST_COLORS[i % len(REQUEST_COLORS)][1],
            'req_width': REQ_WIDTHS[i],
            'arr': arrivals[i],
            'slide_done': slide_done,
            'initial_pre_slot': initial_pre_slot,
            'pre_shifts': pre_shifts,
            'at_slot_0_pre': all_at_slot_0[i],
            'enter_router': enter_router,
            'exit_router_pulse': exit_router_pulse,
            'emit_end': emit_end,
            'gpu_at_back': gpu_at_back,
            'gpu_at_slot_0': gpu_at_slot_0,
            'proc_time': proc_time,
            'proc_start': proc_start,
            'proc_end': proc_end,
            'fade_end': proc_end + T_FADE,
        })

    # GPU queue layout when request i reaches the GPU (emit_end):
    # Count every prior request j on this GPU that has not finished processing
    # yet (proc_end_j > emit_end_i). One of them may be in the proc zone;
    # the rest are (or will be) in the queue. The new arrival sits at the
    # back, horizontally after everyone still in the FIFO.
    #
    # Using gpu_at_slot_0[j] > emit_end was wrong: it dropped anyone who had
    # already reached slot 0 or started proc, so later arrivals incorrectly
    # reused slot 0 and drew on top of each other in the queue/proc seam.
    for i, ev in enumerate(events):
        g = ev['gpu']
        emit_end = ev['emit_end']
        active_prev = [
            j for j in range(i)
            if events[j]['gpu'] == g and events[j]['proc_end'] > emit_end
        ]
        in_proc = sum(
            1 for j in active_prev
            if events[j]['proc_start'] <= emit_end < events[j]['proc_end']
        )
        queued_ahead = len(active_prev) - in_proc
        initial_gpu_slot = queued_ahead
        # Shifts toward slot 0 when an ahead-of-us peer leaves slot 0 for proc.
        in_queue_prev = [
            j for j in active_prev
            if events[j]['proc_start'] > emit_end
        ]
        ahead_sorted = sorted(in_queue_prev, key=lambda j: events[j]['gpu_at_slot_0'])
        gpu_shifts = []
        cur = initial_gpu_slot
        for j in ahead_sorted:
            dep_time = events[j]['gpu_at_slot_0']
            if dep_time < emit_end:
                continue
            cur -= 1
            gpu_shifts.append((dep_time, cur))
        ev['initial_gpu_slot'] = initial_gpu_slot
        ev['gpu_shifts'] = gpu_shifts

    return events


class LLMRouterScene(Scene):
    def construct(self):
        self.camera.background_color = BG_COLOR

        # ============================================================== layout
        router_center = np.array([-1.7, 0.0, 0.0])
        router_w, router_h = 2.6, 1.3

        router = RoundedRectangle(
            width=router_w, height=router_h, corner_radius=0.18,
            stroke_color=ROUTER_STROKE, stroke_width=2.2,
            fill_color=ROUTER_FILL, fill_opacity=0.85,
        ).move_to(router_center)
        router_label = MathTex(
            r"\text{\textbf{Request Router}}", color=BLACK, font_size=30,
        ).move_to(router.get_center())

        router_left_x = router.get_left()[0]      # -3.0
        router_right_x = router.get_right()[0]    # -0.4

        # Pre-queue slot positions (slot 0 = front, just left of router).
        # Slot 3 (~-6.45) is well inside the visible frame (-7.11..7.11).
        def pre_slot_x(slot):
            return router_left_x - 0.45 - slot * 1.00

        # GPU bars
        gpu_ys = [2.3, 0.8, -0.8, -2.3]
        gpu_bar_w = 4.4
        gpu_bar_h = 1.0
        gpu_center_x = 4.6
        queue_frac = 0.4

        gpu_left_edge = gpu_center_x - gpu_bar_w / 2          # 2.4
        queue_w = gpu_bar_w * queue_frac                      # 1.76
        proc_w = gpu_bar_w - queue_w                          # 2.64
        proc_left_x = gpu_left_edge + queue_w                 # 4.16
        queue_zone_center_x = gpu_left_edge + queue_w / 2     # 3.28
        proc_zone_center_x = proc_left_x + proc_w / 2         # 5.48

        # GPU queue slot positions (slot 0 = front, closest to proc).
        # Three slots fit cleanly inside the queue zone.
        def gpu_slot_x(slot):
            return 3.88 - slot * 0.62

        gpus = []
        for i, y in enumerate(gpu_ys):
            outer = RoundedRectangle(
                width=gpu_bar_w, height=gpu_bar_h, corner_radius=0.12,
                stroke_color=GPU_STROKE, stroke_width=1.6,
                fill_color=BG_COLOR, fill_opacity=1.0,
            ).move_to([gpu_center_x, y, 0])
            queue_zone = Rectangle(
                width=queue_w - 0.04, height=gpu_bar_h - 0.08,
                stroke_width=0, fill_color=GPU_QUEUE_FILL, fill_opacity=1.0,
            ).move_to([queue_zone_center_x, y, 0])
            proc_zone = Rectangle(
                width=proc_w - 0.04, height=gpu_bar_h - 0.08,
                stroke_width=0, fill_color=GPU_PROC_FILL, fill_opacity=1.0,
            ).move_to([proc_zone_center_x, y, 0])
            divider = DashedLine(
                start=[proc_left_x, y - 0.38, 0],
                end=[proc_left_x, y + 0.38, 0],
                color=GPU_STROKE, stroke_width=1.0, dash_length=0.06,
            )
            # Background breathing pulse on each proc zone -- conveys
            # "actively computing" even when no request is currently in proc.
            pulse = Rectangle(
                width=proc_w - 0.10, height=gpu_bar_h - 0.16,
                stroke_width=0, fill_color=GPU_PROC_PULSE, fill_opacity=0.0,
            ).move_to([proc_zone_center_x, y, 0])
            name_label = MathTex(
                r"\text{\textbf{GPU " + str(i) + "}}", color=BLACK, font_size=18,
            ).next_to(outer, LEFT, buff=0.22)

            gpus.append({
                'outer': outer, 'queue_zone': queue_zone, 'proc_zone': proc_zone,
                'divider': divider, 'pulse': pulse, 'name_label': name_label,
                'y': y,
            })

        # Static connection lines from router right to each GPU's left edge.
        router_right_pt = np.array([router_right_x, 0.0, 0.0])
        connection_lines = [
            Line(
                start=router_right_pt,
                end=[gpu_left_edge, g['y'], 0],
                stroke_color=LINE_COLOR, stroke_width=1.2,
            )
            for g in gpus
        ]

        top = gpus[0]
        queue_col_label = MathTex(
            r"\text{\textbf{Queue}}", color=BLACK, font_size=22,
        ).move_to([queue_zone_center_x, top['y'] + gpu_bar_h / 2 + 0.20, 0])
        proc_col_label = MathTex(
            r"\text{\textbf{Processing}}", color=BLACK, font_size=22,
        ).move_to([proc_zone_center_x, top['y'] + gpu_bar_h / 2 + 0.20, 0])

        # Compose static scene
        self.add(*connection_lines)
        self.add(
            *[g['outer'] for g in gpus],
            *[g['queue_zone'] for g in gpus],
            *[g['proc_zone'] for g in gpus],
            *[g['divider'] for g in gpus],
            *[g['name_label'] for g in gpus],
        )
        self.add(router, router_label, queue_col_label, proc_col_label)

        # Pulse overlays on proc zones (subtle breathing).
        def make_pulser(phase_init):
            t_state = [phase_init]

            def updater(mob, dt):
                t_state[0] += dt
                op = 0.06 + 0.16 * (np.sin(t_state[0] * 2.6) ** 2)
                mob.set_fill(opacity=op)

            return updater

        for i, g in enumerate(gpus):
            self.add(g['pulse'])
            g['pulse'].add_updater(make_pulser(i * 0.55))

        # ============================================================ schedule
        events = simulate_schedule()

        # =========================================================== animation
        # Each request gets TWO mobjects:
        #   req_pre  -- the visual on the way IN (off-screen -> pre-queue -> router pulse -> fade)
        #   req_post -- the dispatched copy that emerges from the router's
        #               right edge and proceeds through the GPU queue + proc.
        # This gives the router a clean "decision + emit" feel rather than
        # a conveyor-belt slide-through.
        #
        # Critical: we use explicit Transform(mob, fresh_copy_with_target)
        # animations rather than `.animate.move_to(...)`. The `.animate`
        # builder pattern uses a shared `mob.target` attribute that gets
        # overwritten by each subsequent `.animate` call -- so when the
        # Succession is built later, every animation in the chain ends up
        # pointing at the LAST target. That bug manifested here as all
        # queued chips piling up at the proc-entry coordinate instead of
        # taking their assigned slot. Explicit Transforms with their own
        # target instances sidestep this entirely.
        # Note: every slide() target explicitly restores fill/stroke opacity
        # to REQ_OPACITY. Without this, a slide for a mobject that was
        # constructed invisible (opacity 0, so the AnimationGroup's
        # _setup_scene wouldn't show it at t=0) would inherit opacity 0
        # in its target and fade the chip back out mid-slide.
        REQ_OPACITY = 0.95
        HATCH_OPACITY = 0.55

        def make_hatch(width, height, color, spacing=0.10):
            """45-degree diagonal hatch lines filling a width x height rect
            centered at the origin. Lines are clipped to the rectangle."""
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

        def slide(mob, dest_xyz, run_time, rate_func=smooth):
            target = mob.copy()
            target.move_to(dest_xyz)
            target.set_opacity(REQ_OPACITY)
            return Transform(mob, target, run_time=run_time, rate_func=rate_func)

        def tracker_to(tracker, value, run_time):
            """Animate a ValueTracker to a target value via an explicit
            Transform (avoids the .animate quirk where chained builders
            share mob.target)."""
            target = tracker.copy()
            target.set_value(value)
            return Transform(tracker, target, run_time=run_time)

        all_anims = []

        for i, ev in enumerate(events):
            fill_c = ev['fill']
            stroke_c = ev['stroke']
            gy = gpus[ev['gpu']]['y']

            # ---- pre-router visual ----
            req_pre = RoundedRectangle(
                width=ev['req_width'], height=REQ_HEIGHT, corner_radius=0.09,
                stroke_color=stroke_c, stroke_width=1.8,
                fill_color=fill_c, fill_opacity=0.95,
            ).move_to([-9.5, 0, 0])
            self.add(req_pre)

            pre_ops = []
            t_cursor = 0.0

            pre_ops.append(Wait(ev['arr']))
            t_cursor = ev['arr']

            # Slide-in from off-screen to initial pre-queue slot.
            pre_ops.append(
                slide(req_pre,
                      [pre_slot_x(ev['initial_pre_slot']), 0, 0],
                      T_SLIDE)
            )
            t_cursor += T_SLIDE

            # Shifts triggered by each prior request leaving slot 0.
            for shift_time, new_slot in ev['pre_shifts']:
                if shift_time > t_cursor:
                    pre_ops.append(Wait(shift_time - t_cursor))
                    t_cursor = shift_time
                pre_ops.append(
                    slide(req_pre, [pre_slot_x(new_slot), 0, 0], T_QUEUE_SHIFT)
                )
                t_cursor += T_QUEUE_SHIFT

            # Wait until this request's turn at the router.
            if ev['at_slot_0_pre'] > t_cursor:
                pre_ops.append(Wait(ev['at_slot_0_pre'] - t_cursor))
                t_cursor = ev['at_slot_0_pre']

            # Slide slot 0 -> router center.
            pre_ops.append(slide(req_pre, router.get_center(), T_TO_ROUTER))
            t_cursor += T_TO_ROUTER

            # Hold inside the router (decision moment). We deliberately
            # don't scale-pulse: a Transform-based pulse with a target
            # captured at construction time teleports the chip to its
            # initial off-screen position mid-pulse.
            pre_ops.append(Wait(T_PULSE))
            t_cursor += T_PULSE

            # Disappear -- the post-router copy will materialize at the right edge.
            pre_ops.append(FadeOut(req_pre, run_time=0.15))
            t_cursor += 0.15

            all_anims.append(Succession(*pre_ops))

            # ---- post-router visual (dispatched copy) ----
            # Plain bar (not a VGroup with hatch): the hatch is managed
            # separately below so it can rebuild its 45-degree lines each
            # frame instead of being stretched along with the bar.
            req_post = RoundedRectangle(
                width=ev['req_width'], height=REQ_HEIGHT, corner_radius=0.08,
                stroke_color=stroke_c, stroke_width=1.8,
                fill_color=fill_c, fill_opacity=REQ_OPACITY,
            ).move_to([router_right_x, 0, 0])
            req_post.set_opacity(0)  # invisible until appear_target Transform

            # Hatch overlay (separate mobject, regenerated from the bar's
            # current bbox each frame via always_redraw -- so its 45-degree
            # lines never get stretched along with the bar). opacity_tracker
            # controls fade-in/fade-out independently of bar opacity.
            opacity_tracker = ValueTracker(0.0)

            def build_hatch(bar_ref=req_post, tracker_ref=opacity_tracker,
                            color=stroke_c):
                op = tracker_ref.get_value()
                if op < 5e-3:
                    return VGroup()
                bar_w = bar_ref.get_width()
                if bar_w < 1e-2:
                    return VGroup()
                lines = make_hatch(
                    bar_w * 0.88, REQ_HEIGHT * 0.62, color, spacing=0.10,
                )
                lines.move_to([bar_ref.get_x(), bar_ref.get_y(), 0])
                lines.set_opacity(op)
                return lines

            hatch_overlay = always_redraw(build_hatch)
            # Force the hatch above the bar (the AnimationGroup will add the
            # bar later via _setup_scene; without an explicit z_index the
            # bar ends up rendered on top and hides the hatch).
            hatch_overlay.set_z_index(10)
            self.add(hatch_overlay)

            post_ops = []
            t_cursor = 0.0

            # Hold off until the router pulse completes.
            post_ops.append(Wait(ev['exit_router_pulse']))
            t_cursor = ev['exit_router_pulse']

            # Pop into existence at the router's right edge.
            appear_target = req_post.copy()
            appear_target.set_opacity(REQ_OPACITY)
            post_ops.append(Transform(req_post, appear_target, run_time=0.10))
            t_cursor += 0.10

            # Hatch Succession: bring the tracker up at proc_start, hold
            # through the proc duration, then drop back to 0 in sync with
            # the bar's FadeOut. Runs in parallel to the bar's Succession.
            hatch_ops = [
                Wait(ev['proc_start']),
                tracker_to(opacity_tracker, HATCH_OPACITY, 0.15),
                Wait(max(0.0, ev['proc_time'] - 0.15)),
                tracker_to(opacity_tracker, 0.0, T_FADE),
            ]
            all_anims.append(Succession(*hatch_ops))

            # Slide to the back of the assigned GPU's queue.
            slide_to_gpu = max(0.10, ev['emit_end'] - t_cursor)
            post_ops.append(
                slide(req_post,
                      [gpu_slot_x(ev['initial_gpu_slot']), gy, 0],
                      slide_to_gpu)
            )
            t_cursor = ev['emit_end']

            # Shifts triggered by other requests on the same GPU leaving slot 0.
            for shift_time, new_slot in ev['gpu_shifts']:
                if shift_time > t_cursor:
                    post_ops.append(Wait(shift_time - t_cursor))
                    t_cursor = shift_time
                post_ops.append(
                    slide(req_post, [gpu_slot_x(new_slot), gy, 0], T_GPU_SHIFT)
                )
                t_cursor += T_GPU_SHIFT

            # Wait for the proc zone to be free.
            if ev['gpu_at_slot_0'] > t_cursor:
                post_ops.append(Wait(ev['gpu_at_slot_0'] - t_cursor))
                t_cursor = ev['gpu_at_slot_0']

            # Slide from queue slot 0 to the proc-zone left edge. Center
            # the request so its left edge sits at proc_left_x; the
            # subsequent expand will then grow rightward.
            proc_entry_center_x = proc_left_x + ev['req_width'] / 2
            post_ops.append(slide(req_post, [proc_entry_center_x, gy, 0], T_TO_PROC))
            t_cursor += T_TO_PROC

            # Expand-fill: stretch the request horizontally to fill the
            # proc zone. Anchored at the left edge so it reads as a
            # progress bar growing from 0 -> full width.
            target_width = proc_w * 0.94
            proc_target = req_post.copy()
            proc_target.stretch_to_fit_width(target_width)
            proc_target.move_to([proc_left_x + target_width / 2, gy, 0])
            proc_target.set_opacity(REQ_OPACITY)
            post_ops.append(
                Transform(req_post, proc_target,
                          run_time=ev['proc_time'], rate_func=linear)
            )
            t_cursor += ev['proc_time']

            # Done -- fade out so this GPU is visually free again.
            post_ops.append(FadeOut(req_post, run_time=T_FADE))
            t_cursor += T_FADE

            all_anims.append(Succession(*post_ops))

        # =============================================================== play
        self.play(AnimationGroup(*all_anims, lag_ratio=0))

        # Hold the final empty-layout frame so the loop start/end match.
        self.wait(0.85)

        # Stop the breathing pulses for a stable last frame.
        for g in gpus:
            g['pulse'].clear_updaters()
            g['pulse'].set_fill(opacity=0.0)
        self.wait(0.05)
