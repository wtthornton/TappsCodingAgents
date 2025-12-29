#!/usr/bin/env python3
"""
Quick Background Agents Status Monitor

Shows a snapshot of current background agent activity without continuous monitoring.
Useful for quick status checks.

Usage:
    python scripts/monitor_status.py
    python scripts/monitor_status.py --detailed
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tapps_agents.core.runtime_mode import is_cursor_mode
from tapps_agents.workflow.background_agent_api import BackgroundAgentAPI


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


def load_json_file(file_path: Path) -> Optional[dict]:
    """Load JSON file safely."""
    try:
        if file_path.exists():
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def get_active_tasks(reports_dir: Path) -> list[dict]:
    """Get all active tasks from progress files."""
    if not reports_dir.exists():
        return []
    
    active_tasks = []
    for pf in reports_dir.glob("progress-*.json"):
        progress_data = load_json_file(pf)
        if progress_data:
            status = progress_data.get("status", "unknown")
            if status in ["in_progress", "pending"]:
                active_tasks.append({
                    "file": pf.name,
                    "data": progress_data
                })
    
    return active_tasks


def get_recent_results(reports_dir: Path, limit: int = 5) -> list[dict]:
    """Get recent result files."""
    if not reports_dir.exists():
        return []
    
    result_files = [
        f for f in reports_dir.glob("*.json")
        if not f.name.startswith("progress-")
    ]
    
    # Sort by modification time (newest first)
    result_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    
    results = []
    for rf in result_files[:limit]:
        result_data = load_json_file(rf)
        if result_data:
            mtime = datetime.fromtimestamp(rf.stat().st_mtime)
            results.append({
                "file": rf.name,
                "data": result_data,
                "timestamp": mtime
            })
    
    return results


def get_worktree_info(worktrees_dir: Path) -> list[dict]:
    """Get information about active worktrees."""
    if not worktrees_dir.exists():
        return []
    
    worktrees = []
    for wt in worktrees_dir.iterdir():
        if wt.is_dir():
            # Check for command files
            cmd_files = list(wt.glob("**/.cursor-skill-command.txt"))
            
            # Check for progress file
            progress_file = wt / ".tapps-agents" / "progress.json"
            progress_data = None
            if progress_file.exists():
                progress_data = load_json_file(progress_file)
            
            worktrees.append({
                "name": wt.name,
                "command_count": len(cmd_files),
                "has_progress": progress_file.exists(),
                "progress": progress_data
            })
    
    return worktrees


def print_status(detailed: bool = False):
    """Print current background agent status."""
    project_root = Path.cwd()
    reports_dir = project_root / ".tapps-agents" / "reports"
    worktrees_dir = project_root / ".tapps-agents" / "worktrees"
    
    print("=" * 70)
    print("Background Agents Status")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Runtime mode
    print("[Runtime Mode]")
    print("-" * 70)
    if is_cursor_mode():
        print("[OK] Cursor Mode: ACTIVE")
    else:
        print("[FAIL] Cursor Mode: INACTIVE (Background Agents require Cursor IDE)")
    print()
    
    # Active tasks
    print("[Active Tasks]")
    print("-" * 70)
    active_tasks = get_active_tasks(reports_dir)
    if active_tasks:
        print(f"Found {len(active_tasks)} active task(s):")
        for task in active_tasks:
            data = task["data"]
            task_id = data.get("task_id", "unknown")
            status = data.get("status", "unknown")
            elapsed = data.get("elapsed_seconds", 0)
            
            print(f"  - {task_id}")
            print(f"    Status: {status}")
            if elapsed:
                print(f"    Elapsed: {format_duration(elapsed)}")
            
            if detailed:
                steps = data.get("steps", [])
                if steps:
                    print(f"    Steps: {len(steps)}")
                    last_step = steps[-1] if steps else None
                    if last_step:
                        print(f"    Current: {last_step.get('step', 'N/A')}")
    else:
        print("No active tasks")
    print()
    
    # Worktrees
    print("[Active Worktrees]")
    print("-" * 70)
    worktrees = get_worktree_info(worktrees_dir)
    if worktrees:
        print(f"Found {len(worktrees)} worktree(s):")
        for wt in worktrees:
            print(f"  - {wt['name']}")
            if wt['command_count'] > 0:
                print(f"    Commands: {wt['command_count']}")
            if wt['has_progress']:
                print(f"    Progress: Active")
    else:
        print("No active worktrees")
    print()
    
    # Recent results
    if detailed:
        print("[Recent Results]")
        print("-" * 70)
        recent_results = get_recent_results(reports_dir, limit=5)
        if recent_results:
            print(f"Last {len(recent_results)} result(s):")
            for result in recent_results:
                data = result["data"]
                success = data.get("success", False)
                status_icon = "[OK]" if success else "[FAIL]"
                timestamp = result["timestamp"].strftime("%H:%M:%S")
                print(f"  {status_icon} [{timestamp}] {result['file']}")
        else:
            print("No recent results")
        print()
    
    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Active Tasks: {len(active_tasks)}")
    print(f"Active Worktrees: {len(worktrees)}")
    if detailed:
        print(f"Recent Results: {len(get_recent_results(reports_dir, limit=5))}")
    print()
    print("For continuous monitoring, run:")
    print("  python scripts/monitor_background_agents.py")
    print()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Quick status check for Background Agents"
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed information including recent results"
    )
    
    args = parser.parse_args()
    print_status(detailed=args.detailed)


if __name__ == "__main__":
    main()

