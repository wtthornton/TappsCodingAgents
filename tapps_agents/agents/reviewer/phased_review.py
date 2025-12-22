"""
Phased Review Strategy - Review services in phases with progress persistence

Phase 4.3: Phased Review Strategy

Reviews services in phases (critical → high → medium → low) with progress
persistence and resume capability.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ...core.config import ProjectConfig
from .batch_review import BatchReviewResult, BatchReviewWorkflow
from .service_discovery import Priority, Service, ServiceDiscovery


class PhaseResult(BaseModel):
    """Result of a single phase review."""

    phase_name: str
    priority: Priority
    services_count: int
    completed_at: str | None = None  # ISO format timestamp
    batch_result: BatchReviewResult | None = None
    status: str = "pending"  # pending, in_progress, completed, failed
    error: str | None = None


class PhasedReviewProgress(BaseModel):
    """Progress state for phased review with persistence."""

    review_id: str
    started_at: str  # ISO format timestamp
    completed_phases: list[str] = Field(default_factory=list)
    current_phase: str | None = None
    phases: dict[str, PhaseResult] = Field(default_factory=dict)
    total_services: int = 0
    services_reviewed: int = 0
    status: str = "pending"  # pending, in_progress, completed, failed, cancelled
    error: str | None = None
    completed_at: str | None = None  # ISO format timestamp

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "review_id": self.review_id,
            "started_at": self.started_at,
            "completed_phases": self.completed_phases,
            "current_phase": self.current_phase,
            "phases": {
                name: {
                    "phase_name": phase.phase_name,
                    "priority": phase.priority.value,  # Convert enum to string for JSON
                    "services_count": phase.services_count,
                    "completed_at": phase.completed_at,
                    "status": phase.status,
                    "error": phase.error,
                    "batch_result": (
                        phase.batch_result.model_dump()
                        if phase.batch_result
                        else None
                    ),
                }
                for name, phase in self.phases.items()
            },
            "total_services": self.total_services,
            "services_reviewed": self.services_reviewed,
            "status": self.status,
            "error": self.error,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PhasedReviewProgress:
        """Create from dictionary."""
        phases_dict = {}
        for name, phase_data in data.get("phases", {}).items():
            batch_result_data = phase_data.get("batch_result")
            batch_result = (
                BatchReviewResult.model_validate(batch_result_data)
                if batch_result_data
                else None
            )
            # Convert string priority to Priority enum
            priority_str = phase_data["priority"]
            priority = Priority(priority_str) if isinstance(priority_str, str) else priority_str
            
            phases_dict[name] = PhaseResult(
                phase_name=phase_data["phase_name"],
                priority=priority,
                services_count=phase_data["services_count"],
                completed_at=phase_data.get("completed_at"),
                status=phase_data.get("status", "pending"),
                error=phase_data.get("error"),
                batch_result=batch_result,
            )

        return cls(
            review_id=data["review_id"],
            started_at=data["started_at"],
            completed_phases=data.get("completed_phases", []),
            current_phase=data.get("current_phase"),
            phases=phases_dict,
            total_services=data.get("total_services", 0),
            services_reviewed=data.get("services_reviewed", 0),
            status=data.get("status", "pending"),
            error=data.get("error"),
            completed_at=data.get("completed_at"),
        )


class PhasedReviewResult(BaseModel):
    """Final result of phased review."""

    review_id: str
    total_phases: int
    completed_phases: int
    total_services: int
    services_reviewed: int
    passed: int
    failed: int
    average_score: float
    phases: dict[str, PhaseResult]
    status: str  # completed, failed, cancelled
    completed_at: str | None = None
    error: str | None = None


class PhasedReviewStrategy:
    """
    Phased review strategy for reviewing services in priority-based phases.

    Phase 4.3: Phased Review Strategy

    Reviews services in phases: critical → high → medium → low
    with progress persistence and resume capability.
    """

    def __init__(
        self,
        config: ProjectConfig | None = None,
        project_root: Path | None = None,
        progress_file: Path | None = None,
        max_parallel: int = 4,
    ):
        """
        Initialize phased review strategy.

        Args:
            config: Optional project configuration
            project_root: Optional project root directory
            progress_file: Optional path to progress file (default: .tapps-agents/review-progress.json)
            max_parallel: Maximum parallel reviews per phase
        """
        self.config = config
        self.project_root = project_root or Path.cwd()
        self.progress_file = (
            progress_file
            or self.project_root / ".tapps-agents" / "review-progress.json"
        )
        self.max_parallel = max_parallel
        self.batch_workflow = BatchReviewWorkflow(
            config=config, project_root=project_root, max_parallel=max_parallel
        )
        self.service_discovery = ServiceDiscovery(project_root=project_root)

    async def execute_phased_review(
        self,
        review_id: str | None = None,
        phases: list[Priority] | list[str] | None = None,
        resume: bool = True,
        parallel: bool = True,
        include_scoring: bool = True,
        include_llm_feedback: bool = True,
    ) -> PhasedReviewResult:
        """
        Execute phased review strategy.

        Args:
            review_id: Optional review ID (auto-generated if not provided)
            phases: Optional list of phases to execute (default: critical, high, medium, low)
            resume: Whether to resume from saved progress (default: True)
            parallel: Whether to execute reviews in parallel within each phase
            include_scoring: Whether to include code quality scoring
            include_llm_feedback: Whether to include LLM feedback

        Returns:
            PhasedReviewResult with aggregated results
        """
        if phases is None:
            phases = [Priority.CRITICAL, Priority.HIGH, Priority.MEDIUM, Priority.LOW]
        else:
            # Convert string phases to Priority enum if needed
            phases = [
                Priority(p) if isinstance(p, str) else p
                for p in phases
            ]

        # Generate review ID if not provided
        if not review_id:
            review_id = f"phased-review-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Try to load existing progress if resume is enabled
        progress: PhasedReviewProgress | None = None
        if resume:
            progress = self.load_progress(review_id)

        # If no existing progress, create new progress
        if not progress:
            progress = self._initialize_progress(review_id, phases)

        # Execute phases sequentially
        for phase_priority in phases:
            phase_name = phase_priority.value  # Use string value as key
            phase_result = progress.phases.get(phase_name)

            # Skip if already completed
            if phase_result and phase_result.status == "completed":
                continue

            # Skip if not in progress list (might be filtered out)
            if phase_name not in progress.phases:
                continue

            # Update current phase
            progress.current_phase = phase_name
            progress.status = "in_progress"
            if phase_result:
                phase_result.status = "in_progress"
            self.save_progress(progress)

            try:
                await self._execute_single_phase(
                    phase_priority,
                    phase_name,
                    phase_result,
                    progress,
                    parallel,
                    include_scoring,
                    include_llm_feedback,
                )
            except Exception as e:
                # Mark phase as failed
                if phase_result:
                    phase_result.status = "failed"
                    phase_result.error = str(e)
                progress.status = "failed"
                progress.error = f"Phase {phase_name} failed: {str(e)}"
                self.save_progress(progress)
                raise

        # All phases completed
        progress.status = "completed"
        progress.completed_at = datetime.now().isoformat()
        progress.current_phase = None
        self.save_progress(progress)

        # Aggregate final results
        return self._aggregate_phase_results(review_id, phases, progress)

    def _initialize_progress(
        self, review_id: str, phases: list[Priority]
    ) -> PhasedReviewProgress:
        """
        Initialize progress for a new phased review.

        Args:
            review_id: Review ID
            phases: List of phases to execute

        Returns:
            Initialized PhasedReviewProgress
        """
        # Discover and prioritize services
        services = self.service_discovery.discover_services_with_priority(
            prioritize=True, group_by_language=False
        )

        # Group services by priority (phase)
        services_by_phase: dict[Priority, list[Service]] = {}
        for service in services:
            phase = service.priority
            if phase not in services_by_phase:
                services_by_phase[phase] = []
            services_by_phase[phase].append(service)

        # Initialize progress
        progress = PhasedReviewProgress(
            review_id=review_id,
            started_at=datetime.now().isoformat(),
            total_services=len(services),
            status="in_progress",
        )

        # Create phase results
        for phase_priority in phases:
            phase_name = phase_priority.value  # Use string value as key for phases dict
            services_in_phase = services_by_phase.get(phase_priority, [])
            progress.phases[phase_name] = PhaseResult(
                phase_name=phase_name,
                priority=phase_priority,
                services_count=len(services_in_phase),
                status="pending",
            )

        # Save initial progress
        self.save_progress(progress)
        return progress

    async def _execute_single_phase(
        self,
        phase_priority: Priority,
        phase_name: str,
        phase_result: PhaseResult | None,
        progress: PhasedReviewProgress,
        parallel: bool,
        include_scoring: bool,
        include_llm_feedback: bool,
    ) -> None:
        """
        Execute a single phase of the review.

        Args:
            phase_priority: Priority enum for this phase
            phase_name: String name for this phase
            phase_result: PhaseResult object (may be None)
            progress: Overall progress object
            parallel: Whether to execute reviews in parallel
            include_scoring: Whether to include scoring
            include_llm_feedback: Whether to include LLM feedback
        """
        # Get services for this phase
        services_in_phase = [
            s
            for s in self.service_discovery.discover_services_with_priority(
                prioritize=True, group_by_language=False
            )
            if s.priority == phase_priority
        ]

        if not services_in_phase:
            # No services in this phase, mark as completed
            if phase_result:
                phase_result.status = "completed"
                phase_result.completed_at = datetime.now().isoformat()
            return

        # Execute batch review for this phase
        batch_result = await self.batch_workflow.review_services(
            services=services_in_phase,
            parallel=parallel,
            include_scoring=include_scoring,
            include_llm_feedback=include_llm_feedback,
        )

        # Update phase result
        if phase_result:
            phase_result.batch_result = batch_result
            phase_result.status = "completed"
            phase_result.completed_at = datetime.now().isoformat()

        # Update progress
        progress.completed_phases.append(phase_name)
        progress.services_reviewed += batch_result.services_reviewed
        self.save_progress(progress)

    def _aggregate_phase_results(
        self,
        review_id: str,
        phases: list[Priority],
        progress: PhasedReviewProgress,
    ) -> PhasedReviewResult:
        """
        Aggregate results from all phases into final result.

        Args:
            review_id: Review ID
            phases: List of phases that were executed
            progress: Progress object with all phase results

        Returns:
            PhasedReviewResult with aggregated statistics
        """
        total_passed = sum(
            (
                phase.batch_result.passed
                if phase.batch_result
                else 0
            )
            for phase in progress.phases.values()
        )
        total_failed = sum(
            (
                phase.batch_result.failed
                if phase.batch_result
                else 0
            )
            for phase in progress.phases.values()
        )

        # Calculate average score
        scores = [
            (
                phase.batch_result.average_score
                if phase.batch_result and phase.batch_result.average_score > 0
                else None
            )
            for phase in progress.phases.values()
        ]
        valid_scores = [s for s in scores if s is not None]
        average_score = (
            sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
        )

        return PhasedReviewResult(
            review_id=review_id,
            total_phases=len(phases),
            completed_phases=len(progress.completed_phases),
            total_services=progress.total_services,
            services_reviewed=progress.services_reviewed,
            passed=total_passed,
            failed=total_failed,
            average_score=average_score,
            phases={
                name: phase for name, phase in progress.phases.items()
            },
            status="completed",
            completed_at=progress.completed_at,
        )

    def save_progress(self, progress: PhasedReviewProgress) -> None:
        """
        Save progress to disk.

        Phase 4.3: Progress Persistence
        """
        try:
            # Ensure directory exists
            self.progress_file.parent.mkdir(parents=True, exist_ok=True)

            # Use atomic write for safety (similar to workflow file_utils pattern)
            # Write to temp file first, then rename
            temp_file = self.progress_file.with_suffix(".json.tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(progress.to_dict(), f, indent=2)

            # Atomic rename (Windows-compatible)
            if self.progress_file.exists():
                self.progress_file.unlink()
            temp_file.replace(self.progress_file)

        except Exception as e:
            # Best-effort save, log but don't fail
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to save phased review progress: {e}")

    def load_progress(self, review_id: str | None = None) -> PhasedReviewProgress | None:
        """
        Load progress from disk.

        Phase 4.3: Resume Capability

        Args:
            review_id: Optional review ID to load (loads latest if not provided)

        Returns:
            PhasedReviewProgress if found, None otherwise
        """
        if not self.progress_file.exists():
            return None

        try:
            with open(self.progress_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            progress = PhasedReviewProgress.from_dict(data)

            # Filter by review_id if provided
            if review_id and progress.review_id != review_id:
                return None

            return progress

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to load phased review progress: {e}")
            return None

    def clear_progress(self, review_id: str | None = None) -> None:
        """
        Clear saved progress.

        Args:
            review_id: Optional review ID to clear (clears all if not provided)
        """
        if review_id:
            progress = self.load_progress()
            if progress and progress.review_id == review_id:
                if self.progress_file.exists():
                    self.progress_file.unlink()
        else:
            # Clear all progress
            if self.progress_file.exists():
                self.progress_file.unlink()

