"""
Tests for WorkflowDocumentationManager extensions.

Tests state serialization and workflow summarization.
"""

import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

from tapps_agents.simple_mode.documentation_manager import (
    DocumentationError,
    WorkflowDocumentationManager,
)


class TestSaveStepState:
    """Test save_step_state method."""

    def test_save_step_state_with_yaml(self, tmp_path):
        """Test saving state with YAML frontmatter."""
        # Setup: State dict and content
        doc_manager = WorkflowDocumentationManager(
            base_dir=tmp_path, workflow_id="test-workflow"
        )
        state = {
            "step_number": 1,
            "step_name": "enhanced-prompt",
            "timestamp": "2025-12-31T01:31:15",
            "agent_output": {"enhanced_prompt": "Test prompt"},
            "artifacts": [],
            "success_status": True,
        }
        content = "# Step 1: Enhanced Prompt\n\nThis is the content."

        # Execute: Save step state
        file_path = doc_manager.save_step_state(1, state, content, "enhanced-prompt")

        # Assert: File created with YAML frontmatter + content
        assert file_path.exists()
        file_content = file_path.read_text(encoding="utf-8")
        assert "---" in file_content  # YAML frontmatter marker
        assert "step_number: 1" in file_content
        assert "# Step 1: Enhanced Prompt" in file_content
        assert "This is the content." in file_content

    def test_save_step_state_without_pyyaml(self, tmp_path, monkeypatch):
        """Test saving state when PyYAML not available."""
        # Setup: Mock PyYAML not available
        import sys
        if "yaml" in sys.modules:
            monkeypatch.setattr("tapps_agents.simple_mode.documentation_manager.yaml", None)

        doc_manager = WorkflowDocumentationManager(
            base_dir=tmp_path, workflow_id="test-workflow"
        )
        state = {"step_number": 1}
        content = "# Step 1\n\nContent."

        # Execute: Save step state
        file_path = doc_manager.save_step_state(1, state, content, "enhanced-prompt")

        # Assert: Falls back to save_step_documentation, no error
        assert file_path.exists()
        # Should still have content (fallback behavior)
        file_content = file_path.read_text(encoding="utf-8")
        assert "# Step 1" in file_content

    def test_save_step_state_creates_directory(self, tmp_path):
        """Test that save_step_state creates directory if needed."""
        doc_manager = WorkflowDocumentationManager(
            base_dir=tmp_path, workflow_id="test-workflow"
        )
        state = {"step_number": 1}
        content = "# Step 1\n\nContent."

        # Execute: Save step state (directory doesn't exist yet)
        file_path = doc_manager.save_step_state(1, state, content)

        # Assert: Directory and file created
        assert file_path.exists()
        assert file_path.parent.exists()

    def test_save_step_state_serialization_error(self, tmp_path, monkeypatch):
        """Test handling of YAML serialization errors."""
        # Setup: Mock yaml.dump to raise exception
        import yaml
        original_dump = yaml.dump

        def failing_dump(*args, **kwargs):
            raise Exception("YAML serialization failed")

        monkeypatch.setattr(yaml, "dump", failing_dump)

        doc_manager = WorkflowDocumentationManager(
            base_dir=tmp_path, workflow_id="test-workflow"
        )
        state = {"step_number": 1}
        content = "# Step 1\n\nContent."

        # Execute & Assert: Raises DocumentationError
        with pytest.raises(DocumentationError, match="Failed to serialize state"):
            doc_manager.save_step_state(1, state, content)


class TestCreateWorkflowSummary:
    """Test create_workflow_summary method."""

    def test_create_workflow_summary(self, tmp_path):
        """Test workflow summary creation."""
        # Setup: Create workflow with multiple steps
        doc_manager = WorkflowDocumentationManager(
            base_dir=tmp_path, workflow_id="test-workflow"
        )
        workflow_dir = doc_manager.get_documentation_dir()
        workflow_dir.mkdir(parents=True)

        # Create step files
        (workflow_dir / "step1-enhanced-prompt.md").write_text("# Step 1\n\nContent.")
        (workflow_dir / "step2-user-stories.md").write_text("# Step 2\n\n## Key Decisions\n\n- Decision 1")
        (workflow_dir / "step3-architecture.md").write_text("# Step 3\n\nFile: `src/file.py`")

        # Execute: Create summary
        summary_path = doc_manager.create_workflow_summary()

        # Assert: Summary file created with correct content
        assert summary_path.exists()
        summary_content = summary_path.read_text(encoding="utf-8")
        assert "test-workflow" in summary_content
        assert "Step 1" in summary_content
        assert "Step 2" in summary_content
        assert "Step 3" in summary_content
        assert "step1-enhanced-prompt.md" in summary_content

    def test_create_workflow_summary_no_steps(self, tmp_path):
        """Test summary creation when no steps exist."""
        doc_manager = WorkflowDocumentationManager(
            base_dir=tmp_path, workflow_id="test-workflow"
        )

        # Execute: Create summary
        summary_path = doc_manager.create_workflow_summary()

        # Assert: Summary created with "No steps completed" message
        assert summary_path.exists()
        summary_content = summary_path.read_text(encoding="utf-8")
        assert "No steps completed yet" in summary_content


class TestGetCompletedSteps:
    """Test _get_completed_steps method."""

    def test_get_completed_steps(self, tmp_path):
        """Test finding completed steps."""
        # Setup: Create workflow directory with step files
        doc_manager = WorkflowDocumentationManager(
            base_dir=tmp_path, workflow_id="test-workflow"
        )
        workflow_dir = doc_manager.get_documentation_dir()
        workflow_dir.mkdir(parents=True)

        # Create step files
        (workflow_dir / "step1-enhanced-prompt.md").write_text("# Step 1")
        (workflow_dir / "step2-user-stories.md").write_text("# Step 2")
        (workflow_dir / "step4-design.md").write_text("# Step 4")
        (workflow_dir / "workflow-summary.md").write_text("# Summary")  # Should be ignored

        # Execute: Get completed steps
        steps = doc_manager._get_completed_steps()

        # Assert: Returns correct step numbers
        assert 1 in steps
        assert 2 in steps
        assert 4 in steps
        assert 3 not in steps  # Step 3 doesn't exist
        assert len(steps) == 3

    def test_get_completed_steps_no_directory(self, tmp_path):
        """Test getting steps when directory doesn't exist."""
        doc_manager = WorkflowDocumentationManager(
            base_dir=tmp_path, workflow_id="test-workflow"
        )

        # Execute: Get completed steps
        steps = doc_manager._get_completed_steps()

        # Assert: Returns empty list
        assert steps == []


class TestExtractKeyDecisions:
    """Test _extract_key_decisions method."""

    def test_extract_key_decisions(self, tmp_path):
        """Test key decision extraction."""
        # Setup: Create step files with decision sections
        doc_manager = WorkflowDocumentationManager(
            base_dir=tmp_path, workflow_id="test-workflow"
        )
        workflow_dir = doc_manager.get_documentation_dir()
        workflow_dir.mkdir(parents=True)

        (workflow_dir / "step1-enhanced-prompt.md").write_text(
            "# Step 1\n\n## Key Decisions\n\n- Decision 1\n- Decision 2"
        )
        (workflow_dir / "step2-user-stories.md").write_text(
            "# Step 2\n\n## Decision\n\n- Decision 3"
        )

        # Execute: Extract decisions
        decisions = doc_manager._extract_key_decisions()

        # Assert: Returns list of decisions
        assert len(decisions) > 0
        assert any("Decision 1" in d or "Decision 2" in d or "Decision 3" in d for d in decisions)

    def test_extract_key_decisions_no_decisions(self, tmp_path):
        """Test extraction when no decisions exist."""
        doc_manager = WorkflowDocumentationManager(
            base_dir=tmp_path, workflow_id="test-workflow"
        )
        workflow_dir = doc_manager.get_documentation_dir()
        workflow_dir.mkdir(parents=True)

        (workflow_dir / "step1-enhanced-prompt.md").write_text("# Step 1\n\nNo decisions here.")

        # Execute: Extract decisions
        decisions = doc_manager._extract_key_decisions()

        # Assert: Returns empty list
        assert decisions == []


class TestListArtifacts:
    """Test _list_artifacts method."""

    def test_list_artifacts(self, tmp_path):
        """Test artifact listing."""
        # Setup: Create step files mentioning artifacts
        doc_manager = WorkflowDocumentationManager(
            base_dir=tmp_path, workflow_id="test-workflow"
        )
        workflow_dir = doc_manager.get_documentation_dir()
        workflow_dir.mkdir(parents=True)

        (workflow_dir / "step1-enhanced-prompt.md").write_text(
            "# Step 1\n\nCreated `src/file.py` and `tests/test_file.py`"
        )
        (workflow_dir / "step2-user-stories.md").write_text(
            "# Step 2\n\nUpdated `config.yaml`"
        )

        # Execute: List artifacts
        artifacts = doc_manager._list_artifacts()

        # Assert: Returns list of artifact paths
        assert len(artifacts) > 0
        assert any("file.py" in a or "test_file.py" in a or "config.yaml" in a for a in artifacts)

    def test_list_artifacts_no_artifacts(self, tmp_path):
        """Test listing when no artifacts mentioned."""
        doc_manager = WorkflowDocumentationManager(
            base_dir=tmp_path, workflow_id="test-workflow"
        )
        workflow_dir = doc_manager.get_documentation_dir()
        workflow_dir.mkdir(parents=True)

        (workflow_dir / "step1-enhanced-prompt.md").write_text("# Step 1\n\nNo artifacts here.")

        # Execute: List artifacts
        artifacts = doc_manager._list_artifacts()

        # Assert: Returns empty list
        assert artifacts == []
