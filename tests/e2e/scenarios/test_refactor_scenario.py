"""
E2E scenario test: Refactoring.

Tests a complete user journey for refactoring code end-to-end:
- Refactor requirements analysis
- Refactoring implementation
- Code review with quality gates
- Documentation updates
- Regression test verification
- Artifact validation

Includes real-time progress monitoring and hang detection.
"""

from pathlib import Path

import pytest

from tests.e2e.fixtures.dependency_validator import validate_workflow_file
from tests.e2e.fixtures.scenario_templates import create_medium_scenario_template
from tests.e2e.fixtures.scenario_validator import ScenarioValidator
from tests.e2e.fixtures.workflow_monitor import MonitoringConfig, WorkflowActivityMonitor
from tests.e2e.fixtures.workflow_runner import WorkflowRunner


@pytest.mark.e2e_scenario
@pytest.mark.template_type("medium")
@pytest.mark.asyncio
@pytest.mark.monitoring_config(
    max_seconds_without_activity=90.0,
    max_seconds_without_progress=180.0,
    max_seconds_total=600.0,
    check_interval_seconds=5.0,
    log_progress=True,
)
async def test_refactor_scenario(
    e2e_project: Path,
    e2e_correlation_id: str,
    e2e_artifact_capture,
    workflow_monitor: WorkflowActivityMonitor,
    workflow_monitoring_config: MonitoringConfig,
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

    # Execute workflow (mocked mode) with monitoring
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
        validator = ScenarioValidator(project_path, "refactor", "medium")
        is_valid = validator.validate_all()

        if not is_valid:
            errors = validator.get_validation_errors()
            pytest.fail("Scenario validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    except Exception:
        # Artifacts are automatically captured by e2e_artifact_capture fixture on failure
        raise


@pytest.mark.e2e_scenario
@pytest.mark.template_type("medium")
@pytest.mark.requires_llm
@pytest.mark.asyncio
@pytest.mark.monitoring_config(
    max_seconds_without_activity=120.0,
    max_seconds_without_progress=240.0,
    max_seconds_total=900.0,
    check_interval_seconds=5.0,
    log_progress=True,
)
async def test_refactor_scenario_real_llm(
    e2e_project: Path,
    e2e_correlation_id: str,
    e2e_artifact_capture,
    workflow_monitor: WorkflowActivityMonitor,
    workflow_monitoring_config: MonitoringConfig,
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
        validator = ScenarioValidator(project_path, "refactor", "medium")
        is_valid = validator.validate_all()

        if not is_valid:
            errors = validator.get_validation_errors()
            pytest.fail("Scenario validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    except Exception:
        # Artifacts are automatically captured by e2e_artifact_capture fixture on failure
        raise

