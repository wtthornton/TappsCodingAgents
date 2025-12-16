"""
Result Aggregator - Deterministic aggregation of agent results with conflict detection.

Epic 2 / Story 2.5: Parallel Execution & Result Aggregation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .artifact_helper import load_artifact
from .code_artifact import CodeArtifact
from .design_artifact import DesignArtifact
from .enhancement_artifact import EnhancementArtifact
from .planning_artifact import PlanningArtifact
from .review_artifact import ReviewArtifact


@dataclass
class Conflict:
    """Represents a conflict between agent outputs."""

    conflict_type: str  # "file_modification", "overlapping_output", "schema_mismatch"
    agent_ids: list[str]
    description: str
    affected_files: list[str] = field(default_factory=list)
    severity: str = "medium"  # "low", "medium", "high", "critical"


class ResultAggregator:
    """
    Aggregates results from multiple agents with deterministic ordering and conflict detection.

    Epic 2 / Story 2.5: Parallel Execution & Result Aggregation
    """

    def __init__(self, worktree_path: Path | None = None):
        """
        Initialize Result Aggregator.

        Args:
            worktree_path: Optional worktree path for artifact discovery
        """
        self.worktree_path = worktree_path
        self.conflicts: list[Conflict] = []

    def aggregate_artifacts(
        self,
        agent_results: list[dict[str, Any]],
        stable_ordering: bool = True,
    ) -> dict[str, Any]:
        """
        Aggregate artifacts from multiple agent executions.

        Args:
            agent_results: List of agent result dictionaries, each containing:
                - agent_id: str
                - agent_type: str
                - artifact_path: Path | None
                - result: dict (raw agent result)
            stable_ordering: Whether to apply stable ordering to lists

        Returns:
            Aggregated results dictionary with conflicts detected
        """
        # Sort by agent_id for stable ordering
        if stable_ordering:
            agent_results = sorted(agent_results, key=lambda x: x.get("agent_id", ""))

        aggregated: dict[str, Any] = {
            "schema_version": "1.0",
            "total_agents": len(agent_results),
            "successful_agents": 0,
            "failed_agents": 0,
            "artifacts": {},
            "aggregated_results": {},
            "conflicts": [],
        }

        # Track file modifications across agents
        file_modifications: dict[str, list[str]] = {}  # file -> [agent_ids]

        # Process each agent result
        for agent_result in agent_results:
            agent_id = agent_result.get("agent_id", "unknown")
            agent_type = agent_result.get("agent_type", "unknown")
            artifact_path = agent_result.get("artifact_path")
            success = agent_result.get("success", False)

            if success:
                aggregated["successful_agents"] += 1
            else:
                aggregated["failed_agents"] += 1

            # Load artifact if available
            artifact = None
            if artifact_path and Path(artifact_path).exists():
                try:
                    artifact = load_artifact(Path(artifact_path))
                    aggregated["artifacts"][agent_id] = artifact.to_dict()

                    # Track file modifications for conflict detection
                    self._track_file_modifications(artifact, agent_id, file_modifications)
                except Exception as e:
                    # Artifact load failed, but continue aggregation
                    aggregated["artifacts"][agent_id] = {"error": str(e)}

            # Store raw result
            aggregated["aggregated_results"][agent_id] = {
                "agent_type": agent_type,
                "success": success,
                "result": agent_result.get("result", {}),
            }

        # Detect conflicts
        conflicts = self._detect_conflicts(file_modifications, agent_results)
        aggregated["conflicts"] = [self._conflict_to_dict(c) for c in conflicts]
        self.conflicts = conflicts

        # Apply merge rules
        aggregated["merged_outputs"] = self._merge_outputs(
            agent_results, conflicts, stable_ordering
        )

        return aggregated

    def _track_file_modifications(
        self,
        artifact: (
            CodeArtifact
            | DesignArtifact
            | ReviewArtifact
            | PlanningArtifact
            | EnhancementArtifact
        ),
        agent_id: str,
        file_modifications: dict[str, list[str]],
    ) -> None:
        """Track which files are modified by which agents."""
        if isinstance(artifact, CodeArtifact):
            for change in artifact.changes + artifact.refactorings:
                file_path = change.file_path
                if file_path not in file_modifications:
                    file_modifications[file_path] = []
                if agent_id not in file_modifications[file_path]:
                    file_modifications[file_path].append(agent_id)

    def _detect_conflicts(
        self,
        file_modifications: dict[str, list[str]],
        agent_results: list[dict[str, Any]],
    ) -> list[Conflict]:
        """
        Detect conflicts between agent outputs.

        Args:
            file_modifications: Dictionary mapping file paths to list of agent IDs
            agent_results: List of agent result dictionaries

        Returns:
            List of detected conflicts
        """
        conflicts: list[Conflict] = []

        # Detect file modification conflicts
        for file_path, agent_ids in file_modifications.items():
            if len(agent_ids) > 1:
                conflicts.append(
                    Conflict(
                        conflict_type="file_modification",
                        agent_ids=agent_ids,
                        description=f"Multiple agents modified {file_path}",
                        affected_files=[file_path],
                        severity="high",
                    )
                )

        # Detect overlapping outputs (same agent type running multiple times)
        agent_type_counts: dict[str, list[str]] = {}
        for result in agent_results:
            agent_type = result.get("agent_type", "unknown")
            agent_id = result.get("agent_id", "unknown")
            if agent_type not in agent_type_counts:
                agent_type_counts[agent_type] = []
            agent_type_counts[agent_type].append(agent_id)

        for agent_type, agent_ids in agent_type_counts.items():
            if len(agent_ids) > 1:
                conflicts.append(
                    Conflict(
                        conflict_type="overlapping_output",
                        agent_ids=agent_ids,
                        description=f"Multiple {agent_type} agents executed",
                        severity="medium",
                    )
                )

        return conflicts

    def _merge_outputs(
        self,
        agent_results: list[dict[str, Any]],
        conflicts: list[Conflict],
        stable_ordering: bool,
    ) -> dict[str, Any]:
        """
        Merge outputs from multiple agents using explicit merge rules.

        Args:
            agent_results: List of agent result dictionaries
            conflicts: List of detected conflicts
            stable_ordering: Whether to apply stable ordering

        Returns:
            Merged outputs dictionary
        """
        merged: dict[str, Any] = {
            "code_changes": [],
            "design_outputs": [],
            "review_results": [],
            "planning_outputs": [],
            "enhancement_outputs": [],
        }

        # Merge by agent type with stable ordering
        for result in agent_results:
            result.get("agent_type", "unknown")
            artifact_path = result.get("artifact_path")

            if not artifact_path or not Path(artifact_path).exists():
                continue

            try:
                artifact = load_artifact(Path(artifact_path))

                if isinstance(artifact, CodeArtifact):
                    # Merge code changes (append, no deduplication)
                    merged["code_changes"].extend(artifact.changes)
                    merged["code_changes"].extend(artifact.refactorings)

                elif isinstance(artifact, DesignArtifact):
                    # Merge design outputs (append components)
                    merged["design_outputs"].append(artifact.to_dict())

                elif isinstance(artifact, ReviewArtifact):
                    # Merge review results (take highest score, combine comments)
                    if (
                        not merged["review_results"]
                        or artifact.overall_score
                        > merged["review_results"][0].get("overall_score", 0)
                    ):
                        merged["review_results"] = [artifact.to_dict()]

                elif isinstance(artifact, PlanningArtifact):
                    # Merge planning outputs (combine stories)
                    merged["planning_outputs"].extend(artifact.user_stories)

                elif isinstance(artifact, EnhancementArtifact):
                    # Merge enhancement outputs (append)
                    merged["enhancement_outputs"].append(artifact.to_dict())

            except Exception:
                # Skip artifacts that can't be loaded
                continue

        # Apply stable ordering if requested
        if stable_ordering:
            for key in merged:
                if isinstance(merged[key], list):
                    # Sort lists by a stable key (timestamp or ID)
                    merged[key] = sorted(
                        merged[key],
                        key=lambda x: x.get("timestamp", x.get("story_id", "")),
                    )

        return merged

    def _conflict_to_dict(self, conflict: Conflict) -> dict[str, Any]:
        """Convert Conflict to dictionary."""
        return {
            "conflict_type": conflict.conflict_type,
            "agent_ids": conflict.agent_ids,
            "description": conflict.description,
            "affected_files": conflict.affected_files,
            "severity": conflict.severity,
        }

    def get_conflicts(self) -> list[dict[str, Any]]:
        """Get detected conflicts as dictionaries."""
        return [self._conflict_to_dict(c) for c in self.conflicts]

    def has_conflicts(self) -> bool:
        """Check if any conflicts were detected."""
        return len(self.conflicts) > 0

    def has_critical_conflicts(self) -> bool:
        """Check if any critical conflicts were detected."""
        return any(c.severity == "critical" for c in self.conflicts)
