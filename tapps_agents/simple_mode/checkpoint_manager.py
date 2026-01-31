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

    def analyze_early_checkpoint(
        self,
        workflow: WorkflowType,
        enhanced_prompt: str,
    ) -> CheckpointAnalysis:
        """
        Analyze checkpoint early (after Enhance step) using lightweight heuristics.

        This is Checkpoint 1 - performed before Planning to catch obvious mismatches
        early. Uses keyword/pattern matching on enhanced prompt text.

        Args:
            workflow: Current workflow being executed
            enhanced_prompt: Enhanced prompt text from enhance step

        Returns:
            CheckpointAnalysis with mismatch detection (lower confidence than planning checkpoint)

        Raises:
            ValueError: If workflow is unknown

        Performance:
            Target: < 200ms (text analysis only, no I/O)

        Examples:
            >>> manager = CheckpointManager()
            >>> prompt = "Fix typo in README.md - wrong word"
            >>> analysis = manager.analyze_early_checkpoint("*full", prompt)
            >>> analysis.mismatch_detected
            True
            >>> analysis.recommended_workflow
            "*fix"
        """
        # Parameter validation
        if workflow not in ("*full", "*build", "*fix", "*refactor"):
            raise ValueError(f"Unknown workflow: {workflow}")

        # Extract characteristics from enhanced prompt using heuristics
        characteristics = self._analyze_prompt_text(enhanced_prompt)

        # Detect workflow mismatch
        mismatch_detected, recommended = self._detect_early_mismatch(
            workflow, characteristics
        )

        # Calculate token/time savings (only have "enhance" completed)
        completed_steps = ["enhance"]
        token_savings, time_savings, steps_saved = self._calculate_savings(
            workflow, recommended, completed_steps
        )

        # Generate reason
        reason = self._generate_early_reason(workflow, recommended, characteristics)

        # Get remaining steps
        all_steps = self._get_workflow_steps(workflow)
        remaining = tuple(s for s in all_steps if s not in completed_steps)

        return CheckpointAnalysis(
            mismatch_detected=mismatch_detected,
            current_workflow=workflow,
            recommended_workflow=recommended,
            confidence=0.70,  # Lower confidence - only prompt analysis
            detected_scope=characteristics["scope"],
            detected_complexity=characteristics["complexity"],
            story_points=characteristics["estimated_points"],
            files_affected=characteristics["estimated_files"],
            completed_steps=tuple(completed_steps),
            remaining_steps=remaining,
            token_savings=token_savings,
            time_savings=time_savings,
            steps_saved=steps_saved,
            reason=reason,
        )

    def _analyze_prompt_text(self, prompt: str) -> dict[str, Any]:
        """
        Extract task characteristics from prompt text using heuristics.

        Uses keyword matching and pattern recognition to estimate:
        - Intent (bug_fix, feature, refactor)
        - Complexity (low/medium/high)
        - Scope (low/medium/high)

        Args:
            prompt: Enhanced prompt text

        Returns:
            Dict with scope, complexity, estimated_points, estimated_files, intent
        """
        prompt_lower = prompt.lower()

        # Detect intent using keywords
        bug_fix_keywords = ["fix", "bug", "error", "typo", "wrong", "broken", "issue", "crash", "failure"]
        simple_keywords = ["add logging", "update comment", "change text", "rename", "delete", "remove"]
        complex_keywords = ["implement", "architecture", "design", "refactor", "migrate", "integrate"]

        is_bug_fix = any(kw in prompt_lower for kw in bug_fix_keywords)
        is_simple = any(kw in prompt_lower for kw in simple_keywords)
        is_complex = any(kw in prompt_lower for kw in complex_keywords)

        # Estimate complexity
        word_count = len(prompt.split())
        if is_simple or word_count < 30:
            complexity: ComplexityLevel = "low"
            estimated_points = 3
        elif is_complex or word_count > 100:
            complexity = "high"
            estimated_points = 21
        else:
            complexity = "medium"
            estimated_points = 8

        # Estimate scope (files affected)
        # Look for mentions of multiple files, components, modules
        multi_file_indicators = ["files", "components", "modules", "across", "system-wide", "multiple"]
        has_multi_file = any(ind in prompt_lower for ind in multi_file_indicators)

        if has_multi_file:
            scope: ScopeLevel = "high"
            estimated_files = 8
        elif word_count > 80:
            scope = "medium"
            estimated_files = 5
        else:
            scope = "low"
            estimated_files = 2

        return {
            "scope": scope,
            "complexity": complexity,
            "estimated_points": estimated_points,
            "estimated_files": estimated_files,
            "is_bug_fix": is_bug_fix,
            "is_simple": is_simple,
        }

    def _detect_early_mismatch(
        self,
        workflow: WorkflowType,
        characteristics: dict[str, Any],
    ) -> tuple[bool, WorkflowType | None]:
        """
        Detect workflow mismatch from prompt characteristics.

        Similar to _detect_workflow_mismatch but uses estimated values
        from prompt analysis instead of planning artifacts.

        Args:
            workflow: Current workflow type
            characteristics: Estimated characteristics from prompt

        Returns:
            Tuple of (mismatch_detected, recommended_workflow)
        """
        # Check if task is too simple for *full workflow
        if workflow == "*full":
            if characteristics["is_bug_fix"] and characteristics["complexity"] == "low":
                # Bug fix with low complexity → recommend *fix
                return (True, "*fix")
            elif characteristics["complexity"] == "low":
                # Low complexity non-bug → recommend *build
                return (True, "*build")
            elif characteristics["complexity"] == "medium" and characteristics["scope"] == "low":
                # Medium complexity but low scope → recommend *build
                return (True, "*build")

        # No mismatch detected (or insufficient confidence)
        return (False, None)

    def _generate_early_reason(
        self,
        current_workflow: WorkflowType,
        recommended_workflow: WorkflowType | None,
        characteristics: dict[str, Any],
    ) -> str:
        """
        Generate reason for early checkpoint recommendation.

        Args:
            current_workflow: Current workflow type
            recommended_workflow: Recommended workflow (None if no mismatch)
            characteristics: Estimated characteristics

        Returns:
            User-friendly explanation string
        """
        if not recommended_workflow:
            return "Workflow appears appropriate based on prompt analysis."

        intent_desc = "bug fix" if characteristics["is_bug_fix"] else "task"
        return (
            f"Prompt suggests simple {intent_desc} ({characteristics['complexity']} complexity). "
            f"Consider {recommended_workflow} workflow instead of {current_workflow} for token savings."
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

    def analyze_quality_gate(
        self,
        workflow: WorkflowType,
        completed_steps: list[str],
        quality_score: float,
        token_usage: int = 0,
    ) -> CheckpointAnalysis:
        """
        Analyze quality gate checkpoint to suggest early termination.

        This is Checkpoint 3 - performed after Review/Test steps to determine
        if remaining optional steps (security, docs) can be skipped.

        Args:
            workflow: Current workflow being executed
            completed_steps: List of completed steps
            quality_score: Quality score from reviewer (0-100)
            token_usage: Total tokens used so far (optional)

        Returns:
            CheckpointAnalysis suggesting early termination if quality is sufficient

        Performance:
            Target: < 100ms (simple calculation)

        Examples:
            >>> manager = CheckpointManager()
            >>> analysis = manager.analyze_quality_gate(
            ...     "*full",
            ...     ["enhance", "plan", "architect", "design", "implement", "review", "test"],
            ...     quality_score=85.0
            ... )
            >>> analysis.mismatch_detected  # Suggests skipping security/docs
            True
        """
        # Parameter validation
        if workflow not in ("*full", "*build", "*fix", "*refactor"):
            raise ValueError(f"Unknown workflow: {workflow}")

        # Quality gate thresholds
        excellent_threshold = 80.0  # Can skip all optional steps
        good_threshold = 75.0       # Can skip docs, keep security

        # Get workflow steps
        all_steps = self._get_workflow_steps(workflow)
        remaining_steps = [s for s in all_steps if s not in completed_steps]

        # Determine optional steps that can be skipped
        optional_steps = []
        if quality_score >= excellent_threshold:
            # Excellent quality - can skip both security and document
            optional_steps = ["security", "document"]
        elif quality_score >= good_threshold:
            # Good quality - can skip document but keep security
            optional_steps = ["document"]

        # Check if we can skip any remaining steps
        skippable = [s for s in remaining_steps if s in optional_steps]

        if not skippable:
            # No steps can be skipped
            return CheckpointAnalysis(
                mismatch_detected=False,
                current_workflow=workflow,
                recommended_workflow=None,
                confidence=0.90,  # High confidence from quality scores
                detected_scope="medium",  # Not applicable for quality gate
                detected_complexity="medium",  # Not applicable
                story_points=8,  # Not applicable
                files_affected=3,  # Not applicable
                completed_steps=tuple(completed_steps),
                remaining_steps=tuple(remaining_steps),
                token_savings=0,
                time_savings=0,
                steps_saved=0,
                reason=f"Quality score {quality_score:.1f} meets threshold but all remaining steps are required.",
            )

        # Calculate savings from skipping optional steps
        token_savings = sum(self.token_estimates.get(step, 5000) for step in skippable)
        time_savings = sum(self.time_estimates.get(step, 5) for step in skippable)
        steps_saved = len(skippable)

        # Generate reason
        if quality_score >= excellent_threshold:
            reason = (
                f"Excellent quality score ({quality_score:.1f}) exceeds threshold ({excellent_threshold}). "
                f"Can safely skip optional steps: {', '.join(skippable)}."
            )
        else:
            reason = (
                f"Good quality score ({quality_score:.1f}) exceeds threshold ({good_threshold}). "
                f"Can skip documentation step."
            )

        return CheckpointAnalysis(
            mismatch_detected=True,  # Suggests early termination
            current_workflow=workflow,
            recommended_workflow=None,  # Not switching workflows, just terminating early
            confidence=0.90,
            detected_scope="medium",
            detected_complexity="medium",
            story_points=8,
            files_affected=3,
            completed_steps=tuple(completed_steps),
            remaining_steps=tuple([s for s in remaining_steps if s not in skippable]),
            token_savings=token_savings,
            time_savings=time_savings,
            steps_saved=steps_saved,
            reason=reason,
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
