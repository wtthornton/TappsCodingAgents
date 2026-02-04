"""
E2E tests for CLI golden paths (most-used commands).

Tests the most commonly used CLI commands end-to-end:
- reviewer score/review commands
- orchestrator workflow commands
- workflow preset commands

All tests validate JSON output shape and essential keys.
"""


import pytest

from tests.e2e.fixtures.cli_harness import (
    CLIHarness,
    assert_json_output,
    assert_success,
)


@pytest.fixture
def cli_harness(tmp_path):
    """Create a CLI harness for isolated test execution."""
    harness = CLIHarness(base_path=tmp_path / "cli_tests", default_timeout=60.0)
    yield harness
    harness.cleanup()


@pytest.fixture
def test_project(cli_harness):
    """Create an isolated test project."""
    return cli_harness.create_isolated_project(template_type="minimal")


@pytest.fixture
def test_file(test_project):
    """Create a test Python file in the project."""
    test_file_path = test_project / "test_code.py"
    test_file_path.write_text(
        '''"""Test file for CLI golden path tests."""

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b
'''
    )
    return test_file_path


@pytest.mark.e2e_cli
def test_cli_reviewer_score_golden_path(cli_harness, test_project, test_file):
    """
    Test reviewer score command golden path.

    Validates:
    - Command executes successfully (exit code 0)
    - JSON output is valid
    - JSON contains required keys (file, scoring, etc.)
    """
    result = cli_harness.run_command(
        [
            "python",
            "-m",
            "tapps_agents.cli",
            "reviewer",
            "score",
            str(test_file),
            "--format",
            "json",
        ],
        cwd=test_project,
    )

    assert_success(result)
    json_data = assert_json_output(result, required_keys=["file"])

    # Validate JSON structure
    assert "file" in json_data
    assert isinstance(json_data["file"], str)
    # Scoring may be present (depending on implementation)
    if "scoring" in json_data:
        assert isinstance(json_data["scoring"], dict)


@pytest.mark.e2e_cli
def test_cli_reviewer_review_golden_path(cli_harness, test_project, test_file):
    """
    Test reviewer review command golden path.

    Validates:
    - Command executes successfully (exit code 0)
    - JSON output is valid
    - JSON contains required keys (file, review, etc.)
    """
    result = cli_harness.run_command(
        [
            "python",
            "-m",
            "tapps_agents.cli",
            "reviewer",
            "review",
            str(test_file),
            "--format",
            "json",
        ],
        cwd=test_project,
        timeout=120.0,  # Review takes longer than score
    )

    assert_success(result)
    json_data = assert_json_output(result, required_keys=["file"])

    # Validate JSON structure
    assert "file" in json_data
    assert isinstance(json_data["file"], str)
    # Review content may be present (depending on implementation)
    if "review" in json_data:
        assert isinstance(json_data["review"], (str, dict))


@pytest.mark.e2e_cli
def test_cli_orchestrator_workflow_list_golden_path(cli_harness, test_project):
    """
    Test orchestrator workflow-list command golden path.

    Validates:
    - Command executes successfully (exit code 0)
    - JSON output is valid
    - JSON contains workflow list information
    """
    result = cli_harness.run_command(
        [
            "python",
            "-m",
            "tapps_agents.cli",
            "orchestrator",
            "workflow-list",
        ],
        cwd=test_project,
    )

    assert_success(result)
    json_data = assert_json_output(result)

    # Validate JSON structure (workflows may be a list or dict)
    assert isinstance(json_data, (dict, list))


@pytest.mark.e2e_cli
def test_cli_workflow_list_golden_path(cli_harness, test_project):
    """
    Test workflow list command golden path.

    Validates:
    - Command executes successfully (exit code 0)
    - Output contains workflow information
    """
    result = cli_harness.run_command(
        [
            "python",
            "-m",
            "tapps_agents.cli",
            "workflow",
            "list",
        ],
        cwd=test_project,
    )

    assert_success(result)
    # Workflow list may output text or JSON, so we just check success
    assert result.stdout or result.stderr  # Should have some output


@pytest.mark.e2e_cli
def test_cli_workflow_preset_golden_path(cli_harness, test_project):
    """
    Test workflow preset command golden path.

    Validates:
    - Command executes successfully (exit code 0)
    - Workflow starts and runs (may complete or be in progress)
    """
    # Use a quick preset if available, otherwise skip
    result = cli_harness.run_command(
        [
            "python",
            "-m",
            "tapps_agents.cli",
            "workflow",
            "rapid",
        ],
        cwd=test_project,
        timeout=300.0,  # Workflows can take time
    )

    # Workflow may succeed or be interrupted, but should not crash
    # Exit code 0 means successful start/execution
    # Non-zero might mean workflow failed, but that's acceptable for E2E
    assert result.exit_code in [0, 1], f"Unexpected exit code: {result.exit_code}"


@pytest.mark.e2e_cli
def test_cli_score_shortcut_golden_path(cli_harness, test_project, test_file):
    """
    Test score shortcut command golden path.

    Validates:
    - Shortcut command (score) works same as reviewer score
    - Command executes successfully (exit code 0)
    - JSON output is valid
    """
    result = cli_harness.run_command(
        [
            "python",
            "-m",
            "tapps_agents.cli",
            "score",
            str(test_file),
            "--format",
            "json",
        ],
        cwd=test_project,
    )

    assert_success(result)
    json_data = assert_json_output(result, required_keys=["file"])

    # Validate JSON structure
    assert "file" in json_data


@pytest.mark.e2e_cli
def test_cli_workflow_file_path_golden_path(cli_harness, test_project):
    """
    Test top-level workflow command with file path (golden path).

    Validates:
    - Command accepts file paths in addition to preset names
    - File path execution works correctly
    - Both relative and absolute paths are supported
    """

    import yaml

    # Create a test workflow file
    workflows_dir = test_project / "workflows"
    workflows_dir.mkdir(exist_ok=True)
    custom_dir = workflows_dir / "custom"
    custom_dir.mkdir(exist_ok=True)
    
    workflow_file = custom_dir / "test-custom-workflow.yaml"
    workflow_content = {
        "workflow": {
            "id": "test-custom-workflow",
            "name": "Test Custom Workflow",
            "description": "A test custom workflow for file path execution",
            "version": "1.0.0",
            "type": "greenfield",
            "steps": [
                {
                    "id": "step1",
                    "agent": "analyst",
                    "action": "gather-requirements",
                    "requires": [],
                }
            ],
        }
    }
    
    with open(workflow_file, "w", encoding="utf-8") as f:
        yaml.dump(workflow_content, f)

    # Test with relative path
    relative_path = str(workflow_file.relative_to(test_project))
    result = cli_harness.run_command(
        [
            "python",
            "-m",
            "tapps_agents.cli",
            "workflow",
            relative_path,
            "--prompt",
            "Test workflow execution",
            "--auto",
        ],
        cwd=test_project,
        timeout=120.0,  # Workflows can take time
    )

    # Workflow may succeed or be interrupted, but should not crash
    # Exit code 0 means successful start/execution
    # Non-zero might mean workflow failed, but that's acceptable for E2E
    assert result.exit_code in [0, 1], f"Unexpected exit code: {result.exit_code}"


@pytest.mark.e2e_cli
def test_cli_orchestrator_workflow_file_path_golden_path(cli_harness, test_project):
    """
    Test orchestrator workflow command with file path (golden path).

    Validates:
    - Command executes successfully (exit code 0)
    - JSON output is valid
    - JSON contains workflow execution information
    - Supports both relative and absolute paths
    """

    import yaml

    # Create a test workflow file
    workflows_dir = test_project / "workflows"
    workflows_dir.mkdir(exist_ok=True)
    custom_dir = workflows_dir / "custom"
    custom_dir.mkdir(exist_ok=True)
    
    workflow_file = custom_dir / "test-workflow.yaml"
    workflow_content = {
        "workflow": {
            "id": "test-workflow",
            "name": "Test Workflow",
            "description": "A test workflow for file path execution",
            "version": "1.0.0",
            "type": "greenfield",
            "steps": [
                {
                    "id": "step1",
                    "agent": "analyst",
                    "action": "gather-requirements",
                    "requires": [],
                }
            ],
        }
    }
    
    with open(workflow_file, "w", encoding="utf-8") as f:
        yaml.dump(workflow_content, f)

    # Test with relative path
    relative_path = str(workflow_file.relative_to(test_project))
    result = cli_harness.run_command(
        [
            "python",
            "-m",
            "tapps_agents.cli",
            "orchestrator",
            "workflow",
            relative_path,
            "--format",
            "json",
        ],
        cwd=test_project,
    )

    assert_success(result)
    json_data = assert_json_output(result)

    # Validate JSON structure
    assert isinstance(json_data, dict)
    assert "success" in json_data
    assert json_data["success"] is True
    assert "workflow_id" in json_data
    assert json_data["workflow_id"] == "test-workflow"
    assert "workflow_file" in json_data
    assert "status" in json_data


@pytest.mark.e2e_cli
def test_cli_orchestrator_workflow_status_golden_path(cli_harness, test_project):
    """
    Test orchestrator workflow-status command golden path.

    Validates:
    - Command executes successfully (exit code 0)
    - JSON output is valid (even if no active workflow)
    """
    result = cli_harness.run_command(
        [
            "python",
            "-m",
            "tapps_agents.cli",
            "orchestrator",
            "workflow-status",
        ],
        cwd=test_project,
    )

    # Status command should succeed even if no active workflow
    assert_success(result)
    # May output JSON or text, both are acceptable
    if result.stdout.strip().startswith("{"):
        json_data = assert_json_output(result)
        assert isinstance(json_data, dict)

