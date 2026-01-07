"""
Structured Step Result Types for Simple Mode Workflows.

Pydantic v2 BaseModel implementations for validated, type-safe step results.
Uses Python 3.13+ patterns including union types and modern type hints.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class StepStatus(str, Enum):
    """Step execution status."""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    PENDING = "pending"
    RUNNING = "running"


class BaseStepResult(BaseModel):
    """Base class for all step results with common fields."""

    step_number: int = Field(ge=1, le=9)
    step_name: str
    status: StepStatus = StepStatus.PENDING
    agent_name: str
    start_time: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    end_time: str | None = None
    duration_seconds: float | None = None
    error_message: str | None = None
    raw_output: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": False, "extra": "allow"}


class EnhancerStepResult(BaseStepResult):
    """Step 1: Enhancer result with 7-stage pipeline output."""

    enhanced_prompt: str = ""
    requirements: list[str] = Field(default_factory=list)
    architecture_guidance: str = ""
    quality_standards: str = ""
    synthesis: dict[str, Any] = Field(default_factory=dict)
    context7_info: dict[str, Any] = Field(default_factory=dict)


class PlannerStepResult(BaseStepResult):
    """Step 2: Planner result with user stories."""

    stories: list[dict[str, Any]] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    story_points: int = 0
    epic_id: str | None = None
    estimated_complexity: int = 0

    @model_validator(mode="after")
    def validate_stories(self):
        """Ensure stories have required fields."""
        for story in self.stories:
            if "title" not in story and "id" not in story:
                # Add fallback title
                story["title"] = "Untitled Story"
        return self


class ArchitectStepResult(BaseStepResult):
    """Step 3: Architect result with system design."""

    architecture_pattern: str = ""
    components: list[dict[str, Any]] = Field(default_factory=list)
    data_flow: str = ""
    technology_stack: list[str] = Field(default_factory=list)
    scalability_notes: str = ""
    security_considerations: str = ""
    diagram: str = ""


class DesignerStepResult(BaseStepResult):
    """Step 4: Designer result with API/data model design."""

    api_endpoints: list[dict[str, Any]] = Field(default_factory=list)
    data_models: list[dict[str, Any]] = Field(default_factory=list)
    ui_components: list[dict[str, Any]] = Field(default_factory=list)
    design_system_elements: dict[str, Any] = Field(default_factory=dict)
    openapi_spec: dict[str, Any] | None = None


class ImplementerStepResult(BaseStepResult):
    """Step 5: Implementer result with generated code."""

    files_created: list[str] = Field(default_factory=list)
    files_modified: list[str] = Field(default_factory=list)
    code_preview: str = ""
    backup_path: str | None = None


class ReviewerStepResult(BaseStepResult):
    """Step 6: Reviewer result with quality scores."""

    overall_score: float = Field(default=0.0, ge=0.0, le=100.0)
    complexity_score: float = Field(default=0.0, ge=0.0, le=10.0)
    security_score: float = Field(default=0.0, ge=0.0, le=10.0)
    maintainability_score: float = Field(default=0.0, ge=0.0, le=10.0)
    test_coverage_score: float = Field(default=0.0, ge=0.0, le=10.0)
    performance_score: float = Field(default=0.0, ge=0.0, le=10.0)
    issues: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class QAStepResult(BaseStepResult):
    """Step 7: Tester result with test generation."""

    test_files_created: list[str] = Field(default_factory=list)
    test_count: int = 0
    coverage_percent: float | None = None
    test_plan: str = ""


class VerificationStepResult(BaseStepResult):
    """Step 8: Verification result with completeness check."""

    complete: bool = False
    gaps: list[dict[str, Any]] = Field(default_factory=list)
    loopback_step: int | None = None
    deliverables_verified: int = 0
    deliverables_total: int = 0


# Type alias for any step result (Python 3.10+ union syntax)
StepResult = (
    EnhancerStepResult
    | PlannerStepResult
    | ArchitectStepResult
    | DesignerStepResult
    | ImplementerStepResult
    | ReviewerStepResult
    | QAStepResult
    | VerificationStepResult
)


class StepResultParser:
    """Parse raw agent results into structured Pydantic models."""

    _parsers: dict[str, type[BaseStepResult]] = {
        "enhancer": EnhancerStepResult,
        "planner": PlannerStepResult,
        "architect": ArchitectStepResult,
        "designer": DesignerStepResult,
        "implementer": ImplementerStepResult,
        "reviewer": ReviewerStepResult,
        "tester": QAStepResult,
        "verification": VerificationStepResult,
    }

    @classmethod
    def parse(
        cls, agent_name: str, raw: dict[str, Any], step_number: int
    ) -> BaseStepResult:
        """Parse raw result into structured type with validation.

        Args:
            agent_name: Name of the agent that produced the result
            raw: Raw result dictionary from agent execution
            step_number: Step number in the workflow

        Returns:
            Structured step result with proper type
        """
        result_class = cls._parsers.get(agent_name, BaseStepResult)

        # Handle nested result structure
        actual_result = raw.get("result", raw)
        if isinstance(actual_result, str):
            # Handle string results (error messages or raw output)
            actual_result = {"raw_output": {"content": actual_result}}

        # Check for error in result
        if isinstance(actual_result, dict) and actual_result.get("error"):
            return result_class(
                step_number=step_number,
                step_name=agent_name,
                status=StepStatus.FAILED,
                agent_name=agent_name,
                error_message=str(actual_result["error"]),
                raw_output=actual_result,
            )

        # Build result data
        result_data = {
            "step_number": step_number,
            "step_name": agent_name,
            "status": StepStatus.SUCCESS,
            "agent_name": agent_name,
            "raw_output": actual_result if isinstance(actual_result, dict) else {},
        }

        # Merge actual result fields (excluding reserved fields)
        if isinstance(actual_result, dict):
            reserved_fields = {"step_number", "step_name", "status", "agent_name"}
            for key, value in actual_result.items():
                if key not in reserved_fields:
                    result_data[key] = value

        # Parse with Pydantic validation
        try:
            return result_class.model_validate(result_data)
        except Exception as e:
            # Fallback to base result on validation error
            return BaseStepResult(
                step_number=step_number,
                step_name=agent_name,
                status=StepStatus.SUCCESS,
                agent_name=agent_name,
                raw_output=actual_result if isinstance(actual_result, dict) else {},
                error_message=f"Validation warning: {e}",
            )

    @classmethod
    def create_failed_result(
        cls,
        agent_name: str,
        step_number: int,
        error_message: str,
    ) -> BaseStepResult:
        """Create a failed step result.

        Args:
            agent_name: Name of the agent
            step_number: Step number in the workflow
            error_message: Error message describing the failure

        Returns:
            Failed step result
        """
        result_class = cls._parsers.get(agent_name, BaseStepResult)
        return result_class(
            step_number=step_number,
            step_name=agent_name,
            status=StepStatus.FAILED,
            agent_name=agent_name,
            error_message=error_message,
        )

    @classmethod
    def create_skipped_result(
        cls,
        agent_name: str,
        step_number: int,
        skip_reason: str,
    ) -> BaseStepResult:
        """Create a skipped step result.

        Args:
            agent_name: Name of the agent
            step_number: Step number in the workflow
            skip_reason: Reason for skipping the step

        Returns:
            Skipped step result
        """
        result_class = cls._parsers.get(agent_name, BaseStepResult)
        return result_class(
            step_number=step_number,
            step_name=agent_name,
            status=StepStatus.SKIPPED,
            agent_name=agent_name,
            error_message=skip_reason,
        )
