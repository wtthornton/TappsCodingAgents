"""
Preset Workflow Loader

Loads and maps preset workflows with short aliases and voice-friendly names.
"""

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

from .models import Workflow
from .parser import WorkflowParser

# Try to import resource helper for packaged presets
try:
    from ..core.init_project import _resource_at
except ImportError:
    _resource_at = None

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
    # Simple Mode workflows
    "new-feature": "simple-new-feature",
    "simple-new-feature": "simple-new-feature",
    "simple-fix-issues": "simple-fix-issues",
    "simple-improve-quality": "simple-improve-quality",
    "simple-full": "simple-full",
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
            presets_dir = self._find_presets_dir()

        self.presets_dir = Path(presets_dir)
        self.parser = WorkflowParser()

    def _find_presets_dir(self) -> Path:
        """
        Find presets directory by checking multiple locations in order:
        1. Framework source location (for development)
        2. Packaged resources (for installed packages)
        3. Current working directory (for project-specific presets)
        
        Returns:
            Path to presets directory
        """
        # 1. Try framework source location (relative to this file)
        # From tapps_agents/workflow/preset_loader.py:
        #   workflow/ -> tapps_agents/ -> project_root/
        current_file = Path(__file__).parent  # tapps_agents/workflow/
        framework_root = current_file.parent.parent  # project_root/
        framework_presets = framework_root / "workflows" / "presets"
        if framework_presets.exists():
            logger.debug(f"Using framework presets: {framework_presets}")
            return framework_presets

        # 2. Try packaged resources (for installed packages)
        if _resource_at is not None:
            packaged_presets = _resource_at("workflows", "presets")
            if packaged_presets is not None and packaged_presets.is_dir():
                # Convert Traversable to Path by finding a file in it
                try:
                    # List files to verify it's a valid directory
                    files = list(packaged_presets.iterdir())
                    if files:
                        # Use the first file's path to determine the actual filesystem path
                        # For packaged resources, we'll need to handle them differently
                        # For now, we'll fall through to cwd, but log this
                        logger.debug("Found packaged presets, but using cwd fallback")
                except Exception as e:
                    # Log but continue - packaged presets may not be accessible
                    logger.debug(f"Could not access packaged presets: {e}")
                    pass

        # 3. Fallback: try current working directory (for project-specific presets)
        cwd_presets = Path.cwd() / "workflows" / "presets"
        if cwd_presets.exists():
            logger.debug(f"Using project presets: {cwd_presets}")
            return cwd_presets

        # If none found, return framework location anyway (will be created if needed)
        logger.debug(f"No presets found, using framework location: {framework_presets}")
        return framework_presets

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

        # Try multiple locations to find the preset file
        preset_file = self._find_preset_file(preset_name)
        
        if preset_file is None:
            return None

        try:
            return self.parser.parse_file(preset_file)
        except Exception as e:
            raise ValueError(f"Failed to load preset '{preset_name}': {e}") from e

    def _find_preset_file(self, preset_name: str) -> Path | None:
        """
        Find preset file by checking multiple locations in order.
        
        Args:
            preset_name: Name of the preset (without .yaml extension)
            
        Returns:
            Path to preset file or None if not found
        """
        # 1. Check configured presets directory
        preset_file = self.presets_dir / f"{preset_name}.yaml"
        if preset_file.exists():
            return preset_file

        # 2. Try framework source location
        current_file = Path(__file__).parent  # tapps_agents/workflow/
        framework_root = current_file.parent.parent  # project_root/
        framework_preset = framework_root / "workflows" / "presets" / f"{preset_name}.yaml"
        if framework_preset.exists():
            logger.debug(f"Found preset in framework location: {framework_preset}")
            return framework_preset

        # 3. Try packaged resources
        if _resource_at is not None:
            try:
                packaged_preset = _resource_at("workflows", "presets", f"{preset_name}.yaml")
                if packaged_preset is not None and packaged_preset.is_file():
                    # For Traversable, we need to read it and write to a temp location
                    # since the parser expects a Path object
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as tmp:
                        tmp.write(packaged_preset.read_text(encoding='utf-8'))
                        tmp_path = Path(tmp.name)
                        logger.debug(f"Using packaged preset from temp file: {tmp_path}")
                        return tmp_path
            except Exception as e:
                logger.debug(f"Could not load packaged preset: {e}")

        # 4. Try current working directory
        cwd_preset = Path.cwd() / "workflows" / "presets" / f"{preset_name}.yaml"
        if cwd_preset.exists():
            logger.debug(f"Found preset in project location: {cwd_preset}")
            return cwd_preset

        return None

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
