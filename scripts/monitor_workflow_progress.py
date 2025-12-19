#!/usr/bin/env python3
"""
Workflow Progress Monitor

Monitors workflow execution and reports progress to the user.
Designed to work with Cursor mode to maintain communication during execution.

Usage:
    python scripts/monitor_workflow_progress.py [workflow_id]
    python scripts/monitor_workflow_progress.py --latest
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Optional


def find_latest_workflow_state(state_dir: Path) -> Optional[Path]:
    """Find the latest workflow state file."""
    last_file = state_dir / "last.json"
    if last_file.exists():
        try:
            with open(last_file) as f:
                last_data = json.load(f)
                state_file = Path(last_data.get("state_file", ""))
                if state_file.exists():
                    return state_file
        except Exception:
            pass
    
    # Fallback: find most recent state file
    state_files = list(state_dir.glob("*.json"))
    if not state_files:
        return None
    
    # Exclude metadata and last.json
    state_files = [f for f in state_files if f.name not in ["last.json"] and not f.name.endswith(".meta.json")]
    
    if not state_files:
        return None
    
    # Return most recently modified
    return max(state_files, key=lambda p: p.stat().st_mtime)


def load_workflow_state(state_file: Path) -> Optional[dict]:
    """Load workflow state from file."""
    try:
        with open(state_file) as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading state file: {e}", file=sys.stderr)
        return None


def format_progress(state: dict) -> str:
    """Format workflow progress as a readable string."""
    workflow_id = state.get("workflow_id", "unknown")
    status = state.get("status", "unknown")
    current_step = state.get("current_step", "N/A")
    completed_steps = state.get("completed_steps", [])
    total_steps = len(completed_steps) + (1 if current_step != "N/A" else 0)
    
    # Try to get total from step_executions
    step_executions = state.get("step_executions", [])
    if step_executions:
        # Count unique step IDs
        all_step_ids = set()
        for se in step_executions:
            if se.get("step_id"):
                all_step_ids.add(se["step_id"])
        if current_step and current_step != "N/A":
            all_step_ids.add(current_step)
        total_steps = max(total_steps, len(all_step_ids))
    
    completed_count = len(completed_steps)
    progress_pct = (completed_count / total_steps * 100) if total_steps > 0 else 0
    
    # Get recent artifacts
    artifacts = state.get("artifacts", {})
    artifact_count = len(artifacts)
    
    # Get last step execution info
    last_step = None
    if step_executions:
        last_step = step_executions[-1]
    
    lines = [
        f"Workflow: {workflow_id}",
        f"Status: {status.upper()}",
        f"Progress: {completed_count}/{total_steps} steps ({progress_pct:.1f}%)",
        f"Current Step: {current_step}",
        f"Artifacts Created: {artifact_count}",
    ]
    
    if last_step:
        agent = last_step.get("agent", "N/A")
        action = last_step.get("action", "N/A")
        step_status = last_step.get("status", "N/A")
        lines.append(f"Last Step: {agent}/{action} ({step_status})")
    
    return "\n".join(lines)


def monitor_workflow(workflow_id: Optional[str] = None, interval: float = 2.0):
    """Monitor workflow progress."""
    from tapps_agents.core.config import load_config
    
    config = load_config()
    project_root = Path.cwd()
    state_dir = project_root / ".tapps-agents" / "workflow-state"
    
    if not state_dir.exists():
        print(f"State directory not found: {state_dir}", file=sys.stderr)
        print("Make sure you've run a workflow first.", file=sys.stderr)
        return
    
    # Find state file
    if workflow_id:
        # Try to find by workflow_id
        state_file = state_dir / f"{workflow_id}-*.json"
        matches = list(state_dir.glob(f"{workflow_id}-*.json"))
        if matches:
            state_file = matches[0]
        else:
            print(f"Workflow {workflow_id} not found", file=sys.stderr)
            return
    else:
        # Find latest
        state_file = find_latest_workflow_state(state_dir)
        if not state_file:
            print("No workflow state files found.", file=sys.stderr)
            return
    
    print(f"Monitoring workflow state: {state_file.name}")
    print("Press Ctrl+C to stop monitoring\n")
    
    last_status = None
    last_completed_count = -1
    
    try:
        while True:
            state = load_workflow_state(state_file)
            if not state:
                time.sleep(interval)
                continue
            
            current_status = state.get("status", "unknown")
            completed_count = len(state.get("completed_steps", []))
            
            # Only print if status changed or progress updated
            if current_status != last_status or completed_count != last_completed_count:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}]")
                print(format_progress(state))
                print("-" * 60)
                
                last_status = current_status
                last_completed_count = completed_count
                
                # Check if workflow is complete
                if current_status in ["completed", "failed", "paused"]:
                    print(f"\nWorkflow {current_status.upper()}!")
                    break
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Monitor workflow execution progress"
    )
    parser.add_argument(
        "workflow_id",
        nargs="?",
        help="Workflow ID to monitor (optional, defaults to latest)"
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Monitor the latest workflow"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Polling interval in seconds (default: 2.0)"
    )
    
    args = parser.parse_args()
    
    workflow_id = None if args.latest or not args.workflow_id else args.workflow_id
    
    monitor_workflow(workflow_id=workflow_id, interval=args.interval)


if __name__ == "__main__":
    main()

