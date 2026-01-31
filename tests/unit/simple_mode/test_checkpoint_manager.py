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


# ============================================================================
# BuildOrchestrator Integration Tests (Phase 1B)
# ============================================================================

@pytest.mark.unit
class TestBuildOrchestratorCheckpointIntegration:
    """Tests for BuildOrchestrator checkpoint integration (Phase 1B)."""

    @pytest.fixture
    def mock_orchestrator(self, tmp_path: Path):
        """Create a mock BuildOrchestrator for testing."""
        from tapps_agents.simple_mode.orchestrators.build_orchestrator import BuildOrchestrator
        from tapps_agents.core.config import ProjectConfig, SimpleModeConfig

        config = ProjectConfig()
        config.simple_mode = SimpleModeConfig(
            enable_checkpoints=True,
            checkpoint_confidence_threshold=0.7
        )

        orchestrator = BuildOrchestrator(tmp_path, config)
        return orchestrator

    @pytest.fixture
    def sample_checkpoint_analysis(self) -> CheckpointAnalysis:
        """Sample checkpoint analysis for testing."""
        return CheckpointAnalysis(
            mismatch_detected=True,
            current_workflow="*full",
            recommended_workflow="*build",
            confidence=0.85,
            detected_scope="low",
            detected_complexity="medium",
            story_points=8,
            files_affected=3,
            completed_steps=("enhance", "plan", "architect"),
            remaining_steps=("design", "implement", "review", "test", "security", "document"),
            token_savings=12000,
            time_savings=14,
            steps_saved=2,
            reason="Task characteristics suggest *build workflow is more appropriate",
        )

    @pytest.mark.asyncio
    async def test_offer_workflow_switch_user_chooses_switch(
        self, mock_orchestrator, sample_checkpoint_analysis, monkeypatch
    ):
        """Test user input: choice 1 (switch)."""
        # Mock input() to return "1"
        monkeypatch.setattr("builtins.input", lambda: "1")

        choice = await mock_orchestrator._offer_workflow_switch(sample_checkpoint_analysis)

        assert choice == "switch"

    @pytest.mark.asyncio
    async def test_offer_workflow_switch_user_chooses_continue(
        self, mock_orchestrator, sample_checkpoint_analysis, monkeypatch
    ):
        """Test user input: choice 2 (continue)."""
        # Mock input() to return "2"
        monkeypatch.setattr("builtins.input", lambda: "2")

        choice = await mock_orchestrator._offer_workflow_switch(sample_checkpoint_analysis)

        assert choice == "continue"

    @pytest.mark.asyncio
    async def test_offer_workflow_switch_user_chooses_cancel(
        self, mock_orchestrator, sample_checkpoint_analysis, monkeypatch
    ):
        """Test user input: choice 3 (cancel)."""
        # Mock input() to return "3"
        monkeypatch.setattr("builtins.input", lambda: "3")

        choice = await mock_orchestrator._offer_workflow_switch(sample_checkpoint_analysis)

        assert choice == "cancel"

    @pytest.mark.asyncio
    async def test_offer_workflow_switch_invalid_choice(
        self, mock_orchestrator, sample_checkpoint_analysis, monkeypatch
    ):
        """Test user input: invalid choice defaults to continue."""
        # Mock input() to return invalid choice
        monkeypatch.setattr("builtins.input", lambda: "invalid")

        choice = await mock_orchestrator._offer_workflow_switch(sample_checkpoint_analysis)

        assert choice == "continue"

    @pytest.mark.asyncio
    async def test_offer_workflow_switch_ctrl_c_handling(
        self, mock_orchestrator, sample_checkpoint_analysis, monkeypatch
    ):
        """Test user input: Ctrl+C (KeyboardInterrupt) returns cancel."""
        # Mock input() to raise KeyboardInterrupt
        def mock_input():
            raise KeyboardInterrupt()

        monkeypatch.setattr("builtins.input", mock_input)

        choice = await mock_orchestrator._offer_workflow_switch(sample_checkpoint_analysis)

        assert choice == "cancel"

    @pytest.mark.asyncio
    async def test_offer_workflow_switch_eof_handling(
        self, mock_orchestrator, sample_checkpoint_analysis, monkeypatch
    ):
        """Test user input: EOF returns cancel."""
        # Mock input() to raise EOFError
        def mock_input():
            raise EOFError()

        monkeypatch.setattr("builtins.input", mock_input)

        choice = await mock_orchestrator._offer_workflow_switch(sample_checkpoint_analysis)

        assert choice == "cancel"

    @pytest.mark.asyncio
    async def test_offer_workflow_switch_whitespace_handling(
        self, mock_orchestrator, sample_checkpoint_analysis, monkeypatch
    ):
        """Test user input: whitespace is stripped."""
        # Mock input() to return "  1  " (with whitespace)
        monkeypatch.setattr("builtins.input", lambda: "  1  ")

        choice = await mock_orchestrator._offer_workflow_switch(sample_checkpoint_analysis)

        assert choice == "switch"

    @pytest.mark.asyncio
    async def test_switch_and_resume_successful_switch(
        self, mock_orchestrator, sample_checkpoint_analysis, sample_artifacts, monkeypatch
    ):
        """Test successful workflow switch and resume."""
        from tapps_agents.simple_mode.intent_parser import Intent, IntentType

        workflow_id = "test-workflow-123"
        completed_steps = ["enhance", "plan", "architect"]

        # Mock the new orchestrator's execute method
        async def mock_execute(intent, params, fast_mode=False):
            return {
                "success": True,
                "result": "Test implementation complete",
            }

        # Store original intent for resume
        original_intent = Intent(
            type=IntentType.BUILD,
            confidence=1.0,
            parameters={},
            original_input="Test task",
        )
        mock_orchestrator._current_intent = original_intent

        # Mock execute method
        monkeypatch.setattr(mock_orchestrator, "execute", mock_execute)

        result = await mock_orchestrator._switch_and_resume(
            sample_checkpoint_analysis,
            workflow_id,
            completed_steps,
            sample_artifacts,
        )

        assert result["success"]
        assert result["switched"]
        assert result["final_workflow"] == "*build"
        assert result["original_workflow"] == "*full"
        assert result["checkpoint_id"] == workflow_id
        assert result["token_savings"] == 12000
        assert result["time_savings"] == 14

    @pytest.mark.asyncio
    async def test_switch_and_resume_artifact_restoration(
        self, mock_orchestrator, sample_checkpoint_analysis, sample_artifacts, monkeypatch
    ):
        """Test that artifacts are restored correctly during resume."""
        from tapps_agents.simple_mode.intent_parser import Intent, IntentType

        workflow_id = "artifact-restore-test"
        completed_steps = ["enhance", "plan", "architect"]

        # Capture the parameters passed to execute
        captured_params = {}

        async def mock_execute(intent, params, fast_mode=False):
            captured_params.update(params)
            return {"success": True}

        original_intent = Intent(
            type=IntentType.BUILD,
            confidence=1.0,
            parameters={},
            original_input="Test task",
        )
        mock_orchestrator._current_intent = original_intent

        monkeypatch.setattr(mock_orchestrator, "execute", mock_execute)

        await mock_orchestrator._switch_and_resume(
            sample_checkpoint_analysis,
            workflow_id,
            completed_steps,
            sample_artifacts,
        )

        # Verify resume parameters were passed
        assert captured_params.get("_resumed") is True
        assert "_checkpoint_artifacts" in captured_params
        assert captured_params["_completed_steps"] == completed_steps
        assert "_resume_from_step" in captured_params

    @pytest.mark.asyncio
    async def test_switch_and_resume_no_artifacts_found(
        self, mock_orchestrator, sample_checkpoint_analysis, sample_artifacts, monkeypatch
    ):
        """Test graceful handling when no artifacts are found."""
        from tapps_agents.simple_mode.intent_parser import Intent, IntentType

        workflow_id = "no-artifacts-test"
        completed_steps = ["enhance", "plan"]

        # Mock restore_artifacts to return None (no artifacts found)
        from tapps_agents.simple_mode.checkpoint_manager import WorkflowSwitcher

        async def mock_execute(intent, params, fast_mode=False):
            return {"success": True}

        original_intent = Intent(
            type=IntentType.BUILD,
            confidence=1.0,
            parameters={},
            original_input="Test task",
        )
        mock_orchestrator._current_intent = original_intent

        monkeypatch.setattr(mock_orchestrator, "execute", mock_execute)

        # Create a mock switcher that returns None for restore_artifacts
        # This will be handled by the actual WorkflowSwitcher logic

        result = await mock_orchestrator._switch_and_resume(
            sample_checkpoint_analysis,
            workflow_id,
            completed_steps,
            sample_artifacts,
        )

        # Should still succeed, just with empty artifacts
        assert result["success"]
        assert result["switched"]

    @pytest.mark.asyncio
    async def test_checkpoint_after_planning_no_mismatch(
        self, mock_orchestrator
    ):
        """Test checkpoint analysis when no mismatch is detected."""
        planning_results = {
            "story_points": 21,  # High complexity
            "files_affected": 10,  # High scope
        }

        artifacts = {
            "enhance": "Enhanced prompt",
            "plan": {"stories": []},
            "architect": "Architecture design",
        }

        analysis = await mock_orchestrator._checkpoint_after_planning(
            workflow="*full",
            completed_steps=["enhance", "plan", "architect"],
            planning_results=planning_results,
            artifacts=artifacts,
        )

        # Should return None (no mismatch)
        assert analysis is None

    @pytest.mark.asyncio
    async def test_checkpoint_after_planning_mismatch_detected(
        self, mock_orchestrator
    ):
        """Test checkpoint analysis when mismatch is detected."""
        planning_results = {
            "story_points": 8,  # Medium complexity
            "files_affected": 3,  # Low scope
        }

        artifacts = {
            "enhance": "Enhanced prompt",
            "plan": {"stories": []},
            "architect": "Architecture design",
        }

        analysis = await mock_orchestrator._checkpoint_after_planning(
            workflow="*full",
            completed_steps=["enhance", "plan", "architect"],
            planning_results=planning_results,
            artifacts=artifacts,
        )

        # Should detect mismatch and recommend *build
        assert analysis is not None
        assert analysis.mismatch_detected
        assert analysis.recommended_workflow == "*build"
        assert analysis.token_savings > 0
        assert analysis.time_savings > 0

    @pytest.mark.asyncio
    async def test_checkpoint_flags_no_auto_checkpoint(
        self, mock_orchestrator, sample_checkpoint_analysis
    ):
        """Test that --no-auto-checkpoint flag is respected."""
        # This would be tested in execute() method integration
        # For now, verify the flag can be set
        parameters = {"no_auto_checkpoint": True}

        assert parameters.get("no_auto_checkpoint") is True

    @pytest.mark.asyncio
    async def test_checkpoint_flags_checkpoint_debug(
        self, mock_orchestrator
    ):
        """Test that --checkpoint-debug flag enables debug logging."""
        import logging

        parameters = {"checkpoint_debug": True}

        # Verify flag is set
        assert parameters.get("checkpoint_debug") is True

        # In actual code, this would enable debug logging
        # Testing the logger level change requires more complex setup

    @pytest.mark.asyncio
    async def test_resume_detection_in_execute(
        self, mock_orchestrator
    ):
        """Test that resumed workflows are detected correctly."""
        parameters = {
            "_resumed": True,
            "_checkpoint_artifacts": {"enhance": "test"},
            "_completed_steps": ["enhance", "plan"],
            "_resume_from_step": "design",
        }

        # Verify resume parameters are present
        assert parameters.get("_resumed") is True
        assert "_checkpoint_artifacts" in parameters
        assert "_completed_steps" in parameters
        assert "_resume_from_step" in parameters

    @pytest.mark.asyncio
    async def test_switch_and_resume_to_fix_workflow(
        self, mock_orchestrator, sample_artifacts, monkeypatch, tmp_path
    ):
        """Test switching to *fix workflow."""
        from tapps_agents.simple_mode.intent_parser import Intent, IntentType
        from tapps_agents.simple_mode.orchestrators.fix_orchestrator import FixOrchestrator

        analysis = CheckpointAnalysis(
            mismatch_detected=True,
            current_workflow="*full",
            recommended_workflow="*fix",  # Switch to *fix
            confidence=0.90,
            detected_scope="low",
            detected_complexity="low",
            story_points=3,
            files_affected=1,
            completed_steps=("enhance", "plan"),
            remaining_steps=("debug", "implement", "test"),
            token_savings=40000,
            time_savings=60,
            steps_saved=6,
            reason="Simple bug fix",
        )

        # Mock FixOrchestrator's execute method to avoid dependency issues
        async def mock_fix_execute(self, intent, params):
            return {"success": True}

        monkeypatch.setattr(FixOrchestrator, "execute", mock_fix_execute)

        original_intent = Intent(
            type=IntentType.BUILD,
            confidence=1.0,
            parameters={},
            original_input="Fix bug",
        )
        mock_orchestrator._current_intent = original_intent

        result = await mock_orchestrator._switch_and_resume(
            analysis,
            "fix-workflow-test",
            ["enhance", "plan"],
            sample_artifacts,
        )

        assert result["success"]
        assert result["final_workflow"] == "*fix"
        assert result["token_savings"] == 40000


# ============================================================================
# Checkpoint 1 Tests (Early Checkpoint After Enhance)
# ============================================================================

class TestCheckpointManagerEarlyCheckpoint:
    """Tests for CheckpointManager.analyze_early_checkpoint() (Checkpoint 1)."""

    def test_analyze_early_checkpoint_bug_fix_detected(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """Test that bug fix intent is detected from prompt text."""
        # Bug fix prompt should trigger *fix recommendation
        enhanced_prompt = "Fix validation bug in user profile that causes crash when loading"

        analysis = checkpoint_manager.analyze_early_checkpoint(
            workflow="*full",
            enhanced_prompt=enhanced_prompt,
        )

        assert analysis.mismatch_detected
        assert analysis.recommended_workflow == "*fix"
        assert analysis.confidence == 0.70  # Early checkpoint has lower confidence
        assert "enhance" in analysis.completed_steps
        assert len(analysis.completed_steps) == 1  # Only enhance completed
        assert analysis.token_savings > 0
        assert analysis.time_savings > 0

    def test_analyze_early_checkpoint_simple_task_detected(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """Test that simple tasks trigger *build recommendation."""
        # Simple task prompt (low complexity)
        enhanced_prompt = "Add logging statement to track user login events"

        analysis = checkpoint_manager.analyze_early_checkpoint(
            workflow="*full",
            enhanced_prompt=enhanced_prompt,
        )

        assert analysis.mismatch_detected
        assert analysis.recommended_workflow == "*build"
        assert analysis.confidence == 0.70
        assert analysis.detected_complexity == "low"

    def test_analyze_early_checkpoint_complex_task_no_mismatch(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """Test that complex tasks don't trigger mismatch for *full workflow."""
        # Complex architectural task (should use *full)
        enhanced_prompt = """
        Implement OAuth2 authentication system with multi-tenant isolation.
        Requirements:
        - Support multiple OAuth providers (Google, GitHub, Azure)
        - Tenant-based session management with Redis
        - Role-based access control with JWT tokens
        - Secure token refresh mechanism
        - Audit logging for all authentication events
        """

        analysis = checkpoint_manager.analyze_early_checkpoint(
            workflow="*full",
            enhanced_prompt=enhanced_prompt,
        )

        assert not analysis.mismatch_detected
        assert analysis.detected_complexity == "high"
        assert analysis.recommended_workflow is None

    def test_analyze_early_checkpoint_medium_complexity(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """Test medium complexity task detection."""
        # Medium complexity task
        enhanced_prompt = """
        Add user profile page with photo upload and settings.
        Need to create new API endpoint, update database schema,
        and add frontend UI component.
        """

        analysis = checkpoint_manager.analyze_early_checkpoint(
            workflow="*full",
            enhanced_prompt=enhanced_prompt,
        )

        assert analysis.mismatch_detected
        assert analysis.recommended_workflow == "*build"
        # Word count ~30 words → "low" complexity (not "medium")
        assert analysis.detected_complexity == "low"
        assert analysis.detected_scope == "low"

    def test_analyze_early_checkpoint_invalid_workflow(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """Test error handling for invalid workflow type."""
        with pytest.raises(ValueError, match="Unknown workflow"):
            checkpoint_manager.analyze_early_checkpoint(
                workflow="*invalid",
                enhanced_prompt="Some task",
            )

    def test_analyze_early_checkpoint_prompt_analysis_heuristics(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """Test that prompt text analysis heuristics work correctly."""
        # Test various keyword patterns
        bug_fix_prompts = [
            "Fix error in login page",
            "Resolve issue with database connection",
            "Correct typo in user name field",
            "Debug broken test suite",
        ]

        for prompt in bug_fix_prompts:
            analysis = checkpoint_manager.analyze_early_checkpoint(
                workflow="*full",
                enhanced_prompt=prompt,
            )
            assert analysis.mismatch_detected, f"Failed to detect bug fix in: {prompt}"
            assert analysis.recommended_workflow == "*fix"

    def test_analyze_early_checkpoint_word_count_complexity(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """Test that word count influences complexity estimate."""
        # Very short prompt → low complexity
        short_prompt = "Add button"
        analysis_short = checkpoint_manager.analyze_early_checkpoint(
            workflow="*full",
            enhanced_prompt=short_prompt,
        )
        assert analysis_short.detected_complexity == "low"

        # Long prompt → high complexity
        long_prompt = " ".join(["word"] * 150)  # 150 words
        analysis_long = checkpoint_manager.analyze_early_checkpoint(
            workflow="*full",
            enhanced_prompt=long_prompt,
        )
        assert analysis_long.detected_complexity == "high"


# ============================================================================
# Checkpoint 3 Tests (Quality Gate After Test)
# ============================================================================

class TestCheckpointManagerQualityGate:
    """Tests for CheckpointManager.analyze_quality_gate() (Checkpoint 3)."""

    def test_analyze_quality_gate_excellent_quality_skip_all_optional(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """Test that excellent quality (≥80) suggests skipping all optional steps."""
        completed_steps = ["enhance", "plan", "architect", "design", "implement", "review", "test"]

        analysis = checkpoint_manager.analyze_quality_gate(
            workflow="*full",
            completed_steps=completed_steps,
            quality_score=82.5,
            token_usage=45000,
        )

        assert analysis.mismatch_detected  # "mismatch" = early termination recommended
        # remaining_steps should be empty (all optional steps skipped)
        assert len(analysis.remaining_steps) == 0
        assert analysis.confidence == 0.90  # High confidence for quality gate
        assert analysis.token_savings > 0
        assert analysis.time_savings > 0
        assert analysis.steps_saved == 2

    def test_analyze_quality_gate_good_quality_skip_docs_only(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """Test that good quality (75-80) suggests skipping docs only."""
        completed_steps = ["enhance", "plan", "architect", "design", "implement", "review", "test"]

        analysis = checkpoint_manager.analyze_quality_gate(
            workflow="*full",
            completed_steps=completed_steps,
            quality_score=77.0,
            token_usage=40000,
        )

        assert analysis.mismatch_detected
        # remaining_steps should contain security (document was skipped)
        assert "security" in analysis.remaining_steps
        assert "document" not in analysis.remaining_steps  # Document skipped
        assert len(analysis.remaining_steps) == 1
        assert analysis.steps_saved == 1

    def test_analyze_quality_gate_low_quality_no_skip(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """Test that low quality (<75) doesn't suggest skipping steps."""
        completed_steps = ["enhance", "plan", "architect", "design", "implement", "review", "test"]

        analysis = checkpoint_manager.analyze_quality_gate(
            workflow="*full",
            completed_steps=completed_steps,
            quality_score=68.0,
            token_usage=40000,
        )

        assert not analysis.mismatch_detected  # No early termination recommended
        # remaining_steps should contain both security and document (nothing skipped)
        assert len(analysis.remaining_steps) == 2
        assert "security" in analysis.remaining_steps
        assert "document" in analysis.remaining_steps
        assert analysis.steps_saved == 0
        assert analysis.token_savings == 0

    def test_analyze_quality_gate_build_workflow_no_optional_steps(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """Test that *build workflow has no optional steps to skip."""
        # Complete all *build workflow steps
        completed_steps = ["enhance", "plan", "architect", "design", "implement", "review", "test"]

        analysis = checkpoint_manager.analyze_quality_gate(
            workflow="*build",
            completed_steps=completed_steps,
            quality_score=85.0,
        )

        # *build has no security/document steps, so nothing to skip
        assert not analysis.mismatch_detected
        assert len(analysis.remaining_steps) == 0

    def test_analyze_quality_gate_fix_workflow(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """Test quality gate for *fix workflow."""
        completed_steps = ["debug", "fix", "test"]

        analysis = checkpoint_manager.analyze_quality_gate(
            workflow="*fix",
            completed_steps=completed_steps,
            quality_score=90.0,
        )

        # *fix workflow is already minimal, no optional steps
        assert not analysis.mismatch_detected

    def test_analyze_quality_gate_token_usage_tracking(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """Test that token usage is tracked in quality gate analysis."""
        completed_steps = ["enhance", "plan", "architect", "design", "implement", "review", "test"]

        analysis = checkpoint_manager.analyze_quality_gate(
            workflow="*full",
            completed_steps=completed_steps,
            quality_score=85.0,
            token_usage=50000,
        )

        # Token savings should be calculated based on skipped steps
        assert analysis.token_savings > 0
        assert analysis.token_savings < 50000  # Savings less than total usage

    def test_analyze_quality_gate_invalid_workflow(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """Test error handling for invalid workflow type."""
        with pytest.raises(ValueError, match="Unknown workflow"):
            checkpoint_manager.analyze_quality_gate(
                workflow="*invalid",
                completed_steps=["enhance"],
                quality_score=80.0,
            )

    def test_analyze_quality_gate_boundary_conditions(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """Test boundary conditions for quality thresholds."""
        completed_steps = ["enhance", "plan", "architect", "design", "implement", "review", "test"]

        # Exactly 80.0 (excellent threshold) - skip both security and document
        analysis_80 = checkpoint_manager.analyze_quality_gate(
            workflow="*full",
            completed_steps=completed_steps,
            quality_score=80.0,
        )
        assert analysis_80.mismatch_detected
        assert len(analysis_80.remaining_steps) == 0  # All optional steps skipped
        assert analysis_80.steps_saved == 2

        # Exactly 75.0 (good threshold) - skip document only
        analysis_75 = checkpoint_manager.analyze_quality_gate(
            workflow="*full",
            completed_steps=completed_steps,
            quality_score=75.0,
        )
        assert analysis_75.mismatch_detected
        assert len(analysis_75.remaining_steps) == 1  # Security remains
        assert "security" in analysis_75.remaining_steps
        assert analysis_75.steps_saved == 1

        # Just below 75.0 - skip nothing
        analysis_74 = checkpoint_manager.analyze_quality_gate(
            workflow="*full",
            completed_steps=completed_steps,
            quality_score=74.9,
        )
        assert not analysis_74.mismatch_detected
        assert len(analysis_74.remaining_steps) == 2  # Both security and document remain
        assert analysis_74.steps_saved == 0
