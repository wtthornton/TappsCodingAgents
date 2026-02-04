"""
Sync an Epic to Beads (bd): create one bd issue per story and bd dep add from Story.dependencies.

On run_bd failure we log, return the partial story_id->bd_id mapping, and do not re-raise
so the Epic run can continue.
"""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..beads import parse_bd_id_from_stdout
from .models import EpicDocument

logger = logging.getLogger(__name__)


def sync_epic_to_beads(
    epic: EpicDocument,
    project_root: Path,
    run_bd: Callable[[list[str], Path | None], Any],
    *,
    create_parent: bool = True,
) -> tuple[dict[str, str], str | None]:
    """
    Create a bd issue for each story and bd dep add for each dependency.

    Optionally create a parent Epic issue (for grouping only; no story->parent deps).

    run_bd(args, cwd) runs bd and returns a CompletedProcess-like object with
    .returncode, .stdout, .stderr. It is typically beads.client.run_bd partially
    applied with project_root.

    On any run_bd failure we log, return the partial story_id->bd_id mapping,
    and do not re-raise.

    Args:
        epic: Parsed Epic document.
        project_root: Project root (used as cwd when run_bd does not override).
        run_bd: (args, cwd=None) -> result with .returncode, .stdout, .stderr.
        create_parent: If True, create a parent bd issue for the Epic (grouping only).

    Returns:
        (story_id -> bd_id mapping, epic_parent_id or None).
    """
    story_to_bd: dict[str, str] = {}
    epic_parent_id: str | None = None
    cwd = project_root

    # Optional: create parent Epic issue (grouping only; no story->parent deps)
    if create_parent:
        title = f"Epic {epic.epic_number}: {epic.title}"[:200].strip()
        desc = (epic.description or epic.goal or "")[:500].replace("\n", " ").strip()
        args = ["create", title]
        if desc:
            args.extend(["-d", desc])
        try:
            r = run_bd(args, cwd)
            if r.returncode == 0:
                epic_parent_id = parse_bd_id_from_stdout(r.stdout)
            else:
                logger.warning("beads_sync: bd create parent failed: %s", r.stderr)
        except Exception as e:
            logger.warning("beads_sync: bd create parent failed: %s", e)

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
            bd_id = parse_bd_id_from_stdout(r.stdout)
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

    return (story_to_bd, epic_parent_id)
