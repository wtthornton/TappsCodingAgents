"""
Dependency Analyzer - Dependency tree visualization and security auditing

Phase 6.4.3: Dependency Analysis & Security Auditing
"""

import json
import shutil
import subprocess  # nosec B404 - used with fixed args, no shell
import sys
from pathlib import Path
from typing import Any


class DependencyAnalyzer:
    """
    Analyze Python dependencies using pipdeptree and pip-audit.

    Phase 6.4.3: Dependency Analysis & Security Auditing
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize dependency analyzer.

        Args:
            project_root: Root directory of project (default: current directory)
        """
        if project_root is None:
            project_root = Path.cwd()
        self.project_root = Path(project_root).resolve()

        # Check for tool availability
        self.has_pipdeptree = shutil.which("pipdeptree") is not None
        self.has_pip_audit = shutil.which("pip-audit") is not None

    def analyze_dependencies(self) -> dict[str, Any]:
        """
        Perform full dependency analysis.

        Returns:
            Dictionary with:
            - dependency_tree: Dependency tree structure
            - vulnerabilities: Security vulnerabilities found
            - outdated: Outdated packages
            - total_packages: Total number of packages
        """
        result: dict[str, Any] = {
            "dependency_tree": None,
            "vulnerabilities": [],
            "outdated": [],
            "total_packages": 0,
            "tools_available": {
                "pipdeptree": self.has_pipdeptree,
                "pip-audit": self.has_pip_audit,
            },
        }

        # Get dependency tree
        tree_result = self.get_dependency_tree()
        if tree_result:
            result["dependency_tree"] = tree_result.get("tree")
            result["total_packages"] = tree_result.get("package_count", 0)

        # Run security audit
        audit_result = self.run_security_audit()
        if audit_result:
            result["vulnerabilities"] = audit_result.get("vulnerabilities", [])

        # Check for outdated packages
        outdated_result = self.check_outdated()
        if outdated_result:
            result["outdated"] = outdated_result.get("outdated_packages", [])

        return result

    def get_dependency_tree(self) -> dict[str, Any] | None:
        """
        Visualize dependency tree using pipdeptree.

        Returns:
            Dictionary with:
            - tree: Dependency tree as text
            - tree_json: Dependency tree as JSON structure
            - package_count: Total number of packages
        """
        if not self.has_pipdeptree:
            return {
                "tree": None,
                "tree_json": None,
                "package_count": 0,
                "error": "pipdeptree not found in PATH",
            }

        try:
            # Run pipdeptree with JSON output
            result = subprocess.run(  # nosec B603 - fixed module invocation
                [sys.executable, "-m", "pipdeptree", "--json"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.project_root,
            )

            if result.returncode != 0:
                return {
                    "tree": None,
                    "tree_json": None,
                    "package_count": 0,
                    "error": f"pipdeptree failed: {result.stderr}",
                }

            # Parse JSON output
            try:
                tree_json = json.loads(result.stdout)
                package_count = self._count_packages(tree_json)

                # Also get text output
                text_result = subprocess.run(  # nosec B603 - fixed module invocation
                    [sys.executable, "-m", "pipdeptree"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=self.project_root,
                )
                tree_text = text_result.stdout if text_result.returncode == 0 else None

                return {
                    "tree": tree_text,
                    "tree_json": tree_json,
                    "package_count": package_count,
                }
            except json.JSONDecodeError:
                return {
                    "tree": result.stdout,
                    "tree_json": None,
                    "package_count": 0,
                    "error": "Failed to parse JSON output",
                }

        except subprocess.TimeoutExpired:
            return {
                "tree": None,
                "tree_json": None,
                "package_count": 0,
                "error": "pipdeptree timed out",
            }
        except FileNotFoundError:
            return {
                "tree": None,
                "tree_json": None,
                "package_count": 0,
                "error": "pipdeptree not found",
            }
        except Exception as e:
            return {
                "tree": None,
                "tree_json": None,
                "package_count": 0,
                "error": str(e),
            }

    def run_security_audit(
        self, severity_threshold: str = "high", format_type: str = "json"
    ) -> dict[str, Any] | None:
        """
        Scan for security vulnerabilities using pip-audit.

        Args:
            severity_threshold: Minimum severity to report (low/medium/high/critical)
            format_type: Output format (json/text)

        Returns:
            Dictionary with:
            - vulnerabilities: List of vulnerabilities found
            - vulnerability_count: Total number of vulnerabilities
            - severity_breakdown: Count by severity level
        """
        if not self.has_pip_audit:
            return {
                "vulnerabilities": [],
                "vulnerability_count": 0,
                "severity_breakdown": {},
                "error": "pip-audit not found in PATH",
            }

        try:
            # Build command
            command = ["pip-audit", "--format", format_type]

            # Add severity filtering if supported (pip-audit 2.6+)
            # Note: pip-audit severity filtering may vary by version
            # For now, get all vulnerabilities and filter in code

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=120,  # Security audits can take longer
                cwd=self.project_root,
            )

            vulnerabilities = []
            severity_breakdown = {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "unknown": 0,
            }

            if format_type == "json":
                try:
                    audit_data = json.loads(result.stdout)

                    # Handle different pip-audit JSON formats
                    if isinstance(audit_data, dict):
                        if "vulnerabilities" in audit_data:
                            raw_vulns = audit_data["vulnerabilities"]
                        elif "vulns" in audit_data:
                            raw_vulns = audit_data["vulns"]
                        else:
                            raw_vulns = audit_data
                    elif isinstance(audit_data, list):
                        raw_vulns = audit_data
                    else:
                        raw_vulns = []

                    for vuln in raw_vulns:
                        # Extract vulnerability information
                        severity = vuln.get(
                            "severity", vuln.get("severity_level", "unknown")
                        ).lower()
                        if severity not in severity_breakdown:
                            severity = "unknown"

                        # Filter by threshold
                        if self._severity_meets_threshold(severity, severity_threshold):
                            vulnerabilities.append(
                                {
                                    "package": vuln.get(
                                        "name", vuln.get("package", "unknown")
                                    ),
                                    "installed_version": vuln.get(
                                        "installed_version",
                                        vuln.get("version", "unknown"),
                                    ),
                                    "vulnerability_id": vuln.get(
                                        "id", vuln.get("vulnerability_id", "unknown")
                                    ),
                                    "severity": severity,
                                    "description": vuln.get(
                                        "description", vuln.get("summary", "")
                                    ),
                                    "fixed_versions": vuln.get(
                                        "fixed_versions", vuln.get("fix_versions", [])
                                    ),
                                    "cve_id": (
                                        vuln.get("aliases", [{}])[0].get("CVE", "")
                                        if isinstance(vuln.get("aliases"), list)
                                        and vuln.get("aliases")
                                        else None
                                    ),
                                }
                            )
                            severity_breakdown[severity] += 1

                except json.JSONDecodeError:
                    # Fallback to text parsing if JSON fails
                    if result.stdout:
                        vulnerabilities = self._parse_text_audit_output(
                            result.stdout, severity_threshold
                        )
                        for vuln in vulnerabilities:
                            severity = vuln.get("severity", "unknown").lower()
                            if severity in severity_breakdown:
                                severity_breakdown[severity] += 1
            else:
                # Text format
                if result.stdout:
                    vulnerabilities = self._parse_text_audit_output(
                        result.stdout, severity_threshold
                    )
                    for vuln in vulnerabilities:
                        severity = vuln.get("severity", "unknown").lower()
                        if severity in severity_breakdown:
                            severity_breakdown[severity] += 1

            return {
                "vulnerabilities": vulnerabilities,
                "vulnerability_count": len(vulnerabilities),
                "severity_breakdown": severity_breakdown,
                "threshold": severity_threshold,
            }

        except subprocess.TimeoutExpired:
            return {
                "vulnerabilities": [],
                "vulnerability_count": 0,
                "severity_breakdown": {},
                "error": "pip-audit timed out",
            }
        except FileNotFoundError:
            return {
                "vulnerabilities": [],
                "vulnerability_count": 0,
                "severity_breakdown": {},
                "error": "pip-audit not found",
            }
        except Exception as e:
            return {
                "vulnerabilities": [],
                "vulnerability_count": 0,
                "severity_breakdown": {},
                "error": str(e),
            }

    def check_outdated(self) -> dict[str, Any] | None:
        """
        Identify outdated packages.

        Note: pip-audit doesn't directly check for outdated packages.
        This method uses pip list --outdated as a fallback.

        Returns:
            Dictionary with:
            - outdated_packages: List of outdated packages
            - outdated_count: Number of outdated packages
        """
        try:
            # Use pip list --outdated --format=json
            result = subprocess.run(  # nosec B603 - fixed module invocation
                [sys.executable, "-m", "pip", "list", "--outdated", "--format=json"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.project_root,
            )

            if result.returncode != 0:
                return {
                    "outdated_packages": [],
                    "outdated_count": 0,
                    "error": f"pip list failed: {result.stderr}",
                }

            try:
                outdated_data = json.loads(result.stdout)
                outdated_packages = []

                for pkg in outdated_data:
                    outdated_packages.append(
                        {
                            "package": pkg.get("name", "unknown"),
                            "current_version": pkg.get("version", "unknown"),
                            "latest_version": pkg.get("latest_version", "unknown"),
                        }
                    )

                return {
                    "outdated_packages": outdated_packages,
                    "outdated_count": len(outdated_packages),
                }

            except json.JSONDecodeError:
                return {
                    "outdated_packages": [],
                    "outdated_count": 0,
                    "error": "Failed to parse pip list output",
                }

        except subprocess.TimeoutExpired:
            return {
                "outdated_packages": [],
                "outdated_count": 0,
                "error": "pip list timed out",
            }
        except FileNotFoundError:
            return {
                "outdated_packages": [],
                "outdated_count": 0,
                "error": "pip not found",
            }
        except Exception as e:
            return {"outdated_packages": [], "outdated_count": 0, "error": str(e)}

    def _count_packages(self, tree_json: Any) -> int:
        """Count total packages in dependency tree."""
        count = 0

        if isinstance(tree_json, dict):
            # pipdeptree JSON format
            if "package" in tree_json:
                count = 1
                if "dependencies" in tree_json:
                    for dep in tree_json["dependencies"]:
                        count += self._count_packages(dep)
            else:
                # List of packages
                for item in (
                    tree_json.values() if hasattr(tree_json, "values") else [tree_json]
                ):
                    count += self._count_packages(item)
        elif isinstance(tree_json, list):
            for item in tree_json:
                count += self._count_packages(item)

        return count

    def _severity_meets_threshold(self, severity: str, threshold: str) -> bool:
        """Check if severity meets threshold."""
        severity_levels = {
            "critical": 4,
            "high": 3,
            "medium": 2,
            "low": 1,
            "unknown": 0,
        }
        threshold_level = severity_levels.get(threshold.lower(), 0)
        severity_level = severity_levels.get(severity.lower(), 0)
        return severity_level >= threshold_level

    def _parse_text_audit_output(
        self, text: str, threshold: str
    ) -> list[dict[str, Any]]:
        """Parse text output from pip-audit (fallback)."""
        vulnerabilities = []
        lines = text.split("\n")

        for line in lines:
            if "VULN" in line.upper() or "CVE" in line.upper():
                # Try to extract vulnerability info
                parts = line.split()
                if len(parts) >= 2:
                    vulnerabilities.append(
                        {
                            "package": parts[0] if parts else "unknown",
                            "vulnerability_id": (
                                parts[1] if len(parts) > 1 else "unknown"
                            ),
                            "severity": "unknown",
                            "description": line,
                        }
                    )

        return vulnerabilities
