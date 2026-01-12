"""
Multi-Agent Orchestrator

Coordinates parallel execution of multiple agents with conflict resolution,
result aggregation, and performance monitoring.
"""

import asyncio
import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import ProjectConfig, load_config
from .performance_monitor import PerformanceMonitor
from .progress import ProgressReporter
from .worktree import WorktreeManager

logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:
    """Orchestrates parallel execution of multiple agents."""

    def __init__(
        self,
        project_root: Path | None = None,
        config: ProjectConfig | None = None,
        max_parallel: int = 8,
    ):
        """
        Initialize MultiAgentOrchestrator.

        Args:
            project_root: Project root directory
            config: Optional ProjectConfig
            max_parallel: Maximum number of parallel agents
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.config = config or load_config()
        self.max_parallel = max_parallel

        # Initialize components
        self.worktree_manager = WorktreeManager(
            self.project_root, self.project_root / ".tapps-agents" / "worktrees"
        )

        self.output_dir = self.project_root / ".tapps-agents" / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Execution tracking
        self.active_tasks: dict[str, asyncio.Task] = {}
        self.results: dict[str, Any] = {}
        self.performance_metrics: dict[str, Any] = {}

    async def execute_parallel(
        self, agent_tasks: list[dict[str, Any]], task_id: str | None = None
    ) -> dict[str, Any]:
        """
        Execute multiple agent tasks in parallel.

        Args:
            agent_tasks: List of agent task definitions
            task_id: Optional task identifier for progress tracking

        Returns:
            Aggregated results dictionary
        """
        task_id = task_id or f"multi-agent-{int(time.time())}"
        progress_reporter = ProgressReporter(task_id, self.output_dir)
        performance_monitor = PerformanceMonitor(task_id, self.output_dir)

        performance_monitor.start()
        progress_reporter.report_step(
            "multi_agent_start",
            "in_progress",
            f"Starting parallel execution of {len(agent_tasks)} agents",
        )

        start_time = time.time()

        try:
            # Create worktrees for each agent
            worktree_paths = {}
            for i, task in enumerate(agent_tasks):
                agent_id = task.get("agent_id", f"agent-{i}")
                worktree_path = self.worktree_manager.create_worktree(
                    agent_id, f"agent/{agent_id}"
                )
                worktree_paths[agent_id] = worktree_path

            progress_reporter.report_step(
                "worktrees_created",
                "completed",
                f"Created {len(worktree_paths)} worktrees",
            )

            # Execute agents in parallel with semaphore limit
            semaphore = asyncio.Semaphore(self.max_parallel)

            async def execute_agent_task(task: dict[str, Any]) -> dict[str, Any]:
                """Execute a single agent task."""
                agent_id = task.get("agent_id", "unknown")
                async with semaphore:
                    task_start = time.time()
                    try:
                        result = await self._execute_agent_task(
                            task, worktree_paths.get(agent_id)
                        )
                        task_duration = time.time() - task_start

                        # Record performance metrics
                        agent_name = task.get("agent", "unknown")
                        performance_monitor.record_agent(
                            agent_id,
                            agent_name,
                            task_duration,
                            result.get("success", False),
                        )

                        self.performance_metrics[agent_id] = {
                            "duration": task_duration,
                            "success": result.get("success", False),
                        }

                        return result
                    except Exception as e:
                        task_duration = time.time() - task_start
                        logger.error(f"Agent {agent_id} failed: {e}")

                        # Record failed agent
                        agent_name = task.get("agent", "unknown")
                        performance_monitor.record_agent(
                            agent_id, agent_name, task_duration, False, str(e)
                        )

                        self.performance_metrics[agent_id] = {
                            "duration": task_duration,
                            "success": False,
                            "error": str(e),
                        }

                        return {"agent_id": agent_id, "success": False, "error": str(e)}

            # Execute all tasks
            progress_reporter.report_step(
                "execution_start", "in_progress", "Executing agents in parallel"
            )

            results = await asyncio.gather(
                *[execute_agent_task(task) for task in agent_tasks]
            )

            # Aggregate results
            aggregated = self._aggregate_results(agent_tasks, results)

            total_duration = time.time() - start_time

            progress_reporter.report_step(
                "execution_complete",
                "completed",
                f"Completed in {total_duration:.2f}s",
                {
                    "total_duration": total_duration,
                    "agents_executed": len(agent_tasks),
                    "successful": sum(1 for r in results if r.get("success")),
                    "failed": sum(1 for r in results if not r.get("success")),
                },
            )

            # Save aggregated results
            result_file = self.output_dir / f"{task_id}-aggregated.json"
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(aggregated, f, indent=2)

            # Finish performance monitoring
            performance_monitor.finish(self.max_parallel)
            performance_summary = performance_monitor.get_summary()

            aggregated["result_file"] = str(result_file)
            aggregated["performance_metrics"] = self.performance_metrics
            aggregated["performance_summary"] = performance_summary
            aggregated["total_duration"] = total_duration

            progress_reporter.complete(aggregated)

            # Cleanup worktrees
            await self._cleanup_worktrees(worktree_paths)

            return aggregated

        except Exception as e:
            progress_reporter.fail(str(e))
            logger.error(f"Multi-agent execution failed: {e}")

            # Cleanup on error
            await self._cleanup_worktrees(
                worktree_paths if "worktree_paths" in locals() else {}
            )

            # FIXED: Include results dictionary with failure entries for all expected agents
            # This ensures BuildOrchestrator can properly detect which agents failed
            error_results = {}
            for task in agent_tasks:
                agent_id = task.get("agent_id", "unknown")
                agent_name = task.get("agent", "unknown")
                error_results[agent_id] = {
                    "agent_id": agent_id,
                    "agent": agent_name,
                    "command": task.get("command", "unknown"),
                    "success": False,
                    "error": str(e),
                }

            return {
                "success": False,
                "error": str(e),
                "task_id": task_id,
                "results": error_results,
                "total_agents": len(agent_tasks),
                "successful_agents": 0,
                "failed_agents": len(agent_tasks),
            }

    async def _execute_agent_task(
        self, task: dict[str, Any], worktree_path: Path | None = None
    ) -> dict[str, Any]:
        """
        Execute a single agent task.

        Args:
            task: Agent task definition
            worktree_path: Optional worktree path for isolation

        Returns:
            Task result dictionary
        """
        agent_id = task.get("agent_id", "unknown")
        agent_name = task.get("agent", "unknown")
        command = task.get("command", "unknown")
        args = task.get("args", {})
        target = task.get("target", None)

        # Import agent dynamically
        try:
            agent_module = __import__(
                f"tapps_agents.agents.{agent_name}.agent",
                fromlist=[f"{agent_name.title()}Agent"],
            )
            agent_class = getattr(agent_module, f"{agent_name.title()}Agent")

            # Create agent instance
            agent_instance = agent_class(config=self.config)

            # Change to worktree if provided
            original_cwd = Path.cwd()
            if worktree_path:
                import os

                os.chdir(worktree_path)

            try:
                await agent_instance.activate(self.project_root)

                # Add target to args if provided
                if target:
                    args["target"] = target

                # Execute command
                result = await agent_instance.run(command, **args)

                await agent_instance.close()

                return {
                    "agent_id": agent_id,
                    "agent": agent_name,
                    "command": command,
                    "success": True,
                    "result": result,
                }

            finally:
                if worktree_path:
                    os.chdir(original_cwd)

        except Exception as e:
            logger.error(f"Failed to execute agent task {agent_id}: {e}")
            return {
                "agent_id": agent_id,
                "agent": agent_name,
                "command": command,
                "success": False,
                "error": str(e),
            }

    def _aggregate_results(
        self, agent_tasks: list[dict[str, Any]], results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Aggregate results from multiple agent executions.

        Args:
            agent_tasks: Original task definitions
            results: Execution results

        Returns:
            Aggregated results dictionary
        """
        aggregated: dict[str, Any] = {
            "success": True,
            "timestamp": datetime.now(UTC).isoformat(),
            "total_agents": len(agent_tasks),
            "successful_agents": 0,
            "failed_agents": 0,
            "results": {},
            "summary": {},
        }

        for task, result in zip(agent_tasks, results, strict=False):
            agent_id = task.get("agent_id", "unknown")
            agent_name = task.get("agent", "unknown")

            aggregated["results"][agent_id] = result

            if result.get("success"):
                aggregated["successful_agents"] += 1
            else:
                aggregated["failed_agents"] += 1
                aggregated["success"] = False

            # Create summary by agent type
            if agent_name not in aggregated["summary"]:
                aggregated["summary"][agent_name] = {
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                }

            aggregated["summary"][agent_name]["total"] += 1
            if result.get("success"):
                aggregated["summary"][agent_name]["successful"] += 1
            else:
                aggregated["summary"][agent_name]["failed"] += 1

        return aggregated

    async def _cleanup_worktrees(self, worktree_paths: dict[str, Path]):
        """Cleanup worktrees after execution."""
        for agent_id, _worktree_path in worktree_paths.items():
            try:
                self.worktree_manager.remove_worktree(agent_id)
            except Exception as e:
                logger.warning(f"Failed to cleanup worktree {agent_id}: {e}")

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics from last execution."""
        return self.performance_metrics.copy()


async def execute_multi_agent_workflow(
    agent_tasks: list[dict[str, Any]],
    project_root: Path | None = None,
    max_parallel: int = 8,
) -> dict[str, Any]:
    """
    Convenience function to execute multi-agent workflow.

    Args:
        agent_tasks: List of agent task definitions
        project_root: Project root directory
        max_parallel: Maximum parallel agents

    Returns:
        Aggregated results dictionary
    """
    orchestrator = MultiAgentOrchestrator(
        project_root=project_root, max_parallel=max_parallel
    )

    return await orchestrator.execute_parallel(agent_tasks)
