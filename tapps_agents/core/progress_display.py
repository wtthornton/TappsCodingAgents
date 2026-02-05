"""
Phase-grid progress display format.

Terminal-style phase grid with icons, Unicode or ASCII progress bars, status
labels, and optional sub-items. Used for workflow completion, workflow state
show, and multi-phase reporting. Windows/CI-safe when use_unicode=False.
"""

from __future__ import annotations

# Tree characters for sub-items (Unicode); ASCII fallback
_SUB_ITEM_PREFIX_UNICODE = "  \u2514\u2500 "  # └─
_SUB_ITEM_PREFIX_ASCII = "  - "


def create_progress_bar(
    percentage: float,
    width: int = 10,
    use_unicode: bool = True,
) -> str:
    """
    Create a progress bar string.

    Args:
        percentage: Completion 0-100.
        width: Number of blocks (default 10 per HomeIQ spec).
        use_unicode: If True use block char U+2588; else use '#'.

    Returns:
        Bar string like "[█████     ]" or "[#####     ]".
    """
    percentage = max(0.0, min(100.0, percentage))
    filled = int((percentage / 100.0) * width)
    empty = width - filled
    if use_unicode:
        block = "\u2588"  # FULL BLOCK
        bar = block * filled + " " * empty
    else:
        bar = "#" * filled + " " * empty
    return f"[{bar}]"


def create_status_line(
    phase_name: str,
    percentage: float,
    status: str,
    icon: str,
    *,
    use_unicode: bool = True,
    name_width: int = 20,
    bar_width: int = 10,
) -> str:
    """
    Create a single status line: name, icon, bar, percentage, status label.

    Args:
        phase_name: Phase label (e.g. "Phase 1: Build").
        percentage: 0-100.
        status: Uppercase label (e.g. "COMPLETE", "PENDING").
        icon: Single emoji or character.
        use_unicode: If False, icon is replaced by ASCII tag where known.
        name_width: Pad phase name to this width.
        bar_width: Passed to create_progress_bar.

    Returns:
        One formatted line.
    """
    padded_name = phase_name[:name_width].ljust(name_width)
    bar = create_progress_bar(percentage, width=bar_width, use_unicode=use_unicode)
    pct_str = f"{int(percentage):3d}%"

    if not use_unicode:
        icon = _icon_to_ascii(icon)

    return f"{padded_name} {icon} {bar} {pct_str} {status}"


def _icon_to_ascii(icon: str) -> str:
    """Replace common emoji with ASCII tags for plain/Windows output."""
    mapping = {
        "\u2705": "[OK]",       # ✅
        "\u274c": "[FAIL]",     # ❌
        "\u23f3": "[WAIT]",     # ⏳
        "\u27a1\ufe0f": "[RUN]",   # ➡️
        "\U0001f4cb": "[READY]",  # 📋
        "\u26a0\ufe0f": "[WARN]",  # ⚠️
        "\U0001f504": "[RUN]",   # 🔄
        "\u23ed\ufe0f": "[SKIP]",  # ⏭️
    }
    return mapping.get(icon.strip(), "[?]")


def generate_status_report(
    phases: list[dict],
    *,
    title: str = "Progress Summary",
    use_unicode: bool = True,
    show_total: bool = True,
    name_width: int = 20,
    bar_width: int = 10,
) -> str:
    """
    Generate a full status report (title, phase lines, sub_items, TOTAL).

    Args:
        phases: List of dicts with keys: name, percentage, status, icon;
                optional "sub_items": list[str].
        title: First line (e.g. "Progress Summary").
        use_unicode: Use Unicode bar and icons when True.
        show_total: Append "TOTAL: X% complete (N/M phases)".
        name_width: Phase name column width.
        bar_width: Bar width in blocks.

    Returns:
        Formatted multi-line string.
    """
    lines = [title, ""]
    completed_count = 0

    for phase in phases:
        name = phase.get("name", "?")
        percentage = float(phase.get("percentage", 0))
        status = phase.get("status", "PENDING")
        icon = phase.get("icon", "\u23f3")  # ⏳

        line = create_status_line(
            name,
            percentage,
            status,
            icon,
            use_unicode=use_unicode,
            name_width=name_width,
            bar_width=bar_width,
        )
        lines.append(line)

        if percentage >= 100:
            completed_count += 1

        for sub in phase.get("sub_items") or []:
            prefix = _SUB_ITEM_PREFIX_UNICODE if use_unicode else _SUB_ITEM_PREFIX_ASCII
            lines.append(f"{prefix}{sub}")

    if show_total and phases:
        total = len(phases)
        overall_pct = (completed_count / total) * 100.0
        lines.append("")
        lines.append(f"TOTAL: {overall_pct:.1f}% complete ({completed_count}/{total} phases)")

    return "\n".join(lines)
