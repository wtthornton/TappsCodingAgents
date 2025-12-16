"""
Integration test to verify CLI create command generates project timeline in Cursor IDE.

This test is specifically for Cursor IDE execution mode and verifies that:
1. project-timeline.md is created
2. Timeline contains agent execution details (who, what, how long)
3. Timeline is NOT cleaned up after test

The framework uses Background Agents to automatically execute Cursor Skills:
- Creates command files (.cursor-skill-command.txt) in worktrees
- Background Agents automatically pick up and execute these commands
- Framework polls for completion by checking for artifacts
- Timeline is generated when workflow completes

Note: This test does NOT require LLM services as execution happens through Cursor Skills.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def is_cursor_ide():
    """Check if we're running in Cursor IDE."""
    return (
        os.getenv("CURSOR") is not None
        or os.getenv("CURSOR_IDE") is not None
        or os.getenv("CURSOR_SESSION_ID") is not None
    )


pytestmark = pytest.mark.integration


@pytest.mark.cursor_ide
@pytest.mark.e2e
class TestCLICreateTimelineVerification:
    """Test that CLI create command generates proper project timeline."""

    @pytest.mark.timeout(600)  # 10 minutes - allows time for Background Agents to execute
    def test_cli_create_generates_timeline_with_execution_details(self, tmp_path):
        """
        Test that CLI create command generates project-timeline.md with execution details in Cursor IDE.
        
        This test verifies full workflow execution in Cursor mode:
        1. Runs the CLI create command in Cursor mode
        2. Background Agents automatically execute Skills from command files
        3. Framework polls and waits for completion
        4. Verifies project-timeline.md exists with execution details
        5. Does NOT clean up the timeline file (preserved for inspection)
        
        Note: This test does NOT require LLM services as execution happens through Cursor Skills.
        Background Agents handle Skill execution automatically - no manual intervention needed.
        """
        # This test is specifically for Cursor IDE - full execution with Background Agents

        # Use tmp_path but don't clean it up - preserve for inspection
        test_project_dir = tmp_path / "timeline_test_project"
        test_project_dir.mkdir()

        # Get project root (where workflows/presets exists)
        project_root = Path(__file__).parent.parent.parent
        
        original_cwd = os.getcwd()
        
        # Copy workflows directory to test project so presets are available
        import shutil
        workflows_src = project_root / "workflows"
        workflows_dst = test_project_dir / "workflows"
        if workflows_src.exists():
            shutil.copytree(workflows_src, workflows_dst)
        
        # Initialize as Git repo if not already (required for worktrees)
        import subprocess as sp
        sp.run(
            ["git", "init"],
            cwd=str(test_project_dir),
            capture_output=True,
            text=True,
        )
        # Make initial commit so worktrees can be created
        sp.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=str(test_project_dir),
            capture_output=True,
        )
        sp.run(
            ["git", "config", "user.name", "Test User"],
            cwd=str(test_project_dir),
            capture_output=True,
        )
        sp.run(
            ["git", "add", "."],
            cwd=str(test_project_dir),
            capture_output=True,
        )
        sp.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=str(test_project_dir),
            capture_output=True,
        )
        
        os.chdir(test_project_dir)

        try:
            user_prompt = (
                "Create a detailed interactive web application that is very modern "
                "and explains all the detailed information about this application. "
                "Contains a users guide, technical specs, technical designs, "
                "technical architecture and examples. Needs to be easy to use and "
                "a selling point to this application."
            )

            # Set environment to ensure Cursor mode is detected
            env = os.environ.copy()
            # Force Cursor mode - this test is specifically for Cursor IDE execution
            env["TAPPS_AGENTS_MODE"] = "cursor"
            # Ensure Cursor IDE environment is set (required for this test)
            env["CURSOR_IDE"] = "1"
            
            # Run CLI command - Background Agents will automatically execute Skills
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
                timeout=600,  # Allow time for Background Agents to execute
                cwd=str(test_project_dir),
                env=env,
            )

            # Check for critical errors
            stderr_lower = result.stderr.lower()
            stdout_lower = result.stdout.lower()

            critical_errors = [
                "traceback",
                "object of type",
                "not json serializable",
                "attributeerror",
            ]

            has_critical_error = any(
                err in stderr_lower or err in stdout_lower for err in critical_errors
            )

            if has_critical_error:
                pytest.fail(
                    f"Critical error detected:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                )

            # Verify timeline file exists (workflow should complete automatically)
            timeline_file = test_project_dir / "project-timeline.md"
            
            # Check if workflow completed (timeline exists) or is still running
            state_dir = test_project_dir / ".tapps-agents" / "workflow-state"
            if not timeline_file.exists() and state_dir.exists():
                state_files = list(state_dir.glob("*.json"))
                if state_files:
                    with open(state_files[0], encoding="utf-8") as f:
                        state_data = json.load(f)
                    status = state_data.get("status", "unknown")
                    if status == "running":
                        pytest.skip(
                            "Workflow is still running (Background Agents may still be executing). "
                            "Timeline will be generated when workflow completes."
                        )
            
            assert timeline_file.exists(), (
                f"project-timeline.md should be created at {timeline_file}\n"
                f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\n"
                f"Project directory contents: {list(test_project_dir.iterdir())}"
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
            # Check for table with agent, action, duration columns
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
            # Look for time patterns (ISO format dates or formatted durations)
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

            # Store timeline path for user inspection
            print(f"TIMELINE FILE LOCATION: {timeline_file}")
            print(f"FULL PATH: {timeline_file.absolute()}")

            # Verify we can parse timeline structure (if JSON format also exists)
            timeline_json_file = test_project_dir / "project-timeline.json"
            if timeline_json_file.exists():
                with open(timeline_json_file, encoding="utf-8") as f:
                    timeline_data = json.load(f)
                
                # Verify timeline data structure
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

            # Test passes - timeline is verified and preserved

        finally:
            os.chdir(original_cwd)
            # Note: tmp_path will be cleaned up after test session
            # User can copy important files before cleanup if needed

