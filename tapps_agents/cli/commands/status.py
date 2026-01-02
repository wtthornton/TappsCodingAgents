"""
Unified Status Command

Consolidates monitoring functionality from multiple scripts into a single command.
Shows worktrees, progress files, and recent results.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from ...core.runtime_mode import detect_runtime_mode, is_cursor_mode
from ...core.unified_state import UnifiedStateManager
from ...core.worktree import WorktreeManager
# Background Agent API removed


def load_json_file(file_path: Path) -> dict[str, Any] | None:
    """Load JSON file safely."""
    try:
        if file_path.exists():
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def get_progress_files(reports_dir: Path) -> list[Path]:
    """Get all progress files (legacy - Phase 3 uses unified state)."""
    if not reports_dir.exists():
        return []
    return list(reports_dir.glob("progress-*.json"))


def get_result_files(reports_dir: Path) -> list[Path]:
    """Get all result files (legacy - Phase 3 uses unified state)."""
    if not reports_dir.exists():
        return []
    return [f for f in reports_dir.glob("*.json") if not f.name.startswith("progress-")]


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds / 60:.1f}m"
    else:
        return f"{seconds / 3600:.1f}h"


def handle_status_command(
    detailed: bool = False,
    worktrees_only: bool = False,
    format: str = "text",
) -> None:
    """
    Handle the unified status command.

    Args:
        detailed: Show detailed information
        worktrees_only: Show only worktree information
        format: Output format (text or json)
    """
    project_root = Path.cwd()
    reports_dir = project_root / ".tapps-agents" / "reports"
    worktrees_dir = project_root / ".tapps-agents" / "worktrees"
    state_dir = project_root / ".tapps-agents" / "workflow-state"
    unified_state_dir = project_root / ".tapps-agents" / "state"  # Phase 3: Unified state
    # Background Agents removed - no longer checked
    
    # Phase 3: Initialize UnifiedStateManager
    unified_state_manager = UnifiedStateManager(state_dir=unified_state_dir)

    status_data: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "runtime_mode": detect_runtime_mode().value,
        "is_cursor_mode": is_cursor_mode(),
    }

    # 1. Runtime Mode
    if not worktrees_only:
        status_data["runtime"] = {
            "mode": detect_runtime_mode().value,
            "is_cursor_mode": is_cursor_mode(),
        }
        if is_cursor_mode():
            cursor_vars = [
                "CURSOR",
                "CURSOR_IDE",
                "CURSOR_SESSION_ID",
                "CURSOR_WORKSPACE_ROOT",
                "CURSOR_TRACE_ID",
            ]
            found = [v for v in cursor_vars if os.getenv(v)]
            status_data["runtime"]["cursor_env_vars"] = found

    # 2. Worktrees (Background Agents removed)
    worktree_manager = WorktreeManager(project_root, worktrees_dir)
    worktrees = worktree_manager.list_worktrees()
    status_data["worktrees"] = {
        "count": len(worktrees),
        "active": [],
    }

    for agent_id, worktree_path in worktrees.items():
        worktree_info: dict[str, Any] = {
            "id": agent_id,
            "path": str(worktree_path),
        }

        # Check for command files
        cmd_files = list(worktree_path.glob("**/.cursor-skill-command.txt"))
        worktree_info["command_files"] = len(cmd_files)

        # Check for progress files
        progress_file = worktree_path / ".tapps-agents" / "progress.json"
        if progress_file.exists():
            progress_data = load_json_file(progress_file)
            if progress_data:
                worktree_info["progress"] = {
                    "status": progress_data.get("status", "unknown"),
                    "elapsed_seconds": progress_data.get("elapsed_seconds", 0),
                }

        # Check for completion
        completion_file = worktree_path / ".tapps-agents" / "completed.txt"
        worktree_info["completed"] = completion_file.exists()

        status_data["worktrees"]["active"].append(worktree_info)

    # 4. Unified State (Phase 3: Replaces progress, results, and workflow state)
    if not worktrees_only:
        unified_states = unified_state_manager.list_states()
        status_data["unified_state"] = {
            "count": len(unified_states),
            "active": [],
            "completed": [],
            "failed": [],
        }
        
        for state in unified_states:
            state_info = {
                "task_id": state.task_id,
                "workflow_id": state.workflow_id,
                "status": state.status,
                "elapsed_seconds": state.to_dict().get("elapsed_seconds", 0),
                "steps_count": len(state.steps),
            }
            if detailed:
                state_info["data"] = state.to_dict()
            
            # Categorize by status
            if state.status == "completed":
                status_data["unified_state"]["completed"].append(state_info)
            elif state.status == "failed":
                status_data["unified_state"]["failed"].append(state_info)
            else:
                status_data["unified_state"]["active"].append(state_info)
        
        # Sort by elapsed time (most recent first)
        for category in ["active", "completed", "failed"]:
            status_data["unified_state"][category].sort(
                key=lambda x: x.get("elapsed_seconds", 0), reverse=True
            )
    
    # 5. Legacy Progress Files (for backward compatibility)
    if not worktrees_only:
        progress_files = get_progress_files(reports_dir)
        status_data["legacy_progress"] = {
            "count": len(progress_files),
            "note": "Phase 3: Use unified_state instead",
        }

    # 6. Legacy Result Files (for backward compatibility)
    if not worktrees_only:
        result_files = get_result_files(reports_dir)
        status_data["legacy_results"] = {
            "count": len(result_files),
            "note": "Phase 3: Use unified_state instead",
        }

    # 6. Workflow State
    if not worktrees_only and detailed:
        status_data["workflow_state"] = {"count": 0, "files": []}
        if state_dir.exists():
            state_files = list(state_dir.glob("*.json"))
            status_data["workflow_state"]["count"] = len(state_files)
            for sf in state_files[:5]:
                status_data["workflow_state"]["files"].append(sf.name)

    # Background Agent API removed - no API status to check

    # Output
    if format == "json":
        print(json.dumps(status_data, indent=2))
    else:
        _print_text_status(status_data, detailed, worktrees_only)


def _print_text_status(
    status_data: dict[str, Any], detailed: bool, worktrees_only: bool
) -> None:
    """Print status in human-readable text format."""
    print("=" * 70)
    print("TappsCodingAgents Status")
    print("=" * 70)
    print()

    if not worktrees_only:
        # Runtime Mode
        print("[1] Runtime Mode")
        print("-" * 70)
        print(f"Mode: {status_data['runtime']['mode']}")
        print(f"Cursor Mode: {status_data['runtime']['is_cursor_mode']}")
        if status_data["runtime"].get("cursor_env_vars"):
            print(f"Cursor Env Vars: {', '.join(status_data['runtime']['cursor_env_vars'])}")
        print()

    # Worktrees
    print("[2] Active Worktrees")
    print("-" * 70)
    if status_data["worktrees"]["count"] > 0:
        print(f"[ACTIVE] Found {status_data['worktrees']['count']} worktree(s):")
        for wt in status_data["worktrees"]["active"]:
            print(f"  - {wt['id']}")
            if wt.get("command_files", 0) > 0:
                print(f"    -> {wt['command_files']} command file(s)")
            if wt.get("progress"):
                progress = wt["progress"]
                print(f"    -> Status: {progress['status']}")
                if progress.get("elapsed_seconds"):
                    print(f"    -> Elapsed: {format_duration(progress['elapsed_seconds'])}")
            if wt.get("completed"):
                print("    -> [COMPLETED]")
    else:
        print("[IDLE] No active worktrees found")
    print()

    if not worktrees_only:
        # Progress Files
        print("[3] Progress Files")
        print("-" * 70)
        if status_data["progress"]["count"] > 0:
            print(f"[ACTIVE] Found {status_data['progress']['count']} progress file(s):")
            for pf in status_data["progress"]["files"][:5]:
                print(f"  - {pf['file']} (Task: {pf['task_id']}, Status: {pf['status']})")
                if pf.get("elapsed_seconds"):
                    print(f"    -> Elapsed: {format_duration(pf['elapsed_seconds'])}")
            if status_data["progress"]["count"] > 5:
                print(f"  ... and {status_data['progress']['count'] - 5} more")
        else:
            print("[IDLE] No progress files found")
        print()

        # Recent Results
        print("[4] Recent Results")
        print("-" * 70)
        if status_data["results"]["count"] > 0:
            print(f"[ACTIVE] Found {status_data['results']['count']} result file(s):")
            for rf in status_data["results"]["recent"][:5]:
                status_icon = "[OK]" if rf["success"] else "[FAIL]"
                print(f"  {status_icon} {rf['file']} ({rf['timestamp']})")
            if status_data["results"]["count"] > 5:
                print(f"  ... and {status_data['results']['count'] - 5} more")
        else:
            print("[IDLE] No result files found")
        print()

        # Summary
        print("=" * 70)
        print("Summary")
        print("=" * 70)
        if status_data["runtime"]["is_cursor_mode"]:
            print("[CURSOR MODE] Cursor IDE integration active")
            if status_data["worktrees"]["count"] > 0:
                print("[ACTIVE] Active worktrees detected")
            else:
                print("[IDLE] No active worktrees")
        else:
            print("[HEADLESS MODE] Running in headless mode")
        print()

