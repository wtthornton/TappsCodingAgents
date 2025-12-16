"""
Unit tests for Preset Loader.
"""

from pathlib import Path

import pytest
import yaml

from tapps_agents.workflow.preset_loader import PresetLoader

pytestmark = pytest.mark.unit


class TestPresetLoader:
    """Test cases for PresetLoader."""

    @pytest.fixture
    def presets_dir(self, tmp_path):
        """Create a temporary presets directory."""
        presets_dir = tmp_path / "presets"
        presets_dir.mkdir()
        return presets_dir

    @pytest.fixture
    def loader(self, presets_dir):
        """Create a PresetLoader instance."""
        return PresetLoader(presets_dir=presets_dir)

    def test_loader_initialization(self, loader, presets_dir):
        """Test loader initialization."""
        assert loader.presets_dir == presets_dir

    def test_get_preset_name_from_alias(self, loader):
        """Test getting preset name from alias."""
        assert loader.get_preset_name("full") == "full-sdlc"
        assert loader.get_preset_name("rapid") == "rapid-dev"
        assert loader.get_preset_name("fix") == "maintenance"
        assert loader.get_preset_name("enterprise") == "full-sdlc"
        assert loader.get_preset_name("feature") == "rapid-dev"

    def test_get_preset_name_not_found(self, loader):
        """Test getting preset name for unknown alias."""
        assert loader.get_preset_name("unknown") is None

    def test_list_presets_empty(self, loader):
        """Test listing presets when directory is empty."""
        presets = loader.list_presets()
        
        # Should return empty dict or dict with metadata but no files
        assert isinstance(presets, dict)

    def test_list_presets_with_files(self, loader, presets_dir):
        """Test listing presets with YAML files."""
        # Create a preset file
        preset_file = presets_dir / "full-sdlc.yaml"
        preset_data = {
            "workflow": {
                "id": "full-sdlc",
                "name": "Full SDLC",
                "description": "Complete software development lifecycle"
            }
        }
        preset_file.write_text(yaml.dump(preset_data))
        
        presets = loader.list_presets()
        
        assert "full-sdlc" in presets
        assert presets["full-sdlc"]["name"] == "Full SDLC"

    def test_load_preset_success(self, loader, presets_dir):
        """Test loading a preset successfully."""
        preset_file = presets_dir / "full-sdlc.yaml"
        preset_data = {
            "workflow": {
                "id": "full-sdlc",
                "name": "Full SDLC",
                "version": "1.0.0",
                "steps": []
            }
        }
        preset_file.write_text(yaml.dump(preset_data))
        
        workflow = loader.load_preset("full-sdlc")
        
        assert workflow is not None
        assert workflow.id == "full-sdlc"

    def test_load_preset_not_found(self, loader):
        """Test loading a non-existent preset."""
        workflow = loader.load_preset("nonexistent")
        
        assert workflow is None

    def test_load_preset_by_alias(self, loader, presets_dir):
        """Test loading preset using alias."""
        preset_file = presets_dir / "full-sdlc.yaml"
        preset_data = {
            "workflow": {
                "id": "full-sdlc",
                "name": "Full SDLC",
                "version": "1.0.0",
                "steps": []
            }
        }
        preset_file.write_text(yaml.dump(preset_data))
        
        # Load using alias
        workflow = loader.load_preset("full")
        
        assert workflow is not None
        assert workflow.id == "full-sdlc"

