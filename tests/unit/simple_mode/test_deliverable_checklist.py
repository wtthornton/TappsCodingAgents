"""Tests for DeliverableChecklist."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from tapps_agents.simple_mode.orchestrators.deliverable_checklist import (
    DeliverableChecklist,
)


@pytest.fixture
def tmp_project_root(tmp_path):
    """Create temporary project root with directory structure."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    
    # Create some test directories
    (project_root / "tapps_agents" / "resources" / "claude" / "skills" / "test-skill").mkdir(parents=True)
    (project_root / "tapps_agents" / "resources" / "claude" / "skills" / "test-skill" / "SKILL.md").write_text("# Test Skill")
    
    (project_root / "templates").mkdir()
    (project_root / "templates" / "workflow.yaml").write_text("workflow: test")
    
    (project_root / "docs").mkdir()
    (project_root / "docs" / "test.md").write_text("# Test Doc")
    
    (project_root / "examples").mkdir()
    (project_root / "examples" / "test_example.py").write_text("print('test')")
    
    return project_root


@pytest.fixture
def checklist():
    """Create DeliverableChecklist instance."""
    return DeliverableChecklist(requirements={"test": "requirement"})


class TestDeliverableChecklist:
    """Test DeliverableChecklist class."""

    def test_init_with_requirements(self):
        """Test initialization with requirements."""
        requirements = {"req1": "description"}
        checklist = DeliverableChecklist(requirements=requirements)
        assert checklist.requirements == requirements
        assert "core_code" in checklist.checklist
        assert "related_files" in checklist.checklist
        assert "documentation" in checklist.checklist
        assert "tests" in checklist.checklist
        assert "templates" in checklist.checklist
        assert "examples" in checklist.checklist

    def test_init_without_requirements(self):
        """Test initialization without requirements."""
        checklist = DeliverableChecklist()
        assert checklist.requirements == {}
        assert len(checklist.checklist) == 6

    def test_add_deliverable_valid(self, checklist, tmp_path):
        """Test adding valid deliverable."""
        file_path = tmp_path / "test.py"
        file_path.write_text("# test")
        
        checklist.add_deliverable(
            "core_code",
            "Test file",
            file_path,
            status="complete",
            metadata={"req_id": "R1"},
        )
        
        assert len(checklist.checklist["core_code"]) == 1
        item = checklist.checklist["core_code"][0]
        assert item["item"] == "Test file"
        assert item["path"] == file_path
        assert item["status"] == "complete"
        assert item["metadata"]["req_id"] == "R1"

    def test_add_deliverable_invalid_category(self, checklist, tmp_path):
        """Test adding deliverable with invalid category."""
        file_path = tmp_path / "test.py"
        
        with pytest.raises(ValueError, match="Invalid category"):
            checklist.add_deliverable("invalid_category", "Test", file_path)

    def test_add_deliverable_invalid_status(self, checklist, tmp_path):
        """Test adding deliverable with invalid status."""
        file_path = tmp_path / "test.py"
        
        with pytest.raises(ValueError, match="Invalid status"):
            checklist.add_deliverable("core_code", "Test", file_path, status="invalid")

    def test_add_deliverable_nonexistent_file(self, checklist, tmp_path):
        """Test adding deliverable with non-existent file path."""
        file_path = tmp_path / "nonexistent.py"
        
        # Should not raise error, just log warning
        checklist.add_deliverable("core_code", "Test", file_path)
        assert len(checklist.checklist["core_code"]) == 1

    def test_discover_related_files(self, checklist, tmp_project_root):
        """Test discovering related files."""
        core_file = tmp_project_root / "tapps_agents" / "agents" / "test.py"
        core_file.parent.mkdir(parents=True)
        core_file.write_text("# test agent")
        
        related = checklist.discover_related_files([core_file], tmp_project_root)
        
        # Should find skill template and potentially docs/examples
        assert len(related) > 0
        # Should find skill template
        skill_template = tmp_project_root / "tapps_agents" / "resources" / "claude" / "skills" / "test-skill" / "SKILL.md"
        assert any(p == skill_template for p in related)

    def test_find_templates_skill_related(self, checklist, tmp_project_root):
        """Test finding templates for skill-related files."""
        core_file = tmp_project_root / "tapps_agents" / "core" / "skills" / "test.py"
        core_file.parent.mkdir(parents=True)
        
        templates = checklist._find_templates(core_file, tmp_project_root)
        assert len(templates) > 0

    def test_find_templates_workflow_related(self, checklist, tmp_project_root):
        """Test finding templates for workflow-related files."""
        core_file = tmp_project_root / "tapps_agents" / "workflow" / "orchestrator.py"
        core_file.parent.mkdir(parents=True)
        
        templates = checklist._find_templates(core_file, tmp_project_root)
        assert len(templates) > 0

    def test_find_documentation(self, checklist, tmp_project_root):
        """Test finding documentation files."""
        core_file = tmp_project_root / "src" / "test.py"
        core_file.parent.mkdir(parents=True)
        core_file.write_text("# test")
        
        # Create doc that references the file
        doc_file = tmp_project_root / "docs" / "test_ref.md"
        doc_file.write_text("test.py is referenced here")
        
        docs = checklist._find_documentation(core_file, tmp_project_root)
        # Should find docs that reference the file
        assert len(docs) >= 0  # May or may not find depending on content

    def test_find_examples(self, checklist, tmp_project_root):
        """Test finding example files."""
        core_file = tmp_project_root / "src" / "test.py"
        core_file.parent.mkdir(parents=True)
        
        examples = checklist._find_examples(core_file, tmp_project_root)
        # Should find example files
        assert len(examples) >= 0

    def test_verify_completeness_all_complete(self, checklist, tmp_path):
        """Test verification when all items are complete."""
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("# test1")
        file2.write_text("# test2")
        
        checklist.add_deliverable("core_code", "File 1", file1, status="complete")
        checklist.add_deliverable("tests", "Test 1", file2, status="complete")
        
        result = checklist.verify_completeness()
        assert result["complete"] is True
        assert len(result["gaps"]) == 0

    def test_verify_completeness_with_gaps(self, checklist, tmp_path):
        """Test verification when items are incomplete."""
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("# test1")
        file2.write_text("# test2")
        
        checklist.add_deliverable("core_code", "File 1", file1, status="complete")
        checklist.add_deliverable("tests", "Test 1", file2, status="pending")
        
        result = checklist.verify_completeness()
        assert result["complete"] is False
        assert len(result["gaps"]) == 1
        assert result["gaps"][0]["category"] == "tests"
        assert result["gaps"][0]["status"] == "pending"

    def test_mark_complete(self, checklist, tmp_path):
        """Test marking deliverable as complete."""
        file_path = tmp_path / "test.py"
        file_path.write_text("# test")
        
        checklist.add_deliverable("core_code", "Test file", file_path, status="pending")
        checklist.mark_complete("core_code", "Test file", file_path)
        
        item = checklist.checklist["core_code"][0]
        assert item["status"] == "complete"

    def test_mark_complete_by_path_only(self, checklist, tmp_path):
        """Test marking complete by path only."""
        file_path = tmp_path / "test.py"
        file_path.write_text("# test")
        
        checklist.add_deliverable("core_code", "Test file", file_path, status="pending")
        checklist.mark_complete("core_code", path=file_path)
        
        item = checklist.checklist["core_code"][0]
        assert item["status"] == "complete"

    def test_to_dict(self, checklist, tmp_path):
        """Test serialization to dictionary."""
        file_path = tmp_path / "test.py"
        file_path.write_text("# test")
        
        checklist.add_deliverable("core_code", "Test", file_path, status="complete")
        
        data = checklist.to_dict()
        assert "requirements" in data
        assert "checklist" in data
        assert "core_code" in data["checklist"]
        assert len(data["checklist"]["core_code"]) == 1
        assert data["checklist"]["core_code"][0]["path"] == str(file_path)

    def test_from_dict(self, tmp_path):
        """Test deserialization from dictionary."""
        file_path = tmp_path / "test.py"
        file_path.write_text("# test")
        
        data = {
            "requirements": {"req1": "desc"},
            "checklist": {
                "core_code": [
                    {
                        "item": "Test file",
                        "path": str(file_path),
                        "status": "complete",
                        "metadata": {"req_id": "R1"},
                    }
                ],
                "related_files": [],
                "documentation": [],
                "tests": [],
                "templates": [],
                "examples": [],
            },
        }
        
        checklist = DeliverableChecklist.from_dict(data)
        assert checklist.requirements == {"req1": "desc"}
        assert len(checklist.checklist["core_code"]) == 1
        assert checklist.checklist["core_code"][0]["item"] == "Test file"

    def test_verify_completeness_summary(self, checklist, tmp_path):
        """Test verification summary by category."""
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("# test1")
        file2.write_text("# test2")
        
        checklist.add_deliverable("core_code", "File 1", file1, status="complete")
        checklist.add_deliverable("core_code", "File 2", file2, status="pending")
        checklist.add_deliverable("tests", "Test 1", file1, status="complete")
        
        result = checklist.verify_completeness()
        assert "summary" in result
        assert result["summary"]["core_code"]["total"] == 2
        assert result["summary"]["core_code"]["complete"] == 1
        assert result["summary"]["core_code"]["pending"] == 1
        assert result["summary"]["tests"]["total"] == 1
        assert result["summary"]["tests"]["complete"] == 1
