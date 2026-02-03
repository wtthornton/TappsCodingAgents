"""
Task management CLI: create, list, show, update, close, hydrate, dehydrate, run.

Manages task specs in .tapps-agents/task-specs/ and sync with Beads (bd).
"""

from __future__ import annotations

import sys
from pathlib import Path

from ..feedback import get_feedback
from .common import format_json_output


def handle_task_command(args: object) -> None:
    """Dispatch to task subcommand handler."""
    cmd = getattr(args, "task_command", None)
    if not cmd:
        print("task: subcommand required (create, list, show, update, close, hydrate, dehydrate, run)", file=sys.stderr)
        sys.exit(2)
    handlers = {
        "create": _handle_create,
        "list": _handle_list,
        "show": _handle_show,
        "update": _handle_update,
        "close": _handle_close,
        "hydrate": _handle_hydrate,
        "dehydrate": _handle_dehydrate,
        "run": _handle_run,
    }
    handler = handlers.get(cmd)
    if not handler:
        print(f"task: unknown subcommand {cmd!r}", file=sys.stderr)
        sys.exit(2)
    handler(args)


def _project_root() -> Path:
    return Path.cwd()


def _handle_create(args: object) -> None:
    from ...beads.specs import TaskSpec, save_task_spec
    from ...beads.hydration import hydrate_to_beads

    task_id = getattr(args, "id", "").strip()
    title = getattr(args, "title", "").strip()
    if not task_id or not title:
        print("task create: id and --title are required", file=sys.stderr)
        sys.exit(2)
    root = _project_root()
    spec = TaskSpec(
        id=task_id,
        title=title,
        description=getattr(args, "description", "") or "",
        workflow=getattr(args, "workflow", "build") or "build",
    )
    save_task_spec(spec, root)
    print(f"Created task spec: {spec.id} ({root / '.tapps-agents' / 'task-specs' / f'{spec.id}.yaml'})")
    if getattr(args, "beads", False):
        report = hydrate_to_beads(project_root=root)
        if report.bd_unavailable:
            print("Beads (bd) not available; spec created without Beads issue.", file=sys.stderr)
        else:
            print(f"Hydration: created={report.created}, skipped={report.skipped}")


def _handle_list(args: object) -> None:
    from ...beads.specs import load_task_specs

    root = _project_root()
    specs = load_task_specs(root)
    status_filter = getattr(args, "status", None)
    if status_filter:
        specs = [s for s in specs if s.status == status_filter]
    out_fmt = getattr(args, "format", "text")
    if out_fmt == "json":
        format_json_output([s.model_dump() for s in specs])
        return
    if not specs:
        print("No task specs found.")
        return
    for s in specs:
        beads = f" [bd:{s.beads_issue}]" if s.beads_issue else ""
        print(f"  {s.id}  {s.status}  {s.title or ''}{beads}")


def _handle_show(args: object) -> None:
    from ...beads.specs import load_task_spec

    task_id = getattr(args, "id", "").strip()
    if not task_id:
        print("task show: id required", file=sys.stderr)
        sys.exit(2)
    root = _project_root()
    spec = load_task_spec(task_id, root)
    if not spec:
        print(f"Task not found: {task_id}", file=sys.stderr)
        sys.exit(1)
    print(f"id: {spec.id}")
    print(f"title: {spec.title}")
    print(f"status: {spec.status}")
    print(f"workflow: {spec.workflow or 'build'}")
    if spec.beads_issue:
        print(f"beads_issue: {spec.beads_issue}")
    if spec.description:
        print(f"description: {spec.description}")


def _handle_update(args: object) -> None:
    from ...beads.specs import load_task_spec, save_task_spec

    task_id = getattr(args, "id", "").strip()
    status = getattr(args, "status", None)
    if not task_id:
        print("task update: id required", file=sys.stderr)
        sys.exit(2)
    if not status:
        print("task update: --status required", file=sys.stderr)
        sys.exit(2)
    root = _project_root()
    spec = load_task_spec(task_id, root)
    if not spec:
        print(f"Task not found: {task_id}", file=sys.stderr)
        sys.exit(1)
    spec = spec.model_copy(update={"status": status})
    save_task_spec(spec, root)
    print(f"Updated {task_id} status to {status}")


def _handle_close(args: object) -> None:
    from ...beads.specs import load_task_spec, save_task_spec

    task_id = getattr(args, "id", "").strip()
    if not task_id:
        print("task close: id required", file=sys.stderr)
        sys.exit(2)
    root = _project_root()
    spec = load_task_spec(task_id, root)
    if not spec:
        print(f"Task not found: {task_id}", file=sys.stderr)
        sys.exit(1)
    spec = spec.model_copy(update={"status": "done"})
    save_task_spec(spec, root)
    print(f"Closed {task_id}")


def _handle_hydrate(args: object) -> None:
    from ...beads.hydration import hydrate_to_beads

    root = _project_root()
    report = hydrate_to_beads(project_root=root)
    if report.bd_unavailable:
        print("Beads (bd) not available. Install to tools/bd or add bd to PATH.", file=sys.stderr)
        sys.exit(1)
    print(f"created={report.created} skipped={report.skipped} failed={report.failed} deps_added={report.deps_added}")


def _handle_dehydrate(args: object) -> None:
    from ...beads.hydration import dehydrate_from_beads

    root = _project_root()
    updated = dehydrate_from_beads(project_root=root)
    print(f"Updated {updated} spec(s) from Beads.")


def _handle_run(args: object) -> None:
    from ...beads.specs import load_task_spec, save_task_spec

    task_id = getattr(args, "id", "").strip()
    if not task_id:
        print("task run: id required", file=sys.stderr)
        sys.exit(2)
    root = _project_root()
    spec = load_task_spec(task_id, root)
    if not spec:
        print(f"Task not found: {task_id}", file=sys.stderr)
        sys.exit(1)
    workflow_name = (spec.workflow or "build").strip().lower()
    # Map task workflow name to preset
    preset_map = {"build": "rapid", "fix": "fix", "review": "quality", "test": "quality", "full": "full"}
    preset = preset_map.get(workflow_name, "rapid")
    # Update spec to in-progress
    spec = spec.model_copy(update={"status": "in-progress"})
    save_task_spec(spec, root)
    # Run workflow via CLI workflow path (simplified: invoke workflow preset)
    try:
        from ...workflow.executor import WorkflowExecutor
        from ...workflow.preset_loader import PresetLoader
        from ..base import run_async_command

        loader = PresetLoader()
        workflow = loader.load_preset(preset)
        if not workflow:
            print(f"Workflow preset not found: {preset}", file=sys.stderr)
            spec = spec.model_copy(update={"status": "todo"})
            save_task_spec(spec, root)
            sys.exit(1)
        executor = WorkflowExecutor(auto_detect=False, auto_mode=True)
        executor.user_prompt = spec.title or spec.description or spec.id
        target_file = (spec.files or [None])[0] if spec.files else None
        final_state = run_async_command(
            executor.execute(workflow=workflow, target_file=target_file)
        )
        if final_state.status == "completed":
            spec = spec.model_copy(update={"status": "done"})
            save_task_spec(spec, root)
            print(f"Task {task_id} completed.")
        else:
            spec = spec.model_copy(update={"status": "todo"})
            save_task_spec(spec, root)
            print(f"Workflow ended with status: {final_state.status}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        spec = spec.model_copy(update={"status": "todo"})
        save_task_spec(spec, root)
        print(f"Error running workflow: {e}", file=sys.stderr)
        sys.exit(1)
