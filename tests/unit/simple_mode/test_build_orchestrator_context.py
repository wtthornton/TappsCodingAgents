"""
Tests for BuildOrchestrator context enrichment and resume capability.

Tests reading previous step documentation and passing to implementer.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.unit

from tapps_agents.simple_mode.documentation_manager import WorkflowDocumentationManager
from tapps_agents.simple_mode.orchestrators.build_orchestrator import BuildOrchestrator


class TestEnrichImplementerContext:
    """Test _enrich_implementer_context method."""

    @pytest.fixture
    def build_orchestrator(self, tmp_path):
        """Create BuildOrchestrator instance for testing."""
        from tapps_agents.core.config import ProjectConfig

        config = ProjectConfig()
        return BuildOrchestrator(project_root=tmp_path, config=config)

    def test_enrich_context_all_steps(self, build_orchestrator, tmp_path):
        """Test context enrichment when all step files exist."""
        # Setup: Create all step files
        workflow_id = "test-workflow"
        base_dir = tmp_path / "docs" / "workflows" / "simple-mode"
        workflow_dir = base_dir / workflow_id
        workflow_dir.mkdir(parents=True)

        (workflow_dir / "step1-enhanced-prompt.md").write_text(
            "# Step 1\n\nEnhanced prompt content", encoding="utf-8"
        )
        (workflow_dir / "step2-user-stories.md").write_text(
            "# Step 2\n\nUser stories content", encoding="utf-8"
        )
        (workflow_dir / "step3-architecture.md").write_text(
            "# Step 3\n\nArchitecture content", encoding="utf-8"
        )
        (workflow_dir / "step4-design.md").write_text(
            "# Step 4\n\nAPI design content", encoding="utf-8"
        )

        doc_manager = WorkflowDocumentationManager(base_dir=base_dir, workflow_id=workflow_id)

        # Execute: Enrich context
        args = build_orchestrator._enrich_implementer_context(
            workflow_id=workflow_id,
            doc_manager=doc_manager,
            enhanced_prompt="fallback prompt",
        )

        # Assert: Returns dict with all context keys
        assert "specification" in args
        assert "user_stories" in args
        assert "architecture" in args
        assert "api_design" in args
        assert "Enhanced prompt content" in args["specification"]
        assert "User stories content" in args["user_stories"]
        assert "Architecture content" in args["architecture"]
        assert "API design content" in args["api_design"]

    def test_enrich_context_partial_steps(self, build_orchestrator, tmp_path):
        """Test context enrichment when some steps missing."""
        # Setup: Create only step1 and step3
        workflow_id = "test-workflow"
        base_dir = tmp_path / "docs" / "workflows" / "simple-mode"
        workflow_dir = base_dir / workflow_id
        workflow_dir.mkdir(parents=True)

        (workflow_dir / "step1-enhanced-prompt.md").write_text(
            "# Step 1\n\nEnhanced prompt", encoding="utf-8"
        )
        (workflow_dir / "step3-architecture.md").write_text(
            "# Step 3\n\nArchitecture", encoding="utf-8"
        )

        doc_manager = WorkflowDocumentationManager(base_dir=base_dir, workflow_id=workflow_id)

        # Execute: Enrich context
        args = build_orchestrator._enrich_implementer_context(
            workflow_id=workflow_id,
            doc_manager=doc_manager,
            enhanced_prompt="fallback prompt",
        )

        # Assert: Returns available context, missing keys absent
        assert "specification" in args
        assert "architecture" in args
        assert "user_stories" not in args  # Step 2 missing
        assert "api_design" not in args  # Step 4 missing

    def test_enrich_context_no_doc_manager(self, build_orchestrator):
        """Test context enrichment when doc_manager is None."""
        # Setup: doc_manager = None
        # Execute: Enrich context
        args = build_orchestrator._enrich_implementer_context(
            workflow_id="test-workflow",
            doc_manager=None,
            enhanced_prompt="fallback prompt",
        )

        # Assert: Returns only specification (fallback)
        assert args == {"specification": "fallback prompt"}
        assert "user_stories" not in args
        assert "architecture" not in args
        assert "api_design" not in args

    def test_enrich_context_content_truncation(self, build_orchestrator, tmp_path):
        """Test content truncation for large files."""
        # Setup: Create step files with large content (>3000 chars)
        workflow_id = "test-workflow"
        base_dir = tmp_path / "docs" / "workflows" / "simple-mode"
        workflow_dir = base_dir / workflow_id
        workflow_dir.mkdir(parents=True)

        large_content = "# Step 2\n\n" + "x" * 5000  # 5000+ chars
        (workflow_dir / "step2-user-stories.md").write_text(large_content, encoding="utf-8")

        doc_manager = WorkflowDocumentationManager(base_dir=base_dir, workflow_id=workflow_id)

        # Execute: Enrich context
        args = build_orchestrator._enrich_implementer_context(
            workflow_id=workflow_id,
            doc_manager=doc_manager,
            enhanced_prompt="fallback",
        )

        # Assert: Content is truncated to limits
        assert "user_stories" in args
        assert len(args["user_stories"]) <= 3000  # Truncated

    def test_enrich_context_error_handling(self, build_orchestrator, tmp_path):
        """Test error handling in context enrichment."""
        # Setup: Invalid workflow directory
        workflow_id = "test-workflow"
        base_dir = tmp_path / "docs" / "workflows" / "simple-mode"
        doc_manager = WorkflowDocumentationManager(base_dir=base_dir, workflow_id=workflow_id)

        # Execute: Enrich context (should handle errors gracefully)
        args = build_orchestrator._enrich_implementer_context(
            workflow_id=workflow_id,
            doc_manager=doc_manager,
            enhanced_prompt="fallback prompt",
        )

        # Assert: Falls back to base args on error
        assert "specification" in args
        assert args["specification"] == "fallback prompt"


class TestFindLastCompletedStep:
    """Test _find_last_completed_step method."""

    @pytest.fixture
    def build_orchestrator(self, tmp_path):
        """Create BuildOrchestrator instance for testing."""
        from tapps_agents.core.config import ProjectConfig

        config = ProjectConfig()
        return BuildOrchestrator(project_root=tmp_path, config=config)

    def test_find_last_completed_step(self, build_orchestrator, tmp_path):
        """Test finding last completed step."""
        # Setup: Create workflow with steps 1-4
        workflow_id = "test-workflow"
        base_dir = tmp_path / "docs" / "workflows" / "simple-mode"
        workflow_dir = base_dir / workflow_id
        workflow_dir.mkdir(parents=True)

        (workflow_dir / "step1-enhanced-prompt.md").write_text("# Step 1")
        (workflow_dir / "step2-user-stories.md").write_text("# Step 2")
        (workflow_dir / "step3-architecture.md").write_text("# Step 3")
        (workflow_dir / "step4-design.md").write_text("# Step 4")

        # Execute: Find last completed step
        last_step = build_orchestrator._find_last_completed_step(workflow_id)

        # Assert: Returns 4
        assert last_step == 4

    def test_find_last_completed_step_none(self, build_orchestrator, tmp_path):
        """Test finding last step when no steps exist."""
        # Setup: Empty workflow directory
        workflow_id = "test-workflow"
        base_dir = tmp_path / "docs" / "workflows" / "simple-mode"
        base_dir.mkdir(parents=True)

        # Execute: Find last completed step
        last_step = build_orchestrator._find_last_completed_step(workflow_id)

        # Assert: Returns 0
        assert last_step == 0

    def test_find_last_completed_step_gaps(self, build_orchestrator, tmp_path):
        """Test finding last step with gaps in step numbers."""
        # Setup: Create workflow with steps 1, 3, 5 (gaps)
        workflow_id = "test-workflow"
        base_dir = tmp_path / "docs" / "workflows" / "simple-mode"
        workflow_dir = base_dir / workflow_id
        workflow_dir.mkdir(parents=True)

        (workflow_dir / "step1-enhanced-prompt.md").write_text("# Step 1")
        (workflow_dir / "step3-architecture.md").write_text("# Step 3")
        (workflow_dir / "step5-implementation.md").write_text("# Step 5")

        # Execute: Find last completed step
        last_step = build_orchestrator._find_last_completed_step(workflow_id)

        # Assert: Returns 5 (highest step number)
        assert last_step == 5


class TestResume:
    """Test resume method."""

    @pytest.fixture
    def build_orchestrator(self, tmp_path):
        """Create BuildOrchestrator instance for testing."""
        from tapps_agents.core.config import ProjectConfig

        config = ProjectConfig()
        return BuildOrchestrator(project_root=tmp_path, config=config)

    @pytest.mark.asyncio
    async def test_resume_invalid_workflow_id(self, build_orchestrator):
        """Test resume with invalid workflow_id."""
        # Execute & Assert: Raises ValueError
        with pytest.raises(ValueError, match="Invalid workflow_id"):
            await build_orchestrator.resume("test/../workflow")

    @pytest.mark.asyncio
    async def test_resume_workflow_not_found(self, build_orchestrator, tmp_path):
        """Test resume when workflow doesn't exist."""
        # Setup: Non-existent workflow_id
        workflow_id = "non-existent-workflow"

        # Execute & Assert: Raises FileNotFoundError
        with pytest.raises(FileNotFoundError):
            await build_orchestrator.resume(workflow_id)

    @pytest.mark.asyncio
    async def test_resume_auto_detect(self, build_orchestrator, tmp_path):
        """Test resume with auto-detection of last step."""
        # Setup: Create workflow with steps 1-3 completed
        workflow_id = "test-workflow"
        base_dir = tmp_path / "docs" / "workflows" / "simple-mode"
        workflow_dir = base_dir / workflow_id
        workflow_dir.mkdir(parents=True)

        (workflow_dir / "step1-enhanced-prompt.md").write_text(
            "# Step 1\n\nEnhanced prompt", encoding="utf-8"
        )
        (workflow_dir / "step2-user-stories.md").write_text("# Step 2", encoding="utf-8")
        (workflow_dir / "step3-architecture.md").write_text("# Step 3", encoding="utf-8")

        # Mock execute to avoid full workflow execution
        with patch.object(build_orchestrator, "execute", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "workflow_id": workflow_id,
                "steps_executed": ["enhance", "plan", "architect"],
            }

            # Execute: Resume without from_step
            result = await build_orchestrator.resume(workflow_id)

            # Assert: Resumes from step 4 (next after 3)
            assert result["success"] is True
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume_from_specific_step(self, build_orchestrator, tmp_path):
        """Test resume from specific step."""
        # Setup: Create workflow with steps 1-5 completed
        workflow_id = "test-workflow"
        base_dir = tmp_path / "docs" / "workflows" / "simple-mode"
        workflow_dir = base_dir / workflow_id
        workflow_dir.mkdir(parents=True)

        (workflow_dir / "step1-enhanced-prompt.md").write_text("# Step 1", encoding="utf-8")
        (workflow_dir / "step2-user-stories.md").write_text("# Step 2", encoding="utf-8")

        # Mock execute
        with patch.object(build_orchestrator, "execute", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {"success": True, "workflow_id": workflow_id}

            # Execute: Resume from step 3
            result = await build_orchestrator.resume(workflow_id, from_step=3)

            # Assert: Resumes from step 4 (next after 3)
            assert result["success"] is True
            mock_execute.assert_called_once()
