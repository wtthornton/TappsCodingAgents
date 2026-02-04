"""
Advanced Workflow State Management

Provides enhanced state persistence with validation, migration, versioning, and recovery.
"""

from __future__ import annotations

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
    # Epic 12: Enhanced checkpoint metadata
    current_step: str | None = None
    completed_steps_count: int = 0
    progress_percentage: float = 0.0
    trigger_step_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["saved_at"] = self.saved_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StateMetadata:
        """Create from dictionary."""
        data = data.copy()
        data["saved_at"] = datetime.fromisoformat(data["saved_at"])
        return cls(**data)


class StateValidator:
    """Validates workflow state integrity."""

    @staticmethod
    def calculate_checksum(state_data: dict[str, Any]) -> str:
        """Calculate SHA256 checksum for state data."""
        def _make_json_serializable(obj: Any) -> Any:
            """Recursively convert objects to JSON-serializable format."""
            # Handle ProjectProfile objects
            if hasattr(obj, "to_dict") and hasattr(obj, "compliance_requirements"):
                try:
                    from ..core.project_profile import ProjectProfile
                    if isinstance(obj, ProjectProfile):
                        return obj.to_dict()
                except (ImportError, AttributeError):
                    pass
            
            # Handle ComplianceRequirement objects
            if hasattr(obj, "name") and hasattr(obj, "confidence") and hasattr(obj, "indicators"):
                try:
                    from ..core.project_profile import ComplianceRequirement
                    if isinstance(obj, ComplianceRequirement):
                        return asdict(obj)
                except (ImportError, AttributeError):
                    pass
            
            # Handle dictionaries recursively
            if isinstance(obj, dict):
                return {k: _make_json_serializable(v) for k, v in obj.items()}
            
            # Handle lists recursively
            if isinstance(obj, list):
                return [_make_json_serializable(item) for item in obj]
            
            return obj
        
        # Ensure variables are JSON-serializable
        variables = state_data.get("variables", {})
        serializable_variables = _make_json_serializable(variables)
        
        # Create stable representation (sorted keys, no metadata)
        stable_data = {
            "workflow_id": state_data.get("workflow_id"),
            "current_step": state_data.get("current_step"),
            "completed_steps": sorted(state_data.get("completed_steps", [])),
            "skipped_steps": sorted(state_data.get("skipped_steps", [])),
            "status": state_data.get("status"),
            "variables": serializable_variables,
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

        # Epic 12: Extract checkpoint metadata from state if available
        checkpoint_metadata = state.variables.get("_checkpoint_metadata", {})
        
        metadata = StateMetadata(
            version=CURRENT_STATE_VERSION,
            saved_at=datetime.now(),
            checksum=checksum,
            workflow_id=state.workflow_id,
            state_file=state_file,
            workflow_path=str(workflow_path) if workflow_path else None,
            compression=self.compression,
            current_step=checkpoint_metadata.get("current_step") or state.current_step,
            completed_steps_count=checkpoint_metadata.get("completed_steps", len(state.completed_steps)),
            progress_percentage=checkpoint_metadata.get("progress_percentage", 0.0),
            trigger_step_id=checkpoint_metadata.get("trigger_step_id"),
        )

        # Save state file
        state_path = self.state_dir / state_file
        self._write_state_file(state_path, state_data, self.compression)

        # Save metadata
        metadata_path = self.state_dir / f"{state.workflow_id}.meta.json"
        from .file_utils import atomic_write_json
        atomic_write_json(metadata_path, metadata.to_dict(), indent=2)

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
        from .file_utils import atomic_write_json
        atomic_write_json(last_path, last_data, indent=2)

        # Session handoff when workflow ends (plan 2.1)
        if state.status in ("completed", "failed", "paused"):
            try:
                from .session_handoff import SessionHandoff, write_handoff

                project_root = self.state_dir.parent.parent
                done = list(state.completed_steps or [])
                artifact_paths = [
                    a.path for a in (state.artifacts or {}).values()
                    if getattr(a, "path", None)
                ]
                next_steps = [
                    "Resume with: tapps-agents workflow resume",
                    "Run `bd ready` to see unblocked tasks (if using Beads).",
                ]
                handoff = SessionHandoff(
                    workflow_id=state.workflow_id,
                    session_ended_at=datetime.now(timezone.utc).isoformat(),
                    summary=f"Workflow {state.status}. Completed steps: {len(done)}.",
                    done=done,
                    decisions=[],
                    next_steps=next_steps,
                    artifact_paths=artifact_paths,
                    bd_ready_hint="Run `bd ready`" if done else None,
                )
                write_handoff(project_root, handoff)
            except Exception as e:  # pylint: disable=broad-except
                logger.debug("Could not write session handoff: %s", e)

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
                recovered_workflow_id = (
                    workflow_id
                    or state_data.get("workflow_id")
                    or state_data.get("id")
                    or ""
                )
                if (
                    not isinstance(recovered_workflow_id, str)
                    or not recovered_workflow_id
                ):
                    raise ValueError(
                        "Cannot recover: missing workflow_id in state data"
                    )
                return self._recover_from_history(state_path, recovered_workflow_id)

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
                # Update metadata version after migration
                metadata.version = CURRENT_STATE_VERSION
        else:
            # Legacy state without metadata
            metadata = StateMetadata(
                version=CURRENT_STATE_VERSION,  # Use current version for legacy states
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

    def cleanup_old_states(
        self,
        retention_days: int = 30,
        max_states_per_workflow: int = 10,
        remove_completed: bool = True,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        Clean up old workflow states.

        Epic 12: State cleanup functionality

        Args:
            retention_days: Keep states newer than this many days
            max_states_per_workflow: Maximum states to keep per workflow
            remove_completed: Whether to remove states for completed workflows
            dry_run: If True, only report what would be removed (no files deleted)

        Returns:
            Dictionary with cleanup statistics; if dry_run, includes would_remove list
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=retention_days)
        removed_count = 0
        removed_size = 0
        workflows_cleaned = set()
        would_remove: list[dict[str, Any]] = []

        # Group states by workflow_id
        workflow_states: dict[str, list[dict[str, Any]]] = {}
        for state_info in self.list_states():
            workflow_id = state_info.get("workflow_id", "unknown")
            if workflow_id not in workflow_states:
                workflow_states[workflow_id] = []
            workflow_states[workflow_id].append(state_info)

        # Clean up each workflow
        for workflow_id, states in workflow_states.items():
            # Sort by saved_at (newest first)
            states_sorted = sorted(
                states,
                key=lambda x: datetime.fromisoformat(x.get("saved_at", "1970-01-01"))
                if isinstance(x.get("saved_at"), str)
                else datetime.fromtimestamp(0),
                reverse=True,
            )

            # Check if workflow is completed
            is_completed = False
            if remove_completed:
                # Try to load latest state to check status
                try:
                    state, _ = self.load_state(workflow_id=workflow_id, validate=False)
                    is_completed = state.status in ("completed", "failed", "cancelled")
                except Exception:
                    pass

            # Remove old states
            for state_info in states_sorted:
                state_file = state_info.get("state_file", "")
                if not state_file:
                    continue

                state_path = self.state_dir / state_file
                if not state_path.exists():
                    continue

                # Check retention period
                saved_at_str = state_info.get("saved_at", "")
                try:
                    if isinstance(saved_at_str, str):
                        saved_at = datetime.fromisoformat(saved_at_str)
                    else:
                        saved_at = datetime.fromtimestamp(saved_at_str)
                except (ValueError, TypeError):
                    saved_at = datetime.fromtimestamp(0)

                should_remove = False
                reason = ""

                # Remove if older than retention period
                if saved_at < cutoff_date:
                    should_remove = True
                    reason = "retention_period"
                # Remove if completed workflow and remove_completed is True
                elif is_completed and remove_completed:
                    # Keep only the most recent completed state
                    if states_sorted.index(state_info) > 0:
                        should_remove = True
                        reason = "completed_workflow"
                # Remove if exceeds max_states_per_workflow
                elif len([s for s in states_sorted if not should_remove]) > max_states_per_workflow:
                    if states_sorted.index(state_info) >= max_states_per_workflow:
                        should_remove = True
                        reason = "max_states_limit"

                if should_remove:
                    try:
                        # Get file size before removal
                        file_size = state_path.stat().st_size
                        if dry_run:
                            would_remove.append({
                                "state_file": state_file,
                                "workflow_id": workflow_id,
                                "size_bytes": file_size,
                                "reason": reason,
                            })
                            removed_size += file_size
                            removed_count += 1
                            workflows_cleaned.add(workflow_id)
                        else:
                            state_path.unlink()
                            removed_size += file_size
                            removed_count += 1
                            workflows_cleaned.add(workflow_id)
                            # Also remove from history if exists
                            history_path = self.history_dir / state_file
                            if history_path.exists():
                                history_path.unlink()
                            logger.debug(
                                f"Removed state {state_file} (reason: {reason})"
                            )
                    except Exception as e:
                        logger.warning(f"Failed to remove state {state_file}: {e}")

        result = {
            "removed_count": removed_count,
            "removed_size_mb": round(removed_size / (1024 * 1024), 2),
            "workflows_cleaned": len(workflows_cleaned),
        }
        if dry_run:
            result["dry_run"] = True
            result["would_remove"] = would_remove

        logger.info(
            f"State cleanup completed: removed {removed_count} states "
            f"({result['removed_size_mb']} MB) from {len(workflows_cleaned)} workflows"
        )

        return result

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
        """Write state file with optional compression using atomic write."""
        from .file_utils import atomic_write_json
        
        atomic_write_json(path, data, compress=compress, indent=2)

    def _read_state_file(self, path: Path) -> dict[str, Any]:
        """Read state file with optional decompression and safe loading."""
        from .file_utils import safe_load_json
        
        # Use safe loading with validation
        result = safe_load_json(
            path,
            retries=3,
            backoff=0.5,
            min_age_seconds=1.0,  # Shorter wait for explicit loads
            min_size=50,  # Smaller minimum for compressed files
        )
        
        if result is None:
            raise ValueError(f"Failed to load state file: {path}")
        
        return result

    def _state_to_dict(self, state: WorkflowState) -> dict[str, Any]:
        """Convert WorkflowState to dictionary."""

        def _artifact_to_dict(name: str, artifact: Any) -> dict[str, Any]:
            created_at = getattr(artifact, "created_at", None)
            return {
                "name": getattr(artifact, "name", name) or name,
                "path": str(getattr(artifact, "path", "")),
                "status": getattr(artifact, "status", "pending"),
                "created_by": getattr(artifact, "created_by", None),
                "created_at": created_at.isoformat() if created_at else None,
                "metadata": getattr(artifact, "metadata", {}) or {},
            }

        def _make_json_serializable(obj: Any) -> Any:
            """Recursively convert objects to JSON-serializable format."""
            # Handle ProjectProfile objects
            if hasattr(obj, "to_dict") and hasattr(obj, "compliance_requirements"):
                # This is likely a ProjectProfile object
                try:
                    from ..core.project_profile import ProjectProfile
                    if isinstance(obj, ProjectProfile):
                        return obj.to_dict()
                except (ImportError, AttributeError):
                    pass
            
            # Handle ComplianceRequirement objects
            if hasattr(obj, "name") and hasattr(obj, "confidence") and hasattr(obj, "indicators"):
                try:
                    from ..core.project_profile import ComplianceRequirement
                    if isinstance(obj, ComplianceRequirement):
                        return asdict(obj)
                except (ImportError, AttributeError):
                    pass
            
            # Handle dictionaries recursively
            if isinstance(obj, dict):
                return {k: _make_json_serializable(v) for k, v in obj.items()}
            
            # Handle lists recursively
            if isinstance(obj, list):
                return [_make_json_serializable(item) for item in obj]
            
            # Handle other non-serializable types
            try:
                json.dumps(obj)
                return obj
            except (TypeError, ValueError):
                # For non-serializable types, convert to string as fallback
                return str(obj)

        # Convert variables to JSON-serializable format
        variables = state.variables or {}
        serializable_variables = _make_json_serializable(variables)

        return {
            "workflow_id": state.workflow_id,
            "started_at": state.started_at.isoformat(),
            "current_step": state.current_step,
            "completed_steps": state.completed_steps,
            "skipped_steps": state.skipped_steps,
            "artifacts": {
                k: _artifact_to_dict(k, v) for k, v in (state.artifacts or {}).items()
            },
            "variables": serializable_variables,
            "status": state.status,
            "error": state.error,
        }

    def _state_from_dict(self, data: dict[str, Any]) -> WorkflowState:
        """Convert dictionary to WorkflowState."""
        from .models import Artifact

        artifacts = {}
        for k, v in data.get("artifacts", {}).items():
            if not isinstance(v, dict):
                continue

            # New format (preferred)
            if "name" in v or "created_by" in v or "metadata" in v:
                created_at = v.get("created_at")
                artifacts[k] = Artifact(
                    name=v.get("name", k) or k,
                    path=str(v.get("path", "")),
                    status=v.get("status", "pending"),
                    created_by=v.get("created_by"),
                    created_at=(
                        datetime.fromisoformat(created_at) if created_at else None
                    ),
                    metadata=v.get("metadata", {}) or {},
                )
                continue

            # Legacy format (v1): {"path": "...", "status": "...", "step_id": "..."}
            step_id = v.get("step_id")
            artifacts[k] = Artifact(
                name=k,
                path=str(v.get("path", "")),
                status=v.get("status", "pending"),
                created_by=step_id if isinstance(step_id, str) else None,
                created_at=None,
                metadata={},
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
