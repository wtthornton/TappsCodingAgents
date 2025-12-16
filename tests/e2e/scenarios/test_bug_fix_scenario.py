"""
E2E scenario test: Bug Fix.

Tests a complete user journey for fixing a bug end-to-end:
- Bug report analysis
- Bug reproduction
- Bug fix implementation
- Code review with quality gates
- Test verification
- Artifact validation
"""

from pathlib import Path

import pytest

from tests.e2e.fixtures.dependency_validator import validate_workflow_file
from tests.e2e.fixtures.scenario_templates import create_small_scenario_template
from tests.e2e.fixtures.scenario_validator import ScenarioValidator
from tests.e2e.fixtures.workflow_runner import WorkflowRunner


@pytest.mark.e2e_scenario
@pytest.mark.template_type("small")
def test_bug_fix_scenario(
    e2e_project: Path,
    e2e_correlation_id: str,
    e2e_artifact_capture,
):
    """
    Test bug fix scenario end-to-end.

    Scenario: Fix a bug in the divide function that returns wrong sign for negative results.
    Expected: Bug fixed, tests pass, review gate passes, artifacts created.
    """
    # Set up scenario template
    project_path = create_small_scenario_template(e2e_project, "bug_fix")

    # Verify initial state (bug exists)
    assert (project_path / "BUG_REPORT.md").exists()
    assert (project_path / "src" / "calculator.py").exists()
    
    # Verify bug exists in code
    calculator_code = (project_path / "src" / "calculator.py").read_text()
    assert "abs(a / b)" in calculator_code, "Bug should be present in initial state"

    # Validate and load workflow - fail immediately if missing
    workflow_path = Path(__file__).parent.parent.parent.parent / "workflows" / "presets" / "quick-fix.yaml"
    validate_workflow_file(workflow_path)

    runner = WorkflowRunner(project_path, use_mocks=True)
    workflow = runner.load_workflow(workflow_path)

    # Execute workflow (mocked mode)
    try:
        result = runner.run_workflow(workflow, timeout_seconds=300)
        
        # Validate workflow completed
        assert result["status"] in ["completed", "success"], f"Workflow did not complete: {result.get('error')}"

        # Validate bug is fixed
        calculator_code_after = (project_path / "src" / "calculator.py").read_text()
        assert "abs(a / b)" not in calculator_code_after, "Bug should be fixed"

        # Validate scenario outcomes
        validator = ScenarioValidator(project_path, "bug_fix", "small")
        is_valid = validator.validate_all()

        if not is_valid:
            errors = validator.get_validation_errors()
            pytest.fail("Scenario validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    except Exception:
        # Capture artifacts on failure
        runner.capture_state_snapshot("failure")
        raise


@pytest.mark.e2e_scenario
@pytest.mark.template_type("small")
@pytest.mark.requires_llm
def test_bug_fix_scenario_real_llm(
    e2e_project: Path,
    e2e_correlation_id: str,
    e2e_artifact_capture,
):
    """
    Test bug fix scenario with real LLM (optional).

    This test requires real LLM credentials and is marked for scheduled runs only.
    """
    # Set up scenario template
    project_path = create_small_scenario_template(e2e_project, "bug_fix")

    # Validate and load workflow - fail immediately if missing
    workflow_path = Path(__file__).parent.parent.parent.parent / "workflows" / "presets" / "quick-fix.yaml"
    validate_workflow_file(workflow_path)

    runner = WorkflowRunner(project_path, use_mocks=False)
    workflow = runner.load_workflow(workflow_path)

    # Execute workflow with real LLM (longer timeout)
    try:
        result = runner.run_workflow(workflow, timeout_seconds=1800)  # 30 minutes

        # Validate workflow completed
        assert result["status"] in ["completed", "success"], f"Workflow did not complete: {result.get('error')}"

        # Validate bug is fixed
        calculator_code_after = (project_path / "src" / "calculator.py").read_text()
        assert "abs(a / b)" not in calculator_code_after, "Bug should be fixed"

        # Validate scenario outcomes
        validator = ScenarioValidator(project_path, "bug_fix", "small")
        is_valid = validator.validate_all()

        if not is_valid:
            errors = validator.get_validation_errors()
            pytest.fail("Scenario validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    except Exception:
        # Capture artifacts on failure
        runner.capture_state_snapshot("failure")
        raise

