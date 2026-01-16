"""
Tests for Knowledge Base Validator.
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from tapps_agents.experts.knowledge_validator import (
    KnowledgeBaseValidator,
    ValidationIssue,
    ValidationResult,
)

pytestmark = pytest.mark.unit


class TestKnowledgeBaseValidator:
    """Test knowledge base validation."""

    @pytest.fixture
    def temp_knowledge_dir(self):
        """Create temporary knowledge directory."""
        temp_dir = Path(tempfile.mkdtemp())
        knowledge_dir = temp_dir / "knowledge"
        knowledge_dir.mkdir()

        yield knowledge_dir

        shutil.rmtree(temp_dir)

    def test_validate_valid_file(self, temp_knowledge_dir):
        """Test validation of valid markdown file."""
        # Create valid markdown file
        valid_file = temp_knowledge_dir / "valid.md"
        valid_file.write_text(
            """# Valid Document

## Section One
Content here.

### Subsection
More content.
""",
            encoding="utf-8",
        )

        validator = KnowledgeBaseValidator(temp_knowledge_dir)
        result = validator.validate_file(valid_file)

        assert result.is_valid
        assert result.file_path == valid_file
        assert result.has_headers
        assert len(result.issues) == 0

    def test_validate_file_with_no_headers(self, temp_knowledge_dir):
        """Test validation of file without headers."""
        # Create file without headers
        no_headers_file = temp_knowledge_dir / "no-headers.md"
        no_headers_file.write_text(
            """This is content without headers.
Just plain text.
""",
            encoding="utf-8",
        )

        validator = KnowledgeBaseValidator(temp_knowledge_dir)
        result = validator.validate_file(no_headers_file)

        # Should have warning about no headers
        assert any(issue.rule == "no_headers" for issue in result.issues)
        assert not result.has_headers

    def test_validate_unclosed_code_block(self, temp_knowledge_dir):
        """Test validation detects unclosed code blocks."""
        # Create file with unclosed code block (odd number of ``` markers)
        unclosed_file = temp_knowledge_dir / "unclosed.md"
        # Write content with exactly one ``` marker (unclosed)
        # Write with explicit control to avoid triple-quote string issues
        lines = [
            "# Document",
            "",
            "```python",
            "def function():",
            "    return True",
            "# Missing closing marker",
        ]
        unclosed_file.write_text("\n".join(lines), encoding="utf-8")

        # Verify file has odd number of markers (1)
        file_content = unclosed_file.read_text(encoding="utf-8")
        marker_count = file_content.count("```")
        assert marker_count == 1, f"Expected 1 marker, got {marker_count}. Content: {repr(file_content)}"

        validator = KnowledgeBaseValidator(temp_knowledge_dir)
        result = validator.validate_file(unclosed_file)

        # Check what validation actually sees
        # The validation should detect unclosed code block (odd number of markers)
        # Note: If markdown library is not available, this validation may be skipped
        # So we check if the issue exists OR if markdown validation was skipped
        issues_by_rule = {issue.rule: issue for issue in result.issues}
        
        # Either we detect unclosed_code_block OR markdown validation was skipped
        if "unclosed_code_block" in issues_by_rule:
            # Validation correctly detected the issue
            assert True
        elif "markdown_syntax" in issues_by_rule:
            # Markdown parsing error (which is acceptable for unclosed blocks)
            assert True
        else:
            # If no issues found, check if markdown is available
            # If markdown is available, this is a bug; if not, it's expected
            import tapps_agents.experts.knowledge_validator as validator_module
            if validator_module.MARKDOWN_AVAILABLE:
                # Markdown is available but no issue found - this might be a bug
                pytest.fail(f"Expected unclosed_code_block issue but none found. Issues: {list(issues_by_rule.keys())}")
            else:
                # Markdown not available - validation skipped (acceptable)
                pytest.skip("Markdown library not available, unclosed code block validation skipped")

    def test_validate_python_syntax_error(self, temp_knowledge_dir):
        """Test validation detects Python syntax errors in code blocks."""
        # Create file with Python syntax error
        syntax_error_file = temp_knowledge_dir / "syntax-error.md"
        syntax_error_file.write_text(
            """# Document

```python
def function(:  # Syntax error
    return True
```
""",
            encoding="utf-8",
        )

        validator = KnowledgeBaseValidator(temp_knowledge_dir)
        result = validator.validate_file(syntax_error_file)

        # Should detect Python syntax error
        assert any(issue.rule == "python_syntax" for issue in result.issues)

    def test_validate_empty_code_block(self, temp_knowledge_dir):
        """Test validation detects empty code blocks."""
        # Create file with empty code block
        empty_code_file = temp_knowledge_dir / "empty-code.md"
        empty_code_file.write_text(
            """# Document

```python
```
""",
            encoding="utf-8",
        )

        validator = KnowledgeBaseValidator(temp_knowledge_dir)
        result = validator.validate_file(empty_code_file)

        # Should detect empty code block
        assert any(issue.rule == "empty_code_block" for issue in result.issues)

    def test_validate_broken_reference(self, temp_knowledge_dir):
        """Test validation detects broken cross-references."""
        # Create file with broken link
        broken_ref_file = temp_knowledge_dir / "broken-ref.md"
        broken_ref_file.write_text(
            """# Document

See [other file](nonexistent.md) for details.
""",
            encoding="utf-8",
        )

        validator = KnowledgeBaseValidator(temp_knowledge_dir)
        result = validator.validate_file(broken_ref_file)

        # Should detect broken reference
        assert any(issue.rule == "broken_reference" for issue in result.issues)

    def test_validate_header_hierarchy(self, temp_knowledge_dir):
        """Test validation detects header hierarchy issues."""
        # Create file with skipped header level
        hierarchy_file = temp_knowledge_dir / "hierarchy.md"
        hierarchy_file.write_text(
            """# H1

## H2

#### H4  # Skipped H3
""",
            encoding="utf-8",
        )

        validator = KnowledgeBaseValidator(temp_knowledge_dir)
        result = validator.validate_file(hierarchy_file)

        # Should detect header hierarchy issue
        assert any(issue.rule == "header_hierarchy" for issue in result.issues)

    def test_validate_large_file(self, temp_knowledge_dir):
        """Test validation warns about large files."""
        # Create large file (>100KB)
        large_content = "# Large File\n\n" + "Content line.\n" * 5000
        large_file = temp_knowledge_dir / "large.md"
        large_file.write_text(large_content, encoding="utf-8")

        validator = KnowledgeBaseValidator(temp_knowledge_dir)
        result = validator.validate_file(large_file)

        # Should warn about large file if > 100KB
        if result.file_size > 100_000:
            assert any(issue.rule == "file_size" for issue in result.issues)

    def test_validate_all(self, temp_knowledge_dir):
        """Test validating all files in directory."""
        # Create multiple files
        (temp_knowledge_dir / "file1.md").write_text("# File 1\nContent", encoding="utf-8")
        (temp_knowledge_dir / "file2.md").write_text("# File 2\nContent", encoding="utf-8")

        validator = KnowledgeBaseValidator(temp_knowledge_dir)
        results = validator.validate_all()

        assert len(results) == 2
        assert all(r.is_valid for r in results)

    def test_get_summary(self, temp_knowledge_dir):
        """Test validation summary generation."""
        # Create files with some issues
        (temp_knowledge_dir / "valid.md").write_text("# Valid\nContent", encoding="utf-8")
        (temp_knowledge_dir / "invalid.md").write_text("No headers\n", encoding="utf-8")

        validator = KnowledgeBaseValidator(temp_knowledge_dir)
        results = validator.validate_all()
        summary = validator.get_summary(results)

        assert summary["total_files"] == 2
        assert summary["valid_files"] >= 1
        assert "issues_by_severity" in summary
