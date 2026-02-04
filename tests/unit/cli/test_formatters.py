"""
Unit tests for CLI formatters module.

Tests JSON, Markdown, and HTML output formatting functions.
"""

import json

import pytest

from tapps_agents.cli.formatters import format_html, format_json, format_markdown

pytestmark = pytest.mark.unit


class TestFormatJSON:
    """Tests for format_json function."""

    def test_format_json_dict(self):
        """Test format_json with dictionary."""
        data = {
            "file": "test.py",
            "scoring": {
                "overall_score": 85.0,
                "complexity_score": 2.0,
                "security_score": 10.0,
            },
        }
        result = format_json(data)
        
        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed == data
        assert "test.py" in result

    def test_format_json_list(self):
        """Test format_json with list of dictionaries."""
        data = [
            {"file": "file1.py", "scoring": {"overall_score": 85.0}},
            {"file": "file2.py", "scoring": {"overall_score": 90.0}},
        ]
        result = format_json(data)
        
        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed == data
        assert len(parsed) == 2

    def test_format_json_custom_indent(self):
        """Test format_json with custom indentation."""
        data = {"key": "value"}
        result = format_json(data, indent=4)
        
        # Should have 4-space indentation
        lines = result.split("\n")
        assert any("    " in line for line in lines if line.strip())


class TestFormatMarkdown:
    """Tests for format_markdown function."""

    def test_format_markdown_single_file(self):
        """Test format_markdown with single file result."""
        data = {
            "file": "test.py",
            "scoring": {
                "overall_score": 85.0,
                "complexity_score": 2.0,
                "security_score": 10.0,
                "maintainability_score": 9.0,
            },
        }
        result = format_markdown(data)
        
        assert "# Results for: test.py" in result
        assert "## Scores" in result
        assert "**Overall**: 85.0/100" in result
        assert "**Complexity**: 2.0/10" in result
        assert "**Security**: 10.0/10" in result

    def test_format_markdown_batch(self):
        """Test format_markdown with batch results."""
        data = [
            {"file": "file1.py", "scoring": {"overall_score": 85.0}},
            {"file": "file2.py", "scoring": {"overall_score": 90.0}},
        ]
        result = format_markdown(data)
        
        assert "# Batch Results" in result
        assert "Total files: 2" in result
        assert "## File 1: file1.py" in result
        assert "## File 2: file2.py" in result

    def test_format_markdown_with_error(self):
        """Test format_markdown with error in result."""
        data = {
            "file": "test.py",
            "error": "File not found",
        }
        result = format_markdown(data)
        
        assert "## Error" in result
        assert "File not found" in result

    def test_format_markdown_batch_with_errors(self):
        """Test format_markdown with batch results containing errors."""
        data = [
            {"file": "file1.py", "scoring": {"overall_score": 85.0}},
            {"file": "file2.py", "error": "Processing failed"},
        ]
        result = format_markdown(data)
        
        assert "# Batch Results" in result
        assert "**Error**: Processing failed" in result


class TestFormatHTML:
    """Tests for format_html function."""

    def test_format_html_single_file(self):
        """Test format_html with single file result."""
        data = {
            "file": "test.py",
            "scoring": {
                "overall_score": 85.0,
                "complexity_score": 2.0,
                "security_score": 10.0,
                "maintainability_score": 9.0,
            },
        }
        result = format_html(data)
        
        assert "<!DOCTYPE html>" in result
        assert "<html>" in result
        assert "test.py" in result
        assert "85.0" in result
        assert "score-card" in result

    def test_format_html_batch(self):
        """Test format_html with batch results."""
        data = [
            {"file": "file1.py", "scoring": {"overall_score": 85.0, "complexity_score": 2.0, "security_score": 10.0, "maintainability_score": 9.0}},
            {"file": "file2.py", "scoring": {"overall_score": 90.0, "complexity_score": 1.5, "security_score": 10.0, "maintainability_score": 9.5}},
        ]
        result = format_html(data)
        
        assert "<!DOCTYPE html>" in result
        assert "<table>" in result
        assert "file1.py" in result
        assert "file2.py" in result
        assert "85.0" in result
        assert "90.0" in result

    def test_format_html_custom_title(self):
        """Test format_html with custom title."""
        data = {"file": "test.py", "scoring": {"overall_score": 85.0}}
        result = format_html(data, title="Custom Report")
        
        assert "<title>Custom Report</title>" in result
        assert "<h1>Custom Report</h1>" in result

    def test_format_html_with_error(self):
        """Test format_html with error in result."""
        data = {
            "file": "test.py",
            "error": "File not found",
        }
        result = format_html(data)
        
        assert "File not found" in result
        assert "error" in result.lower()

    def test_format_html_batch_with_errors(self):
        """Test format_html with batch results containing errors."""
        data = [
            {"file": "file1.py", "scoring": {"overall_score": 85.0, "complexity_score": 2.0, "security_score": 10.0, "maintainability_score": 9.0}},
            {"file": "file2.py", "error": "Processing failed"},
        ]
        result = format_html(data)
        
        assert "<table>" in result
        assert "Processing failed" in result
        assert "error" in result.lower()

    def test_format_html_styling(self):
        """Test format_html includes CSS styling."""
        data = {"file": "test.py", "scoring": {"overall_score": 85.0}}
        result = format_html(data)
        
        assert "<style>" in result
        assert "font-family" in result
        assert "background-color" in result
        assert ".score-card" in result

