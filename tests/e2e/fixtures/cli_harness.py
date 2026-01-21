"""
CLI E2E harness utilities for running CLI commands in isolated test environments.

Provides:
- Subprocess runner with cwd isolation
- Environment variable injection
- Timeout handling
- Output capture (stdout, stderr, exit code)
- Artifact capture for failed runs
- Secret redaction in outputs
- Windows path correctness
"""

import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Configure logging
logger = logging.getLogger(__name__)

# Common secret patterns to redact
SECRET_PATTERNS = [
    (r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})['\"]?", r"\1: <REDACTED>"),
    (r"(?i)(token|secret|password)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})['\"]?", r"\1: <REDACTED>"),
    (r"(sk-[a-zA-Z0-9]{32,})", "<REDACTED>"),  # OpenAI API keys
    (r"(sk-ant-[a-zA-Z0-9\-]{95,})", "<REDACTED>"),  # Anthropic API keys
]


@dataclass
class CLIResult:
    """Result of a CLI command execution."""

    exit_code: int
    stdout: str
    stderr: str
    command: list[str]
    cwd: Path | None
    env: dict[str, str] | None
    duration_seconds: float
    timed_out: bool = False

    def json_output(self) -> dict[str, Any] | None:
        """
        Parse stdout as JSON if possible.

        Returns:
            Parsed JSON dict or None if not valid JSON
        """
        try:
            return json.loads(self.stdout.strip())
        except (json.JSONDecodeError, ValueError):
            return None

    def success(self) -> bool:
        """Check if command succeeded (exit code 0)."""
        return self.exit_code == 0 and not self.timed_out

    def redacted_stdout(self) -> str:
        """Get stdout with secrets redacted."""
        return redact_secrets(self.stdout)

    def redacted_stderr(self) -> str:
        """Get stderr with secrets redacted."""
        return redact_secrets(self.stderr)


def redact_secrets(text: str) -> str:
    """
    Redact secrets from text using common patterns.

    Args:
        text: Text to redact secrets from

    Returns:
        Text with secrets redacted
    """
    result = text
    for pattern, replacement in SECRET_PATTERNS:
        result = re.sub(pattern, replacement, result)
    return result


class CLIHarness:
    """Harness for running CLI commands in isolated test environments."""

    def __init__(
        self,
        base_path: Path | None = None,
        default_timeout: float = 300.0,
        default_env: dict[str, str] | None = None,
    ):
        """
        Initialize CLI harness.

        Args:
            base_path: Base path for creating isolated test projects (uses tempdir if None)
            default_timeout: Default timeout in seconds for commands
            default_env: Default environment variables to inject
        """
        self.base_path = base_path or Path(tempfile.gettempdir()) / "tapps_agents_e2e_cli"
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.default_timeout = default_timeout
        self.default_env = default_env or {}
        self._temp_projects: list[Path] = []

    def create_isolated_project(
        self, template_type: str = "minimal", project_name: str | None = None
    ) -> Path:
        """
        Create an isolated test project directory.

        Args:
            template_type: Type of project template (minimal, small, medium)
            project_name: Optional project name (generated if not provided)

        Returns:
            Path to the created project directory
        """
        if project_name is None:
            import uuid

            project_name = f"cli_test_{uuid.uuid4().hex[:8]}"

        project_path = self.base_path / project_name
        project_path.mkdir(parents=True, exist_ok=True)

        # Create minimal project structure
        (project_path / ".git").mkdir(exist_ok=True)
        (project_path / "README.md").write_text(f"# {project_name}\n\nTest project for CLI E2E tests.\n")

        # Create a simple Python file for testing
        (project_path / "test_file.py").write_text(
            '"""Test file for CLI E2E tests."""\n\ndef add(a: int, b: int) -> int:\n    """Add two numbers."""\n    return a + b\n\n'
        )

        self._temp_projects.append(project_path)
        return project_path

    def run_command(
        self,
        command: list[str],
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
        capture_output: bool = True,
        check: bool = False,
    ) -> CLIResult:
        """
        Run a CLI command in an isolated environment.

        Args:
            command: Command to run (e.g., ["python", "-m", "tapps_agents.cli", "reviewer", "score", "file.py"])
            cwd: Working directory (uses isolated project if None)
            env: Environment variables to inject (merged with default_env)
            timeout: Timeout in seconds (uses default_timeout if None)
            capture_output: Whether to capture stdout/stderr
            check: Whether to raise exception on non-zero exit code

        Returns:
            CLIResult with execution details
        """
        import time

        if timeout is None:
            timeout = self.default_timeout

        # Merge environment variables
        merged_env = os.environ.copy()
        merged_env.update(self.default_env)
        if env:
            merged_env.update(env)

        # Add project root to PYTHONPATH so `python -m tapps_agents.cli` works
        # when the package is not installed (e.g. in CI or editable from other env)
        if any("tapps_agents" in str(p) for p in command):
            project_root = Path(__file__).resolve().parents[3]
            existing = merged_env.get("PYTHONPATH", "")
            merged_env["PYTHONPATH"] = str(project_root) + (os.pathsep + existing if existing else "")

        # Ensure command uses proper Python executable
        if command[0] in ("python", "python3"):
            command = [sys.executable] + command[1:]

        # Use isolated project as cwd if not specified
        if cwd is None and self._temp_projects:
            cwd = self._temp_projects[-1]
        elif cwd is None:
            cwd = self.base_path

        # Normalize paths for Windows
        if sys.platform == "win32":
            cwd = Path(cwd).resolve()

        logger.info(f"Running CLI command: {' '.join(command)}")
        logger.info(f"Working directory: {cwd}")
        logger.debug(f"Environment: {list(merged_env.keys())}")

        start_time = time.time()
        timed_out = False

        try:
            result = subprocess.run(
                command,
                cwd=str(cwd),
                env=merged_env,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                check=False,  # We handle check ourselves
            )
            exit_code = result.returncode
            stdout = result.stdout if capture_output else ""
            stderr = result.stderr if capture_output else ""
        except subprocess.TimeoutExpired as e:
            exit_code = 124  # Standard timeout exit code
            stdout = e.stdout.decode("utf-8") if e.stdout else ""
            stderr = e.stderr.decode("utf-8") if e.stderr else ""
            timed_out = True
            logger.warning(f"Command timed out after {timeout} seconds")

        duration = time.time() - start_time

        cli_result = CLIResult(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            command=command,
            cwd=cwd,
            env=merged_env,
            duration_seconds=duration,
            timed_out=timed_out,
        )

        if check and not cli_result.success():
            raise CLIExecutionError(
                f"Command failed with exit code {exit_code}",
                cli_result,
            )

        return cli_result

    def cleanup(self):
        """Clean up all created temporary projects."""
        for project_path in self._temp_projects:
            if project_path.exists():
                try:
                    shutil.rmtree(project_path)
                    logger.debug(f"Cleaned up project: {project_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup project {project_path}: {e}")
        self._temp_projects.clear()


class CLIExecutionError(Exception):
    """Exception raised when CLI command execution fails."""

    def __init__(self, message: str, result: CLIResult):
        super().__init__(message)
        self.result = result


def assert_json_output(result: CLIResult, required_keys: list[str] | None = None) -> dict[str, Any]:
    """
    Assert that CLI result has valid JSON output with required keys.

    Args:
        result: CLI execution result
        required_keys: List of required keys in JSON output

    Returns:
        Parsed JSON dict

    Raises:
        AssertionError: If output is not valid JSON or missing required keys
    """
    json_data = result.json_output()
    assert json_data is not None, f"Expected JSON output, got: {result.stdout[:200]}"

    if required_keys:
        missing_keys = [key for key in required_keys if key not in json_data]
        assert (
            not missing_keys
        ), f"JSON output missing required keys: {missing_keys}. Got keys: {list(json_data.keys())}"

    return json_data


def assert_exit_code(result: CLIResult, expected: int):
    """
    Assert that CLI result has expected exit code.

    Args:
        result: CLI execution result
        expected: Expected exit code

    Raises:
        AssertionError: If exit code doesn't match
    """
    assert (
        result.exit_code == expected
    ), f"Expected exit code {expected}, got {result.exit_code}. stderr: {result.redacted_stderr()[:500]}"


def assert_success(result: CLIResult):
    """
    Assert that CLI command succeeded.

    Args:
        result: CLI execution result

    Raises:
        AssertionError: If command failed or timed out
    """
    assert not result.timed_out, f"Command timed out after {result.duration_seconds}s"
    assert_exit_code(result, 0)


def assert_failure(result: CLIResult, min_exit_code: int = 1):
    """
    Assert that CLI command failed with non-zero exit code.

    Args:
        result: CLI execution result
        min_exit_code: Minimum expected exit code (default: 1)

    Raises:
        AssertionError: If command succeeded
    """
    assert (
        result.exit_code >= min_exit_code
    ), f"Expected failure (exit code >= {min_exit_code}), got {result.exit_code}"


def capture_cli_artifacts(
    result: CLIResult,
    project_path: Path | None = None,
    test_name: str = "cli_test",
) -> dict[str, Any]:
    """
    Capture artifacts from a failed CLI run for debugging.

    Args:
        result: CLI execution result
        project_path: Optional project path to capture artifacts from
        test_name: Test name for artifact organization

    Returns:
        Dictionary containing captured artifacts
    """
    artifacts: dict[str, Any] = {
        "test_name": test_name,
        "command": " ".join(result.command),
        "exit_code": result.exit_code,
        "timed_out": result.timed_out,
        "duration_seconds": result.duration_seconds,
        "stdout": result.redacted_stdout(),
        "stderr": result.redacted_stderr(),
        "cwd": str(result.cwd) if result.cwd else None,
    }

    if project_path and project_path.exists():
        # Capture project artifacts
        config_dir = project_path / ".tapps-agents"
        if config_dir.exists():
            artifacts["project_artifacts"] = {
                "logs": [str(f) for f in (config_dir / "logs").glob("*.log") if (config_dir / "logs").exists()],
                "state": [str(f) for f in config_dir.glob("**/*.json")],
            }

    return artifacts

