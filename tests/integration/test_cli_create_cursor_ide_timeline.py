"""
Integration test for CLI create command in Cursor IDE with timeline verification.

This test is designed to run in the actual Cursor IDE environment (billstest directory)
and verifies that:
1. project-timeline.md is created
2. Timeline contains agent execution details (who, what, how long)
3. Timeline is preserved for inspection
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


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


def is_cursor_ide():
    """Check if we're running in Cursor IDE."""
    return (
        os.getenv("CURSOR") is not None
        or os.getenv("CURSOR_IDE") is not None
        or os.getenv("CURSOR_SESSION_ID") is not None
    )


pytestmark = pytest.mark.integration


@pytest.mark.requires_llm
@pytest.mark.e2e
class TestCLICreateCursorIDETimeline:
    """
    Test CLI create command in Cursor IDE environment.
    
    This test should run in the actual project directory (billstest) where
    Git is properly initialized and workflows are available.
    """

    @pytest.mark.timeout(600)  # 10 minutes
    def test_cli_create_generates_timeline_in_cursor_ide(self):
        """
        Test that CLI create command generates project-timeline.md in Cursor IDE.
        
        This test runs in the actual project directory (billstest) where:
        - Git is properly initialized
        - Workflow presets are available
        - Cursor IDE environment is active
        
        The timeline file is preserved in the project directory for inspection.
        """
        if not has_any_llm():
            pytest.skip("No LLM service available")

        # Get the project directory (should be billstest when running from Cursor)
        # Or use current working directory
        project_dir = Path.cwd()
        
        # Check if we're in a project directory with workflows
        workflows_dir = project_dir / "workflows"
        if not workflows_dir.exists():
            # Try parent directory
            parent_workflows = project_dir.parent / "workflows"
            if parent_workflows.exists():
                project_dir = project_dir.parent
        
        # Verify workflows exist
        if not (project_dir / "workflows" / "presets").exists():
            pytest.skip(
                f"Workflow presets not found. Expected at {project_dir / 'workflows' / 'presets'}"
            )

        original_cwd = os.getcwd()
        os.chdir(project_dir)

        try:
            user_prompt = (
                "Create a detailed interactive web application that is very modern "
                "and explains all the detailed information about this application. "
                "Contains a users guide, technical specs, technical designs, "
                "technical architecture and examples. Needs to be easy to use and "
                "a selling point to this application."
            )

            # Ensure Cursor mode is enabled
            env = os.environ.copy()
            env["TAPPS_AGENTS_MODE"] = "cursor"
            if "CURSOR_IDE" not in env:
                env["CURSOR_IDE"] = "1"

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
                timeout=600,
                cwd=str(project_dir),
                env=env,
            )

            # Check for critical errors
            stderr_lower = result.stderr.lower()
            stdout_lower = result.stdout.lower()

            critical_errors = [
                "traceback",
                "object of type",
                "not json serializable",
                "attributeerror.*path",
            ]

            has_critical_error = any(
                err in stderr_lower or err in stdout_lower for err in critical_errors
            )

            if has_critical_error:
                pytest.fail(
                    f"Critical error detected:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                )

            # Verify timeline file exists
            timeline_file = project_dir / "project-timeline.md"
            
            # Note: Timeline is only created if workflow completes successfully
            # If workflow failed or is still running, timeline won't exist yet
            if not timeline_file.exists():
                # Check if workflow is still running or failed
                state_dir = project_dir / ".tapps-agents" / "workflow-state"
                if state_dir.exists():
                    state_files = list(state_dir.glob("full-sdlc-*.json"))
                    if state_files:
                        # Try to load state to see status
                        try:
                            with open(state_files[0], encoding="utf-8") as f:
                                state_data = json.load(f)
                            status = state_data.get("status", "unknown")
                            if status == "running":
                                pytest.skip(
                                    "Workflow is still running. Timeline will be generated when workflow completes."
                                )
                            elif status == "failed":
                                pytest.fail(
                                    f"Workflow failed with status: {status}\n"
                                    f"Error: {state_data.get('error', 'Unknown')}\n"
                                    f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                                )
                        except Exception:
                            pass
                
                pytest.fail(
                    f"project-timeline.md was not created at {timeline_file}\n"
                    f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\n"
                    f"Project directory contents: {list(project_dir.iterdir())}"
                )

            # Read and verify timeline content
            timeline_content = timeline_file.read_text(encoding="utf-8")
            
            # Verify timeline contains required sections
            assert "Project Timeline" in timeline_content, (
                "Timeline should contain 'Project Timeline' header"
            )
            
            assert "Workflow" in timeline_content, (
                "Timeline should contain workflow information"
            )

            assert "Agent Execution Timeline" in timeline_content, (
                "Timeline should contain 'Agent Execution Timeline' section"
            )

            # Verify timeline contains agent execution details
            assert "| Step ID | Agent | Action |" in timeline_content or "| Step" in timeline_content, (
                "Timeline should contain execution table with agent and action columns"
            )

            # Check for duration information
            assert "Duration" in timeline_content or "duration" in timeline_content.lower(), (
                "Timeline should contain duration information"
            )

            # Verify specific SDLC agents are mentioned
            sdlc_agents = ["analyst", "planner", "architect", "implementer", "reviewer", "tester"]
            found_agents = [agent for agent in sdlc_agents if agent.lower() in timeline_content.lower()]
            
            assert len(found_agents) > 0, (
                f"Timeline should mention SDLC agents. Found: {found_agents}\n"
                f"Timeline content:\n{timeline_content[:1000]}"
            )

            # Verify timeline contains timing information
            import re
            time_patterns = [
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",  # ISO datetime
                r"\d+\.\d+s",  # Seconds format
                r"\d+\.\d+m",  # Minutes format
            ]
            
            has_timing = any(re.search(pattern, timeline_content) for pattern in time_patterns)
            assert has_timing, (
                "Timeline should contain timing information (dates/times/durations)\n"
                f"Timeline content:\n{timeline_content[:1000]}"
            )

            # Verify summary statistics section
            assert "Summary Statistics" in timeline_content or "Summary" in timeline_content, (
                "Timeline should contain summary statistics"
            )

            # Print timeline content for inspection
            print(f"\n{'='*80}")
            print(f"PROJECT TIMELINE GENERATED (preserved at: {timeline_file})")
            print(f"{'='*80}")
            print(timeline_content)
            print(f"{'='*80}\n")

            # Verify timeline JSON structure if it exists
            timeline_json_file = project_dir / "project-timeline.json"
            if timeline_json_file.exists():
                with open(timeline_json_file, encoding="utf-8") as f:
                    timeline_data = json.load(f)
                
                assert "workflow_id" in timeline_data, "Timeline JSON should have workflow_id"
                assert "steps" in timeline_data, "Timeline JSON should have steps"
                
                if timeline_data["steps"]:
                    step = timeline_data["steps"][0]
                    assert "agent" in step, "Step should have agent"
                    assert "action" in step, "Step should have action"
                    assert "started_at" in step, "Step should have started_at"
                    assert "duration_seconds" in step or "duration_formatted" in step, (
                        "Step should have duration information"
                    )
                    
                    # Print step details
                    print("\nFirst step execution details:")
                    print(f"  Agent: {step.get('agent')}")
                    print(f"  Action: {step.get('action')}")
                    print(f"  Started: {step.get('started_at')}")
                    print(f"  Duration: {step.get('duration_formatted', step.get('duration_seconds'))}")
                    print(f"  Status: {step.get('status')}")

            # Timeline is verified and preserved in project directory
            print(f"\n✓ Timeline file preserved at: {timeline_file.absolute()}")

        finally:
            os.chdir(original_cwd)
            # Timeline file is NOT cleaned up - it remains in the project directory

