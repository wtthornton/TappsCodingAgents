"""
E2E test fixtures and utilities.

This package provides:
- Project templates (minimal, small, medium)
- Scenario templates (feature, bug_fix, refactor)
- E2E harness utilities (project creation, artifact capture, cleanup)
- CLI harness utilities (subprocess runner, output capture, isolation)
- CI/CD artifact bundling utilities (failure artifacts, JUnit reports)
- CI/CD safety controls (credential gates, timeouts, cost controls)
- Workflow runner utilities
- Scenario validation utilities
- Reliability controls (timeouts, retries, cost guardrails)
- Shared fixtures for E2E tests
"""

from .cli_harness import (
    CLIExecutionError,
    CLIHarness,
    CLIResult,
    assert_exit_code,
    assert_failure,
    assert_json_output,
    assert_success,
    capture_cli_artifacts,
)
from .e2e_harness import (
    assert_artifact_content,
    assert_artifact_exists,
    assert_json_artifact_shape,
    capture_artifacts,
    capture_state_snapshot,
    cleanup_project,
    create_failure_bundle,
    create_test_project,
    generate_correlation_id,
    redact_secrets,
)
from .project_templates import (
    TemplateType,
    create_medium_template,
    create_minimal_template,
    create_small_template,
    create_template,
)
from .reliability_controls import (
    CostConfig,
    CostTracker,
    ReliabilityController,
    RetryConfig,
    TimeoutConfig,
    get_reliability_controller,
    set_reliability_controller,
)
from .scenario_templates import (
    ScenarioType,
    create_medium_scenario_template,
    create_small_scenario_template,
    get_expected_outputs,
)
from .ci_artifacts import (
    attach_correlation_id,
    collect_failure_artifacts,
    create_junit_summary,
    create_test_summary,
    get_correlation_id,
)
from .ci_safety import (
    CostConfig as CICostConfig,
    CredentialGate,
    SafetyController,
    TimeoutConfig as CITimeoutConfig,
    check_ci_environment,
    create_credential_gate_for_context7,
    create_credential_gate_for_llm,
    should_run_real_service_tests,
)
from .scenario_validator import ScenarioValidator
from .workflow_runner import GateController, WorkflowRunner

__all__ = [
    # E2E harness
    "create_test_project",
    "capture_artifacts",
    "assert_artifact_exists",
    "assert_artifact_content",
    "assert_json_artifact_shape",
    "cleanup_project",
    "generate_correlation_id",
    "capture_state_snapshot",
    "create_failure_bundle",
    "redact_secrets",
    # CLI harness
    "CLIHarness",
    "CLIResult",
    "CLIExecutionError",
    "assert_json_output",
    "assert_exit_code",
    "assert_success",
    "assert_failure",
    "capture_cli_artifacts",
    # Project templates
    "TemplateType",
    "create_minimal_template",
    "create_small_template",
    "create_medium_template",
    "create_template",
    # Scenario templates
    "ScenarioType",
    "create_small_scenario_template",
    "create_medium_scenario_template",
    "get_expected_outputs",
    # Scenario validation
    "ScenarioValidator",
    # Workflow runner
    "WorkflowRunner",
    "GateController",
    # Reliability controls
    "TimeoutConfig",
    "RetryConfig",
    "CostConfig",
    "CostTracker",
    "ReliabilityController",
    "get_reliability_controller",
    "set_reliability_controller",
    # CI/CD artifacts
    "collect_failure_artifacts",
    "create_test_summary",
    "create_junit_summary",
    "attach_correlation_id",
    "get_correlation_id",
    # CI/CD safety
    "CredentialGate",
    "SafetyController",
    "CITimeoutConfig",
    "CICostConfig",
    "check_ci_environment",
    "should_run_real_service_tests",
    "create_credential_gate_for_llm",
    "create_credential_gate_for_context7",
]
