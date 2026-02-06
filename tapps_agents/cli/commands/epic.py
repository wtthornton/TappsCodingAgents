"""
Epic CLI command handlers.

Phase 1.2: epic status
Phase 1.3: cleanup epic-state
Phase 2.2: epic approve / pause
"""

import json
import logging
from pathlib import Path

from ...core.config import load_config
from ...core.unicode_safe import safe_print
from ...epic.state_manager import EpicStateManager

logger = logging.getLogger(__name__)


def handle_epic_command(args: object) -> None:
    """Route epic subcommands."""
    command = getattr(args, "epic_command", None)
    if command == "status":
        handle_epic_status_command(args)
    elif command == "approve":
        handle_epic_approve_command(args)
    elif command == "pause":
        handle_epic_pause_command(args)
    else:
        safe_print("Usage: tapps-agents epic {status|approve|pause}")
        safe_print("  status  - Show Epic execution status")
        safe_print("  approve - Pre-approve an Epic for execution")
        safe_print("  pause   - Pause and write handoff")


def handle_epic_status_command(args: object) -> None:
    """Show Epic execution status."""
    project_root = Path.cwd()
    state_manager = EpicStateManager(project_root=project_root)
    show_all = getattr(args, "all", False)
    output_format = getattr(args, "format", "text")
    epic_path_str = getattr(args, "epic_path", None)

    if show_all:
        states = state_manager.list_epic_states()
        if not states:
            safe_print("No epic states found.")
            return
        if output_format == "json":
            safe_print(json.dumps(states, indent=2))
            return
        # Text table
        safe_print(f"{'Epic ID':<15} {'Title':<35} {'Progress':<10} {'Updated':<20}")
        safe_print("-" * 80)
        for s in states:
            safe_print(
                f"{s['epic_id']:<15} {s['epic_title'][:33]:<35} "
                f"{s['done']}/{s['total']} ({s['completion']})  {s['updated_at'][:19]}"
            )
        return

    if not epic_path_str:
        safe_print("Error: Provide epic_path or use --all")
        return

    # Parse epic and load state
    from ...epic.parser import EpicParser

    parser = EpicParser(project_root=project_root)
    epic = parser.parse(epic_path_str)
    epic_id = f"epic-{epic.epic_number}"
    state = state_manager.load_state(epic_id)

    if output_format == "json":
        safe_print(json.dumps(state or {"epic_id": epic_id, "status": "no state"}, indent=2))
        return

    # Text output
    safe_print(f"Epic {epic.epic_number}: {epic.title}")
    safe_print(f"Stories: {len(epic.stories)}")

    if state:
        stories = state.get("stories", [])
        done = sum(1 for s in stories if s.get("status") == "done")
        failed = sum(1 for s in stories if s.get("status") == "failed")
        pct = (done / len(stories) * 100) if stories else 0.0
        safe_print(f"Progress: {done}/{len(stories)} done ({pct:.0f}%), {failed} failed")
        safe_print(f"Updated: {state.get('updated_at', 'N/A')}")
        safe_print("")
        safe_print(f"{'Story':<10} {'Title':<40} {'Status':<12} {'Score':<8}")
        safe_print("-" * 70)
        for s in stories:
            scores = s.get("quality_scores", {})
            score_str = str(scores.get("overall", "")) if scores else ""
            safe_print(
                f"{s.get('story_id', '?'):<10} "
                f"{s.get('title', '')[:38]:<40} "
                f"{s.get('status', 'pending'):<12} "
                f"{score_str:<8}"
            )
    else:
        safe_print("No execution state found. Run the Epic first.")


def handle_epic_approve_command(args: object) -> None:
    """Write approval marker for an Epic."""
    project_root = Path.cwd()
    epic_path_str = getattr(args, "epic_path", None)
    if not epic_path_str:
        safe_print("Error: epic_path required")
        return

    from ...epic.parser import EpicParser

    parser = EpicParser(project_root=project_root)
    epic = parser.parse(epic_path_str)
    epic_id = f"epic-{epic.epic_number}"

    marker_dir = project_root / ".tapps-agents" / "epic-state"
    marker_dir.mkdir(parents=True, exist_ok=True)
    marker = marker_dir / f"{epic_id}.approved"
    marker.write_text(f"Approved at {__import__('datetime').datetime.now().isoformat()}\n", encoding="utf-8")
    safe_print(f"Epic {epic_id} approved. Marker: {marker}")


def handle_epic_pause_command(args: object) -> None:
    """Pause and write handoff for a running Epic."""
    project_root = Path.cwd()
    epic_path_str = getattr(args, "epic_path", None)
    if not epic_path_str:
        safe_print("Error: epic_path required")
        return

    from ...epic.parser import EpicParser

    parser = EpicParser(project_root=project_root)
    epic = parser.parse(epic_path_str)
    epic_id = f"epic-{epic.epic_number}"

    state_manager = EpicStateManager(project_root=project_root)
    state = state_manager.load_state(epic_id)
    if not state:
        safe_print(f"No state found for {epic_id}. Nothing to pause.")
        return

    handoff_path = state_manager.write_handoff(epic_id, state)
    safe_print(f"Handoff written: {handoff_path}")


def handle_cleanup_epic_state_command(args: object) -> None:
    """Clean up old epic state files."""
    project_root = Path.cwd()
    state_manager = EpicStateManager(project_root=project_root)
    retention_days = getattr(args, "retention_days", 30)
    remove_completed = getattr(args, "remove_completed", False)
    archive = getattr(args, "archive", False)
    dry_run = getattr(args, "dry_run", False)

    actions = state_manager.cleanup_states(
        retention_days=retention_days,
        remove_completed=remove_completed,
        archive=archive,
        dry_run=dry_run,
    )

    if not actions:
        safe_print("No epic state files to clean up.")
        return

    prefix = "[DRY RUN] " if dry_run else ""
    for a in actions:
        safe_print(f"{prefix}{a['action']}: {a['file']}")
    safe_print(f"\n{prefix}{len(actions)} file(s) {'would be' if dry_run else ''} processed.")
