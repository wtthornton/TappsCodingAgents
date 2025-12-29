#!/usr/bin/env python3
"""
Demo script to trigger a Background Agent execution that will show up in monitoring.

This simulates what happens when a Background Agent is triggered via Cursor.
It creates progress files, runs a command, and produces results that the
monitoring script can detect.
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tapps_agents.core.background_wrapper import run_background_task


async def main():
    """Trigger a demo background agent execution."""
    print("=" * 70)
    print("Triggering Background Agent Demo")
    print("=" * 70)
    print()
    print("This will create progress files and run a command that")
    print("the monitoring script can detect.")
    print()
    
    # Create task ID
    task_id = f"demo-quality-{int(time.time())}"
    agent_id = "quality-analyzer"
    
    print(f"Agent ID: {agent_id}")
    print(f"Task ID: {task_id}")
    print(f"Progress file will be: .tapps-agents/reports/progress-{task_id}.json")
    print()
    print("Starting execution...")
    print()
    
    try:
        # Run a background task using the convenience function
        # This will create progress files automatically
        result = await run_background_task(
            agent_id=agent_id,
            task_id=task_id,
            agent="reviewer",
            command="score",
            args={"files": ["README.md"]},
            use_worktree=False  # Don't create worktree for demo
        )
        
        print()
        print("=" * 70)
        print("Background Agent execution complete!")
        print("=" * 70)
        print()
        print("You should now see activity in the monitoring script:")
        print(f"  - Progress file: .tapps-agents/reports/progress-{task_id}.json")
        print(f"  - Result file: .tapps-agents/reports/{task_id}-*.json")
        print()
        print("Run the monitoring script in another terminal to see the activity:")
        print("  python scripts/monitor_background_agents.py --interval 1")
        print()
        print("Or check the progress file directly:")
        print(f"  cat .tapps-agents/reports/progress-{task_id}.json")
        
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
