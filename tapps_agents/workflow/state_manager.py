"""
Advanced Workflow State Management

Provides enhanced state persistence with validation, migration, versioning, and recovery.
"""

import gzip
import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import WorkflowState

logger = logging.getLogger(__name__)

# State format version for migration
CURRENT_STATE_VERSION = "2.0"


@dataclass
class StateMetadata:
    """Metadata for persisted workflow state."""

    version: str
    saved_at: datetime
    checksum: str
    workflow_id: str
    state_file: str
    workflow_path: str | None = None
    compression: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["saved_at"] = self.saved_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StateMetadata":
        """Create from dictionary."""
        data = data.copy()
        data["saved_at"] = datetime.fromisoformat(data["saved_at"])
        return cls(**data)


class StateValidator:
    """Validates workflow state integrity."""

    @staticmethod
    def calculate_checksum(state_data: dict[str, Any]) -> str:
        """Calculate SHA256 checksum for state data."""
        # Create stable representation (sorted keys, no metadata)
        stable_data = {
            "workflow_id": state_data.get("workflow_id"),
            "current_step": state_data.get("current_step"),
            "completed_steps": sorted(state_data.get("completed_steps", [])),
            "skipped_steps": sorted(state_data.get("skipped_steps", [])),
            "status": state_data.get("status"),
            "variables": json.dumps(state_data.get("variables", {}), sort_keys=True),
        }
        stable_str = json.dumps(stable_data, sort_keys=True)
        return hashlib.sha256(stable_str.encode()).hexdigest()

    @staticmethod
    def validate_state(
        state_data: dict[str, Any], expected_checksum: str | None = None
    ) -> tuple[bool, str | None]:
        """
        Validate state integrity.

        Returns:
            (is_valid, error_message)
        """
        # Check required fields
        required_fields = ["workflow_id", "started_at", "status"]
        for field in required_fields:
            if field not in state_data:
                return False, f"Missing required field: {field}"

        # Validate status
        valid_statuses = ["running", "paused", "completed", "failed"]
        if state_data.get("status") not in valid_statuses:
            return False, f"Invalid status: {state_data.get('status')}"

        # Validate checksum if provided
        if expected_checksum:
            calculated = StateValidator.calculate_checksum(state_data)
            if calculated != expected_checksum:
                return (
                    False,
                    f"Checksum mismatch: expected {expected_checksum[:8]}..., got {calculated[:8]}...",
                )

        return True, None


class StateMigrator:
    """Handles migration of state between versions."""

    @staticmethod
    def migrate_state(
        state_data: dict[str, Any], from_version: str, to_version: str
    ) -> dict[str, Any]:
        """
        Migrate state from one version to another.

        Args:
            state_data: State data to migrate
            from_version: Source version
            to_version: Target version

        Returns:
            Migrated state data
        """
        if from_version == to_version:
            return state_data

        # Migration path: 1.0 -> 2.0
        if from_version == "1.0" and to_version == "2.0":
            # Add default fields if missing
            if "skipped_steps" not in state_data:
                state_data["skipped_steps"] = []
            if "artifacts" not in state_data:
                state_data["artifacts"] = {}
            if "variables" not in state_data:
                state_data["variables"] = {}

            # Ensure status field exists
            if "status" not in state_data:
                state_data["status"] = "running"

        return state_data


class AdvancedStateManager:
    """Advanced workflow state manager with validation, migration, and recovery."""

    def __init__(self, state_dir: Path, compression: bool = False):
        """
        Initialize advanced state manager.

        Args:
            state_dir: Directory for state storage
            compression: Enable compression for state files
        """
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.compression = compression
        self.history_dir = self.state_dir / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def save_state(
        self, state: WorkflowState, workflow_path: Path | None = None
    ) -> Path:
        """
        Save workflow state with validation and metadata.

        Args:
            state: Workflow state to save
            workflow_path: Optional path to workflow YAML

        Returns:
            Path to saved state file
        """
        # Convert state to dict
        state_data = self._state_to_dict(state)

        # Calculate checksum
        checksum = StateValidator.calculate_checksum(state_data)
        state_data["_checksum"] = checksum

        # Create metadata
        state_file = (
            f"{state.workflow_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        )
        if self.compression:
            state_file += ".gz"

        metadata = StateMetadata(
            version=CURRENT_STATE_VERSION,
            saved_at=datetime.now(),
            checksum=checksum,
            workflow_id=state.workflow_id,
            state_file=state_file,
            workflow_path=str(workflow_path) if workflow_path else None,
            compression=self.compression,
        )

        # Save state file
        state_path = self.state_dir / state_file
        self._write_state_file(state_path, state_data, self.compression)

        # Save metadata
        metadata_path = self.state_dir / f"{state.workflow_id}.meta.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata.to_dict(), f, indent=2)

        # Save to history
        history_path = self.history_dir / state_file
        self._write_state_file(history_path, state_data, self.compression)

        # Update last pointer
        last_data = {
            "workflow_id": state.workflow_id,
            "state_file": str(state_path),
            "metadata_file": str(metadata_path),
            "saved_at": datetime.now().isoformat(),
            "version": CURRENT_STATE_VERSION,
            "workflow_path": str(workflow_path) if workflow_path else None,
        }
        last_path = self.state_dir / "last.json"
        with open(last_path, "w", encoding="utf-8") as f:
            json.dump(last_data, f, indent=2)

        logger.info(f"Saved workflow state: {state.workflow_id} to {state_path}")
        return state_path

    def load_state(
        self,
        workflow_id: str | None = None,
        state_file: Path | None = None,
        validate: bool = True,
    ) -> tuple[WorkflowState, StateMetadata]:
        """
        Load workflow state with validation and migration.

        Args:
            workflow_id: Workflow ID to load (uses last if not specified)
            state_file: Specific state file to load
            validate: Whether to validate state integrity

        Returns:
            (WorkflowState, StateMetadata)
        """
        # Determine which state file to load
        if state_file:
            state_path = Path(state_file)
        elif workflow_id:
            # Find latest state for workflow
            metadata_path = self.state_dir / f"{workflow_id}.meta.json"
            if metadata_path.exists():
                with open(metadata_path, encoding="utf-8") as f:
                    metadata_data = json.load(f)
                state_path = self.state_dir / metadata_data["state_file"]
            else:
                raise FileNotFoundError(f"No state found for workflow: {workflow_id}")
        else:
            # Load last state
            last_path = self.state_dir / "last.json"
            if not last_path.exists():
                raise FileNotFoundError("No persisted workflow state found")

            with open(last_path, encoding="utf-8") as f:
                last_data = json.load(f)

            state_path = Path(last_data["state_file"])
            if not state_path.is_absolute():
                state_path = self.state_dir / state_path

        # Load state data
        state_data = self._read_state_file(state_path)

        # Extract checksum if present
        expected_checksum = state_data.pop("_checksum", None)

        # Validate if requested
        if validate:
            is_valid, error = StateValidator.validate_state(
                state_data, expected_checksum
            )
            if not is_valid:
                logger.warning(f"State validation failed: {error}")
                # Try to recover from history
                return self._recover_from_history(
                    state_path, workflow_id or state_data.get("workflow_id")
                )

        # Check version and migrate if needed
        metadata_path = self.state_dir / f"{state_data['workflow_id']}.meta.json"
        if metadata_path.exists():
            with open(metadata_path, encoding="utf-8") as f:
                metadata_data = json.load(f)
            metadata = StateMetadata.from_dict(metadata_data)

            if metadata.version != CURRENT_STATE_VERSION:
                logger.info(
                    f"Migrating state from {metadata.version} to {CURRENT_STATE_VERSION}"
                )
                state_data = StateMigrator.migrate_state(
                    state_data, metadata.version, CURRENT_STATE_VERSION
                )
        else:
            # Legacy state without metadata
            metadata = StateMetadata(
                version="1.0",
                saved_at=datetime.fromisoformat(
                    state_data.get("started_at", datetime.now().isoformat())
                ),
                checksum=expected_checksum or "",
                workflow_id=state_data["workflow_id"],
                state_file=str(state_path.name),
                compression=self.compression,
            )

        # Convert to WorkflowState
        state = self._state_from_dict(state_data)

        return state, metadata

    def list_states(self, workflow_id: str | None = None) -> list[dict[str, Any]]:
        """
        List available workflow states.

        Args:
            workflow_id: Optional workflow ID to filter by

        Returns:
            List of state metadata dictionaries
        """
        states = []

        if workflow_id:
            # List history for specific workflow
            pattern = f"{workflow_id}-*.json*"
            for state_file in self.history_dir.glob(pattern):
                try:
                    state_data = self._read_state_file(state_file)
                    states.append(
                        {
                            "workflow_id": state_data.get("workflow_id"),
                            "state_file": str(state_file),
                            "status": state_data.get("status"),
                            "current_step": state_data.get("current_step"),
                            "saved_at": state_file.stat().st_mtime,
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to read state file {state_file}: {e}")
        else:
            # List all workflows
            for metadata_file in self.state_dir.glob("*.meta.json"):
                try:
                    with open(metadata_file, encoding="utf-8") as f:
                        metadata_data = json.load(f)
                    states.append(metadata_data)
                except Exception as e:
                    logger.warning(f"Failed to read metadata {metadata_file}: {e}")

        return sorted(states, key=lambda x: x.get("saved_at", 0), reverse=True)

    def _recover_from_history(
        self, corrupted_path: Path, workflow_id: str
    ) -> tuple[WorkflowState, StateMetadata]:
        """Attempt to recover state from history."""
        logger.info(f"Attempting recovery from history for {workflow_id}")

        # Find most recent valid state in history
        pattern = f"{workflow_id}-*.json*"
        history_files = sorted(
            self.history_dir.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        for history_file in history_files:
            try:
                state_data = self._read_state_file(history_file)
                expected_checksum = state_data.pop("_checksum", None)
                is_valid, error = StateValidator.validate_state(
                    state_data, expected_checksum
                )
                if is_valid:
                    logger.info(f"Recovered valid state from {history_file}")
                    # Re-save as current state
                    return self.load_state(state_file=history_file, validate=False)
            except Exception as e:
                logger.warning(f"Failed to recover from {history_file}: {e}")
                continue

        raise ValueError(f"Could not recover state for workflow {workflow_id}")

    def _write_state_file(self, path: Path, data: dict[str, Any], compress: bool):
        """Write state file with optional compression."""
        if compress:
            with gzip.open(path, "wt", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        else:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    def _read_state_file(self, path: Path) -> dict[str, Any]:
        """Read state file with optional decompression."""
        if path.suffix == ".gz" or path.name.endswith(".gz"):
            with gzip.open(path, "rt", encoding="utf-8") as f:
                return json.load(f)
        else:
            with open(path, encoding="utf-8") as f:
                return json.load(f)

    def _state_to_dict(self, state: WorkflowState) -> dict[str, Any]:
        """Convert WorkflowState to dictionary."""
        return {
            "workflow_id": state.workflow_id,
            "started_at": state.started_at.isoformat(),
            "current_step": state.current_step,
            "completed_steps": state.completed_steps,
            "skipped_steps": state.skipped_steps,
            "artifacts": {
                k: {
                    "path": str(v.path),
                    "status": v.status,
                    "step_id": v.step_id,
                }
                for k, v in (state.artifacts or {}).items()
            },
            "variables": state.variables or {},
            "status": state.status,
            "error": state.error,
        }

    def _state_from_dict(self, data: dict[str, Any]) -> WorkflowState:
        """Convert dictionary to WorkflowState."""
        from .models import Artifact

        artifacts = {}
        for k, v in data.get("artifacts", {}).items():
            artifacts[k] = Artifact(
                path=Path(v["path"]),
                status=v["status"],
                step_id=v.get("step_id"),
            )

        return WorkflowState(
            workflow_id=data["workflow_id"],
            started_at=datetime.fromisoformat(data["started_at"]),
            current_step=data.get("current_step"),
            completed_steps=data.get("completed_steps", []),
            skipped_steps=data.get("skipped_steps", []),
            artifacts=artifacts,
            variables=data.get("variables", {}),
            status=data.get("status", "running"),
            error=data.get("error"),
        )
