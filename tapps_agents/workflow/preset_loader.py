"""
Preset Workflow Loader

Loads and maps preset workflows with short aliases and voice-friendly names.
"""

from pathlib import Path
from typing import Any

import yaml

from .models import Workflow
from .parser import WorkflowParser

# Preset name mappings
PRESET_ALIASES: dict[str, str] = {
    # Short commands
    "full": "full-sdlc",
    "rapid": "rapid-dev",
    "fix": "maintenance",
    "quality": "quality",
    "hotfix": "quick-fix",
    # Voice-friendly aliases
    "enterprise": "full-sdlc",
    "feature": "rapid-dev",
    "refactor": "maintenance",
    "improve": "quality",
    "urgent": "quick-fix",
    # Full names
    "full-sdlc": "full-sdlc",
    "rapid-dev": "rapid-dev",
    "maintenance": "maintenance",
    "quick-fix": "quick-fix",
}


class PresetLoader:
    """Loads preset workflows from YAML files."""

    def __init__(self, presets_dir: Path | None = None):
        """
        Initialize preset loader.

        Args:
            presets_dir: Directory containing preset YAML files.
                        Defaults to workflows/presets/ relative to project root.
        """
        if presets_dir is None:
            # Try to find presets directory relative to this file
            current_file = Path(__file__).parent
            project_root = current_file.parent.parent.parent
            presets_dir = project_root / "workflows" / "presets"

            # Fallback: try current working directory
            if not presets_dir.exists():
                presets_dir = Path.cwd() / "workflows" / "presets"

        self.presets_dir = Path(presets_dir)
        self.parser = WorkflowParser()

    def get_preset_name(self, alias: str) -> str | None:
        """
        Get preset name from alias.

        Args:
            alias: Short alias or voice-friendly name

        Returns:
            Preset name or None if not found
        """
        return PRESET_ALIASES.get(alias.lower())

    def list_presets(self) -> dict[str, dict[str, Any]]:
        """
        List all available presets with their aliases.

        Returns:
            Dictionary mapping preset names to their metadata
        """
        presets: dict[str, dict[str, Any]] = {}

        # First, collect all unique preset names
        unique_presets = set(PRESET_ALIASES.values())

        # Load metadata for each preset
        for preset_name in unique_presets:
            preset_file = self.presets_dir / f"{preset_name}.yaml"
            if preset_file.exists():
                try:
                    with open(preset_file, encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                        workflow_data = data.get("workflow", {})
                        presets[preset_name] = {
                            "name": workflow_data.get("name", preset_name),
                            "description": workflow_data.get("description", ""),
                            "aliases": [],
                        }
                except (KeyError, ValueError, TypeError, yaml.YAMLError, OSError) as e:
                    # Skip invalid preset entries (file errors, YAML errors, missing keys)
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.warning(f"Invalid preset '{preset_name}': {e}")
                    presets[preset_name] = {
                        "name": preset_name,
                        "description": "",
                        "aliases": [],
                    }

        # Add aliases to each preset
        for alias, preset_name in PRESET_ALIASES.items():
            if preset_name in presets:
                if alias not in presets[preset_name]["aliases"]:
                    presets[preset_name]["aliases"].append(alias)

        return presets

    def load_preset(self, alias: str) -> Workflow | None:
        """
        Load a preset workflow by alias.

        Args:
            alias: Short alias, voice-friendly name, or preset name

        Returns:
            Workflow object or None if not found
        """
        preset_name = self.get_preset_name(alias)
        if not preset_name:
            # Try direct name match
            preset_name = alias

        preset_file = self.presets_dir / f"{preset_name}.yaml"

        if not preset_file.exists():
            return None

        try:
            return self.parser.parse_file(preset_file)
        except Exception as e:
            raise ValueError(f"Failed to load preset '{preset_name}': {e}") from e

    def find_preset_by_intent(self, intent: str) -> str | None:
        """
        Find preset by natural language intent (for voice commands).

        Args:
            intent: Natural language description (e.g., "run rapid development")

        Returns:
            Preset name or None if not found
        """
        intent_lower = intent.lower()

        # Keywords for each preset
        keywords = {
            "full-sdlc": ["full", "enterprise", "complete", "sdlc", "lifecycle", "all"],
            "rapid-dev": ["rapid", "quick", "fast", "feature", "sprint", "dev"],
            "maintenance": ["maintenance", "fix", "refactor", "improve", "bug", "debt"],
            "quality": ["quality", "improve", "review", "refactor", "clean"],
            "quick-fix": [
                "hotfix",
                "urgent",
                "quick fix",
                "emergency",
                "patch",
                "critical",
            ],
        }

        # Score each preset based on keyword matches
        scores = {}
        for preset_name, preset_keywords in keywords.items():
            score = sum(1 for keyword in preset_keywords if keyword in intent_lower)
            if score > 0:
                scores[preset_name] = score

        if scores:
            # Return preset with highest score
            return max(scores.items(), key=lambda x: x[1])[0]

        return None
