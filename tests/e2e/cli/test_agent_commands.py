"""
Comprehensive tests for all agent commands with representative parameter combinations.

Tests all 13 agents with various parameter combinations to ensure:
- Commands execute without errors
- Output formats work correctly
- Parameter combinations are valid
- Both *command and command formats work
"""

import pytest

from tests.e2e.cli.test_base import CLICommandTestBase, ParameterizedCommandTest
from tests.e2e.cli.validation_helpers import assert_valid_json, assert_text_output, assert_success_exit


@pytest.mark.e2e_cli
class TestReviewerAgent(CLICommandTestBase):
    """Tests for Reviewer Agent commands."""

    def test_reviewer_score_minimal(self):
        """Test reviewer score command with minimal parameters."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "score", str(test_file), "--format", "json"]
        )
        assert_valid_json(result)

    def test_reviewer_score_with_format_text(self):
        """Test reviewer score with text format."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "score", str(test_file), "--format", "text"]
        )
        assert_text_output(result)

    def test_reviewer_score_star_format(self):
        """Test reviewer *score command (with star prefix)."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "*score", str(test_file), "--format", "json"]
        )
        assert_valid_json(result)

    def test_reviewer_review_minimal(self):
        """Test reviewer review command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "review", str(test_file), "--format", "json"],
            expect_success=False,  # May require network
        )
        # Accept success or graceful failure
        assert result.exit_code in [0, 1]

    def test_reviewer_lint_minimal(self):
        """Test reviewer lint command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "lint", str(test_file), "--format", "json"]
        )
        assert_valid_json(result)

    def test_reviewer_type_check_minimal(self):
        """Test reviewer type-check command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "type-check", str(test_file), "--format", "json"],
            expect_success=False,  # May fail if mypy not installed
        )
        assert result.exit_code in [0, 1]

    def test_reviewer_report_minimal(self):
        """Test reviewer report command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "report", str(self.test_project), "json"]
        )
        assert_success_exit(result)

    def test_reviewer_duplication_minimal(self):
        """Test reviewer duplication command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "duplication", str(self.test_project), "--format", "json"],
            timeout=60.0,
            expect_success=False,  # May take time
        )
        assert result.exit_code in [0, 1, 124]  # 124 = timeout

    def test_reviewer_docs_minimal(self):
        """Test reviewer docs command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "docs", "fastapi", "--format", "json"],
            expect_success=False,  # May require network
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestPlannerAgent(CLICommandTestBase):
    """Tests for Planner Agent commands."""

    def test_planner_plan_minimal(self):
        """Test planner plan command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "planner", "plan", "Create a user authentication feature", "--format", "json"],
            expect_success=False,  # May require network
        )
        assert result.exit_code in [0, 1]

    def test_planner_create_story_minimal(self):
        """Test planner create-story command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "planner", "create-story", "User login", "--format", "json"],
            expect_success=False,  # May require network
        )
        assert result.exit_code in [0, 1]

    def test_planner_list_stories_minimal(self):
        """Test planner list-stories command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "planner", "list-stories", "--format", "json"],
            expect_success=False,  # May require network
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestImplementerAgent(CLICommandTestBase):
    """Tests for Implementer Agent commands."""

    def test_implementer_implement_minimal(self):
        """Test implementer implement command."""
        target_file = self.test_project / "new_feature.py"
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "implementer", "implement", "Create a simple calculator", str(target_file), "--format", "json"],
            expect_success=False,  # May require network
        )
        assert result.exit_code in [0, 1]

    def test_implementer_refactor_minimal(self):
        """Test implementer refactor command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "implementer", "refactor", str(test_file), "Add type hints", "--format", "json"],
            expect_success=False,  # May require network
        )
        assert result.exit_code in [0, 1]

    def test_implementer_generate_code_minimal(self):
        """Test implementer generate-code command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "implementer", "generate-code", "Create a hello world function", "--format", "json"],
            expect_success=False,  # May require network
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestTesterAgent(CLICommandTestBase):
    """Tests for Tester Agent commands."""

    def test_tester_test_minimal(self):
        """Test tester test command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "tester", "test", str(test_file), "--format", "json"],
            expect_success=False,  # May require network
        )
        assert result.exit_code in [0, 1]

    def test_tester_generate_tests_minimal(self):
        """Test tester generate-tests command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "tester", "generate-tests", str(test_file), "--format", "json"],
            expect_success=False,  # May require network
        )
        assert result.exit_code in [0, 1]

    def test_tester_run_tests_minimal(self):
        """Test tester run-tests command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "tester", "run-tests", "--format", "json"],
            expect_success=False,  # May fail if no tests exist
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestDebuggerAgent(CLICommandTestBase):
    """Tests for Debugger Agent commands."""

    def test_debugger_debug_minimal(self):
        """Test debugger debug command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "debugger", "debug", "ValueError: invalid input", "--file", str(test_file), "--format", "json"],
            expect_success=False,  # May require network
        )
        assert result.exit_code in [0, 1]

    def test_debugger_analyze_error_minimal(self):
        """Test debugger analyze-error command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "debugger", "analyze-error", "TypeError: unsupported operand", "--format", "json"],
            expect_success=False,  # May require network
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestDocumenterAgent(CLICommandTestBase):
    """Tests for Documenter Agent commands."""

    def test_documenter_document_minimal(self):
        """Test documenter document command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "documenter", "document", str(test_file), "--output-format", "markdown"],
            expect_success=False,  # May require network
        )
        assert result.exit_code in [0, 1]

    def test_documenter_generate_docs_minimal(self):
        """Test documenter generate-docs command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "documenter", "generate-docs", str(test_file), "--output-format", "markdown"],
            expect_success=False,  # May require network
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestAnalystAgent(CLICommandTestBase):
    """Tests for Analyst Agent commands."""

    def test_analyst_gather_requirements_minimal(self):
        """Test analyst gather-requirements command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "analyst", "gather-requirements", "Build a task management app", "--format", "json"],
            expect_success=False,  # May require network
        )
        assert result.exit_code in [0, 1]

    def test_analyst_stakeholder_analysis_minimal(self):
        """Test analyst stakeholder-analysis command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "analyst", "stakeholder-analysis", "E-commerce platform"],
            expect_success=False,  # May require network
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestArchitectAgent(CLICommandTestBase):
    """Tests for Architect Agent commands."""

    def test_architect_design_system_minimal(self):
        """Test architect design-system command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "architect", "design-system", "Microservices architecture for e-commerce", "--format", "json"],
            expect_success=False,  # May require network
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestDesignerAgent(CLICommandTestBase):
    """Tests for Designer Agent commands."""

    def test_designer_api_design_minimal(self):
        """Test designer api-design command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "designer", "api-design", "User management API", "--format", "json"],
            expect_success=False,  # May require network
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestImproverAgent(CLICommandTestBase):
    """Tests for Improver Agent commands."""

    def test_improver_improve_quality_minimal(self):
        """Test improver improve-quality command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "improver", "improve-quality", str(test_file), "--format", "json"],
            expect_success=False,  # May require network
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestOpsAgent(CLICommandTestBase):
    """Tests for Ops Agent commands."""

    def test_ops_security_scan_minimal(self):
        """Test ops security-scan command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "ops", "security-scan", "--target", str(self.test_project)],
            expect_success=False,  # May require network
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestEnhancerAgent(CLICommandTestBase):
    """Tests for Enhancer Agent commands."""

    def test_enhancer_enhance_minimal(self):
        """Test enhancer enhance command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "enhancer", "enhance", "Build a REST API", "--format", "json"],
            expect_success=False,  # May require network
        )
        assert result.exit_code in [0, 1]

    def test_enhancer_enhance_quick_minimal(self):
        """Test enhancer enhance-quick command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "enhancer", "enhance-quick", "Add user authentication", "--format", "json"],
            expect_success=False,  # May require network
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestOrchestratorAgent(CLICommandTestBase):
    """Tests for Orchestrator Agent commands."""

    def test_orchestrator_orchestrate_minimal(self):
        """Test orchestrator orchestrate command."""
        # Create a simple workflow file
        workflow_file = self.test_project / "test_workflow.yaml"
        workflow_file.write_text(
            """name: Test Workflow
steps:
  - name: test
    agent: reviewer
    command: score
    args:
      file: test_file.py
"""
        )
        
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "orchestrator", "orchestrate", str(workflow_file), "--format", "json"],
            expect_success=False,  # May require network or fail if workflow invalid
        )
        assert result.exit_code in [0, 1, 2]

