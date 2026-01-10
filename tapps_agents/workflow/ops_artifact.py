"""
Operations Analysis Artifact Schema.

Defines versioned JSON schema for operations results from Background Agents.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .common_enums import ArtifactStatus, OperationType
from .metadata_models import ArtifactMetadata


class SecurityIssue(BaseModel):
    """Security issue found during scanning."""

    severity: str  # "high", "medium", "low", "info"
    issue_type: str
    description: str
    file_path: str | None = None
    line: int | None = None
    recommendation: str | None = None

    model_config = {"extra": "forbid"}


class ComplianceCheck(BaseModel):
    """Compliance check result."""

    check: str
    status: str  # "pass", "fail", "warning", "error"
    message: str
    recommendation: str | None = None

    model_config = {"extra": "forbid"}


class DeploymentStep(BaseModel):
    """Deployment step."""

    step: int
    action: str
    command: str | None = None
    description: str | None = None
    status: str = "pending"  # "pending", "completed", "failed", "skipped"

    model_config = {"extra": "forbid"}


class InfrastructureFile(BaseModel):
    """Infrastructure file created."""

    file_path: str
    file_type: str  # "dockerfile", "docker-compose", "kubernetes", "terraform"
    status: str = "created"  # "created", "updated", "error"
    error_message: str | None = None

    model_config = {"extra": "forbid"}


class OperationsArtifact(BaseModel):
    """
    Versioned operations artifact.

    Schema version: 1.0
    Migrated to Pydantic BaseModel for runtime validation and type safety.
    """

    schema_version: str = "1.0"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: ArtifactStatus = ArtifactStatus.PENDING
    worktree_path: str | None = None
    correlation_id: str | None = None

    # Operation type
    operation_type: OperationType | None = None

    # Security scan results
    security_issues: list[SecurityIssue] = Field(default_factory=list)
    security_issue_count: int = 0
    security_severity_breakdown: dict[str, int] = Field(default_factory=dict)

    # Compliance check results
    compliance_type: str | None = None
    compliance_status: str | None = None  # "compliant", "non_compliant", "partial", "unknown"
    compliance_checks: list[ComplianceCheck] = Field(default_factory=list)

    # Deployment results
    deployment_target: str | None = None
    deployment_environment: str | None = None
    deployment_steps: list[DeploymentStep] = Field(default_factory=list)
    deployment_status: str | None = None  # "planned", "executed", "failed"

    # Infrastructure setup results
    infrastructure_type: str | None = None
    infrastructure_files: list[InfrastructureFile] = Field(default_factory=list)

    # Dependency audit results
    dependency_vulnerabilities: list[dict[str, Any]] = Field(default_factory=list)
    vulnerability_count: int = 0
    severity_breakdown: dict[str, int] = Field(default_factory=dict)
    tools_available: dict[str, bool] = Field(default_factory=dict)

    # Error information
    error: str | None = None
    cancelled: bool = False
    timeout: bool = False

    # Metadata
    execution_time_seconds: float | None = None
    metadata: ArtifactMetadata = Field(default_factory=dict)

    model_config = {"extra": "forbid"}

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

    def add_infrastructure_file(self, infra_file: InfrastructureFile) -> None:
        """Add an infrastructure file."""
        self.infrastructure_files.append(infra_file)

    def mark_completed(self) -> None:
        """Mark operations as completed."""
        self.status = ArtifactStatus.COMPLETED

    def mark_failed(self, error: str) -> None:
        """Mark operations as failed."""
        self.status = ArtifactStatus.FAILED
        self.error = error

    def mark_cancelled(self) -> None:
        """Mark operations as cancelled."""
        self.status = ArtifactStatus.CANCELLED
        self.cancelled = True

    def mark_timeout(self) -> None:
        """Mark operations as timed out."""
        self.status = ArtifactStatus.TIMEOUT
        self.timeout = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OperationsArtifact:
        """
        Create from dictionary (backward compatibility with old dataclass format).

        This method supports both old dataclass format and new Pydantic format.
        """
        # Try Pydantic validation first (new format)
        try:
            return cls.model_validate(data)
        except Exception:
            # Fall back to manual conversion (old dataclass format)
            return cls._from_dict_legacy(data)

    @classmethod
    def _from_dict_legacy(cls, data: dict[str, Any]) -> OperationsArtifact:
        """Convert from legacy dataclass format."""
        # Convert security_issues from list of dicts to list of SecurityIssue objects
        security_issues = []
        if "security_issues" in data:
            for si_data in data["security_issues"]:
                if isinstance(si_data, dict):
                    security_issues.append(SecurityIssue(**si_data))
                else:
                    security_issues.append(si_data)

        # Convert compliance_checks from list of dicts to list of ComplianceCheck objects
        compliance_checks = []
        if "compliance_checks" in data:
            for cc_data in data["compliance_checks"]:
                if isinstance(cc_data, dict):
                    compliance_checks.append(ComplianceCheck(**cc_data))
                else:
                    compliance_checks.append(cc_data)

        # Convert deployment_steps from list of dicts to list of DeploymentStep objects
        deployment_steps = []
        if "deployment_steps" in data:
            for ds_data in data["deployment_steps"]:
                if isinstance(ds_data, dict):
                    deployment_steps.append(DeploymentStep(**ds_data))
                else:
                    deployment_steps.append(ds_data)

        # Convert infrastructure_files from list of dicts to list of InfrastructureFile objects
        infrastructure_files = []
        if "infrastructure_files" in data:
            for inf_data in data["infrastructure_files"]:
                if isinstance(inf_data, dict):
                    infrastructure_files.append(InfrastructureFile(**inf_data))
                else:
                    infrastructure_files.append(inf_data)

        # Convert status string to enum
        status = ArtifactStatus.PENDING
        if "status" in data and data["status"]:
            try:
                status = ArtifactStatus(data["status"].lower())
            except ValueError:
                pass

        # Convert operation_type string to enum
        operation_type = None
        if "operation_type" in data and data["operation_type"]:
            try:
                operation_type = OperationType(data["operation_type"].lower().replace("-", "_"))
            except ValueError:
                pass

        # Build new artifact
        artifact_data = data.copy()
        artifact_data["security_issues"] = security_issues
        artifact_data["compliance_checks"] = compliance_checks
        artifact_data["deployment_steps"] = deployment_steps
        artifact_data["infrastructure_files"] = infrastructure_files
        artifact_data["status"] = status
        artifact_data["operation_type"] = operation_type

        # Remove methods that might cause issues
        artifact_data.pop("to_dict", None)
        artifact_data.pop("from_dict", None)
        artifact_data.pop("add_security_issue", None)
        artifact_data.pop("add_compliance_check", None)
        artifact_data.pop("add_deployment_step", None)
        artifact_data.pop("add_infrastructure_file", None)
        artifact_data.pop("mark_completed", None)
        artifact_data.pop("mark_failed", None)
        artifact_data.pop("mark_cancelled", None)
        artifact_data.pop("mark_timeout", None)

        return cls(**artifact_data)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary (backward compatibility method).

        For new code, use model_dump(mode="json") instead.
        """
        return self.model_dump(mode="json", exclude_none=False)
