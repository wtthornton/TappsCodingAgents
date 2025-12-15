"""
Shared fixtures for E2E tests.

Provides:
- e2e_project: Creates isolated test project
- e2e_correlation_id: Generates correlation ID for test
- e2e_artifact_capture: Automatic artifact capture on failure
- e2e_cleanup: Automatic cleanup
"""

import pytest
from pathlib import Path
from typing import Generator

from tests.e2e.fixtures.e2e_harness import (
    create_test_project,
    generate_correlation_id,
    capture_artifacts,
    cleanup_project,
    create_failure_bundle,
)
from tests.e2e.fixtures.project_templates import TemplateType
from tests.e2e.fixtures.workflow_runner import (
    WorkflowRunner,
    GateController,
)


@pytest.fixture
def e2e_correlation_id() -> str:
    """
    Generate a correlation ID for an E2E test run.

    Returns:
        Unique correlation ID string
    """
    return generate_correlation_id()


@pytest.fixture
def e2e_project(tmp_path: Path, request) -> Generator[Path, None, None]:
    """
    Create an isolated test project for E2E testing.

    Uses the 'template_type' marker to determine which template to use.
    Defaults to 'minimal' if not specified.

    Yields:
        Path to the created project directory

    Example:
        @pytest.mark.template_type("small")
        def test_something(e2e_project):
            # e2e_project is a Path to the test project
            pass
    """
    # Get template type from marker, default to minimal
    template_marker = request.node.get_closest_marker("template_type")
    template_type: TemplateType = "minimal"
    if template_marker:
        template_type = template_marker.args[0] if template_marker.args else "minimal"

    project_path = create_test_project(template_type, tmp_path)

    yield project_path

    # Cleanup after test
    cleanup_project(project_path)


@pytest.fixture
def e2e_artifact_capture(e2e_project: Path, e2e_correlation_id: str, request) -> Generator[None, None, None]:
    """
    Automatically capture artifacts on test failure.

    This fixture runs after the test and captures artifacts if the test failed.

    Yields:
        None (this is a setup/teardown fixture)
    """
    test_name = request.node.name
    snapshots = []

    yield

    # Only capture if test failed
    rep_call = getattr(request.node, "rep_call", None)
    if rep_call and rep_call.failed:
        try:
            artifacts = capture_artifacts(e2e_project, test_name, e2e_correlation_id)
            # Store artifacts in request for potential inspection
            if hasattr(request.config, "cache"):
                request.config.cache.set(f"e2e_artifacts_{e2e_correlation_id}", artifacts)
        except Exception as e:
            # Don't fail the test if artifact capture fails
            import logging
            logging.getLogger(__name__).warning(f"Failed to capture artifacts: {e}")


@pytest.fixture(autouse=True)
def e2e_cleanup(e2e_project: Path, request) -> Generator[None, None, None]:
    """
    Automatically clean up test project after test completion.

    This fixture is autouse=True, so it runs for all E2E tests.

    Yields:
        None (this is a setup/teardown fixture)
    """
    yield

    # Cleanup happens in e2e_project fixture, but this provides an additional safety net
    # The e2e_project fixture already handles cleanup, so this is mainly for logging
    pass


@pytest.fixture
def workflow_runner(e2e_project: Path, request) -> WorkflowRunner:
    """
    Create a workflow runner for E2E workflow tests.

    Uses mocked mode by default unless 'requires_llm' marker is present.

    Yields:
        WorkflowRunner instance

    Example:
        @pytest.mark.e2e_workflow
        def test_workflow(workflow_runner):
            state, results = await workflow_runner.run_workflow(workflow_path)
    """
    # Check if test requires real LLM
    use_mocks = not bool(request.node.get_closest_marker("requires_llm"))

    runner = WorkflowRunner(e2e_project, use_mocks=use_mocks)
    return runner


@pytest.fixture
def gate_controller() -> GateController:
    """
    Create a gate controller for deterministic gate outcomes in tests.

    Yields:
        GateController instance

    Example:
        def test_gate_routing(gate_controller):
            gate_controller.set_outcome("quality_gate", False)
            # ... run workflow ...
    """
    return GateController()


@pytest.fixture
def workflow_project(e2e_project: Path) -> Path:
    """
    Alias for e2e_project for workflow-specific tests.

    This is a convenience fixture that makes it clear the project is for workflow testing.

    Yields:
        Path to the test project directory
    """
    return e2e_project


# Hook to capture test results for artifact capture
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Store test result for artifact capture fixture."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
