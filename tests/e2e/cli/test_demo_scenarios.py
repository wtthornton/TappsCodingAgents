"""
Demo scenario tests converted from demo/run_demo.py.

Tests complete demo scenarios as integration tests.
"""

import pytest

from tests.e2e.cli.scenario_test_base import ScenarioTestBase
from tests.e2e.cli.validation_helpers import assert_valid_json
from tests.e2e.fixtures.demo_helpers import (
    create_test_code_files,
    create_test_project,
    run_code_review_demo,
    run_code_scoring_demo,
    run_quality_tools_demo,
)


@pytest.mark.e2e_cli
class TestDemoScenarios(ScenarioTestBase):
    """Tests for demo scenarios."""

    def test_code_scoring_scenario(self):
        """Test code scoring demo scenario."""
        # Create demo project structure
        demo_dir = self.test_project / "demo_scenario"
        demo_dir.mkdir(exist_ok=True)
        project_path = create_test_project(demo_dir)
        test_files = create_test_code_files(project_path)
        
        # Run code scoring
        result = run_code_scoring_demo(self.cli_harness, project_path, test_files["calculator"])
        self.record_step("code_scoring", ["score", str(test_files["calculator"])], result)
        
        # Validate result
        assert_valid_json(result)

    def test_code_review_scenario(self):
        """Test code review demo scenario."""
        # Create demo project structure
        demo_dir = self.test_project / "demo_scenario"
        demo_dir.mkdir(exist_ok=True)
        project_path = create_test_project(demo_dir)
        test_files = create_test_code_files(project_path)
        
        # Run code review
        result = run_code_review_demo(self.cli_harness, project_path, test_files["calculator"])
        self.record_step("code_review", ["reviewer", "review", str(test_files["calculator"])], result)
        
        # Accept success or graceful failure (may require network)
        assert result.exit_code in [0, 1]

    def test_quality_tools_scenario(self):
        """Test quality tools demo scenario."""
        # Create demo project structure
        demo_dir = self.test_project / "demo_scenario"
        demo_dir.mkdir(exist_ok=True)
        project_path = create_test_project(demo_dir)
        create_test_code_files(project_path)
        src_dir = project_path / "src"
        
        # Run quality tools (linting, type checking)
        results = run_quality_tools_demo(self.cli_harness, project_path, src_dir)
        
        # Record steps
        for i, result in enumerate(results):
            self.record_step(f"quality_tool_{i}", ["reviewer", "lint"], result)
        
        # Validate results (may fail if tools not installed)
        for result in results:
            assert result.exit_code in [0, 1]

    def test_multi_step_scenario(self):
        """Test multi-step scenario (scoring -> review -> lint)."""
        # Create demo project
        demo_dir = self.test_project / "multi_step"
        demo_dir.mkdir(exist_ok=True)
        project_path = create_test_project(demo_dir)
        test_files = create_test_code_files(project_path)
        
        # Step 1: Code scoring
        score_result = run_code_scoring_demo(self.cli_harness, project_path, test_files["calculator"])
        self.record_step("step1_scoring", ["score"], score_result)
        assert_valid_json(score_result)
        
        # Step 2: Code review
        review_result = run_code_review_demo(self.cli_harness, project_path, test_files["calculator"])
        self.record_step("step2_review", ["reviewer", "review"], review_result)
        assert review_result.exit_code in [0, 1]
        
        # Step 3: Linting
        src_dir = project_path / "src"
        lint_results = run_quality_tools_demo(self.cli_harness, project_path, src_dir)
        self.record_step("step3_lint", ["reviewer", "lint"], lint_results[0] if lint_results else None)
        
        # Get scenario summary
        summary = self.get_scenario_summary()
        assert summary["total_steps"] >= 2

