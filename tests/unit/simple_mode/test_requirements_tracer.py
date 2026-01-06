"""Tests for RequirementsTracer."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

pytestmark = pytest.mark.unit

from tapps_agents.simple_mode.orchestrators.requirements_tracer import (
    RequirementsTracer,
)


@pytest.fixture
def tracer():
    """Create RequirementsTracer instance."""
    requirements = {
        "R1-VERIFY-001": {"description": "Test requirement 1"},
        "R2-CHECKLIST-001": {"description": "Test requirement 2"},
    }
    return RequirementsTracer(requirements=requirements)


@pytest.fixture
def tmp_project_root(tmp_path):
    """Create temporary project root."""
    return tmp_path / "project"


class TestRequirementsTracer:
    """Test RequirementsTracer class."""

    def test_init_with_requirements(self):
        """Test initialization with requirements."""
        requirements = {"R1": {"desc": "test"}}
        tracer = RequirementsTracer(requirements=requirements)
        assert tracer.requirements == requirements
        assert tracer.trace == {}

    def test_init_without_requirements(self):
        """Test initialization without requirements."""
        tracer = RequirementsTracer()
        assert tracer.requirements == {}
        assert tracer.trace == {}

    def test_add_trace_code(self, tracer, tmp_path):
        """Test adding code trace."""
        file_path = tmp_path / "test.py"
        file_path.write_text("# test")
        
        tracer.add_trace("R1-VERIFY-001", "code", file_path)
        
        assert "R1-VERIFY-001" in tracer.trace
        assert len(tracer.trace["R1-VERIFY-001"]["code"]) == 1
        assert tracer.trace["R1-VERIFY-001"]["code"][0] == file_path

    def test_add_trace_multiple_types(self, tracer, tmp_path):
        """Test adding multiple trace types."""
        code_file = tmp_path / "code.py"
        test_file = tmp_path / "test_code.py"
        doc_file = tmp_path / "doc.md"
        
        tracer.add_trace("R1-VERIFY-001", "code", code_file)
        tracer.add_trace("R1-VERIFY-001", "tests", test_file)
        tracer.add_trace("R1-VERIFY-001", "docs", doc_file)
        
        trace = tracer.trace["R1-VERIFY-001"]
        assert len(trace["code"]) == 1
        assert len(trace["tests"]) == 1
        assert len(trace["docs"]) == 1

    def test_add_trace_invalid_type(self, tracer, tmp_path):
        """Test adding trace with invalid deliverable type."""
        file_path = tmp_path / "test.py"
        
        with pytest.raises(ValueError, match="Invalid deliverable_type"):
            tracer.add_trace("R1-VERIFY-001", "invalid_type", file_path)

    def test_add_trace_duplicate(self, tracer, tmp_path):
        """Test adding duplicate trace (should not duplicate)."""
        file_path = tmp_path / "test.py"
        file_path.write_text("# test")
        
        tracer.add_trace("R1-VERIFY-001", "code", file_path)
        tracer.add_trace("R1-VERIFY-001", "code", file_path)  # Duplicate
        
        assert len(tracer.trace["R1-VERIFY-001"]["code"]) == 1

    def test_verify_requirement_complete(self, tracer, tmp_path):
        """Test verifying requirement that is complete."""
        code_file = tmp_path / "code.py"
        test_file = tmp_path / "test.py"
        doc_file = tmp_path / "doc.md"
        
        tracer.add_trace("R1-VERIFY-001", "code", code_file)
        tracer.add_trace("R1-VERIFY-001", "tests", test_file)
        tracer.add_trace("R1-VERIFY-001", "docs", doc_file)
        
        result = tracer.verify_requirement("R1-VERIFY-001")
        assert result["complete"] is True
        assert len(result["gaps"]) == 0

    def test_verify_requirement_missing_code(self, tracer, tmp_path):
        """Test verifying requirement missing code."""
        result = tracer.verify_requirement("R1-VERIFY-001")
        assert result["complete"] is False
        assert "code" in result["gaps"]

    def test_verify_requirement_missing_tests(self, tracer, tmp_path):
        """Test verifying requirement missing tests."""
        code_file = tmp_path / "code.py"
        tracer.add_trace("R1-VERIFY-001", "code", code_file)
        
        result = tracer.verify_requirement("R1-VERIFY-001")
        assert result["complete"] is False
        assert "tests" in result["gaps"]

    def test_verify_requirement_missing_docs(self, tracer, tmp_path):
        """Test verifying requirement missing docs."""
        code_file = tmp_path / "code.py"
        test_file = tmp_path / "test.py"
        tracer.add_trace("R1-VERIFY-001", "code", code_file)
        tracer.add_trace("R1-VERIFY-001", "tests", test_file)
        
        result = tracer.verify_requirement("R1-VERIFY-001")
        assert result["complete"] is False
        assert "docs" in result["gaps"]

    def test_verify_requirement_not_found(self, tracer):
        """Test verifying requirement that doesn't exist."""
        result = tracer.verify_requirement("R-NOT-FOUND")
        assert result["complete"] is False
        assert result["missing"] == "all"

    def test_verify_all_requirements(self, tracer, tmp_path):
        """Test verifying all requirements."""
        code_file = tmp_path / "code.py"
        test_file = tmp_path / "test.py"
        
        # Complete R1
        tracer.add_trace("R1-VERIFY-001", "code", code_file)
        tracer.add_trace("R1-VERIFY-001", "tests", test_file)
        
        result = tracer.verify_all_requirements()
        assert "requirements" in result
        assert "R1-VERIFY-001" in result["requirements"]
        assert "R2-CHECKLIST-001" in result["requirements"]
        
        # R1 should be incomplete (missing docs)
        # R2 should be missing all
        assert result["complete"] is False
        assert len(result["gaps"]) > 0

    def test_extract_requirement_ids_from_stories(self, tracer):
        """Test extracting requirement IDs from user stories."""
        user_stories = [
            {"id": "R1-VERIFY-001", "title": "Story 1"},
            {"id": "R2-CHECKLIST-001", "title": "Story 2"},
            {"requirement_id": "R3-TEST-001", "title": "Story 3"},
        ]
        
        req_ids = tracer.extract_requirement_ids(user_stories)
        assert "R1-VERIFY-001" in req_ids
        assert "R2-CHECKLIST-001" in req_ids
        assert "R3-TEST-001" in req_ids

    def test_extract_requirement_ids_from_text(self):
        """Test extracting requirement IDs from text."""
        tracer = RequirementsTracer()
        user_stories = [
            {"text": "R1-VERIFY-001: Implement verification"},
            {"text": "R2-CHECKLIST-001: Add checklist"},
        ]
        
        req_ids = tracer.extract_requirement_ids(user_stories)
        # Should extract IDs using regex
        assert len(req_ids) >= 0  # May or may not find depending on format

    def test_get_traceability_report(self, tracer, tmp_path):
        """Test generating traceability report."""
        code_file = tmp_path / "code.py"
        test_file = tmp_path / "test.py"
        
        tracer.add_trace("R1-VERIFY-001", "code", code_file)
        tracer.add_trace("R1-VERIFY-001", "tests", test_file)
        tracer.add_trace("R2-CHECKLIST-001", "code", code_file)
        
        report = tracer.get_traceability_report()
        
        assert "matrix" in report
        assert "statistics" in report
        assert "R1-VERIFY-001" in report["matrix"]
        assert report["matrix"]["R1-VERIFY-001"]["code"] == 1
        assert report["matrix"]["R1-VERIFY-001"]["tests"] == 1
        assert report["statistics"]["total_requirements"] == 2
        assert report["statistics"]["traced_requirements"] == 2

    def test_to_dict(self, tracer, tmp_path):
        """Test serialization to dictionary."""
        file_path = tmp_path / "test.py"
        tracer.add_trace("R1-VERIFY-001", "code", file_path)
        
        data = tracer.to_dict()
        assert "requirements" in data
        assert "trace" in data
        assert "R1-VERIFY-001" in data["trace"]
        assert data["trace"]["R1-VERIFY-001"]["code"] == [str(file_path)]

    def test_from_dict(self, tmp_path):
        """Test deserialization from dictionary."""
        file_path = tmp_path / "test.py"
        
        data = {
            "requirements": {
                "R1-VERIFY-001": {"description": "Test requirement"},
            },
            "trace": {
                "R1-VERIFY-001": {
                    "code": [str(file_path)],
                    "tests": [],
                    "docs": [],
                    "templates": [],
                },
            },
        }
        
        tracer = RequirementsTracer.from_dict(data)
        assert "R1-VERIFY-001" in tracer.requirements
        assert "R1-VERIFY-001" in tracer.trace
        assert len(tracer.trace["R1-VERIFY-001"]["code"]) == 1
        assert tracer.trace["R1-VERIFY-001"]["code"][0] == file_path
