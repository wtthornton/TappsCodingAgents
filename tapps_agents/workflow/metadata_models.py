"""
Structured Metadata Models for Workflow Artifacts.

Defines TypedDict and Pydantic models for structured metadata, plan details,
task inputs, and task results.
"""

from __future__ import annotations

import sys
from typing import Any

from pydantic import BaseModel, Field

# Pydantic requires typing_extensions.TypedDict on Python < 3.12
if sys.version_info >= (3, 12):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


class ArtifactMetadata(TypedDict, total=False):
    """
    Flexible but typed metadata structure for artifacts.

    Uses TypedDict with total=False to allow partial metadata while maintaining
    type hints for known fields.
    """

    agent_version: str
    execution_context: str
    custom_tags: list[str]
    related_artifacts: list[str]
    workflow_id: str
    step_id: str
    agent_id: str
    execution_mode: str


class PlanDetails(BaseModel):
    """Structured plan information for planning artifacts."""

    summary: str
    estimated_duration_hours: float | None = None
    key_risks: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    objectives: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class TaskInputs(BaseModel):
    """Structured task inputs for agent task assignments."""

    files: list[str] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)
    options: dict[str, Any] = Field(default_factory=dict)
    environment: dict[str, str] = Field(default_factory=dict)
    parameters: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class TaskResults(BaseModel):
    """Structured task results for agent task completions."""

    output_files: list[str] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)
    artifacts: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    output: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class RetryPolicy(BaseModel):
    """Structured retry policy for task assignments."""

    max_retries: int = Field(default=0, ge=0)
    backoff_seconds: int = Field(default=60, ge=0)
    backoff_multiplier: float = Field(default=2.0, gt=0)
    max_backoff_seconds: int | None = Field(default=None, ge=0)

    model_config = {"extra": "forbid"}
