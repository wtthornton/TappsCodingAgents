"""
Dockerfile Validator - Validates Dockerfile patterns

Phase 4.2: Docker & Containerization Enhancement for HomeIQ
"""

import re
from pathlib import Path
from typing import Any


class DockerfileValidator:
    """
    Validates Dockerfile patterns and best practices.

    Checks for:
    - Security issues (root user, secrets)
    - Layer ordering
    - Multi-stage builds
    - Health checks
    - Image optimization
    """

    def __init__(self):
        """Initialize Dockerfile validator."""
        pass

    def validate_dockerfile(self, dockerfile: Path) -> dict[str, Any]:
        """
        Validate Dockerfile.

        Args:
            dockerfile: Path to Dockerfile

        Returns:
            Dictionary with validation results:
            {
                "valid": bool,
                "issues": list[str],
                "suggestions": list[str],
                "security_issues": list[str],
                "optimization_opportunities": list[str]
            }
        """
        issues: list[str] = []
        suggestions: list[str] = []
        security_issues: list[str] = []
        optimizations: list[str] = []

        try:
            content = dockerfile.read_text()
            lines = content.split("\n")
        except Exception as e:
            return {
                "valid": False,
                "issues": [f"Failed to read Dockerfile: {e}"],
                "suggestions": [],
                "security_issues": [],
                "optimization_opportunities": [],
            }

        # Check for FROM instruction
        if not any(line.strip().startswith("FROM") for line in lines):
            issues.append("Missing FROM instruction")
            return {
                "valid": False,
                "issues": issues,
                "suggestions": suggestions,
                "security_issues": security_issues,
                "optimization_opportunities": optimizations,
            }

        # Check for root user
        has_user_instruction = any("USER" in line.upper() for line in lines)
        if not has_user_instruction:
            security_issues.append("Running as root user - add USER instruction")
            suggestions.append("Create non-root user and use USER instruction")

        # Check for secrets in Dockerfile
        secret_patterns = [
            r"ENV\s+\w*PASSWORD\s*=",
            r"ENV\s+\w*SECRET\s*=",
            r"ENV\s+\w*KEY\s*=",
            r"ENV\s+\w*TOKEN\s*=",
        ]
        for pattern in secret_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                security_issues.append(f"Potential secret in Dockerfile: {pattern}")
                suggestions.append(
                    "Use environment variables or secrets management instead"
                )

        # Check for multi-stage build
        from_count = len([line for line in lines if line.strip().startswith("FROM")])
        if from_count == 1:
            suggestions.append("Consider using multi-stage build to reduce image size")
        elif from_count > 1:
            # Check for AS keyword (multi-stage)
            has_as = any("AS" in line.upper() for line in lines)
            if has_as:
                optimizations.append("Multi-stage build detected - good practice")

        # Check for health check
        has_healthcheck = any("HEALTHCHECK" in line.upper() for line in lines)
        if not has_healthcheck:
            suggestions.append("Consider adding HEALTHCHECK instruction")

        # Check layer ordering (COPY requirements before COPY .)
        copy_requirements = False
        for line in lines:
            if "COPY" in line.upper() and "requirements" in line.lower():
                copy_requirements = True
            if "COPY" in line.upper() and (line.strip().endswith(".") or "./" in line):
                if not copy_requirements:
                    optimizations.append(
                        "Consider copying requirements.txt before copying all files for better caching"
                    )

        # Check for .dockerignore mention
        if ".dockerignore" not in content and "dockerignore" not in content.lower():
            suggestions.append("Consider using .dockerignore to reduce build context")

        # Check for specific tags (not 'latest')
        from_lines = [line for line in lines if line.strip().startswith("FROM")]
        for from_line in from_lines:
            if ":latest" in from_line or (":" not in from_line and "FROM" in from_line):
                suggestions.append("Use specific image tags instead of 'latest'")

        # Check for apt-get update without cleanup
        if "apt-get update" in content.lower():
            if "rm -rf /var/lib/apt/lists/*" not in content.lower():
                optimizations.append(
                    "Clean apt cache after apt-get update to reduce image size"
                )

        # Check for combining RUN commands
        run_commands = [line for line in lines if line.strip().startswith("RUN")]
        if len(run_commands) > 5:
            suggestions.append("Consider combining RUN commands to reduce layers")

        return {
            "valid": len(issues) == 0 and len(security_issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "security_issues": security_issues,
            "optimization_opportunities": optimizations,
        }

    def review_file(self, file_path: Path, code: str) -> dict[str, Any]:
        """
        Review a file for Dockerfile patterns.

        Args:
            file_path: Path to the file
            code: File content (not used for Dockerfile)

        Returns:
            Dictionary with review results:
            {
                "is_dockerfile": bool,
                "validation": dict
            }
        """
        results = {"is_dockerfile": False, "validation": {}}

        # Check if file is Dockerfile
        if file_path.name in [
            "Dockerfile",
            "Dockerfile.prod",
            "Dockerfile.dev",
        ] or file_path.name.startswith("Dockerfile."):
            results["is_dockerfile"] = True
            validation = self.validate_dockerfile(file_path)
            results["validation"] = validation

        return results
