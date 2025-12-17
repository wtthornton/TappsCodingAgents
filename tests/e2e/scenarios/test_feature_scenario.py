"""
E2E scenario test: Feature Implementation.

Tests a complete user journey for implementing a new feature end-to-end:
- Feature request analysis
- Feature design
- Feature implementation
- Code review with quality gates
- Test generation and execution
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
@pytest.mark.asyncio
async def test_feature_implementation_scenario(
    e2e_project: Path,
    e2e_correlation_id: str,
    e2e_artifact_capture,
):
    """
    Test feature implementation scenario end-to-end.

    Scenario: Implement a new feature (multiplication function) in a calculator module.
    Expected: Feature code created, tests pass, quality gates pass, artifacts created.
    """
    # Set up scenario template
    project_path = create_small_scenario_template(e2e_project, "feature")

    # Verify initial state
    assert (project_path / "FEATURE_REQUEST.md").exists()
    assert (project_path / "src" / "calculator.py").exists()
    assert (project_path / "tests" / "test_calculator.py").exists()

    # Validate and load workflow - fail immediately if missing
    workflow_path = Path(__file__).parent.parent.parent.parent / "workflows" / "presets" / "feature-implementation.yaml"
    validate_workflow_file(workflow_path)

    runner = WorkflowRunner(project_path, use_mocks=True)

    # Execute workflow (mocked mode)
    # Note: In real scenarios, this would use real agents, but for E2E tests
    # we use mocked agents to keep tests fast and deterministic
    try:
        state, result = await runner.run_workflow(workflow_path, max_steps=50)
        
        # Validate workflow completed
        assert result["status"] in ["completed", "success"], f"Workflow did not complete: {result.get('error')}"

        # Validate scenario outcomes
        validator = ScenarioValidator(project_path, "feature", "small")
        is_valid = validator.validate_all()

        if not is_valid:
            errors = validator.get_validation_errors()
            pytest.fail("Scenario validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    except Exception:
        # Artifacts are automatically captured by e2e_artifact_capture fixture on failure
        raise


@pytest.mark.e2e_scenario
@pytest.mark.template_type("small")
@pytest.mark.requires_llm
@pytest.mark.asyncio
async def test_feature_implementation_scenario_real_llm(
    e2e_project: Path,
    e2e_correlation_id: str,
    e2e_artifact_capture,
):
    """
    Test feature implementation scenario with real LLM (optional).

    This test requires real LLM credentials and is marked for scheduled runs only.
    """
    # Set up scenario template
    project_path = create_small_scenario_template(e2e_project, "feature")

    # Validate and load workflow - fail immediately if missing
    workflow_path = Path(__file__).parent.parent.parent.parent / "workflows" / "presets" / "feature-implementation.yaml"
    validate_workflow_file(workflow_path)

    runner = WorkflowRunner(project_path, use_mocks=False)

    # Execute workflow with real LLM (longer timeout)
    try:
        state, result = await runner.run_workflow(workflow_path, max_steps=50)

        # Validate workflow completed
        assert result["status"] in ["completed", "success"], f"Workflow did not complete: {result.get('error')}"

        # Validate scenario outcomes
        validator = ScenarioValidator(project_path, "feature", "small")
        is_valid = validator.validate_all()

        if not is_valid:
            errors = validator.get_validation_errors()
            pytest.fail("Scenario validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    except Exception:
        # Artifacts are automatically captured by e2e_artifact_capture fixture on failure
        raise

