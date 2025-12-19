"""
E2E scenario test: Feature Implementation.

Tests a complete user journey for implementing a new feature end-to-end:
- Feature request analysis
- Feature design
- Feature implementation
- Code review with quality gates
- Test generation and execution
- Artifact validation

Includes real-time progress monitoring and hang detection.
"""

import logging
from pathlib import Path

import pytest

from tests.e2e.fixtures.dependency_validator import validate_workflow_file
from tests.e2e.fixtures.scenario_templates import create_small_scenario_template
from tests.e2e.fixtures.scenario_validator import ScenarioValidator
from tests.e2e.fixtures.workflow_monitor import MonitoringConfig, WorkflowActivityMonitor
from tests.e2e.fixtures.workflow_runner import WorkflowRunner

logger = logging.getLogger(__name__)


@pytest.mark.e2e_scenario
@pytest.mark.template_type("small")
@pytest.mark.asyncio
@pytest.mark.monitoring_config(
    max_seconds_without_activity=90.0,
    max_seconds_without_progress=180.0,
    max_seconds_total=600.0,
    check_interval_seconds=5.0,
    log_progress=True,
)
async def test_feature_implementation_scenario(
    e2e_project: Path,
    e2e_correlation_id: str,
    e2e_artifact_capture,
    workflow_monitor: WorkflowActivityMonitor,
    workflow_monitoring_config: MonitoringConfig,
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

    # Execute workflow (mocked mode) with monitoring
    # Note: In real scenarios, this would use real agents, but for E2E tests
    # we use mocked agents to keep tests fast and deterministic
    try:
        state, result = await runner.run_workflow(
            workflow_path,
            max_steps=50,
            monitoring_config=workflow_monitoring_config,
            custom_observers=[workflow_monitor],
        )
        
        # Validate workflow completed
        assert result["status"] in ["completed", "success"], f"Workflow did not complete: {result.get('error')}"

        # Validate monitoring results
        monitoring_results = result.get("monitoring")
        if monitoring_results:
            assert monitoring_results.get("snapshots_count", 0) > 0, "Monitoring should have captured snapshots"
            assert not monitoring_results.get("hang_detected", True), "No hang should be detected"

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
@pytest.mark.asyncio
@pytest.mark.monitoring_config(
    max_seconds_without_activity=120.0,
    max_seconds_without_progress=240.0,
    max_seconds_total=900.0,
    check_interval_seconds=5.0,
    log_progress=True,
)
async def test_feature_implementation_scenario_real_llm(
    e2e_project: Path,
    e2e_correlation_id: str,
    e2e_artifact_capture,
    workflow_monitor: WorkflowActivityMonitor,
    workflow_monitoring_config: MonitoringConfig,
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

    # Execute workflow with real LLM (longer timeout) and monitoring
    try:
        state, result = await runner.run_workflow(
            workflow_path,
            max_steps=50,
            monitoring_config=workflow_monitoring_config,
            custom_observers=[workflow_monitor],
        )

        # Validate workflow completed
        assert result["status"] in ["completed", "success"], f"Workflow did not complete: {result.get('error')}"

        # Validate monitoring results
        monitoring_results = result.get("monitoring")
        if monitoring_results:
            assert monitoring_results.get("snapshots_count", 0) > 0, "Monitoring should have captured snapshots"

        # Validate scenario outcomes
        validator = ScenarioValidator(project_path, "feature", "small")
        is_valid = validator.validate_all()

        if not is_valid:
            errors = validator.get_validation_errors()
            pytest.fail("Scenario validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    except Exception:
        # Artifacts are automatically captured by e2e_artifact_capture fixture on failure
        raise

