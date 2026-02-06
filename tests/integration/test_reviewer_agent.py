"""
Integration tests for ReviewerAgent.
"""

from pathlib import Path

import pytest

from tapps_agents.agents.reviewer.agent import ReviewerAgent
from tests.fixtures.sample_code import COMPLEX_CODE, INSECURE_CODE, SIMPLE_CODE


@pytest.mark.integration
class TestReviewerAgent:
    """Integration tests for ReviewerAgent."""

    @pytest.mark.asyncio
    async def test_reviewer_initialization(self):
        """Test that ReviewerAgent initializes correctly."""
        reviewer = ReviewerAgent()
        assert reviewer.agent_id == "reviewer"
        assert reviewer.agent_name == "Reviewer Agent"
        assert reviewer.scorer is not None

    @pytest.mark.asyncio
    async def test_reviewer_get_commands(self):
        """Test that ReviewerAgent returns correct commands."""
        reviewer = ReviewerAgent()
        commands = reviewer.get_commands()

        command_names = [cmd["command"] for cmd in commands]
        assert "*help" in command_names
        assert "*review" in command_names
        assert "*score" in command_names

    @pytest.mark.asyncio
    async def test_reviewer_help_command(self):
        """Test that help command works."""
        reviewer = ReviewerAgent()
        result = await reviewer.run("help")

        assert result["type"] == "help"
        assert "content" in result
        assert "Reviewer Agent" in result["content"]

    @pytest.mark.asyncio
    async def test_reviewer_review_command(self, sample_python_file: Path):
        """Test that review command works."""
        reviewer = ReviewerAgent()
        result = await reviewer.run("review", file=str(sample_python_file))

        assert "file" in result
        assert "scoring" in result
        assert "feedback" in result
        assert "passed" in result
        assert isinstance(result["scoring"]["overall_score"], (int, float))

    @pytest.mark.asyncio
    async def test_reviewer_review_command_no_file(self):
        """Test that review command handles missing file gracefully."""
        reviewer = ReviewerAgent()

        result = await reviewer.run("review", file=None)

        assert "error" in result
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_reviewer_score_command(self, sample_python_file: Path):
        """Test that score command works without LLM feedback."""
        reviewer = ReviewerAgent()

        result = await reviewer.run("score", file=str(sample_python_file))

        assert "file" in result
        assert "scoring" in result
        assert "feedback" not in result  # Score only, no feedback
        assert isinstance(result["scoring"]["overall_score"], (int, float))

    @pytest.mark.asyncio
    async def test_reviewer_review_file_simple_code(self, tmp_path: Path):
        """Test reviewing simple code."""
        reviewer = ReviewerAgent()
        test_file = tmp_path / "simple.py"
        test_file.write_text(SIMPLE_CODE)
        result = await reviewer.review_file(
            test_file, include_scoring=True, include_llm_feedback=True
        )

        assert result["file"] == str(test_file)
        assert "scoring" in result
        assert "feedback" in result
        assert result["passed"] is not None

    @pytest.mark.asyncio
    async def test_reviewer_review_file_complex_code(self, tmp_path: Path):
        """Test reviewing complex code."""
        reviewer = ReviewerAgent()
        test_file = tmp_path / "complex.py"
        test_file.write_text(COMPLEX_CODE)
        result = await reviewer.review_file(
            test_file, include_scoring=True, include_llm_feedback=True
        )

        assert result["file"] == str(test_file)
        assert result["scoring"]["complexity_score"] >= 0
        # Complex code might have lower scores
        assert result["scoring"]["overall_score"] >= 0

    @pytest.mark.asyncio
    async def test_reviewer_review_file_insecure_code(self, tmp_path: Path):
        """Test reviewing code with security issues."""
        reviewer = ReviewerAgent()
        test_file = tmp_path / "insecure.py"
        test_file.write_text(INSECURE_CODE)
        result = await reviewer.review_file(
            test_file, include_scoring=True, include_llm_feedback=True
        )

        assert result["file"] == str(test_file)
        # Security score should be lower
        assert result["scoring"]["security_score"] >= 0
        assert result["scoring"]["security_score"] <= 10

    @pytest.mark.asyncio
    async def test_reviewer_score_only_no_llm(self, sample_python_file: Path):
        """Test that score-only mode returns scoring without feedback."""
        reviewer = ReviewerAgent()
        result = await reviewer.review_file(
            sample_python_file, include_scoring=True, include_llm_feedback=False
        )
        assert "scoring" in result
        assert "feedback" not in result

    @pytest.mark.asyncio
    async def test_reviewer_activation(self, temp_project_dir: Path):
        """Test that reviewer activation works."""
        reviewer = ReviewerAgent()

        # Should not raise exception
        await reviewer.activate(temp_project_dir)

        # Activation should complete

    @pytest.mark.asyncio
    async def test_reviewer_close(self):
        """Test that reviewer cleanup works."""
        reviewer = ReviewerAgent()
        await reviewer.close()
        # Should not raise

    @pytest.mark.asyncio
    async def test_reviewer_unknown_command(self):
        """Test that unknown commands return error."""
        reviewer = ReviewerAgent()

        result = await reviewer.run("unknown_command")

        assert "error" in result
        assert (
            "unknown" in result["error"].lower() or "command" in result["error"].lower()
        )

    @pytest.mark.asyncio
    async def test_reviewer_score_command_no_file(self):
        """Test score command without file path."""
        reviewer = ReviewerAgent()
        await reviewer.activate()
        result = await reviewer.run("score")
        assert "error" in result
        assert "File path required" in result["error"]

    @pytest.mark.asyncio
    async def test_reviewer_review_file_not_found(self, tmp_path: Path):
        """Test review_file raises FileNotFoundError for non-existent file."""
        reviewer = ReviewerAgent()
        await reviewer.activate()
        non_existent = tmp_path / "nonexistent.py"

        with pytest.raises(FileNotFoundError, match="File not found"):
            await reviewer.review_file(non_existent)

    @pytest.mark.asyncio
    async def test_reviewer_review_file_too_large(self, tmp_path: Path):
        """Test review_file raises ValueError for files exceeding size limit."""
        reviewer = ReviewerAgent()
        await reviewer.activate()
        large_file = tmp_path / "large.py"
        # Create file larger than default max (1MB)
        large_content = "x" * (2 * 1024 * 1024)  # 2MB
        large_file.write_text(large_content, encoding="utf-8")

        with pytest.raises(ValueError, match="File too large"):
            await reviewer.review_file(large_file)

    @pytest.mark.asyncio
    async def test_reviewer_review_file_path_traversal_detection(
        self, tmp_path: Path
    ):
        """Test path traversal detection."""
        reviewer = ReviewerAgent()
        await reviewer.activate()

        # Create a path with .. traversal that doesn't exist when resolved
        # This tests line 123: the specific check for ".." in path and not exists
        traversal_path = Path(str(tmp_path) + "/../nonexistent_file.py")
        # Ensure it doesn't exist
        if traversal_path.exists():
            traversal_path = Path(str(tmp_path) + "/../../nonexistent_file_2.py")

        # This should raise ValueError for path traversal detection
        with pytest.raises(
            (ValueError, FileNotFoundError), match="Path traversal|File not found"
        ):
            await reviewer.review_file(traversal_path)

    @pytest.mark.asyncio
    async def test_reviewer_review_file_suspicious_path(self, tmp_path: Path):
        """Test detection of suspicious path patterns."""
        reviewer = ReviewerAgent()
        await reviewer.activate()

        # Create path with URL-encoded traversal patterns
        suspicious_file = tmp_path / "test%2e%2epy"
        suspicious_file.write_text("print('test')", encoding="utf-8")

        with pytest.raises(ValueError, match="Suspicious path detected"):
            await reviewer.review_file(suspicious_file)

    @pytest.mark.asyncio
    async def test_reviewer_review_file_encoding_error(self, tmp_path: Path):
        """Test handling of files with encoding errors."""
        reviewer = ReviewerAgent()
        await reviewer.activate()
        bad_encoding_file = tmp_path / "bad_encoding.py"
        # Write some bytes that are not valid UTF-8
        bad_encoding_file.write_bytes(b"\x80\x81\x82")

        with pytest.raises(ValueError, match="Cannot decode file as UTF-8"):
            await reviewer.review_file(bad_encoding_file)

    @pytest.mark.asyncio
    async def test_reviewer_llm_feedback_exception(self, tmp_path: Path):
        """Test that review returns scoring and feedback key when LLM is requested."""
        reviewer = ReviewerAgent()
        await reviewer.activate()
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello(): pass", encoding="utf-8")
        result = await reviewer.review_file(
            test_file, include_scoring=True, include_llm_feedback=True
        )
        assert "scoring" in result
        assert "feedback" in result

    @pytest.mark.asyncio
    async def test_reviewer_performance_large_file(self, tmp_path: Path):
        """Performance test: Review a large file (1000+ lines) should complete in <5s."""
        import time

        print("\n[TEST] Starting large file performance test...")
        reviewer = ReviewerAgent()
        await reviewer.activate()
        print("[TEST] Reviewer agent activated")

        # Create a large Python file (~1500 lines)
        print("[TEST] Creating large test file (1500 lines)...")
        large_code = "# Large file test\n"
        large_code += "\n".join([f"def func_{i}(): return {i}" for i in range(1500)])

        large_file = tmp_path / "large_test.py"
        large_file.write_text(large_code, encoding="utf-8")
        print(f"[TEST] File created: {len(large_code)} bytes")

        print("[TEST] Starting file review (this may take a few seconds)...")
        start_time = time.time()
        result = await reviewer.review_file(
            large_file,
            include_scoring=True,
            include_llm_feedback=False,  # Skip LLM to focus on scoring performance
        )
        elapsed = time.time() - start_time
        print(f"[TEST] Review completed in {elapsed:.2f}s")

        # Should complete in <5 seconds for 1500-line file
        assert elapsed < 5.0, f"Review took {elapsed:.2f}s, expected <5s"
        assert "scoring" in result
        assert result["scoring"]["overall_score"] >= 0
        print("[TEST] Large file performance test passed OK")

    # Phase 6.1: Ruff Integration Tests
    @pytest.mark.asyncio
    async def test_reviewer_lint_command(self, sample_python_file: Path):
        """Test that lint command works (Phase 6)."""
        reviewer = ReviewerAgent()

        result = await reviewer.run("lint", file=str(sample_python_file))

        assert "file" in result
        assert "linting_score" in result
        assert "issues" in result
        assert "issue_count" in result
        assert "error_count" in result
        assert "warning_count" in result
        assert "fatal_count" in result
        assert 0 <= result["linting_score"] <= 10

    @pytest.mark.asyncio
    async def test_reviewer_lint_command_no_file(self):
        """Test that lint command handles missing file gracefully."""
        reviewer = ReviewerAgent()

        result = await reviewer.run("lint", file=None)

        assert "error" in result
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_reviewer_lint_file_non_python(self, tmp_path: Path):
        """Test lint_file returns appropriate result for non-Python files."""
        reviewer = ReviewerAgent()
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is not Python code")

        result = await reviewer.lint_file(test_file)

        assert result["file"] == str(test_file)
        assert result["linting_score"] == 10.0
        assert result["issue_count"] == 0
        assert "message" in result
        assert (
            "Python" in result["message"]
            or "TypeScript" in result["message"]
            or "JavaScript" in result["message"]
        )

    @pytest.mark.asyncio
    async def test_reviewer_lint_file_not_found(self, tmp_path: Path):
        """Test lint_file raises FileNotFoundError for non-existent file."""
        reviewer = ReviewerAgent()
        non_existent = tmp_path / "nonexistent.py"

        with pytest.raises(FileNotFoundError, match="File not found"):
            await reviewer.lint_file(non_existent)

    @pytest.mark.asyncio
    async def test_reviewer_get_commands_includes_lint(self):
        """Test that get_commands includes *lint command (Phase 6)."""
        reviewer = ReviewerAgent()
        commands = reviewer.get_commands()

        command_names = [cmd["command"] for cmd in commands]
        assert "*lint" in command_names

    @pytest.mark.asyncio
    async def test_reviewer_review_includes_linting_score(
        self, sample_python_file: Path
    ):
        """Test that review command includes linting_score in results (Phase 6.1)."""
        reviewer = ReviewerAgent()
        result = await reviewer.run("review", file=str(sample_python_file))

        assert "scoring" in result
        assert "linting_score" in result["scoring"]
        assert "linting" in result["scoring"]["metrics"]

    # Phase 6.2: mypy Integration Tests
    @pytest.mark.asyncio
    async def test_reviewer_type_check_command(
        self, sample_python_file: Path
    ):
        """Test that type-check command works (Phase 6.2)."""
        reviewer = ReviewerAgent()

        result = await reviewer.run("type-check", file=str(sample_python_file))

        assert "file" in result
        assert "type_checking_score" in result
        assert "errors" in result
        assert "error_count" in result
        assert "error_codes" in result
        assert 0 <= result["type_checking_score"] <= 10

    @pytest.mark.asyncio
    async def test_reviewer_type_check_command_no_file(self):
        """Test that type-check command handles missing file gracefully."""
        reviewer = ReviewerAgent()

        result = await reviewer.run("type-check", file=None)

        assert "error" in result
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_reviewer_type_check_file_non_python(self, tmp_path: Path):
        """Test type_check_file returns appropriate result for non-Python files."""
        reviewer = ReviewerAgent()
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is not Python code")

        result = await reviewer.type_check_file(test_file)

        assert result["file"] == str(test_file)
        assert result["type_checking_score"] == 10.0
        assert result["error_count"] == 0
        assert "message" in result
        assert "Python" in result["message"] or "TypeScript" in result["message"]

    @pytest.mark.asyncio
    async def test_reviewer_type_check_file_not_found(self, tmp_path: Path):
        """Test type_check_file raises FileNotFoundError for non-existent file."""
        reviewer = ReviewerAgent()
        non_existent = tmp_path / "nonexistent.py"

        with pytest.raises(FileNotFoundError, match="File not found"):
            await reviewer.type_check_file(non_existent)

    @pytest.mark.asyncio
    async def test_reviewer_get_commands_includes_type_check(self):
        """Test that get_commands includes *type-check command (Phase 6.2)."""
        reviewer = ReviewerAgent()
        commands = reviewer.get_commands()

        command_names = [cmd["command"] for cmd in commands]
        assert "*type-check" in command_names

    @pytest.mark.asyncio
    async def test_reviewer_review_includes_type_checking_score(
        self, sample_python_file: Path
    ):
        """Test that review command includes type_checking_score in results (Phase 6.2)."""
        reviewer = ReviewerAgent()
        result = await reviewer.run("review", file=str(sample_python_file))

        assert "scoring" in result
        assert "type_checking_score" in result["scoring"]
        assert "type_checking" in result["scoring"]["metrics"]
