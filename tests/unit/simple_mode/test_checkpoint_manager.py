"""
Unit tests for checkpoint_manager module.

Tests CheckpointManager, WorkflowSwitcher, and related functionality
for mid-execution workflow checkpoints with artifact preservation.

Coverage target: 80%+
"""

import json
import time
from pathlib import Path
from typing import Any

import pytest

from tapps_agents.simple_mode.checkpoint_manager import (
    ArtifactManifest,
    CheckpointAnalysis,
    CheckpointManager,
    PlanningResults,
    SwitchResult,
    WorkflowSwitcher,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def temp_checkpoint_dir(tmp_path: Path) -> Path:
    """Create temporary checkpoint directory."""
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    return checkpoint_dir


@pytest.fixture
def checkpoint_manager() -> CheckpointManager:
    """Create CheckpointManager instance."""
    return CheckpointManager()


@pytest.fixture
def workflow_switcher(temp_checkpoint_dir: Path) -> WorkflowSwitcher:
    """Create WorkflowSwitcher instance."""
    return WorkflowSwitcher(temp_checkpoint_dir)


@pytest.fixture
def sample_planning_results() -> PlanningResults:
    """Sample planning results for testing."""
    return {
        "story_points": 8,
        "files_affected": 3,
        "user_stories": [
            {"id": "STORY-1", "title": "Test story 1"},
            {"id": "STORY-2", "title": "Test story 2"},
        ],
        "architectural_impact": "medium",
        "complexity_estimate": "medium",
    }


@pytest.fixture
def sample_artifacts() -> dict[str, Any]:
    """Sample artifacts for testing."""
    return {
        "enhance": "Enhanced prompt content with detailed requirements",
        "plan": {
            "story_points": 8,
            "stories": [
                {"id": "STORY-1", "title": "Test story 1", "points": 5},
                {"id": "STORY-2", "title": "Test story 2", "points": 3},
            ],
        },
        "architect": "System architecture design document",
    }


# ============================================================================
# CheckpointAnalysis Tests
# ============================================================================

class TestCheckpointAnalysis:
    """Tests for CheckpointAnalysis dataclass."""

    def test_checkpoint_analysis_immutable(self):
        """Test that CheckpointAnalysis is immutable (frozen)."""
        analysis = CheckpointAnalysis(
            mismatch_detected=True,
            current_workflow="*full",
            recommended_workflow="*build",
            confidence=0.85,
            detected_scope="low",
            detected_complexity="medium",
            story_points=8,
            files_affected=3,
            completed_steps=("enhance", "plan"),
            remaining_steps=("design", "implement", "review", "test"),
            token_savings=25000,
            time_savings=35,
            steps_saved=5,
            reason="Task too simple for *full workflow",
        )

        # Test immutability
        with pytest.raises(Exception):  # FrozenInstanceError
            analysis.mismatch_detected = False  # type: ignore

    def test_checkpoint_analysis_validation_confidence(self):
        """Test confidence validation."""
        with pytest.raises(ValueError, match="confidence must be 0.0-1.0"):
            CheckpointAnalysis(
                mismatch_detected=True,
                current_workflow="*full",
                recommended_workflow="*build",
                confidence=1.5,  # Invalid: > 1.0
                detected_scope="low",
                detected_complexity="medium",
                story_points=8,
                files_affected=3,
                completed_steps=("enhance",),
                remaining_steps=("plan",),
                token_savings=1000,
                time_savings=10,
                steps_saved=1,
                reason="Test",
            )

    def test_checkpoint_analysis_validation_story_points(self):
        """Test story_points validation."""
        with pytest.raises(ValueError, match="story_points must be positive"):
            CheckpointAnalysis(
                mismatch_detected=False,
                current_workflow="*full",
                recommended_workflow=None,
                confidence=0.85,
                detected_scope="low",
                detected_complexity="low",
                story_points=-5,  # Invalid: negative
                files_affected=3,
                completed_steps=("enhance",),
                remaining_steps=("plan",),
                token_savings=0,
                time_savings=0,
                steps_saved=0,
                reason="Test",
            )

    def test_checkpoint_analysis_validation_savings(self):
        """Test savings validation."""
        with pytest.raises(ValueError, match="Savings estimates must be non-negative"):
            CheckpointAnalysis(
                mismatch_detected=True,
                current_workflow="*full",
                recommended_workflow="*build",
                confidence=0.85,
                detected_scope="low",
                detected_complexity="medium",
                story_points=8,
                files_affected=3,
                completed_steps=("enhance",),
                remaining_steps=("plan",),
                token_savings=-1000,  # Invalid: negative
                time_savings=10,
                steps_saved=1,
                reason="Test",
            )


# ============================================================================
# ArtifactManifest Tests
# ============================================================================

class TestArtifactManifest:
    """Tests for ArtifactManifest dataclass."""

    def test_artifact_manifest_to_dict(self):
        """Test converting manifest to dict."""
        manifest = ArtifactManifest(
            workflow_id="test-workflow-123",
            original_workflow="*full",
            new_workflow="*build",
            timestamp="2026-01-30T10:30:00Z",
            completed_steps=["enhance", "plan"],
            artifacts={"enhance": "artifacts/enhance_output.md"},
        )

        result = manifest.to_dict()

        assert result["workflow_id"] == "test-workflow-123"
        assert result["original_workflow"] == "*full"
        assert result["new_workflow"] == "*build"
        assert result["timestamp"] == "2026-01-30T10:30:00Z"
        assert result["completed_steps"] == ["enhance", "plan"]
        assert result["artifacts"] == {"enhance": "artifacts/enhance_output.md"}

    def test_artifact_manifest_from_dict(self):
        """Test creating manifest from dict."""
        data = {
            "workflow_id": "test-workflow-456",
            "original_workflow": "*full",
            "new_workflow": "*fix",
            "timestamp": "2026-01-30T11:00:00Z",
            "completed_steps": ["enhance", "plan", "architect"],
            "artifacts": {
                "enhance": "artifacts/enhance_output.md",
                "plan": "artifacts/plan_output.md",
            },
        }

        manifest = ArtifactManifest.from_dict(data)

        assert manifest.workflow_id == "test-workflow-456"
        assert manifest.original_workflow == "*full"
        assert manifest.new_workflow == "*fix"
        assert manifest.timestamp == "2026-01-30T11:00:00Z"
        assert manifest.completed_steps == ["enhance", "plan", "architect"]
        assert len(manifest.artifacts) == 2

    def test_artifact_manifest_roundtrip(self):
        """Test roundtrip conversion (to_dict → from_dict)."""
        original = ArtifactManifest(
            workflow_id="roundtrip-test",
            original_workflow="*build",
            new_workflow="*fix",
            timestamp="2026-01-30T12:00:00Z",
            completed_steps=["enhance"],
            artifacts={"enhance": "artifacts/enhance_output.md"},
        )

        # Convert to dict and back
        data = original.to_dict()
        restored = ArtifactManifest.from_dict(data)

        assert restored.workflow_id == original.workflow_id
        assert restored.original_workflow == original.original_workflow
        assert restored.new_workflow == original.new_workflow
        assert restored.timestamp == original.timestamp
        assert restored.completed_steps == original.completed_steps
        assert restored.artifacts == original.artifacts


# ============================================================================
# CheckpointManager Tests
# ============================================================================

class TestCheckpointManager:
    """Tests for CheckpointManager class."""

    def test_initialization_default(self):
        """Test default initialization."""
        manager = CheckpointManager()

        assert manager.token_estimates is not None
        assert manager.time_estimates is not None
        assert len(manager.token_estimates) > 0
        assert len(manager.time_estimates) > 0

    def test_initialization_custom_estimates(self):
        """Test initialization with custom estimates."""
        custom_token_estimates = {"enhance": 1000, "plan": 2000}
        custom_time_estimates = {"enhance": 1, "plan": 3}

        manager = CheckpointManager(
            token_estimates=custom_token_estimates,
            time_estimates=custom_time_estimates,
        )

        assert manager.token_estimates == custom_token_estimates
        assert manager.time_estimates == custom_time_estimates

    def test_initialization_validation_negative_tokens(self):
        """Test validation of negative token estimates."""
        with pytest.raises(ValueError, match="Token estimates must be non-negative"):
            CheckpointManager(token_estimates={"enhance": -1000})

    def test_initialization_validation_negative_time(self):
        """Test validation of negative time estimates."""
        with pytest.raises(ValueError, match="Time estimates must be non-negative"):
            CheckpointManager(time_estimates={"plan": -5})

    def test_analyze_checkpoint_no_mismatch(
        self, checkpoint_manager: CheckpointManager
    ):
        """Test checkpoint analysis with no mismatch (high complexity task)."""
        # High complexity task should match *full workflow
        planning = PlanningResults(
            story_points=21,  # High complexity
            files_affected=10,  # High scope
        )

        analysis = checkpoint_manager.analyze_checkpoint(
            workflow="*full",
            completed_steps=["enhance", "plan"],
            planning_results=planning,
        )

        assert not analysis.mismatch_detected
        assert analysis.recommended_workflow is None
        assert analysis.current_workflow == "*full"
        assert analysis.detected_complexity == "high"
        assert analysis.detected_scope == "high"
        assert analysis.token_savings == 0
        assert analysis.time_savings == 0
        assert analysis.steps_saved == 0

    def test_analyze_checkpoint_full_to_build_mismatch(
        self, checkpoint_manager: CheckpointManager, sample_planning_results: PlanningResults
    ):
        """Test *full workflow mismatch → recommend *build."""
        analysis = checkpoint_manager.analyze_checkpoint(
            workflow="*full",
            completed_steps=["enhance", "plan", "architect"],
            planning_results=sample_planning_results,
        )

        assert analysis.mismatch_detected
        assert analysis.recommended_workflow == "*build"
        assert analysis.current_workflow == "*full"
        assert analysis.detected_complexity == "medium"
        assert analysis.detected_scope == "low"
        assert analysis.story_points == 8
        assert analysis.files_affected == 3
        assert analysis.token_savings > 0  # Should save tokens
        assert analysis.time_savings > 0  # Should save time
        assert analysis.steps_saved > 0  # Should save steps
        assert analysis.confidence == 0.85

    def test_analyze_checkpoint_full_to_fix_mismatch(
        self, checkpoint_manager: CheckpointManager
    ):
        """Test *full workflow mismatch → recommend *fix (low complexity)."""
        planning = PlanningResults(
            story_points=3,  # Low complexity
            files_affected=2,  # Low scope
        )

        analysis = checkpoint_manager.analyze_checkpoint(
            workflow="*full",
            completed_steps=["enhance", "plan"],
            planning_results=planning,
        )

        assert analysis.mismatch_detected
        assert analysis.recommended_workflow == "*fix"
        assert analysis.detected_complexity == "low"
        assert analysis.detected_scope == "low"
        assert analysis.token_savings > 0
        assert analysis.steps_saved > 0

    def test_analyze_checkpoint_validation_unknown_workflow(
        self, checkpoint_manager: CheckpointManager, sample_planning_results: PlanningResults
    ):
        """Test validation of unknown workflow."""
        with pytest.raises(ValueError, match="Unknown workflow"):
            checkpoint_manager.analyze_checkpoint(
                workflow="*unknown",  # type: ignore
                completed_steps=["enhance"],
                planning_results=sample_planning_results,
            )

    def test_analyze_checkpoint_validation_empty_steps(
        self, checkpoint_manager: CheckpointManager, sample_planning_results: PlanningResults
    ):
        """Test validation of empty completed_steps."""
        with pytest.raises(ValueError, match="completed_steps must not be empty"):
            checkpoint_manager.analyze_checkpoint(
                workflow="*full",
                completed_steps=[],  # Invalid: empty
                planning_results=sample_planning_results,
            )

    def test_analyze_checkpoint_validation_missing_story_points(
        self, checkpoint_manager: CheckpointManager
    ):
        """Test validation of missing story_points in planning_results."""
        invalid_planning: PlanningResults = {
            "files_affected": 3,
            # Missing story_points
        }

        with pytest.raises(TypeError, match="planning_results missing required key"):
            checkpoint_manager.analyze_checkpoint(
                workflow="*full",
                completed_steps=["enhance"],
                planning_results=invalid_planning,
            )

    def test_analyze_checkpoint_performance(
        self, checkpoint_manager: CheckpointManager, sample_planning_results: PlanningResults
    ):
        """Test that checkpoint analysis completes in < 500ms."""
        start = time.perf_counter()

        checkpoint_manager.analyze_checkpoint(
            workflow="*full",
            completed_steps=["enhance", "plan"],
            planning_results=sample_planning_results,
        )

        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms

        assert elapsed < 500, f"Analysis took {elapsed:.2f}ms (target: <500ms)"

    def test_analyze_checkpoint_completed_remaining_steps(
        self, checkpoint_manager: CheckpointManager, sample_planning_results: PlanningResults
    ):
        """Test completed and remaining steps are calculated correctly."""
        analysis = checkpoint_manager.analyze_checkpoint(
            workflow="*full",
            completed_steps=["enhance", "plan", "architect"],
            planning_results=sample_planning_results,
        )

        # Verify completed steps
        assert analysis.completed_steps == ("enhance", "plan", "architect")

        # Verify remaining steps
        expected_remaining = ("design", "implement", "review", "test", "security", "document")
        assert analysis.remaining_steps == expected_remaining

    def test_analyze_planning_artifacts_scope_mapping(
        self, checkpoint_manager: CheckpointManager
    ):
        """Test scope mapping from files_affected."""
        # Test low scope (1-3 files)
        planning_low = PlanningResults(story_points=5, files_affected=2)
        chars_low = checkpoint_manager._analyze_planning_artifacts(planning_low)
        assert chars_low["scope"] == "low"

        # Test medium scope (4-6 files)
        planning_medium = PlanningResults(story_points=5, files_affected=5)
        chars_medium = checkpoint_manager._analyze_planning_artifacts(planning_medium)
        assert chars_medium["scope"] == "medium"

        # Test high scope (7+ files)
        planning_high = PlanningResults(story_points=5, files_affected=10)
        chars_high = checkpoint_manager._analyze_planning_artifacts(planning_high)
        assert chars_high["scope"] == "high"

    def test_analyze_planning_artifacts_complexity_mapping(
        self, checkpoint_manager: CheckpointManager
    ):
        """Test complexity mapping from story_points."""
        # Test low complexity (1-5 points)
        planning_low = PlanningResults(story_points=3, files_affected=2)
        chars_low = checkpoint_manager._analyze_planning_artifacts(planning_low)
        assert chars_low["complexity"] == "low"

        # Test medium complexity (8-13 points)
        planning_medium = PlanningResults(story_points=8, files_affected=2)
        chars_medium = checkpoint_manager._analyze_planning_artifacts(planning_medium)
        assert chars_medium["complexity"] == "medium"

        # Test high complexity (21+ points)
        planning_high = PlanningResults(story_points=21, files_affected=2)
        chars_high = checkpoint_manager._analyze_planning_artifacts(planning_high)
        assert chars_high["complexity"] == "high"

    def test_calculate_savings(self, checkpoint_manager: CheckpointManager):
        """Test token/time savings calculation."""
        token_savings, time_savings, steps_saved = checkpoint_manager._calculate_savings(
            current_workflow="*full",
            recommended_workflow="*build",
            completed_steps=["enhance", "plan", "architect"],
        )

        # *full has 9 steps, *build has 7 steps
        # Completed: 3, Remaining in *full: 6, Remaining in *build: 4
        # Steps saved: 6 - 4 = 2 (security, document)
        assert steps_saved == 2
        assert token_savings > 0  # Should save tokens for skipped steps
        assert time_savings > 0  # Should save time for skipped steps

    def test_calculate_savings_no_recommendation(
        self, checkpoint_manager: CheckpointManager
    ):
        """Test savings calculation with no recommendation."""
        token_savings, time_savings, steps_saved = checkpoint_manager._calculate_savings(
            current_workflow="*full",
            recommended_workflow=None,
            completed_steps=["enhance"],
        )

        assert token_savings == 0
        assert time_savings == 0
        assert steps_saved == 0


# ============================================================================
# WorkflowSwitcher Tests
# ============================================================================

class TestWorkflowSwitcher:
    """Tests for WorkflowSwitcher class."""

    def test_initialization(self, temp_checkpoint_dir: Path):
        """Test WorkflowSwitcher initialization."""
        switcher = WorkflowSwitcher(temp_checkpoint_dir)

        assert switcher.checkpoint_dir == temp_checkpoint_dir
        assert temp_checkpoint_dir.exists()
        assert temp_checkpoint_dir.is_dir()

    def test_initialization_creates_directory(self, tmp_path: Path):
        """Test that initialization creates checkpoint directory if missing."""
        new_dir = tmp_path / "new_checkpoints"
        assert not new_dir.exists()

        switcher = WorkflowSwitcher(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_initialization_validation_not_directory(self, tmp_path: Path):
        """Test validation that checkpoint_dir must be a directory."""
        file_path = tmp_path / "not_a_dir.txt"
        file_path.write_text("test")

        with pytest.raises(ValueError, match="checkpoint_dir must be a directory"):
            WorkflowSwitcher(file_path)

    def test_switch_workflow_success(
        self,
        workflow_switcher: WorkflowSwitcher,
        sample_artifacts: dict[str, Any],
        temp_checkpoint_dir: Path,
    ):
        """Test successful workflow switch."""
        result = workflow_switcher.switch_workflow(
            workflow_id="test-workflow-123",
            from_workflow="*full",
            to_workflow="*build",
            completed_steps=["enhance", "plan", "architect"],
            artifacts=sample_artifacts,
        )

        assert result["success"]
        assert result["new_workflow_id"] == "test-workflow-123"
        assert "enhance" in result["preserved_artifacts"]
        assert "plan" in result["preserved_artifacts"]
        assert "architect" in result["preserved_artifacts"]
        assert result["resume_from_step"] == "design"  # First uncompleted step in *build
        assert result["error"] is None

        # Verify files were created
        workflow_dir = temp_checkpoint_dir / "test-workflow-123"
        assert workflow_dir.exists()
        assert (workflow_dir / "manifest.json").exists()
        assert (workflow_dir / "artifacts").exists()

    def test_switch_workflow_validation_invalid_workflow_id(
        self, workflow_switcher: WorkflowSwitcher, sample_artifacts: dict[str, Any]
    ):
        """Test validation of invalid workflow_id."""
        with pytest.raises(ValueError, match="Invalid workflow_id"):
            workflow_switcher.switch_workflow(
                workflow_id="../../../etc/passwd",  # Invalid: path traversal
                from_workflow="*full",
                to_workflow="*build",
                completed_steps=["enhance"],
                artifacts=sample_artifacts,
            )

    def test_switch_workflow_validation_empty_steps(
        self, workflow_switcher: WorkflowSwitcher, sample_artifacts: dict[str, Any]
    ):
        """Test validation of empty completed_steps."""
        with pytest.raises(ValueError, match="completed_steps must not be empty"):
            workflow_switcher.switch_workflow(
                workflow_id="test-123",
                from_workflow="*full",
                to_workflow="*build",
                completed_steps=[],  # Invalid: empty
                artifacts=sample_artifacts,
            )

    def test_switch_workflow_artifact_preservation(
        self,
        workflow_switcher: WorkflowSwitcher,
        sample_artifacts: dict[str, Any],
        temp_checkpoint_dir: Path,
    ):
        """Test that artifacts are preserved correctly."""
        result = workflow_switcher.switch_workflow(
            workflow_id="artifact-test",
            from_workflow="*full",
            to_workflow="*build",
            completed_steps=["enhance", "plan"],
            artifacts=sample_artifacts,
        )

        assert result["success"]

        # Verify artifact files exist
        artifacts_dir = temp_checkpoint_dir / "artifact-test" / "artifacts"
        assert (artifacts_dir / "enhance_output.md").exists()
        assert (artifacts_dir / "plan_output.md").exists()

        # Verify artifact content
        enhance_content = (artifacts_dir / "enhance_output.md").read_text(encoding="utf-8")
        assert enhance_content == sample_artifacts["enhance"]

        plan_content = (artifacts_dir / "plan_output.md").read_text(encoding="utf-8")
        plan_data = json.loads(plan_content)
        assert plan_data == sample_artifacts["plan"]

    def test_switch_workflow_manifest_creation(
        self,
        workflow_switcher: WorkflowSwitcher,
        sample_artifacts: dict[str, Any],
        temp_checkpoint_dir: Path,
    ):
        """Test that manifest file is created correctly."""
        result = workflow_switcher.switch_workflow(
            workflow_id="manifest-test",
            from_workflow="*full",
            to_workflow="*fix",
            completed_steps=["enhance", "plan", "architect"],
            artifacts=sample_artifacts,
        )

        assert result["success"]

        # Read and verify manifest
        manifest_path = temp_checkpoint_dir / "manifest-test" / "manifest.json"
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))

        assert manifest_data["workflow_id"] == "manifest-test"
        assert manifest_data["original_workflow"] == "*full"
        assert manifest_data["new_workflow"] == "*fix"
        assert manifest_data["completed_steps"] == ["enhance", "plan", "architect"]
        assert "enhance" in manifest_data["artifacts"]

    def test_restore_artifacts_success(
        self,
        workflow_switcher: WorkflowSwitcher,
        sample_artifacts: dict[str, Any],
    ):
        """Test successful artifact restoration."""
        # First, switch workflow to create artifacts
        workflow_switcher.switch_workflow(
            workflow_id="restore-test",
            from_workflow="*full",
            to_workflow="*build",
            completed_steps=["enhance", "plan"],
            artifacts=sample_artifacts,
        )

        # Then, restore artifacts
        restored = workflow_switcher.restore_artifacts("restore-test")

        assert restored is not None
        assert "enhance" in restored
        assert "plan" in restored
        assert restored["enhance"] == sample_artifacts["enhance"]
        assert restored["plan"] == sample_artifacts["plan"]

    def test_restore_artifacts_not_found(self, workflow_switcher: WorkflowSwitcher):
        """Test restoring artifacts for non-existent workflow."""
        restored = workflow_switcher.restore_artifacts("nonexistent-workflow")

        assert restored is None

    def test_restore_artifacts_validation_invalid_id(
        self, workflow_switcher: WorkflowSwitcher
    ):
        """Test validation of invalid workflow_id in restore."""
        with pytest.raises(ValueError, match="Invalid workflow_id"):
            workflow_switcher.restore_artifacts("../invalid/path")

    def test_is_valid_workflow_id(self):
        """Test workflow ID validation."""
        # Valid IDs
        assert WorkflowSwitcher._is_valid_workflow_id("build-abc123")
        assert WorkflowSwitcher._is_valid_workflow_id("workflow-2026-01-30")
        assert WorkflowSwitcher._is_valid_workflow_id("test-123-456")
        assert WorkflowSwitcher._is_valid_workflow_id("abc")

        # Invalid IDs
        assert not WorkflowSwitcher._is_valid_workflow_id("../path/traversal")
        assert not WorkflowSwitcher._is_valid_workflow_id("workflow/with/slashes")
        assert not WorkflowSwitcher._is_valid_workflow_id("UPPERCASE")
        assert not WorkflowSwitcher._is_valid_workflow_id("with spaces")
        assert not WorkflowSwitcher._is_valid_workflow_id("with_underscores")
        assert not WorkflowSwitcher._is_valid_workflow_id("")

    def test_get_workflow_steps(self, workflow_switcher: WorkflowSwitcher):
        """Test getting workflow step sequences."""
        full_steps = workflow_switcher._get_workflow_steps("*full")
        assert len(full_steps) == 9
        assert full_steps[0] == "enhance"
        assert "security" in full_steps

        build_steps = workflow_switcher._get_workflow_steps("*build")
        assert len(build_steps) == 7
        assert "security" not in build_steps

        fix_steps = workflow_switcher._get_workflow_steps("*fix")
        assert len(fix_steps) == 3
        assert fix_steps == ["debug", "implement", "test"]


# ============================================================================
# Integration Tests
# ============================================================================

class TestCheckpointIntegration:
    """Integration tests for checkpoint system."""

    def test_full_checkpoint_flow(
        self,
        checkpoint_manager: CheckpointManager,
        workflow_switcher: WorkflowSwitcher,
        sample_planning_results: PlanningResults,
        sample_artifacts: dict[str, Any],
    ):
        """Test complete checkpoint flow: analyze → switch → restore."""
        # Step 1: Analyze checkpoint
        analysis = checkpoint_manager.analyze_checkpoint(
            workflow="*full",
            completed_steps=["enhance", "plan", "architect"],
            planning_results=sample_planning_results,
        )

        assert analysis.mismatch_detected
        assert analysis.recommended_workflow == "*build"

        # Step 2: Switch workflow
        switch_result = workflow_switcher.switch_workflow(
            workflow_id="integration-test",
            from_workflow=analysis.current_workflow,
            to_workflow=analysis.recommended_workflow,
            completed_steps=list(analysis.completed_steps),
            artifacts=sample_artifacts,
        )

        assert switch_result["success"]
        assert switch_result["resume_from_step"] == "design"

        # Step 3: Restore artifacts
        restored = workflow_switcher.restore_artifacts("integration-test")

        assert restored is not None
        assert len(restored) == 3
        assert all(step in restored for step in ["enhance", "plan", "architect"])

    def test_checkpoint_with_different_workflows(
        self, checkpoint_manager: CheckpointManager
    ):
        """Test checkpoint analysis with different workflow types."""
        planning = PlanningResults(story_points=5, files_affected=2)

        # Test with *full
        analysis_full = checkpoint_manager.analyze_checkpoint(
            "*full", ["enhance"], planning
        )
        assert analysis_full.mismatch_detected

        # Test with *build (should not mismatch)
        analysis_build = checkpoint_manager.analyze_checkpoint(
            "*build", ["enhance"], planning
        )
        assert not analysis_build.mismatch_detected

        # Test with *fix (should not mismatch)
        analysis_fix = checkpoint_manager.analyze_checkpoint(
            "*fix", ["debug"], planning
        )
        assert not analysis_fix.mismatch_detected
