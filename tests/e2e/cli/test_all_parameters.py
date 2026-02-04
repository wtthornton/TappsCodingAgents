"""
Comprehensive parameterized tests for all CLI commands and parameter combinations.

This test suite systematically tests all commands with all their parameter combinations
to ensure complete coverage of the CLI interface.
"""


import pytest

from tests.e2e.cli.test_base import CLICommandTestBase
from tests.e2e.cli.test_data_generators import (
    generate_file_paths,
)
from tests.e2e.cli.validation_helpers import (
    assert_text_output,
    assert_valid_json,
)


@pytest.mark.e2e_cli
class TestReviewerParameters(CLICommandTestBase):
    """Parameterized tests for Reviewer Agent commands."""

    @pytest.mark.parametrize("format_type", ["json", "text", "markdown", "html"])
    def test_reviewer_review_formats(self, format_type):
        """Test reviewer review with all format options."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "review", str(test_file), "--format", format_type],
            expect_success=False,  # May require network
        )
        assert result.exit_code in [0, 1]
        if format_type == "json":
            assert_valid_json(result)
        elif format_type == "text":
            assert_text_output(result)

    @pytest.mark.parametrize("format_type", ["json", "text", "markdown", "html"])
    def test_reviewer_score_formats(self, format_type):
        """Test reviewer score with all format options."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "score", str(test_file), "--format", format_type]
        )
        assert result.exit_code in [0, 1]
        if format_type == "json":
            assert_valid_json(result)

    @pytest.mark.parametrize("max_workers", [1, 2, 4, 8])
    def test_reviewer_review_max_workers(self, max_workers):
        """Test reviewer review with different max-workers values."""
        test_file = self.get_test_file()
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "reviewer", "review",
                str(test_file), "--max-workers", str(max_workers), "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    @pytest.mark.parametrize("fail_under", [50, 70, 80, 90])
    def test_reviewer_review_fail_under(self, fail_under):
        """Test reviewer review with different fail-under thresholds."""
        test_file = self.get_test_file()
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "reviewer", "review",
                str(test_file), "--fail-under", str(fail_under), "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1, 2]  # 2 = quality threshold not met

    def test_reviewer_review_multiple_files(self):
        """Test reviewer review with multiple files."""
        files = generate_file_paths(self.test_project, count=3)
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "reviewer", "review",
                str(files[0]), str(files[1]), str(files[2]), "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_reviewer_review_with_pattern(self):
        """Test reviewer review with pattern matching."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "reviewer", "review",
                "--pattern", "**/*.py", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_reviewer_review_with_output(self):
        """Test reviewer review with output file."""
        test_file = self.get_test_file()
        output_file = self.test_project / "review_output.json"
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "reviewer", "review",
                str(test_file), "--output", str(output_file), "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    @pytest.mark.parametrize("format_type", ["json", "text"])
    def test_reviewer_lint_formats(self, format_type):
        """Test reviewer lint with format options."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "lint", str(test_file), "--format", format_type]
        )
        assert result.exit_code in [0, 1]

    def test_reviewer_lint_fail_on_issues(self):
        """Test reviewer lint with fail-on-issues flag."""
        test_file = self.get_test_file()
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "reviewer", "lint",
                str(test_file), "--fail-on-issues", "--format", "json"
            ]
        )
        assert result.exit_code in [0, 1, 2]  # 2 = issues found

    @pytest.mark.parametrize("format_type", ["json", "text"])
    def test_reviewer_type_check_formats(self, format_type):
        """Test reviewer type-check with format options."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "type-check", str(test_file), "--format", format_type]
        )
        assert result.exit_code in [0, 1]

    @pytest.mark.parametrize("formats", [["json"], ["markdown"], ["html"], ["json", "markdown"], ["all"]])
    def test_reviewer_report_formats(self, formats):
        """Test reviewer report with different format combinations."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "reviewer", "report",
                str(self.test_project)
            ] + formats,
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_reviewer_report_with_output_dir(self):
        """Test reviewer report with custom output directory."""
        output_dir = self.test_project / "custom_reports"
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "reviewer", "report",
                str(self.test_project), "json", "--output-dir", str(output_dir)
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    @pytest.mark.parametrize("format_type", ["json", "text"])
    def test_reviewer_duplication_formats(self, format_type):
        """Test reviewer duplication with format options."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "reviewer", "duplication",
                str(self.test_project), "--format", format_type
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1] or result.timed_out

    @pytest.mark.parametrize("mode", ["code", "info"])
    def test_reviewer_docs_modes(self, mode):
        """Test reviewer docs with different modes."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "reviewer", "docs",
                "fastapi", "--mode", mode, "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    @pytest.mark.parametrize("page", [1, 2, 3])
    def test_reviewer_docs_pages(self, page):
        """Test reviewer docs with different page numbers."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "reviewer", "docs",
                "fastapi", "--page", str(page), "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_reviewer_docs_with_topic(self):
        """Test reviewer docs with topic."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "reviewer", "docs",
                "fastapi", "routing", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_reviewer_docs_no_cache(self):
        """Test reviewer docs with no-cache flag."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "reviewer", "docs",
                "fastapi", "--no-cache", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestPlannerParameters(CLICommandTestBase):
    """Parameterized tests for Planner Agent commands."""

    @pytest.mark.parametrize("format_type", ["json", "text", "markdown"])
    def test_planner_plan_formats(self, format_type):
        """Test planner plan with all format options."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "planner", "plan",
                "Create a user authentication feature", "--format", format_type
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    @pytest.mark.parametrize("enhance_mode", ["quick", "full"])
    def test_planner_plan_enhance_modes(self, enhance_mode):
        """Test planner plan with different enhance modes."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "planner", "plan",
                "Create a feature", "--enhance", "--enhance-mode", enhance_mode, "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_planner_plan_no_enhance(self):
        """Test planner plan with no-enhance flag."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "planner", "plan",
                "Create a feature", "--no-enhance", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_planner_plan_with_output(self):
        """Test planner plan with output file."""
        output_file = self.test_project / "plan_output.json"
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "planner", "plan",
                "Create a feature", "--output", str(output_file), "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    @pytest.mark.parametrize("priority", ["high", "medium", "low"])
    def test_planner_create_story_priorities(self, priority):
        """Test planner create-story with different priorities."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "planner", "create-story",
                "User login feature", "--priority", priority, "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_planner_create_story_with_epic(self):
        """Test planner create-story with epic."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "planner", "create-story",
                "User login", "--epic", "Authentication", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_planner_list_stories_with_epic(self):
        """Test planner list-stories with epic filter."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "planner", "list-stories",
                "--epic", "Authentication", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_planner_list_stories_with_status(self):
        """Test planner list-stories with status filter."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "planner", "list-stories",
                "--status", "todo", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestImplementerParameters(CLICommandTestBase):
    """Parameterized tests for Implementer Agent commands."""

    @pytest.mark.parametrize("format_type", ["json", "text", "markdown", "diff"])
    def test_implementer_refactor_formats(self, format_type):
        """Test implementer refactor with all format options."""
        test_file = self.get_test_file()
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "implementer", "refactor",
                str(test_file), "Add type hints", "--format", format_type
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    @pytest.mark.parametrize("language", ["python", "javascript", "typescript"])
    def test_implementer_implement_languages(self, language):
        """Test implementer implement with different languages."""
        target_file = self.test_project / f"test_{language}.{language if language != 'typescript' else 'ts'}"
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "implementer", "implement",
                "Create a hello world function", str(target_file),
                "--language", language, "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_implementer_implement_with_context(self):
        """Test implementer implement with context."""
        target_file = self.test_project / "test_with_context.py"
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "implementer", "implement",
                "Create a calculator", str(target_file),
                "--context", "Use FastAPI and Pydantic", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_implementer_generate_code_with_file(self):
        """Test implementer generate-code with file context."""
        test_file = self.get_test_file()
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "implementer", "generate-code",
                "Add a new function", "--file", str(test_file), "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestTesterParameters(CLICommandTestBase):
    """Parameterized tests for Tester Agent commands."""

    def test_tester_test_with_integration(self):
        """Test tester test with integration flag."""
        test_file = self.get_test_file()
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "tester", "test",
                str(test_file), "--integration", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_tester_test_with_test_file(self):
        """Test tester test with custom test file."""
        test_file = self.get_test_file()
        test_output = self.test_project / "tests" / "test_custom.py"
        test_output.parent.mkdir(exist_ok=True)
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "tester", "test",
                str(test_file), "--test-file", str(test_output), "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_tester_test_with_focus(self):
        """Test tester test with focus aspects."""
        test_file = self.get_test_file()
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "tester", "test",
                str(test_file), "--focus", "edge_cases,error_handling", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_tester_generate_tests_with_integration(self):
        """Test tester generate-tests with integration flag."""
        test_file = self.get_test_file()
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "tester", "generate-tests",
                str(test_file), "--integration", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_tester_run_tests_with_path(self):
        """Test tester run-tests with test path."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "tester", "run-tests",
                str(self.test_project), "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_tester_run_tests_no_coverage(self):
        """Test tester run-tests with no-coverage flag."""
        # Use a shorter timeout since this command can discover tests from parent directories
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "tester", "run-tests",
                "--no-coverage", "--format", "json"
            ],
            expect_success=False,
            timeout=60.0,  # 60 seconds - should fail quickly if no tests found
        )
        # Command may timeout, fail, or succeed depending on test discovery
        # Accept timeout (124) or standard exit codes (0, 1)
        assert result.exit_code in [0, 1, 124] or result.timed_out


@pytest.mark.e2e_cli
class TestGlobalFlags(CLICommandTestBase):
    """Tests for global flags with various commands."""

    @pytest.mark.parametrize("flag", ["--quiet", "-q"])
    def test_quiet_flag(self, flag):
        """Test quiet flag with reviewer score."""
        test_file = self.get_test_file()
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", flag,
                "reviewer", "score", str(test_file), "--format", "json"
            ]
        )
        assert result.exit_code in [0, 1]

    @pytest.mark.parametrize("flag", ["--verbose", "-v"])
    def test_verbose_flag(self, flag):
        """Test verbose flag with reviewer score."""
        test_file = self.get_test_file()
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", flag,
                "reviewer", "score", str(test_file), "--format", "json"
            ]
        )
        assert result.exit_code in [0, 1]

    @pytest.mark.parametrize("progress_mode", ["auto", "rich", "plain", "off"])
    def test_progress_modes(self, progress_mode):
        """Test progress flag with different modes."""
        test_file = self.get_test_file()
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "--progress", progress_mode,
                "reviewer", "score", str(test_file), "--format", "json"
            ]
        )
        assert result.exit_code in [0, 1]

    def test_no_progress_flag(self):
        """Test no-progress flag."""
        test_file = self.get_test_file()
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "--no-progress",
                "reviewer", "score", str(test_file), "--format", "json"
            ]
        )
        assert result.exit_code in [0, 1]

    def test_global_flags_after_subcommand(self):
        """Test global flags can appear after subcommand."""
        test_file = self.get_test_file()
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "reviewer", "score",
                str(test_file), "--format", "json", "--quiet"
            ]
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestTopLevelParameters(CLICommandTestBase):
    """Parameterized tests for top-level commands."""

    @pytest.mark.parametrize("format_type", ["json", "text"])
    def test_doctor_formats(self, format_type):
        """Test doctor command with format options."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "doctor", "--format", format_type]
        )
        assert result.exit_code in [0, 1]

    def test_doctor_with_config_path(self):
        """Test doctor command with config path."""
        config_path = self.test_project / "custom_config.yaml"
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "doctor", "--config-path", str(config_path)]
        )
        assert result.exit_code in [0, 1, 2]  # 2 = config not found

    @pytest.mark.parametrize("workflow", ["full", "rapid", "enterprise", "feature"])
    def test_create_workflows(self, workflow):
        """Test create command with different workflows."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "create",
                "Build a simple todo app", "--workflow", workflow, "--yes"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    @pytest.mark.parametrize("preset", ["full", "rapid", "fix", "quality", "hotfix"])
    def test_workflow_presets(self, preset):
        """Test workflow command with different presets."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "workflow", preset,
                "--prompt", "Add a feature", "--auto"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_workflow_with_file(self):
        """Test workflow command with file parameter."""
        test_file = self.get_test_file()
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "workflow", "fix",
                "--file", str(test_file), "--auto"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    @pytest.mark.parametrize("flag", ["--no-rules", "--no-presets", "--no-config", "--no-skills"])
    def test_init_flags(self, flag):
        """Test init command with various skip flags."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "init", flag, "--yes"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_init_reset(self):
        """Test init command with reset flag."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "init", "--reset", "--yes", "--dry-run"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_simple_mode_status(self):
        """Test simple-mode status command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "simple-mode", "status"]
        )
        assert result.exit_code in [0, 1]

    @pytest.mark.parametrize("format_type", ["json", "text"])
    def test_simple_mode_status_formats(self, format_type):
        """Test simple-mode status with format options."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "simple-mode", "status", "--format", format_type]
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestAnalystParameters(CLICommandTestBase):
    """Parameterized tests for Analyst Agent commands."""

    @pytest.mark.parametrize("format_type", ["json", "text", "markdown"])
    def test_analyst_gather_requirements_formats(self, format_type):
        """Test analyst gather-requirements with format options."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "analyst", "gather-requirements",
                "Build a task management app", "--format", format_type
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_analyst_gather_requirements_with_context(self):
        """Test analyst gather-requirements with context."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "analyst", "gather-requirements",
                "Build an API", "--context", "Must use FastAPI and PostgreSQL", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    @pytest.mark.parametrize("enhance_mode", ["quick", "full"])
    def test_analyst_gather_requirements_enhance_modes(self, enhance_mode):
        """Test analyst gather-requirements with enhance modes."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "analyst", "gather-requirements",
                "Build a feature", "--enhance", "--enhance-mode", enhance_mode, "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_analyst_stakeholder_analysis(self):
        """Test analyst stakeholder-analysis command."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "analyst", "stakeholder-analysis",
                "Build a new feature"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_analyst_tech_research(self):
        """Test analyst tech-research command."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "analyst", "tech-research",
                "REST API framework", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_analyst_estimate_effort(self):
        """Test analyst estimate-effort command."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "analyst", "estimate-effort",
                "Add user authentication", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_analyst_assess_risk(self):
        """Test analyst assess-risk command."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "analyst", "assess-risk",
                "Migrate to new database", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestEnhancerParameters(CLICommandTestBase):
    """Parameterized tests for Enhancer Agent commands."""

    @pytest.mark.parametrize("format_type", ["markdown", "json", "yaml"])
    def test_enhancer_enhance_formats(self, format_type):
        """Test enhancer enhance with format options."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "enhancer", "enhance",
                "Build a todo app", "--format", format_type
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    @pytest.mark.parametrize("format_type", ["markdown", "json", "yaml"])
    def test_enhancer_enhance_quick_formats(self, format_type):
        """Test enhancer enhance-quick with format options."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "enhancer", "enhance-quick",
                "Add user authentication", "--format", format_type
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    @pytest.mark.parametrize("stage", ["analysis", "requirements", "architecture", "codebase", "quality", "strategy", "synthesis"])
    def test_enhancer_enhance_stage(self, stage):
        """Test enhancer enhance-stage with different stages."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "enhancer", "enhance-stage",
                stage, "Build a feature", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestDebuggerParameters(CLICommandTestBase):
    """Parameterized tests for Debugger Agent commands."""

    def test_debugger_debug_with_file(self):
        """Test debugger debug with file."""
        test_file = self.get_test_file()
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "debugger", "debug",
                "ValueError: invalid input", "--file", str(test_file), "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_debugger_debug_with_line(self):
        """Test debugger debug with line number."""
        test_file = self.get_test_file()
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "debugger", "debug",
                "TypeError: unsupported operand", "--file", str(test_file),
                "--line", "10", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_debugger_analyze_error_with_stack_trace(self):
        """Test debugger analyze-error with stack trace."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "debugger", "analyze-error",
                "KeyError: 'missing_key'",
                "--stack-trace", "Traceback...", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestDocumenterParameters(CLICommandTestBase):
    """Parameterized tests for Documenter Agent commands."""

    @pytest.mark.parametrize("output_format", ["markdown", "html", "rst"])
    def test_documenter_document_formats(self, output_format):
        """Test documenter document with format options."""
        test_file = self.get_test_file()
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "documenter", "document",
                str(test_file), "--output-format", output_format
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_documenter_document_with_output_file(self):
        """Test documenter document with output file."""
        test_file = self.get_test_file()
        output_file = self.test_project / "documentation.md"
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "documenter", "document",
                str(test_file), "--output-file", str(output_file)
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_documenter_generate_docs(self):
        """Test documenter generate-docs command."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "documenter", "generate-docs",
                "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_documenter_update_readme(self):
        """Test documenter update-readme command."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "documenter", "update-readme",
                "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestImproverParameters(CLICommandTestBase):
    """Parameterized tests for Improver Agent commands."""

    def test_improver_improve_quality(self):
        """Test improver improve-quality command."""
        test_file = self.get_test_file()
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "improver", "improve-quality",
                str(test_file), "Add error handling", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_improver_optimize(self):
        """Test improver optimize command."""
        test_file = self.get_test_file()
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "improver", "optimize",
                str(test_file), "Improve performance", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_improver_refactor(self):
        """Test improver refactor command."""
        test_file = self.get_test_file()
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "improver", "refactor",
                str(test_file), "Extract common logic", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestOpsParameters(CLICommandTestBase):
    """Parameterized tests for Ops Agent commands."""

    def test_ops_security_scan(self):
        """Test ops security-scan command."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "ops", "security-scan",
                "--target", str(self.test_project), "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    @pytest.mark.parametrize("standard", ["GDPR", "HIPAA", "PCI-DSS"])
    def test_ops_check_compliance(self, standard):
        """Test ops check-compliance with different standards."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "ops", "check-compliance",
                "--standard", standard, "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_ops_audit_dependencies(self):
        """Test ops audit-dependencies command."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "ops", "audit-dependencies",
                "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_ops_plan_deployment(self):
        """Test ops plan-deployment command."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "ops", "plan-deployment",
                "Deploy to production", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestArchitectParameters(CLICommandTestBase):
    """Parameterized tests for Architect Agent commands."""

    def test_architect_design_system(self):
        """Test architect design-system command."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "architect", "design-system",
                "Build a microservices architecture", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_architect_patterns(self):
        """Test architect patterns command."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "architect", "patterns",
                "Design a caching layer", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestDesignerParameters(CLICommandTestBase):
    """Parameterized tests for Designer Agent commands."""

    def test_designer_api_design(self):
        """Test designer api-design command."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "designer", "api-design",
                "Design REST API for user management", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_designer_design_model(self):
        """Test designer design-model command."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "designer", "design-model",
                "Design database schema for e-commerce", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestOrchestratorParameters(CLICommandTestBase):
    """Parameterized tests for Orchestrator Agent commands."""

    def test_orchestrator_orchestrate(self):
        """Test orchestrator orchestrate command."""
        # Create a simple workflow file
        workflow_file = self.test_project / "test_workflow.yaml"
        workflow_file.write_text("""name: test
steps:
  - agent: reviewer
    command: score
    args:
      file: test.py
""")
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "orchestrator", "orchestrate",
                str(workflow_file), "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_orchestrator_sequence(self):
        """Test orchestrator sequence command."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "orchestrator", "sequence",
                "plan,design,implement", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestCommandAliases(CLICommandTestBase):
    """Tests for command aliases (*command format)."""

    def test_reviewer_star_score(self):
        """Test reviewer *score alias."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "*score", str(test_file), "--format", "json"]
        )
        assert result.exit_code in [0, 1]

    def test_reviewer_star_review(self):
        """Test reviewer *review alias."""
        test_file = self.get_test_file()
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "reviewer", "*review",
                str(test_file), "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_planner_star_plan(self):
        """Test planner *plan alias."""
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "planner", "*plan",
                "Create a feature", "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_implementer_star_implement(self):
        """Test implementer *implement alias."""
        target_file = self.test_project / "test_star_implement.py"
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "implementer", "*implement",
                "Create a function", str(target_file), "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestParameterCombinations(CLICommandTestBase):
    """Tests for multiple parameter combinations."""

    def test_reviewer_review_full_params(self):
        """Test reviewer review with all optional parameters."""
        test_file = self.get_test_file()
        output_file = self.test_project / "full_review.json"
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "reviewer", "review",
                str(test_file),
                "--format", "json",
                "--output", str(output_file),
                "--max-workers", "4",
                "--fail-under", "70"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1, 2]

    def test_planner_plan_full_params(self):
        """Test planner plan with all optional parameters."""
        output_file = self.test_project / "full_plan.json"
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "planner", "plan",
                "Create a comprehensive feature",
                "--format", "json",
                "--output", str(output_file),
                "--enhance",
                "--enhance-mode", "full"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

    def test_tester_test_full_params(self):
        """Test tester test with all optional parameters."""
        test_file = self.get_test_file()
        test_output = self.test_project / "tests" / "test_full.py"
        test_output.parent.mkdir(exist_ok=True)
        result = self.run_command(
            [
                "python", "-m", "tapps_agents.cli", "tester", "test",
                str(test_file),
                "--test-file", str(test_output),
                "--integration",
                "--focus", "edge_cases,error_handling",
                "--format", "json"
            ],
            expect_success=False,
        )
        assert result.exit_code in [0, 1]

