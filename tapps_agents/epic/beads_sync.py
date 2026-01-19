"""
Sync an Epic to Beads (bd): create one bd issue per story and bd dep add from Story.dependencies.

On run_bd failure we log, return the partial story_id->bd_id mapping, and do not re-raise
so the Epic run can continue.
"""

import logging
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .models import EpicDocument, Story

logger = logging.getLogger(__name__)

# Match bd ids like "TappsCodingAgents-a3f2" or "bd-abc1" in create output (suffix 3+ chars)
_BD_ID_PATTERN = re.compile(r"([A-Za-z0-9]+-[a-zA-Z0-9]{3,})")


def _parse_bd_id_from_stdout(stdout: str) -> str | None:
    """Extract a bd issue id from bd create stdout."""
    # Prefer "Created issue: ID" or "✓ Created issue: ID"
    for line in (stdout or "").splitlines():
        if "reated" in line and "issue" in line.lower():
            m = _BD_ID_PATTERN.search(line)
            if m:
                return m.group(1)
    # Fallback: any line that looks like prefix-hash
    m = _BD_ID_PATTERN.search(stdout or "")
    return m.group(1) if m else None


def sync_epic_to_beads(
    epic: EpicDocument,
    project_root: Path,
    run_bd: Callable[[list[str], Path | None], Any],
) -> dict[str, str]:
    """
    Create a bd issue for each story and bd dep add for each dependency.

    run_bd(args, cwd) runs bd and returns a CompletedProcess-like object with
    .returncode, .stdout, .stderr. It is typically beads.client.run_bd partially
    applied with project_root.

    On any run_bd failure we log, return the partial story_id->bd_id mapping,
    and do not re-raise.

    Args:
        epic: Parsed Epic document.
        project_root: Project root (used as cwd when run_bd does not override).
        run_bd: (args, cwd=None) -> result with .returncode, .stdout, .stderr.

    Returns:
        Mapping from story_id (e.g. "8.1") to bd issue id (e.g. "TappsCodingAgents-a3f2").
    """
    story_to_bd: dict[str, str] = {}
    cwd = project_root

    # Create one bd issue per story
    for story in epic.stories:
        title = (story.title or f"Story {story.story_id}")[:200].strip()
        desc = (story.description or "")[:500].replace("\n", " ").strip()
        args = ["create", title]
        if desc:
            args.extend(["-d", desc])
        try:
            r = run_bd(args, cwd)
            if r.returncode != 0:
                logger.warning(
                    "beads_sync: bd create failed for %s: %s", story.story_id, r.stderr
                )
                continue
            bd_id = _parse_bd_id_from_stdout(r.stdout)
            if bd_id:
                story_to_bd[story.story_id] = bd_id
            else:
                logger.warning(
                    "beads_sync: could not parse bd id from create stdout for %s",
                    story.story_id,
                )
        except Exception as e:
            logger.warning("beads_sync: bd create failed for %s: %s", story.story_id, e)

    # bd dep add child parent  => parent blocks child (child depends on parent)
    for story in epic.stories:
        s_bd = story_to_bd.get(story.story_id)
        if not s_bd or not story.dependencies:
            continue
        for dep_id in story.dependencies:
            dep_bd = story_to_bd.get(dep_id)
            if not dep_bd:
                continue
            try:
                r = run_bd(["dep", "add", s_bd, dep_bd], cwd)
                if r.returncode != 0:
                    logger.warning(
                        "beads_sync: bd dep add %s %s failed: %s",
                        s_bd,
                        dep_bd,
                        r.stderr,
                    )
            except Exception as e:
                logger.warning(
                    "beads_sync: bd dep add %s %s failed: %s", s_bd, dep_bd, e
                )

    return story_to_bd
