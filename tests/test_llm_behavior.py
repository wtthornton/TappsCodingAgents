"""
Tests for LLM Behavior Configuration (ENH-001-S4).

Tests the EnforcementConfig dataclass including validation,
YAML loading, error handling, and default values.
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from tapps_agents.core.llm_behavior import EnforcementConfig

pytestmark = pytest.mark.unit


class TestEnforcementConfigDefaults:
    """Test default configuration values."""

    def test_default_values(self):
        """Test that default configuration values are correct."""
        config = EnforcementConfig()

        assert config.mode == "blocking"
        assert config.confidence_threshold == 60.0
        assert config.suggest_workflows is True
        assert config.block_direct_edits is True

    def test_default_initialization(self):
        """Test EnforcementConfig initializes with defaults."""
        config = EnforcementConfig()

        # Verify all fields have expected defaults
        assert isinstance(config.mode, str)
        assert isinstance(config.confidence_threshold, float)
        assert isinstance(config.suggest_workflows, bool)
        assert isinstance(config.block_direct_edits, bool)


class TestEnforcementConfigCustomValues:
    """Test custom configuration values."""

    def test_custom_blocking_mode(self):
        """Test custom configuration with blocking mode."""
        config = EnforcementConfig(
            mode="blocking",
            confidence_threshold=75.0,
            suggest_workflows=False,
            block_direct_edits=True
        )

        assert config.mode == "blocking"
        assert config.confidence_threshold == 75.0
        assert config.suggest_workflows is False
        assert config.block_direct_edits is True

    def test_custom_warning_mode(self):
        """Test custom configuration with warning mode."""
        config = EnforcementConfig(
            mode="warning",
            confidence_threshold=50.0,
            suggest_workflows=True,
            block_direct_edits=False
        )

        assert config.mode == "warning"
        assert config.confidence_threshold == 50.0
        assert config.suggest_workflows is True
        assert config.block_direct_edits is False

    def test_custom_silent_mode(self):
        """Test custom configuration with silent mode."""
        config = EnforcementConfig(
            mode="silent",
            confidence_threshold=80.0,
            suggest_workflows=False,
            block_direct_edits=False
        )

        assert config.mode == "silent"
        assert config.confidence_threshold == 80.0
        assert config.suggest_workflows is False
        assert config.block_direct_edits is False

    def test_edge_case_threshold_zero(self):
        """Test threshold at minimum edge (0)."""
        config = EnforcementConfig(confidence_threshold=0.0)
        assert config.confidence_threshold == 0.0

    def test_edge_case_threshold_hundred(self):
        """Test threshold at maximum edge (100)."""
        config = EnforcementConfig(confidence_threshold=100.0)
        assert config.confidence_threshold == 100.0


class TestEnforcementConfigValidation:
    """Test configuration validation."""

    def test_invalid_mode_raises_valueerror(self):
        """Test that invalid mode raises ValueError."""
        with pytest.raises(ValueError, match="Invalid enforcement mode"):
            EnforcementConfig(mode="invalid")

    def test_invalid_mode_empty_string(self):
        """Test that empty string mode raises ValueError."""
        with pytest.raises(ValueError, match="Invalid enforcement mode"):
            EnforcementConfig(mode="")

    def test_invalid_mode_numeric(self):
        """Test that numeric mode raises ValueError."""
        with pytest.raises(ValueError, match="Invalid enforcement mode"):
            EnforcementConfig(mode="123")

    def test_threshold_too_low_raises_valueerror(self):
        """Test that threshold below 0 raises ValueError."""
        with pytest.raises(ValueError, match="must be in range"):
            EnforcementConfig(confidence_threshold=-1.0)

    def test_threshold_too_high_raises_valueerror(self):
        """Test that threshold above 100 raises ValueError."""
        with pytest.raises(ValueError, match="must be in range"):
            EnforcementConfig(confidence_threshold=101.0)

    def test_threshold_way_out_of_range(self):
        """Test threshold far outside valid range."""
        with pytest.raises(ValueError, match="must be in range"):
            EnforcementConfig(confidence_threshold=500.0)

    def test_threshold_negative_extreme(self):
        """Test threshold with large negative value."""
        with pytest.raises(ValueError, match="must be in range"):
            EnforcementConfig(confidence_threshold=-100.0)

    def test_threshold_non_numeric_string(self):
        """Test that non-numeric threshold raises TypeError."""
        with pytest.raises(TypeError, match="must be a number"):
            EnforcementConfig(confidence_threshold="invalid")  # type: ignore

    def test_threshold_none_raises_typeerror(self):
        """Test that None threshold raises TypeError."""
        with pytest.raises(TypeError, match="must be a number"):
            EnforcementConfig(confidence_threshold=None)  # type: ignore

    def test_threshold_list_raises_typeerror(self):
        """Test that list threshold raises TypeError."""
        with pytest.raises(TypeError, match="must be a number"):
            EnforcementConfig(confidence_threshold=[60])  # type: ignore


class TestEnforcementConfigFromFile:
    """Test loading configuration from YAML files."""

    def test_load_valid_config(self):
        """Test loading valid configuration from file."""
        config_data = {
            "llm_behavior": {
                "workflow_enforcement": {
                    "mode": "warning",
                    "confidence_threshold": 70,
                    "suggest_workflows": False,
                    "block_direct_edits": False
                }
            }
        }

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            config = EnforcementConfig.from_config_file(config_path)

            assert config.mode == "warning"
            assert config.confidence_threshold == 70.0
            assert config.suggest_workflows is False
            assert config.block_direct_edits is False
        finally:
            config_path.unlink()

    def test_load_config_with_all_modes(self):
        """Test loading config with each valid mode."""
        for mode in ["blocking", "warning", "silent"]:
            config_data = {
                "llm_behavior": {
                    "workflow_enforcement": {
                        "mode": mode
                    }
                }
            }

            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.yaml', delete=False, encoding='utf-8'
            ) as f:
                yaml.dump(config_data, f)
                config_path = Path(f.name)

            try:
                config = EnforcementConfig.from_config_file(config_path)
                assert config.mode == mode
            finally:
                config_path.unlink()

    def test_missing_file_returns_defaults(self):
        """Test that missing config file returns defaults."""
        config = EnforcementConfig.from_config_file(Path("nonexistent.yaml"))

        assert config.mode == "blocking"
        assert config.confidence_threshold == 60.0
        assert config.suggest_workflows is True
        assert config.block_direct_edits is True

    def test_empty_file_returns_defaults(self):
        """Test that empty config file returns defaults."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            f.write("")
            config_path = Path(f.name)

        try:
            config = EnforcementConfig.from_config_file(config_path)

            assert config.mode == "blocking"
            assert config.confidence_threshold == 60.0
        finally:
            config_path.unlink()

    def test_missing_llm_behavior_section_returns_defaults(self):
        """Test that missing llm_behavior section returns defaults."""
        config_data = {"other_section": {"key": "value"}}

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            config = EnforcementConfig.from_config_file(config_path)

            assert config.mode == "blocking"
            assert config.confidence_threshold == 60.0
        finally:
            config_path.unlink()

    def test_missing_workflow_enforcement_section_returns_defaults(self):
        """Test that missing workflow_enforcement section returns defaults."""
        config_data = {
            "llm_behavior": {
                "other_setting": "value"
            }
        }

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            config = EnforcementConfig.from_config_file(config_path)

            assert config.mode == "blocking"
            assert config.confidence_threshold == 60.0
        finally:
            config_path.unlink()

    def test_llm_behavior_not_dict_returns_defaults(self):
        """Test that non-dict llm_behavior returns defaults."""
        config_data = {"llm_behavior": "not a dict"}

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            config = EnforcementConfig.from_config_file(config_path)
            assert config.mode == "blocking"
        finally:
            config_path.unlink()

    def test_workflow_enforcement_not_dict_returns_defaults(self):
        """Test that non-dict workflow_enforcement returns defaults."""
        config_data = {
            "llm_behavior": {
                "workflow_enforcement": "not a dict"
            }
        }

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            config = EnforcementConfig.from_config_file(config_path)
            assert config.mode == "blocking"
        finally:
            config_path.unlink()

    def test_partial_config_uses_defaults(self):
        """Test that partial config fills in defaults for missing fields."""
        config_data = {
            "llm_behavior": {
                "workflow_enforcement": {
                    "mode": "silent"
                    # Other fields missing
                }
            }
        }

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            config = EnforcementConfig.from_config_file(config_path)

            assert config.mode == "silent"  # From config
            assert config.confidence_threshold == 60.0  # Default
            assert config.suggest_workflows is True  # Default
            assert config.block_direct_edits is True  # Default
        finally:
            config_path.unlink()

    def test_invalid_yaml_raises_valueerror(self):
        """Test that invalid YAML syntax raises ValueError."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            f.write("invalid: yaml: syntax:\n  - broken")
            config_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Invalid YAML"):
                EnforcementConfig.from_config_file(config_path)
        finally:
            config_path.unlink()

    def test_invalid_mode_in_file_raises_valueerror(self):
        """Test that invalid mode in config file raises ValueError."""
        config_data = {
            "llm_behavior": {
                "workflow_enforcement": {
                    "mode": "invalid_mode"
                }
            }
        }

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Invalid enforcement mode"):
                EnforcementConfig.from_config_file(config_path)
        finally:
            config_path.unlink()

    def test_invalid_threshold_in_file_raises_valueerror(self):
        """Test that invalid threshold in config file raises ValueError."""
        config_data = {
            "llm_behavior": {
                "workflow_enforcement": {
                    "confidence_threshold": 150
                }
            }
        }

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="must be in range"):
                EnforcementConfig.from_config_file(config_path)
        finally:
            config_path.unlink()

    def test_type_conversion_int_to_float_threshold(self):
        """Test that integer threshold is converted to float."""
        config_data = {
            "llm_behavior": {
                "workflow_enforcement": {
                    "confidence_threshold": 75  # Integer
                }
            }
        }

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            config = EnforcementConfig.from_config_file(config_path)

            assert config.confidence_threshold == 75.0
            assert isinstance(config.confidence_threshold, float)
        finally:
            config_path.unlink()

    def test_type_conversion_bool_flags(self):
        """Test that boolean values are handled correctly."""
        config_data = {
            "llm_behavior": {
                "workflow_enforcement": {
                    "suggest_workflows": True,
                    "block_direct_edits": False
                }
            }
        }

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            config = EnforcementConfig.from_config_file(config_path)

            assert config.suggest_workflows is True
            assert config.block_direct_edits is False
        finally:
            config_path.unlink()

    def test_load_from_none_path_uses_default(self):
        """Test that None config_path uses default path."""
        # This test assumes default config doesn't exist
        config = EnforcementConfig.from_config_file(None)

        # Should return defaults since default config likely doesn't exist
        assert config.mode in ["blocking", "warning", "silent"]
        assert 0 <= config.confidence_threshold <= 100


class TestEnforcementConfigEdgeCases:
    """Test edge cases and error scenarios."""

    def test_threshold_boundary_values(self):
        """Test threshold at exact boundaries."""
        # Test minimum boundary
        config_min = EnforcementConfig(confidence_threshold=0.0)
        assert config_min.confidence_threshold == 0.0

        # Test maximum boundary
        config_max = EnforcementConfig(confidence_threshold=100.0)
        assert config_max.confidence_threshold == 100.0

    def test_threshold_just_outside_boundaries(self):
        """Test threshold just outside valid range."""
        # Just below minimum
        with pytest.raises(ValueError):
            EnforcementConfig(confidence_threshold=-0.1)

        # Just above maximum
        with pytest.raises(ValueError):
            EnforcementConfig(confidence_threshold=100.1)

    def test_all_boolean_combinations(self):
        """Test all combinations of boolean flags."""
        combinations = [
            (True, True),
            (True, False),
            (False, True),
            (False, False)
        ]

        for suggest, block in combinations:
            config = EnforcementConfig(
                suggest_workflows=suggest,
                block_direct_edits=block
            )
            assert config.suggest_workflows == suggest
            assert config.block_direct_edits == block

    def test_unicode_in_yaml_file(self):
        """Test handling of Unicode characters in YAML."""
        config_data = {
            "llm_behavior": {
                "workflow_enforcement": {
                    "mode": "blocking"
                }
            },
            "comment": "Test with émojis 🎉"
        }

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            yaml.dump(config_data, f, allow_unicode=True)
            config_path = Path(f.name)

        try:
            config = EnforcementConfig.from_config_file(config_path)
            assert config.mode == "blocking"
        finally:
            config_path.unlink()

    def test_very_large_yaml_file(self):
        """Test handling of large YAML file with enforcement config."""
        config_data = {
            "llm_behavior": {
                "workflow_enforcement": {
                    "mode": "warning",
                    "confidence_threshold": 65.0
                }
            },
            "other_large_section": {f"key_{i}": f"value_{i}" for i in range(1000)}
        }

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            config = EnforcementConfig.from_config_file(config_path)

            assert config.mode == "warning"
            assert config.confidence_threshold == 65.0
        finally:
            config_path.unlink()


class TestEnforcementConfigIntegration:
    """Integration tests with real config file."""

    def test_load_from_actual_config_file_if_exists(self):
        """Test loading from actual project config file if it exists."""
        config_path = Path(".tapps-agents/config.yaml")

        if config_path.exists():
            # Try to load config - should not raise
            config = EnforcementConfig.from_config_file(config_path)

            # Verify config is valid
            assert config.mode in ["blocking", "warning", "silent"]
            assert 0 <= config.confidence_threshold <= 100
            assert isinstance(config.suggest_workflows, bool)
            assert isinstance(config.block_direct_edits, bool)
        else:
            # If file doesn't exist, should return defaults
            config = EnforcementConfig.from_config_file(config_path)

            assert config.mode == "blocking"
            assert config.confidence_threshold == 60.0

    def test_create_and_load_realistic_config(self):
        """Test creating and loading a realistic configuration."""
        # Create a realistic config
        config_data = {
            "llm_behavior": {
                "mode": "senior-developer",
                "workflow_enforcement": {
                    "mode": "blocking",
                    "confidence_threshold": 60,
                    "suggest_workflows": True,
                    "block_direct_edits": True
                }
            },
            "agents": {
                "reviewer": {
                    "quality_threshold": 70.0
                }
            }
        }

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            config = EnforcementConfig.from_config_file(config_path)

            assert config.mode == "blocking"
            assert config.confidence_threshold == 60.0
            assert config.suggest_workflows is True
            assert config.block_direct_edits is True
        finally:
            config_path.unlink()
