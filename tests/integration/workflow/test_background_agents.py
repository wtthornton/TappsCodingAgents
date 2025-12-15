"""
Integration tests for Background Quality and Testing Agents.

Tests the full flow: agent execution, artifact generation, and completion detection.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tapps_agents.workflow.background_quality_agent import BackgroundQualityAgent
from tapps_agents.workflow.background_testing_agent import BackgroundTestingAgent
from tapps_agents.workflow.cursor_skill_helper import check_skill_completion


@pytest.mark.integration
@pytest.mark.asyncio
async def test_background_quality_agent_creates_artifact(tmp_path: Path) -> None:
    """Test that quality agent creates artifact file."""
    # Create a simple Python file to analyze
    test_file = tmp_path / "test_code.py"
    test_file.write_text(
        """
def hello_world():
    print("Hello, World!")
    return True
""",
        encoding="utf-8",
    )

    agent = BackgroundQualityAgent(
        worktree_path=tmp_path,
        correlation_id="test-quality-001",
        timeout_seconds=60.0,
    )

    artifact = await agent.run_quality_analysis(target_path=test_file)

    # Verify artifact was created
    assert artifact.status in ["completed", "failed", "timeout"]
    assert artifact.worktree_path == str(tmp_path)
    assert artifact.correlation_id == "test-quality-001"

    # Verify artifact file exists
    artifact_path = tmp_path / "reports" / "quality" / "quality-report.json"
    assert artifact_path.exists()

    # Verify artifact can be loaded
    with open(artifact_path, encoding="utf-8") as f:
        loaded_data = json.load(f)

    assert loaded_data["schema_version"] == "1.0"
    assert loaded_data["worktree_path"] == str(tmp_path)


@pytest.mark.asyncio
async def test_background_testing_agent_creates_artifact(tmp_path: Path) -> None:
    """Test that testing agent creates artifact file."""
    # Create a simple test file
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    test_file = tests_dir / "test_example.py"
    test_file.write_text(
        """
import pytest

def test_example():
    assert True
""",
        encoding="utf-8",
    )

    agent = BackgroundTestingAgent(
        worktree_path=tmp_path,
        correlation_id="test-testing-001",
        timeout_seconds=60.0,
    )

    artifact = await agent.run_tests(test_path=tests_dir, coverage=False)

    # Verify artifact was created
    assert artifact.status in ["completed", "failed", "timeout", "not_run"]
    assert artifact.worktree_path == str(tmp_path)
    assert artifact.correlation_id == "test-testing-001"

    # Verify artifact file exists (if tests ran)
    artifact_path = tmp_path / "reports" / "tests" / "test-report.json"
    if artifact.status != "not_run":
        assert artifact_path.exists()

        # Verify artifact can be loaded
        with open(artifact_path, encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data["schema_version"] == "1.0"
        assert loaded_data["worktree_path"] == str(tmp_path)


@pytest.mark.asyncio
async def test_skill_completion_detection_quality(tmp_path: Path) -> None:
    """Test that skill completion detection finds quality artifacts."""
    # Create artifact directory and file
    reports_dir = tmp_path / "reports" / "quality"
    reports_dir.mkdir(parents=True, exist_ok=True)

    artifact_path = reports_dir / "quality-report.json"
    artifact_data = {
        "schema_version": "1.0",
        "status": "completed",
        "worktree_path": str(tmp_path),
    }
    artifact_path.write_text(json.dumps(artifact_data), encoding="utf-8")

    # Check completion
    completion = check_skill_completion(worktree_path=tmp_path)

    assert completion["completed"] is True
    assert "reports/quality/quality-report.json" in completion["found_artifacts"]


@pytest.mark.asyncio
async def test_skill_completion_detection_testing(tmp_path: Path) -> None:
    """Test that skill completion detection finds testing artifacts."""
    # Create artifact directory and file
    reports_dir = tmp_path / "reports" / "tests"
    reports_dir.mkdir(parents=True, exist_ok=True)

    artifact_path = reports_dir / "test-report.json"
    artifact_data = {
        "schema_version": "1.0",
        "status": "completed",
        "worktree_path": str(tmp_path),
    }
    artifact_path.write_text(json.dumps(artifact_data), encoding="utf-8")

    # Check completion
    completion = check_skill_completion(worktree_path=tmp_path)

    assert completion["completed"] is True
    assert "reports/tests/test-report.json" in completion["found_artifacts"]


@pytest.mark.asyncio
async def test_quality_agent_timeout(tmp_path: Path) -> None:
    """Test that quality agent respects timeout."""
    agent = BackgroundQualityAgent(
        worktree_path=tmp_path,
        timeout_seconds=0.1,  # Very short timeout
    )

    # This should timeout quickly
    artifact = await agent.run_quality_analysis()

    assert artifact.status == "timeout"
    assert artifact.timeout is True


@pytest.mark.asyncio
async def test_testing_agent_timeout(tmp_path: Path) -> None:
    """Test that testing agent respects timeout."""
    agent = BackgroundTestingAgent(
        worktree_path=tmp_path,
        timeout_seconds=0.1,  # Very short timeout
    )

    # This should timeout quickly
    artifact = await agent.run_tests()

    assert artifact.status == "timeout"
    assert artifact.timeout is True
