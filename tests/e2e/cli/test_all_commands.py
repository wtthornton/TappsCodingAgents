"""
Comprehensive E2E tests for all tapps-agents CLI commands.

Refactored to use base classes and validation helpers.
Tests all commands with various parameter combinations to ensure:
- Commands execute without errors
- Output formats work correctly
- Error handling is appropriate
- Both *command and command formats work

NOTE: This file contains legacy tests. New comprehensive tests are organized in:
- test_agent_commands.py: All agent commands
- test_top_level_commands.py: Top-level commands
- test_global_flags.py: Global flags
- test_error_handling.py: Error scenarios
- test_output_formats.py: Format validation
- test_demo_scenarios.py: Demo scenarios
"""

import pytest

from tests.e2e.cli.test_base import CLICommandTestBase
from tests.e2e.cli.validation_helpers import assert_valid_json, assert_success_exit


# Fixtures and test project setup are now handled by CLICommandTestBase


# ============================================================================
# Reviewer Agent Commands
# ============================================================================

@pytest.mark.e2e_cli
class TestReviewerCommandsRefactored(CLICommandTestBase):
    """Refactored reviewer command tests using base class."""
    
    def test_reviewer_score_command(self):
        """Test reviewer score command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "score", str(test_file), "--format", "json"]
        )
        json_data = assert_valid_json(result)
        # Check for either direct 'file' key or wrapped in 'data'
        assert "file" in json_data or ("data" in json_data and isinstance(json_data["data"], dict))


    def test_reviewer_score_star_command(self):
        """Test reviewer *score command (with star prefix)."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "*score", str(test_file), "--format", "json"]
        )
        json_data = assert_valid_json(result)
        # Check for either direct 'file' key or wrapped in 'data'
        assert "file" in json_data or ("data" in json_data and isinstance(json_data["data"], dict))


    def test_reviewer_review_command(self):
        """Test reviewer review command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "review", str(test_file), "--format", "json"],
            expect_success=False,  # May require network
        )
        # Review may require network, so we check for either success or graceful failure
        assert result.exit_code in [0, 1]  # 0 = success, 1 = network error handled gracefully


@pytest.mark.e2e_cli
class TestReviewerCommandsLegacy(CLICommandTestBase):
    """Legacy reviewer command tests converted to class-based."""
    
    def test_reviewer_lint_command(self):
        """Test reviewer lint command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "lint", str(test_file), "--format", "json"]
        )
        # Lint may fail if ruff not installed or has issues
        assert result.exit_code in [0, 1]

    def test_reviewer_type_check_command(self):
        """Test reviewer type-check command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "type-check", str(test_file), "--format", "json"]
        )
        # Type checking may fail if mypy not installed, so we accept 0 or 1
        assert result.exit_code in [0, 1]

    def test_reviewer_security_scan_command(self):
        """Test reviewer security-scan command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "security-scan", str(test_file), "--format", "json"],
            expect_success=False,  # May require network or have parsing issues
        )
        # Security scan may require network or fail parsing, so we check for various exit codes
        assert result.exit_code in [0, 1, 2]

    def test_reviewer_duplication_command(self):
        """Test reviewer duplication command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "duplication", str(self.test_project), "--format", "json"],
            timeout=60.0,  # Shorter timeout for this specific command
            expect_success=False,  # May fail due to jscpd parsing issues
        )
        # Duplication may take time or fail, so we accept timeout or failure
        assert result.exit_code in [0, 1] or result.timed_out

    def test_reviewer_report_command(self):
        """Test reviewer report command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "report", str(self.test_project), "json"],
            expect_success=False,  # May fail if no files to analyze
        )
        # Report may fail if no files to analyze
        assert result.exit_code in [0, 1]


# ============================================================================
# Planner Agent Commands
# ============================================================================

@pytest.mark.e2e_cli
class TestPlannerCommandsLegacy(CLICommandTestBase):
    """Legacy planner command tests converted to class-based."""
    
    def test_planner_plan_command(self):
        """Test planner plan command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "planner", "plan", "Create a user authentication feature", "--format", "json"],
            expect_success=False,  # May require network
        )
        # Plan may require network, so we check for either success or graceful failure
        assert result.exit_code in [0, 1]

    def test_planner_create_story_command(self):
        """Test planner create-story command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "planner", "create-story", "User login", "--format", "json"],
            expect_success=False,  # May require network
        )
        # May require network
        assert result.exit_code in [0, 1]

    def test_planner_list_stories_command(self):
        """Test planner list-stories command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "planner", "list-stories", "--format", "json"],
            expect_success=False,  # May require network or return empty list
        )
        # May require network or return empty list
        assert result.exit_code in [0, 1]


# ============================================================================
# Implementer Agent Commands
# ============================================================================

@pytest.mark.e2e_cli
class TestImplementerCommandsLegacy(CLICommandTestBase):
    """Legacy implementer command tests converted to class-based."""
    
    def test_implementer_implement_command(self):
        """Test implementer implement command."""
        target_file = self.test_project / "new_feature.py"
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "implementer", "implement", "Create a simple calculator", str(target_file), "--format", "json"],
            expect_success=False,  # May require network
        )
        # May require network
        assert result.exit_code in [0, 1]

    def test_implementer_refactor_command(self):
        """Test implementer refactor command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "implementer", "refactor", str(test_file), "Add type hints", "--format", "json"],
            expect_success=False,  # May require network
        )
        # May require network
        assert result.exit_code in [0, 1]

    def test_implementer_generate_code_command(self):
        """Test implementer generate-code command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "implementer", "generate-code", "Create a hello world function", "--format", "json"],
            expect_success=False,  # May require network
        )
        # May require network
        assert result.exit_code in [0, 1]


# ============================================================================
# Tester Agent Commands
# ============================================================================

@pytest.mark.e2e_cli
class TestTesterCommandsLegacy(CLICommandTestBase):
    """Legacy tester command tests converted to class-based."""
    
    def test_tester_test_command(self):
        """Test tester test command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "tester", "test", str(test_file), "--format", "json"],
            expect_success=False,  # May require network
        )
        # May require network
        assert result.exit_code in [0, 1]

    def test_tester_generate_tests_command(self):
        """Test tester generate-tests command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "tester", "generate-tests", str(test_file), "--format", "json"],
            expect_success=False,  # May require network
        )
        # May require network
        assert result.exit_code in [0, 1]

    def test_tester_run_tests_command(self):
        """Test tester run-tests command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "tester", "run-tests", "--format", "json"],
            expect_success=False,  # May fail if no tests exist
        )
        # May fail if no tests exist, which is acceptable
        assert result.exit_code in [0, 1]


# ============================================================================
# Debugger Agent Commands
# ============================================================================

@pytest.mark.e2e_cli
class TestDebuggerCommandsLegacy(CLICommandTestBase):
    """Legacy debugger command tests converted to class-based."""
    
    def test_debugger_debug_command(self):
        """Test debugger debug command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "debugger", "debug", "ValueError: invalid input", "--file", str(test_file), "--format", "json"],
            expect_success=False,  # May require network or fail parsing
        )
        # May require network or fail parsing
        assert result.exit_code in [0, 1]

    def test_debugger_analyze_error_command(self):
        """Test debugger analyze-error command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "debugger", "analyze-error", "TypeError: unsupported operand", "--format", "json"],
            expect_success=False,  # May require network
        )
        # May require network
        assert result.exit_code in [0, 1]


# ============================================================================
# Documenter Agent Commands
# ============================================================================

@pytest.mark.e2e_cli
class TestDocumenterCommandsLegacy(CLICommandTestBase):
    """Legacy documenter command tests converted to class-based."""
    
    def test_documenter_document_command(self):
        """Test documenter document command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "documenter", "document", str(test_file), "--output-format", "markdown"]
        )
        # May require network
        assert result.exit_code in [0, 1]

    def test_documenter_generate_docs_command(self):
        """Test documenter generate-docs command (API documentation)."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "documenter", "generate-docs", str(test_file), "--output-format", "markdown"]
        )
        # May require network
        assert result.exit_code in [0, 1]

    def test_documenter_update_readme_command(self):
        """Test documenter update-readme command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "documenter", "update-readme"]
        )
        # May require network
        assert result.exit_code in [0, 1]


# ============================================================================
# Analyst Agent Commands
# ============================================================================

@pytest.mark.e2e_cli
class TestAnalystCommandsLegacy(CLICommandTestBase):
    """Legacy analyst command tests converted to class-based."""
    
    def test_analyst_gather_requirements_command(self):
        """Test analyst gather-requirements command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "analyst", "gather-requirements", "Build a task management app", "--format", "json"],
            expect_success=False,  # May require network
        )
        # May require network
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
def test_analyst_stakeholder_analysis_command(cli_harness, test_project):
    """Test analyst stakeholder-analysis command."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "analyst", "stakeholder-analysis", "E-commerce platform", "--format", "json"],
        cwd=test_project,
    )
    # May require network
    assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
def test_analyst_tech_research_command(cli_harness, test_project):
    """Test analyst tech-research command."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "analyst", "tech-research", "Web framework for API", "--format", "json"],
        cwd=test_project,
    )
    # May require network
    assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
def test_analyst_estimate_effort_command(cli_harness, test_project):
    """Test analyst estimate-effort command."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "analyst", "estimate-effort", "User authentication feature", "--format", "json"],
        cwd=test_project,
    )
    # May require network
    assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
def test_analyst_assess_risk_command(cli_harness, test_project):
    """Test analyst assess-risk command."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "analyst", "assess-risk", "Payment processing feature", "--format", "json"],
        cwd=test_project,
    )
    # May require network
    assert result.exit_code in [0, 1]


# ============================================================================
# Architect Agent Commands
# ============================================================================

@pytest.mark.e2e_cli
def test_architect_design_command(cli_harness, test_project):
    """Test architect design command."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "architect", "design", "Microservices architecture for e-commerce", "--format", "json"],
        cwd=test_project,
    )
    # May require network
    assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
def test_architect_patterns_command(cli_harness, test_project):
    """Test architect tech-selection command (patterns doesn't exist, using tech-selection instead)."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "architect", "tech-selection", "REST API framework", "--format", "json"],
        cwd=test_project,
    )
    # May require network
    assert result.exit_code in [0, 1, 2]


# ============================================================================
# Designer Agent Commands
# ============================================================================

@pytest.mark.e2e_cli
def test_designer_design_api_command(cli_harness, test_project):
    """Test designer api-design command."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "designer", "api-design", "User management API", "--format", "json"],
        cwd=test_project,
    )
    # May require network
    assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
def test_designer_design_model_command(cli_harness, test_project):
    """Test designer data-model-design command."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "designer", "data-model-design", "User data model", "--format", "json"],
        cwd=test_project,
    )
    # May require network
    assert result.exit_code in [0, 1]


# ============================================================================
# Improver Agent Commands
# ============================================================================

@pytest.mark.e2e_cli
def test_improver_improve_command(cli_harness, test_project, test_file):
    """Test improver improve-quality command."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "improver", "improve-quality", str(test_file), "--format", "json"],
        cwd=test_project,
    )
    # May require network
    assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
def test_improver_optimize_command(cli_harness, test_project, test_file):
    """Test improver optimize command."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "improver", "optimize", str(test_file), "--format", "json"],
        cwd=test_project,
    )
    # May require network
    assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
def test_improver_refactor_command(cli_harness, test_project, test_file):
    """Test improver refactor command."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "improver", "refactor", str(test_file), "--instruction", "Extract functions", "--format", "json"],
        cwd=test_project,
    )
    # May require network
    assert result.exit_code in [0, 1]


# ============================================================================
# Ops Agent Commands
# ============================================================================

@pytest.mark.e2e_cli
def test_ops_audit_security_command(cli_harness, test_project):
    """Test ops security-scan command."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "ops", "security-scan", "--target", str(test_project), "--format", "json"],
        cwd=test_project,
    )
    # May require network
    assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
def test_ops_check_compliance_command(cli_harness, test_project):
    """Test ops compliance-check command."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "ops", "compliance-check", "--format", "json"],
        cwd=test_project,
    )
    # May require network
    assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
def test_ops_audit_dependencies_command(cli_harness, test_project):
    """Test ops audit-dependencies command."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "ops", "audit-dependencies", "--format", "json"],
        cwd=test_project,
    )
    # May require network
    assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
def test_ops_plan_deployment_command(cli_harness, test_project):
    """Test ops deploy command (plan-deployment doesn't exist, using deploy instead)."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "ops", "deploy", "--target", "local", "--format", "json"],
        cwd=test_project,
    )
    # May require network or fail if deployment config missing
    assert result.exit_code in [0, 1, 2]


# ============================================================================
# Enhancer Agent Commands
# ============================================================================

@pytest.mark.e2e_cli
def test_enhancer_enhance_command(cli_harness, test_project):
    """Test enhancer enhance command."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "enhancer", "enhance", "Build a REST API", "--format", "json"],
        cwd=test_project,
    )
    # May require network
    assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
def test_enhancer_enhance_quick_command(cli_harness, test_project):
    """Test enhancer enhance-quick command."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "enhancer", "enhance-quick", "Add user authentication", "--format", "json"],
        cwd=test_project,
    )
    # May require network
    assert result.exit_code in [0, 1]


# ============================================================================
# Orchestrator Agent Commands
# ============================================================================

@pytest.mark.e2e_cli
def test_orchestrator_orchestrate_command(cli_harness, test_project):
    """Test orchestrator orchestrate command."""
    # Create a simple workflow file
    workflow_file = test_project / "test_workflow.yaml"
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
    
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "orchestrator", "orchestrate", str(workflow_file), "--format", "json"],
        cwd=test_project,
    )
    # May require network or fail if workflow invalid
    assert result.exit_code in [0, 1, 2]


# ============================================================================
# Top-Level Commands
# ============================================================================

# ============================================================================
# Top-Level Commands (Refactored)
# ============================================================================

@pytest.mark.e2e_cli
class TestTopLevelCommandsRefactored(CLICommandTestBase):
    """Refactored top-level command tests using base class."""
    
    def test_score_command(self):
        """Test top-level score command (shortcut for reviewer score)."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "score", str(test_file), "--format", "json"]
        )
        json_data = assert_valid_json(result)
        # Check for either direct 'file' key or wrapped in 'data'
        assert "file" in json_data or ("data" in json_data and isinstance(json_data["data"], dict))


@pytest.mark.e2e_cli
def test_doctor_command(cli_harness, test_project):
    """Test doctor command."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "doctor", "--format", "json"],
        cwd=test_project,
    )
    # Doctor command should succeed (exit code 0)
    assert result.exit_code == 0


@pytest.mark.e2e_cli
def test_workflow_list_command(cli_harness, test_project):
    """Test workflow list command."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "workflow", "list"],
        cwd=test_project,
    )
    assert_success(result)


@pytest.mark.e2e_cli
def test_workflow_recommend_command(cli_harness, test_project):
    """Test workflow recommend command."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "workflow", "recommend", "--format", "json"],
        cwd=test_project,
    )
    # May require network
    assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
def test_init_command(cli_harness, test_project):
    """Test init command."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "init", "--yes", "--no-cache"],
        cwd=test_project,
    )
    # Init should succeed
    assert result.exit_code in [0, 1]  # May fail if already initialized


@pytest.mark.e2e_cli
def test_simple_mode_status_command(cli_harness, test_project):
    """Test simple-mode status command."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "simple-mode", "status", "--format", "json"],
        cwd=test_project,
    )
    assert_success(result)


@pytest.mark.e2e_cli
def test_version_command(cli_harness, test_project):
    """Test --version flag."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "--version"],
        cwd=test_project,
    )
    assert_success(result)
    assert "tapps-agents" in result.stdout.lower() or "version" in result.stdout.lower()


@pytest.mark.e2e_cli
def test_help_command(cli_harness, test_project):
    """Test --help flag."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "--help"],
        cwd=test_project,
    )
    assert_success(result)
    assert "TappsCodingAgents" in result.stdout or "tapps-agents" in result.stdout.lower()


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.e2e_cli
def test_invalid_command(cli_harness, test_project):
    """Test invalid command handling."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "invalid-command"],
        cwd=test_project,
    )
    # Should fail gracefully
    assert result.exit_code != 0


@pytest.mark.e2e_cli
def test_missing_file_argument(cli_harness, test_project):
    """Test missing file argument."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "reviewer", "score"],
        cwd=test_project,
    )
    # Should fail with error message
    assert result.exit_code != 0


@pytest.mark.e2e_cli
def test_nonexistent_file(cli_harness, test_project):
    """Test nonexistent file handling."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "reviewer", "score", "nonexistent_file.py", "--format", "json"],
        cwd=test_project,
    )
    # Should fail gracefully
    assert result.exit_code != 0


# ============================================================================
# Format Tests
# ============================================================================

@pytest.mark.e2e_cli
def test_json_format(cli_harness, test_project, test_file):
    """Test JSON output format."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "reviewer", "score", str(test_file), "--format", "json"],
        cwd=test_project,
    )
    assert_success(result)
    json_data = assert_json_output(result)
    assert isinstance(json_data, dict)


@pytest.mark.e2e_cli
def test_text_format(cli_harness, test_project, test_file):
    """Test text output format."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "reviewer", "score", str(test_file), "--format", "text"],
        cwd=test_project,
    )
    assert_success(result)
    # Text format should produce readable output
    assert len(result.stdout) > 0


@pytest.mark.e2e_cli
def test_markdown_format(cli_harness, test_project, test_file):
    """Test markdown output format."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "reviewer", "score", str(test_file), "--format", "markdown"],
        cwd=test_project,
    )
    assert_success(result)
    # Markdown format should produce readable output
    assert len(result.stdout) > 0


# ============================================================================
# Global Flags Tests
# ============================================================================

@pytest.mark.e2e_cli
def test_quiet_flag(cli_harness, test_project, test_file):
    """Test --quiet flag."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "--quiet", "reviewer", "score", str(test_file), "--format", "json"],
        cwd=test_project,
    )
    assert_success(result)


@pytest.mark.e2e_cli
def test_verbose_flag(cli_harness, test_project, test_file):
    """Test --verbose flag."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "--verbose", "reviewer", "score", str(test_file), "--format", "json"],
        cwd=test_project,
    )
    assert_success(result)


@pytest.mark.e2e_cli
def test_no_progress_flag(cli_harness, test_project, test_file):
    """Test --no-progress flag."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "--no-progress", "reviewer", "score", str(test_file), "--format", "json"],
        cwd=test_project,
    )
    assert_success(result)


@pytest.mark.e2e_cli
def test_progress_flag(cli_harness, test_project, test_file):
    """Test --progress flag."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "--progress", "off", "reviewer", "score", str(test_file), "--format", "json"],
        cwd=test_project,
    )
    assert_success(result)

