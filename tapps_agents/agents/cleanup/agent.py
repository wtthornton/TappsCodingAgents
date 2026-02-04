"""
Cleanup Agent - Project structure analysis and intelligent cleanup

This agent helps keep projects clean by:
- Analyzing project structure for cleanup opportunities
- Detecting duplicate files, outdated docs, and naming inconsistencies
- Generating cleanup plans with rationale for each action
- Executing cleanup operations safely with backups and rollback
"""

from pathlib import Path
from typing import Any

from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config
from ...utils.project_cleanup_agent import (
    AnalysisReport,
    CleanupPlan,
    ProjectAnalyzer,
)
from ...utils.project_cleanup_agent import (
    CleanupAgent as CleanupAgentUtil,
)


class CleanupAgent(BaseAgent):
    """
    Cleanup Agent - Project structure analysis and cleanup.

    Permissions: Read, Write, Edit, Glob, Bash

    This agent provides guided project cleanup capabilities:
    - Analyze project structure (duplicates, outdated files, naming issues)
    - Generate cleanup plans with user confirmation
    - Execute cleanup operations safely with backups
    - Support dry-run mode for previewing changes
    """

    def __init__(self, config: ProjectConfig | None = None):
        super().__init__(
            agent_id="cleanup-agent",
            agent_name="Cleanup Agent",
            config=config,
        )
        # Use config if provided, otherwise load defaults
        if config is None:
            config = load_config()
        self.config = config

        # Get cleanup agent config
        cleanup_config = config.agents.cleanup_agent if config and config.agents else None
        self.dry_run_default = cleanup_config.dry_run_default if cleanup_config else True
        self.backup_enabled = cleanup_config.backup_enabled if cleanup_config else True
        self.interactive_mode = cleanup_config.interactive_mode if cleanup_config else True

        # Utility components (lazily initialized)
        self._util: CleanupAgentUtil | None = None
        self._analyzer: ProjectAnalyzer | None = None

    def _get_util(self, project_root: Path | None = None) -> CleanupAgentUtil:
        """Get or create the cleanup utility instance."""
        root = project_root or self._project_root or Path.cwd()
        if self._util is None or self._util.project_root != root:
            self._util = CleanupAgentUtil(root)
        return self._util

    def _get_analyzer(self, project_root: Path | None = None) -> ProjectAnalyzer:
        """Get or create the analyzer instance."""
        root = project_root or self._project_root or Path.cwd()
        if self._analyzer is None or self._analyzer.project_root != root:
            self._analyzer = ProjectAnalyzer(root)
        return self._analyzer

    def get_commands(self) -> list[dict[str, str]]:
        """Return list of available commands."""
        commands = super().get_commands()
        commands.extend(
            [
                {
                    "command": "*analyze",
                    "description": "Analyze project structure for cleanup opportunities",
                },
                {
                    "command": "*plan",
                    "description": "Generate cleanup plan from analysis",
                },
                {
                    "command": "*execute",
                    "description": "Execute cleanup plan (dry-run by default)",
                },
                {
                    "command": "*run",
                    "description": "Run full cleanup workflow (analyze, plan, execute)",
                },
            ]
        )
        return commands

    async def run(self, command: str, **kwargs) -> dict[str, Any]:
        """Execute a command."""
        if command == "analyze":
            return await self.analyze_command(**kwargs)
        elif command == "plan":
            return await self.plan_command(**kwargs)
        elif command == "execute":
            return await self.execute_command(**kwargs)
        elif command == "run":
            return await self.run_full_cleanup_command(**kwargs)
        elif command == "help":
            return self._help()
        else:
            return {"error": f"Unknown command: {command}"}

    async def analyze_command(
        self,
        path: str | Path | None = None,
        pattern: str = "*.md",
        output: str | Path | None = None,
    ) -> dict[str, Any]:
        """
        Analyze project structure for cleanup opportunities.

        Args:
            path: Path to analyze (defaults to project docs/)
            pattern: File pattern to match (default: *.md)
            output: Optional output file for analysis report

        Returns:
            Analysis report with duplicates, outdated files, naming issues
        """
        project_root = self._project_root or Path.cwd()
        scan_path = Path(path) if path else project_root / "docs"

        if not scan_path.exists():
            return {
                "error": f"Path does not exist: {scan_path}",
                "type": "analyze",
                "success": False,
            }

        try:
            util = self._get_util(project_root)
            report = await util.run_analysis(scan_path, pattern)

            result = {
                "type": "analyze",
                "success": True,
                "report": {
                    "total_files": report.total_files,
                    "total_size_mb": report.total_size / 1024 / 1024,
                    "duplicate_groups": len(report.duplicates),
                    "duplicate_files": report.duplicate_count,
                    "potential_savings_kb": report.potential_savings / 1024,
                    "outdated_files": len(report.outdated_files),
                    "obsolete_files": report.obsolete_file_count,
                    "naming_issues": len(report.naming_issues),
                    "timestamp": report.timestamp.isoformat(),
                    "scan_path": str(report.scan_path),
                },
                "summary": report.to_markdown(),
                "message": f"Analysis complete: {report.total_files} files analyzed",
            }

            # Save report if output specified
            if output:
                output_path = Path(output)
                output_path.write_text(report.model_dump_json(indent=2))
                result["output_file"] = str(output_path)

            return result

        except Exception as e:
            return {
                "type": "analyze",
                "success": False,
                "error": str(e),
            }

    async def plan_command(
        self,
        analysis_file: str | Path | None = None,
        path: str | Path | None = None,
        pattern: str = "*.md",
        output: str | Path | None = None,
    ) -> dict[str, Any]:
        """
        Generate cleanup plan from analysis.

        Args:
            analysis_file: Path to analysis report JSON (optional)
            path: Path to analyze if no analysis file (defaults to docs/)
            pattern: File pattern if running fresh analysis
            output: Optional output file for cleanup plan

        Returns:
            Cleanup plan with prioritized actions
        """
        project_root = self._project_root or Path.cwd()

        try:
            # Load analysis or run fresh
            if analysis_file:
                analysis_path = Path(analysis_file)
                if not analysis_path.exists():
                    return {
                        "error": f"Analysis file not found: {analysis_path}",
                        "type": "plan",
                        "success": False,
                    }
                analysis = AnalysisReport.model_validate_json(analysis_path.read_text())
            else:
                scan_path = Path(path) if path else project_root / "docs"
                util = self._get_util(project_root)
                analysis = await util.run_analysis(scan_path, pattern)

            # Generate plan
            util = self._get_util(project_root)
            plan = util.run_planning(analysis)

            result = {
                "type": "plan",
                "success": True,
                "plan": {
                    "total_actions": len(plan.actions),
                    "high_priority": plan.high_priority_count,
                    "medium_priority": plan.medium_priority_count,
                    "low_priority": plan.low_priority_count,
                    "estimated_savings_mb": plan.estimated_savings / 1024 / 1024,
                    "estimated_file_reduction": f"{plan.estimated_file_reduction:.1f}%",
                    "created_at": plan.created_at.isoformat(),
                },
                "actions_preview": [
                    {
                        "type": str(a.action_type),
                        "files": [str(f) for f in a.source_files],
                        "target": str(a.target_path) if a.target_path else None,
                        "rationale": a.rationale,
                        "priority": a.priority,
                        "safety": str(a.safety_level),
                        "requires_confirmation": a.requires_confirmation,
                    }
                    for a in plan.actions[:10]  # Preview first 10
                ],
                "summary": plan.to_markdown(),
                "message": f"Plan generated: {len(plan.actions)} actions",
            }

            # Save plan if output specified
            if output:
                output_path = Path(output)
                output_path.write_text(plan.model_dump_json(indent=2))
                result["output_file"] = str(output_path)

            return result

        except Exception as e:
            return {
                "type": "plan",
                "success": False,
                "error": str(e),
            }

    async def execute_command(
        self,
        plan_file: str | Path | None = None,
        path: str | Path | None = None,
        pattern: str = "*.md",
        dry_run: bool | None = None,
        backup: bool | None = None,
    ) -> dict[str, Any]:
        """
        Execute cleanup plan.

        Args:
            plan_file: Path to cleanup plan JSON (optional)
            path: Path to analyze if no plan file
            pattern: File pattern if running fresh
            dry_run: Preview changes without executing (default: True)
            backup: Create backup before execution (default: True)

        Returns:
            Execution report with results
        """
        project_root = self._project_root or Path.cwd()

        # Use defaults if not specified
        if dry_run is None:
            dry_run = self.dry_run_default
        if backup is None:
            backup = self.backup_enabled

        try:
            # Load plan or generate fresh
            if plan_file:
                plan_path = Path(plan_file)
                if not plan_path.exists():
                    return {
                        "error": f"Plan file not found: {plan_path}",
                        "type": "execute",
                        "success": False,
                    }
                plan = CleanupPlan.model_validate_json(plan_path.read_text())
            else:
                # Run analysis and planning first
                scan_path = Path(path) if path else project_root / "docs"
                util = self._get_util(project_root)
                analysis = await util.run_analysis(scan_path, pattern)
                plan = util.run_planning(analysis)

            # Execute plan
            util = self._get_util(project_root)
            report = await util.run_execution(plan, dry_run=dry_run, create_backup=backup)

            result = {
                "type": "execute",
                "success": True,
                "dry_run": report.dry_run,
                "report": {
                    "total_operations": len(report.operations),
                    "successful": report.success_count,
                    "failed": report.failure_count,
                    "files_deleted": report.files_deleted,
                    "files_moved": report.files_moved,
                    "files_renamed": report.files_renamed,
                    "files_modified": report.files_modified,
                    "duration_seconds": report.duration_seconds,
                    "backup_location": str(report.backup_location) if report.backup_location else None,
                },
                "summary": report.to_markdown(),
                "message": (
                    f"{'Dry run' if dry_run else 'Execution'} complete: "
                    f"{report.success_count} successful, {report.failure_count} failed"
                ),
            }

            return result

        except Exception as e:
            return {
                "type": "execute",
                "success": False,
                "error": str(e),
            }

    async def run_full_cleanup_command(
        self,
        path: str | Path | None = None,
        pattern: str = "*.md",
        dry_run: bool | None = None,
        backup: bool | None = None,
    ) -> dict[str, Any]:
        """
        Run full cleanup workflow (analyze, plan, execute).

        Args:
            path: Path to analyze (defaults to docs/)
            pattern: File pattern to match
            dry_run: Preview changes without executing (default: True)
            backup: Create backup before execution (default: True)

        Returns:
            Combined report with analysis, plan, and execution results
        """
        project_root = self._project_root or Path.cwd()
        scan_path = Path(path) if path else project_root / "docs"

        # Use defaults if not specified
        if dry_run is None:
            dry_run = self.dry_run_default
        if backup is None:
            backup = self.backup_enabled

        if not scan_path.exists():
            return {
                "error": f"Path does not exist: {scan_path}",
                "type": "run",
                "success": False,
            }

        try:
            util = self._get_util(project_root)
            analysis, plan, execution = await util.run_full_cleanup(
                scan_path,
                pattern,
                dry_run=dry_run,
                create_backup=backup,
            )

            return {
                "type": "run",
                "success": True,
                "dry_run": execution.dry_run,
                "analysis": {
                    "total_files": analysis.total_files,
                    "duplicates": analysis.duplicate_count,
                    "outdated": len(analysis.outdated_files),
                    "naming_issues": len(analysis.naming_issues),
                },
                "plan": {
                    "total_actions": len(plan.actions),
                    "estimated_savings_mb": plan.estimated_savings / 1024 / 1024,
                },
                "execution": {
                    "successful": execution.success_count,
                    "failed": execution.failure_count,
                    "files_modified": execution.files_modified,
                    "backup_location": str(execution.backup_location) if execution.backup_location else None,
                },
                "summary": "\n".join([
                    "=" * 60,
                    analysis.to_markdown(),
                    "=" * 60,
                    plan.to_markdown(),
                    "=" * 60,
                    execution.to_markdown(),
                ]),
                "message": (
                    f"{'Dry run' if dry_run else 'Cleanup'} complete: "
                    f"{analysis.total_files} files analyzed, "
                    f"{len(plan.actions)} actions, "
                    f"{execution.success_count} successful"
                ),
            }

        except Exception as e:
            return {
                "type": "run",
                "success": False,
                "error": str(e),
            }

    def _help(self) -> dict[str, Any]:
        """Return help information for Cleanup Agent."""
        examples = [
            "  *analyze --path ./docs --pattern '*.md'",
            "  *plan --analysis-file analysis.json --output cleanup-plan.json",
            "  *execute --plan-file cleanup-plan.json --dry-run",
            "  *run --path ./docs --dry-run --backup",
        ]
        help_text = "\n".join([self.format_help(), "\nExamples:", *examples])
        return {"type": "help", "content": help_text}

    async def close(self):
        """Close agent and clean up resources."""
        self._util = None
        self._analyzer = None
