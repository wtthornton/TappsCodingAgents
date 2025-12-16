"""
Unit tests for edge cases and boundary conditions in core components.

This module tests:
- Empty inputs and None values
- Very large inputs and files
- Encoding and Unicode handling
- Binary file handling
- Missing optional dependencies
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from tapps_agents.agents.reviewer.scoring import CodeScorer


@pytest.mark.unit
class TestEmptyInputHandling:
    """Test handling of empty inputs and None values."""

    def test_agent_parse_command_none(self, base_agent):
        """Test parsing None command."""
        agent = base_agent
        # None should be handled gracefully
        try:
            command, args = agent.parse_command(None)
            # If it doesn't raise, should return valid structure
            assert isinstance(command, str) or command is None
            assert isinstance(args, dict)
        except (TypeError, AttributeError, IndexError):
            # Acceptable to raise on None
            pass

    def test_agent_parse_command_whitespace_only(self, base_agent):
        """Test parsing whitespace-only command."""
        agent = base_agent
        command, args = agent.parse_command("   \n\t  ")
        # Should handle whitespace gracefully
        assert isinstance(command, str)
        assert isinstance(args, dict)

    def test_scorer_score_file_none_path(self, tmp_path: Path):
        """Test scoring with None file path."""
        scorer = CodeScorer()
        with pytest.raises((TypeError, AttributeError)):
            scorer.score_file(None, "code")

    def test_scorer_score_file_none_content(self, tmp_path: Path):
        """Test scoring with None content."""
        scorer = CodeScorer()
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass")
        
        # None content should raise TypeError
        with pytest.raises((TypeError, ValueError)):
            scorer.score_file(test_file, None)

    def test_scorer_score_file_empty_string_content(self, tmp_path: Path):
        """Test scoring with empty string content."""
        scorer = CodeScorer()
        test_file = tmp_path / "empty.py"
        test_file.write_text("")
        
        result = scorer.score_file(test_file, "")
        assert isinstance(result, dict)
        assert "overall_score" in result
        # Empty file should still return valid scores
        assert 0 <= result["overall_score"] <= 100

    def test_agent_get_context_none_path(self, base_agent):
        """Test get_context with None path."""
        agent = base_agent
        with pytest.raises((TypeError, AttributeError)):
            agent.get_context(None)

    def test_agent_get_context_empty_path(self, base_agent, tmp_path: Path):
        """Test get_context with empty path."""
        agent = base_agent
        # Create a valid empty directory path, not an empty string
        empty_dir = tmp_path / "empty_dir"
        empty_dir.mkdir()
        empty_file = empty_dir / "test.py"
        empty_file.write_text("")
        
        # Should handle empty file
        context = agent.get_context(empty_file)
        assert isinstance(context, dict)


@pytest.mark.unit
class TestVeryLargeInputHandling:
    """Test handling of very large inputs and files."""

    def test_scorer_score_very_large_file(self, tmp_path: Path):
        """Test scoring a very large file (10MB+)."""
        scorer = CodeScorer()
        large_file = tmp_path / "large.py"
        
        # Create a large Python file (10MB of code)
        large_code = "# " + "x" * (10 * 1024 * 1024) + "\ndef test(): pass\n"
        large_file.write_text(large_code)
        
        # Should handle large files, though may be slow
        result = scorer.score_file(large_file, large_code)
        assert isinstance(result, dict)
        assert "overall_score" in result

    def test_scorer_score_very_large_function(self, tmp_path: Path):
        """Test scoring code with a very large function."""
        scorer = CodeScorer()
        test_file = tmp_path / "large_func.py"
        
        # Create a function with 1000+ lines
        large_func = "def large_function():\n"
        large_func += "\n".join([f"    x{i} = {i}" for i in range(2000)])
        
        result = scorer.score_file(test_file, large_func)
        assert isinstance(result, dict)
        # Very large functions should score lower
        assert result["performance_score"] < 10.0

    def test_agent_validate_path_very_large_file(self, base_agent, tmp_path: Path):
        """Test validating a very large file."""
        agent = base_agent
        large_file = tmp_path / "large.py"
        
        # Create a 50MB file
        large_content = "x" * (50 * 1024 * 1024)
        large_file.write_text(large_content)
        
        # Should raise ValueError for file too large (default max is 10MB)
        with pytest.raises(ValueError, match=r"File too large"):
            agent._validate_path(large_file)

    def test_scorer_score_very_long_line(self, tmp_path: Path):
        """Test scoring code with very long lines."""
        scorer = CodeScorer()
        test_file = tmp_path / "long_line.py"
        
        # Create a file with a very long line (100KB)
        long_line = "x" * (100 * 1024)
        code = f"def test(): return '{long_line}'\n"
        test_file.write_text(code)
        
        result = scorer.score_file(test_file, code)
        assert isinstance(result, dict)
        assert "overall_score" in result


@pytest.mark.unit
class TestEncodingAndUnicodeHandling:
    """Test handling of encoding and Unicode characters."""

    def test_scorer_score_unicode_file(self, tmp_path: Path):
        """Test scoring file with Unicode characters."""
        scorer = CodeScorer()
        test_file = tmp_path / "unicode.py"
        
        # Unicode characters in code
        unicode_code = """
def test():
    # Emoji: 🚀
    # Chinese: 测试
    # Russian: тест
    # Arabic: اختبار
    # Japanese: テスト
    message = "Hello 世界 🌍"
    return message
"""
        test_file.write_text(unicode_code, encoding="utf-8")
        
        result = scorer.score_file(test_file, unicode_code)
        assert isinstance(result, dict)
        assert "overall_score" in result

    def test_scorer_score_unicode_in_strings(self, tmp_path: Path):
        """Test scoring code with Unicode in strings."""
        scorer = CodeScorer()
        test_file = tmp_path / "unicode_strings.py"
        
        unicode_code = """
def greet():
    return "Hello, 世界! 🌍 Привет тест テスト"
"""
        test_file.write_text(unicode_code, encoding="utf-8")
        
        result = scorer.score_file(test_file, unicode_code)
        assert isinstance(result, dict)

    def test_scorer_score_unicode_in_comments(self, tmp_path: Path):
        """Test scoring code with Unicode in comments."""
        scorer = CodeScorer()
        test_file = tmp_path / "unicode_comments.py"
        
        unicode_code = """
# Comment with emoji: 🚀
# Comment with Chinese: 这是注释
def test():
    pass
"""
        test_file.write_text(unicode_code, encoding="utf-8")
        
        result = scorer.score_file(test_file, unicode_code)
        assert isinstance(result, dict)

    def test_agent_get_context_unicode_file(self, base_agent, tmp_path: Path):
        """Test get_context with Unicode file."""
        agent = base_agent
        unicode_file = tmp_path / "unicode.py"
        unicode_file.write_text("# 测试 🚀\ndef test(): pass\n", encoding="utf-8")
        
        context = agent.get_context(unicode_file)
        assert isinstance(context, dict)
        assert "content" in context or "text" in context

    def test_scorer_score_special_characters(self, tmp_path: Path):
        """Test scoring code with special characters."""
        scorer = CodeScorer()
        test_file = tmp_path / "special.py"
        
        special_code = """
def test():
    # Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?
    return "Special: \\n\\t\\r"
"""
        test_file.write_text(special_code)
        
        result = scorer.score_file(test_file, special_code)
        assert isinstance(result, dict)


@pytest.mark.unit
class TestBinaryFileHandling:
    """Test handling of binary files."""

    def test_scorer_score_binary_file(self, tmp_path: Path):
        """Test scoring a binary file (should handle gracefully)."""
        scorer = CodeScorer()
        binary_file = tmp_path / "binary.bin"
        
        # Write binary data
        binary_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd")
        
        # Should handle binary files gracefully (may raise or return default scores)
        try:
            content = binary_file.read_text(errors="replace")
            result = scorer.score_file(binary_file, content)
            assert isinstance(result, dict)
        except (UnicodeDecodeError, ValueError):
            # Acceptable to raise on binary files
            pass

    def test_scorer_score_mixed_binary_text(self, tmp_path: Path):
        """Test scoring file with mixed binary and text."""
        scorer = CodeScorer()
        mixed_file = tmp_path / "mixed.py"
        
        # Mix of text and binary-like content
        mixed_content = "def test():\n    data = b'\\x00\\x01\\x02'\n    return data\n"
        mixed_file.write_text(mixed_content)
        
        result = scorer.score_file(mixed_file, mixed_content)
        assert isinstance(result, dict)

    def test_agent_validate_path_binary_file(self, base_agent, tmp_path: Path):
        """Test validating a binary file."""
        agent = base_agent
        binary_file = tmp_path / "binary.bin"
        binary_file.write_bytes(b"\x00\x01\x02")
        
        # Binary files may not be valid Python files, but should be handled
        try:
            agent._validate_path(binary_file)
        except ValueError:
            # Acceptable to raise for non-Python files
            pass


@pytest.mark.unit
class TestMissingOptionalDependencies:
    """Test behavior when optional dependencies are missing."""

    @patch("tapps_agents.agents.reviewer.scoring.HAS_RADON", False)
    def test_scorer_without_radon(self, tmp_path: Path):
        """Test scoring when radon is not available."""
        # Reimport to get the patched version
        from importlib import reload

        import tapps_agents.agents.reviewer.scoring as scoring_module
        
        # Force reload to pick up the patch
        reload(scoring_module)
        scorer = scoring_module.CodeScorer()
        
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass")
        
        # Should still work without radon (may use fallback)
        result = scorer.score_file(test_file, "def test(): pass")
        assert isinstance(result, dict)
        assert "complexity_score" in result
        # Complexity score should still be calculated (may use AST fallback)

    @patch("tapps_agents.agents.reviewer.scoring.HAS_BANDIT", False)
    def test_scorer_without_bandit(self, tmp_path: Path):
        """Test scoring when bandit is not available."""
        from importlib import reload

        import tapps_agents.agents.reviewer.scoring as scoring_module
        
        reload(scoring_module)
        scorer = scoring_module.CodeScorer()
        
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass")
        
        # Should still work without bandit
        result = scorer.score_file(test_file, "def test(): pass")
        assert isinstance(result, dict)
        assert "security_score" in result
        # Security score should still be calculated (may use fallback)

    @patch("tapps_agents.agents.reviewer.scoring.HAS_RUFF", False)
    def test_scorer_without_ruff(self, tmp_path: Path):
        """Test scoring when ruff is not available."""
        from importlib import reload

        import tapps_agents.agents.reviewer.scoring as scoring_module
        
        reload(scoring_module)
        scorer = scoring_module.CodeScorer()
        
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass")
        
        # Should still work without ruff
        result = scorer.score_file(test_file, "def test(): pass")
        assert isinstance(result, dict)
        assert "linting_score" in result
        # Linting score may be default or use fallback

    @patch("tapps_agents.agents.reviewer.scoring.HAS_MYPY", False)
    def test_scorer_without_mypy(self, tmp_path: Path):
        """Test scoring when mypy is not available."""
        from importlib import reload

        import tapps_agents.agents.reviewer.scoring as scoring_module
        
        reload(scoring_module)
        scorer = scoring_module.CodeScorer()
        
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass")
        
        # Should still work without mypy
        result = scorer.score_file(test_file, "def test(): pass")
        assert isinstance(result, dict)
        # Type checking may be skipped, but scoring should continue

    def test_scorer_all_optional_deps_missing(self, tmp_path: Path):
        """Test scoring when all optional dependencies are missing."""
        with patch("tapps_agents.agents.reviewer.scoring.HAS_RADON", False), \
             patch("tapps_agents.agents.reviewer.scoring.HAS_BANDIT", False), \
             patch("tapps_agents.agents.reviewer.scoring.HAS_RUFF", False), \
             patch("tapps_agents.agents.reviewer.scoring.HAS_MYPY", False):
            
            from importlib import reload

            import tapps_agents.agents.reviewer.scoring as scoring_module
            
            reload(scoring_module)
            scorer = scoring_module.CodeScorer()
            
            test_file = tmp_path / "test.py"
            test_file.write_text("def test(): pass")
            
            # Should still work with basic AST analysis
            result = scorer.score_file(test_file, "def test(): pass")
            assert isinstance(result, dict)
            assert "overall_score" in result
            # Should return valid scores using fallback methods

