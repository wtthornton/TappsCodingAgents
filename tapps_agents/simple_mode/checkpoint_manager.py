"""
Checkpoint Manager System - Mid-Execution Workflow Checkpoints.

Provides checkpoint analysis after the Planning step in workflows to detect
when the current workflow is overkill for the task. Offers users the option
to switch to a more appropriate workflow with token/time savings estimates.

Performance:
    - Checkpoint analysis: < 500ms (P99 latency)
    - In-memory analysis only (no I/O during analysis)

Thread Safety:
    - Not thread-safe (single-threaded orchestrator execution)

Examples:
    >>> manager = CheckpointManager()
    >>> planning = {"story_points": 8, "files_affected": 3}
    >>> analysis = manager.analyze_checkpoint(
    ...     "*full", ["enhance", "plan"], planning
    ... )
    >>> analysis.mismatch_detected
    True
    >>> analysis.recommended_workflow
    "*build"
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, TypedDict

from .workflow_suggester import COMPLEXITY_ORDER, SCOPE_ORDER, WORKFLOW_REQUIREMENTS

# ============================================================================
# Type Aliases
# ============================================================================

WorkflowType = Literal["*full", "*build", "*fix", "*refactor"]
ScopeLevel = Literal["low", "medium", "high"]
ComplexityLevel = Literal["low", "medium", "high"]


# ============================================================================
# Data Models
# ============================================================================

class PlanningResults(TypedDict, total=False):
    """
    Type-safe dict for planning step results.

    Attributes:
        story_points: Estimated story points from planner (1, 2, 3, 5, 8, 13, 21)
        files_affected: Number of files affected by the task
        user_stories: List of user story dictionaries
        architectural_impact: Architectural impact level (low, medium, high)
        complexity_estimate: Complexity estimate from planner
    """

    story_points: int
    files_affected: int
    user_stories: list[dict[str, Any]]
    architectural_impact: str
    complexity_estimate: str


class SwitchResult(TypedDict):
    """
    Type-safe dict for workflow switch results.

    Attributes:
        success: Whether the workflow switch succeeded
        new_workflow_id: New workflow ID (same as original for continuity)
        preserved_artifacts: List of preserved artifact step names
        resume_from_step: Step to resume from in new workflow
        error: Error message if switch failed, None otherwise
    """

    success: bool
    new_workflow_id: str
    preserved_artifacts: list[str]
    resume_from_step: str
    error: str | None


@dataclass(frozen=True)
class CheckpointAnalysis:
    """
    Immutable analysis results from checkpoint evaluation.

    Represents detected workflow mismatch characteristics and recommendations
    for workflow switching, calculated from planning artifacts.

    Attributes:
        mismatch_detected: Whether workflow mismatch was detected
        current_workflow: Current workflow being executed
        recommended_workflow: Suggested workflow (None if no mismatch)
        confidence: Confidence in recommendation (0.7-1.0)

        detected_scope: Task scope from planning (low/medium/high)
        detected_complexity: Complexity from story points (low/medium/high)
        story_points: Estimated story points from planning
        files_affected: Number of files affected

        completed_steps: Tuple of completed workflow steps (immutable)
        remaining_steps: Tuple of remaining workflow steps (immutable)

        token_savings: Estimated tokens saved by switching
        time_savings: Estimated minutes saved by switching
        steps_saved: Number of workflow steps saved

        reason: Human-readable explanation for recommendation

    Validation:
        - confidence must be 0.0-1.0
        - story_points must be positive
        - files_affected must be non-negative
        - savings estimates must be non-negative

    Immutability:
        frozen=True ensures analysis data cannot be modified after creation
    """

    mismatch_detected: bool
    current_workflow: WorkflowType
    recommended_workflow: WorkflowType | None
    confidence: float  # 0.0-1.0

    # Task characteristics
    detected_scope: ScopeLevel
    detected_complexity: ComplexityLevel
    story_points: int
    files_affected: int

    # Workflow steps
    completed_steps: tuple[str, ...]
    remaining_steps: tuple[str, ...]

    # Savings estimates
    token_savings: int
    time_savings: int  # minutes
    steps_saved: int

    # User messaging
    reason: str

    def __post_init__(self) -> None:
        """Validate field constraints."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be 0.0-1.0, got {self.confidence}")
        if self.story_points < 0:
            raise ValueError(f"story_points must be positive, got {self.story_points}")
        if self.files_affected < 0:
            raise ValueError(f"files_affected must be non-negative, got {self.files_affected}")
        if self.token_savings < 0 or self.time_savings < 0 or self.steps_saved < 0:
            raise ValueError("Savings estimates must be non-negative")


@dataclass
class ArtifactManifest:
    """
    Manifest for preserved workflow artifacts.

    Tracks which artifacts were preserved during workflow switching to enable
    seamless resume and avoid re-running completed steps.

    Attributes:
        workflow_id: Original workflow identifier
        original_workflow: Original workflow type
        new_workflow: New workflow type switched to
        timestamp: When artifacts were preserved (ISO 8601 UTC)
        completed_steps: Steps that were completed before switch
        artifacts: Mapping of step_name → relative_file_path

    JSON Schema:
        {
            "workflow_id": str,
            "original_workflow": str,
            "new_workflow": str,
            "timestamp": str (ISO 8601),
            "completed_steps": [str],
            "artifacts": {str: str}
        }
    """

    workflow_id: str
    original_workflow: WorkflowType
    new_workflow: WorkflowType
    timestamp: str  # ISO 8601 UTC
    completed_steps: list[str]
    artifacts: dict[str, str]  # step_name → relative_file_path

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to JSON-serializable dict.

        Returns:
            Dictionary suitable for JSON serialization
        """
        return {
            "workflow_id": self.workflow_id,
            "original_workflow": self.original_workflow,
            "new_workflow": self.new_workflow,
            "timestamp": self.timestamp,
            "completed_steps": self.completed_steps,
            "artifacts": self.artifacts,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ArtifactManifest:
        """
        Create ArtifactManifest from JSON dict.

        Args:
            data: Dictionary from JSON deserialization

        Returns:
            ArtifactManifest instance

        Raises:
            KeyError: If required keys are missing
        """
        return cls(
            workflow_id=data["workflow_id"],
            original_workflow=data["original_workflow"],
            new_workflow=data["new_workflow"],
            timestamp=data["timestamp"],
            completed_steps=data["completed_steps"],
            artifacts=data["artifacts"],
        )


# ============================================================================
# CheckpointManager
# ============================================================================

class CheckpointManager:
    """
    Manages mid-execution workflow checkpoints.

    Analyzes workflow progress at strategic points (after Planning step) to detect
    when the current workflow is overkill for the task. Offers users the option to
    switch to a more appropriate workflow with token/time savings estimates.

    Responsibilities:
        - Analyze planning artifacts (story points, files, complexity)
        - Detect workflow mismatch based on planning results
        - Calculate token/time savings estimates
        - Generate user-friendly checkpoint prompts

    Performance:
        Target: < 500ms for checkpoint analysis (P99 latency)
        Uses in-memory analysis only (no I/O during analysis)

    Thread Safety:
        Not thread-safe (single-threaded orchestrator execution)

    Testability:
        - No global state
        - Dependency injection via constructor
        - Pure functions for analysis logic
    """

    def __init__(
        self,
        token_estimates: dict[str, int] | None = None,
        time_estimates: dict[str, int] | None = None,
    ) -> None:
        """
        Initialize checkpoint manager.

        Args:
            token_estimates: Custom token estimates per step (optional)
                Default: {"enhance": 2000, "plan": 3000, ...}
            time_estimates: Custom time estimates per step in minutes (optional)
                Default: {"enhance": 2, "plan": 5, ...}

        Raises:
            ValueError: If estimates contain negative values
        """
        self.token_estimates = token_estimates or self._default_token_estimates()
        self.time_estimates = time_estimates or self._default_time_estimates()

        # Validate estimates
        if any(v < 0 for v in self.token_estimates.values()):
            raise ValueError("Token estimates must be non-negative")
        if any(v < 0 for v in self.time_estimates.values()):
            raise ValueError("Time estimates must be non-negative")

    def analyze_checkpoint(
        self,
        workflow: WorkflowType,
        completed_steps: list[str],
        planning_results: PlanningResults,
    ) -> CheckpointAnalysis:
        """
        Analyze checkpoint to detect workflow mismatch.

        Examines planning artifacts (user stories, story points, files affected)
        to determine if the current workflow is appropriate. Detects mismatches
        when task complexity/scope doesn't justify the workflow overhead.

        Args:
            workflow: Current workflow being executed
            completed_steps: List of completed workflow steps
            planning_results: Planning step outputs with task characteristics

        Returns:
            CheckpointAnalysis with mismatch detection and recommendations

        Raises:
            ValueError: If workflow is unknown or completed_steps is empty
            TypeError: If planning_results is missing required keys

        Performance:
            Target: < 500ms (in-memory analysis only, no I/O)

        Examples:
            >>> manager = CheckpointManager()
            >>> planning = {"story_points": 8, "files_affected": 3}
            >>> analysis = manager.analyze_checkpoint(
            ...     "*full", ["enhance", "plan"], planning
            ... )
            >>> analysis.mismatch_detected
            True
            >>> analysis.recommended_workflow
            "*build"
        """
        # Parameter validation
        if workflow not in ("*full", "*build", "*fix", "*refactor"):
            raise ValueError(f"Unknown workflow: {workflow}")
        if not completed_steps:
            raise ValueError("completed_steps must not be empty")
        if "story_points" not in planning_results:
            raise TypeError("planning_results missing required key: story_points")

        # Step 1: Extract task characteristics from planning
        characteristics = self._analyze_planning_artifacts(planning_results)

        # Step 2: Detect workflow mismatch
        mismatch_detected, recommended = self._detect_workflow_mismatch(
            workflow, characteristics
        )

        # Step 3: Calculate token/time savings
        token_savings, time_savings, steps_saved = self._calculate_savings(
            workflow, recommended, completed_steps
        )

        # Step 4: Generate user-friendly reason message
        reason = self._generate_reason(workflow, recommended, characteristics)

        # Step 5: Get remaining steps for current workflow
        all_steps = self._get_workflow_steps(workflow)
        remaining = tuple(s for s in all_steps if s not in completed_steps)

        return CheckpointAnalysis(
            mismatch_detected=mismatch_detected,
            current_workflow=workflow,
            recommended_workflow=recommended,
            confidence=0.85,  # High confidence from planning data
            detected_scope=characteristics["scope"],
            detected_complexity=characteristics["complexity"],
            story_points=characteristics["story_points"],
            files_affected=characteristics["files_affected"],
            completed_steps=tuple(completed_steps),
            remaining_steps=remaining,
            token_savings=token_savings,
            time_savings=time_savings,
            steps_saved=steps_saved,
            reason=reason,
        )

    def _analyze_planning_artifacts(
        self, planning_results: PlanningResults
    ) -> dict[str, Any]:
        """
        Extract task characteristics from planning artifacts.

        Maps planning outputs (story points, files, user stories) to
        standardized characteristics (scope, complexity).

        Heuristics:
            Scope (files affected):
            - low: 1-3 files (focused change)
            - medium: 4-6 files (moderate reach)
            - high: 7+ files (system-wide)

            Complexity (story points):
            - low: 1-5 story points (simple task)
            - medium: 8-13 story points (moderate task)
            - high: 21+ story points (complex task)

        Args:
            planning_results: Planning step outputs

        Returns:
            Dict with scope, complexity, story_points, files_affected
        """
        story_points = planning_results.get("story_points", 5)
        files_affected = planning_results.get("files_affected", 3)

        # Map files_affected to scope level
        if files_affected <= 3:
            scope: ScopeLevel = "low"
        elif files_affected <= 6:
            scope = "medium"
        else:
            scope = "high"

        # Map story_points to complexity level
        if story_points <= 5:
            complexity: ComplexityLevel = "low"
        elif story_points <= 13:
            complexity = "medium"
        else:
            complexity = "high"

        return {
            "scope": scope,
            "complexity": complexity,
            "story_points": story_points,
            "files_affected": files_affected,
        }

    def _detect_workflow_mismatch(
        self,
        workflow: WorkflowType,
        characteristics: dict[str, Any],
    ) -> tuple[bool, WorkflowType | None]:
        """
        Detect if workflow doesn't match task characteristics.

        Compares task characteristics against workflow requirements to determine
        if the current workflow is overkill or inappropriate.

        Logic:
            - *full requires high complexity OR high scope
            - If task is too simple for *full → recommend *fix or *build
            - *build and *fix are generally appropriate (no downgrade)

        Args:
            workflow: Current workflow type
            characteristics: Task characteristics from planning

        Returns:
            Tuple of (mismatch_detected, recommended_workflow)
            recommended_workflow is None if no mismatch
        """
        requirements = WORKFLOW_REQUIREMENTS.get(workflow)
        if not requirements:
            return (False, None)  # Unknown workflow, no recommendation

        # Check if task is too simple for *full workflow
        if workflow == "*full":
            # *full requires high complexity OR high scope
            task_complexity = COMPLEXITY_ORDER[characteristics["complexity"]]
            task_scope = SCOPE_ORDER[characteristics["scope"]]

            if task_complexity < COMPLEXITY_ORDER["high"] and task_scope < SCOPE_ORDER["high"]:
                # Too simple for *full workflow
                if characteristics["complexity"] == "low":
                    # Low complexity → recommend *fix workflow
                    return (True, "*fix")
                else:
                    # Medium complexity → recommend *build workflow
                    return (True, "*build")

        # No mismatch detected
        return (False, None)

    def _calculate_savings(
        self,
        current_workflow: WorkflowType,
        recommended_workflow: WorkflowType | None,
        completed_steps: list[str],
    ) -> tuple[int, int, int]:
        """
        Calculate token/time savings from switching workflows.

        Computes the savings by comparing remaining steps in current workflow
        versus remaining steps in recommended workflow.

        Args:
            current_workflow: Current workflow type
            recommended_workflow: Recommended workflow (None if no mismatch)
            completed_steps: List of completed steps

        Returns:
            Tuple of (token_savings, time_savings_minutes, steps_saved)
        """
        if not recommended_workflow:
            return (0, 0, 0)

        # Get workflow step sequences
        current_steps = self._get_workflow_steps(current_workflow)
        recommended_steps = self._get_workflow_steps(recommended_workflow)

        # Calculate remaining steps in each workflow
        remaining_current = [s for s in current_steps if s not in completed_steps]
        remaining_recommended = [s for s in recommended_steps if s not in completed_steps]

        # Calculate steps saved
        steps_saved = len(remaining_current) - len(remaining_recommended)

        # Calculate token savings
        token_savings = sum(
            self.token_estimates.get(step, 5000)
            for step in remaining_current
            if step not in remaining_recommended
        )

        # Calculate time savings (minutes)
        time_savings = sum(
            self.time_estimates.get(step, 5)
            for step in remaining_current
            if step not in remaining_recommended
        )

        return (token_savings, time_savings, steps_saved)

    def _get_workflow_steps(self, workflow: WorkflowType) -> list[str]:
        """
        Get workflow step sequence.

        Args:
            workflow: Workflow type

        Returns:
            List of step names in execution order
        """
        workflow_steps: dict[WorkflowType, list[str]] = {
            "*full": ["enhance", "plan", "architect", "design", "implement", "review", "test", "security", "document"],
            "*build": ["enhance", "plan", "architect", "design", "implement", "review", "test"],
            "*fix": ["debug", "implement", "test"],
            "*refactor": ["review", "design", "implement", "test"],
        }
        return workflow_steps.get(workflow, [])

    def _generate_reason(
        self,
        current_workflow: WorkflowType,
        recommended_workflow: WorkflowType | None,
        characteristics: dict[str, Any],
    ) -> str:
        """
        Generate human-readable reason for recommendation.

        Args:
            current_workflow: Current workflow type
            recommended_workflow: Recommended workflow (None if no mismatch)
            characteristics: Task characteristics

        Returns:
            User-friendly explanation string
        """
        if not recommended_workflow:
            return "Workflow matches task characteristics."

        return (
            f"Task characteristics ({characteristics['complexity']} complexity, "
            f"{characteristics['scope']} scope, {characteristics['story_points']} story points) "
            f"suggest {recommended_workflow} workflow is more appropriate than {current_workflow}."
        )

    @staticmethod
    def _default_token_estimates() -> dict[str, int]:
        """
        Default token estimates per workflow step.

        Returns:
            Dict mapping step_name → estimated_tokens
        """
        return {
            "enhance": 2000,
            "plan": 3000,
            "architect": 5000,
            "design": 4000,
            "implement": 10000,
            "review": 6000,
            "test": 8000,
            "security": 7000,
            "document": 5000,
        }

    @staticmethod
    def _default_time_estimates() -> dict[str, int]:
        """
        Default time estimates per workflow step (minutes).

        Returns:
            Dict mapping step_name → estimated_minutes
        """
        return {
            "enhance": 2,
            "plan": 5,
            "architect": 8,
            "design": 6,
            "implement": 15,
            "review": 10,
            "test": 12,
            "security": 8,
            "document": 6,
        }


# ============================================================================
# WorkflowSwitcher
# ============================================================================

class WorkflowSwitcher:
    """
    Handles workflow switching with artifact preservation.

    Responsibilities:
        - Preserve completed artifacts from current workflow
        - Create artifact manifest for traceability
        - Enable workflow resumption from checkpoint

    File Structure:
        .tapps-agents/checkpoints/{workflow_id}/
            manifest.json           # Artifact manifest
            artifacts/
                enhanced_prompt.md  # From enhance step
                user_stories.md     # From plan step
                architecture.md     # From architect step

    Thread Safety:
        Not thread-safe (file I/O without locking)
    """

    def __init__(self, checkpoint_dir: Path) -> None:
        """
        Initialize workflow switcher.

        Args:
            checkpoint_dir: Directory for checkpoint storage
                (.tapps-agents/checkpoints/)

        Raises:
            ValueError: If checkpoint_dir is not a directory
        """
        if not checkpoint_dir.exists():
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
        if not checkpoint_dir.is_dir():
            raise ValueError(f"checkpoint_dir must be a directory: {checkpoint_dir}")

        self.checkpoint_dir = checkpoint_dir

    def switch_workflow(
        self,
        workflow_id: str,
        from_workflow: WorkflowType,
        to_workflow: WorkflowType,
        completed_steps: list[str],
        artifacts: dict[str, Any],
    ) -> SwitchResult:
        """
        Switch from current workflow to recommended workflow.

        Preserves completed artifacts and creates resume point for new workflow.

        Args:
            workflow_id: Current workflow identifier
            from_workflow: Current workflow type
            to_workflow: New workflow type
            completed_steps: Completed workflow steps
            artifacts: Completed artifacts {step_name: artifact_data}

        Returns:
            SwitchResult with success status and metadata

        Raises:
            ValueError: If workflow_id contains invalid characters
            ValueError: If completed_steps is empty

        Side Effects:
            - Creates checkpoint directory
            - Saves artifact manifest to disk
            - Saves artifact files to disk
        """
        # Parameter validation
        if not self._is_valid_workflow_id(workflow_id):
            raise ValueError(
                f"Invalid workflow_id: {workflow_id}. "
                "Must match pattern: ^[a-z0-9-]+$"
            )
        if not completed_steps:
            raise ValueError("completed_steps must not be empty")

        try:
            # Create checkpoint directory structure
            checkpoint_path = self.checkpoint_dir / workflow_id
            checkpoint_path.mkdir(parents=True, exist_ok=True)
            artifacts_path = checkpoint_path / "artifacts"
            artifacts_path.mkdir(exist_ok=True)

            # Preserve artifacts to disk
            preserved = self._preserve_artifacts(
                artifacts_path, completed_steps, artifacts
            )

            # Create artifact manifest
            manifest = ArtifactManifest(
                workflow_id=workflow_id,
                original_workflow=from_workflow,
                new_workflow=to_workflow,
                timestamp=datetime.now(UTC).isoformat(),
                completed_steps=completed_steps,
                artifacts=preserved,
            )

            # Save manifest to disk
            manifest_path = checkpoint_path / "manifest.json"
            manifest_path.write_text(
                json.dumps(manifest.to_dict(), indent=2),
                encoding="utf-8"
            )

            # Determine resume step (first uncompleted step in new workflow)
            new_workflow_steps = self._get_workflow_steps(to_workflow)
            resume_from = next(
                (s for s in new_workflow_steps if s not in completed_steps),
                new_workflow_steps[0],
            )

            return {
                "success": True,
                "new_workflow_id": workflow_id,  # Reuse same ID for continuity
                "preserved_artifacts": list(preserved.keys()),
                "resume_from_step": resume_from,
                "error": None,
            }

        except OSError as e:
            return {
                "success": False,
                "new_workflow_id": workflow_id,
                "preserved_artifacts": [],
                "resume_from_step": "",
                "error": f"Failed to switch workflow: {e}",
            }

    def restore_artifacts(self, workflow_id: str) -> dict[str, Any] | None:
        """
        Restore preserved artifacts for resumed workflow.

        Args:
            workflow_id: Workflow identifier to restore

        Returns:
            Dict of artifacts {step_name: artifact_data}, or None if not found

        Raises:
            ValueError: If workflow_id is invalid
            IOError: If manifest file is corrupted
        """
        if not self._is_valid_workflow_id(workflow_id):
            raise ValueError(f"Invalid workflow_id: {workflow_id}")

        # Load manifest
        manifest_path = self.checkpoint_dir / workflow_id / "manifest.json"
        if not manifest_path.exists():
            return None

        try:
            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest = ArtifactManifest.from_dict(manifest_data)
        except (json.JSONDecodeError, KeyError) as e:
            raise OSError(f"Corrupted manifest file: {e}") from e

        # Load all artifacts from disk
        restored = {}
        checkpoint_path = self.checkpoint_dir / workflow_id

        for step, rel_path in manifest.artifacts.items():
            artifact_path = checkpoint_path / rel_path
            if artifact_path.exists():
                try:
                    artifact_data = artifact_path.read_text(encoding="utf-8")
                    # Try to parse as JSON, fallback to string
                    try:
                        restored[step] = json.loads(artifact_data)
                    except json.JSONDecodeError:
                        restored[step] = artifact_data
                except OSError:
                    # Skip artifacts that can't be read
                    continue

        return restored

    def _preserve_artifacts(
        self,
        artifacts_path: Path,
        completed_steps: list[str],
        artifacts: dict[str, Any],
    ) -> dict[str, str]:
        """
        Save artifacts to checkpoint directory.

        Args:
            artifacts_path: Path to artifacts directory
            completed_steps: List of completed steps
            artifacts: Artifacts to preserve

        Returns:
            Dict mapping step_name → relative_file_path
        """
        preserved = {}

        for step in completed_steps:
            artifact_data = artifacts.get(step)
            if artifact_data:
                # Save artifact (format depends on artifact type)
                filename = f"{step}_output.md"
                file_path = artifacts_path / filename

                if isinstance(artifact_data, str):
                    file_path.write_text(artifact_data, encoding="utf-8")
                elif isinstance(artifact_data, dict):
                    file_path.write_text(
                        json.dumps(artifact_data, indent=2),
                        encoding="utf-8"
                    )
                else:
                    # Convert to string for other types
                    file_path.write_text(str(artifact_data), encoding="utf-8")

                preserved[step] = f"artifacts/{filename}"

        return preserved

    def _get_workflow_steps(self, workflow: WorkflowType) -> list[str]:
        """
        Get workflow step sequence.

        Args:
            workflow: Workflow type

        Returns:
            List of step names in execution order
        """
        workflow_steps: dict[WorkflowType, list[str]] = {
            "*full": ["enhance", "plan", "architect", "design", "implement", "review", "test", "security", "document"],
            "*build": ["enhance", "plan", "architect", "design", "implement", "review", "test"],
            "*fix": ["debug", "implement", "test"],
            "*refactor": ["review", "design", "implement", "test"],
        }
        return workflow_steps.get(workflow, [])

    @staticmethod
    def _is_valid_workflow_id(workflow_id: str) -> bool:
        """
        Validate workflow ID against regex pattern.

        Args:
            workflow_id: Workflow identifier to validate

        Returns:
            True if valid (matches ^[a-z0-9-]+$), False otherwise
        """
        return bool(re.match(r"^[a-z0-9-]+$", workflow_id))
