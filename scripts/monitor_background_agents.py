#!/usr/bin/env python3
"""
Background Agents Monitor

Monitors Background Agent execution in real-time by watching:
- Progress files (.tapps-agents/reports/progress-*.json)
- Worktrees (.tapps-agents/worktrees/)
- Result files (.tapps-agents/reports/*.json)
- Terminal output indicators

Usage:
    python scripts/monitor_background_agents.py
    python scripts/monitor_background_agents.py --interval 2
    python scripts/monitor_background_agents.py --task-id <task-id>
"""

import json
import sys
import time
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Set
from collections import defaultdict

# Safe print function that handles encoding errors
def safe_print(*args, **kwargs):
    """Print with encoding error handling."""
    # Ensure flush is in kwargs
    if 'flush' not in kwargs:
        kwargs['flush'] = True
    
    try:
        # Try normal print first
        print(*args, **kwargs)
        sys.stdout.flush()
    except (UnicodeEncodeError, UnicodeDecodeError) as e:
        # Fallback: convert to ASCII-safe string
        message = ' '.join(str(arg) for arg in args)
        # Replace any problematic characters
        safe_message = message.encode('ascii', 'replace').decode('ascii')
        try:
            print(safe_message, flush=True)
            sys.stdout.flush()
        except Exception:
            # Last resort: write directly to buffer
            try:
                sys.stdout.buffer.write(safe_message.encode('ascii'))
                sys.stdout.buffer.write(b'\n')
                sys.stdout.buffer.flush()
            except Exception:
                # If all else fails, write to stderr
                try:
                    sys.stderr.write(f"Error printing: {safe_message}\n")
                    sys.stderr.flush()
                except Exception:
                    pass

# Fix Windows encoding issues
if sys.platform == "win32":
    try:
        # Set UTF-8 encoding for stdout/stderr on Windows
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        else:
            # Fallback for older Python versions
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        # If encoding setup fails, use safe_print for all output
        pass


def load_json_file(file_path: Path) -> Optional[dict]:
    """Load JSON file safely."""
    try:
        if file_path.exists():
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        return None
    return None


def get_progress_files(reports_dir: Path) -> List[Path]:
    """Get all progress files."""
    if not reports_dir.exists():
        return []
    return list(reports_dir.glob("progress-*.json"))


def get_result_files(reports_dir: Path) -> List[Path]:
    """Get all result files (excluding progress files)."""
    if not reports_dir.exists():
        return []
    return [f for f in reports_dir.glob("*.json") if not f.name.startswith("progress-")]


def get_worktrees(worktrees_dir: Path) -> List[Path]:
    """Get all active worktrees."""
    if not worktrees_dir.exists():
        return []
    return [d for d in worktrees_dir.iterdir() if d.is_dir()]


def format_progress_status(progress_data: dict) -> str:
    """Format progress file status."""
    task_id = progress_data.get("task_id", "unknown")
    status = progress_data.get("status", "unknown")
    elapsed = progress_data.get("elapsed_seconds", 0)
    
    lines = [
        f"Task ID: {task_id}",
        f"Status: {status.upper()}",
    ]
    
    if elapsed:
        lines.append(f"Elapsed: {elapsed:.1f}s")
    
    steps = progress_data.get("steps", [])
    if steps:
        last_step = steps[-1]
        step_name = last_step.get("step", "N/A")
        step_status = last_step.get("status", "N/A")
        step_message = last_step.get("message", "")
        lines.append(f"Current Step: {step_name} ({step_status})")
        if step_message:
            lines.append(f"Message: {step_message}")
    
    error = progress_data.get("error")
    if error:
        lines.append(f"ERROR: {error}")
    
    return "\n".join(lines)


def format_result_status(result_data: dict, file_path: Path) -> str:
    """Format result file status."""
    success = result_data.get("success", False)
    # Use ASCII-safe characters for Windows compatibility
    status_icon = "[OK]" if success else "[FAIL]"
    
    lines = [
        f"{status_icon} Result: {file_path.name}",
        f"Success: {success}",
    ]
    
    if not success:
        error = result_data.get("error", "Unknown error")
        lines.append(f"Error: {error}")
    
    return "\n".join(lines)


def format_worktree_status(worktree_path: Path) -> str:
    """Format worktree status."""
    lines = [f"[WORKTREE] Worktree: {worktree_path.name}"]
    
    # Check for command files
    cmd_files = list(worktree_path.glob("**/.cursor-skill-command.txt"))
    if cmd_files:
        lines.append(f"  Commands: {len(cmd_files)}")
    
    # Check for progress files in worktree
    progress_file = worktree_path / ".tapps-agents" / "progress.json"
    if progress_file.exists():
        lines.append("  Progress file exists")
    
    return "\n".join(lines)


def monitor_background_agents(
    task_id: Optional[str] = None,
    interval: float = 2.0,
    watch_all: bool = True
):
    """Monitor Background Agent execution."""
    project_root = Path.cwd()
    reports_dir = project_root / ".tapps-agents" / "reports"
    worktrees_dir = project_root / ".tapps-agents" / "worktrees"
    
    # Force flush output immediately
    sys.stdout.flush()
    sys.stderr.flush()
    
    safe_print("=" * 70)
    safe_print("Background Agents Monitor")
    safe_print("=" * 70)
    safe_print(f"Monitoring directory: {reports_dir}")
    safe_print(f"Worktrees directory: {worktrees_dir}")
    if task_id:
        safe_print(f"Task ID filter: {task_id}")
    safe_print(f"Polling interval: {interval}s")
    safe_print("Press Ctrl+C to stop monitoring")
    safe_print("")
    sys.stdout.flush()
    
    # Show initial status
    if reports_dir.exists():
        progress_count = len(get_progress_files(reports_dir))
        result_count = len(get_result_files(reports_dir))
        safe_print(f"Found {progress_count} progress file(s), {result_count} result file(s)")
    else:
        safe_print(f"Reports directory does not exist yet: {reports_dir}")
    
    if worktrees_dir.exists():
        worktree_count = len(get_worktrees(worktrees_dir))
        safe_print(f"Found {worktree_count} worktree(s)")
    else:
        safe_print(f"Worktrees directory does not exist yet: {worktrees_dir}")
    
    safe_print("Waiting for background agent activity...")
    safe_print("")
    sys.stdout.flush()
    
    # Track seen files to detect new ones
    seen_progress_files: Set[str] = set()
    seen_result_files: Set[str] = set()
    seen_worktrees: Set[str] = set()
    
    # Track last status for each task
    last_status: Dict[str, dict] = {}
    
    try:
        while True:
            timestamp = datetime.now().strftime('%H:%M:%S')
            updates = []
            
            # Check progress files
            progress_files = get_progress_files(reports_dir)
            for pf in progress_files:
                file_key = pf.name
                
                # Filter by task_id if specified
                if task_id and task_id not in file_key:
                    continue
                
                progress_data = load_json_file(pf)
                if progress_data:
                    task_id_from_file = progress_data.get("task_id", "unknown")
                    
                    # Check if this is a new file or status changed
                    is_new = file_key not in seen_progress_files
                    status_changed = False
                    
                    if file_key in last_status:
                        old_status = last_status[file_key].get("status")
                        new_status = progress_data.get("status")
                        status_changed = old_status != new_status
                    
                    if is_new or status_changed:
                        seen_progress_files.add(file_key)
                        last_status[file_key] = progress_data
                        
                        # Use ASCII-safe status indicators
                        status = progress_data.get("status", "unknown")
                        if status == "in_progress":
                            status_icon = "[RUNNING]"
                        elif status == "completed":
                            status_icon = "[COMPLETE]"
                        elif status == "failed":
                            status_icon = "[FAILED]"
                        else:
                            status_icon = "[STATUS]"
                        
                        updates.append((
                            timestamp,
                            f"{status_icon} Progress Update",
                            format_progress_status(progress_data)
                        ))
            
            # Check result files
            result_files = get_result_files(reports_dir)
            for rf in result_files:
                file_key = rf.name
                
                # Filter by task_id if specified
                if task_id and task_id not in file_key:
                    continue
                
                if file_key not in seen_result_files:
                    seen_result_files.add(file_key)
                    result_data = load_json_file(rf)
                    if result_data:
                        updates.append((
                            timestamp,
                            "[RESULT] New Result File",
                            format_result_status(result_data, rf)
                        ))
            
            # Check worktrees
            worktrees = get_worktrees(worktrees_dir)
            for wt in worktrees:
                worktree_key = wt.name
                
                if worktree_key not in seen_worktrees:
                    seen_worktrees.add(worktree_key)
                    updates.append((
                        timestamp,
                        "[WORKTREE] New Worktree",
                        format_worktree_status(wt)
                    ))
            
            # Print updates
            if updates:
                safe_print(f"\n[{timestamp}]")
                safe_print("-" * 70)
                for ts, title, content in updates:
                    safe_print(f"\n{title}")
                    safe_print(content)
                safe_print("-" * 70)
            
            # Show heartbeat every 10 seconds if no updates
            elif len(seen_progress_files) == 0 and len(seen_worktrees) == 0:
                # Show heartbeat to indicate monitor is running
                if int(time.time()) % 10 == 0:
                    safe_print(f"[{timestamp}] Monitoring... (no activity yet)")
                    sys.stdout.flush()
            elif len(seen_progress_files) > 0 or len(seen_worktrees) > 0:
                # Only print summary occasionally
                if int(time.time()) % 10 == 0:
                    active_tasks = sum(
                        1 for pf in progress_files
                        if load_json_file(pf) and 
                        load_json_file(pf).get("status") == "in_progress"
                    )
                    safe_print(f"[{timestamp}] Monitoring... ({active_tasks} active task(s))")
                    sys.stdout.flush()
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        safe_print("\n\n" + "=" * 70)
        safe_print("Monitoring stopped by user.")
        safe_print("=" * 70)
        
        # Final summary
        safe_print("\nSummary:")
        safe_print(f"  Progress files monitored: {len(seen_progress_files)}")
        safe_print(f"  Result files found: {len(seen_result_files)}")
        safe_print(f"  Worktrees detected: {len(seen_worktrees)}")
        
        # Show final status of all tasks
        if seen_progress_files:
            safe_print("\nFinal Task Status:")
            for pf in get_progress_files(reports_dir):
                if task_id and task_id not in pf.name:
                    continue
                progress_data = load_json_file(pf)
                if progress_data:
                    task_id_val = progress_data.get("task_id", "unknown")
                    status = progress_data.get("status", "unknown")
                    # Use ASCII-safe status indicators
                    if status == "completed":
                        status_icon = "[OK]"
                    elif status == "failed":
                        status_icon = "[FAIL]"
                    elif status == "in_progress":
                        status_icon = "[RUN]"
                    else:
                        status_icon = "[?]"
                    safe_print(f"  {status_icon} {task_id_val}: {status}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Monitor Background Agent execution in real-time"
    )
    parser.add_argument(
        "--task-id",
        type=str,
        help="Monitor specific task ID (optional)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Polling interval in seconds (default: 2.0)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        default=True,
        help="Monitor all tasks (default: True)"
    )
    
    args = parser.parse_args()
    
    monitor_background_agents(
        task_id=args.task_id,
        interval=args.interval,
        watch_all=args.all
    )


if __name__ == "__main__":
    main()

