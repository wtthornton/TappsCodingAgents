"""
E2E scenario test: Refactoring.

Tests a complete user journey for refactoring code end-to-end:
- Refactor requirements analysis
- Refactoring implementation
- Code review with quality gates
- Documentation updates
- Regression test verification
- Artifact validation
"""

from pathlib import Path

import pytest

from tests.e2e.fixtures.dependency_validator import validate_workflow_file
from tests.e2e.fixtures.scenario_templates import create_medium_scenario_template
from tests.e2e.fixtures.scenario_validator import ScenarioValidator
from tests.e2e.fixtures.workflow_runner import WorkflowRunner


@pytest.mark.e2e_scenario
@pytest.mark.template_type("medium")
def test_refactor_scenario(
    e2e_project: Path,
    e2e_correlation_id: str,
    e2e_artifact_capture,
):
    """
    Test refactoring scenario end-to-end.

    Scenario: Refactor legacy code to separate concerns (data processing, config, caching).
    Expected: Refactored code, tests pass, quality maintained/improved, docs updated.
    """
    # Set up scenario template
    project_path = create_medium_scenario_template(e2e_project, "refactor")

    # Verify initial state
    assert (project_path / "REFACTOR_REQUIREMENTS.md").exists()
    assert (project_path / "src" / "mypackage" / "legacy.py").exists()
    assert (project_path / "tests" / "test_legacy.py").exists()

    # Verify legacy code structure
    legacy_code = (project_path / "src" / "mypackage" / "legacy.py").read_text()
    assert "LegacyProcessor" in legacy_code, "Legacy code should be present"

    # Validate and load workflow - fail immediately if missing (no fallback)
    workflow_path = Path(__file__).parent.parent.parent.parent / "workflows" / "multi-agent-refactor.yaml"
    validate_workflow_file(workflow_path)

    runner = WorkflowRunner(project_path, use_mocks=True)
    workflow = runner.load_workflow(workflow_path)

    # Execute workflow (mocked mode)
    try:
        result = runner.run_workflow(workflow, timeout_seconds=300)
        
        # Validate workflow completed
        assert result["status"] in ["completed", "success"], f"Workflow did not complete: {result.get('error')}"

        # Validate scenario outcomes
        validator = ScenarioValidator(project_path, "refactor", "medium")
        is_valid = validator.validate_all()

        if not is_valid:
            errors = validator.get_validation_errors()
            pytest.fail("Scenario validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    except Exception:
        # Capture artifacts on failure
        runner.capture_state_snapshot("failure")
        raise


@pytest.mark.e2e_scenario
@pytest.mark.template_type("medium")
@pytest.mark.requires_llm
def test_refactor_scenario_real_llm(
    e2e_project: Path,
    e2e_correlation_id: str,
    e2e_artifact_capture,
):
    """
    Test refactoring scenario with real LLM (optional).

    This test requires real LLM credentials and is marked for scheduled runs only.
    """
    # Set up scenario template
    project_path = create_medium_scenario_template(e2e_project, "refactor")

    # Validate and load workflow - fail immediately if missing (no fallback)
    workflow_path = Path(__file__).parent.parent.parent.parent / "workflows" / "multi-agent-refactor.yaml"
    validate_workflow_file(workflow_path)

    runner = WorkflowRunner(project_path, use_mocks=False)
    workflow = runner.load_workflow(workflow_path)

    # Execute workflow with real LLM (longer timeout)
    try:
        result = runner.run_workflow(workflow, timeout_seconds=1800)  # 30 minutes

        # Validate workflow completed
        assert result["status"] in ["completed", "success"], f"Workflow did not complete: {result.get('error')}"

        # Validate scenario outcomes
        validator = ScenarioValidator(project_path, "refactor", "medium")
        is_valid = validator.validate_all()

        if not is_valid:
            errors = validator.get_validation_errors()
            pytest.fail("Scenario validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    except Exception:
        # Capture artifacts on failure
        runner.capture_state_snapshot("failure")
        raise

