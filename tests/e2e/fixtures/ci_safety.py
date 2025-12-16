"""
CI/CD safety controls for real-service E2E tests.

Provides:
- Credential presence gates
- Token/time budgeting
- Per-suite timeouts
- Scheduled-only enforcement
- Cost controls
"""

import logging
import os
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class CredentialGate:
    """Configuration for credential gating."""

    required_vars: list[str]
    skip_on_missing: bool = True
    fail_on_missing: bool = False

    def check(self) -> tuple[bool, str | None]:
        """
        Check if required credentials are available.

        Returns:
            Tuple of (available, reason)
        """
        missing = [var for var in self.required_vars if not os.getenv(var)]
        if missing:
            reason = f"Missing required credentials: {', '.join(missing)}"
            return False, reason
        return True, None


@dataclass
class TimeoutConfig:
    """Configuration for test suite timeouts."""

    smoke_timeout_seconds: float = 60.0
    workflow_timeout_seconds: float = 300.0
    scenario_timeout_seconds: float = 1800.0
    cli_timeout_seconds: float = 300.0


@dataclass
class CostConfig:
    """Configuration for cost controls."""

    max_tokens_per_run: int | None = None
    max_api_calls_per_run: int | None = None
    max_cost_per_run: float | None = None
    alert_on_regression: bool = True


class SafetyController:
    """Controller for CI/CD safety controls."""

    def __init__(
        self,
        credential_gate: CredentialGate | None = None,
        timeout_config: TimeoutConfig | None = None,
        cost_config: CostConfig | None = None,
    ):
        """
        Initialize safety controller.

        Args:
            credential_gate: Credential gate configuration
            timeout_config: Timeout configuration
            cost_config: Cost control configuration
        """
        self.credential_gate = credential_gate or CredentialGate(required_vars=[])
        self.timeout_config = timeout_config or TimeoutConfig()
        self.cost_config = cost_config or CostConfig()
        self._token_count = 0
        self._api_call_count = 0

    def check_credentials(self) -> tuple[bool, str | None]:
        """
        Check if required credentials are available.

        Returns:
            Tuple of (available, reason)
        """
        return self.credential_gate.check()

    def should_skip(self) -> tuple[bool, str | None]:
        """
        Determine if tests should be skipped.

        Returns:
            Tuple of (should_skip, reason)
        """
        if self.credential_gate.skip_on_missing:
            available, reason = self.check_credentials()
            if not available:
                return True, reason
        return False, None

    def get_timeout(self, test_type: str) -> float:
        """
        Get timeout for test type.

        Args:
            test_type: Type of test (smoke, workflow, scenario, cli)

        Returns:
            Timeout in seconds
        """
        timeouts = {
            "smoke": self.timeout_config.smoke_timeout_seconds,
            "workflow": self.timeout_config.workflow_timeout_seconds,
            "scenario": self.timeout_config.scenario_timeout_seconds,
            "cli": self.timeout_config.cli_timeout_seconds,
        }
        return timeouts.get(test_type, 300.0)

    def track_tokens(self, count: int):
        """
        Track token usage.

        Args:
            count: Number of tokens used
        """
        self._token_count += count
        if (
            self.cost_config.max_tokens_per_run
            and self._token_count > self.cost_config.max_tokens_per_run
        ):
            logger.warning(
                f"Token usage exceeded limit: {self._token_count} > {self.cost_config.max_tokens_per_run}"
            )

    def track_api_call(self):
        """Track API call."""
        self._api_call_count += 1
        if (
            self.cost_config.max_api_calls_per_run
            and self._api_call_count > self.cost_config.max_api_calls_per_run
        ):
            logger.warning(
                f"API call count exceeded limit: {self._api_call_count} > {self.cost_config.max_api_calls_per_run}"
            )

    def get_stats(self) -> dict[str, int]:
        """
        Get usage statistics.

        Returns:
            Dictionary with usage stats
        """
        return {
            "tokens": self._token_count,
            "api_calls": self._api_call_count,
        }


def check_ci_environment() -> dict[str, bool]:
    """
    Check CI environment variables.

    Returns:
        Dictionary with environment checks
    """
    return {
        "is_ci": os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true",
        "is_scheduled": os.getenv("GITHUB_EVENT_NAME") == "schedule",
        "is_workflow_dispatch": os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch",
        "is_pull_request": os.getenv("GITHUB_EVENT_NAME") == "pull_request",
        "is_main_branch": os.getenv("GITHUB_REF") == "refs/heads/main",
    }


def should_run_real_service_tests() -> tuple[bool, str]:
    """
    Determine if real-service tests should run.

    Returns:
        Tuple of (should_run, reason)
    """
    env = check_ci_environment()

    # Only run on schedule or manual dispatch
    if env["is_scheduled"] or env["is_workflow_dispatch"]:
        return True, "Scheduled or manual trigger"
    elif env["is_pull_request"]:
        return False, "PR checks - real service tests skipped"
    elif env["is_main_branch"]:
        return False, "Main branch - real service tests skipped (use schedule)"
    else:
        return False, "Not a scheduled or manual trigger"


def create_credential_gate_for_llm() -> CredentialGate:
    """
    Create credential gate for LLM services.

    Returns:
        CredentialGate configured for LLM services
    """
    return CredentialGate(
        required_vars=["ANTHROPIC_API_KEY", "OPENAI_API_KEY"],
        skip_on_missing=True,
        fail_on_missing=False,
    )


def create_credential_gate_for_context7() -> CredentialGate:
    """
    Create credential gate for Context7.

    Returns:
        CredentialGate configured for Context7
    """
    return CredentialGate(
        required_vars=["CONTEXT7_API_KEY"],
        skip_on_missing=True,
        fail_on_missing=False,
    )

