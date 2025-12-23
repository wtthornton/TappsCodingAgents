"""
Container Debugger

Debugs container errors with automatic fix suggestions.
"""

import logging
import subprocess  # nosec B404
from pathlib import Path
from typing import Any

from .analyzer import DockerfileAnalyzer
from .error_patterns import ErrorPatternDatabase

logger = logging.getLogger(__name__)


class ContainerDebugger:
    """
    Debugs container errors with pattern matching and fix suggestions.

    Features:
    - Analyze container logs
    - Match errors to known patterns
    - Check Dockerfile for issues
    - Suggest fixes with confidence scores
    - Test fixes in container context
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize container debugger.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root or Path.cwd()
        self.dockerfile_analyzer = DockerfileAnalyzer(project_root=self.project_root)
        self.error_patterns = ErrorPatternDatabase()

    def debug(
        self, service_name: str, error_message: str | None = None
    ) -> dict[str, Any]:
        """
        Debug a container error.

        Args:
            service_name: Name of the service/container
            error_message: Optional error message (if None, will check logs)

        Returns:
            Debug results with fix suggestions
        """
        # Get error message from logs if not provided
        if not error_message:
            error_message = self._get_container_logs(service_name)

        # Match error to pattern
        pattern = self.error_patterns.match_error(error_message)
        best_fix = self.error_patterns.get_best_fix(error_message)

        # Analyze Dockerfile
        dockerfile_path = self.project_root / "services" / service_name / "Dockerfile"
        dockerfile_issues = []
        if dockerfile_path.exists():
            dockerfile_issues = self.dockerfile_analyzer.analyze(dockerfile_path)

        # Build result
        result: dict[str, Any] = {
            "service": service_name,
            "error_message": error_message,
            "pattern_matched": pattern.pattern if pattern else None,
            "pattern_category": pattern.category if pattern else None,
            "best_fix": {
                "action": best_fix.action if best_fix else None,
                "confidence": best_fix.confidence if best_fix else 0.0,
                "description": best_fix.description if best_fix else None,
            },
            "dockerfile_issues": [
                {
                    "type": issue.issue_type,
                    "line": issue.line_number,
                    "description": issue.description,
                    "severity": issue.severity,
                    "suggested_fix": issue.suggested_fix,
                }
                for issue in dockerfile_issues
            ],
            "suggested_fixes": self._generate_fix_suggestions(
                pattern, best_fix, dockerfile_issues
            ),
        }

        return result

    def _get_container_logs(self, service_name: str) -> str:
        """Get container logs for a service."""
        try:
            # Try docker-compose logs
            result = subprocess.run(
                ["docker-compose", "logs", "--tail", "50", service_name],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout
        except Exception as e:
            logger.debug(f"Failed to get docker-compose logs: {e}")

        try:
            # Try docker logs
            result = subprocess.run(
                ["docker", "logs", "--tail", "50", service_name],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout
        except Exception as e:
            logger.debug(f"Failed to get docker logs: {e}")

        return "Could not retrieve container logs"

    def _generate_fix_suggestions(
        self,
        pattern: Any,
        best_fix: Any,
        dockerfile_issues: list[Any],
    ) -> list[dict[str, Any]]:
        """Generate fix suggestions."""
        suggestions = []

        if best_fix and best_fix.confidence > 0.95:
            suggestions.append(
                {
                    "action": best_fix.action,
                    "description": best_fix.description,
                    "confidence": best_fix.confidence,
                    "auto_apply": True,
                }
            )

        # Add Dockerfile fix suggestions
        for issue in dockerfile_issues:
            if issue.severity in ["critical", "high"]:
                suggestions.append(
                    {
                        "action": f"fix_dockerfile_{issue.issue_type}",
                        "description": issue.suggested_fix,
                        "confidence": issue.confidence,
                        "line": issue.line_number,
                        "auto_apply": issue.confidence > 0.9,
                    }
                )

        return suggestions

    def apply_fix(
        self, service_name: str, fix_action: str, auto_confirm: bool = False
    ) -> dict[str, Any]:
        """
        Apply a fix to a service.

        Args:
            service_name: Name of the service
            fix_action: Action to apply
            auto_confirm: Whether to apply without confirmation

        Returns:
            Fix result
        """
        dockerfile_path = self.project_root / "services" / service_name / "Dockerfile"
        if not dockerfile_path.exists():
            return {"success": False, "error": "Dockerfile not found"}

        # Apply fix based on action
        if fix_action == "move_workdir_before_copy":
            return self._fix_workdir_order(dockerfile_path)
        elif fix_action == "use_python_m_uvicorn":
            return self._fix_uvicorn_command(dockerfile_path)
        else:
            return {"success": False, "error": f"Unknown fix action: {fix_action}"}

    def _fix_workdir_order(self, dockerfile_path: Path) -> dict[str, Any]:
        """Fix WORKDIR order in Dockerfile."""
        content = dockerfile_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Find WORKDIR and COPY lines
        workdir_idx = None
        copy_indices: list[int] = []

        for i, line in enumerate(lines):
            if line.strip().startswith("WORKDIR"):
                workdir_idx = i
            elif line.strip().startswith("COPY"):
                copy_indices.append(i)

        if workdir_idx is None or not copy_indices:
            return {"success": False, "error": "Could not find WORKDIR or COPY commands"}

        # Move WORKDIR before first COPY
        if workdir_idx > copy_indices[0]:
            workdir_line = lines.pop(workdir_idx)
            lines.insert(copy_indices[0], workdir_line)
            dockerfile_path.write_text("\n".join(lines), encoding="utf-8")
            return {"success": True, "message": "Moved WORKDIR before COPY commands"}

        return {"success": False, "message": "WORKDIR already in correct position"}

    def _fix_uvicorn_command(self, dockerfile_path: Path) -> dict[str, Any]:
        """Fix uvicorn command to use 'python -m'."""
        content = dockerfile_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        fixed = False
        for i, line in enumerate(lines):
            if "uvicorn" in line and "python -m" not in line:
                # Replace uvicorn with python -m uvicorn
                lines[i] = line.replace("uvicorn", "python -m uvicorn")
                fixed = True

        if fixed:
            dockerfile_path.write_text("\n".join(lines), encoding="utf-8")
            return {"success": True, "message": "Updated uvicorn command to use 'python -m'"}
        return {"success": False, "message": "No uvicorn command found to fix"}

