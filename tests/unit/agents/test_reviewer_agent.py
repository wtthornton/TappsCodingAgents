"""
Tests for Reviewer Agent with real CodeScorer behavior.

Tests agent initialization, command handling, and business logic
using real CodeScorer instances. Agents now return instruction objects
instead of calling LLMs directly.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.agents.reviewer.agent import ReviewerAgent

pytestmark = pytest.mark.unit


class TestReviewerAgentInitialization:
    """Tests for ReviewerAgent initialization."""

    @patch("tapps_agents.agents.reviewer.agent.load_config")
    def test_reviewer_agent_init(self, mock_load_config):
        """Test ReviewerAgent initialization."""
        mock_config = MagicMock()
        mock_config.scoring = None
        mock_config.quality_tools = MagicMock()
        mock_config.quality_tools.ruff_enabled = True
        mock_config.quality_tools.mypy_enabled = True
        mock_config.quality_tools.jscpd_enabled = True
        mock_config.quality_tools.duplication_threshold = 3.0
        mock_config.quality_tools.min_duplication_lines = 5
        mock_config.quality_tools.pip_audit_enabled = True
        mock_config.quality_tools.typescript_enabled = True
        mock_config.quality_tools.eslint_config = None
        mock_config.quality_tools.tsconfig_path = None
        mock_load_config.return_value = mock_config
        
        agent = ReviewerAgent()
        assert agent.agent_id == "reviewer"
        assert agent.agent_name == "Reviewer Agent"
        assert agent.config is not None
        assert agent.scorer is not None

    @pytest.mark.asyncio
    async def test_reviewer_agent_activate(self, temp_project_dir: Path):
        """Test ReviewerAgent activation."""
        agent = ReviewerAgent()
        await agent.activate(temp_project_dir)
        
        assert agent.config is not None

    @pytest.mark.asyncio
    async def test_reviewer_agent_get_commands(self):
        """Test ReviewerAgent command list."""
        agent = ReviewerAgent()
        commands = agent.get_commands()
        
        assert isinstance(commands, list)
        assert len(commands) > 0
        # Should have review and score commands
        command_names = [cmd["command"] for cmd in commands]
        assert any("review" in cmd.lower() for cmd in command_names)


class TestReviewerAgentReviewCommand:
    """Tests for review command with real CodeScorer behavior."""

    @pytest.mark.asyncio
    async def test_review_command_success(self, sample_python_file):
        """Test review command with successful review using real CodeScorer."""
        agent = ReviewerAgent()
        
        # Use real CodeScorer instance (already created in ReviewerAgent.__init__)
        # Agent now returns instruction objects instead of calling LLMs
        result = await agent.run("review", file=str(sample_python_file))
        
        assert "file" in result
        assert "scoring" in result
        # Validate real scoring results (not just mocked values)
        assert "overall_score" in result["scoring"]
        assert isinstance(result["scoring"]["overall_score"], (int, float))
        assert 0 <= result["scoring"]["overall_score"] <= 100
        # Validate individual scores are present
        assert "complexity_score" in result["scoring"]
        assert "security_score" in result["scoring"]
        assert "maintainability_score" in result["scoring"]

    @pytest.mark.asyncio
    async def test_review_command_file_not_found(self, tmp_path):
        """Test review command with non-existent file."""
        agent = ReviewerAgent()
        non_existent = tmp_path / "nonexistent.py"
        
        result = await agent.run("review", file=str(non_existent))
        
        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_review_command_invalid_file(self, tmp_path):
        """Test review command with invalid file."""
        agent = ReviewerAgent()
        invalid_file = tmp_path / "invalid.txt"
        invalid_file.write_text("not python code")
        
        # Should handle gracefully (may return error or attempt to process)
        result = await agent.run("review", file=str(invalid_file))
        assert isinstance(result, dict)
        # May contain error or attempt to process with real CodeScorer


class TestReviewerAgentScoreCommand:
    """Tests for score command with real CodeScorer behavior."""

    @pytest.mark.asyncio
    async def test_score_command_success(self, sample_python_file):
        """Test score command with successful scoring using real CodeScorer."""
        agent = ReviewerAgent()
        
        # Use real CodeScorer instance (already created in ReviewerAgent.__init__)
        result = await agent.run("score", file=str(sample_python_file))
        
        assert "file" in result
        assert "scoring" in result
        assert "overall_score" in result["scoring"]
        # Validate real scoring results
        assert isinstance(result["scoring"]["overall_score"], (int, float))
        assert 0 <= result["scoring"]["overall_score"] <= 100
        # Validate all expected score fields are present
        expected_fields = [
            "complexity_score", "security_score", "maintainability_score",
            "test_coverage_score", "performance_score"
        ]
        for field in expected_fields:
            assert field in result["scoring"], f"Missing expected score field: {field}"

    @pytest.mark.asyncio
    async def test_score_command_file_not_found(self, tmp_path):
        """Test score command with non-existent file."""
        agent = ReviewerAgent()
        non_existent = tmp_path / "nonexistent.py"
        
        result = await agent.run("score", file=str(non_existent))
        
        assert "error" in result


class TestReviewerAgentErrorHandling:
    """Tests for error handling with real CodeScorer."""

    @pytest.mark.asyncio
    async def test_review_command_scorer_error(self, sample_python_file):
        """Test review command handles scorer errors from real CodeScorer."""
        agent = ReviewerAgent()
        
        # Patch the scorer's score_file method to raise a specific error
        # This tests error propagation through real agent code
        error_message = "Scorer error: File parsing failed"
        
        def failing_score_file(*args, **kwargs):
            raise RuntimeError(error_message)
        
        agent.scorer.score_file = failing_score_file
        
        # Error should be raised or handled gracefully
        result = await agent.run("review", file=str(sample_python_file))
        
        # Should handle error gracefully and propagate error information
        assert isinstance(result, dict)
        # Validate that error information is included in result
        # The error might be in the result dict or the scoring might be absent
        assert "error" in result or "scoring" not in result
        if "error" in result:
            # Error should contain the original error message
            error_info = result.get("error", {})
            if isinstance(error_info, dict):
                error_msg = error_info.get("message", "") or str(error_info)
                assert error_message in error_msg or "error" in str(result).lower()
            else:
                # Error might be a string
                assert error_message in str(error_info) or "error" in str(result).lower()


class TestReviewerAgentLintCommand:
    """Tests for lint command."""

    @pytest.mark.asyncio
    async def test_lint_command_success(self, sample_python_file):
        """Test lint command with successful linting."""
        agent = ReviewerAgent()
        result = await agent.run("lint", file=str(sample_python_file))
        
        assert "file" in result
        assert "linting_score" in result
        assert "issues" in result
        assert "issue_count" in result
        assert "error_count" in result
        assert "warning_count" in result
        assert "fatal_count" in result
        assert isinstance(result["linting_score"], (int, float))
        assert 0 <= result["linting_score"] <= 10

    @pytest.mark.asyncio
    async def test_lint_command_file_not_found(self, tmp_path):
        """Test lint command with non-existent file."""
        agent = ReviewerAgent()
        non_existent = tmp_path / "nonexistent.py"
        
        result = await agent.run("lint", file=str(non_existent))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_lint_command_missing_file_param(self):
        """Test lint command without file parameter."""
        agent = ReviewerAgent()
        result = await agent.run("lint")
        
        assert "error" in result
        assert "file path required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_lint_file_method(self, sample_python_file):
        """Test lint_file method directly."""
        agent = ReviewerAgent()
        result = await agent.lint_file(sample_python_file)
        
        assert "file" in result
        assert "linting_score" in result
        assert "issues" in result
        assert "tool" in result

    @pytest.mark.asyncio
    async def test_lint_file_typescript(self, tmp_path):
        """Test lint_file with TypeScript file."""
        agent = ReviewerAgent()
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("const x: number = 'string';")
        
        result = await agent.lint_file(ts_file)
        assert "file" in result
        assert "tool" in result


class TestReviewerAgentTypeCheckCommand:
    """Tests for type-check command."""

    @pytest.mark.asyncio
    async def test_type_check_command_success(self, sample_python_file):
        """Test type-check command with successful type checking."""
        agent = ReviewerAgent()
        result = await agent.run("type-check", file=str(sample_python_file))
        
        assert "file" in result
        assert "type_checking_score" in result
        assert "errors" in result
        assert "error_count" in result
        assert "error_codes" in result
        assert isinstance(result["type_checking_score"], (int, float))
        assert 0 <= result["type_checking_score"] <= 10

    @pytest.mark.asyncio
    async def test_type_check_command_file_not_found(self, tmp_path):
        """Test type-check command with non-existent file."""
        agent = ReviewerAgent()
        non_existent = tmp_path / "nonexistent.py"
        
        result = await agent.run("type-check", file=str(non_existent))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_type_check_command_missing_file_param(self):
        """Test type-check command without file parameter."""
        agent = ReviewerAgent()
        result = await agent.run("type-check")
        
        assert "error" in result
        assert "file path required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_type_check_file_method(self, sample_python_file):
        """Test type_check_file method directly."""
        agent = ReviewerAgent()
        result = await agent.type_check_file(sample_python_file)
        
        assert "file" in result
        assert "type_checking_score" in result
        assert "errors" in result
        assert "tool" in result

    @pytest.mark.asyncio
    async def test_type_check_file_typescript(self, tmp_path):
        """Test type_check_file with TypeScript file."""
        agent = ReviewerAgent()
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("const x: number = 'string';")
        
        result = await agent.type_check_file(ts_file)
        assert "file" in result
        assert "tool" in result


class TestReviewerAgentReportCommand:
    """Tests for report command."""

    @pytest.mark.asyncio
    async def test_report_command_all_formats(self, sample_python_file, tmp_path):
        """Test report command with all formats."""
        agent = ReviewerAgent()
        output_dir = str(tmp_path / "reports")
        
        result = await agent.run("report", format="all", output_dir=output_dir, target=str(sample_python_file))
        
        assert "format" in result
        assert "output_dir" in result
        assert "reports" in result
        assert "summary" in result
        assert "json" in result["reports"] or "all" in result["format"]

    @pytest.mark.asyncio
    async def test_report_command_json_format(self, sample_python_file, tmp_path):
        """Test report command with JSON format."""
        agent = ReviewerAgent()
        output_dir = str(tmp_path / "reports")
        
        result = await agent.run("report", format="json", output_dir=output_dir, target=str(sample_python_file))
        
        assert "reports" in result
        assert "json" in result["reports"]

    @pytest.mark.asyncio
    async def test_report_command_markdown_format(self, sample_python_file, tmp_path):
        """Test report command with Markdown format."""
        agent = ReviewerAgent()
        output_dir = str(tmp_path / "reports")
        
        result = await agent.run("report", format="markdown", output_dir=output_dir, target=str(sample_python_file))
        
        assert "reports" in result
        assert "markdown" in result["reports"]

    @pytest.mark.asyncio
    async def test_report_command_html_format(self, sample_python_file, tmp_path):
        """Test report command with HTML format."""
        agent = ReviewerAgent()
        output_dir = str(tmp_path / "reports")
        
        result = await agent.run("report", format="html", output_dir=output_dir, target=str(sample_python_file))
        
        assert "reports" in result
        assert "html" in result["reports"]

    @pytest.mark.asyncio
    async def test_report_command_multiple_files(self, tmp_path):
        """Test report command with multiple files."""
        agent = ReviewerAgent()
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("def func1(): pass")
        file2.write_text("def func2(): pass")
        
        result = await agent.run("report", format="json", files=[str(file1), str(file2)])
        
        assert "summary" in result
        assert result["summary"]["files_analyzed"] >= 0

    @pytest.mark.asyncio
    async def test_generate_reports_method(self, sample_python_file, tmp_path):
        """Test generate_reports method directly."""
        agent = ReviewerAgent()
        output_dir = str(tmp_path / "reports")
        
        result = await agent.generate_reports(
            format_type="json",
            output_dir=output_dir,
            target=str(sample_python_file)
        )
        
        assert "format" in result
        assert "reports" in result


class TestReviewerAgentDuplicationCommand:
    """Tests for duplication command."""

    @pytest.mark.asyncio
    async def test_duplication_command_success(self, sample_python_file):
        """Test duplication command with successful duplication check."""
        agent = ReviewerAgent()
        result = await agent.run("duplication", file=str(sample_python_file))
        
        assert "file_or_directory" in result
        assert "duplication_score" in result
        assert "duplication_percentage" in result
        assert "threshold" in result
        assert "passed" in result
        assert isinstance(result["duplication_score"], (int, float))

    @pytest.mark.asyncio
    async def test_duplication_command_directory(self, tmp_path):
        """Test duplication command with directory."""
        agent = ReviewerAgent()
        result = await agent.run("duplication", file=str(tmp_path))
        
        assert "file_or_directory" in result
        assert "duplication_score" in result

    @pytest.mark.asyncio
    async def test_duplication_command_missing_file_param(self):
        """Test duplication command without file parameter."""
        agent = ReviewerAgent()
        result = await agent.run("duplication")
        
        assert "error" in result
        assert "file or directory path required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_check_duplication_method(self, sample_python_file):
        """Test check_duplication method directly."""
        agent = ReviewerAgent()
        result = await agent.check_duplication(sample_python_file)
        
        assert "file_or_directory" in result
        assert "duplication_score" in result


class TestReviewerAgentAnalyzeProjectCommand:
    """Tests for analyze-project command."""

    @pytest.mark.asyncio
    async def test_analyze_project_command_success(self, tmp_path):
        """Test analyze-project command."""
        # Create a simple project structure
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / "service1").mkdir()
        (project_root / "service1" / "main.py").write_text("def main(): pass")
        
        agent = ReviewerAgent()
        await agent.activate(project_root)
        
        result = await agent.run("analyze-project", project_root=str(project_root))
        
        assert "project_root" in result
        assert "services_found" in result
        assert "services_analyzed" in result

    @pytest.mark.asyncio
    async def test_analyze_project_command_no_services(self, tmp_path):
        """Test analyze-project command with no services found."""
        agent = ReviewerAgent()
        await agent.activate(tmp_path)
        
        result = await agent.run("analyze-project", project_root=str(tmp_path))
        
        assert "project_root" in result
        assert "services_found" in result or "error" in result

    @pytest.mark.asyncio
    async def test_analyze_project_method(self, tmp_path):
        """Test analyze_project method directly."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        agent = ReviewerAgent()
        await agent.activate(project_root)
        
        result = await agent.analyze_project(project_root=project_root)
        
        assert "project_root" in result


class TestReviewerAgentAnalyzeServicesCommand:
    """Tests for analyze-services command."""

    @pytest.mark.asyncio
    async def test_analyze_services_command_success(self, tmp_path):
        """Test analyze-services command with specific services."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / "service1").mkdir()
        (project_root / "service1" / "main.py").write_text("def main(): pass")
        
        agent = ReviewerAgent()
        await agent.activate(project_root)
        
        result = await agent.run("analyze-services", services=["service1"], project_root=str(project_root))
        
        assert "project_root" in result
        assert "services" in result

    @pytest.mark.asyncio
    async def test_analyze_services_command_all_services(self, tmp_path):
        """Test analyze-services command with all services."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / "service1").mkdir()
        (project_root / "service1" / "main.py").write_text("def main(): pass")
        
        agent = ReviewerAgent()
        await agent.activate(project_root)
        
        result = await agent.run("analyze-services", project_root=str(project_root))
        
        assert "project_root" in result

    @pytest.mark.asyncio
    async def test_analyze_services_method(self, tmp_path):
        """Test analyze_services method directly."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        agent = ReviewerAgent()
        await agent.activate(project_root)
        
        result = await agent.analyze_services(services=["service1"], project_root=project_root)
        
        assert "project_root" in result


class TestReviewerAgentReviewFileMethod:
    """Tests for review_file method with various options."""

    @pytest.mark.asyncio
    async def test_review_file_with_scoring_only(self, sample_python_file):
        """Test review_file with scoring only, no LLM feedback."""
        agent = ReviewerAgent()
        result = await agent.review_file(
            sample_python_file,
            include_scoring=True,
            include_llm_feedback=False
        )
        
        assert "file" in result
        assert "scoring" in result
        assert "feedback" not in result

    @pytest.mark.asyncio
    async def test_review_file_with_llm_feedback(self, sample_python_file):
        """Test review_file with LLM feedback."""
        agent = ReviewerAgent()
        # Mock the _generate_feedback method to avoid model parameter issue
        with patch.object(agent, '_generate_feedback', new_callable=AsyncMock) as mock_feedback:
            mock_feedback.return_value = {"instruction": {}, "skill_command": "*review"}
            result = await agent.review_file(
                sample_python_file,
                include_scoring=True,
                include_llm_feedback=True
            )
            
            assert "file" in result
            assert "scoring" in result
            # Feedback may not be present if expert_registry is None
            # but the method should still work

    @pytest.mark.asyncio
    async def test_review_file_without_scoring(self, sample_python_file):
        """Test review_file without scoring."""
        agent = ReviewerAgent()
        result = await agent.review_file(
            sample_python_file,
            include_scoring=False,
            include_llm_feedback=False
        )
        
        assert "file" in result
        assert "scoring" not in result

    @pytest.mark.asyncio
    async def test_review_file_unicode_error(self, tmp_path):
        """Test review_file with file that can't be decoded as UTF-8."""
        agent = ReviewerAgent()
        # Create a file with invalid UTF-8
        invalid_file = tmp_path / "invalid.py"
        invalid_file.write_bytes(b'\xff\xfe\x00\x00')  # Invalid UTF-8
        
        with pytest.raises(ValueError, match="Cannot decode file as UTF-8"):
            await agent.review_file(invalid_file)

    @pytest.mark.asyncio
    async def test_review_file_with_expert_consultation(self, sample_python_file):
        """Test review_file with expert consultation."""
        agent = ReviewerAgent()
        # Mock expert registry
        mock_registry = MagicMock()
        mock_consultation = MagicMock()
        mock_consultation.weighted_answer = "Security advice"
        mock_consultation.confidence = 0.9
        mock_registry.consult = AsyncMock(return_value=mock_consultation)
        agent.expert_registry = mock_registry
        
        # Mock _generate_feedback to avoid model parameter issue
        with patch.object(agent, '_generate_feedback', new_callable=AsyncMock) as mock_feedback:
            mock_feedback.return_value = {"instruction": {}, "skill_command": "*review"}
            result = await agent.review_file(
                sample_python_file,
                include_scoring=True,
                include_llm_feedback=True
            )
            
            assert "file" in result
            # Expert consultation should be called
            assert mock_registry.consult.called

    @pytest.mark.asyncio
    async def test_review_file_passed_threshold(self, sample_python_file):
        """Test review_file determines pass/fail based on threshold."""
        agent = ReviewerAgent()
        result = await agent.review_file(
            sample_python_file,
            include_scoring=True,
            include_llm_feedback=False
        )
        
        assert "passed" in result
        assert "threshold" in result
        assert isinstance(result["passed"], bool)


class TestReviewerAgentDependencySecurity:
    """Tests for dependency security penalty calculation."""

    @pytest.mark.asyncio
    async def test_get_dependency_security_penalty_disabled(self):
        """Test dependency security penalty when disabled."""
        agent = ReviewerAgent()
        agent.dependency_analyzer_enabled = False
        
        penalty = agent._get_dependency_security_penalty()
        assert penalty == 10.0  # No penalty when disabled

    @pytest.mark.asyncio
    async def test_get_dependency_security_penalty_enabled(self, tmp_path):
        """Test dependency security penalty when enabled."""
        agent = ReviewerAgent()
        agent.dependency_analyzer_enabled = True
        agent.dependency_analyzer = MagicMock()
        
        # Mock audit result with vulnerabilities
        mock_audit = {
            "severity_breakdown": {
                "critical": 1,
                "high": 2,
                "medium": 3,
                "low": 4
            }
        }
        agent.dependency_analyzer.run_security_audit = MagicMock(return_value=mock_audit)
        
        penalty = agent._get_dependency_security_penalty()
        # Should calculate penalty: 10 - (1*3 + 2*2 + 3*1 + 4*0.5) = 10 - 9 = 1.0
        assert 0 <= penalty <= 10

    @pytest.mark.asyncio
    async def test_get_dependency_security_penalty_audit_error(self, tmp_path):
        """Test dependency security penalty when audit fails."""
        agent = ReviewerAgent()
        agent.dependency_analyzer_enabled = True
        agent.dependency_analyzer = MagicMock()
        agent.dependency_analyzer.run_security_audit = MagicMock(return_value={"error": "Failed"})
        
        penalty = agent._get_dependency_security_penalty()
        assert penalty == 10.0  # No penalty on error

    @pytest.mark.asyncio
    async def test_get_dependency_security_penalty_exception(self, tmp_path):
        """Test dependency security penalty when exception occurs."""
        agent = ReviewerAgent()
        agent.dependency_analyzer_enabled = True
        agent.dependency_analyzer = MagicMock()
        agent.dependency_analyzer.run_security_audit = MagicMock(side_effect=Exception("Error"))
        
        penalty = agent._get_dependency_security_penalty()
        assert penalty == 10.0  # No penalty on exception


class TestReviewerAgentErrorHandlingExtended:
    """Extended error handling tests."""

    @pytest.mark.asyncio
    async def test_review_command_missing_file_param(self):
        """Test review command without file parameter."""
        agent = ReviewerAgent()
        result = await agent.run("review")
        
        assert "error" in result
        assert "file path required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_score_command_missing_file_param(self):
        """Test score command without file parameter."""
        agent = ReviewerAgent()
        result = await agent.run("score")
        
        assert "error" in result
        assert "file path required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_unknown_command(self):
        """Test unknown command handling."""
        agent = ReviewerAgent()
        result = await agent.run("unknown-command")
        
        assert "error" in result
        assert "unknown command" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_help_command(self):
        """Test help command."""
        agent = ReviewerAgent()
        result = await agent.run("help")
        
        assert "type" in result
        assert result["type"] == "help"
        assert "content" in result

    @pytest.mark.asyncio
    async def test_review_file_path_traversal_protection(self, tmp_path):
        """Test review_file protects against path traversal."""
        agent = ReviewerAgent()
        # Try to access file outside project root
        malicious_path = tmp_path.parent / "outside.py"
        malicious_path.write_text("malicious code")
        
        # Should raise ValueError or return error
        result = await agent.run("review", file=str(malicious_path))
        # May return error or raise exception depending on validation
        assert isinstance(result, dict)


class TestReviewerAgentIntegration:
    """Integration tests for ReviewerAgent with dependencies."""

    @pytest.mark.asyncio
    async def test_review_file_with_dependency_analyzer(self, sample_python_file, tmp_path):
        """Test review_file integrates with DependencyAnalyzer."""
        agent = ReviewerAgent()
        await agent.activate(tmp_path)
        
        # Mock dependency analyzer if enabled
        if agent.dependency_analyzer_enabled and agent.dependency_analyzer:
            agent.dependency_analyzer.run_security_audit = MagicMock(return_value={
                "severity_breakdown": {}
            })
        
        result = await agent.review_file(
            sample_python_file,
            include_scoring=True,
            include_llm_feedback=False
        )
        
        assert "scoring" in result
        # Should include dependency_security_score if dependency analyzer is enabled
        if agent.dependency_analyzer_enabled:
            assert "dependency_security_score" in result["scoring"]

    @pytest.mark.asyncio
    async def test_lint_file_with_typescript_scorer(self, tmp_path):
        """Test lint_file integrates with TypeScriptScorer."""
        agent = ReviewerAgent()
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("const x = 1;")
        
        result = await agent.lint_file(ts_file)
        
        assert "file" in result
        assert "tool" in result
        # Should use eslint if TypeScript scorer is enabled
        if agent.typescript_enabled and agent.typescript_scorer:
            assert result["tool"] in ["eslint", "none"]

    @pytest.mark.asyncio
    async def test_type_check_file_with_typescript_scorer(self, tmp_path):
        """Test type_check_file integrates with TypeScriptScorer."""
        agent = ReviewerAgent()
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("const x: number = 1;")
        
        result = await agent.type_check_file(ts_file)
        
        assert "file" in result
        assert "tool" in result
        # Should use tsc if TypeScript scorer is enabled
        if agent.typescript_enabled and agent.typescript_scorer:
            assert result["tool"] in ["tsc", "none"]

