"""
Tests for Cursor Rules Generator.

Epic 8: Automated Documentation Generation
"""


import pytest

from tapps_agents.workflow.rules_generator import CursorRulesGenerator

pytestmark = pytest.mark.unit


class TestCursorRulesGenerator:
    """Test CursorRulesGenerator functionality."""

    def test_generator_initialization(self, tmp_path):
        """Test generator can be initialized."""
        generator = CursorRulesGenerator(project_root=tmp_path)
        assert generator.project_root == tmp_path

    def test_find_workflow_files_project_presets(self, tmp_path):
        """Test finding workflow files in project presets."""
        # Create workflow presets directory
        presets_dir = tmp_path / "workflows" / "presets"
        presets_dir.mkdir(parents=True)

        # Create a test workflow file
        workflow_file = presets_dir / "test-workflow.yaml"
        workflow_file.write_text(
            """workflow:
  id: test
  name: Test Workflow
  description: Test description
  version: 1.0.0
  type: greenfield
  steps:
    - id: step1
      agent: analyst
      action: gather_requirements
""",
            encoding="utf-8",
        )

        generator = CursorRulesGenerator(project_root=tmp_path)
        files = generator.find_workflow_files()

        assert len(files) > 0
        assert any("test-workflow.yaml" in str(f[0]) for f in files)

    def test_extract_quality_gates(self, tmp_path):
        """Test quality gate extraction from workflow."""
        from tapps_agents.workflow.models import (
            Workflow,
            WorkflowSettings,
            WorkflowStep,
            WorkflowType,
        )

        workflow = Workflow(
            id="test",
            name="Test",
            description="Test",
            version="1.0.0",
            type=WorkflowType.GREENFIELD,
            settings=WorkflowSettings(),
            steps=[
                WorkflowStep(
                    id="review",
                    agent="reviewer",
                    action="review_code",
                    scoring={
                        "enabled": True,
                        "thresholds": {
                            "overall_min": 70,
                            "security_min": 7.0,
                            "maintainability_min": 7.5,
                        },
                    },
                )
            ],
        )

        generator = CursorRulesGenerator(project_root=tmp_path)
        gates = generator.extract_quality_gates(workflow)

        assert "overall" in gates
        assert gates["overall"] == 70
        assert "security" in gates
        assert gates["security"] == 7.0
        assert "maintainability" in gates
        assert gates["maintainability"] == 7.5

    def test_get_workflow_aliases(self, tmp_path):
        """Test workflow alias mapping."""
        generator = CursorRulesGenerator(project_root=tmp_path)

        assert generator.get_workflow_aliases("full-sdlc") == ["full", "enterprise"]
        assert generator.get_workflow_aliases("rapid-dev") == ["rapid", "feature"]
        assert generator.get_workflow_aliases("unknown") == []

    def test_generate_markdown(self, tmp_path):
        """Test markdown generation from workflow."""
        # Create a simple workflow file
        presets_dir = tmp_path / "workflows" / "presets"
        presets_dir.mkdir(parents=True)

        workflow_file = presets_dir / "test.yaml"
        workflow_file.write_text(
            """workflow:
  id: test
  name: Test Workflow
  description: Test description
  version: 1.0.0
  type: greenfield
  steps:
    - id: step1
      agent: analyst
      action: gather_requirements
"""
        )

        generator = CursorRulesGenerator(project_root=tmp_path)
        content = generator.generate()

        assert "# Workflow Presets" in content
        assert "Test Workflow" in content
        assert "analyst" in content.lower()

    def test_write_file(self, tmp_path):
        """Test writing generated markdown to file."""
        # Create a simple workflow file
        presets_dir = tmp_path / "workflows" / "presets"
        presets_dir.mkdir(parents=True)

        workflow_file = presets_dir / "test.yaml"
        workflow_file.write_text(
            """workflow:
  id: test
  name: Test Workflow
  description: Test description
  version: 1.0.0
  type: greenfield
  steps:
    - id: step1
      agent: analyst
      action: gather_requirements
"""
        )

        generator = CursorRulesGenerator(project_root=tmp_path)
        output_path = tmp_path / ".cursor" / "rules" / "workflow-presets.mdc"
        result_path = generator.write(output_path=output_path, backup=False)

        assert result_path == output_path
        assert output_path.exists()
        assert output_path.read_text(encoding="utf-8").startswith("# Workflow Presets")

    def test_write_backup_existing(self, tmp_path):
        """Test that existing file is backed up."""
        # Create a simple workflow file
        presets_dir = tmp_path / "workflows" / "presets"
        presets_dir.mkdir(parents=True)

        workflow_file = presets_dir / "test.yaml"
        workflow_file.write_text(
            """workflow:
  id: test
  name: Test Workflow
  description: Test description
  version: 1.0.0
  type: greenfield
  steps:
    - id: step1
      agent: analyst
      action: gather_requirements
""",
            encoding="utf-8",
        )

        generator = CursorRulesGenerator(project_root=tmp_path)
        output_path = tmp_path / ".cursor" / "rules" / "workflow-presets.mdc"
        output_path.parent.mkdir(parents=True)

        # Create existing file
        output_path.write_text("Old content", encoding="utf-8")

        # Generate with backup
        generator.write(output_path=output_path, backup=True)

        # Check backup exists
        backup_path = output_path.with_suffix(".mdc.backup")
        assert backup_path.exists()
        assert backup_path.read_text(encoding="utf-8") == "Old content"

        # Check new content was written
        assert output_path.exists()
        assert output_path.read_text(encoding="utf-8") != "Old content"

    def test_generate_no_workflows_raises_error(self, tmp_path, monkeypatch):
        """Test that generate raises ValueError when no workflows found."""
        generator = CursorRulesGenerator(project_root=tmp_path)

        # Mock find_workflow_files to return empty list
        def mock_find_files():
            return []

        monkeypatch.setattr(generator, "find_workflow_files", mock_find_files)

        with pytest.raises(ValueError, match="No workflow YAML files found"):
            generator.generate()

    def test_write_empty_content_raises_error(self, tmp_path, monkeypatch):
        """Test that write raises ValueError when generated content is empty."""
        generator = CursorRulesGenerator(project_root=tmp_path)
        output_path = tmp_path / ".cursor" / "rules" / "workflow-presets.mdc"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Mock generate to return empty content
        def mock_generate():
            return ""

        monkeypatch.setattr(generator, "generate", mock_generate)

        with pytest.raises(ValueError, match="Generated content is empty"):
            generator.write(output_path=output_path, backup=False)

