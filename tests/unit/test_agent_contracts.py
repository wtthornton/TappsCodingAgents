"""
Contract Tests for Agent I/O Contracts.

Epic 2 / Story 2.6: Agent Contract Tests & Backward Compatibility Harness

These tests ensure that agent inputs/outputs remain compatible with existing workflows
and that every agent run produces required artifacts in agreed schemas.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tapps_agents.workflow.artifact_helper import load_artifact, write_artifact
from tapps_agents.workflow.code_artifact import CodeArtifact, CodeChange
from tapps_agents.workflow.design_artifact import Component, DesignArtifact
from tapps_agents.workflow.enhancement_artifact import (
    EnhancementArtifact,
)
from tapps_agents.workflow.planning_artifact import PlanningArtifact, UserStory
from tapps_agents.workflow.review_artifact import ReviewArtifact

pytestmark = pytest.mark.unit


class TestArtifactSchemas:
    """Test that artifact schemas are valid and versioned."""

    def test_code_artifact_schema(self):
        """Test CodeArtifact has required schema fields."""
        artifact = CodeArtifact(
            worktree_path="/test",
            correlation_id="test-123",
            operation_type="implement",
        )

        assert artifact.schema_version == "1.0"
        assert artifact.timestamp is not None
        assert artifact.status == "pending"
        assert artifact.worktree_path == "/test"
        assert artifact.correlation_id == "test-123"

        # Test serialization
        artifact_dict = artifact.to_dict()
        assert "schema_version" in artifact_dict
        assert "timestamp" in artifact_dict
        assert "status" in artifact_dict

        # Test deserialization
        loaded = CodeArtifact.from_dict(artifact_dict)
        assert loaded.schema_version == artifact.schema_version
        assert loaded.worktree_path == artifact.worktree_path

    def test_design_artifact_schema(self):
        """Test DesignArtifact has required schema fields."""
        artifact = DesignArtifact(
            worktree_path="/test",
            correlation_id="test-123",
            operation_type="design-system",
        )

        assert artifact.schema_version == "1.0"
        assert artifact.timestamp is not None
        assert artifact.status == "pending"

        # Test serialization
        artifact_dict = artifact.to_dict()
        assert "schema_version" in artifact_dict
        assert "components" in artifact_dict

    def test_review_artifact_schema(self):
        """Test ReviewArtifact has required schema fields."""
        artifact = ReviewArtifact(
            worktree_path="/test",
            correlation_id="test-123",
        )

        assert artifact.schema_version == "1.0"
        assert artifact.timestamp is not None

        # Test gate fields (for workflow gating)
        artifact.overall_score = 85.0
        artifact.threshold = 70.0
        artifact.mark_completed()

        assert artifact.passed is True
        assert artifact.decision == "APPROVED"

    def test_planning_artifact_schema(self):
        """Test PlanningArtifact has required schema fields."""
        artifact = PlanningArtifact(
            worktree_path="/test",
            correlation_id="test-123",
            operation_type="plan",
        )

        assert artifact.schema_version == "1.0"
        assert artifact.timestamp is not None

        # Test story addition
        story = UserStory(
            story_id="story-1",
            title="Test Story",
            description="A test story",
        )
        artifact.add_story(story)

        assert artifact.total_stories == 1
        assert len(artifact.user_stories) == 1

    def test_enhancement_artifact_schema(self):
        """Test EnhancementArtifact has required schema fields."""
        artifact = EnhancementArtifact(
            worktree_path="/test",
            correlation_id="test-123",
            original_prompt="Test prompt",
            enhanced_prompt="Enhanced test prompt",
        )

        assert artifact.schema_version == "1.0"
        assert artifact.timestamp is not None
        assert artifact.original_prompt == "Test prompt"
        assert artifact.enhanced_prompt == "Enhanced test prompt"


class TestArtifactPersistence:
    """Test that artifacts can be written and loaded correctly."""

    def test_write_and_load_code_artifact(self, tmp_path: Path):
        """Test writing and loading CodeArtifact."""
        artifact = CodeArtifact(
            worktree_path=str(tmp_path),
            correlation_id="test-123",
        )

        change = CodeChange(
            file_path="test.py",
            change_type="feature",
            lines_added=10,
            lines_removed=2,
        )
        artifact.add_change(change)
        artifact.mark_completed()

        # Write artifact
        artifact_path = write_artifact(artifact, worktree_path=tmp_path)
        assert artifact_path.exists()

        # Load artifact
        loaded = load_artifact(artifact_path)
        assert isinstance(loaded, CodeArtifact)
        assert loaded.schema_version == "1.0"
        assert len(loaded.changes) == 1
        assert loaded.status == "completed"

    def test_write_and_load_design_artifact(self, tmp_path: Path):
        """Test writing and loading DesignArtifact."""
        artifact = DesignArtifact(
            worktree_path=str(tmp_path),
            correlation_id="test-123",
        )

        component = Component(
            name="API Service",
            component_type="service",
            technology="FastAPI",
        )
        artifact.add_component(component)
        artifact.mark_completed()

        # Write artifact
        artifact_path = write_artifact(artifact, worktree_path=tmp_path)
        assert artifact_path.exists()

        # Load artifact
        loaded = load_artifact(artifact_path)
        assert isinstance(loaded, DesignArtifact)
        assert len(loaded.components) == 1
        assert loaded.components[0].name == "API Service"


class TestArtifactAggregation:
    """Test that artifacts can be aggregated deterministically."""

    def test_stable_ordering(self):
        """Test that artifact lists maintain stable ordering."""
        from tapps_agents.workflow.result_aggregator import ResultAggregator

        aggregator = ResultAggregator()

        # Create multiple agent results
        agent_results = [
            {
                "agent_id": "agent-2",
                "agent_type": "code",
                "success": True,
                "result": {},
            },
            {
                "agent_id": "agent-1",
                "agent_type": "code",
                "success": True,
                "result": {},
            },
            {
                "agent_id": "agent-3",
                "agent_type": "review",
                "success": True,
                "result": {},
            },
        ]

        aggregated = aggregator.aggregate_artifacts(agent_results, stable_ordering=True)

        # Results should be sorted by agent_id
        agent_ids = list(aggregated["aggregated_results"].keys())
        assert agent_ids == ["agent-1", "agent-2", "agent-3"]

    def test_conflict_detection(self, tmp_path: Path):
        """Test that file modification conflicts are detected."""
        from tapps_agents.workflow.result_aggregator import ResultAggregator

        aggregator = ResultAggregator(worktree_path=tmp_path)

        # Create artifacts that modify the same file
        artifact1 = CodeArtifact(
            worktree_path=str(tmp_path),
            correlation_id="test-1",
        )
        change1 = CodeChange(file_path="common.py", change_type="feature", lines_added=5)
        artifact1.add_change(change1)
        artifact1_path = write_artifact(artifact1, worktree_path=tmp_path)

        artifact2 = CodeArtifact(
            worktree_path=str(tmp_path),
            correlation_id="test-2",
        )
        change2 = CodeChange(file_path="common.py", change_type="refactor", lines_added=3)
        artifact2.add_change(change2)
        artifact2_path = write_artifact(artifact2, worktree_path=tmp_path)

        agent_results = [
            {
                "agent_id": "agent-1",
                "agent_type": "code",
                "success": True,
                "artifact_path": str(artifact1_path),
                "result": {},
            },
            {
                "agent_id": "agent-2",
                "agent_type": "code",
                "success": True,
                "artifact_path": str(artifact2_path),
                "result": {},
            },
        ]

        aggregated = aggregator.aggregate_artifacts(agent_results)

        # Should detect conflict
        assert aggregator.has_conflicts()
        conflicts = aggregator.get_conflicts()
        assert len(conflicts) > 0
        assert any(c["conflict_type"] == "file_modification" for c in conflicts)


class TestBackwardCompatibility:
    """Test that agent contracts remain backward compatible."""

    def test_review_artifact_gate_fields(self):
        """Test that ReviewArtifact maintains gate fields for workflow compatibility."""
        artifact = ReviewArtifact()

        # These fields are used by workflow gates
        artifact.overall_score = 75.0
        artifact.threshold = 70.0
        artifact.mark_completed()

        # Gate fields must be present
        assert "passed" in artifact.to_dict()
        assert "threshold" in artifact.to_dict()
        assert "overall_score" in artifact.to_dict()
        assert "decision" in artifact.to_dict()

        # Gate logic must work
        assert artifact.passed is True
        assert artifact.decision in ["APPROVED", "APPROVED_WITH_SUGGESTIONS", "CHANGES_REQUESTED"]

    def test_artifact_json_compatibility(self):
        """Test that artifacts can be serialized to JSON for compatibility."""
        artifacts = [
            CodeArtifact(correlation_id="test"),
            DesignArtifact(correlation_id="test"),
            ReviewArtifact(correlation_id="test"),
            PlanningArtifact(correlation_id="test"),
            EnhancementArtifact(correlation_id="test", original_prompt="test"),
        ]

        for artifact in artifacts:
            # Should serialize to JSON without errors
            json_str = json.dumps(artifact.to_dict())
            assert json_str is not None

            # Should deserialize from JSON
            loaded_dict = json.loads(json_str)
            assert loaded_dict["schema_version"] == "1.0"
