"""
Operations Analysis Artifact Schema.

Defines versioned JSON schema for operations results from Background Agents.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SecurityIssue:
    """Security issue found during scanning."""

    severity: str  # "high", "medium", "low", "info"
    issue_type: str
    description: str
    file_path: str | None = None
    line: int | None = None
    recommendation: str | None = None


@dataclass
class ComplianceCheck:
    """Compliance check result."""

    check: str
    status: str  # "pass", "fail", "warning", "error"
    message: str
    recommendation: str | None = None


@dataclass
class DeploymentStep:
    """Deployment step."""

    step: int
    action: str
    command: str | None = None
    description: str | None = None
    status: str = "pending"  # "pending", "completed", "failed", "skipped"


@dataclass
class InfrastructureFile:
    """Infrastructure file created."""

    file_path: str
    file_type: str  # "dockerfile", "docker-compose", "kubernetes", "terraform"
    status: str = "created"  # "created", "updated", "error"
    error_message: str | None = None


@dataclass
class OperationsArtifact:
    """
    Versioned operations artifact.

    Schema version: 1.0
    """

    schema_version: str = "1.0"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"  # "pending", "running", "completed", "failed", "cancelled", "timeout"
    worktree_path: str | None = None
    correlation_id: str | None = None

    # Operation type
    operation_type: str | None = None  # "security_scan", "compliance_check", "deploy", "infrastructure_setup", "dependency_audit"

    # Security scan results
    security_issues: list[SecurityIssue] = field(default_factory=list)
    security_issue_count: int = 0
    security_severity_breakdown: dict[str, int] = field(default_factory=dict)

    # Compliance check results
    compliance_type: str | None = None
    compliance_status: str | None = None  # "compliant", "non_compliant", "partial", "unknown"
    compliance_checks: list[ComplianceCheck] = field(default_factory=list)

    # Deployment results
    deployment_target: str | None = None
    deployment_environment: str | None = None
    deployment_steps: list[DeploymentStep] = field(default_factory=list)
    deployment_status: str | None = None  # "planned", "executed", "failed"

    # Infrastructure setup results
    infrastructure_type: str | None = None
    infrastructure_files: list[InfrastructureFile] = field(default_factory=list)

    # Dependency audit results
    dependency_vulnerabilities: list[dict[str, Any]] = field(default_factory=list)
    vulnerability_count: int = 0
    severity_breakdown: dict[str, int] = field(default_factory=dict)
    tools_available: dict[str, bool] = field(default_factory=dict)

    # Error information
    error: str | None = None
    cancelled: bool = False
    timeout: bool = False

    # Metadata
    execution_time_seconds: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert nested objects to dicts
        data["security_issues"] = [asdict(si) for si in self.security_issues]
        data["compliance_checks"] = [asdict(cc) for cc in self.compliance_checks]
        data["deployment_steps"] = [asdict(ds) for ds in self.deployment_steps]
        data["infrastructure_files"] = [asdict(inf) for inf in self.infrastructure_files]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OperationsArtifact:
        """Create from dictionary."""
        # Convert nested dicts back to objects
        if "security_issues" in data:
            data["security_issues"] = [
                SecurityIssue(**si) for si in data["security_issues"]
            ]
        if "compliance_checks" in data:
            data["compliance_checks"] = [
                ComplianceCheck(**cc) for cc in data["compliance_checks"]
            ]
        if "deployment_steps" in data:
            data["deployment_steps"] = [
                DeploymentStep(**ds) for ds in data["deployment_steps"]
            ]
        if "infrastructure_files" in data:
            data["infrastructure_files"] = [
                InfrastructureFile(**inf) for inf in data["infrastructure_files"]
            ]
        return cls(**data)

    def add_security_issue(self, issue: SecurityIssue) -> None:
        """Add a security issue."""
        self.security_issues.append(issue)
        self.security_issue_count += 1
        severity = issue.severity.lower()
        self.security_severity_breakdown[severity] = (
            self.security_severity_breakdown.get(severity, 0) + 1
        )

    def add_compliance_check(self, check: ComplianceCheck) -> None:
        """Add a compliance check result."""
        self.compliance_checks.append(check)

    def add_deployment_step(self, step: DeploymentStep) -> None:
        """Add a deployment step."""
        self.deployment_steps.append(step)

    def add_infrastructure_file(self, file: InfrastructureFile) -> None:
        """Add an infrastructure file."""
        self.infrastructure_files.append(file)

    def mark_completed(self) -> None:
        """Mark operation as completed."""
        self.status = "completed"

    def mark_failed(self, error: str) -> None:
        """Mark operation as failed."""
        self.status = "failed"
        self.error = error

    def mark_cancelled(self) -> None:
        """Mark operation as cancelled."""
        self.status = "cancelled"
        self.cancelled = True

    def mark_timeout(self) -> None:
        """Mark operation as timed out."""
        self.status = "timeout"
        self.timeout = True
