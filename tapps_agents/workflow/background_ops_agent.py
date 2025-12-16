"""
Background Operations Agent - Executes operations tasks as a Background Agent.

This module provides a Background Agent wrapper around the Ops Agent
that produces versioned, machine-readable operations artifacts.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from ..agents.ops.agent import OpsAgent
from ..core.config import load_config
from .ops_artifact import (
    ComplianceCheck,
    DeploymentStep,
    InfrastructureFile,
    OperationsArtifact,
    SecurityIssue,
)


class BackgroundOpsAgent:
    """
    Background Operations Agent that runs operations tasks and produces artifacts.

    Epic 2 / Story 2.2: Background Cloud Agents - Docs, Ops, Context
    """

    def __init__(
        self,
        worktree_path: Path,
        correlation_id: str | None = None,
        timeout_seconds: float = 1200.0,  # 20 minutes default
    ):
        """
        Initialize Background Operations Agent.

        Args:
            worktree_path: Path to worktree where operations should run
            correlation_id: Optional correlation ID for tracking
            timeout_seconds: Maximum execution time in seconds
        """
        self.worktree_path = Path(worktree_path)
        self.correlation_id = correlation_id
        self.timeout_seconds = timeout_seconds
        self.config = load_config()
        self.ops_agent: OpsAgent | None = None
        self._cancelled = False

    async def run_operation(
        self,
        operation_type: str,
        **kwargs: Any,
    ) -> OperationsArtifact:
        """
        Run an operation and produce artifact.

        Args:
            operation_type: Type of operation to run
                          ("security_scan", "compliance_check", "deploy",
                           "infrastructure_setup", "dependency_audit")
            **kwargs: Additional arguments for the operation

        Returns:
            OperationsArtifact with operation results
        """
        artifact = OperationsArtifact(
            worktree_path=str(self.worktree_path),
            correlation_id=self.correlation_id,
            operation_type=operation_type,
        )

        try:
            # Initialize ops agent
            self.ops_agent = OpsAgent(config=self.config, project_root=self.worktree_path)
            await self.ops_agent.activate(project_root=self.worktree_path)

            # Change to worktree directory for operations
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(self.worktree_path)

                artifact.status = "running"

                # Run operation with timeout
                await asyncio.wait_for(
                    self._execute_operation(artifact, operation_type, **kwargs),
                    timeout=self.timeout_seconds,
                )

                artifact.mark_completed()

            finally:
                os.chdir(original_cwd)
                if self.ops_agent:
                    await self.ops_agent.close()

        except TimeoutError:
            artifact.mark_timeout()
        except asyncio.CancelledError:
            artifact.mark_cancelled()
        except Exception as e:
            artifact.mark_failed(str(e))

        # Write artifact to worktree
        self._write_artifact(artifact)

        return artifact

    async def _execute_operation(
        self,
        artifact: OperationsArtifact,
        operation_type: str,
        **kwargs: Any,
    ) -> None:
        """Execute the specified operation."""
        if self._cancelled:
            artifact.mark_cancelled()
            return

        if not self.ops_agent:
            artifact.mark_failed("Ops agent not initialized")
            return

        try:
            if operation_type == "security_scan":
                await self._run_security_scan(artifact, **kwargs)
            elif operation_type == "compliance_check":
                await self._run_compliance_check(artifact, **kwargs)
            elif operation_type == "deploy":
                await self._run_deploy(artifact, **kwargs)
            elif operation_type == "infrastructure_setup":
                await self._run_infrastructure_setup(artifact, **kwargs)
            elif operation_type == "dependency_audit":
                await self._run_dependency_audit(artifact, **kwargs)
            else:
                artifact.mark_failed(f"Unknown operation type: {operation_type}")

        except Exception as e:
            artifact.mark_failed(str(e))

    async def _run_security_scan(
        self, artifact: OperationsArtifact, **kwargs: Any
    ) -> None:
        """Run security scan."""
        if not self.ops_agent:
            return

        try:
            target = kwargs.get("target")
            scan_type = kwargs.get("scan_type", "all")

            result_dict = await self.ops_agent._handle_security_scan(
                target=target, scan_type=scan_type
            )

            if "error" in result_dict:
                artifact.mark_failed(result_dict["error"])
                return

            # Parse security issues
            issues = result_dict.get("issues", [])
            for issue_data in issues:
                issue = SecurityIssue(
                    severity=issue_data.get("severity", "info"),
                    issue_type=issue_data.get("type", "unknown"),
                    description=issue_data.get("description", ""),
                    file_path=issue_data.get("file_path"),
                    line=issue_data.get("line"),
                    recommendation=issue_data.get("recommendation"),
                )
                artifact.add_security_issue(issue)

        except Exception as e:
            artifact.mark_failed(f"Security scan failed: {str(e)}")

    async def _run_compliance_check(
        self, artifact: OperationsArtifact, **kwargs: Any
    ) -> None:
        """Run compliance check."""
        if not self.ops_agent:
            return

        try:
            compliance_type = kwargs.get("compliance_type", "general")

            result_dict = await self.ops_agent._handle_compliance_check(
                compliance_type=compliance_type
            )

            if "error" in result_dict:
                artifact.mark_failed(result_dict["error"])
                return

            artifact.compliance_type = compliance_type
            artifact.compliance_status = result_dict.get("compliance_status")

            # Parse compliance checks
            checks = result_dict.get("checks", [])
            for check_data in checks:
                check = ComplianceCheck(
                    check=check_data.get("check", ""),
                    status=check_data.get("status", "unknown"),
                    message=check_data.get("message", ""),
                    recommendation=check_data.get("recommendation"),
                )
                artifact.add_compliance_check(check)

        except Exception as e:
            artifact.mark_failed(f"Compliance check failed: {str(e)}")

    async def _run_deploy(
        self, artifact: OperationsArtifact, **kwargs: Any
    ) -> None:
        """Run deployment."""
        if not self.ops_agent:
            return

        try:
            target = kwargs.get("target", "local")
            environment = kwargs.get("environment")

            result_dict = await self.ops_agent._handle_deploy(
                target=target, environment=environment
            )

            if "error" in result_dict:
                artifact.mark_failed(result_dict["error"])
                return

            artifact.deployment_target = target
            artifact.deployment_environment = environment
            artifact.deployment_status = result_dict.get("status", "planned")

            # Parse deployment steps
            deployment_plan = result_dict.get("deployment_plan", {})
            steps = deployment_plan.get("steps", [])
            for step_data in steps:
                step = DeploymentStep(
                    step=step_data.get("step", 0),
                    action=step_data.get("action", ""),
                    command=step_data.get("command"),
                    description=step_data.get("description"),
                    status="pending",
                )
                artifact.add_deployment_step(step)

        except Exception as e:
            artifact.mark_failed(f"Deployment failed: {str(e)}")

    async def _run_infrastructure_setup(
        self, artifact: OperationsArtifact, **kwargs: Any
    ) -> None:
        """Run infrastructure setup."""
        if not self.ops_agent:
            return

        try:
            infrastructure_type = kwargs.get("infrastructure_type", "docker")

            result_dict = await self.ops_agent._handle_infrastructure_setup(
                infrastructure_type=infrastructure_type
            )

            if "error" in result_dict:
                artifact.mark_failed(result_dict["error"])
                return

            artifact.infrastructure_type = infrastructure_type

            # Parse infrastructure files
            files_created = result_dict.get("files_created", [])
            for file_path in files_created:
                if file_path:
                    file = InfrastructureFile(
                        file_path=file_path,
                        file_type=infrastructure_type,
                        status="created",
                    )
                    artifact.add_infrastructure_file(file)

        except Exception as e:
            artifact.mark_failed(f"Infrastructure setup failed: {str(e)}")

    async def _run_dependency_audit(
        self, artifact: OperationsArtifact, **kwargs: Any
    ) -> None:
        """Run dependency audit."""
        if not self.ops_agent:
            return

        try:
            severity_threshold = kwargs.get("severity_threshold")

            result_dict = await self.ops_agent._handle_audit_dependencies(
                severity_threshold=severity_threshold
            )

            if "error" in result_dict:
                artifact.mark_failed(result_dict["error"])
                return

            # Parse vulnerability data
            vulnerabilities = result_dict.get("vulnerabilities", [])
            artifact.dependency_vulnerabilities = vulnerabilities
            artifact.vulnerability_count = result_dict.get("vulnerability_count", 0)
            artifact.severity_breakdown = result_dict.get("severity_breakdown", {})
            artifact.tools_available = result_dict.get("tools_available", {})

        except Exception as e:
            artifact.mark_failed(f"Dependency audit failed: {str(e)}")

    def _write_artifact(self, artifact: OperationsArtifact) -> None:
        """Write artifact to worktree."""
        reports_dir = self.worktree_path / "reports" / "operations"
        reports_dir.mkdir(parents=True, exist_ok=True)

        artifact_path = reports_dir / "ops-report.json"
        with open(artifact_path, "w", encoding="utf-8") as f:
            json.dump(artifact.to_dict(), f, indent=2)

    def cancel(self) -> None:
        """Cancel running operation."""
        self._cancelled = True
