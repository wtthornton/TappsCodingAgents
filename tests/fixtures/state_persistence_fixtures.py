"""
Test fixtures for state persistence and checkpointing.

Epic 12: State Persistence and Resume - Story 12.7
Provides reusable fixtures for testing state persistence, checkpoints, and recovery.
"""

import gzip
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from tapps_agents.workflow.models import Artifact, WorkflowState


@pytest.fixture
def temp_state_dir():
    """Create a temporary directory for state storage."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    import shutil
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_workflow_state():
    """Create a sample workflow state for testing."""
    return WorkflowState(
        workflow_id="test-workflow-123",
        started_at=datetime.now(),
        current_step="step-2",
        completed_steps=["step-0", "step-1"],
        skipped_steps=[],
        artifacts={
            "artifact-1": Artifact(
                path="output/file1.txt",
                type="file",
                created_at=datetime.now(),
            )
        },
        variables={"key1": "value1", "key2": 42},
        status="running",
    )


@pytest.fixture
def completed_workflow_state():
    """Create a completed workflow state."""
    return WorkflowState(
        workflow_id="completed-workflow",
        started_at=datetime.now() - timedelta(hours=1),
        current_step=None,
        completed_steps=["step-0", "step-1", "step-2", "step-3"],
        skipped_steps=[],
        artifacts={},
        variables={},
        status="completed",
    )


@pytest.fixture
def failed_workflow_state():
    """Create a failed workflow state."""
    return WorkflowState(
        workflow_id="failed-workflow",
        started_at=datetime.now() - timedelta(minutes=30),
        current_step="step-2",
        completed_steps=["step-0", "step-1"],
        skipped_steps=[],
        artifacts={},
        variables={},
        status="failed",
    )


def create_valid_state_file(
    state_dir: Path,
    workflow_id: str = "test-workflow",
    version: str = "2.0",
    compression: bool = False,
) -> Path:
    """
    Create a valid state file for testing.

    Args:
        state_dir: Directory to create state file in
        workflow_id: Workflow ID
        version: State version
        compression: Whether to compress the file

    Returns:
        Path to created state file
    """
    state_data = {
        "version": version,
        "workflow_id": workflow_id,
        "started_at": datetime.now().isoformat(),
        "current_step": "step-1",
        "completed_steps": ["step-0"],
        "skipped_steps": [],
        "artifacts": {},
        "variables": {},
        "status": "running",
        "metadata": {
            "saved_at": datetime.now().isoformat(),
            "checksum": "test_checksum",
        },
    }

    state_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{workflow_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    if compression:
        filename += ".gz"

    state_file = state_dir / filename

    if compression:
        with gzip.open(state_file, "wt", encoding="utf-8") as f:
            json.dump(state_data, f)
    else:
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state_data, f)

    return state_file


def create_corrupted_state_file(
    state_dir: Path,
    workflow_id: str = "corrupted-workflow",
    corruption_type: str = "invalid_json",
) -> Path:
    """
    Create a corrupted state file for testing recovery.

    Args:
        state_dir: Directory to create state file in
        workflow_id: Workflow ID
        corruption_type: Type of corruption ("invalid_json", "missing_fields", "invalid_checksum")

    Returns:
        Path to created corrupted state file
    """
    state_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{workflow_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    state_file = state_dir / filename

    if corruption_type == "invalid_json":
        # Invalid JSON syntax
        state_file.write_text("{ invalid json }")
    elif corruption_type == "missing_fields":
        # Missing required fields
        state_file.write_text('{"workflow_id": "test"}')
    elif corruption_type == "invalid_checksum":
        # Valid JSON but invalid checksum
        state_data = {
            "version": "2.0",
            "workflow_id": workflow_id,
            "started_at": datetime.now().isoformat(),
            "status": "running",
            "metadata": {
                "saved_at": datetime.now().isoformat(),
                "checksum": "invalid_checksum_value",
            },
        }
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state_data, f)
    else:
        # Truncated file
        state_file.write_text('{"workflow_id": "test", "version": "2.0", "incomplete":')

    return state_file


def create_old_version_state_file(
    state_dir: Path,
    workflow_id: str = "old-version-workflow",
    version: str = "1.0",
) -> Path:
    """
    Create a state file with old version format for migration testing.

    Args:
        state_dir: Directory to create state file in
        workflow_id: Workflow ID
        version: State version (should be "1.0" for old format)

    Returns:
        Path to created state file
    """
    state_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{workflow_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    state_file = state_dir / filename

    # Old version 1.0 format (missing skipped_steps, artifacts, variables)
    state_data = {
        "version": version,
        "workflow_id": workflow_id,
        "started_at": datetime.now().isoformat(),
        "current_step": "step-1",
        "completed_steps": ["step-0"],
        "status": "running",
        "metadata": {
            "saved_at": datetime.now().isoformat(),
            "checksum": "old_checksum",
        },
    }

    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state_data, f)

    return state_file


@pytest.fixture
def valid_state_file(temp_state_dir):
    """Fixture for a valid state file."""
    return create_valid_state_file(temp_state_dir)


@pytest.fixture
def corrupted_state_file(temp_state_dir):
    """Fixture for a corrupted state file."""
    return create_corrupted_state_file(temp_state_dir, corruption_type="invalid_json")


@pytest.fixture
def old_version_state_file(temp_state_dir):
    """Fixture for an old version state file."""
    return create_old_version_state_file(temp_state_dir, version="1.0")


@pytest.fixture
def multiple_state_files(temp_state_dir):
    """Create multiple state files for cleanup testing."""
    files = []
    for i in range(5):
        workflow_id = f"workflow-{i}"
        state_file = create_valid_state_file(temp_state_dir, workflow_id=workflow_id)
        files.append(state_file)
        # Stagger modification times
        import time
        time.sleep(0.01)
    return files


@pytest.fixture
def large_state_file(temp_state_dir):
    """Create a large state file for size limit testing."""
    state_dir = temp_state_dir
    state_dir.mkdir(parents=True, exist_ok=True)
    filename = f"large-workflow-{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    state_file = state_dir / filename

    # Create a large state with many artifacts and variables
    large_data = {
        "version": "2.0",
        "workflow_id": "large-workflow",
        "started_at": datetime.now().isoformat(),
        "current_step": "step-100",
        "completed_steps": [f"step-{i}" for i in range(100)],
        "skipped_steps": [],
        "artifacts": {f"artifact-{i}": {"path": f"file{i}.txt"} for i in range(100)},
        "variables": {f"key{i}": f"value{i}" * 100 for i in range(100)},
        "status": "running",
        "metadata": {
            "saved_at": datetime.now().isoformat(),
            "checksum": "large_checksum",
        },
    }

    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(large_data, f)

    return state_file


class StateFileFactory:
    """Factory for creating various state file scenarios."""

    def __init__(self, state_dir: Path):
        self.state_dir = state_dir

    def create_valid(self, workflow_id: str = "test-workflow") -> Path:
        """Create a valid state file."""
        return create_valid_state_file(self.state_dir, workflow_id=workflow_id)

    def create_corrupted(self, corruption_type: str = "invalid_json") -> Path:
        """Create a corrupted state file."""
        return create_corrupted_state_file(
            self.state_dir, corruption_type=corruption_type
        )

    def create_old_version(self, version: str = "1.0") -> Path:
        """Create an old version state file."""
        return create_old_version_state_file(self.state_dir, version=version)

    def create_compressed(self, workflow_id: str = "compressed-workflow") -> Path:
        """Create a compressed state file."""
        return create_valid_state_file(
            self.state_dir, workflow_id=workflow_id, compression=True
        )


@pytest.fixture
def state_file_factory(temp_state_dir):
    """Fixture for StateFileFactory."""
    return StateFileFactory(temp_state_dir)

