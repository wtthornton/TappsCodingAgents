"""
Storage manager for Tier 1 Enhancement infrastructure.

Provides file-based storage for feedback, learned prompts, and evaluation results.
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .storage_models import (
    CleanupPolicy,
    StorageMetadata,
    StoragePath,
    VersionInfo,
)

logger = logging.getLogger(__name__)


class FeedbackStorage:
    """Manages storage of feedback data in `.tapps-agents/feedback/`."""

    def __init__(self, storage_path: StoragePath):
        """
        Initialize feedback storage.
        
        Args:
            storage_path: Storage path configuration
        """
        self.storage_path = storage_path
        self.feedback_dir = storage_path.feedback_dir
        self.feedback_dir.mkdir(parents=True, exist_ok=True)

    def save_feedback(
        self, feedback_data: dict[str, Any], filename: str | None = None
    ) -> Path:
        """
        Save feedback data to file.
        
        Args:
            feedback_data: Feedback data dictionary
            filename: Optional filename (auto-generated if None)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"feedback_{timestamp}.json"

        file_path = self.feedback_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Add metadata
        feedback_data["_metadata"] = {
            "saved_at": datetime.now().isoformat(),
            "file": str(file_path),
        }

        # Atomic write
        temp_path = file_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(feedback_data, f, indent=2, ensure_ascii=False)
        temp_path.replace(file_path)

        logger.debug(f"Saved feedback to {file_path}")
        return file_path

    def load_feedback(self, filename: str) -> dict[str, Any]:
        """Load feedback data from file."""
        file_path = self.feedback_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Feedback file not found: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_feedback(self, agent_name: str | None = None) -> list[Path]:
        """List feedback files, optionally filtered by agent."""
        if not self.feedback_dir.exists():
            return []
        
        files = list(self.feedback_dir.glob("feedback_*.json"))
        if agent_name:
            # Filter by agent name in file content (simple approach)
            filtered = []
            for file_path in files:
                try:
                    data = self.load_feedback(file_path.name)
                    if data.get("agent_name") == agent_name:
                        filtered.append(file_path)
                except Exception:
                    continue
            return filtered
        return files

    def cleanup(self, policy: CleanupPolicy) -> int:
        """Clean up old feedback files based on policy."""
        if not policy.enabled:
            return 0
        
        files = self.list_feedback()
        if len(files) <= policy.max_items_per_type:
            return 0
        
        # Sort by modification time
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        
        cleaned = 0
        now = datetime.now()
        
        # Keep latest if retain_latest is enabled
        keep_count = policy.max_items_per_type if policy.retain_latest else 0
        
        for file_path in files[keep_count:]:
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            file_age = now - file_mtime
            age_days = file_age.days
            if policy.should_cleanup(age_days, len(files) - cleaned):
                try:
                    file_path.unlink()
                    cleaned += 1
                except Exception as e:
                    logger.warning(f"Failed to delete {file_path}: {e}")
        
        return cleaned


class PromptStorage:
    """Manages storage of learned prompts in `.tapps-agents/learned-prompts/`."""

    def __init__(self, storage_path: StoragePath):
        """
        Initialize prompt storage.
        
        Args:
            storage_path: Storage path configuration
        """
        self.storage_path = storage_path
        self.prompts_dir = storage_path.learned_prompts_dir
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        
        # Subdirectories for different prompt types
        self.eval_dir = self.prompts_dir / "eval"
        self.system_dir = self.prompts_dir / "system"
        self.instructions_dir = self.prompts_dir / "instructions"
        
        for subdir in [self.eval_dir, self.system_dir, self.instructions_dir]:
            subdir.mkdir(parents=True, exist_ok=True)

    def save_prompt(
        self,
        prompt_type: str,
        prompt_data: dict[str, Any],
        version: str | None = None,
    ) -> Path:
        """
        Save learned prompt.
        
        Args:
            prompt_type: Type of prompt (eval, system, instructions)
            prompt_data: Prompt data dictionary
            version: Optional version string (auto-generated if None)
            
        Returns:
            Path to saved file
        """
        # Determine subdirectory
        subdir_map = {
            "eval": self.eval_dir,
            "system": self.system_dir,
            "instructions": self.instructions_dir,
        }
        subdir = subdir_map.get(prompt_type, self.prompts_dir)
        
        if version is None:
            version = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename = f"{prompt_type}_{version}.json"
        file_path = subdir / filename
        
        # Add metadata
        prompt_data["_metadata"] = {
            "saved_at": datetime.now().isoformat(),
            "version": version,
            "prompt_type": prompt_type,
            "file": str(file_path),
        }
        
        # Atomic write
        temp_path = file_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(prompt_data, f, indent=2, ensure_ascii=False)
        temp_path.replace(file_path)
        
        logger.debug(f"Saved prompt to {file_path}")
        return file_path

    def load_prompt(self, prompt_type: str, version: str) -> dict[str, Any]:
        """Load prompt by type and version."""
        subdir_map = {
            "eval": self.eval_dir,
            "system": self.system_dir,
            "instructions": self.instructions_dir,
        }
        subdir = subdir_map.get(prompt_type, self.prompts_dir)
        
        filename = f"{prompt_type}_{version}.json"
        file_path = subdir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_versions(self, prompt_type: str) -> list[str]:
        """List available versions for a prompt type."""
        subdir_map = {
            "eval": self.eval_dir,
            "system": self.system_dir,
            "instructions": self.instructions_dir,
        }
        subdir = subdir_map.get(prompt_type, self.prompts_dir)
        
        if not subdir.exists():
            return []
        
        versions = []
        for file_path in subdir.glob(f"{prompt_type}_*.json"):
            # Extract version from filename
            version = file_path.stem.replace(f"{prompt_type}_", "")
            versions.append(version)
        
        return sorted(versions, reverse=True)

    def get_latest_version(self, prompt_type: str) -> dict[str, Any] | None:
        """Get the latest version of a prompt type."""
        versions = self.list_versions(prompt_type)
        if not versions:
            return None
        return self.load_prompt(prompt_type, versions[0])


class EvaluationStorage:
    """Manages storage of evaluation results in `.tapps-agents/evaluation/`."""

    def __init__(self, storage_path: StoragePath):
        """
        Initialize evaluation storage.
        
        Args:
            storage_path: Storage path configuration
        """
        self.storage_path = storage_path
        self.evaluation_dir = storage_path.evaluation_dir
        self.evaluation_dir.mkdir(parents=True, exist_ok=True)

    def save_evaluation(
        self, evaluation_data: dict[str, Any], identifier: str | None = None
    ) -> Path:
        """
        Save evaluation result.
        
        Args:
            evaluation_data: Evaluation result dictionary
            identifier: Optional identifier (auto-generated if None)
            
        Returns:
            Path to saved file
        """
        if identifier is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            identifier = f"eval_{timestamp}"
        
        filename = f"{identifier}.json"
        file_path = self.evaluation_dir / filename
        
        # Add metadata
        evaluation_data["_metadata"] = {
            "saved_at": datetime.now().isoformat(),
            "identifier": identifier,
            "file": str(file_path),
        }
        
        # Atomic write
        temp_path = file_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(evaluation_data, f, indent=2, ensure_ascii=False)
        temp_path.replace(file_path)
        
        logger.debug(f"Saved evaluation to {file_path}")
        return file_path

    def load_evaluation(self, identifier: str) -> dict[str, Any]:
        """Load evaluation result by identifier."""
        filename = f"{identifier}.json"
        file_path = self.evaluation_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"Evaluation file not found: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_evaluations(self, limit: int | None = None) -> list[Path]:
        """List evaluation files."""
        if not self.evaluation_dir.exists():
            return []
        
        files = sorted(
            self.evaluation_dir.glob("eval_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        
        if limit:
            return files[:limit]
        return files


class StorageManager:
    """Manages all storage types for Tier 1 enhancements."""

    def __init__(self, project_root: Path | None = None):
        """
        Initialize storage manager.
        
        Args:
            project_root: Project root directory (auto-detected if None)
        """
        if project_root is None:
            # Auto-detect project root by looking for .tapps-agents
            current = Path.cwd()
            for parent in [current] + list(current.parents):
                if (parent / ".tapps-agents").exists():
                    project_root = parent
                    break
            if project_root is None:
                project_root = current
        
        self.project_root = project_root
        self.storage_path = StoragePath.from_project_root(project_root)
        self.storage_path.ensure_directories()
        
        self.feedback = FeedbackStorage(self.storage_path)
        self.prompts = PromptStorage(self.storage_path)
        self.evaluation = EvaluationStorage(self.storage_path)

    def cleanup_all(self, policy: CleanupPolicy) -> dict[str, int]:
        """Clean up all storage types based on policy."""
        results = {
            "feedback": self.feedback.cleanup(policy),
            "prompts": 0,  # Prompt cleanup handled separately
            "evaluation": 0,  # Evaluation cleanup handled separately
        }
        return results

    def get_storage_metadata(self) -> dict[str, Any]:
        """Get metadata about storage usage."""
        def get_dir_size(path: Path) -> int:
            """Calculate directory size in bytes."""
            total = 0
            try:
                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        total += file_path.stat().st_size
            except Exception:
                pass
            return total
        
        def count_files(path: Path) -> int:
            """Count files in directory."""
            try:
                return len(list(path.rglob("*.json")))
            except Exception:
                return 0
        
        return {
            "feedback": {
                "size_bytes": get_dir_size(self.storage_path.feedback_dir),
                "file_count": count_files(self.storage_path.feedback_dir),
            },
            "learned_prompts": {
                "size_bytes": get_dir_size(self.storage_path.learned_prompts_dir),
                "file_count": count_files(self.storage_path.learned_prompts_dir),
            },
            "evaluation": {
                "size_bytes": get_dir_size(self.storage_path.evaluation_dir),
                "file_count": count_files(self.storage_path.evaluation_dir),
            },
        }

