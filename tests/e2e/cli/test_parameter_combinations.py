"""
E2E tests for parameter combinations.

Tests various parameter combinations across commands to ensure they work correctly together.
"""

import pytest

from tests.e2e.cli.test_base import CLICommandTestBase
from tests.e2e.cli.validation_helpers import assert_valid_json, assert_success_exit


@pytest.mark.e2e_cli
class TestReviewerParameterCombinations(CLICommandTestBase):
    """Tests for Reviewer Agent parameter combinations."""

    def test_reviewer_review_multiple_files(self):
        """Test reviewer review with multiple files."""
        test_file1 = self.get_test_file("test_file.py")
        test_file2 = self.get_test_file("src/main.py")
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "review", str(test_file1), str(test_file2), "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_reviewer_review_with_pattern(self):
        """Test reviewer review with glob pattern."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "review", "--pattern", "**/*.py", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_reviewer_review_with_max_workers(self):
        """Test reviewer review with max-workers parameter."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "review", str(test_file), "--max-workers", "2", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_reviewer_review_with_fail_under(self):
        """Test reviewer review with fail-under threshold."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "review", str(test_file), "--fail-under", "70", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_reviewer_review_with_output_file(self):
        """Test reviewer review with output file."""
        test_file = self.get_test_file()
        output_file = self.test_project / "review_output.json"
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "review", str(test_file), "--output", str(output_file), "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_reviewer_lint_with_fail_on_issues(self):
        """Test reviewer lint with fail-on-issues flag."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "lint", str(test_file), "--fail-on-issues", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_reviewer_docs_with_mode(self):
        """Test reviewer docs with mode parameter."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "docs", "fastapi", "--mode", "info", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_reviewer_docs_with_page(self):
        """Test reviewer docs with page parameter."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "docs", "pytest", "--page", "2", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_reviewer_docs_with_no_cache(self):
        """Test reviewer docs with no-cache flag."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "docs", "react", "--no-cache", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestPlannerParameterCombinations(CLICommandTestBase):
    """Tests for Planner Agent parameter combinations."""

    def test_planner_plan_with_enhance(self):
        """Test planner plan with enhance flag."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "planner", "plan", "Create user authentication", "--enhance", "--enhance-mode", "full", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_planner_plan_with_no_enhance(self):
        """Test planner plan with no-enhance flag."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "planner", "plan", "Add feature", "--no-enhance", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_planner_create_story_with_epic_and_priority(self):
        """Test planner create-story with epic and priority."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "planner", "create-story", "User login", "--epic", "Authentication", "--priority", "high", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_planner_list_stories_with_filters(self):
        """Test planner list-stories with filters."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "planner", "list-stories", "--epic", "Auth", "--status", "todo", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestImplementerParameterCombinations(CLICommandTestBase):
    """Tests for Implementer Agent parameter combinations."""

    def test_implementer_implement_with_context(self):
        """Test implementer implement with context."""
        test_file = self.get_test_file("new_file.py")
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "implementer", "implement", "Create a calculator class", str(test_file), "--context", "Use FastAPI patterns", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_implementer_implement_with_language(self):
        """Test implementer implement with language parameter."""
        test_file = self.get_test_file("new_file.js")
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "implementer", "implement", "Create a function", str(test_file), "--language", "javascript", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_implementer_refactor_with_format_diff(self):
        """Test implementer refactor with diff format."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "implementer", "refactor", str(test_file), "Extract methods", "--format", "diff"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestTesterParameterCombinations(CLICommandTestBase):
    """Tests for Tester Agent parameter combinations."""

    def test_tester_test_with_integration(self):
        """Test tester test with integration flag."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "tester", "test", str(test_file), "--integration", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_tester_test_with_test_file(self):
        """Test tester test with custom test file."""
        test_file = self.get_test_file()
        test_file_path = self.test_project / "tests" / "test_custom.py"
        test_file_path.parent.mkdir(parents=True, exist_ok=True)
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "tester", "test", str(test_file), "--test-file", str(test_file_path), "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_tester_test_with_focus(self):
        """Test tester test with focus parameter."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "tester", "test", str(test_file), "--focus", "error_handling,edge_cases", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_tester_run_tests_with_path(self):
        """Test tester run-tests with test path."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "tester", "run-tests", "tests/", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_tester_run_tests_with_no_coverage(self):
        """Test tester run-tests with no-coverage flag."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "tester", "run-tests", "--no-coverage", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestAnalystParameterCombinations(CLICommandTestBase):
    """Tests for Analyst Agent parameter combinations."""

    def test_analyst_gather_requirements_with_context(self):
        """Test analyst gather-requirements with context."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "analyst", "gather-requirements", "Build a task management app", "--context", "For a team of 10 developers", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_analyst_stakeholder_analysis_with_stakeholders(self):
        """Test analyst stakeholder-analysis with stakeholders list."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "analyst", "stakeholder-analysis", "E-commerce platform", "--stakeholders", "product-owner", "end-users", "devops-team", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_analyst_tech_research_with_criteria(self):
        """Test analyst tech-research with criteria."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "analyst", "tech-research", "Database for high-traffic app", "--criteria", "scalability", "performance", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestDesignerParameterCombinations(CLICommandTestBase):
    """Tests for Designer Agent parameter combinations."""

    def test_designer_api_design_with_type(self):
        """Test designer api-design with type parameter."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "designer", "api-design", "User management API", "--type", "full", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_designer_data_model_design_with_type(self):
        """Test designer data-model-design with type parameter."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "designer", "data-model-design", "User data model", "--type", "quick", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestImproverParameterCombinations(CLICommandTestBase):
    """Tests for Improver Agent parameter combinations."""

    def test_improver_refactor_with_instruction(self):
        """Test improver refactor with instruction parameter."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "improver", "refactor", str(test_file), "--instruction", "Extract common patterns", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_improver_optimize_with_type(self):
        """Test improver optimize with type parameter."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "improver", "optimize", str(test_file), "--type", "memory", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_improver_optimize_with_type_both(self):
        """Test improver optimize with type both."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "improver", "optimize", str(test_file), "--type", "both", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestOpsParameterCombinations(CLICommandTestBase):
    """Tests for Ops Agent parameter combinations."""

    def test_ops_check_compliance_with_standard(self):
        """Test ops check-compliance with standard parameter."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "ops", "check-compliance", "--standard", "GDPR", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_ops_audit_security_with_target(self):
        """Test ops audit-security with target parameter."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "ops", "audit-security", str(self.test_project), "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]
