"""
Shared parsing for Beads (bd) output: extract issue id from bd create stdout.

Used by beads_sync (epic) and beads_hooks (simple_mode, workflow).
"""

import re

# Match bd ids like "TappsCodingAgents-a3f2" or "bd-abc1" in create output (suffix 3+ chars)
BD_ID_PATTERN = re.compile(r"([A-Za-z0-9]+-[a-zA-Z0-9]{3,})")


def parse_bd_id_from_stdout(stdout: str) -> str | None:
    """
    Extract a bd issue id from bd create stdout.

    Prefer lines containing "Created issue" (or "reated" + "issue"), then
    fallback to first prefix-hash match in the text.

    Args:
        stdout: Captured stdout from `bd create`.

    Returns:
        The bd issue id, or None if not found.
    """
    for line in (stdout or "").splitlines():
        if "reated" in line and "issue" in line.lower():
            m = BD_ID_PATTERN.search(line)
            if m:
                return m.group(1)
    m = BD_ID_PATTERN.search(stdout or "")
    return m.group(1) if m else None
