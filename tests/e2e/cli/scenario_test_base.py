"""
Base class for multi-step workflow scenario testing.

Provides utilities for testing complex scenarios that involve
multiple commands and artifact verification.
"""

import pytest
from pathlib import Path
from typing import Any

from tests.e2e.cli.test_base import CLICommandTestBase
from tests.e2e.cli.validation_helpers import assert_file_exists, assert_file_content


class ScenarioTestBase(CLICommandTestBase):
    """Base class for scenario tests with multi-step validation."""

    @pytest.fixture(autouse=True)
    def setup_scenario_state(self):
        """Set up scenario test state."""
        self.scenario_steps: list[dict[str, Any]] = []
        self.scenario_artifacts: dict[str, Path] = {}
        yield
        # Cleanup if needed

    def record_step(self, step_name: str, command: list[str], result: Any) -> None:
        """
        Record a scenario step for tracking.
        
        Args:
            step_name: Name of the step
            command: Command that was run
            result: Result of the command
        """
        self.scenario_steps.append({
            "name": step_name,
            "command": command,
            "result": result,
        })

    def verify_artifact(self, artifact_name: str, file_path: Path, min_length: int | None = None) -> str:
        """
        Verify that an artifact file exists and optionally check content.
        
        Args:
            artifact_name: Name of the artifact
            file_path: Path to artifact file
            min_length: Optional minimum file length
            
        Returns:
            File content
            
        Raises:
            AssertionError: If artifact doesn't exist or content invalid
        """
        assert_file_exists(file_path, description=artifact_name)
        content = file_path.read_text()
        
        if min_length is not None:
            assert len(content) >= min_length, (
                f"Artifact '{artifact_name}' content too short. "
                f"Expected >= {min_length}, got {len(content)}"
            )
        
        self.scenario_artifacts[artifact_name] = file_path
        return content

    def verify_step_success(self, step_name: str) -> dict[str, Any]:
        """
        Verify that a recorded step succeeded.
        
        Args:
            step_name: Name of the step to verify
            
        Returns:
            Step information
            
        Raises:
            AssertionError: If step not found or failed
        """
        step = next((s for s in self.scenario_steps if s["name"] == step_name), None)
        assert step is not None, f"Step '{step_name}' not found in scenario"
        
        # Check if result has success indicator
        result = step["result"]
        if hasattr(result, "exit_code"):
            assert result.exit_code == 0, f"Step '{step_name}' failed with exit code {result.exit_code}"
        
        return step

    def get_scenario_summary(self) -> dict[str, Any]:
        """
        Get summary of scenario execution.
        
        Returns:
            Dictionary with scenario summary
        """
        return {
            "total_steps": len(self.scenario_steps),
            "steps": [
                {
                    "name": step["name"],
                    "command": " ".join(step["command"]),
                    "success": (
                        step["result"].exit_code == 0
                        if hasattr(step["result"], "exit_code")
                        else True
                    ),
                }
                for step in self.scenario_steps
            ],
            "artifacts": {
                name: str(path)
                for name, path in self.scenario_artifacts.items()
            },
        }

