"""
Vidaptive: Conference Talk Video Script
"Tight Loops, Smooth Streams: Responsive Congestion Control for Real-Time Video"

This script generates a ~15-minute conference talk video about the Vidaptive paper.
Render with: manim -pqh vidaptive_talk.py SceneName

Target total duration: ~900 seconds (15 minutes)
"""

from manim import *
import numpy as np

# ============================================================================
# CONFIGURATION & COLOR SCHEME
# ============================================================================

config.frame_rate = 30
config.frame_width = 16
config.frame_height = 9
config.background_color = "#1E1E1E"  # Apply background globally

# Color palette
VIDAPTIVE_COLOR = "#2E86AB"  # Blue
GCC_COLOR = "#A23B72"  # Purple
COPA_COLOR = "#F18F01"  # Orange
DUMMY_COLOR = GRAY_D
VIDEO_PACKET_COLOR = VIDAPTIVE_COLOR
BACKGROUND_COLOR = "#1E1E1E"
TEXT_COLOR = WHITE

# Layout constants
TITLE_AREA_HEIGHT = 1.5
CAPTION_AREA_HEIGHT = 1.0
MAIN_AREA_TOP = 3.5
MAIN_AREA_BOTTOM = -3.0

# Timing constants
DEFAULT_WAIT_SHORT = 0.5
DEFAULT_WAIT_LONG = 1.5

# Typography sizes
TITLE_SIZE = 60
SUBTITLE_SIZE = 40
CAPTION_SIZE = 28
BULLET_SIZE = 30


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def add_title(scene_or_text: str | Scene, title_text: str = "") -> Text:
    """Create a title text at the top of the screen.
    
    Can be called as:
    - add_title(self, "Title Text") in a scene's construct()
    - add_title("Title Text") for standalone usage
    """
    if isinstance(scene_or_text, str):
        title_text = scene_or_text
    title = Text(title_text, font_size=TITLE_SIZE, color=TEXT_COLOR, weight=BOLD)
    return title.to_edge(UP, buff=0.3)


def add_caption(scene_or_text: str | Scene, caption_text: str = "") -> Text:
    """Create a caption text at the bottom of the screen."""
    if isinstance(scene_or_text, str):
        caption_text = scene_or_text
    caption = Text(caption_text, font_size=CAPTION_SIZE, color=TEXT_COLOR, slant=ITALIC)
    return caption.to_edge(DOWN, buff=0.3)


def add_takeaway(scene_or_text: str | Scene, takeaway_text: str = "") -> Text:
    """Create a highlighted takeaway banner (yellow) at bottom."""
    if isinstance(scene_or_text, str):
        takeaway_text = scene_or_text
    takeaway = Text(
        takeaway_text, 
        font_size=CAPTION_SIZE + 2, 
        color=YELLOW, 
        weight=BOLD
    )
    return takeaway.to_edge(DOWN, buff=0.3)


def make_title(text: str, font_size: int = TITLE_SIZE) -> Text:
    """Create a title text at the top of the screen (legacy helper)."""
    return add_title(text)


def make_subtitle(text: str, font_size: int = SUBTITLE_SIZE) -> Text:
    """Create a subtitle text."""
    subtitle = Text(text, font_size=font_size, color=TEXT_COLOR)
    return subtitle


def make_bullet_list(items: list[str], font_size: int = BULLET_SIZE, buff: float = 0.5) -> VGroup:
    """Create a bulleted list of items."""
    bullet_items = []
    for item in items:
        bullet = Text("•", font_size=font_size, color=TEXT_COLOR)
        text = Text(item, font_size=font_size, color=TEXT_COLOR)
        bullet_item = VGroup(bullet, text)
        text.next_to(bullet, RIGHT, buff=0.2)
        bullet_items.append(bullet_item)
    
    group = VGroup(*bullet_items)
    group.arrange(DOWN, aligned_edge=LEFT, buff=buff)
    return group


def make_network_pipe(
    sender_label: str = "Sender",
    receiver_label: str = "Receiver",
    link_length: float = 6.0,
    link_height: float = 0.6
) -> VGroup:
    """Create a sender → bottleneck link → receiver diagram."""
    sender_box = Rectangle(
        width=1.5, height=1.0, color=VIDAPTIVE_COLOR
    ).shift(LEFT * (link_length / 2 + 1.5))
    
    receiver_box = Rectangle(
        width=1.5, height=1.0, color=VIDAPTIVE_COLOR
    ).shift(RIGHT * (link_length / 2 + 1.5))
    
    # Link pipe
    link = Rectangle(
        width=link_length, height=link_height,
        fill_opacity=0.3, fill_color=VIDAPTIVE_COLOR,
        stroke_color=VIDAPTIVE_COLOR, stroke_width=3
    )
    
    # Arrow
    arrow = Arrow(
        start=link.get_left() + 0.2 * RIGHT,
        end=link.get_right() + 0.2 * LEFT,
        color=TEXT_COLOR, buff=0
    )
    
    # Labels
    sender_text = Text(sender_label, font_size=28, color=TEXT_COLOR)
    sender_text.next_to(sender_box, DOWN, buff=0.2)
    
    receiver_text = Text(receiver_label, font_size=28, color=TEXT_COLOR)
    receiver_text.next_to(receiver_box, DOWN, buff=0.2)
    
    # Bottleneck indicator
    bottleneck_marker = Text("Bottleneck", font_size=24, color=YELLOW)
    bottleneck_marker.next_to(link, UP, buff=0.3)
    
    return VGroup(
        sender_box, receiver_box, link, arrow,
        sender_text, receiver_text, bottleneck_marker
    )


def make_queue_box(label: str = "Queue", width: float = 2.0, height: float = 1.5) -> VGroup:
    """Create a queue box with label."""
    box = Rectangle(
        width=width, height=height,
        stroke_color=VIDAPTIVE_COLOR, stroke_width=2,
        fill_opacity=0.1, fill_color=VIDAPTIVE_COLOR
    )
    label_text = Text(label, font_size=24, color=TEXT_COLOR)
    label_text.next_to(box, UP, buff=0.2)
    return VGroup(box, label_text)


def make_packet(
    is_video: bool = True,
    size: float = 0.3,
    label: str = ""
) -> VGroup:
    """Create a packet (small rectangle) for video or dummy."""
    color = VIDEO_PACKET_COLOR if is_video else DUMMY_COLOR
    packet = Rectangle(
        width=size, height=size * 0.6,
        fill_color=color, fill_opacity=0.8,
        stroke_color=color, stroke_width=1
    )
    
    if label:
        label_text = Text(label, font_size=16, color=TEXT_COLOR)
        label_text.move_to(packet)
        return VGroup(packet, label_text)
    return packet


def make_caption(text: str, font_size: int = CAPTION_SIZE) -> Text:
    """Create a caption text at the bottom of the screen (legacy helper)."""
    return add_caption(text)


def clear_scene(self: Scene, keep_title: bool = False):
    """Optional helper to clear scene, keeping title if requested."""
    mobjects_to_remove = [m for m in self.mobjects if not (keep_title and hasattr(m, 'text') and m.text)]
    self.remove(*mobjects_to_remove)


def make_lightning_icon() -> VGroup:
    """Create a simple lightning bolt icon."""
    points = [
        np.array([0, 0.5, 0]),
        np.array([0.2, 0.2, 0]),
        np.array([0, 0, 0]),
        np.array([0.3, -0.2, 0]),
        np.array([0.1, -0.5, 0]),
        np.array([-0.1, -0.2, 0]),
        np.array([0.1, 0, 0]),
        np.array([-0.1, 0.2, 0]),
    ]
    bolt = Polygon(*points, fill_color=YELLOW, fill_opacity=1, stroke_color=YELLOW)
    return bolt.scale(0.5)


def make_box_icon() -> VGroup:
    """Create a simple box icon."""
    box = Rectangle(width=0.6, height=0.6, stroke_color=VIDAPTIVE_COLOR, stroke_width=2)
    lid = Line(box.get_top() + LEFT * 0.2, box.get_top() + RIGHT * 0.2, stroke_color=VIDAPTIVE_COLOR, stroke_width=2)
    return VGroup(box, lid)


def make_wrench_icon() -> VGroup:
    """Create a simple wrench icon."""
    handle = Line(LEFT * 0.3, RIGHT * 0.3, stroke_color=GRAY, stroke_width=3)
    head = Circle(radius=0.15, stroke_color=GRAY, stroke_width=3)
    head.shift(RIGHT * 0.15)
    return VGroup(handle, head)


def make_plug_icon() -> VGroup:
    """Create a simple plug icon."""
    body = Rectangle(width=0.3, height=0.5, fill_color=GRAY, fill_opacity=0.8, stroke_color=GRAY)
    prong1 = Line(body.get_top() + LEFT * 0.08, body.get_top() + LEFT * 0.08 + UP * 0.2, stroke_color=GRAY, stroke_width=3)
    prong2 = Line(body.get_top() + RIGHT * 0.08, body.get_top() + RIGHT * 0.08 + UP * 0.2, stroke_color=GRAY, stroke_width=3)
    return VGroup(body, prong1, prong2)


# ============================================================================
# SCENE 0: PersonalStoryHook
# ============================================================================

class PersonalStoryHook(Scene):
    """VO: Knock knock... let's turn off the videos!! Story beat about latency killing interactivity."""
    
    def construct(self):
        self.camera.background_color = BACKGROUND_COLOR
        
        # VO: It was during a group meeting. Everyone had their cameras on, and the call was laggy.
        
        title = add_title(self, "A Personal Story")
        
        # Chat bubbles appearing one by one
        chat1 = Text("Knock knock...", font_size=SUBTITLE_SIZE, color=TEXT_COLOR)
        chat1.shift(UP * 2 + LEFT * 2)
        chat_bubble1 = SurroundingRectangle(chat1, color=VIDAPTIVE_COLOR, buff=0.3, corner_radius=0.2)
        
        chat2 = Text("Let's turn off the videos!", font_size=SUBTITLE_SIZE, color=TEXT_COLOR)
        chat2.shift(UP * 1 + LEFT * 1.5)
        chat_bubble2 = SurroundingRectangle(chat2, color=GCC_COLOR, buff=0.3, corner_radius=0.2)
        
        chat3 = Text("The call is too laggy", font_size=SUBTITLE_SIZE, color=TEXT_COLOR)
        chat3.shift(LEFT * 1)
        chat_bubble3 = SurroundingRectangle(chat3, color=COPA_COLOR, buff=0.3, corner_radius=0.2)
        
        # Camera icon with cross-out
        camera_icon = Rectangle(width=1.5, height=1.0, stroke_color=TEXT_COLOR, stroke_width=3)
        camera_icon.shift(RIGHT * 3)
        lens = Circle(radius=0.3, stroke_color=TEXT_COLOR, stroke_width=2)
        lens.move_to(camera_icon.get_center() + UP * 0.1)
        
        cross_line1 = Line(
            camera_icon.get_corner(UL) + 0.2 * DOWN + 0.2 * RIGHT,
            camera_icon.get_corner(DR) + 0.2 * UP + 0.2 * LEFT,
            color=RED, stroke_width=5
        )
        cross_line2 = Line(
            camera_icon.get_corner(UR) + 0.2 * DOWN + 0.2 * LEFT,
            camera_icon.get_corner(DL) + 0.2 * UP + 0.2 * RIGHT,
            color=RED, stroke_width=5
        )
        
        # Big takeaway
        takeaway = add_takeaway(self, "Latency kills interactivity")
        
        # Animate
        self.play(Write(title), run_time=1)
        self.wait(DEFAULT_WAIT_SHORT)
        
        self.play(Write(chat1), Create(chat_bubble1), run_time=1)
        self.wait(DEFAULT_WAIT_SHORT)
        
        self.play(Write(chat2), Create(chat_bubble2), run_time=1.2)
        self.wait(DEFAULT_WAIT_SHORT)
        
        self.play(Write(chat3), Create(chat_bubble3), run_time=1.2)
        self.wait(1)
        
        self.play(Create(camera_icon), Create(lens), run_time=1)
        self.wait(0.5)
        self.play(Create(cross_line1), Create(cross_line2), run_time=1.5)
        self.wait(1)
        
        self.play(Write(takeaway), run_time=1.5)
        self.wait(2)
        
        # Total: ~40-50 seconds


# ============================================================================
# SCENE 1: VideoAppClasses
# ============================================================================

class VideoAppClasses(Scene):
    """VO: Video apps fall into two classes: streaming vs real-time."""
    
    def construct(self):
        self.camera.background_color = BACKGROUND_COLOR
        
        title = add_title(self, "Video App Classes")
        
        # 2-column comparison: Streaming vs Real-time
        streaming_col = VGroup()
        streaming_title = Text("Streaming", font_size=SUBTITLE_SIZE, color=GCC_COLOR, weight=BOLD)
        streaming_title.shift(LEFT * 4 + UP * 2)
        
        streaming_items = make_bullet_list([
            "Netflix, YouTube",
            "Large buffers OK",
            "Quality-first"
        ], font_size=BULLET_SIZE, buff=0.4)
        streaming_items.shift(LEFT * 4 + UP * 0.5)
        
        realtime_col = VGroup()
        realtime_title = Text("Real-time", font_size=SUBTITLE_SIZE, color=VIDAPTIVE_COLOR, weight=BOLD)
        realtime_title.shift(RIGHT * 4 + UP * 2)
        
        realtime_items = make_bullet_list([
            "Zoom, Teams, gaming",
            "No buffer allowed",
            "Latency-critical"
        ], font_size=BULLET_SIZE, buff=0.4)
        realtime_items.shift(RIGHT * 4 + UP * 0.5)
        
        # Latency target visualization
        latency_arrow = Arrow(
            LEFT * 2 + DOWN * 1.5,
            RIGHT * 2 + DOWN * 1.5,
            color=YELLOW, stroke_width=4
        )
        latency_label = Text("Latency budget", font_size=24, color=YELLOW, weight=BOLD)
        latency_label.next_to(latency_arrow, UP, buff=0.3)
        
        capture_label = Text("Capture", font_size=20, color=TEXT_COLOR)
        capture_label.next_to(latency_arrow.get_start(), DOWN, buff=0.3)
        
        display_label = Text("Display", font_size=20, color=TEXT_COLOR)
        display_label.next_to(latency_arrow.get_end(), DOWN, buff=0.3)
        
        caption = add_caption(self, "Real-time apps need sub-100ms end-to-end latency")
        
        # Animate
        self.play(Write(title), run_time=1)
        self.wait(DEFAULT_WAIT_SHORT)
        
        self.play(Write(streaming_title), Write(realtime_title), run_time=1.5)
        self.wait(DEFAULT_WAIT_SHORT)
        
        self.play(
            Write(streaming_items),
            Write(realtime_items),
            run_time=2.5
        )
        self.wait(1)
        
        self.play(Create(latency_arrow), Write(latency_label), run_time=1.5)
        self.play(Write(capture_label), Write(display_label), run_time=1)
        self.wait(1)
        
        self.play(Write(caption), run_time=1)
        self.wait(2)
        
        # Total: ~60 seconds


# ============================================================================
# SCENE 2: SystemStructureAndWhereCCFits
# ============================================================================

class SystemStructureAndWhereCCFits(Scene):
    """VO: Let's look at the pipeline and where congestion control fits."""
    
    def construct(self):
        self.camera.background_color = BACKGROUND_COLOR
        
        title = add_title(self, "System Structure: Where Does CC Fit?")
        
        # Pipeline: Encoder → Pacer → Network → Decoder
        encoder_box = Rectangle(
            width=1.8, height=1.0,
            stroke_color=VIDAPTIVE_COLOR, stroke_width=2,
            fill_opacity=0.1, fill_color=VIDAPTIVE_COLOR
        )
        encoder_box.shift(LEFT * 5 + UP * 0.5)
        
        encoder_label = Text("Encoder", font_size=24, color=TEXT_COLOR)
        encoder_label.move_to(encoder_box)
        
        pacer_box = Rectangle(
            width=1.8, height=1.0,
            stroke_color=YELLOW, stroke_width=2,
            fill_opacity=0.1, fill_color=YELLOW
        )
        pacer_box.shift(LEFT * 2 + UP * 0.5)
        
        pacer_label = Text("Pacer", font_size=24, color=TEXT_COLOR)
        pacer_label.move_to(pacer_box)
        
        network_box = Rectangle(
            width=1.8, height=1.0,
            stroke_color=TEXT_COLOR, stroke_width=2
        )
        network_box.shift(RIGHT * 1 + UP * 0.5)
        
        network_label = Text("Network", font_size=24, color=TEXT_COLOR)
        network_label.move_to(network_box)
        
        decoder_box = Rectangle(
            width=1.8, height=1.0,
            stroke_color=GREEN, stroke_width=2,
            fill_opacity=0.1, fill_color=GREEN
        )
        decoder_box.shift(RIGHT * 4 + UP * 0.5)
        
        decoder_label = Text("Decoder", font_size=24, color=TEXT_COLOR)
        decoder_label.move_to(decoder_box)
        
        # Flow arrows
        arrow1 = Arrow(encoder_box.get_right(), pacer_box.get_left(), color=TEXT_COLOR, buff=0.1)
        arrow2 = Arrow(pacer_box.get_right(), network_box.get_left(), color=TEXT_COLOR, buff=0.1)
        arrow3 = Arrow(network_box.get_right(), decoder_box.get_left(), color=TEXT_COLOR, buff=0.1)
        
        # CC block feeding Target bitrate
        cc_box = Rectangle(
            width=2.5, height=1.2,
            stroke_color=ORANGE, stroke_width=3,
            fill_opacity=0.2, fill_color=ORANGE
        )
        cc_box.shift(LEFT * 1.5 + DOWN * 2)
        
        cc_label = Text("Congestion\nControl", font_size=22, color=TEXT_COLOR, weight=BOLD)
        cc_label.move_to(cc_box)
        
        # Arrow from CC to encoder
        cc_arrow = Arrow(
            cc_box.get_top(),
            encoder_box.get_bottom(),
            color=ORANGE, stroke_width=3, buff=0.2
        )
        
        target_label = Text("Target bitrate", font_size=20, color=ORANGE)
        target_label.next_to(cc_arrow, RIGHT, buff=0.2)
        
        # Takeaway
        takeaway = add_takeaway(self, "Today CC controls the encoder, not the wire")
        
        # Animate
        self.play(Write(title), run_time=1)
        self.wait(DEFAULT_WAIT_SHORT)
        
        # Show pipeline
        boxes = [encoder_box, encoder_label, pacer_box, pacer_label,
                 network_box, network_label, decoder_box, decoder_label]
        self.play(LaggedStart(*[Create(b) for b in boxes], lag_ratio=0.1), run_time=2)
        self.wait(DEFAULT_WAIT_SHORT)
        
        self.play(Create(arrow1), Create(arrow2), Create(arrow3), run_time=1.5)
        self.wait(DEFAULT_WAIT_SHORT)
        
        # Show CC
        self.play(Create(cc_box), Write(cc_label), run_time=1.5)
        self.wait(DEFAULT_WAIT_SHORT)
        self.play(Create(cc_arrow), Write(target_label), run_time=1.5)
        self.wait(1)
        
        self.play(Write(takeaway), run_time=1.5)
        self.wait(1)
        
        # Total: ~45 seconds


# ============================================================================
# SCENE 3: FirstStepSwapInCopa
# ============================================================================

class FirstStepSwapInCopa(Scene):
    """VO: Our first step: swap WebRTC GCC for Copa. What happened?"""
    
    def construct(self):
        self.camera.background_color = BACKGROUND_COLOR
        
        title = add_title(self, "First Step: Swap in Copa")
        
        # WebRTC GCC box
        gcc_box = Rectangle(
            width=3, height=1.5,
            stroke_color=GCC_COLOR, stroke_width=3,
            fill_opacity=0.2, fill_color=GCC_COLOR
        )
        gcc_box.shift(LEFT * 2)
        
        gcc_label = Text("WebRTC GCC", font_size=32, color=TEXT_COLOR, weight=BOLD)
        gcc_label.move_to(gcc_box)
        
        # Copa box
        copa_box = Rectangle(
            width=3, height=1.5,
            stroke_color=COPA_COLOR, stroke_width=3,
            fill_opacity=0.2, fill_color=COPA_COLOR
        )
        copa_box.shift(RIGHT * 2)
        
        copa_label = Text("Copa", font_size=32, color=TEXT_COLOR, weight=BOLD)
        copa_label.move_to(copa_box)
        
        # Swap arrow
        swap_arrow = DoubleArrow(
            gcc_box.get_right(),
            copa_box.get_left(),
            color=YELLOW, stroke_width=4, buff=0.3
        )
        
        # Latency numbers
        gcc_latency = Text("P95 latency:\n200ms", font_size=24, color=GCC_COLOR)
        gcc_latency.next_to(gcc_box, DOWN, buff=0.5)
        
        copa_latency = Text("P95 latency:\n3000ms", font_size=24, color=RED, weight=BOLD)
        copa_latency.next_to(copa_box, DOWN, buff=0.5)
        
        # Big WHY stamp
        why_stamp = Text("WHY?", font_size=56, color=RED, weight=BOLD)
        why_stamp.shift(DOWN * 2.5)
        why_box = SurroundingRectangle(
            why_stamp, color=RED, stroke_width=5, buff=0.3
        )
        
        caption = add_caption(self, "Copa performs poorly on video traffic")
        
        # Animate
        self.play(Write(title), run_time=1)
        self.wait(DEFAULT_WAIT_SHORT)
        
        self.play(Create(gcc_box), Write(gcc_label), run_time=1.5)
        self.play(Write(gcc_latency), run_time=1)
        self.wait(DEFAULT_WAIT_SHORT)
        
        self.play(Create(swap_arrow), run_time=1)
        self.wait(DEFAULT_WAIT_SHORT)
        
        self.play(Create(copa_box), Write(copa_label), run_time=1.5)
        self.play(Write(copa_latency), run_time=1)
        self.wait(1)
        
        self.play(Create(why_box), Write(why_stamp), run_time=1.5)
        self.wait(1)
        
        self.play(Write(caption), run_time=1)
        self.wait(1)
        
        # Total: ~55 seconds


# ============================================================================
# SCENE 4: BackloggedAssumptionGap (rewrite from WhyCCAsWinOnBackloggedFlows)
# ============================================================================

# ============================================================================
# SCENE 5: EncoderUnreliability
# ============================================================================

class EncoderUnreliability(Scene):
    """VO: The encoder target bitrate vs achieved bitrate lags. This causes problems."""
    
    def construct(self):
        self.camera.background_color = BACKGROUND_COLOR
        
        title = add_title(self, "Encoder Unreliability")
        
        # Plot showing target vs achieved mismatch
        axes = Axes(
            x_range=[0, 8, 1],
            y_range=[0, 5, 1],
            x_length=8,
            y_length=3,
            axis_config={"color": TEXT_COLOR, "font_size": 18},
            tips=False
        )
        axes.shift(UP * 0.5)
        
        # Target bitrate steps
        target_line = axes.plot(
            lambda x: 3 if x < 2 else (4 if x < 4 else (2 if x < 6 else 3.5)),
            color=YELLOW, x_range=[0, 8], stroke_width=3
        )
        target_label = Text("Target bitrate", font_size=20, color=YELLOW)
        target_label.next_to(axes, UP, buff=0.3)
        
        # Achieved bitrate lags
        achieved_curve = axes.plot(
            lambda x: 2.5 + 0.5 * np.sin(x * 1.5) + 0.3 * np.sin(x * 3),
            color=GCC_COLOR, x_range=[0, 8], stroke_width=2
        )
        achieved_label = Text("Achieved bitrate (lags)", font_size=20, color=GCC_COLOR)
        achieved_label.next_to(target_label, RIGHT, buff=1.5)
        
        # Two callout boxes
        callout1_box = Rectangle(
            width=3.5, height=1.2,
            stroke_color=RED, stroke_width=3,
            fill_opacity=0.1, fill_color=RED
        )
        callout1_box.shift(LEFT * 3.5 + DOWN * 2)
        
        callout1_text = Text(
            "Quality left on table\n(if too conservative)",
            font_size=22, color=TEXT_COLOR
        )
        callout1_text.move_to(callout1_box)
        
        callout2_box = Rectangle(
            width=3.5, height=1.2,
            stroke_color=RED, stroke_width=3,
            fill_opacity=0.1, fill_color=RED
        )
        callout2_box.shift(RIGHT * 3.5 + DOWN * 2)
        
        callout2_text = Text(
            "Latency spike\n(if too aggressive)",
            font_size=22, color=TEXT_COLOR
        )
        callout2_text.move_to(callout2_box)
        
        caption = add_caption(self, "Target vs. achieved bitrate mismatch causes quality/latency problems")
        
        # Animate
        self.play(Write(title), run_time=1)
        self.wait(DEFAULT_WAIT_SHORT)
        
        self.play(Create(axes), run_time=1)
        self.wait(DEFAULT_WAIT_SHORT)
        
        self.play(Create(target_line), Write(target_label), run_time=1.5)
        self.wait(DEFAULT_WAIT_SHORT)
        
        self.play(Create(achieved_curve), Write(achieved_label), run_time=2)
        self.wait(1)
        
        self.play(
            Create(callout1_box),
            Write(callout1_text),
            run_time=1.5
        )
        self.wait(0.5)
        
        self.play(
            Create(callout2_box),
            Write(callout2_text),
            run_time=1.5
        )
        self.wait(1)
        
        self.play(Write(caption), run_time=1)
        self.wait(2)
        
        # Total: ~70-80 seconds


# ============================================================================
# SCENE 4: BackloggedAssumptionGap
# ============================================================================

class BackloggedAssumptionGap(Scene):
    """VO: Most congestion controls assume a backlogged traffic source. Video isn't backlogged."""
    
    def construct(self):
        self.camera.background_color = BACKGROUND_COLOR
        
        title = add_title(self, "The Backlogged Assumption Gap")
        
        # Key line
        key_line = Text(
            "Most congestion controls assume a backlogged traffic source.",
            font_size=32, color=YELLOW, weight=BOLD
        )
        key_line.shift(UP * 3)
        
        # Two lanes (simplified)
        top_lane_label = Text("Backlogged Flow", font_size=SUBTITLE_SIZE, color=GREEN, weight=BOLD)
        top_lane_label.shift(UP * 1.5 + LEFT * 4)
        
        bottom_lane_label = Text("Video Flow", font_size=SUBTITLE_SIZE, color=RED, weight=BOLD)
        bottom_lane_label.shift(UP * 1.5 + RIGHT * 4)
        
        # Top lane: continuous packets
        top_pipe = Rectangle(
            width=6, height=0.6,
            stroke_color=GREEN, stroke_width=2,
            fill_opacity=0.1, fill_color=GREEN
        )
        top_pipe.shift(UP * 0.5 + LEFT * 1)
        
        top_packets = VGroup()
        for i in range(10):
            packet = make_packet(is_video=True, size=0.3)
            packet.move_to(top_pipe.get_left() + RIGHT * (i * 0.62 + 0.2))
            top_packets.add(packet)
        
        # Bottom lane: gaps
        bottom_pipe = Rectangle(
            width=6, height=0.6,
            stroke_color=RED, stroke_width=2,
            fill_opacity=0.1, fill_color=RED
        )
        bottom_pipe.shift(DOWN * 1.5 + RIGHT * 1)
        
        bottom_packets = VGroup()
        positions = [0.2, 0.9, 2.1, 3.4, 4.9, 6.2]  # Gaps
        for pos in positions:
            packet = make_packet(is_video=True, size=0.3)
            packet.move_to(bottom_pipe.get_left() + RIGHT * pos)
            bottom_packets.add(packet)
        
        # Simple feedback loop visualization
        top_loop = DashedLine(
            start=top_pipe.get_right() + DOWN * 0.4,
            end=top_pipe.get_left() + DOWN * 0.4,
            color=GREEN, dash_length=0.2
        )
        top_check = Text("✓", font_size=32, color=GREEN)
        top_check.next_to(top_loop, DOWN, buff=0.2)
        
        bottom_loop = DashedLine(
            start=bottom_pipe.get_right() + UP * 0.4,
            end=bottom_pipe.get_left() + UP * 0.4,
            color=RED, dash_length=0.2, stroke_opacity=0.5
        )
        bottom_x = Text("✗", font_size=32, color=RED)
        bottom_x.next_to(bottom_loop, UP, buff=0.2)
        
        # End message
        end_message = Text(
            "Video isn't backlogged → feedback loop breaks",
            font_size=28, color=YELLOW, weight=BOLD
        )
        end_message.shift(DOWN * 3)
        
        caption = add_caption(self, "Video flows have gaps; CCAs need continuous feedback")
        
        # Animate
        self.play(Write(title), run_time=1)
        self.wait(DEFAULT_WAIT_SHORT)
        self.play(Write(key_line), run_time=2)
        self.wait(1)
        
        self.play(
            Write(top_lane_label),
            Write(bottom_lane_label),
            run_time=1.5
        )
        self.wait(DEFAULT_WAIT_SHORT)
        
        self.play(Create(top_pipe), Create(bottom_pipe), run_time=1)
        self.wait(DEFAULT_WAIT_SHORT)
        
        self.play(
            LaggedStart(*[FadeIn(p) for p in top_packets], lag_ratio=0.1),
            run_time=2
        )
        self.wait(DEFAULT_WAIT_SHORT)
        
        self.play(
            LaggedStart(*[FadeIn(p) for p in bottom_packets], lag_ratio=0.15),
            run_time=2
        )
        self.wait(1)
        
        self.play(Create(top_loop), Write(top_check), run_time=1.5)
        self.wait(0.5)
        self.play(Create(bottom_loop), Write(bottom_x), run_time=1.5)
        self.wait(1)
        
        self.play(Write(end_message), run_time=1.5)
        self.wait(1)
        self.play(Write(caption), run_time=1)
        self.wait(2)
        
        # Total: ~75 seconds


# ============================================================================
# SCENE 6: OptionsBridge
# ============================================================================

class OptionsBridge(Scene):
    """VO: What are our options? Three approaches: modify codec, new video CC, or leverage backlogged CCs."""
    
    def construct(self):
        self.camera.background_color = BACKGROUND_COLOR
        
        title = add_title(self, "Options")
        
        # Three cards
        card1_box = Rectangle(
            width=3.5, height=2.5,
            stroke_color=COPA_COLOR, stroke_width=3,
            fill_opacity=0.1, fill_color=COPA_COLOR
        )
        card1_box.shift(LEFT * 5)
        
        card1_title = Text("1. Modify codec", font_size=28, color=COPA_COLOR, weight=BOLD)
        card1_title.next_to(card1_box, UP, buff=0.2)
        
        card1_icon = make_wrench_icon()
        card1_icon.move_to(card1_box.get_center() + UP * 0.5)
        
        card1_label = Text("Salsify", font_size=22, color=TEXT_COLOR)
        card1_label.move_to(card1_box.get_center())
        
        card2_box = Rectangle(
            width=3.5, height=2.5,
            stroke_color=GCC_COLOR, stroke_width=3,
            fill_opacity=0.1, fill_color=GCC_COLOR
        )
        card2_box.shift(ORIGIN)
        
        card2_title = Text("2. New video CC", font_size=28, color=GCC_COLOR, weight=BOLD)
        card2_title.next_to(card2_box, UP, buff=0.2)
        
        card2_label = Text("GCC/PCC", font_size=22, color=TEXT_COLOR)
        card2_label.move_to(card2_box.get_center())
        
        card3_box = Rectangle(
            width=3.5, height=2.5,
            stroke_color=VIDAPTIVE_COLOR, stroke_width=5,
            fill_opacity=0.2, fill_color=VIDAPTIVE_COLOR
        )
        card3_box.shift(RIGHT * 5)
        
        card3_title = Text("3. Leverage backlogged CCs", font_size=26, color=VIDAPTIVE_COLOR, weight=BOLD)
        card3_title.next_to(card3_box, UP, buff=0.2)
        
        card3_icon = make_plug_icon()
        card3_icon.move_to(card3_box.get_center() + UP * 0.5)
        
        card3_label = Text("Our choice", font_size=22, color=TEXT_COLOR, weight=BOLD)
        card3_label.move_to(card3_box.get_center())
        
        # Highlight card 3
        highlight_box = SurroundingRectangle(
            card3_box, color=YELLOW, stroke_width=4, buff=0.2
        )
        
        takeaway = add_takeaway(self, "We choose (3): reuse strong CCAs")
        
        # Animate
        self.play(Write(title), run_time=1)
        self.wait(DEFAULT_WAIT_SHORT)
        
        # Card 1 (10-12s)
        self.play(Create(card1_box), Write(card1_title), run_time=1.5)
        self.play(Create(card1_icon), Write(card1_label), run_time=1.5)
        self.wait(1)
        
        # Card 2 (10-12s)
        self.play(Create(card2_box), Write(card2_title), run_time=1.5)
        self.play(Write(card2_label), run_time=1.5)
        self.wait(1)
        
        # Card 3 (10-12s) - highlighted
        self.play(Create(card3_box), Write(card3_title), run_time=1.5)
        self.play(Create(card3_icon), Write(card3_label), run_time=1.5)
        self.wait(0.5)
        self.play(Create(highlight_box), run_time=1)
        self.wait(1)
        
        self.play(Write(takeaway), run_time=1.5)
        self.wait(1)
        
        # Total: ~35-45 seconds


# ============================================================================
# SCENE 7: VidaptiveMakeFlowBacklogged (rewrite from CoreIdeaMakeVideoBacklogged)
# ============================================================================

class VidaptiveMakeFlowBacklogged(Scene):
    """VO: Make the video flow appear backlogged by decoupling encoding from transmission."""
    
    def construct(self):
        self.camera.background_color = BACKGROUND_COLOR
        
        title = add_title(self, "Vidaptive: Make Flow Backlogged")
        
        # Encoder producing frames
        encoder = Rectangle(
            width=2, height=1.2,
            stroke_color=VIDAPTIVE_COLOR, stroke_width=3
        )
        encoder.shift(LEFT * 5 + UP * 1)
        
        encoder_label = Text("Encoder", font_size=28, color=TEXT_COLOR)
        encoder_label.move_to(encoder)
        
        # Pacer
        pacer = Rectangle(
            width=2, height=1.2,
            stroke_color=YELLOW, stroke_width=3
        )
        pacer.shift(LEFT * 5 + DOWN * 1)
        
        pacer_label = Text("Pacer", font_size=28, color=TEXT_COLOR)
        pacer_label.move_to(pacer)
        
        # Queue in between
        queue = Rectangle(
            width=0.8, height=1.0,
            stroke_color=VIDAPTIVE_COLOR, stroke_width=2,
            fill_opacity=0.3, fill_color=VIDAPTIVE_COLOR
        )
        queue.shift(LEFT * 5)
        
        # Arrow from encoder to queue
        encoder_to_queue = Arrow(
            start=encoder.get_bottom(),
            end=queue.get_top(),
            color=VIDAPTIVE_COLOR, buff=0.1
        )
        
        # Arrow from queue to pacer
        queue_to_pacer = Arrow(
            start=queue.get_bottom(),
            end=pacer.get_top(),
            color=VIDAPTIVE_COLOR, buff=0.1
        )
        
        # CC-Rate control
        cc_rate_label = Text("CC-Rate", font_size=24, color=YELLOW, weight=BOLD)
        cc_rate_label.shift(LEFT * 1.5 + UP * 2)
        
        cc_rate_arrow = Arrow(
            start=cc_rate_label.get_bottom(),
            end=pacer.get_top() + RIGHT * 0.5,
            color=YELLOW, buff=0.2
        )
        
        # Dummy generator
        dummy_gen = Text("Dummy Generator", font_size=24, color=GRAY)
        dummy_gen.shift(LEFT * 1.5 + DOWN * 2)
        
        dummy_arrow = Arrow(
            start=dummy_gen.get_top(),
            end=pacer.get_bottom() + RIGHT * 0.5,
            color=GRAY, buff=0.2
        )
        
        # Animated packets
        packet_area = Rectangle(
            width=6, height=2,
            stroke_color=TEXT_COLOR, stroke_width=1,
            stroke_opacity=0.3
        )
        packet_area.shift(RIGHT * 2)
        
        # Scenario 1: Encoder output > CC-Rate
        scenario1_label = Text("Encoder output > CC-Rate: queue builds", font_size=24, color=RED)
        scenario1_label.shift(RIGHT * 2 + UP * 3)
        
        queue_packets = VGroup()
        for i in range(5):
            packet = make_packet(is_video=True, size=0.3)
            packet.move_to(queue.get_left() + RIGHT * (i * 0.15 + 0.2) + UP * (i * 0.2 - 0.4))
            queue_packets.add(packet)
        
        # Scenario 2: Encoder output < CC-Rate
        scenario2_label = Text("Encoder output < CC-Rate: insert dummy packets", font_size=24, color=GREEN)
        scenario2_label.shift(RIGHT * 2 + DOWN * 3)
        
        mixed_packets = VGroup()
        positions = [0, 1, 2.5, 3, 4.5, 5]
        for i, pos in enumerate(positions):
            is_vid = (i % 2 == 0)
            packet = make_packet(is_video=is_vid, size=0.3)
            packet.move_to(packet_area.get_left() + RIGHT * pos)
            mixed_packets.add(packet)
        
        # Legend: Video vs Dummy
        legend_box = Rectangle(
            width=3, height=1,
            stroke_color=TEXT_COLOR, stroke_width=1,
            fill_opacity=0.1, fill_color=TEXT_COLOR
        )
        legend_box.shift(RIGHT * 3 + UP * 2)
        
        video_legend = VGroup()
        video_packet_leg = make_packet(is_video=True, size=0.2)
        video_packet_leg.shift(RIGHT * 2.5 + UP * 2.3 + LEFT * 1)
        video_text_leg = Text("Video", font_size=18, color=TEXT_COLOR)
        video_text_leg.next_to(video_packet_leg, RIGHT, buff=0.2)
        video_legend.add(video_packet_leg, video_text_leg)
        
        dummy_legend = VGroup()
        dummy_packet_leg = make_packet(is_video=False, size=0.2)
        dummy_packet_leg.shift(RIGHT * 2.5 + UP * 1.8 + LEFT * 1)
        dummy_text_leg = Text("Dummy", font_size=18, color=TEXT_COLOR)
        dummy_text_leg.next_to(dummy_packet_leg, RIGHT, buff=0.2)
        dummy_legend.add(dummy_packet_leg, dummy_text_leg)
        
        caption = add_caption(self, "Network sees a backlogged sender")
        takeaway = add_takeaway(self, "Network sees a backlogged sender")
        
        # Animate
        self.play(Write(title), run_time=1)
        self.wait(DEFAULT_WAIT_SHORT)
        self.play(
            Create(encoder), Write(encoder_label),
            Create(pacer), Write(pacer_label),
            Create(queue),
            run_time=2
        )
        self.wait(0.5)
        self.play(
            Create(encoder_to_queue),
            Create(queue_to_pacer),
            run_time=1.5
        )
        self.wait(0.5)
        self.play(
            Write(cc_rate_label),
            Create(cc_rate_arrow),
            run_time=1.5
        )
        self.wait(0.5)
        self.play(
            Write(dummy_gen),
            Create(dummy_arrow),
            run_time=1.5
        )
        self.wait(1)
        
        # Show scenario 1
        self.play(Write(scenario1_label), run_time=1)
        self.play(
            LaggedStart(*[FadeIn(p, shift=UP) for p in queue_packets], lag_ratio=0.2),
            run_time=2
        )
        self.wait(1)
        self.play(FadeOut(scenario1_label, queue_packets), run_time=1)
        
        # Show scenario 2
        self.play(Write(scenario2_label), run_time=1)
        self.play(
            Create(packet_area),
            LaggedStart(*[FadeIn(p) for p in mixed_packets], lag_ratio=0.15),
            run_time=2
        )
        self.wait(1)
        
        # Show legend
        self.play(Create(legend_box), run_time=1)
        self.play(Write(video_legend), Write(dummy_legend), run_time=1.5)
        self.wait(1)
        
        self.play(Write(caption), run_time=1)
        self.wait(1)
        self.play(Write(takeaway), run_time=1.5)
        self.wait(2)
        
        # Total: ~80 seconds


# ============================================================================
# SCENE 8: NextChallengeMatchingToCCRate
# ============================================================================

class NextChallengeMatchingToCCRate(Scene):
    """VO: The next challenge: matching encoder target to CC-Rate. Too low = quality loss. Too high = tail latency."""
    
    def construct(self):
        self.camera.background_color = BACKGROUND_COLOR
        
        title = add_title(self, "Next Challenge: Matching to CC-Rate")
        
        # CC-Rate as horizontal bar
        cc_rate_bar = Rectangle(
            width=6, height=0.8,
            stroke_color=GREEN, stroke_width=3,
            fill_opacity=0.3, fill_color=GREEN
        )
        cc_rate_bar.shift(UP * 2)
        
        cc_rate_label = Text("CC-Rate", font_size=28, color=GREEN, weight=BOLD)
        cc_rate_label.next_to(cc_rate_bar, UP, buff=0.3)
        
        # Encoder target as α×CC-Rate slider
        alpha_label = Text("α × CC-Rate", font_size=24, color=YELLOW, weight=BOLD)
        alpha_label.shift(UP * 0.5)
        
        alpha_slider = Line(
            LEFT * 3, RIGHT * 3,
            color=YELLOW, stroke_width=3
        )
        alpha_slider.shift(UP * 0.2)
        
        alpha_dot = Dot(alpha_slider.get_center(), color=YELLOW, radius=0.15)
        alpha_value = Text("α = 0.8", font_size=20, color=YELLOW)
        alpha_value.next_to(alpha_dot, DOWN, buff=0.2)
        
        # Two extremes
        extreme_low_box = Rectangle(
            width=3, height=1.5,
            stroke_color=RED, stroke_width=3,
            fill_opacity=0.1, fill_color=RED
        )
        extreme_low_box.shift(LEFT * 3.5 + DOWN * 1.5)
        
        extreme_low_label = Text("α too low", font_size=22, color=RED, weight=BOLD)
        extreme_low_label.next_to(extreme_low_box, UP, buff=0.2)
        
        extreme_low_text = Text("Quality loss", font_size=20, color=TEXT_COLOR)
        extreme_low_text.move_to(extreme_low_box)
        
        extreme_high_box = Rectangle(
            width=3, height=1.5,
            stroke_color=RED, stroke_width=3,
            fill_opacity=0.1, fill_color=RED
        )
        extreme_high_box.shift(RIGHT * 3.5 + DOWN * 1.5)
        
        extreme_high_label = Text("α too high", font_size=22, color=RED, weight=BOLD)
        extreme_high_label.next_to(extreme_high_box, UP, buff=0.2)
        
        extreme_high_text = Text("Tail latency", font_size=20, color=TEXT_COLOR)
        extreme_high_text.move_to(extreme_high_box)
        
        takeaway = add_takeaway(self, "Need headroom")
        caption = add_caption(self, "α controls the quality-latency tradeoff")
        
        # Animate
        self.play(Write(title), run_time=1)
        self.wait(DEFAULT_WAIT_SHORT)
        
        self.play(Create(cc_rate_bar), Write(cc_rate_label), run_time=1.5)
        self.wait(DEFAULT_WAIT_SHORT)
        
        self.play(Write(alpha_label), Create(alpha_slider), run_time=1.5)
        self.play(Create(alpha_dot), Write(alpha_value), run_time=1)
        self.wait(1)
        
        self.play(
            Create(extreme_low_box),
            Write(extreme_low_label),
            Write(extreme_low_text),
            run_time=1.5
        )
        self.wait(0.5)
        
        self.play(
            Create(extreme_high_box),
            Write(extreme_high_label),
            Write(extreme_high_text),
            run_time=1.5
        )
        self.wait(1)
        
        self.play(Write(takeaway), run_time=1.5)
        self.wait(1)
        self.play(Write(caption), run_time=1)
        self.wait(2)
        
        # Total: ~70 seconds


# ============================================================================
# SCENE 5: VidaptiveArchitecture (keep for reference, can be removed later)
# ============================================================================

class VidaptiveArchitecture(Scene):
    """VO: Here's Vidaptive's architecture. It uses a pacer, dummy packets, and an online bitrate controller."""
    
    def construct(self):
        title = make_title("Vidaptive Architecture")
        
        # Block diagram components
        encoder = Rectangle(
            width=2.2, height=1.0,
            stroke_color=VIDAPTIVE_COLOR, stroke_width=3,
            fill_opacity=0.2, fill_color=VIDAPTIVE_COLOR
        )
        encoder.shift(LEFT * 5 + UP * 2)
        
        encoder_label = Text("Video\nEncoder", font_size=24, color=TEXT_COLOR)
        encoder_label.move_to(encoder)
        
        media_queue = Rectangle(
            width=2.2, height=1.0,
            stroke_color=VIDAPTIVE_COLOR, stroke_width=2,
            fill_opacity=0.1, fill_color=VIDAPTIVE_COLOR
        )
        media_queue.shift(LEFT * 5 + UP * 0.5)
        
        queue_label = Text("Media\nQueue", font_size=24, color=TEXT_COLOR)
        queue_label.move_to(media_queue)
        
        pacer = Rectangle(
            width=2.2, height=1.0,
            stroke_color=YELLOW, stroke_width=3,
            fill_opacity=0.2, fill_color=YELLOW
        )
        pacer.shift(LEFT * 5 + DOWN * 0.5)
        
        pacer_label = Text("Pacer", font_size=24, color=TEXT_COLOR)
        pacer_label.move_to(pacer)
        
        network = Rectangle(
            width=2.2, height=1.0,
            stroke_color=TEXT_COLOR, stroke_width=2
        )
        network.shift(LEFT * 5 + DOWN * 2)
        
        network_label = Text("Network", font_size=24, color=TEXT_COLOR)
        network_label.move_to(network)
        
        # Control blocks
        cc = Rectangle(
            width=2.2, height=1.0,
            stroke_color=GREEN, stroke_width=2,
            fill_opacity=0.1, fill_color=GREEN
        )
        cc.shift(RIGHT * 2 + UP * 1)
        
        cc_label = Text("Congestion\nController", font_size=20, color=TEXT_COLOR)
        cc_label.move_to(cc)
        
        dummy_gen = Rectangle(
            width=2.2, height=1.0,
            stroke_color=GRAY, stroke_width=2,
            fill_opacity=0.1, fill_color=GRAY
        )
        dummy_gen.shift(RIGHT * 2 + DOWN * 1)
        
        dummy_label = Text("Dummy\nGenerator", font_size=20, color=TEXT_COLOR)
        dummy_label.move_to(dummy_gen)
        
        rate_ctrl = Rectangle(
            width=2.2, height=1.2,
            stroke_color=ORANGE, stroke_width=3,
            fill_opacity=0.2, fill_color=ORANGE
        )
        rate_ctrl.shift(RIGHT * 4.5 + UP * 0.5)
        
        rate_label = Text("Encoder Rate\nController", font_size=20, color=TEXT_COLOR)
        rate_label.move_to(rate_ctrl)
        
        # Arrows
        arrows = VGroup()
        
        # Main flow
        arrows.add(Arrow(encoder.get_bottom(), media_queue.get_top(), color=VIDAPTIVE_COLOR, buff=0.1))
        arrows.add(Arrow(media_queue.get_bottom(), pacer.get_top(), color=VIDAPTIVE_COLOR, buff=0.1))
        arrows.add(Arrow(pacer.get_bottom(), network.get_top(), color=VIDAPTIVE_COLOR, buff=0.1))
        
        # Control arrows
        cc_to_pacer = Arrow(cc.get_left(), pacer.get_right(), color=GREEN, buff=0.1)
        cc_to_pacer_label = Text("CC-Rate/\ncwnd", font_size=18, color=GREEN)
        cc_to_pacer_label.next_to(cc_to_pacer, UP, buff=0.1)
        arrows.add(cc_to_pacer)
        
        dummy_to_pacer = Arrow(dummy_gen.get_left(), pacer.get_right(), color=GRAY, buff=0.1)
        arrows.add(dummy_to_pacer)
        
        # Feedback arrows
        queue_to_rate = CurvedArrow(
            media_queue.get_right(),
            rate_ctrl.get_left(),
            color=ORANGE, stroke_width=2
        )
        queue_to_rate_label = Text("queue/\nservice time", font_size=16, color=ORANGE)
        queue_to_rate_label.next_to(queue_to_rate, DOWN, buff=0.1)
        arrows.add(queue_to_rate)
        
        rate_to_encoder = CurvedArrow(
            rate_ctrl.get_bottom(),
            encoder.get_top(),
            color=ORANGE, stroke_width=2
        )
        rate_to_encoder_label = Text("target\nbitrate", font_size=16, color=ORANGE)
        rate_to_encoder_label.next_to(rate_to_encoder, RIGHT, buff=0.1)
        arrows.add(rate_to_encoder)
        
        # Callout box
        callout_box = SurroundingRectangle(
            VGroup(title, encoder, network, rate_ctrl),
            color=YELLOW, stroke_width=3, buff=0.5
        )
        callout_box.shift(DOWN * 0.5)
        
        callout_title = Text("What Vidaptive Changes:", font_size=28, color=YELLOW, weight=BOLD)
        callout_title.shift(DOWN * 3.5 + LEFT * 4)
        
        callout_items = make_bullet_list([
            "1. Always-on pacing at CC-Rate",
            "2. Dummy packets to keep feedback loop tight",
            "3. Online bitrate controller with latency bound"
        ], font_size=22, buff=0.3)
        callout_items.shift(DOWN * 4.2 + LEFT * 2)
        
        caption = make_caption("Vidaptive decouples encoding from congestion control")
        
        # Animate
        self.play(Write(title), run_time=1)
        self.wait(0.5)
        
        # Build diagram
        components = [encoder, encoder_label, media_queue, queue_label,
                     pacer, pacer_label, network, network_label,
                     cc, cc_label, dummy_gen, dummy_label,
                     rate_ctrl, rate_label]
        self.play(LaggedStart(*[Create(c) for c in components], lag_ratio=0.1), run_time=3)
        self.wait(0.5)
        
        # Show arrows
        self.play(LaggedStart(*[Create(a) for a in arrows], lag_ratio=0.1), run_time=2.5)
        self.play(
            Write(cc_to_pacer_label),
            Write(queue_to_rate_label),
            Write(rate_to_encoder_label),
            run_time=1.5
        )
        self.wait(1)
        
        # Highlight control loops
        self.play(
            arrows[3].animate.set_stroke(width=5, color=YELLOW),  # CC to pacer
            run_time=1
        )
        self.wait(0.5)
        self.play(
            arrows[3].animate.set_stroke(width=2, color=GREEN),
            arrows[5].animate.set_stroke(width=5, color=YELLOW),  # Feedback loop
            arrows[6].animate.set_stroke(width=5, color=YELLOW),
            run_time=1.5
        )
        self.wait(1)
        self.play(
            arrows[5].animate.set_stroke(width=2, color=ORANGE),
            arrows[6].animate.set_stroke(width=2, color=ORANGE),
            run_time=0.5
        )
        self.wait(1)
        
        # Show callout
        self.play(Create(callout_box), Write(callout_title), run_time=1.5)
        self.play(Write(callout_items), run_time=2)
        self.wait(1)
        self.play(Write(caption), run_time=1)
        self.wait(2)
        
        # Total: ~110 seconds


# ============================================================================
# SCENE 6: LatencyChallengeFrameTransmissionTime
# ============================================================================

class LatencyChallengeFrameTransmissionTime(Scene):
    """VO: But there's a challenge. When network capacity drops, frame transmission time stretches."""
    
    def construct(self):
        title = make_title("Latency Challenge: Frame Transmission Time")
        
        # Capacity curve
        axes = Axes(
            x_range=[0, 10, 1],
            y_range=[0, 6, 1],
            x_length=8,
            y_length=4,
            axis_config={"color": TEXT_COLOR, "font_size": 18},
            tips=False
        )
        axes.shift(UP * 1)
        
        # High capacity scenario
        high_capacity = axes.plot(
            lambda x: 4.5 if x < 8 else 2.0,
            color=GREEN, x_range=[0, 10], stroke_width=3
        )
        
        # Frame size as area
        frame_area_high = axes.get_area(
            high_capacity, x_range=[0, 4], color=VIDAPTIVE_COLOR, opacity=0.5
        )
        
        # Low capacity scenario
        low_capacity = axes.plot(
            lambda x: 2.0 if x < 8 else 2.0,
            color=RED, x_range=[0, 10], stroke_width=3
        )
        
        frame_area_low = axes.get_area(
            low_capacity, x_range=[0, 9], color=VIDAPTIVE_COLOR, opacity=0.5
        )
        
        capacity_label = Text("Capacity", font_size=24, color=TEXT_COLOR)
        capacity_label.next_to(axes, LEFT, buff=0.3)
        
        time_label = Text("Time", font_size=24, color=TEXT_COLOR)
        time_label.next_to(axes, DOWN, buff=0.3)
        
        # Equation text
        equation = Text(
            "Transmission time grows when capacity drops",
            font_size=32, color=YELLOW, weight=BOLD
        )
        equation.shift(DOWN * 2)
        
        # Visual explanation
        before_label = Text("Before: high capacity", font_size=24, color=GREEN)
        before_label.shift(LEFT * 3.5 + DOWN * 3.5)
        
        after_label = Text("After: capacity drop", font_size=24, color=RED)
        after_label.shift(RIGHT * 3.5 + DOWN * 3.5)
        
        caption = make_caption("We need headroom to bound tail latency")
        key_phrase = Text(
            "We need headroom to bound tail latency",
            font_size=32, color=YELLOW, weight=BOLD
        )
        key_phrase.shift(DOWN * 3.8)
        
        # Animate
        self.play(Write(title), run_time=1)
        self.wait(0.5)
        self.play(Create(axes), Write(capacity_label), Write(time_label), run_time=1.5)
        self.wait(0.5)
        
        # Show high capacity
        self.play(Create(high_capacity), run_time=1.5)
        self.play(Create(frame_area_high), Write(before_label), run_time=2)
        self.wait(1)
        
        # Transition to low capacity
        self.play(
            Transform(high_capacity, low_capacity),
            Transform(frame_area_high, frame_area_low),
            Write(after_label),
            run_time=2.5
        )
        self.wait(1)
        self.play(Write(equation), run_time=2)
        self.wait(1)
        self.play(Write(caption), run_time=1)
        self.wait(0.5)
        self.play(Write(key_phrase), run_time=1.5)
        self.wait(2)
        
        # Total: ~80 seconds


# ============================================================================
# SCENE 7: AlphaKnobAndServiceTime
# ============================================================================

class AlphaKnobAndServiceTime(Scene):
    """VO: Vidaptive introduces α, a knob that controls the encoder target bitrate relative to congestion control rate."""
    
    def construct(self):
        title = make_title("The α Knob and Service Time")
        
        # Introduce α
        alpha_formula = MathTex(
            r"\text{Encoder target} = \alpha \times \text{CC-Rate}",
            font_size=48, color=TEXT_COLOR
        )
        alpha_formula.shift(UP * 2.5)
        
        # Service time distribution
        axes = Axes(
            x_range=[0, 10, 1],
            y_range=[0, 5, 1],
            x_length=6,
            y_length=3,
            axis_config={"color": TEXT_COLOR, "font_size": 18},
            tips=False
        )
        axes.shift(DOWN * 0.5)
        
        # Distribution of service times
        x_vals = np.linspace(0, 10, 100)
        # Normal-like distribution
        mu, sigma = 5, 1.5
        dist_curve = axes.plot(
            lambda x: 4 * np.exp(-0.5 * ((x - mu) / sigma) ** 2),
            color=VIDAPTIVE_COLOR, x_range=[0, 10], stroke_width=3
        )
        
        # P90 line
        p90_y = 4 * np.exp(-0.5 * ((7 - mu) / sigma) ** 2)
        p90_line = DashedLine(
            start=axes.c2p(7, 0),
            end=axes.c2p(7, p90_y),
            color=YELLOW, stroke_width=2
        )
        p90_label = Text("P90", font_size=20, color=YELLOW)
        p90_label.next_to(p90_line, UP, buff=0.1)
        
        # Alpha visualization
        alpha_knob = Circle(radius=0.8, color=ORANGE, stroke_width=4)
        alpha_knob.shift(RIGHT * 4 + UP * 1)
        
        alpha_value = Text("α = 0.8", font_size=32, color=ORANGE, weight=BOLD)
        alpha_value.move_to(alpha_knob)
        
        # Quality vs latency tradeoff
        tradeoff_box = Rectangle(
            width=5, height=2.5,
            stroke_color=TEXT_COLOR, stroke_width=2,
            fill_opacity=0.1, fill_color=TEXT_COLOR
        )
        tradeoff_box.shift(DOWN * 2.5)
        
        tradeoff_title = Text("Quality vs Latency Tradeoff", font_size=24, color=TEXT_COLOR, weight=BOLD)
        tradeoff_title.next_to(tradeoff_box, UP, buff=0.2)
        
        alpha_high = Text("α high → larger frames, higher quality, more tail risk", font_size=20, color=RED)
        alpha_high.shift(DOWN * 2.5 + UP * 0.6)
        
        alpha_low = Text("α low → safer latency, lower quality", font_size=20, color=GREEN)
        alpha_low.shift(DOWN * 2.5 + DOWN * 0.6)
        
        # Animate α decreasing
        alpha_decreasing_label = Text("α decreases when variability increases", font_size=24, color=YELLOW)
        alpha_decreasing_label.shift(DOWN * 3.8)
        
        caption = make_caption("α controls the quality-latency tradeoff")
        
        # Animate
        self.play(Write(title), run_time=1)
        self.wait(0.5)
        self.play(Write(alpha_formula), run_time=2)
        self.wait(1)
        
        self.play(Create(axes), run_time=1)
        self.play(Create(dist_curve), run_time=2)
        self.wait(0.5)
        self.play(Create(p90_line), Write(p90_label), run_time=1.5)
        self.wait(1)
        
        self.play(Create(alpha_knob), Write(alpha_value), run_time=1.5)
        self.wait(1)
        
        self.play(
            Create(tradeoff_box),
            Write(tradeoff_title),
            Write(alpha_high),
            Write(alpha_low),
            run_time=2.5
        )
        self.wait(1)
        
        # Show α decreasing
        alpha_value_new = Text("α = 0.5", font_size=32, color=ORANGE, weight=BOLD)
        alpha_value_new.move_to(alpha_knob)
        self.play(Transform(alpha_value, alpha_value_new), run_time=1.5)
        self.wait(0.5)
        self.play(Write(alpha_decreasing_label), run_time=1.5)
        self.wait(1)
        self.play(Write(caption), run_time=1)
        self.wait(2)
        
        # Total: ~120 seconds


# ============================================================================
# SCENE 8: OnlineAlphaEstimatorCounterfactual
# ============================================================================

class OnlineAlphaEstimatorCounterfactual(Scene):
    """VO: Vidaptive estimates α online using a counterfactual approach based on service times."""
    
    def construct(self):
        title = make_title("Online α Estimator: Counterfactual Approach")
        
        # Service time samples
        samples_label = Text("Service Time Samples:", font_size=28, color=TEXT_COLOR, weight=BOLD)
        samples_label.shift(UP * 3 + LEFT * 4)
        
        samples = VGroup()
        sample_values = [2.1, 3.5, 2.8, 4.2, 3.1, 2.9, 3.8]
        for i, val in enumerate(sample_values):
            sample = Text(f"d_{i+1} = {val}ms", font_size=20, color=TEXT_COLOR)
            sample.shift(UP * 2.5 + LEFT * 4 + RIGHT * (i % 4) * 1.8 + DOWN * (i // 4) * 0.6)
            samples.add(sample)
        
        # Normalized values
        normalized_label = Text("Normalized:", font_size=24, color=YELLOW)
        normalized_label.shift(UP * 1.5 + LEFT * 4)
        
        # Percentile target
        percentile_label = Text("Target percentile P = 33ms", font_size=28, color=GREEN, weight=BOLD)
        percentile_label.shift(LEFT * 2)
        
        # Formula
        formula = MathTex(
            r"\alpha = \frac{P}{\text{percentile}(\text{normalized } d)}",
            font_size=40, color=TEXT_COLOR
        )
        formula.shift(DOWN * 0.5)
        
        # Visual step-by-step
        step1 = Text("1. Collect service times", font_size=24, color=VIDAPTIVE_COLOR)
        step1.shift(DOWN * 1.8 + LEFT * 4)
        
        step2 = Text("2. Normalize by current α", font_size=24, color=VIDAPTIVE_COLOR)
        step2.shift(DOWN * 2.3 + LEFT * 4)
        
        step3 = Text("3. Compute percentile", font_size=24, color=VIDAPTIVE_COLOR)
        step3.shift(DOWN * 2.8 + LEFT * 4)
        
        step4 = Text("4. Set α to hit target", font_size=24, color=VIDAPTIVE_COLOR)
        step4.shift(DOWN * 3.3 + LEFT * 4)
        
        # Animated computation
        computation_box = Rectangle(
            width=4, height=2,
            stroke_color=YELLOW, stroke_width=2,
            fill_opacity=0.1, fill_color=YELLOW
        )
        computation_box.shift(RIGHT * 3 + DOWN * 0.5)
        
        comp_label = Text("α = 0.75", font_size=36, color=YELLOW, weight=BOLD)
        comp_label.move_to(computation_box)
        
        caption = make_caption("Choose α to hit a target service-time percentile")
        key_phrase = Text(
            "Choose α to hit a target service-time percentile",
            font_size=28, color=YELLOW, weight=BOLD
        )
        key_phrase.shift(DOWN * 3.8)
        
        # Animate
        self.play(Write(title), run_time=1)
        self.wait(0.5)
        self.play(Write(samples_label), run_time=1)
        self.play(LaggedStart(*[Write(s) for s in samples], lag_ratio=0.1), run_time=2)
        self.wait(0.5)
        self.play(Write(normalized_label), run_time=1)
        self.wait(0.5)
        self.play(Write(percentile_label), run_time=1.5)
        self.wait(1)
        self.play(Write(formula), run_time=2)
        self.wait(1)
        
        # Steps
        self.play(Write(step1), run_time=1)
        self.wait(0.3)
        self.play(Write(step2), run_time=1)
        self.wait(0.3)
        self.play(Write(step3), run_time=1)
        self.wait(0.3)
        self.play(Write(step4), run_time=1)
        self.wait(0.5)
        
        # Computation
        self.play(Create(computation_box), run_time=1)
        self.play(Write(comp_label), run_time=1.5)
        self.wait(1)
        self.play(Write(caption), run_time=1)
        self.wait(0.5)
        self.play(Write(key_phrase), run_time=1.5)
        self.wait(2)
        
        # Total: ~130 seconds


# ============================================================================
# SCENE 9: LatencySafeguardPauseEncoding
# ============================================================================

class LatencySafeguardPauseEncoding(Scene):
    """VO: To prevent queue buildup, Vidaptive pauses encoding when the oldest packet waits too long."""
    
    def construct(self):
        title = make_title("Latency Safeguard: Pause Encoding")
        
        # Pacer queue
        queue_box = Rectangle(
            width=1.5, height=2.5,
            stroke_color=VIDAPTIVE_COLOR, stroke_width=3,
            fill_opacity=0.2, fill_color=VIDAPTIVE_COLOR
        )
        queue_box.shift(LEFT * 4)
        
        queue_label = Text("Pacer\nQueue", font_size=28, color=TEXT_COLOR)
        queue_label.next_to(queue_box, UP, buff=0.3)
        
        # Packets in queue
        queue_packets = VGroup()
        for i in range(8):
            packet = make_packet(is_video=True, size=0.25)
            packet.move_to(queue_box.get_top() + DOWN * (i * 0.28 + 0.15))
            queue_packets.add(packet)
        
        # Oldest packet highlighted
        oldest_packet = queue_packets[-1].copy()
        oldest_packet.set_stroke(color=RED, width=4)
        
        # Timer/threshold
        tau_label = Text("τ (threshold)", font_size=24, color=RED, weight=BOLD)
        tau_label.shift(LEFT * 4 + DOWN * 3)
        
        timer = Text("Wait time: 45ms > τ", font_size=24, color=RED)
        timer.shift(LEFT * 4 + DOWN * 3.5)
        
        # Encoder
        encoder_box = Rectangle(
            width=2.5, height=1.5,
            stroke_color=YELLOW, stroke_width=3,
            fill_opacity=0.3, fill_color=YELLOW
        )
        encoder_box.shift(RIGHT * 3 + UP * 1)
        
        encoder_label = Text("Encoder", font_size=32, color=TEXT_COLOR, weight=BOLD)
        encoder_label.move_to(encoder_box)
        
        # Pause indicator
        pause_label = Text("PAUSE", font_size=48, color=RED, weight=BOLD)
        pause_label.move_to(encoder_box)
        
        # Drain animation
        drain_label = Text("Queue drains...", font_size=24, color=GREEN)
        drain_label.shift(RIGHT * 3 + DOWN * 1)
        
        # After draining
        empty_queue = queue_box.copy()
        empty_queue.set_fill(opacity=0.1)
        
        resume_label = Text("RESUME", font_size=48, color=GREEN, weight=BOLD)
        resume_label.move_to(encoder_box)
        
        caption = make_caption("Send fresh frames, don't pile up doomed frames")
        key_phrase = Text(
            "Send fresh frames, don't pile up doomed frames",
            font_size=28, color=YELLOW, weight=BOLD
        )
        key_phrase.shift(DOWN * 3.8)
        
        # Animate
        self.play(Write(title), run_time=1)
        self.wait(0.5)
        self.play(
            Create(queue_box),
            Write(queue_label),
            run_time=1.5
        )
        self.wait(0.5)
        self.play(
            LaggedStart(*[FadeIn(p) for p in queue_packets], lag_ratio=0.1),
            run_time=2
        )
        self.wait(0.5)
        self.play(
            Create(oldest_packet),
            Write(tau_label),
            Write(timer),
            run_time=2
        )
        self.wait(1)
        
        # Show encoder
        self.play(
            Create(encoder_box),
            Write(encoder_label),
            run_time=1.5
        )
        self.wait(0.5)
        
        # Pause
        self.play(
            encoder_box.animate.set_fill(opacity=0.1),
            encoder_label.animate.set_opacity(0.3),
            Transform(encoder_label, pause_label),
            run_time=1.5
        )
        self.wait(1)
        
        # Drain
        self.play(Write(drain_label), run_time=1)
        self.play(
            LaggedStart(*[FadeOut(p, shift=RIGHT) for p in reversed(queue_packets)], lag_ratio=0.15),
            run_time=2.5
        )
        self.wait(0.5)
        
        # Resume
        self.play(
            Transform(encoder_label, resume_label),
            encoder_box.animate.set_fill(opacity=0.3),
            run_time=1.5
        )
        self.wait(1)
        self.play(Write(caption), run_time=1)
        self.wait(0.5)
        self.play(Write(key_phrase), run_time=1.5)
        self.wait(2)
        
        # Total: ~70 seconds


# ============================================================================
# SCENE 10: ResultsCDFQualityLatency
# ============================================================================

class ResultsCDFQualityLatency(Scene):
    """VO: Let's look at the results. Vidaptive improves both quality and latency compared to existing approaches."""
    
    def construct(self):
        title = make_title("Results: Quality and Latency")
        
        # Left panel: VMAF CDF
        left_axes = Axes(
            x_range=[0, 100, 10],
            y_range=[0, 1, 0.2],
            x_length=3.5,
            y_length=2.5,
            axis_config={"color": TEXT_COLOR, "font_size": 16},
            tips=False
        )
        left_axes.shift(LEFT * 4 + DOWN * 0.5)
        
        left_title = Text("VMAF CDF", font_size=28, color=TEXT_COLOR, weight=BOLD)
        left_title.next_to(left_axes, UP, buff=0.3)
        
        # VMAF curves (stylized)
        x_vals = np.linspace(0, 100, 100)
        
        # GCC curve (lower)
        gcc_cdf = left_axes.plot(
            lambda x: 0.3 * (1 - np.exp(-x / 30)) + 0.7 * (1 - np.exp(-x / 60)),
            color=GCC_COLOR, x_range=[0, 100], stroke_width=3
        )
        gcc_label = Text("GCC", font_size=20, color=GCC_COLOR)
        gcc_label.next_to(gcc_cdf, RIGHT, buff=0.2)
        
        # Vidaptive curve (higher)
        vidaptive_cdf = left_axes.plot(
            lambda x: 0.5 * (1 - np.exp(-x / 25)) + 0.5 * (1 - np.exp(-x / 50)),
            color=VIDAPTIVE_COLOR, x_range=[0, 100], stroke_width=3
        )
        vidaptive_label = Text("Vidaptive", font_size=20, color=VIDAPTIVE_COLOR)
        vidaptive_label.next_to(vidaptive_cdf, RIGHT, buff=0.2)
        
        # Right panel: Latency CDF
        right_axes = Axes(
            x_range=[0, 100, 10],
            y_range=[0, 1, 0.2],
            x_length=3.5,
            y_length=2.5,
            axis_config={"color": TEXT_COLOR, "font_size": 16},
            tips=False
        )
        right_axes.shift(RIGHT * 4 + DOWN * 0.5)
        
        right_title = Text("Latency CDF", font_size=28, color=TEXT_COLOR, weight=BOLD)
        right_title.next_to(right_axes, UP, buff=0.3)
        
        # Latency curves
        # GCC (higher latency)
        gcc_latency = right_axes.plot(
            lambda x: 1 - np.exp(-x / 40),
            color=GCC_COLOR, x_range=[0, 100], stroke_width=3
        )
        gcc_lat_label = Text("GCC", font_size=20, color=GCC_COLOR)
        gcc_lat_label.next_to(gcc_latency, RIGHT, buff=0.2)
        
        # Copa (backlogged, bad tail)
        copa_latency = right_axes.plot(
            lambda x: 0.7 * (1 - np.exp(-x / 25)) + 0.3 * (1 - np.exp(-x / 80)),
            color=COPA_COLOR, x_range=[0, 100], stroke_width=3
        )
        copa_label = Text("Copa\n(backlogged)", font_size=18, color=COPA_COLOR)
        copa_label.next_to(copa_latency, RIGHT, buff=0.2)
        
        # Vidaptive (better tail)
        vidaptive_latency = right_axes.plot(
            lambda x: 1 - np.exp(-x / 20),
            color=VIDAPTIVE_COLOR, x_range=[0, 100], stroke_width=3
        )
        vidaptive_lat_label = Text("Vidaptive", font_size=20, color=VIDAPTIVE_COLOR)
        vidaptive_lat_label.next_to(vidaptive_latency, RIGHT, buff=0.2)
        
        # Callout box with numbers
        callout = Rectangle(
            width=6, height=1.8,
            stroke_color=YELLOW, stroke_width=3,
            fill_opacity=0.2, fill_color=YELLOW
        )
        callout.shift(DOWN * 3)
        
        callout_title = Text("Key Results:", font_size=24, color=YELLOW, weight=BOLD)
        callout_title.next_to(callout, UP, buff=0.2)
        
        results = VGroup(
            Text("~1.5× bitrate", font_size=22, color=TEXT_COLOR),
            Text("+40% VMAF", font_size=22, color=TEXT_COLOR),
            Text("~57% reduction in P95 frame latency", font_size=22, color=TEXT_COLOR)
        )
        results.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        results.move_to(callout)
        
        caption = make_caption("Vidaptive improves quality and reduces tail latency")
        
        # Animate
        self.play(Write(title), run_time=1)
        self.wait(0.5)
        
        # Left panel
        self.play(Create(left_axes), Write(left_title), run_time=1.5)
        self.wait(0.5)
        self.play(Create(gcc_cdf), Write(gcc_label), run_time=1.5)
        self.wait(0.5)
        self.play(Create(vidaptive_cdf), Write(vidaptive_label), run_time=1.5)
        self.wait(1)
        
        # Right panel
        self.play(Create(right_axes), Write(right_title), run_time=1.5)
        self.wait(0.5)
        self.play(Create(gcc_latency), Write(gcc_lat_label), run_time=1.5)
        self.wait(0.5)
        self.play(Create(copa_latency), Write(copa_label), run_time=1.5)
        self.wait(0.5)
        self.play(Create(vidaptive_latency), Write(vidaptive_lat_label), run_time=1.5)
        self.wait(1)
        
        # Callout
        self.play(Create(callout), Write(callout_title), run_time=1.5)
        self.play(LaggedStart(*[Write(r) for r in results], lag_ratio=0.3), run_time=2)
        self.wait(1)
        self.play(Write(caption), run_time=1)
        self.wait(2)
        
        # Total: ~130 seconds


# ============================================================================
# SCENE 11: TradeoffFrontierP
# ============================================================================

class TradeoffFrontierP(Scene):
    """VO: By adjusting the percentile target P, Vidaptive exposes different operating points on the quality-latency frontier."""
    
    def construct(self):
        title = make_title("Tradeoff Frontier")
        
        # Scatter plot: Avg VMAF vs P95 Latency
        axes = Axes(
            x_range=[0, 100, 10],
            y_range=[50, 90, 5],
            x_length=8,
            y_length=5,
            axis_config={"color": TEXT_COLOR, "font_size": 20},
            tips=False
        )
        
        x_label = Text("P95 Latency (ms)", font_size=24, color=TEXT_COLOR)
        x_label.next_to(axes, DOWN, buff=0.3)
        
        y_label = Text("Avg VMAF", font_size=24, color=TEXT_COLOR)
        y_label.next_to(axes, LEFT, buff=0.3).rotate(PI / 2)
        
        # Vidaptive points at different P values
        vidaptive_points = [
            (25, 75, "P=10"),
            (35, 78, "P=15"),
            (45, 80, "P=20"),
            (60, 82, "P=33"),
        ]
        
        vidaptive_dots = VGroup()
        vidaptive_labels = VGroup()
        for x, y, label in vidaptive_points:
            dot = Dot(axes.c2p(x, y), color=VIDAPTIVE_COLOR, radius=0.08)
            vidaptive_dots.add(dot)
            
            label_text = Text(label, font_size=16, color=VIDAPTIVE_COLOR)
            label_text.next_to(dot, UP, buff=0.15)
            vidaptive_labels.add(label_text)
        
        # GCC baseline
        gcc_dot = Dot(axes.c2p(70, 68), color=GCC_COLOR, radius=0.08)
        gcc_label = Text("GCC", font_size=20, color=GCC_COLOR)
        gcc_label.next_to(gcc_dot, DOWN, buff=0.15)
        
        # Frontier line (connecting Vidaptive points)
        frontier_points = [axes.c2p(x, y) for x, y, _ in vidaptive_points]
        frontier_line = VMobject(color=VIDAPTIVE_COLOR, stroke_width=3)
        frontier_line.set_points_as_corners(frontier_points)
        
        # Arrow indicating better frontier
        frontier_arrow = Arrow(
            start=axes.c2p(85, 77),
            end=axes.c2p(50, 79),
            color=YELLOW, stroke_width=4
        )
        frontier_arrow_label = Text("Better frontier", font_size=24, color=YELLOW, weight=BOLD)
        frontier_arrow_label.next_to(frontier_arrow, UP, buff=0.3)
        
        caption = make_caption("Vidaptive exposes operating points not achievable before")
        key_phrase = Text(
            "Vidaptive exposes operating points not achievable before",
            font_size=28, color=YELLOW, weight=BOLD
        )
        key_phrase.shift(DOWN * 3.5)
        
        # Animate
        self.play(Write(title), run_time=1)
        self.wait(0.5)
        self.play(
            Create(axes),
            Write(x_label),
            Write(y_label),
            run_time=2
        )
        self.wait(0.5)
        
        # Show GCC baseline
        self.play(Create(gcc_dot), Write(gcc_label), run_time=1.5)
        self.wait(0.5)
        
        # Show Vidaptive points
        self.play(
            LaggedStart(*[Create(d) for d in vidaptive_dots], lag_ratio=0.2),
            LaggedStart(*[Write(l) for l in vidaptive_labels], lag_ratio=0.2),
            run_time=2.5
        )
        self.wait(0.5)
        
        # Show frontier
        self.play(Create(frontier_line), run_time=1.5)
        self.wait(0.5)
        self.play(
            Create(frontier_arrow),
            Write(frontier_arrow_label),
            run_time=1.5
        )
        self.wait(1)
        self.play(Write(caption), run_time=1)
        self.wait(0.5)
        self.play(Write(key_phrase), run_time=1.5)
        self.wait(2)
        
        # Total: ~80 seconds


# ============================================================================
# SCENE 12: ComparisonSalsifyDeployability
# ============================================================================

class ComparisonSalsifyDeployability(Scene):
    """VO: How does Vidaptive compare to other approaches like Salsify? The key difference is deployability."""
    
    def construct(self):
        title = make_title("Comparison: Vidaptive vs Salsify")
        
        # Two columns
        salsify_col = VGroup()
        salsify_title = Text("Salsify", font_size=36, color=COPA_COLOR, weight=BOLD)
        salsify_title.shift(LEFT * 4 + UP * 2.5)
        
        salsify_items = make_bullet_list([
            "Needs codec modifications",
            "Drops frames for latency",
            "Higher tail latency"
        ], font_size=28, buff=0.4)
        salsify_items.shift(LEFT * 4 + UP * 0.5)
        
        # Icons for Salsify
        wrench_icon = Text("🔧", font_size=40)
        wrench_icon.next_to(salsify_items[0], RIGHT, buff=0.3)
        
        vidaptive_col = VGroup()
        vidaptive_title = Text("Vidaptive", font_size=36, color=VIDAPTIVE_COLOR, weight=BOLD)
        vidaptive_title.shift(RIGHT * 4 + UP * 2.5)
        
        vidaptive_items = make_bullet_list([
            "No codec changes",
            "Thin adaptation layer",
            "Lower tail latency"
        ], font_size=28, buff=0.4)
        vidaptive_items.shift(RIGHT * 4 + UP * 0.5)
        
        # Icons for Vidaptive
        plug_icon = Text("🔌", font_size=40)
        plug_icon.next_to(vidaptive_items[0], RIGHT, buff=0.3)
        
        # Divider
        divider = DashedLine(
            start=UP * 4,
            end=DOWN * 3,
            color=GRAY, dash_length=0.3
        )
        
        # Takeaway
        takeaway = Text(
            "Practical deployability matters",
            font_size=32, color=YELLOW, weight=BOLD
        )
        takeaway.shift(DOWN * 2.5)
        
        caption = make_caption("Vidaptive is a thin layer requiring no codec changes")
        
        # Animate
        self.play(Write(title), run_time=1)
        self.wait(0.5)
        self.play(
            Write(salsify_title),
            Write(vidaptive_title),
            Create(divider),
            run_time=2
        )
        self.wait(0.5)
        
        self.play(
            LaggedStart(*[Write(item) for item in salsify_items], lag_ratio=0.2),
            run_time=2
        )
        self.play(Write(wrench_icon), run_time=0.5)
        self.wait(0.5)
        
        self.play(
            LaggedStart(*[Write(item) for item in vidaptive_items], lag_ratio=0.2),
            run_time=2
        )
        self.play(Write(plug_icon), run_time=0.5)
        self.wait(1)
        
        self.play(Write(takeaway), run_time=1.5)
        self.wait(1)
        self.play(Write(caption), run_time=1)
        self.wait(2)
        
        # Total: ~70 seconds


# ============================================================================
# SCENE 13: ClosingTakeaways
# ============================================================================

class ClosingTakeaways(Scene):
    """VO: Let's summarize the key takeaways from Vidaptive."""
    
    def construct(self):
        title = make_title("Key Takeaways")
        
        # Three big bullets
        bullet1 = VGroup()
        icon1 = Text("⚡", font_size=48)
        text1 = Text(
            "Tight RTT-scale feedback loop drives responsiveness",
            font_size=32, color=TEXT_COLOR
        )
        text1.next_to(icon1, RIGHT, buff=0.5)
        bullet1.add(icon1, text1)
        bullet1.shift(UP * 1.5)
        
        bullet2 = VGroup()
        icon2 = Text("📦", font_size=48)
        text2 = Text(
            "Dummy packets can be beneficial when synchronized with CC",
            font_size=32, color=TEXT_COLOR
        )
        text2.next_to(icon2, RIGHT, buff=0.5)
        bullet2.add(icon2, text2)
        
        bullet3 = VGroup()
        icon3 = Text("🔧", font_size=48)
        text3 = Text(
            "Thin layer + existing CCAs can beat specialized video controllers",
            font_size=32, color=TEXT_COLOR
        )
        text3.next_to(icon3, RIGHT, buff=0.5)
        bullet3.add(icon3, text3)
        bullet3.shift(DOWN * 1.5)
        
        # End card
        end_card_bg = Rectangle(
            width=12, height=4,
            fill_color=BACKGROUND_COLOR, fill_opacity=0.9,
            stroke_color=VIDAPTIVE_COLOR, stroke_width=4
        )
        end_card_bg.shift(DOWN * 3)
        
        end_title = Text(
            "Tight loops → Smooth streams",
            font_size=42, color=VIDAPTIVE_COLOR, weight=BOLD
        )
        end_title.shift(DOWN * 2.2)
        
        paper_title = Text(
            "Tight Loops, Smooth Streams:",
            font_size=28, color=TEXT_COLOR
        )
        paper_title.shift(DOWN * 2.8)
        
        paper_subtitle = Text(
            "Responsive Congestion Control for Real-Time Video",
            font_size=24, color=TEXT_COLOR
        )
        paper_subtitle.shift(DOWN * 3.4)
        
        authors = Text(
            "Vidaptive",
            font_size=20, color=GRAY
        )
        authors.shift(DOWN * 3.9)
        
        caption = make_caption("Thank you!")
        
        # Animate
        self.play(Write(title), run_time=1)
        self.wait(0.5)
        
        self.play(Write(bullet1), run_time=2)
        self.wait(0.5)
        self.play(Write(bullet2), run_time=2)
        self.wait(0.5)
        self.play(Write(bullet3), run_time=2)
        self.wait(2)
        
        # End card
        self.play(Create(end_card_bg), run_time=1)
        self.play(Write(end_title), run_time=1.5)
        self.wait(0.5)
        self.play(Write(paper_title), run_time=1)
        self.play(Write(paper_subtitle), run_time=1.5)
        self.wait(0.5)
        self.play(Write(authors), run_time=1)
        self.wait(1)
        self.play(Write(caption), run_time=1)
        self.wait(2)
        
        # Total: ~60 seconds


# ============================================================================
# RENDERING INSTRUCTIONS
# ============================================================================
"""
AVAILABLE SCENES (in order):
1. IntroHook
2. RealtimeVideoConstraints
3. StatusQuoGCCProblem
4. WhyCCAsWinOnBackloggedFlows
5. CoreIdeaMakeVideoBacklogged
6. VidaptiveArchitecture
7. LatencyChallengeFrameTransmissionTime
8. AlphaKnobAndServiceTime
9. OnlineAlphaEstimatorCounterfactual
10. LatencySafeguardPauseEncoding
11. ResultsCDFQualityLatency
12. TradeoffFrontierP
13. ComparisonSalsifyDeployability
14. ClosingTakeaways

TO RENDER A SINGLE SCENE:
Replace "SceneName" with one of the scene names above, for example:

    uv run manim -pqh vidaptive_talk.py IntroHook
    uv run manim -pqh vidaptive_talk.py VidaptiveArchitecture

TO RENDER ALL SCENES SEQUENTIALLY:

Using bash/zsh:
    for scene in IntroHook RealtimeVideoConstraints StatusQuoGCCProblem \
                 WhyCCAsWinOnBackloggedFlows CoreIdeaMakeVideoBacklogged \
                 VidaptiveArchitecture LatencyChallengeFrameTransmissionTime \
                 AlphaKnobAndServiceTime OnlineAlphaEstimatorCounterfactual \
                 LatencySafeguardPauseEncoding ResultsCDFQualityLatency \
                 TradeoffFrontierP ComparisonSalsifyDeployability ClosingTakeaways; do
        uv run manim -pqh vidaptive_talk.py $scene
    done

Or render them individually:
    uv run manim -pqh vidaptive_talk.py IntroHook
    uv run manim -pqh vidaptive_talk.py RealtimeVideoConstraints
    uv run manim -pqh vidaptive_talk.py StatusQuoGCCProblem
    # ... and so on

RENDERING OPTIONS:
-p: Preview (opens video after rendering)
-qh: High quality (can also use -ql for low quality, -qm for medium)
-pqh: Preview with high quality (recommended)

Total approximate duration: ~900 seconds (15 minutes)
"""
