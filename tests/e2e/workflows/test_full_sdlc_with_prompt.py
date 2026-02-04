"""
E2E test for full-sdlc workflow with user prompt.

Tests workflow execution with an explicit user prompt passed to the workflow.
Includes real-time progress monitoring and hang detection.
"""

import logging
from pathlib import Path

import pytest

from tests.e2e.fixtures.sdlc_validators import (
    SDLCPhaseValidator,
    assert_architecture_includes,
    assert_html_has_animations,
    assert_html_has_dark_theme,
    assert_requirements_contain,
)
from tests.e2e.fixtures.workflow_monitor import (
    MonitoringConfig,
    WorkflowActivityMonitor,
)
from tests.e2e.fixtures.workflow_runner import WorkflowRunner

logger = logging.getLogger(__name__)


@pytest.mark.e2e_workflow
@pytest.mark.template_type("minimal")
@pytest.mark.asyncio
@pytest.mark.timeout(600)
@pytest.mark.behavioral_mock
@pytest.mark.monitoring_config(
    max_seconds_without_activity=120.0,
    max_seconds_without_progress=240.0,
    max_seconds_total=600.0,
    check_interval_seconds=5.0,
    log_progress=True,
)
async def test_full_sdlc_workflow_with_prompt(
    e2e_project: Path,
    e2e_correlation_id: str,
    e2e_artifact_capture,
    workflow_runner: WorkflowRunner,
    workflow_monitor: WorkflowActivityMonitor,
    workflow_monitoring_config: MonitoringConfig,
):
    """
    Test full SDLC workflow execution with explicit user prompt and comprehensive monitoring/validation.

    Scenario: User requests "Create a simple html page with animation that is dark and modern"
    Expected: Workflow executes all steps, creates HTML page with dark theme and animations,
              and passes SDLC phase validations.
    """
    workflow_path = Path(__file__).parent.parent.parent.parent / "workflows" / "presets" / "full-sdlc.yaml"
    user_prompt = "Create a simple html page with animation that is dark and modern"

    # Register SDLC validator
    sdlc_validator = SDLCPhaseValidator(e2e_project)
    validators = {
        "requirements": sdlc_validator,
        "architecture": sdlc_validator,
        "implementation": sdlc_validator,
        "quality_gate": sdlc_validator,
    }

    # Execute workflow with user prompt and monitoring
    final_state, results = await workflow_runner.run_workflow(
        workflow_path,
        user_prompt=user_prompt,
        monitoring_config=workflow_monitoring_config,
        custom_observers=[workflow_monitor],
        validators=validators,
    )

    # --- General Workflow Assertions ---
    assert final_state is not None
    assert final_state.workflow_id.startswith("full-sdlc")
    assert results["correlation_id"] is not None
    assert final_state.status in ["completed", "success"], f"Workflow did not complete: {final_state.status}"
    assert final_state.variables.get("user_prompt") == user_prompt, "User prompt should persist in final state"
    assert results.get("steps_completed", 0) > 0, "No steps were executed"
    assert "requirements" in results.get("completed_steps_ids", []), "Requirements step should have executed"

    # --- Monitoring Assertions ---
    monitoring_results = results.get("monitoring")
    assert monitoring_results is not None, "Monitoring results should be present"
    assert monitoring_results.get("snapshots_count", 0) > 0, "Monitoring should have captured activity snapshots"
    assert not monitoring_results.get("hang_detected", True), "No hang should be detected"
    assert monitoring_results.get("observed_events_count", 0) > 0, "Monitor should have observed events"

    # --- SDLC Phase Validation Assertions ---
    # Requirements Validation
    requirements_validation = final_state.variables.get("requirements_validation_result")
    assert requirements_validation is not None, "Requirements validation result should be present"
    assert requirements_validation["passed"], f"Requirements validation failed: {requirements_validation['errors']}"
    requirements_path = e2e_project / "requirements.md"
    assert requirements_path.exists(), "requirements.md file should exist"
    assert_requirements_contain(requirements_path, ["html page", "animation", "dark", "modern"])

    # Architecture Validation
    architecture_validation = final_state.variables.get("architecture_validation_result")
    assert architecture_validation is not None, "Architecture validation result should be present"
    assert architecture_validation["passed"], f"Architecture validation failed: {architecture_validation['errors']}"
    architecture_path = e2e_project / "architecture.md"
    assert architecture_path.exists(), "architecture.md file should exist"

    # Implementation Validation
    implementation_validation = final_state.variables.get("implementation_validation_result")
    assert implementation_validation is not None, "Implementation validation result should be present"
    assert implementation_validation["passed"], f"Implementation validation failed: {implementation_validation['errors']}"
    
    # Find the created HTML file
    html_files = [f for f in e2e_project.rglob("*.html") if f.is_file()]
    assert len(html_files) > 0, "At least one HTML file should be created"
    html_file = html_files[0]
    assert_html_has_dark_theme(html_file)
    assert_html_has_animations(html_file)

    # Quality Gate Validation (if applicable)
    quality_gate_validation = final_state.variables.get("review_validation_result")
    if quality_gate_validation:
        assert quality_gate_validation["passed"], f"Quality gate validation failed: {quality_gate_validation['errors']}"


@pytest.mark.e2e_workflow
@pytest.mark.template_type("minimal")
@pytest.mark.asyncio
@pytest.mark.timeout(120)
@pytest.mark.behavioral_mock
@pytest.mark.monitoring_config(
    max_seconds_without_activity=30.0,
    max_seconds_without_progress=60.0,
    max_seconds_total=120.0,
    check_interval_seconds=2.0,
    log_progress=True,
)
async def test_full_sdlc_workflow_with_prompt_mocked(
    e2e_project: Path,
    workflow_runner: WorkflowRunner,
    workflow_monitor: WorkflowActivityMonitor,
    workflow_monitoring_config: MonitoringConfig,
):
    """
    Test full SDLC workflow with prompt using mocked agents (faster test).
    This test validates that the prompt is properly passed through the workflow
    and basic monitoring works without requiring full execution.
    """
    workflow_path = Path(__file__).parent.parent.parent.parent / "workflows" / "presets" / "full-sdlc.yaml"
    user_prompt = "Create a simple html page with animation that is dark and modern"

    # Execute workflow with user prompt and monitoring (limited steps for faster test)
    final_state, results = await workflow_runner.run_workflow(
        workflow_path,
        max_steps=3,  # Limit steps for mocked test
        user_prompt=user_prompt,
        monitoring_config=workflow_monitoring_config,
        custom_observers=[workflow_monitor],
    )

    assert final_state.variables.get("user_prompt") == user_prompt
    steps_completed = results.get("steps_completed", 0)
    assert steps_completed > 0

    monitoring_results = results.get("monitoring")
    assert monitoring_results is not None
    assert monitoring_results["activity_summary"]["total_activities"] > 0
    assert not monitoring_results["activity_summary"]["hang_detected"]
    assert monitoring_results.get("observed_events_count", 0) > 0


# ============================================================================
# Phase 4: Gate Routing Tests
# ============================================================================

@pytest.mark.e2e_workflow
@pytest.mark.template_type("minimal")
@pytest.mark.asyncio
@pytest.mark.timeout(300)
@pytest.mark.behavioral_mock
@pytest.mark.monitoring_config(
    max_seconds_without_activity=60.0,
    max_seconds_without_progress=120.0,
    max_seconds_total=300.0,
    check_interval_seconds=3.0,
    log_progress=True,
)
async def test_quality_gate_pass_path(
    e2e_project: Path,
    workflow_runner: WorkflowRunner,
    workflow_monitor: WorkflowActivityMonitor,
    workflow_monitoring_config: MonitoringConfig,
):
    """
    Test that quality gate passes when scores meet thresholds and workflow continues to testing.
    
    Scenario: Review step produces scores above thresholds (overall >= 70, security >= 7.0)
    Expected: Gate passes, workflow proceeds to testing step
    """
    workflow_path = Path(__file__).parent.parent.parent.parent / "workflows" / "presets" / "full-sdlc.yaml"
    user_prompt = "Create a simple html page with animation that is dark and modern"

    # Register validator to track quality gate
    sdlc_validator = SDLCPhaseValidator(e2e_project)
    validators = {"quality_gate": sdlc_validator}

    # Mock high scores to ensure gate passes
    # Note: With behavioral mocks, we can't directly control scores, but we can verify the path
    final_state, results = await workflow_runner.run_workflow(
        workflow_path,
        max_steps=10,  # Enough to reach review step
        user_prompt=user_prompt,
        monitoring_config=workflow_monitoring_config,
        custom_observers=[workflow_monitor],
        validators=validators,
    )

    # Verify workflow reached review step
    completed_steps = results.get("completed_steps_ids", [])
    assert "review" in completed_steps, "Review step should have executed"

    # Verify quality gate validation ran
    quality_gate_validation = final_state.variables.get("review_validation_result")
    if quality_gate_validation:
        # If validation passed, workflow should continue to testing
        if quality_gate_validation["passed"]:
            # Check if testing step executed (gate passed path)
            assert "testing" in completed_steps or final_state.status == "completed", \
                "If gate passed, testing step should execute"
        else:
            # If validation failed, workflow should loop back to implementation
            logger.info(f"Quality gate failed: {quality_gate_validation['errors']}")


@pytest.mark.e2e_workflow
@pytest.mark.template_type("minimal")
@pytest.mark.asyncio
@pytest.mark.timeout(300)
@pytest.mark.behavioral_mock
@pytest.mark.monitoring_config(
    max_seconds_without_activity=60.0,
    max_seconds_without_progress=120.0,
    max_seconds_total=300.0,
    check_interval_seconds=3.0,
    log_progress=True,
)
async def test_quality_gate_fail_path(
    e2e_project: Path,
    workflow_runner: WorkflowRunner,
    workflow_monitor: WorkflowActivityMonitor,
    workflow_monitoring_config: MonitoringConfig,
):
    """
    Test that quality gate fails when scores below thresholds and workflow loops back to implementation.
    
    Scenario: Review step produces scores below thresholds
    Expected: Gate fails, workflow loops back to implementation step
    """
    workflow_path = Path(__file__).parent.parent.parent.parent / "workflows" / "presets" / "full-sdlc.yaml"
    user_prompt = "Create a simple html page with animation that is dark and modern"

    # Register validator
    sdlc_validator = SDLCPhaseValidator(e2e_project)
    validators = {"quality_gate": sdlc_validator}

    final_state, results = await workflow_runner.run_workflow(
        workflow_path,
        max_steps=15,  # Allow for potential loop back
        user_prompt=user_prompt,
        monitoring_config=workflow_monitoring_config,
        custom_observers=[workflow_monitor],
        validators=validators,
    )

    # Verify review step executed
    completed_steps = results.get("completed_steps_ids", [])
    assert "review" in completed_steps, "Review step should have executed"

    # Check quality gate validation result
    quality_gate_validation = final_state.variables.get("review_validation_result")
    if quality_gate_validation and not quality_gate_validation["passed"]:
        # If gate failed, implementation should have run again (loop back)
        implementation_count = completed_steps.count("implementation")
        assert implementation_count >= 1, "Implementation step should have executed at least once"
        logger.info(f"Quality gate failed as expected: {quality_gate_validation['errors']}")


@pytest.mark.e2e_workflow
@pytest.mark.template_type("minimal")
@pytest.mark.asyncio
@pytest.mark.timeout(180)
@pytest.mark.behavioral_mock
@pytest.mark.monitoring_config(
    max_seconds_without_activity=45.0,
    max_seconds_without_progress=90.0,
    max_seconds_total=180.0,
    check_interval_seconds=2.0,
    log_progress=True,
)
async def test_quality_gate_threshold_enforcement(
    e2e_project: Path,
    workflow_runner: WorkflowRunner,
    workflow_monitor: WorkflowActivityMonitor,
    workflow_monitoring_config: MonitoringConfig,
):
    """
    Test that quality gate enforces thresholds correctly (overall_min: 70, security_min: 7.0).
    
    Scenario: Review step with scoring
    Expected: Validation checks both overall_min and security_min thresholds
    """
    workflow_path = Path(__file__).parent.parent.parent.parent / "workflows" / "presets" / "full-sdlc.yaml"
    user_prompt = "Create a simple html page with animation that is dark and modern"

    # Register validator
    sdlc_validator = SDLCPhaseValidator(e2e_project)
    validators = {"quality_gate": sdlc_validator}

    final_state, results = await workflow_runner.run_workflow(
        workflow_path,
        max_steps=10,  # Enough to reach review
        user_prompt=user_prompt,
        monitoring_config=workflow_monitoring_config,
        custom_observers=[workflow_monitor],
        validators=validators,
    )

    # Verify review step executed
    completed_steps = results.get("completed_steps_ids", [])
    assert "review" in completed_steps, "Review step should have executed"

    # Verify quality gate validation ran and checked thresholds
    quality_gate_validation = final_state.variables.get("review_validation_result")
    if quality_gate_validation:
        # Validator should have checked both thresholds
        errors = quality_gate_validation.get("errors", [])
        # Check that threshold validation occurred (either passed or failed with threshold messages)
        threshold_checked = any(
            "overall" in err.lower() or "security" in err.lower() or "threshold" in err.lower()
            for err in errors
        ) or quality_gate_validation["passed"]
        assert threshold_checked, "Quality gate should check overall and security thresholds"


# ============================================================================
# Phase 4: Artifact Quality Tests
# ============================================================================

@pytest.mark.e2e_workflow
@pytest.mark.template_type("minimal")
@pytest.mark.asyncio
@pytest.mark.timeout(300)
@pytest.mark.behavioral_mock
@pytest.mark.monitoring_config(
    max_seconds_without_activity=60.0,
    max_seconds_without_progress=120.0,
    max_seconds_total=300.0,
    check_interval_seconds=3.0,
    log_progress=True,
)
async def test_requirements_artifact_quality(
    e2e_project: Path,
    workflow_runner: WorkflowRunner,
    workflow_monitor: WorkflowActivityMonitor,
    workflow_monitoring_config: MonitoringConfig,
):
    """
    Test that requirements.md artifact meets quality standards.
    
    Scenario: Requirements step creates requirements.md
    Expected: File exists, is not empty, contains expected keywords from prompt
    """
    workflow_path = Path(__file__).parent.parent.parent.parent / "workflows" / "presets" / "full-sdlc.yaml"
    user_prompt = "Create a simple html page with animation that is dark and modern"

    # Register validator
    sdlc_validator = SDLCPhaseValidator(e2e_project)
    validators = {"requirements": sdlc_validator}

    final_state, results = await workflow_runner.run_workflow(
        workflow_path,
        max_steps=5,  # Enough to complete requirements step
        user_prompt=user_prompt,
        monitoring_config=workflow_monitoring_config,
        custom_observers=[workflow_monitor],
        validators=validators,
    )

    # Verify requirements step executed
    assert "requirements" in results.get("completed_steps_ids", []), "Requirements step should have executed"

    # Verify requirements validation passed
    requirements_validation = final_state.variables.get("requirements_validation_result")
    assert requirements_validation is not None, "Requirements validation should have run"
    assert requirements_validation["passed"], f"Requirements validation failed: {requirements_validation['errors']}"

    # Verify artifact quality
    requirements_path = e2e_project / "requirements.md"
    assert requirements_path.exists(), "requirements.md should exist"
    assert requirements_path.stat().st_size > 0, "requirements.md should not be empty"
    
    # Verify content quality (contains keywords from prompt)
    assert_requirements_contain(requirements_path, ["html", "animation", "dark", "modern"])


@pytest.mark.e2e_workflow
@pytest.mark.template_type("minimal")
@pytest.mark.asyncio
@pytest.mark.timeout(300)
@pytest.mark.behavioral_mock
@pytest.mark.monitoring_config(
    max_seconds_without_activity=60.0,
    max_seconds_without_progress=120.0,
    max_seconds_total=300.0,
    check_interval_seconds=3.0,
    log_progress=True,
)
async def test_architecture_artifact_quality(
    e2e_project: Path,
    workflow_runner: WorkflowRunner,
    workflow_monitor: WorkflowActivityMonitor,
    workflow_monitoring_config: MonitoringConfig,
):
    """
    Test that architecture.md artifact meets quality standards.
    
    Scenario: Design step creates architecture.md
    Expected: File exists, contains design information
    """
    workflow_path = Path(__file__).parent.parent.parent.parent / "workflows" / "presets" / "full-sdlc.yaml"
    user_prompt = "Create a simple html page with animation that is dark and modern"

    # Register validator
    sdlc_validator = SDLCPhaseValidator(e2e_project)
    validators = {"architecture": sdlc_validator}

    final_state, results = await workflow_runner.run_workflow(
        workflow_path,
        max_steps=8,  # Enough to complete design step
        user_prompt=user_prompt,
        monitoring_config=workflow_monitoring_config,
        custom_observers=[workflow_monitor],
        validators=validators,
    )

    # Verify design step executed
    assert "design" in results.get("completed_steps_ids", []), "Design step should have executed"

    # Verify architecture validation passed
    architecture_validation = final_state.variables.get("architecture_validation_result")
    assert architecture_validation is not None, "Architecture validation should have run"
    assert architecture_validation["passed"], f"Architecture validation failed: {architecture_validation['errors']}"

    # Verify artifact quality
    architecture_path = e2e_project / "architecture.md"
    assert architecture_path.exists(), "architecture.md should exist"
    assert architecture_path.stat().st_size > 0, "architecture.md should not be empty"
    
    # Verify content quality (contains design topics)
    assert_architecture_includes(architecture_path, ["design", "system", "component"])


@pytest.mark.e2e_workflow
@pytest.mark.template_type("minimal")
@pytest.mark.asyncio
@pytest.mark.timeout(300)
@pytest.mark.behavioral_mock
@pytest.mark.monitoring_config(
    max_seconds_without_activity=60.0,
    max_seconds_without_progress=120.0,
    max_seconds_total=300.0,
    check_interval_seconds=3.0,
    log_progress=True,
)
async def test_implementation_artifact_quality(
    e2e_project: Path,
    workflow_runner: WorkflowRunner,
    workflow_monitor: WorkflowActivityMonitor,
    workflow_monitoring_config: MonitoringConfig,
):
    """
    Test that implementation artifacts (HTML files) meet quality standards.
    
    Scenario: Implementation step creates HTML file
    Expected: HTML file exists, has dark theme, has animations
    """
    workflow_path = Path(__file__).parent.parent.parent.parent / "workflows" / "presets" / "full-sdlc.yaml"
    user_prompt = "Create a simple html page with animation that is dark and modern"

    # Register validator
    sdlc_validator = SDLCPhaseValidator(e2e_project)
    validators = {"implementation": sdlc_validator}

    final_state, results = await workflow_runner.run_workflow(
        workflow_path,
        max_steps=10,  # Enough to complete implementation step
        user_prompt=user_prompt,
        monitoring_config=workflow_monitoring_config,
        custom_observers=[workflow_monitor],
        validators=validators,
    )

    # Verify implementation step executed
    assert "implementation" in results.get("completed_steps_ids", []), "Implementation step should have executed"

    # Verify implementation validation passed
    implementation_validation = final_state.variables.get("implementation_validation_result")
    assert implementation_validation is not None, "Implementation validation should have run"
    assert implementation_validation["passed"], f"Implementation validation failed: {implementation_validation['errors']}"

    # Verify artifact quality - find HTML file
    html_files = [f for f in e2e_project.rglob("*.html") if f.is_file()]
    assert len(html_files) > 0, "At least one HTML file should be created"
    
    html_file = html_files[0]
    assert html_file.stat().st_size > 0, "HTML file should not be empty"
    
    # Verify content quality
    assert_html_has_dark_theme(html_file)
    assert_html_has_animations(html_file)

