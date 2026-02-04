"""
Knowledge Base Validator

Validates knowledge base files for structure, syntax, and quality.
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import markdown
    from markdown.extensions import codehilite, fenced_code, tables
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    markdown = None


@dataclass
class ValidationIssue:
    """A validation issue found in a knowledge file."""

    file_path: Path
    severity: str  # 'error', 'warning', 'info'
    line_number: int | None
    message: str
    rule: str  # Rule identifier


@dataclass
class ValidationResult:
    """Result of knowledge base validation."""

    file_path: Path
    is_valid: bool
    issues: list[ValidationIssue]
    file_size: int
    line_count: int
    has_headers: bool
    has_code_blocks: bool
    has_examples: bool


class KnowledgeBaseValidator:
    """Validates knowledge base markdown files."""

    def __init__(self, knowledge_dir: Path):
        """
        Initialize validator.

        Args:
            knowledge_dir: Directory containing knowledge files
        """
        self.knowledge_dir = Path(knowledge_dir)
        self.issues: list[ValidationIssue] = []

    def validate_all(self) -> list[ValidationResult]:
        """
        Validate all markdown files in knowledge directory.

        Returns:
            List of validation results
        """
        results: list[ValidationResult] = []

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "README.md":
                continue  # Skip README files

            result = self.validate_file(md_file)
            results.append(result)

        return results

    def validate_file(self, file_path: Path) -> ValidationResult:
        """
        Validate a single knowledge file.

        Args:
            file_path: Path to markdown file

        Returns:
            ValidationResult with issues found
        """
        issues: list[ValidationIssue] = []

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            file_size = len(content)
            line_count = len(lines)

            # Check file size
            if file_size > 100_000:  # 100KB limit
                issues.append(
                    ValidationIssue(
                        file_path=file_path,
                        severity="warning",
                        line_number=None,
                        message=f"File is large ({file_size:,} bytes). Consider splitting.",
                        rule="file_size",
                    )
                )

            # Check for headers
            has_headers = any(line.strip().startswith("#") for line in lines)
            if not has_headers:
                issues.append(
                    ValidationIssue(
                        file_path=file_path,
                        severity="warning",
                        line_number=None,
                        message="File has no headers. Headers improve chunking and navigation.",
                        rule="no_headers",
                    )
                )

            # Check markdown syntax
            md_issues = self._validate_markdown_syntax(content, file_path)
            issues.extend(md_issues)

            # Check for code blocks
            has_code_blocks = "```" in content
            has_examples = has_code_blocks

            # Validate code examples
            if has_code_blocks:
                code_issues = self._validate_code_blocks(content, file_path)
                issues.extend(code_issues)

            # Check for cross-references
            ref_issues = self._validate_cross_references(content, file_path, self.knowledge_dir)
            issues.extend(ref_issues)

            # Check structure
            structure_issues = self._validate_structure(content, file_path)
            issues.extend(structure_issues)

            # Determine if valid (no errors)
            is_valid = all(issue.severity != "error" for issue in issues)

            return ValidationResult(
                file_path=file_path,
                is_valid=is_valid,
                issues=issues,
                file_size=file_size,
                line_count=line_count,
                has_headers=has_headers,
                has_code_blocks=has_code_blocks,
                has_examples=has_examples,
            )

        except Exception as e:
            issues.append(
                ValidationIssue(
                    file_path=file_path,
                    severity="error",
                    line_number=None,
                    message=f"Failed to read file: {e}",
                    rule="read_error",
                )
            )
            return ValidationResult(
                file_path=file_path,
                is_valid=False,
                issues=issues,
                file_size=0,
                line_count=0,
                has_headers=False,
                has_code_blocks=False,
                has_examples=False,
            )

    def _validate_markdown_syntax(self, content: str, file_path: Path) -> list[ValidationIssue]:
        """Validate markdown syntax."""
        issues: list[ValidationIssue] = []

        if not MARKDOWN_AVAILABLE:
            # Skip markdown validation if library not available
            return issues

        try:
            # Try to parse markdown
            md = markdown.Markdown(
                extensions=[
                    "codehilite",
                    "fenced_code",
                    "tables",
                    "toc",
                ]
            )
            md.convert(content)
        except Exception as e:
            issues.append(
                ValidationIssue(
                    file_path=file_path,
                    severity="error",
                    line_number=None,
                    message=f"Markdown syntax error: {e}",
                    rule="markdown_syntax",
                )
            )

        # Check for unclosed code blocks (simple check - count ``` markers)
        # Note: This is a simple heuristic - a more sophisticated check would
        # track code block state through the file
        code_block_markers = content.count("```")
        if code_block_markers > 0 and code_block_markers % 2 != 0:
            issues.append(
                ValidationIssue(
                    file_path=file_path,
                    severity="error",
                    line_number=None,
                    message="Unclosed code block detected (odd number of ``` markers)",
                    rule="unclosed_code_block",
                )
            )

        return issues

    def _validate_code_blocks(self, content: str, file_path: Path) -> list[ValidationIssue]:
        """Validate code blocks in content."""
        issues: list[ValidationIssue] = []

        # Extract code blocks
        code_block_pattern = re.compile(r"```(\w+)?\n(.*?)```", re.DOTALL)
        matches = code_block_pattern.finditer(content)

        for match in matches:
            language = match.group(1) or "unknown"
            code = match.group(2)

            # Validate Python code
            if language == "python":
                try:
                    ast.parse(code)
                except SyntaxError as e:
                    line_num = content[: match.start()].count("\n") + 1
                    issues.append(
                        ValidationIssue(
                            file_path=file_path,
                            severity="error",
                            line_number=line_num,
                            message=f"Python syntax error in code block: {e.msg}",
                            rule="python_syntax",
                        )
                    )

            # Check for empty code blocks
            if not code.strip():
                line_num = content[: match.start()].count("\n") + 1
                issues.append(
                    ValidationIssue(
                        file_path=file_path,
                        severity="warning",
                        line_number=line_num,
                        message="Empty code block found",
                        rule="empty_code_block",
                    )
                )

        return issues

    def _validate_cross_references(self, content: str, file_path: Path, knowledge_dir: Path) -> list[ValidationIssue]:
        """Validate cross-references to other files."""
        issues: list[ValidationIssue] = []

        # Find markdown links
        link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
        matches = link_pattern.finditer(content)

        for match in matches:
            match.group(1)
            link_target = match.group(2)

            # Skip external links
            if link_target.startswith("http://") or link_target.startswith("https://"):
                continue

            # Check if referenced file exists
            if link_target.startswith("/"):
                # Absolute path from knowledge root
                target_path = knowledge_dir / link_target.lstrip("/")
            else:
                # Relative path
                target_path = file_path.parent / link_target

            if not target_path.exists():
                line_num = content[: match.start()].count("\n") + 1
                issues.append(
                    ValidationIssue(
                        file_path=file_path,
                        severity="warning",
                        line_number=line_num,
                        message=f"Broken cross-reference: {link_target}",
                        rule="broken_reference",
                    )
                )

        return issues

    def _validate_structure(self, content: str, file_path: Path) -> list[ValidationIssue]:
        """Validate document structure."""
        issues: list[ValidationIssue] = []
        lines = content.split("\n")

        # Check for title (first line should be H1)
        if lines and not lines[0].strip().startswith("# "):
            issues.append(
                ValidationIssue(
                    file_path=file_path,
                    severity="info",
                    line_number=1,
                    message="First line should be an H1 title (# Title)",
                    rule="missing_title",
                )
            )

        # Check header hierarchy (don't skip levels)
        prev_level = 0
        for i, line in enumerate(lines, 1):
            if line.strip().startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                if level > prev_level + 1:
                    issues.append(
                        ValidationIssue(
                            file_path=file_path,
                            severity="warning",
                            line_number=i,
                            message=f"Header level skipped (H{prev_level} → H{level})",
                            rule="header_hierarchy",
                        )
                    )
                prev_level = level

        # Check for very long lines (hard to read)
        for i, line in enumerate(lines, 1):
            if len(line) > 120 and not line.strip().startswith("```"):
                issues.append(
                    ValidationIssue(
                        file_path=file_path,
                        severity="info",
                        line_number=i,
                        message=f"Long line ({len(line)} chars). Consider breaking into multiple lines.",
                        rule="long_line",
                    )
                )

        return issues

    def get_summary(self, results: list[ValidationResult]) -> dict[str, Any]:
        """
        Get validation summary.

        Args:
            results: List of validation results

        Returns:
            Summary dictionary
        """
        total_files = len(results)
        valid_files = sum(1 for r in results if r.is_valid)
        total_issues = sum(len(r.issues) for r in results)

        issues_by_severity = {"error": 0, "warning": 0, "info": 0}
        for result in results:
            for issue in result.issues:
                issues_by_severity[issue.severity] += 1

        return {
            "total_files": total_files,
            "valid_files": valid_files,
            "invalid_files": total_files - valid_files,
            "total_issues": total_issues,
            "issues_by_severity": issues_by_severity,
            "files_with_headers": sum(1 for r in results if r.has_headers),
            "files_with_code": sum(1 for r in results if r.has_code_blocks),
            "average_file_size": sum(r.file_size for r in results) / total_files if total_files > 0 else 0,
        }
