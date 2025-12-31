"""
Background Agent Wrapper

Provides utilities for running TappsCodingAgents commands in Background Agent mode.
Handles Context7 cache sharing, progress reporting, and result delivery.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from ..context7.commands import Context7Commands
from .config import ProjectConfig, load_config
from .progress import create_progress_reporter
from .worktree import WorktreeManager

logger = logging.getLogger(__name__)


class BackgroundAgentWrapper:
    """Wrapper for running agents in Background Agent mode."""

    def __init__(
        self,
        agent_id: str,
        task_id: str,
        config: ProjectConfig | None = None,
        use_worktree: bool = True,
    ):
        """
        Initialize BackgroundAgentWrapper.

        Args:
            agent_id: Unique identifier for the agent
            task_id: Unique identifier for the task
            config: Optional ProjectConfig (loads if not provided)
            use_worktree: If True, use git worktree for isolation
        """
        self.agent_id = agent_id
        self.task_id = task_id
        self.config = config or load_config()
        self.use_worktree = use_worktree

        # Setup paths
        self.project_root = Path.cwd()
        self.output_dir = self.project_root / ".tapps-agents" / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.worktree_manager: WorktreeManager | None = None
        self.worktree_path: Path | None = None
        self.progress_reporter = create_progress_reporter(task_id, self.output_dir)
        self.context7_commands: Context7Commands | None = None

        # Setup worktree if enabled
        if self.use_worktree:
            self.worktree_manager = WorktreeManager(
                self.project_root, self.project_root / ".tapps-agents" / "worktrees"
            )

    async def setup(self) -> dict[str, Any]:
        """
        Setup the background agent environment.

        Returns:
            Setup result dictionary
        """
        print(
            f"[BACKGROUND AGENT] Setting up environment...",
            file=sys.stderr,
            flush=True,
        )
        
        self.progress_reporter.report_step(
            "setup", "in_progress", "Setting up background agent"
        )

        try:
            # Create worktree if enabled
            if self.use_worktree and self.worktree_manager:
                self.worktree_path = self.worktree_manager.create_worktree(
                    self.agent_id, f"agent/{self.agent_id}"
                )
                self.progress_reporter.report_step(
                    "worktree_created",
                    "completed",
                    f"Created worktree at {self.worktree_path}",
                )

            # Initialize Context7 commands
            if self.config.context7 and self.config.context7.enabled:
                self.context7_commands = Context7Commands(
                    project_root=self.worktree_path or self.project_root,
                    config=self.config,
                )
                self.progress_reporter.report_step(
                    "context7_initialized", "completed", "Context7 commands initialized"
                )

            self.progress_reporter.report_step("setup", "completed", "Setup complete")
            
            print(
                f"[BACKGROUND AGENT] Setup complete",
                file=sys.stderr,
                flush=True,
            )

            return {
                "success": True,
                "worktree_path": (
                    str(self.worktree_path) if self.worktree_path else None
                ),
                "output_dir": str(self.output_dir),
            }

        except Exception as e:
            self.progress_reporter.report_step("setup", "failed", f"Setup failed: {e}")
            print(
                f"[BACKGROUND AGENT] Setup failed: {e}",
                file=sys.stderr,
                flush=True,
            )
            return {"success": False, "error": str(e)}

    async def run_command(
        self,
        agent: str,
        command: str,
        args: dict[str, Any],
        output_format: str = "json",
    ) -> dict[str, Any]:
        """
        Run an agent command in background mode.

        Args:
            agent: Agent name (e.g., "reviewer", "improver")
            command: Command name (e.g., "review", "refactor")
            args: Command arguments
            output_format: Output format (json, text)

        Returns:
            Command result dictionary
        """
        # Print visible start indicator
        print(
            f"\n{'='*60}\n"
            f"[BACKGROUND AGENT] Starting: {agent} {command}\n"
            f"{'='*60}",
            file=sys.stderr,
            flush=True,
        )
        
        self.progress_reporter.report_step(
            "command_start", "in_progress", f"Running {agent} {command}"
        )

        try:
            # Import agent dynamically
            agent_module = __import__(
                f"tapps_agents.agents.{agent}.agent", fromlist=[f"{agent.title()}Agent"]
            )
            agent_class = getattr(agent_module, f"{agent.title()}Agent")

            # Create agent instance
            agent_instance = agent_class()
            await agent_instance.activate()

            # Show running indicator for long operations
            print(
                f"[BACKGROUND AGENT] Running {agent} {command}...",
                file=sys.stderr,
                flush=True,
            )

            # Run command
            result = await agent_instance.run(command, **args)

            # Save result
            result_file = self.output_dir / f"{self.task_id}-{agent}-{command}.json"
            with open(result_file, "w") as f:
                json.dump(result, f, indent=2)

            self.progress_reporter.report_step(
                "command_complete",
                "completed",
                f"Command completed, result saved to {result_file}",
                {"result_file": str(result_file)},
            )

            await agent_instance.close()

            # Print visible end indicator
            print(
                f"\n{'='*60}\n"
                f"[BACKGROUND AGENT] Completed: {agent} {command}\n"
                f"Result saved to: {result_file}\n"
                f"{'='*60}\n",
                file=sys.stderr,
                flush=True,
            )

            return {"success": True, "result": result, "result_file": str(result_file)}

        except Exception as e:
            self.progress_reporter.report_step(
                "command_failed", "failed", f"Command failed: {e}"
            )
            
            # Print visible error indicator
            print(
                f"\n{'='*60}\n"
                f"[BACKGROUND AGENT] Failed: {agent} {command}\n"
                f"Error: {e}\n"
                f"{'='*60}\n",
                file=sys.stderr,
                flush=True,
            )
            
            return {"success": False, "error": str(e)}

    async def cleanup(
        self, auto_cleanup_others: bool = False, retention_days: int = 7
    ) -> dict[str, Any]:
        """
        Cleanup the background agent environment.

        Args:
            auto_cleanup_others: If True, also cleanup other old worktrees
            retention_days: Retention period in days for auto-cleanup (default: 7)

        Returns:
            Cleanup result dictionary
        """
        self.progress_reporter.report_step("cleanup", "in_progress", "Cleaning up")

        try:
            # Mark worktree as completed
            if self.use_worktree and self.worktree_path:
                completion_file = (
                    self.worktree_path / ".tapps-agents" / "completed.txt"
                )
                completion_file.parent.mkdir(parents=True, exist_ok=True)
                completion_file.write_text(
                    f"Completed at {datetime.now().isoformat()}\n"
                )

            # Remove worktree if enabled
            if self.use_worktree and self.worktree_manager:
                self.worktree_manager.remove_worktree(self.agent_id)
                self.progress_reporter.report_step(
                    "worktree_removed", "completed", "Worktree removed"
                )

            # Auto-cleanup other old worktrees if requested
            if auto_cleanup_others and self.worktree_manager:
                cleaned_count = self.worktree_manager.auto_cleanup(
                    retention_days=retention_days, keep_active=True
                )
                if cleaned_count > 0:
                    self.progress_reporter.report_step(
                        "auto_cleanup",
                        "completed",
                        f"Cleaned up {cleaned_count} old worktree(s)",
                    )

            self.progress_reporter.report_step(
                "cleanup", "completed", "Cleanup complete"
            )

            return {"success": True}

        except Exception as e:
            self.progress_reporter.report_step(
                "cleanup", "failed", f"Cleanup failed: {e}"
            )
            return {"success": False, "error": str(e)}

    def get_progress(self) -> dict[str, Any]:
        """
        Get current progress.

        Returns:
            Progress data dictionary
        """
        return self.progress_reporter.get_progress()


async def run_background_task(
    agent_id: str,
    task_id: str,
    agent: str,
    command: str,
    args: dict[str, Any],
    use_worktree: bool = True,
) -> dict[str, Any]:
    """
    Convenience function to run a background task.

    Args:
        agent_id: Unique identifier for the agent
        task_id: Unique identifier for the task
        agent: Agent name
        command: Command name
        args: Command arguments
        use_worktree: If True, use git worktree for isolation

    Returns:
        Task result dictionary
    """
    # Print visible task start indicator
    print(
        f"\n{'='*60}\n"
        f"[BACKGROUND AGENT TASK] Starting\n"
        f"Agent ID: {agent_id}\n"
        f"Task ID: {task_id}\n"
        f"Command: {agent} {command}\n"
        f"{'='*60}\n",
        file=sys.stderr,
        flush=True,
    )
    
    wrapper = BackgroundAgentWrapper(agent_id, task_id, use_worktree=use_worktree)

    try:
        # Setup
        setup_result = await wrapper.setup()
        if not setup_result.get("success"):
            print(
                f"\n{'='*60}\n"
                f"[BACKGROUND AGENT TASK] Setup Failed\n"
                f"Error: {setup_result.get('error', 'Unknown error')}\n"
                f"{'='*60}\n",
                file=sys.stderr,
                flush=True,
            )
            return setup_result

        # Run command
        result = await wrapper.run_command(agent, command, args)

        # Complete
        wrapper.progress_reporter.complete(result)

        # Print visible task completion indicator
        print(
            f"\n{'='*60}\n"
            f"[BACKGROUND AGENT TASK] Completed Successfully\n"
            f"Task ID: {task_id}\n"
            f"{'='*60}\n",
            file=sys.stderr,
            flush=True,
        )

        return result

    except Exception as e:
        wrapper.progress_reporter.fail(str(e))
        
        # Print visible task failure indicator
        print(
            f"\n{'='*60}\n"
            f"[BACKGROUND AGENT TASK] Failed\n"
            f"Task ID: {task_id}\n"
            f"Error: {e}\n"
            f"{'='*60}\n",
            file=sys.stderr,
            flush=True,
        )
        
        return {"success": False, "error": str(e)}

    finally:
        # Cleanup
        await wrapper.cleanup()


if __name__ == "__main__":
    # CLI entry point for background agent wrapper
    import argparse

    parser = argparse.ArgumentParser(description="Background Agent Wrapper")
    parser.add_argument("--agent-id", required=True, help="Agent identifier")
    parser.add_argument("--task-id", required=True, help="Task identifier")
    parser.add_argument("--agent", required=True, help="Agent name")
    parser.add_argument("--command", required=True, help="Command name")
    parser.add_argument("--args", help="Command arguments (JSON)")
    parser.add_argument("--no-worktree", action="store_true", help="Disable worktree")

    args = parser.parse_args()

    command_args = json.loads(args.args) if args.args else {}

    result = asyncio.run(
        run_background_task(
            args.agent_id,
            args.task_id,
            args.agent,
            args.command,
            command_args,
            use_worktree=not args.no_worktree,
        )
    )

    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("success") else 1)
