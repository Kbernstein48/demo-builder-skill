from __future__ import annotations

import math
import textwrap
from collections.abc import Iterable

import numpy as np
from manim import *


BG = "#182126"
INK = "#2D373C"
INK_SOFT = "#343434"
WHITE = "#FFFFFF"
MUTED = "#A0AAB9"
ORANGE = "#FA4616"
ORANGE_DARK = "#A32200"
ORANGE_SOFT = "#FB6B45"
TEAL = "#0BA2B3"
TEAL_DARK = "#15839A"
TEAL_SOFT = "#5BCBDE"
BLUE = "#1E6482"
GREY = "#D9D9D9"
FONT = "Arial"
SAFE_WIDTH = 12.8
SAFE_HEIGHT = 7.0
GRID_UNIT = 0.55


def fit_to_box(mob: Mobject, max_width: float, max_height: float) -> Mobject:
    if mob.width > max_width:
        mob.scale_to_fit_width(max_width)
    if mob.height > max_height:
        mob.scale_to_fit_height(max_height)
    return mob


def brand_text(text: str, size: int = 32, color: str = WHITE, weight: str = NORMAL) -> Text:
    # Render at 2x and scale down to avoid pseudo-spacing artifacts in short
    # all-caps labels under Cairo/Pango at 1080p.
    return Text(
        text,
        font=FONT,
        font_size=size * 2,
        color=color,
        weight=weight,
        disable_ligatures=True,
    ).scale(0.5)


def wrapped_text(
    text: str,
    width_chars: int,
    size: int,
    color: str = WHITE,
    max_width: float = SAFE_WIDTH,
    max_height: float | None = None,
    weight: str = NORMAL,
) -> Text:
    lines: list[str] = []
    for raw in text.split("\n"):
        if raw.strip():
            lines.extend(textwrap.wrap(raw, width=width_chars))
        else:
            lines.append("")
    mob = Text(
        "\n".join(lines),
        font=FONT,
        font_size=size,
        color=color,
        weight=weight,
        disable_ligatures=True,
        line_spacing=0.78,
    )
    fit_to_box(mob, max_width, max_height or SAFE_HEIGHT)
    return mob


def title_block(kicker: str, title: str, subtitle: str | None = None) -> VGroup:
    kick = brand_text(kicker.upper(), 18, TEAL, BOLD)
    main = brand_text(title, 40, WHITE, BOLD)
    main.set_color_by_gradient(TEAL_SOFT, WHITE, ORANGE)
    fit_to_box(main, SAFE_WIDTH, 1.0)
    parts: list[Mobject] = [kick, main]
    if subtitle:
        parts.append(wrapped_text(subtitle, 66, 19, MUTED, max_width=12.3, max_height=0.75))
    return VGroup(*parts).arrange(DOWN, buff=0.16)


def brand_backdrop(scene: Scene, density: int = 8, show_pixels: bool = True) -> None:
    bg = Rectangle(width=15.5, height=8.8, fill_color=BG, fill_opacity=1, stroke_width=0)
    scene.add(bg)
    grid = VGroup()
    for x in np.linspace(-7.2, 7.2, density):
        grid.add(Line([x, -4.1, 0], [x, 4.1, 0], stroke_color=INK, stroke_width=1, stroke_opacity=0.42))
    for y in np.linspace(-4, 4, max(5, density // 2)):
        grid.add(Line([-7.4, y, 0], [7.4, y, 0], stroke_color=INK, stroke_width=1, stroke_opacity=0.30))
    scene.add(grid)
    if show_pixels:
        scene.add(pixel_motif([(-6.85, 3.55), (-6.58, 3.55), (-6.31, 3.55), (-6.85, 3.28)]))
        scene.add(pixel_motif([(6.62, -3.46), (6.35, -3.46), (6.62, -3.19), (6.08, -3.46)]))


def pixel_motif(points: Iterable[tuple[float, float]], size: float = 0.13) -> VGroup:
    colors = [ORANGE_DARK, "#A5E2F0", TEAL_DARK, INK]
    pixels = VGroup()
    for index, (x, y) in enumerate(points):
        pixels.add(
            Square(
                side_length=size,
                fill_color=colors[index % len(colors)],
                fill_opacity=0.72,
                stroke_width=0,
            ).move_to([x, y, 0])
        )
    return pixels


def label_card(
    label: str,
    sub: str | None = None,
    color: str = TEAL,
    width: float = 2.6,
    height: float = 1.0,
) -> VGroup:
    shell = RoundedRectangle(
        width=width,
        height=height,
        corner_radius=0.16,
        stroke_color=color,
        stroke_width=2,
        fill_color=INK,
        fill_opacity=0.82,
    )
    label_mob = wrapped_text(label, max(8, int(width * 7.5)), 22, WHITE, max_width=width - 0.22)
    parts: list[Mobject] = [label_mob]
    if sub:
        parts.append(wrapped_text(sub, max(10, int(width * 9)), 14, MUTED, max_width=width - 0.22))
    body = VGroup(*parts).arrange(DOWN, buff=0.08)
    fit_to_box(body, width - 0.18, height - 0.14)
    body.move_to(shell)
    shell.set_z_index(3)
    body.set_z_index(4)
    return VGroup(shell, body)


def pill(label: str, color: str = TEAL, size: int = 18) -> VGroup:
    text = brand_text(label, size, WHITE, BOLD)
    box = RoundedRectangle(
        width=max(1.2, text.width + 0.46),
        height=text.height + 0.28,
        corner_radius=0.18,
        stroke_color=color,
        stroke_width=2,
        fill_color=color,
        fill_opacity=0.14,
    )
    text.move_to(box)
    box.set_z_index(5)
    text.set_z_index(6)
    return VGroup(box, text)


def process_rail(labels: list[str], colors: list[str] | None = None, card_width: float = 1.38) -> VGroup:
    colors = colors or [TEAL, ORANGE]
    steps = VGroup()
    for index, label in enumerate(labels):
        steps.add(label_card(label, color=colors[index % len(colors)], width=card_width, height=0.72))
    steps.arrange(RIGHT, buff=0.30)
    arrows = VGroup()
    for left, right in zip(steps[:-1], steps[1:], strict=False):
        arrows.add(Arrow(left.get_right(), right.get_left(), buff=0.06, color=MUTED, stroke_width=2, max_tip_length_to_length_ratio=0.12))
    return VGroup(steps, arrows)


def waveform(
    width: float = 3.0,
    amp: float = 0.38,
    color: str = TEAL,
    cycles: float = 3.0,
    phase: float = 0.0,
    jagged: bool = False,
    stroke_width: float = 5,
) -> VMobject:
    points = []
    count = 110
    for i in range(count):
        t = i / (count - 1)
        x = -width / 2 + width * t
        envelope = 0.35 + 0.65 * math.sin(math.pi * t)
        y = amp * envelope * math.sin(TAU * cycles * t + phase)
        if jagged:
            y += amp * 0.24 * math.sin(TAU * cycles * 3.1 * t + 0.7)
            y += amp * 0.12 * math.sin(TAU * cycles * 7.0 * t)
        points.append([x, y, 0])
    mob = VMobject(stroke_color=color, stroke_width=stroke_width)
    if jagged:
        mob.set_points_as_corners(points)
    else:
        mob.set_points_smoothly(points)
    return mob


def connector(start: Mobject, end: Mobject, color: str = TEAL, width: float = 4) -> Arrow:
    return Arrow(start.get_center(), end.get_center(), buff=0.55, stroke_width=width, color=color, max_tip_length_to_length_ratio=0.08)


def grid_point(column: float, row: float, columns: int = 12, rows: int = 7) -> np.ndarray:
    x = -SAFE_WIDTH / 2 + (SAFE_WIDTH / columns) * column
    y = SAFE_HEIGHT / 2 - (SAFE_HEIGHT / rows) * row
    return np.array([x, y, 0.0])


def place_on_grid(mob: Mobject, column: float, row: float, columns: int = 12, rows: int = 7) -> Mobject:
    return mob.move_to(grid_point(column, row, columns, rows))


def bounds(mob: Mobject, pad: float = 0.0) -> tuple[float, float, float, float]:
    return (
        mob.get_left()[0] - pad,
        mob.get_right()[0] + pad,
        mob.get_bottom()[1] - pad,
        mob.get_top()[1] + pad,
    )


def assert_no_overlaps(named_mobjects: dict[str, Mobject], pad: float = 0.05) -> None:
    items = list(named_mobjects.items())
    for index, (left_name, left_mob) in enumerate(items):
        left = bounds(left_mob, pad)
        for right_name, right_mob in items[index + 1 :]:
            right = bounds(right_mob, pad)
            separate = left[1] < right[0] or right[1] < left[0] or left[3] < right[2] or right[3] < left[2]
            if not separate:
                raise AssertionError(f"Layout overlap: {left_name} intersects {right_name}")


def graph_node(label: str, color: str = TEAL, width: float = 1.44, height: float = 0.58) -> VGroup:
    shell = RoundedRectangle(
        width=width,
        height=height,
        corner_radius=0.13,
        stroke_color=color,
        stroke_width=2,
        fill_color=INK,
        fill_opacity=0.97,
    )
    text = brand_text(label, 13, WHITE, BOLD)
    fit_to_box(text, width - 0.16, height - 0.18)
    text.move_to(shell)
    shell.set_z_index(3)
    text.set_z_index(4)
    return VGroup(shell, text)


def assert_safe_area(
    named_mobjects: dict[str, Mobject],
    x_limit: float = SAFE_WIDTH / 2 - 0.05,
    y_limit: float = SAFE_HEIGHT / 2 + 0.05,
) -> None:
    for name, mob in named_mobjects.items():
        if (
            mob.get_left()[0] < -x_limit
            or mob.get_right()[0] > x_limit
            or mob.get_bottom()[1] < -y_limit
            or mob.get_top()[1] > y_limit
        ):
            raise AssertionError(f"{name} is outside the safe area")


def assert_text_contained(container: Mobject, text: Mobject, padding: float = 0.12) -> None:
    if (
        text.get_left()[0] < container.get_left()[0] + padding
        or text.get_right()[0] > container.get_right()[0] - padding
        or text.get_bottom()[1] < container.get_bottom()[1] + padding
        or text.get_top()[1] > container.get_top()[1] - padding
    ):
        raise AssertionError("Text escapes its fixed container")


def border_port(mob: Mobject, side: str, offset: float = 0.0) -> np.ndarray:
    if side == "left":
        return mob.get_left() + UP * offset
    if side == "right":
        return mob.get_right() + UP * offset
    if side == "top":
        return mob.get_top() + RIGHT * offset
    if side == "bottom":
        return mob.get_bottom() + RIGHT * offset
    raise ValueError(f"Unknown port side: {side}")


def orthogonal_connector(
    source: Mobject,
    target: Mobject,
    color: str = TEAL,
    *,
    source_side: str = "right",
    target_side: str = "left",
    source_offset: float = 0.0,
    target_offset: float = 0.0,
    gutter: float | None = None,
    stroke_width: float = 2.2,
    dashed: bool = False,
) -> VGroup:
    """Create a border-to-border Manhattan connector with route metadata."""
    start = border_port(source, source_side, source_offset)
    end = border_port(target, target_side, target_offset)
    if source_side in {"left", "right"} and target_side in {"left", "right"}:
        if abs(start[1] - end[1]) < 0.02:
            points = [start, end]
        else:
            gutter_x = gutter if gutter is not None else (start[0] + end[0]) / 2
            points = [start, np.array([gutter_x, start[1], 0]), np.array([gutter_x, end[1], 0]), end]
    elif source_side in {"top", "bottom"} and target_side in {"top", "bottom"}:
        if abs(start[0] - end[0]) < 0.02:
            points = [start, end]
        else:
            gutter_y = gutter if gutter is not None else (start[1] + end[1]) / 2
            points = [start, np.array([start[0], gutter_y, 0]), np.array([end[0], gutter_y, 0]), end]
    else:
        points = [start, np.array([end[0], start[1], 0]), end]

    cleaned = [points[0]]
    for point in points[1:]:
        if np.linalg.norm(point - cleaned[-1]) > 0.02:
            cleaned.append(point)
    if len(cleaned) < 2:
        raise ValueError("Connector ports collapsed to one point")

    parts = VGroup()
    for first, second in zip(cleaned[:-2], cleaned[1:-1]):
        segment: Mobject = Line(first, second, color=color, stroke_width=stroke_width)
        if dashed:
            segment = DashedVMobject(segment, num_dashes=max(4, int(segment.get_length() * 5)))
        parts.add(segment)
    final: Mobject = Arrow(
        cleaned[-2],
        cleaned[-1],
        buff=0,
        color=color,
        stroke_width=stroke_width,
        max_tip_length_to_length_ratio=0.14,
    )
    if dashed:
        final = DashedVMobject(final, num_dashes=max(4, int(final.get_length() * 5)))
    parts.add(final)
    parts.set_z_index(1)
    parts.route_points = [point.copy() for point in cleaned]
    parts.route_source = source
    parts.route_target = target
    return parts


def network_link(
    source: Mobject,
    target: Mobject,
    color: str = TEAL,
    *,
    stroke_width: float = 1.45,
    opacity: float = 0.34,
    buff: float = 0.045,
) -> VGroup:
    """Create a straight border-clipped graph link without an arrowhead."""
    source_center = source.get_center()
    target_center = target.get_center()
    delta = target_center - source_center
    norm = float(np.linalg.norm(delta))
    if norm <= 1e-6:
        raise ValueError("Graph nodes cannot share a center")
    direction = delta / norm

    def boundary_t(mob: Mobject) -> float:
        x_t = (mob.width / 2) / abs(delta[0]) if abs(delta[0]) > 1e-6 else np.inf
        y_t = (mob.height / 2) / abs(delta[1]) if abs(delta[1]) > 1e-6 else np.inf
        return float(min(x_t, y_t))

    start = source_center + delta * boundary_t(source) + direction * buff
    end = target_center - delta * boundary_t(target) - direction * buff
    line = Line(start, end, color=color, stroke_width=stroke_width).set_opacity(opacity)
    line.set_z_index(1)
    group = VGroup(line)
    group.route_points = [start.copy(), end.copy()]
    group.route_source = source
    group.route_target = target
    return group


def assert_connector_clearance(
    connector: VGroup,
    obstacles: dict[str, Mobject],
    *,
    padding: float = 0.08,
) -> None:
    points = getattr(connector, "route_points", None)
    if not points:
        raise AssertionError("Connector has no route_points metadata")
    source = getattr(connector, "route_source", None)
    target = getattr(connector, "route_target", None)
    for name, obstacle in obstacles.items():
        if obstacle is source or obstacle is target:
            continue
        left, right, bottom, top = bounds(obstacle, padding)
        for first, second in zip(points[:-1], points[1:]):
            for ratio in np.linspace(0, 1, 25):
                point = first + (second - first) * ratio
                if left < point[0] < right and bottom < point[1] < top:
                    raise AssertionError(f"Connector enters unrelated node: {name}")


def assert_connectors_do_not_cross(
    connectors: dict[str, VGroup],
    *,
    tolerance: float = 0.025,
) -> None:
    """Fail when independent Manhattan connectors cross or share a run."""

    def orientation(first: np.ndarray, second: np.ndarray) -> str:
        if abs(first[1] - second[1]) <= tolerance:
            return "h"
        if abs(first[0] - second[0]) <= tolerance:
            return "v"
        raise AssertionError("Connector contains a non-orthogonal segment")

    def endpoint(point: np.ndarray, first: np.ndarray, second: np.ndarray) -> bool:
        return np.linalg.norm(point - first) <= tolerance or np.linalg.norm(point - second) <= tolerance

    names = list(connectors)
    for index, left_name in enumerate(names):
        left_points = getattr(connectors[left_name], "route_points", None)
        if not left_points:
            raise AssertionError(f"Connector has no route metadata: {left_name}")
        for right_name in names[index + 1 :]:
            right_points = getattr(connectors[right_name], "route_points", None)
            if not right_points:
                raise AssertionError(f"Connector has no route metadata: {right_name}")
            for a0, a1 in zip(left_points[:-1], left_points[1:]):
                a_kind = orientation(a0, a1)
                for b0, b1 in zip(right_points[:-1], right_points[1:]):
                    b_kind = orientation(b0, b1)
                    if a_kind != b_kind:
                        h0, h1 = (a0, a1) if a_kind == "h" else (b0, b1)
                        v0, v1 = (b0, b1) if a_kind == "h" else (a0, a1)
                        point = np.array([v0[0], h0[1], 0.0])
                        on_h = min(h0[0], h1[0]) - tolerance <= point[0] <= max(h0[0], h1[0]) + tolerance
                        on_v = min(v0[1], v1[1]) - tolerance <= point[1] <= max(v0[1], v1[1]) + tolerance
                        if on_h and on_v and not (endpoint(point, a0, a1) and endpoint(point, b0, b1)):
                            raise AssertionError(f"Connector crossing: {left_name} intersects {right_name}")
                    elif a_kind == "h" and abs(a0[1] - b0[1]) <= tolerance:
                        overlap = min(max(a0[0], a1[0]), max(b0[0], b1[0])) - max(min(a0[0], a1[0]), min(b0[0], b1[0]))
                        if overlap > tolerance:
                            raise AssertionError(f"Connector shared run: {left_name} overlaps {right_name}")
                    elif a_kind == "v" and abs(a0[0] - b0[0]) <= tolerance:
                        overlap = min(max(a0[1], a1[1]), max(b0[1], b1[1])) - max(min(a0[1], a1[1]), min(b0[1], b1[1]))
                        if overlap > tolerance:
                            raise AssertionError(f"Connector shared run: {left_name} overlaps {right_name}")
