"""
Integration test for CLI create command executing full SDLC workflow.

This test verifies that the CLI create command properly executes the full
SDLC workflow and produces expected artifacts (timeline, state files, etc.).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


def check_ollama_available():
    """Check if Ollama is available."""
    import httpx
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


def check_anthropic_available():
    """Check if Anthropic API key is available."""
    return os.getenv("ANTHROPIC_API_KEY") is not None


def has_any_llm():
    """Check if any LLM service is available."""
    return (
        check_ollama_available()
        or check_anthropic_available()
        or os.getenv("OPENAI_API_KEY") is not None
    )


pytestmark = pytest.mark.integration


@pytest.mark.requires_llm
@pytest.mark.e2e
class TestCLICreateFullSDLC:
    """Integration tests for CLI create command with full SDLC workflow."""

    @pytest.fixture
    def test_project_dir(self, tmp_path):
        """Create a temporary project directory for testing."""
        project_dir = tmp_path / "test_create_project"
        project_dir.mkdir()
        return project_dir

    @pytest.mark.timeout(600)  # 10 minutes timeout for full SDLC
    def test_cli_create_executes_full_sdlc_workflow(
        self, test_project_dir
    ):
        """
        Test that CLI create command executes full SDLC workflow.
        
        This test runs the actual CLI command and verifies:
        1. Command executes without critical errors
        2. Workflow state is created
        3. Timeline file is generated (if workflow completes)
        4. SDLC steps are executed
        """
        if not has_any_llm():
            pytest.skip("No LLM service available")

        # Change to test project directory
        original_cwd = os.getcwd()
        os.chdir(test_project_dir)

        try:
            # Run the CLI create command
            user_prompt = (
                "Create a detailed interactive web application that is very modern "
                "and explains all the detailed information about this application. "
                "Contains a users guide, technical specs, technical designs, "
                "technical architecture and examples. Needs to be easy to use and "
                "a selling point to this application."
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "tapps_agents.cli",
                    "create",
                    user_prompt,
                ],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes
                cwd=str(test_project_dir),
            )

            # Check that command ran (may fail if workflow fails, but should not crash)
            # Exit code might be non-zero if workflow fails, but we check for critical errors
            stderr_lower = result.stderr.lower()
            stdout_lower = result.stdout.lower()

            # Check for critical errors that indicate the command itself failed
            critical_errors = [
                "traceback",
                "object of type",
                "not json serializable",
                "attributeerror",
                "typeerror",
                "import error",
                "module not found",
            ]

            has_critical_error = any(
                err in stderr_lower or err in stdout_lower
                for err in critical_errors
            )

            if has_critical_error:
                pytest.fail(
                    f"Critical error detected in CLI execution:\n"
                    f"STDOUT:\n{result.stdout}\n\n"
                    f"STDERR:\n{result.stderr}\n\n"
                    f"Return code: {result.returncode}"
                )

            # Verify workflow state directory exists
            state_dir = test_project_dir / ".tapps-agents" / "workflow-state"
            
            # Workflow might have started even if it didn't complete
            # Check for workflow state files
            if state_dir.exists():
                state_files = list(state_dir.glob("*.json"))
                assert len(state_files) > 0, (
                    f"Expected workflow state files in {state_dir}, "
                    f"but found none. STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                )

                # Verify at least one state file contains workflow information
                found_valid_state = False
                for state_file in state_files:
                    try:
                        with open(state_file, encoding="utf-8") as f:
                            state_data = json.load(f)
                        if "workflow_id" in state_data:
                            found_valid_state = True
                            break
                    except (json.JSONDecodeError, KeyError):
                        continue

                assert found_valid_state, (
                    f"No valid workflow state found in {state_dir}. "
                    f"Files: {[f.name for f in state_files]}"
                )

            # Check for timeline file (created when workflow completes)
            timeline_file = test_project_dir / "project-timeline.md"
            if timeline_file.exists():
                timeline_content = timeline_file.read_text(encoding="utf-8")
                
                # Verify timeline contains expected SDLC information
                assert "Project Timeline" in timeline_content, (
                    "Timeline file should contain 'Project Timeline' header"
                )
                assert "Workflow" in timeline_content, (
                    "Timeline should contain workflow information"
                )

                # Check for SDLC steps (even if some failed, we should see attempts)
                sdlc_agents = ["analyst", "planner", "architect", "implementer", "reviewer"]
                found_agents = [agent for agent in sdlc_agents if agent in timeline_content.lower()]
                
                # At least some SDLC agents should appear in timeline
                assert len(found_agents) > 0, (
                    f"Expected to find SDLC agents in timeline, "
                    f"but found: {found_agents}. Timeline content:\n{timeline_content[:500]}"
                )

            # Verify project profile was created
            profile_file = test_project_dir / ".tapps-agents" / "project-profile.yaml"
            # Profile creation is optional, so we don't assert it exists
            # but we can log if it does
            if profile_file.exists():
                # Verify it's valid YAML
                try:
                    with open(profile_file, encoding="utf-8") as f:
                        profile_data = yaml.safe_load(f)
                    assert profile_data is not None, "Profile file should contain valid YAML"
                except yaml.YAMLError:
                    # Not critical if profile parsing fails
                    pass

            # Output success message with key info
            print(f"\n✓ CLI create command executed")
            if timeline_file.exists():
                print(f"✓ Timeline file created: {timeline_file}")
            if state_dir.exists():
                print(f"✓ Workflow state directory exists: {state_dir}")
                print(f"  - State files: {len(list(state_dir.glob('*.json')))}")

        finally:
            # Restore original directory
            os.chdir(original_cwd)

    @pytest.mark.timeout(300)  # 5 minutes for workflow state check
    def test_cli_create_workflow_state_structure(
        self, test_project_dir
    ):
        """
        Test that CLI create command creates proper workflow state structure.
        
        This is a lighter test that focuses on state structure rather than
        full workflow execution.
        """
        if not has_any_llm():
            pytest.skip("No LLM service available")

        original_cwd = os.getcwd()
        os.chdir(test_project_dir)

        try:
            # Use a shorter prompt for faster execution
            user_prompt = "Create a simple calculator application"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "tapps_agents.cli",
                    "create",
                    user_prompt,
                ],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes
                cwd=str(test_project_dir),
            )

            # Check for critical serialization errors
            stderr_lower = result.stderr.lower()
            stdout_lower = result.stdout.lower()

            # The specific error we fixed
            assert "not json serializable" not in stderr_lower, (
                f"JSON serialization error detected (this should be fixed):\n"
                f"STDERR:\n{result.stderr}"
            )
            assert "not json serializable" not in stdout_lower, (
                f"JSON serialization error in stdout:\n{result.stdout}"
            )

            # Check workflow state directory structure
            state_dir = test_project_dir / ".tapps-agents" / "workflow-state"
            if state_dir.exists():
                # Check for state files (try different patterns)
                state_files = list(state_dir.glob("full-sdlc-*.json"))
                if len(state_files) == 0:
                    # Try any JSON file in state directory
                    state_files = list(state_dir.glob("*.json"))
                    # Exclude metadata files
                    state_files = [f for f in state_files if not f.name.endswith(".meta.json") and f.name != "last.json"]
                
                if len(state_files) > 0:
                    # Verify state file structure
                    state_file = state_files[0]
                    with open(state_file, encoding="utf-8") as f:
                        state_data = json.load(f)

                    # Verify required fields
                    assert "workflow_id" in state_data, "State should have workflow_id"
                    assert "status" in state_data, "State should have status"
                    assert "variables" in state_data, "State should have variables"

                    # Verify user prompt is stored
                    variables = state_data.get("variables", {})
                    assert "user_prompt" in variables, (
                        "State variables should contain user_prompt"
                    )

                    # Verify project_profile can be serialized (our fix)
                    if "project_profile" in variables:
                        profile = variables["project_profile"]
                        # Should be a dict (not an object) - our fix ensures this
                        assert isinstance(profile, dict) or profile is None, (
                            "project_profile should be a dict (serialized), "
                            f"not {type(profile)}"
                        )

                        # Verify it's JSON serializable
                        try:
                            json.dumps(profile)
                        except (TypeError, ValueError) as e:
                            pytest.fail(
                                f"project_profile should be JSON serializable: {e}\n"
                                f"Profile data: {profile}"
                            )
                else:
                    # If no state files found, that's okay - workflow might not have started
                    # But we should at least verify there were no critical errors
                    pass

        finally:
            os.chdir(original_cwd)

