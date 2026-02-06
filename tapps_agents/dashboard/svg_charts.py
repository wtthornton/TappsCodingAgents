"""
Pure-Python SVG chart generators for the dashboard.

Generates inline SVG strings for: ring gauges, bar charts, sparklines,
horizontal bar charts, and status badges.  No external dependencies.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


# ── colour palette (matches PRD dark-theme) ──────────────────────────
GREEN = "#00b894"
YELLOW = "#fdcb6e"
RED = "#ff6b6b"
BLUE = "#74b9ff"
CYAN = "#53d8fb"
ACCENT = "#0f3460"
SURFACE = "#16213e"
TEXT = "#e0e0e0"
TEXT_DIM = "#8899aa"


def _score_colour(value: float, max_val: float = 100.0) -> str:
    """Return a colour based on value/max ratio."""
    ratio = value / max_val if max_val else 0
    if ratio >= 0.8:
        return GREEN
    if ratio >= 0.6:
        return YELLOW
    return RED


def _status_colour(status: str) -> str:
    """Colour for health status strings."""
    s = status.lower()
    if s in ("healthy", "pass", "success"):
        return GREEN
    if s in ("degraded", "warning", "warn"):
        return YELLOW
    return RED


# ── Ring Gauge ────────────────────────────────────────────────────────

def ring_gauge(
    value: float,
    max_val: float = 100.0,
    size: int = 120,
    stroke: int = 10,
    label: str = "",
    colour: str | None = None,
) -> str:
    """SVG ring gauge (donut chart) with centred value text.

    Args:
        value: Current value.
        max_val: Maximum value for the gauge.
        size: Width/height in pixels.
        stroke: Ring thickness.
        label: Optional label under the value.
        colour: Override colour (auto-selects from value if None).

    Returns:
        SVG string.
    """
    radius = (size - stroke) / 2
    circumference = 2 * math.pi * radius
    ratio = min(value / max_val, 1.0) if max_val else 0
    dash = circumference * ratio
    gap = circumference - dash
    cx = cy = size / 2
    fill = colour or _score_colour(value, max_val)

    display_val = f"{value:.0f}" if value == int(value) else f"{value:.1f}"

    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}"'
        f' xmlns="http://www.w3.org/2000/svg">'
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none"'
        f' stroke="{SURFACE}" stroke-width="{stroke}"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none"'
        f' stroke="{fill}" stroke-width="{stroke}"'
        f' stroke-dasharray="{dash:.1f} {gap:.1f}"'
        f' stroke-linecap="round"'
        f' transform="rotate(-90 {cx} {cy})"/>'
        f'<text x="{cx}" y="{cy}" text-anchor="middle"'
        f' dominant-baseline="central" fill="{TEXT}"'
        f' font-size="{size // 4}px" font-weight="bold">{display_val}</text>'
        + (
            f'<text x="{cx}" y="{cy + size // 5}" text-anchor="middle"'
            f' fill="{TEXT_DIM}" font-size="{size // 8}px">{label}</text>'
            if label
            else ""
        )
        + "</svg>"
    )


# ── Bar Chart ─────────────────────────────────────────────────────────

def bar_chart(
    labels: list[str],
    values: list[float],
    width: int = 400,
    height: int = 200,
    colour: str = CYAN,
    show_values: bool = True,
) -> str:
    """Simple vertical bar chart.

    Args:
        labels: X-axis labels.
        values: Bar heights.
        width: SVG width.
        height: SVG height.
        colour: Bar colour.
        show_values: Show values on top of bars.

    Returns:
        SVG string.
    """
    if not values:
        return f'<svg width="{width}" height="{height}"></svg>'

    n = len(values)
    max_v = max(values) or 1
    padding_top = 24
    padding_bottom = 40
    chart_h = height - padding_top - padding_bottom
    bar_gap = 4
    bar_w = max(((width - 20) / n) - bar_gap, 4)
    start_x = 10

    bars: list[str] = []
    for i, (label, val) in enumerate(zip(labels, values)):
        bh = (val / max_v) * chart_h
        bx = start_x + i * (bar_w + bar_gap)
        by = padding_top + chart_h - bh
        bars.append(
            f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w:.1f}"'
            f' height="{bh:.1f}" rx="2" fill="{colour}" opacity="0.85"/>'
        )
        if show_values and val > 0:
            bars.append(
                f'<text x="{bx + bar_w / 2:.1f}" y="{by - 4:.1f}"'
                f' text-anchor="middle" fill="{TEXT_DIM}" font-size="10">'
                f"{val:.0f}</text>"
            )
        # Truncate label if too long
        short = label[:6] + ".." if len(label) > 8 else label
        bars.append(
            f'<text x="{bx + bar_w / 2:.1f}" y="{height - 8:.1f}"'
            f' text-anchor="middle" fill="{TEXT_DIM}" font-size="10"'
            f' transform="rotate(-30 {bx + bar_w / 2:.1f} {height - 8:.1f})">'
            f"{short}</text>"
        )

    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"'
        f' xmlns="http://www.w3.org/2000/svg">'
        + "".join(bars)
        + "</svg>"
    )


# ── Horizontal Bar Chart ──────────────────────────────────────────────

def horizontal_bar_chart(
    labels: list[str],
    values: list[float],
    width: int = 350,
    bar_height: int = 22,
    colours: list[str] | None = None,
) -> str:
    """Horizontal bar chart with labels on the left.

    Args:
        labels: Category labels.
        values: Bar lengths.
        width: SVG width.
        bar_height: Height of each bar.
        colours: Optional per-bar colours.

    Returns:
        SVG string.
    """
    if not values:
        return ""

    n = len(values)
    max_v = max(values) or 1
    label_w = 100
    chart_w = width - label_w - 10
    gap = 4
    height = n * (bar_height + gap) + 10

    rows: list[str] = []
    for i, (label, val) in enumerate(zip(labels, values)):
        y = i * (bar_height + gap) + 5
        bw = (val / max_v) * chart_w
        c = (colours[i] if colours and i < len(colours) else CYAN)
        rows.append(
            f'<text x="{label_w - 6}" y="{y + bar_height / 2 + 4:.0f}"'
            f' text-anchor="end" fill="{TEXT_DIM}" font-size="11">{label}</text>'
            f'<rect x="{label_w}" y="{y}" width="{bw:.1f}"'
            f' height="{bar_height}" rx="3" fill="{c}" opacity="0.8"/>'
            f'<text x="{label_w + bw + 6:.1f}" y="{y + bar_height / 2 + 4:.0f}"'
            f' fill="{TEXT}" font-size="11">{val:.0f}</text>'
        )

    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"'
        f' xmlns="http://www.w3.org/2000/svg">'
        + "".join(rows)
        + "</svg>"
    )


# ── Sparkline ─────────────────────────────────────────────────────────

def sparkline(
    values: list[float],
    width: int = 100,
    height: int = 24,
    colour: str = CYAN,
    fill: bool = True,
) -> str:
    """Tiny inline sparkline chart.

    Args:
        values: Data points.
        width: SVG width.
        height: SVG height.
        colour: Stroke colour.
        fill: Add a translucent area fill.

    Returns:
        SVG string.
    """
    if not values or len(values) < 2:
        return f'<svg width="{width}" height="{height}"></svg>'

    min_v = min(values)
    max_v = max(values)
    v_range = max_v - min_v or 1
    pad = 2
    w = width - 2 * pad
    h = height - 2 * pad

    points: list[str] = []
    for i, v in enumerate(values):
        x = pad + (i / (len(values) - 1)) * w
        y = pad + h - ((v - min_v) / v_range) * h
        points.append(f"{x:.1f},{y:.1f}")

    polyline = " ".join(points)
    # Area fill: close the path along the bottom
    area_points = polyline + f" {pad + w:.1f},{pad + h:.1f} {pad:.1f},{pad + h:.1f}"

    parts = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"'
        f' xmlns="http://www.w3.org/2000/svg">',
    ]
    if fill:
        parts.append(
            f'<polygon points="{area_points}" fill="{colour}" opacity="0.15"/>'
        )
    parts.append(
        f'<polyline points="{polyline}" fill="none" stroke="{colour}"'
        f' stroke-width="1.5" stroke-linejoin="round"/>'
    )
    parts.append("</svg>")
    return "".join(parts)


# ── Status Badge ──────────────────────────────────────────────────────

def status_badge(status: str, size: int = 12) -> str:
    """Coloured status dot."""
    c = _status_colour(status)
    return (
        f'<svg width="{size}" height="{size}" style="vertical-align:middle">'
        f'<circle cx="{size // 2}" cy="{size // 2}" r="{size // 2 - 1}" fill="{c}"/>'
        f"</svg>"
    )


# ── Number Pill ───────────────────────────────────────────────────────

def number_pill(
    value: str,
    label: str,
    colour: str = CYAN,
) -> str:
    """Inline metric pill (number + label)."""
    return (
        f'<span class="pill" style="border-color:{colour}">'
        f'<span class="pill-val" style="color:{colour}">{value}</span>'
        f'<span class="pill-label">{label}</span></span>'
    )


# ── Radar / Spider Chart ─────────────────────────────────────────────

def radar_chart(
    dimensions: dict[str, float],
    max_val: float = 100.0,
    size: int = 260,
    colour: str = CYAN,
) -> str:
    """Radar (spider) chart for quality dimensions.

    Args:
        dimensions: Mapping of label -> value.
        max_val: Scale maximum.
        size: Width and height.
        colour: Fill/stroke colour.

    Returns:
        SVG string.
    """
    if not dimensions:
        return ""

    labels = list(dimensions.keys())
    vals = list(dimensions.values())
    n = len(labels)
    cx = cy = size / 2
    r = size / 2 - 30  # Leave room for labels
    angle_step = 2 * math.pi / n

    # Grid rings
    grid: list[str] = []
    for ring_frac in (0.25, 0.5, 0.75, 1.0):
        pts = []
        for i in range(n):
            angle = -math.pi / 2 + i * angle_step
            x = cx + r * ring_frac * math.cos(angle)
            y = cy + r * ring_frac * math.sin(angle)
            pts.append(f"{x:.1f},{y:.1f}")
        grid.append(
            f'<polygon points="{" ".join(pts)}" fill="none"'
            f' stroke="{TEXT_DIM}" stroke-width="0.5" opacity="0.3"/>'
        )

    # Data polygon
    data_pts = []
    for i, v in enumerate(vals):
        ratio = min(v / max_val, 1.0) if max_val else 0
        angle = -math.pi / 2 + i * angle_step
        x = cx + r * ratio * math.cos(angle)
        y = cy + r * ratio * math.sin(angle)
        data_pts.append(f"{x:.1f},{y:.1f}")

    # Axis labels
    lbl_parts: list[str] = []
    for i, lab in enumerate(labels):
        angle = -math.pi / 2 + i * angle_step
        lx = cx + (r + 18) * math.cos(angle)
        ly = cy + (r + 18) * math.sin(angle)
        anchor = "middle"
        if math.cos(angle) > 0.3:
            anchor = "start"
        elif math.cos(angle) < -0.3:
            anchor = "end"
        short = lab[:10]
        lbl_parts.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}"'
            f' dominant-baseline="central" fill="{TEXT_DIM}" font-size="10">'
            f"{short}</text>"
        )

    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}"'
        f' xmlns="http://www.w3.org/2000/svg">'
        + "".join(grid)
        + f'<polygon points="{" ".join(data_pts)}" fill="{colour}" opacity="0.25"'
        f' stroke="{colour}" stroke-width="1.5"/>'
        + "".join(lbl_parts)
        + "</svg>"
    )
