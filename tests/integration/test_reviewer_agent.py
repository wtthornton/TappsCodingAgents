"""
Integration tests for ReviewerAgent.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from tapps_agents.agents.reviewer.agent import ReviewerAgent
from tests.fixtures.sample_code import SIMPLE_CODE, COMPLEX_CODE, INSECURE_CODE


@pytest.mark.integration
class TestReviewerAgent:
    """Integration tests for ReviewerAgent."""
    
    @pytest.mark.asyncio
    async def test_reviewer_initialization(self, mock_mal):
        """Test that ReviewerAgent initializes correctly."""
        reviewer = ReviewerAgent(mal=mock_mal)
        assert reviewer.agent_id == "reviewer"
        assert reviewer.agent_name == "Reviewer Agent"
        assert reviewer.mal is not None
        assert reviewer.scorer is not None
    
    @pytest.mark.asyncio
    async def test_reviewer_get_commands(self, mock_mal):
        """Test that ReviewerAgent returns correct commands."""
        reviewer = ReviewerAgent(mal=mock_mal)
        commands = reviewer.get_commands()
        
        command_names = [cmd["command"] for cmd in commands]
        assert "*help" in command_names
        assert "*review" in command_names
        assert "*score" in command_names
    
    @pytest.mark.asyncio
    async def test_reviewer_help_command(self, mock_mal):
        """Test that help command works."""
        reviewer = ReviewerAgent(mal=mock_mal)
        result = await reviewer.run("help")
        
        assert result["type"] == "help"
        assert "content" in result
        assert "Reviewer Agent" in result["content"]
    
    @pytest.mark.asyncio
    async def test_reviewer_review_command(self, mock_mal, sample_python_file: Path):
        """Test that review command works."""
        reviewer = ReviewerAgent(mal=mock_mal)
        mock_mal.generate.return_value = "This code looks good. No major issues found."
        
        result = await reviewer.run("review", file=str(sample_python_file))
        
        assert "file" in result
        assert "scoring" in result
        assert "feedback" in result
        assert "passed" in result
        assert isinstance(result["scoring"]["overall_score"], (int, float))
    
    @pytest.mark.asyncio
    async def test_reviewer_review_command_no_file(self, mock_mal):
        """Test that review command handles missing file gracefully."""
        reviewer = ReviewerAgent(mal=mock_mal)
        
        result = await reviewer.run("review", file=None)
        
        assert "error" in result
        assert "required" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_reviewer_score_command(self, mock_mal, sample_python_file: Path):
        """Test that score command works without LLM feedback."""
        reviewer = ReviewerAgent(mal=mock_mal)
        
        result = await reviewer.run("score", file=str(sample_python_file))
        
        assert "file" in result
        assert "scoring" in result
        assert "feedback" not in result  # Score only, no feedback
        assert isinstance(result["scoring"]["overall_score"], (int, float))
    
    @pytest.mark.asyncio
    async def test_reviewer_review_file_simple_code(self, mock_mal, tmp_path: Path):
        """Test reviewing simple code."""
        reviewer = ReviewerAgent(mal=mock_mal)
        test_file = tmp_path / "simple.py"
        test_file.write_text(SIMPLE_CODE)
        mock_mal.generate.return_value = "Simple, clean code. Good structure."
        
        result = await reviewer.review_file(test_file, include_scoring=True, include_llm_feedback=True)
        
        assert result["file"] == str(test_file)
        assert "scoring" in result
        assert "feedback" in result
        assert result["passed"] is not None
    
    @pytest.mark.asyncio
    async def test_reviewer_review_file_complex_code(self, mock_mal, tmp_path: Path):
        """Test reviewing complex code."""
        reviewer = ReviewerAgent(mal=mock_mal)
        test_file = tmp_path / "complex.py"
        test_file.write_text(COMPLEX_CODE)
        mock_mal.generate.return_value = "Complex code with nested logic. Consider refactoring."
        
        result = await reviewer.review_file(test_file, include_scoring=True, include_llm_feedback=True)
        
        assert result["file"] == str(test_file)
        assert result["scoring"]["complexity_score"] >= 0
        # Complex code might have lower scores
        assert result["scoring"]["overall_score"] >= 0
    
    @pytest.mark.asyncio
    async def test_reviewer_review_file_insecure_code(self, mock_mal, tmp_path: Path):
        """Test reviewing code with security issues."""
        reviewer = ReviewerAgent(mal=mock_mal)
        test_file = tmp_path / "insecure.py"
        test_file.write_text(INSECURE_CODE)
        mock_mal.generate.return_value = "Security issues detected: eval(), exec(), pickle.loads()"
        
        result = await reviewer.review_file(test_file, include_scoring=True, include_llm_feedback=True)
        
        assert result["file"] == str(test_file)
        # Security score should be lower
        assert result["scoring"]["security_score"] >= 0
        assert result["scoring"]["security_score"] <= 10
    
    @pytest.mark.asyncio
    async def test_reviewer_score_only_no_llm(self, mock_mal, sample_python_file: Path):
        """Test that score-only mode doesn't call LLM."""
        reviewer = ReviewerAgent(mal=mock_mal)
        
        result = await reviewer.review_file(
            sample_python_file,
            include_scoring=True,
            include_llm_feedback=False
        )
        
        assert "scoring" in result
        assert "feedback" not in result
        # LLM should not be called
        mock_mal.generate.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_reviewer_activation(self, mock_mal, temp_project_dir: Path):
        """Test that reviewer activation works."""
        reviewer = ReviewerAgent(mal=mock_mal)
        
        # Should not raise exception
        await reviewer.activate(temp_project_dir)
        
        # Activation should complete
    
    @pytest.mark.asyncio
    async def test_reviewer_close(self, mock_mal):
        """Test that reviewer cleanup works."""
        reviewer = ReviewerAgent(mal=mock_mal)
        
        await reviewer.close()
        
        # MAL close should be called
        mock_mal.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reviewer_unknown_command(self, mock_mal):
        """Test that unknown commands return error."""
        reviewer = ReviewerAgent(mal=mock_mal)
        
        result = await reviewer.run("unknown_command")
        
        assert "error" in result
        assert "unknown" in result["error"].lower() or "command" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_reviewer_score_command_no_file(self, mock_mal):
        """Test score command without file path."""
        reviewer = ReviewerAgent(mal=mock_mal)
        await reviewer.activate()
        result = await reviewer.run("score")
        assert "error" in result
        assert "File path required" in result["error"]
    
    @pytest.mark.asyncio
    async def test_reviewer_review_file_not_found(self, mock_mal, tmp_path: Path):
        """Test review_file raises FileNotFoundError for non-existent file."""
        reviewer = ReviewerAgent(mal=mock_mal)
        await reviewer.activate()
        non_existent = tmp_path / "nonexistent.py"
        
        with pytest.raises(FileNotFoundError, match="File not found"):
            await reviewer.review_file(non_existent)
    
    @pytest.mark.asyncio
    async def test_reviewer_review_file_too_large(self, mock_mal, tmp_path: Path):
        """Test review_file raises ValueError for files exceeding size limit."""
        reviewer = ReviewerAgent(mal=mock_mal)
        await reviewer.activate()
        large_file = tmp_path / "large.py"
        # Create file larger than default max (1MB)
        large_content = "x" * (2 * 1024 * 1024)  # 2MB
        large_file.write_text(large_content, encoding='utf-8')
        
        with pytest.raises(ValueError, match="File too large"):
            await reviewer.review_file(large_file)
    
    @pytest.mark.asyncio
    async def test_reviewer_review_file_path_traversal_detection(self, mock_mal, tmp_path: Path):
        """Test path traversal detection."""
        reviewer = ReviewerAgent(mal=mock_mal)
        await reviewer.activate()
        
        # Create a path with .. traversal that doesn't exist when resolved
        # This tests line 123: the specific check for ".." in path and not exists
        traversal_path = Path(str(tmp_path) + "/../nonexistent_file.py")
        # Ensure it doesn't exist
        if traversal_path.exists():
            traversal_path = Path(str(tmp_path) + "/../../nonexistent_file_2.py")
        
        # This should raise ValueError for path traversal detection
        with pytest.raises((ValueError, FileNotFoundError), match="Path traversal|File not found"):
            await reviewer.review_file(traversal_path)
    
    @pytest.mark.asyncio
    async def test_reviewer_review_file_suspicious_path(self, mock_mal, tmp_path: Path):
        """Test detection of suspicious path patterns."""
        reviewer = ReviewerAgent(mal=mock_mal)
        await reviewer.activate()
        
        # Create path with URL-encoded traversal patterns
        suspicious_file = tmp_path / "test%2e%2epy"
        suspicious_file.write_text("print('test')", encoding='utf-8')
        
        with pytest.raises(ValueError, match="Suspicious path detected"):
            await reviewer.review_file(suspicious_file)
    
    @pytest.mark.asyncio
    async def test_reviewer_review_file_encoding_error(self, mock_mal, tmp_path: Path):
        """Test handling of files with encoding errors."""
        reviewer = ReviewerAgent(mal=mock_mal)
        await reviewer.activate()
        bad_encoding_file = tmp_path / "bad_encoding.py"
        # Write some bytes that are not valid UTF-8
        bad_encoding_file.write_bytes(b'\x80\x81\x82')

        with pytest.raises(ValueError, match="Cannot decode file as UTF-8"):
            await reviewer.review_file(bad_encoding_file)
    
    @pytest.mark.asyncio
    async def test_reviewer_llm_feedback_exception(self, mock_mal, tmp_path: Path):
        """Test that LLM feedback gracefully handles exceptions."""
        reviewer = ReviewerAgent(mal=mock_mal)
        await reviewer.activate()
        
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello(): pass", encoding='utf-8')
        
        # Make MAL.generate raise an exception
        mock_mal.generate.side_effect = Exception("LLM connection failed")
        
        result = await reviewer.review_file(
            test_file,
            include_scoring=True,
            include_llm_feedback=True
        )
        
        # Should still return results, but with error in feedback
        assert "feedback" in result
        assert "error" in result["feedback"]
        assert "LLM connection failed" in result["feedback"]["error"]
    
    @pytest.mark.asyncio
    async def test_reviewer_performance_large_file(self, mock_mal, tmp_path: Path):
        """Performance test: Review a large file (1000+ lines) should complete in <5s."""
        import time
        
        print("\n[TEST] Starting large file performance test...")
        reviewer = ReviewerAgent(mal=mock_mal)
        await reviewer.activate()
        print("[TEST] Reviewer agent activated")
        
        # Create a large Python file (~1500 lines)
        print("[TEST] Creating large test file (1500 lines)...")
        large_code = "# Large file test\n"
        large_code += "\n".join([f"def func_{i}(): return {i}" for i in range(1500)])
        
        large_file = tmp_path / "large_test.py"
        large_file.write_text(large_code, encoding='utf-8')
        print(f"[TEST] File created: {len(large_code)} bytes")
        
        print("[TEST] Starting file review (this may take a few seconds)...")
        start_time = time.time()
        result = await reviewer.review_file(
            large_file,
            include_scoring=True,
            include_llm_feedback=False  # Skip LLM to focus on scoring performance
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
    async def test_reviewer_lint_command(self, mock_mal, sample_python_file: Path):
        """Test that lint command works (Phase 6)."""
        reviewer = ReviewerAgent(mal=mock_mal)
        
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
    async def test_reviewer_lint_command_no_file(self, mock_mal):
        """Test that lint command handles missing file gracefully."""
        reviewer = ReviewerAgent(mal=mock_mal)
        
        result = await reviewer.run("lint", file=None)
        
        assert "error" in result
        assert "required" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_reviewer_lint_file_non_python(self, mock_mal, tmp_path: Path):
        """Test lint_file returns appropriate result for non-Python files."""
        reviewer = ReviewerAgent(mal=mock_mal)
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is not Python code")
        
        result = await reviewer.lint_file(test_file)
        
        assert result["file"] == str(test_file)
        assert result["linting_score"] == 10.0
        assert result["issue_count"] == 0
        assert "message" in result
        assert "Python" in result["message"] or "TypeScript" in result["message"] or "JavaScript" in result["message"]
    
    @pytest.mark.asyncio
    async def test_reviewer_lint_file_not_found(self, mock_mal, tmp_path: Path):
        """Test lint_file raises FileNotFoundError for non-existent file."""
        reviewer = ReviewerAgent(mal=mock_mal)
        non_existent = tmp_path / "nonexistent.py"
        
        with pytest.raises(FileNotFoundError, match="File not found"):
            await reviewer.lint_file(non_existent)
    
    @pytest.mark.asyncio
    async def test_reviewer_get_commands_includes_lint(self, mock_mal):
        """Test that get_commands includes *lint command (Phase 6)."""
        reviewer = ReviewerAgent(mal=mock_mal)
        commands = reviewer.get_commands()
        
        command_names = [cmd["command"] for cmd in commands]
        assert "*lint" in command_names
    
    @pytest.mark.asyncio
    async def test_reviewer_review_includes_linting_score(self, mock_mal, sample_python_file: Path):
        """Test that review command includes linting_score in results (Phase 6.1)."""
        reviewer = ReviewerAgent(mal=mock_mal)
        mock_mal.generate.return_value = "Code review feedback"
        
        result = await reviewer.run("review", file=str(sample_python_file))
        
        assert "scoring" in result
        assert "linting_score" in result["scoring"]
        assert "linting" in result["scoring"]["metrics"]
    
    # Phase 6.2: mypy Integration Tests
    @pytest.mark.asyncio
    async def test_reviewer_type_check_command(self, mock_mal, sample_python_file: Path):
        """Test that type-check command works (Phase 6.2)."""
        reviewer = ReviewerAgent(mal=mock_mal)
        
        result = await reviewer.run("type-check", file=str(sample_python_file))
        
        assert "file" in result
        assert "type_checking_score" in result
        assert "errors" in result
        assert "error_count" in result
        assert "error_codes" in result
        assert 0 <= result["type_checking_score"] <= 10
    
    @pytest.mark.asyncio
    async def test_reviewer_type_check_command_no_file(self, mock_mal):
        """Test that type-check command handles missing file gracefully."""
        reviewer = ReviewerAgent(mal=mock_mal)
        
        result = await reviewer.run("type-check", file=None)
        
        assert "error" in result
        assert "required" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_reviewer_type_check_file_non_python(self, mock_mal, tmp_path: Path):
        """Test type_check_file returns appropriate result for non-Python files."""
        reviewer = ReviewerAgent(mal=mock_mal)
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is not Python code")
        
        result = await reviewer.type_check_file(test_file)
        
        assert result["file"] == str(test_file)
        assert result["type_checking_score"] == 10.0
        assert result["error_count"] == 0
        assert "message" in result
        assert "Python" in result["message"] or "TypeScript" in result["message"]
    
    @pytest.mark.asyncio
    async def test_reviewer_type_check_file_not_found(self, mock_mal, tmp_path: Path):
        """Test type_check_file raises FileNotFoundError for non-existent file."""
        reviewer = ReviewerAgent(mal=mock_mal)
        non_existent = tmp_path / "nonexistent.py"
        
        with pytest.raises(FileNotFoundError, match="File not found"):
            await reviewer.type_check_file(non_existent)
    
    @pytest.mark.asyncio
    async def test_reviewer_get_commands_includes_type_check(self, mock_mal):
        """Test that get_commands includes *type-check command (Phase 6.2)."""
        reviewer = ReviewerAgent(mal=mock_mal)
        commands = reviewer.get_commands()
        
        command_names = [cmd["command"] for cmd in commands]
        assert "*type-check" in command_names
    
    @pytest.mark.asyncio
    async def test_reviewer_review_includes_type_checking_score(self, mock_mal, sample_python_file: Path):
        """Test that review command includes type_checking_score in results (Phase 6.2)."""
        reviewer = ReviewerAgent(mal=mock_mal)
        mock_mal.generate.return_value = "Code review feedback"
        
        result = await reviewer.run("review", file=str(sample_python_file))
        
        assert "scoring" in result
        assert "type_checking_score" in result["scoring"]
        assert "type_checking" in result["scoring"]["metrics"]

