"""
Hydration engine: create Beads issues from task specs, update specs from Beads.

Hydrate: for specs without beads_issue, run bd create and save id; recreate
dependency graph with bd dep add. Dehydrate: run bd list, update spec files
with current status. Handles missing bd gracefully (log, no crash).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from .client import is_available, run_bd
from .parse import parse_bd_id_from_stdout
from .specs import load_task_specs, save_task_spec

logger = logging.getLogger(__name__)


@dataclass
class HydrationReport:
    """Summary of a hydration run."""

    created: int = 0
    skipped: int = 0
    failed: int = 0
    deps_added: int = 0
    bd_unavailable: bool = False
    dry_run: bool = False


def hydrate_to_beads(
    project_root: Path | None = None,
    *,
    dry_run: bool = False,
) -> HydrationReport:
    """
    Create Beads issues for task specs that don't have beads_issue; recreate deps.

    For each spec in .tapps-agents/task-specs/ without beads_issue, runs
    bd create and stores the returned id in the spec file. Then runs
    bd dep add for each dependency. If bd is not available, logs and returns
    without raising.

    Args:
        project_root: Project root (default: cwd).
        dry_run: If True, do not run bd or write files; report what would be done.

    Returns:
        HydrationReport with created/skipped/failed/deps_added counts.
    """
    project_root = project_root or Path.cwd()
    report = HydrationReport(dry_run=dry_run)

    if not is_available(project_root):
        logger.warning("Hydration skipped: bd not available")
        report.bd_unavailable = True
        return report

    specs = load_task_specs(project_root)
    if not specs:
        return report

    # Map spec.id -> beads_issue id after creation
    spec_to_bd: dict[str, str] = {}
    for spec in specs:
        if spec.beads_issue:
            spec_to_bd[spec.id] = spec.beads_issue
            report.skipped += 1
            continue
        if dry_run:
            report.created += 1
            continue
        title = (spec.title or spec.id)[:200].strip()
        desc = (spec.description or "")[:500].replace("\n", " ").strip()
        args = ["create", title]
        if desc:
            args.extend(["-d", desc])
        try:
            r = run_bd(project_root, args)
            if r.returncode != 0:
                logger.warning("Hydration: bd create failed for %s: %s", spec.id, r.stderr)
                report.failed += 1
                continue
            bd_id = parse_bd_id_from_stdout(r.stdout)
            if bd_id:
                spec_to_bd[spec.id] = bd_id
                spec.beads_issue = bd_id
                save_task_spec(spec, project_root)
                report.created += 1
            else:
                logger.warning("Hydration: could not parse bd id for %s", spec.id)
                report.failed += 1
        except Exception as e:
            logger.warning("Hydration: bd create failed for %s: %s", spec.id, e)
            report.failed += 1

    # Recreate dependency graph: bd dep add child parent (parent blocks child)
    if dry_run:
        for spec in specs:
            if spec.dependencies and spec_to_bd.get(spec.id):
                report.deps_added += len([d for d in spec.dependencies if spec_to_bd.get(d)])
        return report

    for spec in specs:
        child_bd = spec_to_bd.get(spec.id)
        if not child_bd or not spec.dependencies:
            continue
        for dep_id in spec.dependencies:
            parent_bd = spec_to_bd.get(dep_id)
            if not parent_bd:
                continue
            try:
                r = run_bd(project_root, ["dep", "add", child_bd, parent_bd])
                if r.returncode == 0:
                    report.deps_added += 1
                else:
                    logger.warning(
                        "Hydration: bd dep add %s %s failed: %s",
                        child_bd,
                        parent_bd,
                        r.stderr,
                    )
            except Exception as e:
                logger.warning("Hydration: bd dep add %s %s failed: %s", child_bd, parent_bd, e)

    return report


def dehydrate_from_beads(project_root: Path | None = None) -> int:
    """
    Update task spec files with current status from Beads.

    Runs bd list (or equivalent), maps beads_issue id to status, and updates
    each spec file. If bd is not available, logs and returns 0.

    Args:
        project_root: Project root (default: cwd).

    Returns:
        Number of spec files updated.
    """
    project_root = project_root or Path.cwd()

    if not is_available(project_root):
        logger.warning("Dehydration skipped: bd not available")
        return 0

    # Try bd list --json; fallback to parsing stdout if format differs
    try:
        r = run_bd(project_root, ["list", "--json"])
    except Exception as e:
        logger.warning("Dehydration: bd list failed: %s", e)
        return 0

    if r.returncode != 0:
        logger.warning("Dehydration: bd list failed: %s", r.stderr)
        return 0

    bd_status_by_id: dict[str, str] = {}
    try:
        raw = json.loads(r.stdout or "[]")
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict):
                    bid = item.get("id") or item.get("bd_id") or item.get("issue_id")
                    status = item.get("status") or item.get("state") or "todo"
                    if bid:
                        bd_status_by_id[str(bid)] = str(status).lower()
        elif isinstance(raw, dict):
            for bid, info in raw.items():
                if isinstance(info, dict):
                    status = info.get("status") or info.get("state") or "todo"
                else:
                    status = str(info)
                bd_status_by_id[str(bid)] = str(status).lower()
    except json.JSONDecodeError:
        # Fallback: parse line-based output for "id status" or "id\tstatus"
        for line in (r.stdout or "").splitlines():
            parts = line.strip().split()
            if len(parts) >= 2:
                bd_status_by_id[parts[0]] = parts[1].lower()
            elif len(parts) == 1:
                bd_status_by_id[parts[0]] = "todo"

    specs = load_task_specs(project_root)
    updated = 0
    for spec in specs:
        if not spec.beads_issue:
            continue
        new_status = bd_status_by_id.get(spec.beads_issue)
        if not new_status:
            continue
        # Map bd status to our status if needed
        if new_status in ("todo", "open", "pending"):
            mapped = "todo"
        elif new_status in ("in-progress", "in_progress", "wip"):
            mapped = "in-progress"
        elif new_status in ("done", "closed", "completed"):
            mapped = "done"
        elif new_status == "blocked":
            mapped = "blocked"
        else:
            mapped = spec.status
        if spec.status != mapped:
            spec = spec.model_copy(update={"status": mapped})
            save_task_spec(spec, project_root)
            updated += 1

    return updated
