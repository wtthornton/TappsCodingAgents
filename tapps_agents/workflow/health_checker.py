"""
Health Check System for Background Agent Auto-Execution.

Provides health checks for Background Agent configuration and system readiness.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .background_agent_config import BackgroundAgentConfigValidator

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: str
    details: dict[str, Any] | None = None


class HealthChecker:
    """Health checker for Background Agent auto-execution."""

    def __init__(self, project_root: Path | None = None):
        """
        Initialize health checker.

        Args:
            project_root: Project root directory (defaults to current directory)
        """
        self.project_root = project_root or Path.cwd()
        self.config_dir = self.project_root / ".tapps-agents"
        self.background_agents_config = self.project_root / ".cursor" / "background-agents.yaml"

    def check_all(self) -> list[HealthCheckResult]:
        """
        Run all health checks.

        Returns:
            List of health check results
        """
        results: list[HealthCheckResult] = []

        results.append(self.check_configuration())
        results.append(self.check_file_system())
        results.append(self.check_status_file_access())
        results.append(self.check_command_file_access())

        return results

    def check_configuration(self) -> HealthCheckResult:
        """Check Background Agent configuration validity."""
        try:
            if not self.background_agents_config.exists():
                return HealthCheckResult(
                    name="configuration",
                    status="degraded",
                    message="Background Agent configuration file not found",
                    details={"path": str(self.background_agents_config)},
                )

            # Validate configuration
            validator = BackgroundAgentConfigValidator(self.background_agents_config)
            is_valid, errors = validator.validate()
            
            if not is_valid:

            if errors:
                return HealthCheckResult(
                    name="configuration",
                    status="unhealthy",
                    message=f"Configuration validation failed: {len(errors)} error(s)",
                    details={"errors": errors},
                )

            return HealthCheckResult(
                name="configuration",
                status="healthy",
                message="Configuration is valid",
            )

        except Exception as e:
            return HealthCheckResult(
                name="configuration",
                status="unhealthy",
                message=f"Failed to check configuration: {e}",
            )

    def check_file_system(self) -> HealthCheckResult:
        """Check file system accessibility."""
        try:
            # Check if config directory is writable
            if not self.config_dir.exists():
                try:
                    self.config_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    return HealthCheckResult(
                        name="file_system",
                        status="unhealthy",
                        message=f"Cannot create config directory: {e}",
                    )

            # Check if we can write to config directory
            test_file = self.config_dir / ".health_check_test"
            try:
                test_file.write_text("test")
                test_file.unlink()
            except Exception as e:
                return HealthCheckResult(
                    name="file_system",
                    status="unhealthy",
                    message=f"Cannot write to config directory: {e}",
                )

            return HealthCheckResult(
                name="file_system",
                status="healthy",
                message="File system is accessible",
            )

        except Exception as e:
            return HealthCheckResult(
                name="file_system",
                status="unhealthy",
                message=f"File system check failed: {e}",
            )

    def check_status_file_access(self) -> HealthCheckResult:
        """Check if status files can be read."""
        try:
            # Check if status file directory exists or can be created
            status_dir = self.project_root / ".cursor"
            if not status_dir.exists():
                try:
                    status_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    return HealthCheckResult(
                        name="status_file_access",
                        status="degraded",
                        message=f"Cannot create status file directory: {e}",
                    )

            # Check if we can read existing status files
            status_files = list(status_dir.glob(".cursor-skill-status*.json"))
            if status_files:
                try:
                    import json

                    for status_file in status_files[:5]:  # Check first 5
                        with open(status_file, encoding="utf-8") as f:
                            json.load(f)
                except Exception as e:
                    return HealthCheckResult(
                        name="status_file_access",
                        status="degraded",
                        message=f"Cannot read status files: {e}",
                    )

            return HealthCheckResult(
                name="status_file_access",
                status="healthy",
                message="Status file access is working",
                details={"status_files_found": len(status_files)},
            )

        except Exception as e:
            return HealthCheckResult(
                name="status_file_access",
                status="degraded",
                message=f"Status file access check failed: {e}",
            )

    def check_command_file_access(self) -> HealthCheckResult:
        """Check if command files can be created."""
        try:
            # Check if command file directory exists or can be created
            command_dir = self.project_root / ".cursor"
            if not command_dir.exists():
                try:
                    command_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    return HealthCheckResult(
                        name="command_file_access",
                        status="degraded",
                        message=f"Cannot create command file directory: {e}",
                    )

            # Check if we can write command files
            test_command_file = command_dir / ".cursor-skill-command-test.txt"
            try:
                test_command_file.write_text("test command")
                test_command_file.unlink()
            except Exception as e:
                return HealthCheckResult(
                    name="command_file_access",
                    status="unhealthy",
                    message=f"Cannot write command files: {e}",
                )

            return HealthCheckResult(
                name="command_file_access",
                status="healthy",
                message="Command file access is working",
            )

        except Exception as e:
            return HealthCheckResult(
                name="command_file_access",
                status="degraded",
                message=f"Command file access check failed: {e}",
            )

    def get_overall_status(self) -> str:
        """
        Get overall health status.

        Returns:
            "healthy", "degraded", or "unhealthy"
        """
        results = self.check_all()

        if any(r.status == "unhealthy" for r in results):
            return "unhealthy"
        if any(r.status == "degraded" for r in results):
            return "degraded"
        return "healthy"

