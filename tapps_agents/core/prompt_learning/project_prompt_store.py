"""Project-specific prompt store."""

from pathlib import Path
from typing import Any

from ..storage_manager import PromptStorage, StorageManager


class ProjectPromptStore:
    """Stores project-specific learned prompts."""

    def __init__(self, project_root: Path | None = None):
        self.storage_manager = StorageManager(project_root)
        self.prompt_storage = self.storage_manager.prompts

    def store_learned_prompt(
        self, prompt_type: str, prompt_data: dict[str, Any]
    ) -> Path:
        """Store learned prompt."""
        return self.prompt_storage.save_prompt(prompt_type, prompt_data)

    def get_latest_prompt(self, prompt_type: str) -> dict[str, Any] | None:
        """Get latest learned prompt."""
        return self.prompt_storage.get_latest_version(prompt_type)

