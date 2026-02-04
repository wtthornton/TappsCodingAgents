"""
Tests for WorkflowDocumentationReader.

Tests reading step documentation and state from .md files.
"""


import pytest

pytestmark = pytest.mark.unit

from tapps_agents.simple_mode.documentation_reader import (
    DocumentationReaderError,
    WorkflowDocumentationReader,
)


class TestWorkflowDocumentationReader:
    """Test WorkflowDocumentationReader class."""

    def test_init_valid(self, tmp_path):
        """Test initialization with valid workflow_id."""
        reader = WorkflowDocumentationReader(
            base_dir=tmp_path, workflow_id="test-workflow-123"
        )
        assert reader.base_dir == tmp_path
        assert reader.workflow_id == "test-workflow-123"

    def test_init_invalid_workflow_id_dot_dot(self, tmp_path):
        """Test initialization with invalid workflow_id containing .."""
        with pytest.raises(ValueError, match="Invalid workflow_id"):
            WorkflowDocumentationReader(base_dir=tmp_path, workflow_id="test/../workflow")

    def test_init_invalid_workflow_id_slash(self, tmp_path):
        """Test initialization with invalid workflow_id containing /"""
        with pytest.raises(ValueError, match="Invalid workflow_id"):
            WorkflowDocumentationReader(base_dir=tmp_path, workflow_id="test/workflow")

    def test_init_empty_workflow_id(self, tmp_path):
        """Test initialization with empty workflow_id."""
        with pytest.raises(ValueError, match="Invalid workflow_id"):
            WorkflowDocumentationReader(base_dir=tmp_path, workflow_id="")

    def test_get_documentation_dir(self, tmp_path):
        """Test getting documentation directory."""
        reader = WorkflowDocumentationReader(
            base_dir=tmp_path, workflow_id="test-workflow"
        )
        doc_dir = reader.get_documentation_dir()
        assert doc_dir == tmp_path / "test-workflow"

    def test_get_step_file_path_with_name(self, tmp_path):
        """Test getting step file path with step name."""
        reader = WorkflowDocumentationReader(
            base_dir=tmp_path, workflow_id="test-workflow"
        )
        file_path = reader.get_step_file_path(1, "enhanced-prompt")
        assert file_path.name == "step1-enhanced-prompt.md"
        assert file_path.parent == tmp_path / "test-workflow"

    def test_get_step_file_path_without_name(self, tmp_path):
        """Test getting step file path without step name."""
        reader = WorkflowDocumentationReader(
            base_dir=tmp_path, workflow_id="test-workflow"
        )
        file_path = reader.get_step_file_path(2)
        assert file_path.name == "step2.md"
        assert file_path.parent == tmp_path / "test-workflow"

    def test_read_step_documentation_success(self, tmp_path):
        """Test reading existing step documentation file."""
        # Setup: Create workflow directory and file
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()
        step_file = workflow_dir / "step1-enhanced-prompt.md"
        expected_content = "# Step 1: Enhanced Prompt\n\nThis is test content."
        step_file.write_text(expected_content, encoding="utf-8")

        # Execute: Read step documentation
        reader = WorkflowDocumentationReader(base_dir=tmp_path, workflow_id="test-workflow")
        content = reader.read_step_documentation(1, "enhanced-prompt")

        # Assert: Content matches expected
        assert content == expected_content

    def test_read_step_documentation_file_not_found(self, tmp_path):
        """Test reading non-existent file returns empty string."""
        # Setup: No file exists
        reader = WorkflowDocumentationReader(base_dir=tmp_path, workflow_id="test-workflow")

        # Execute: Read step documentation
        content = reader.read_step_documentation(1, "enhanced-prompt")

        # Assert: Returns empty string, no exception
        assert content == ""

    def test_read_step_documentation_invalid_encoding(self, tmp_path):
        """Test reading file with invalid encoding raises error."""
        # Setup: Create file with invalid encoding (binary data)
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()
        step_file = workflow_dir / "step1-enhanced-prompt.md"
        step_file.write_bytes(b"\xff\xfe\x00\x00")  # Invalid UTF-8

        reader = WorkflowDocumentationReader(base_dir=tmp_path, workflow_id="test-workflow")

        # Execute & Assert: Raises DocumentationReaderError
        with pytest.raises(DocumentationReaderError):
            reader.read_step_documentation(1, "enhanced-prompt")

    def test_read_step_state_with_frontmatter(self, tmp_path):
        """Test parsing YAML frontmatter from step file."""
        # Setup: Create file with YAML frontmatter
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()
        step_file = workflow_dir / "step1-enhanced-prompt.md"
        content = """---
step_number: 1
step_name: enhanced-prompt
timestamp: "2025-12-31T01:31:15"
agent_output:
  enhanced_prompt: "Test prompt"
  success: true
artifacts: []
success_status: true
---
# Step 1: Enhanced Prompt
This is the markdown content.
"""
        step_file.write_text(content, encoding="utf-8")

        # Execute: Read step state
        reader = WorkflowDocumentationReader(base_dir=tmp_path, workflow_id="test-workflow")
        state = reader.read_step_state(1, "enhanced-prompt")

        # Assert: Returns parsed state dictionary
        assert isinstance(state, dict)
        assert state["step_number"] == 1
        assert state["step_name"] == "enhanced-prompt"
        assert state["timestamp"] == "2025-12-31T01:31:15"
        assert state["agent_output"]["enhanced_prompt"] == "Test prompt"
        assert state["success_status"] is True

    def test_read_step_state_without_frontmatter(self, tmp_path):
        """Test reading file without YAML frontmatter returns empty dict."""
        # Setup: Create file without frontmatter
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()
        step_file = workflow_dir / "step1-enhanced-prompt.md"
        step_file.write_text("# Step 1\n\nNo frontmatter here.", encoding="utf-8")

        # Execute: Read step state
        reader = WorkflowDocumentationReader(base_dir=tmp_path, workflow_id="test-workflow")
        state = reader.read_step_state(1, "enhanced-prompt")

        # Assert: Returns empty dict
        assert state == {}

    def test_read_step_state_invalid_yaml(self, tmp_path):
        """Test handling invalid YAML frontmatter."""
        # Setup: Create file with invalid YAML
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()
        step_file = workflow_dir / "step1-enhanced-prompt.md"
        content = """---
invalid: yaml: content: [unclosed
---
# Step 1
Content here.
"""
        step_file.write_text(content, encoding="utf-8")

        # Execute: Read step state
        reader = WorkflowDocumentationReader(base_dir=tmp_path, workflow_id="test-workflow")
        state = reader.read_step_state(1, "enhanced-prompt")

        # Assert: Returns empty dict, logs warning (no exception raised)
        assert state == {}

    def test_read_step_state_file_not_found(self, tmp_path):
        """Test reading state from non-existent file returns empty dict."""
        reader = WorkflowDocumentationReader(base_dir=tmp_path, workflow_id="test-workflow")
        state = reader.read_step_state(1, "enhanced-prompt")
        assert state == {}

    def test_validate_step_documentation_all_present(self, tmp_path):
        """Test validation when all required sections exist."""
        # Setup: Create file with all required sections
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()
        step_file = workflow_dir / "step1-enhanced-prompt.md"
        content = """# Step 1

## Requirements Analysis
Some requirements here.

## Architecture Guidance
Some architecture here.
"""
        step_file.write_text(content, encoding="utf-8")

        # Execute: Validate
        reader = WorkflowDocumentationReader(base_dir=tmp_path, workflow_id="test-workflow")
        validation = reader.validate_step_documentation(
            1, "enhanced-prompt", ["Requirements Analysis", "Architecture Guidance"]
        )

        # Assert: All sections return True
        assert validation["Requirements Analysis"] is True
        assert validation["Architecture Guidance"] is True

    def test_validate_step_documentation_missing(self, tmp_path):
        """Test validation when sections are missing."""
        # Setup: Create file without required sections
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()
        step_file = workflow_dir / "step1-enhanced-prompt.md"
        step_file.write_text("# Step 1\n\nNo sections here.", encoding="utf-8")

        # Execute: Validate
        reader = WorkflowDocumentationReader(base_dir=tmp_path, workflow_id="test-workflow")
        validation = reader.validate_step_documentation(
            1, "enhanced-prompt", ["Requirements Analysis", "Architecture Guidance"]
        )

        # Assert: Missing sections return False
        assert validation["Requirements Analysis"] is False
        assert validation["Architecture Guidance"] is False

    def test_validate_step_documentation_file_not_found(self, tmp_path):
        """Test validation when file doesn't exist."""
        reader = WorkflowDocumentationReader(base_dir=tmp_path, workflow_id="test-workflow")
        validation = reader.validate_step_documentation(
            1, "enhanced-prompt", ["Requirements Analysis"]
        )
        assert validation["Requirements Analysis"] is False

    def test_validate_step_documentation_case_insensitive(self, tmp_path):
        """Test validation is case-insensitive for section names."""
        # Setup: Create file with lowercase section
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()
        step_file = workflow_dir / "step1-enhanced-prompt.md"
        content = """# Step 1

## requirements analysis
Some content here.
"""
        step_file.write_text(content, encoding="utf-8")

        # Execute: Validate with capitalized section name
        reader = WorkflowDocumentationReader(base_dir=tmp_path, workflow_id="test-workflow")
        validation = reader.validate_step_documentation(
            1, "enhanced-prompt", ["Requirements Analysis"]
        )

        # Assert: Case-insensitive matching works
        assert validation["Requirements Analysis"] is True


class TestDocumentationReaderError:
    """Test DocumentationReaderError exception."""

    def test_init(self):
        """Test exception initialization."""
        error = DocumentationReaderError("Test error message")
        assert str(error) == "Test error message"
