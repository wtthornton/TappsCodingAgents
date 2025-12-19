"""
Comprehensive unit tests for PresetLoader.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from tapps_agents.workflow.preset_loader import PRESET_ALIASES, PresetLoader

pytestmark = pytest.mark.unit


@pytest.fixture
def temp_presets_dir():
    """Create temporary presets directory."""
    temp_dir = Path(tempfile.mkdtemp())
    presets_dir = temp_dir / "presets"
    presets_dir.mkdir(parents=True)
    yield presets_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def loader(temp_presets_dir):
    """Create PresetLoader instance."""
    return PresetLoader(presets_dir=temp_presets_dir)


@pytest.fixture
def sample_workflow_data():
    """Sample workflow data for testing."""
    return {
        "workflow": {
            "id": "full-sdlc",
            "name": "Full SDLC",
            "description": "Complete software development lifecycle",
            "version": "1.0.0",
            "steps": [
                {"name": "analyze", "agent": "analyst"},
                {"name": "design", "agent": "architect"},
            ],
        }
    }


class TestPresetLoaderInit:
    """Tests for PresetLoader initialization."""

    def test_init_with_presets_dir(self, temp_presets_dir):
        """Test initialization with explicit presets directory."""
        loader = PresetLoader(presets_dir=temp_presets_dir)
        assert loader.presets_dir == temp_presets_dir
        assert loader.parser is not None

    def test_init_without_presets_dir(self):
        """Test initialization without presets directory (uses default)."""
        loader = PresetLoader()
        # Should try to find presets directory relative to file
        assert loader.presets_dir is not None
        assert loader.parser is not None

    def test_init_fallback_to_cwd(self):
        """Test initialization falls back to cwd if default doesn't exist."""
        with patch("tapps_agents.workflow.preset_loader.Path") as mock_path:
            # Mock __file__ parent
            mock_file = Mock()
            mock_file.parent.parent.parent = Path("/nonexistent")
            mock_path.return_value.__file__ = mock_file
            mock_path.cwd.return_value = Path("/cwd")
            
            loader = PresetLoader()
            # Should use fallback
            assert loader.presets_dir is not None


class TestPresetLoaderGetPresetName:
    """Tests for get_preset_name method."""

    def test_get_preset_name_short_aliases(self, loader):
        """Test getting preset name from short aliases."""
        assert loader.get_preset_name("full") == "full-sdlc"
        assert loader.get_preset_name("rapid") == "rapid-dev"
        assert loader.get_preset_name("fix") == "maintenance"
        assert loader.get_preset_name("quality") == "quality"
        assert loader.get_preset_name("hotfix") == "quick-fix"

    def test_get_preset_name_voice_aliases(self, loader):
        """Test getting preset name from voice-friendly aliases."""
        assert loader.get_preset_name("enterprise") == "full-sdlc"
        assert loader.get_preset_name("feature") == "rapid-dev"
        assert loader.get_preset_name("refactor") == "maintenance"
        assert loader.get_preset_name("improve") == "quality"
        assert loader.get_preset_name("urgent") == "quick-fix"

    def test_get_preset_name_full_names(self, loader):
        """Test getting preset name from full names."""
        assert loader.get_preset_name("full-sdlc") == "full-sdlc"
        assert loader.get_preset_name("rapid-dev") == "rapid-dev"
        assert loader.get_preset_name("maintenance") == "maintenance"
        assert loader.get_preset_name("quick-fix") == "quick-fix"

    def test_get_preset_name_case_insensitive(self, loader):
        """Test that get_preset_name is case-insensitive."""
        assert loader.get_preset_name("FULL") == "full-sdlc"
        assert loader.get_preset_name("Rapid") == "rapid-dev"
        assert loader.get_preset_name("ENTERPRISE") == "full-sdlc"

    def test_get_preset_name_not_found(self, loader):
        """Test getting preset name for unknown alias."""
        assert loader.get_preset_name("unknown") is None
        assert loader.get_preset_name("") is None
        assert loader.get_preset_name("nonexistent") is None


class TestPresetLoaderListPresets:
    """Tests for list_presets method."""

    def test_list_presets_empty_directory(self, loader):
        """Test listing presets when directory is empty."""
        presets = loader.list_presets()
        
        # Should return dict with preset names from aliases
        assert isinstance(presets, dict)
        # Should have entries for all unique preset names
        unique_presets = set(PRESET_ALIASES.values())
        assert len(presets) == len(unique_presets)

    def test_list_presets_with_valid_file(self, loader, temp_presets_dir, sample_workflow_data):
        """Test listing presets with valid YAML file."""
        preset_file = temp_presets_dir / "full-sdlc.yaml"
        preset_file.write_text(yaml.dump(sample_workflow_data))
        
        presets = loader.list_presets()
        
        assert "full-sdlc" in presets
        assert presets["full-sdlc"]["name"] == "Full SDLC"
        assert presets["full-sdlc"]["description"] == "Complete software development lifecycle"
        assert "full" in presets["full-sdlc"]["aliases"]
        assert "enterprise" in presets["full-sdlc"]["aliases"]

    def test_list_presets_with_invalid_yaml(self, loader, temp_presets_dir):
        """Test listing presets with invalid YAML file."""
        preset_file = temp_presets_dir / "full-sdlc.yaml"
        preset_file.write_text("invalid: yaml: content: [")
        
        presets = loader.list_presets()
        
        # Should handle error gracefully and still return entry
        assert "full-sdlc" in presets
        assert presets["full-sdlc"]["name"] == "full-sdlc"  # Default name
        assert presets["full-sdlc"]["description"] == ""  # Default description

    def test_list_presets_with_missing_workflow_key(self, loader, temp_presets_dir):
        """Test listing presets with missing workflow key."""
        preset_file = temp_presets_dir / "full-sdlc.yaml"
        preset_file.write_text(yaml.dump({"not_workflow": {}}))
        
        presets = loader.list_presets()
        
        # Should handle KeyError gracefully
        assert "full-sdlc" in presets
        assert presets["full-sdlc"]["name"] == "full-sdlc"  # Default name

    def test_list_presets_with_multiple_presets(self, loader, temp_presets_dir):
        """Test listing multiple presets."""
        # Create multiple preset files
        for preset_name in ["full-sdlc", "rapid-dev", "maintenance"]:
            preset_file = temp_presets_dir / f"{preset_name}.yaml"
            preset_data = {
                "workflow": {
                    "id": preset_name,
                    "name": preset_name.replace("-", " ").title(),
                    "description": f"Description for {preset_name}",
                }
            }
            preset_file.write_text(yaml.dump(preset_data))
        
        presets = loader.list_presets()
        
        assert "full-sdlc" in presets
        assert "rapid-dev" in presets
        assert "maintenance" in presets
        assert "full" in presets["full-sdlc"]["aliases"]
        assert "rapid" in presets["rapid-dev"]["aliases"]
        assert "fix" in presets["maintenance"]["aliases"]

    def test_list_presets_aliases_aggregation(self, loader, temp_presets_dir):
        """Test that aliases are properly aggregated for each preset."""
        preset_file = temp_presets_dir / "full-sdlc.yaml"
        preset_data = {
            "workflow": {
                "id": "full-sdlc",
                "name": "Full SDLC",
            }
        }
        preset_file.write_text(yaml.dump(preset_data))
        
        presets = loader.list_presets()
        
        # Should have all aliases for full-sdlc
        aliases = presets["full-sdlc"]["aliases"]
        assert "full" in aliases
        assert "enterprise" in aliases
        assert "full-sdlc" in aliases


class TestPresetLoaderLoadPreset:
    """Tests for load_preset method."""

    def test_load_preset_by_name(self, loader, temp_presets_dir, sample_workflow_data):
        """Test loading preset by name."""
        preset_file = temp_presets_dir / "full-sdlc.yaml"
        preset_file.write_text(yaml.dump(sample_workflow_data))
        
        workflow = loader.load_preset("full-sdlc")
        
        assert workflow is not None
        assert workflow.id == "full-sdlc"

    def test_load_preset_by_alias(self, loader, temp_presets_dir, sample_workflow_data):
        """Test loading preset using alias."""
        preset_file = temp_presets_dir / "full-sdlc.yaml"
        preset_file.write_text(yaml.dump(sample_workflow_data))
        
        # Load using alias
        workflow = loader.load_preset("full")
        
        assert workflow is not None
        assert workflow.id == "full-sdlc"

    def test_load_preset_not_found(self, loader):
        """Test loading non-existent preset."""
        workflow = loader.load_preset("nonexistent")
        
        assert workflow is None

    def test_load_preset_direct_name_when_alias_not_found(self, loader, temp_presets_dir):
        """Test loading preset by direct name when alias doesn't exist."""
        preset_file = temp_presets_dir / "custom-workflow.yaml"
        preset_data = {
            "workflow": {
                "id": "custom-workflow",
                "name": "Custom Workflow",
                "steps": [],
            }
        }
        preset_file.write_text(yaml.dump(preset_data))
        
        # Try to load by direct name (not in aliases)
        workflow = loader.load_preset("custom-workflow")
        
        assert workflow is not None
        assert workflow.id == "custom-workflow"

    def test_load_preset_invalid_yaml(self, loader, temp_presets_dir):
        """Test loading preset with invalid YAML."""
        preset_file = temp_presets_dir / "full-sdlc.yaml"
        preset_file.write_text("invalid: yaml: [")
        
        with pytest.raises(ValueError, match="Failed to load preset"):
            loader.load_preset("full-sdlc")

    def test_load_preset_parser_error(self, loader, temp_presets_dir):
        """Test loading preset that causes parser error."""
        preset_file = temp_presets_dir / "full-sdlc.yaml"
        preset_file.write_text(yaml.dump({"workflow": {"invalid": "data"}}))
        
        # Parser might raise exception
        with patch.object(loader.parser, "parse_file", side_effect=Exception("Parse error")):
            with pytest.raises(ValueError, match="Failed to load preset"):
                loader.load_preset("full-sdlc")


class TestPresetLoaderFindPresetByIntent:
    """Tests for find_preset_by_intent method."""

    def test_find_preset_by_intent_full_sdlc(self, loader):
        """Test finding preset by intent for full SDLC."""
        assert loader.find_preset_by_intent("run full sdlc") == "full-sdlc"
        assert loader.find_preset_by_intent("enterprise development") == "full-sdlc"
        assert loader.find_preset_by_intent("complete lifecycle") == "full-sdlc"

    def test_find_preset_by_intent_rapid_dev(self, loader):
        """Test finding preset by intent for rapid development."""
        assert loader.find_preset_by_intent("rapid development") == "rapid-dev"
        assert loader.find_preset_by_intent("quick feature") == "rapid-dev"
        assert loader.find_preset_by_intent("fast sprint") == "rapid-dev"

    def test_find_preset_by_intent_maintenance(self, loader):
        """Test finding preset by intent for maintenance."""
        assert loader.find_preset_by_intent("maintenance work") == "maintenance"
        assert loader.find_preset_by_intent("fix bugs") == "maintenance"
        assert loader.find_preset_by_intent("refactor code") == "maintenance"

    def test_find_preset_by_intent_quality(self, loader):
        """Test finding preset by intent for quality."""
        assert loader.find_preset_by_intent("improve quality") == "quality"
        assert loader.find_preset_by_intent("code review") == "quality"
        assert loader.find_preset_by_intent("clean code") == "quality"

    def test_find_preset_by_intent_quick_fix(self, loader):
        """Test finding preset by intent for quick fix."""
        assert loader.find_preset_by_intent("hotfix urgent") == "quick-fix"
        assert loader.find_preset_by_intent("quick fix emergency") == "quick-fix"
        assert loader.find_preset_by_intent("critical patch") == "quick-fix"

    def test_find_preset_by_intent_multiple_keywords(self, loader):
        """Test finding preset with multiple matching keywords."""
        # Should return preset with highest score
        result = loader.find_preset_by_intent("rapid quick fast feature")
        assert result == "rapid-dev"

    def test_find_preset_by_intent_no_match(self, loader):
        """Test finding preset with no matching keywords."""
        assert loader.find_preset_by_intent("random text") is None
        assert loader.find_preset_by_intent("") is None

    def test_find_preset_by_intent_case_insensitive(self, loader):
        """Test that find_preset_by_intent is case-insensitive."""
        assert loader.find_preset_by_intent("FULL SDLC") == "full-sdlc"
        assert loader.find_preset_by_intent("Rapid Development") == "rapid-dev"

    def test_find_preset_by_intent_highest_score_wins(self, loader):
        """Test that preset with highest keyword score wins."""
        # "rapid" and "quick" both match rapid-dev, "hotfix" matches quick-fix
        # rapid-dev should win with 2 keywords vs 1
        result = loader.find_preset_by_intent("rapid quick hotfix")
        assert result == "rapid-dev"  # 2 keywords vs 1

