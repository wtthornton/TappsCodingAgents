"""
Unit tests for configuration system.
"""

from pathlib import Path

import pytest
import yaml

from tapps_agents.core.config import (
    AgentsConfig,
    BeadsConfig,
    ProjectConfig,
    ReviewerAgentConfig,
    ScoringWeightsConfig,
    get_default_config,
    load_config,
)


@pytest.mark.unit
class TestScoringWeightsConfig:
    """Test ScoringWeightsConfig model"""

    def test_default_weights(self):
        """Test that default weights are valid (7 categories, must sum to 1.0)."""
        weights = ScoringWeightsConfig()
        assert weights.complexity == 0.18
        assert weights.security == 0.27
        assert weights.maintainability == 0.24
        assert weights.test_coverage == 0.13
        assert weights.performance == 0.08
        assert weights.structure == 0.05
        assert weights.devex == 0.05

    def test_weights_sum_validation(self):
        """Test that weights must sum to 1.0 (all 7 categories)."""
        # Valid: all 7 sum to 1.0
        weights = ScoringWeightsConfig(
            complexity=0.20,
            security=0.20,
            maintainability=0.20,
            test_coverage=0.15,
            performance=0.10,
            structure=0.08,
            devex=0.07,
        )
        assert (
            weights.complexity
            + weights.security
            + weights.maintainability
            + weights.test_coverage
            + weights.performance
            + weights.structure
            + weights.devex
        ) == 1.0

        # Invalid: doesn't sum to 1.0 (passing 5 leaves structure/devex at 0.05 each -> 1.6)
        with pytest.raises(ValueError, match="must sum to 1.0"):
            ScoringWeightsConfig(
                complexity=0.3,
                security=0.3,
                maintainability=0.3,
                test_coverage=0.3,
                performance=0.3,
            )

    def test_weight_range_validation(self):
        """Test that weights must be between 0.0 and 1.0"""
        with pytest.raises(ValueError):
            ScoringWeightsConfig(complexity=-0.1)

        with pytest.raises(ValueError):
            ScoringWeightsConfig(complexity=1.1)


@pytest.mark.unit
class TestReviewerAgentConfig:
    """Test ReviewerAgentConfig model"""

    def test_default_values(self):
        """Test default configuration values"""
        config = ReviewerAgentConfig()
        assert config.quality_threshold == 70.0
        assert config.include_scoring is True
        assert config.include_llm_feedback is True
        assert config.max_file_size == 1024 * 1024

    def test_threshold_range_validation(self):
        """Test quality_threshold range validation"""
        with pytest.raises(ValueError):
            ReviewerAgentConfig(quality_threshold=-1.0)

        with pytest.raises(ValueError):
            ReviewerAgentConfig(quality_threshold=101.0)

    def test_max_file_size_validation(self):
        """Test max_file_size minimum validation"""
        with pytest.raises(ValueError):
            ReviewerAgentConfig(max_file_size=500)  # Below minimum 1024


@pytest.mark.unit
class TestBeadsConfig:
    """Test BeadsConfig model."""

    def test_default_values(self):
        """BeadsConfig defaults: enabled=True, required=False, hooks_simple_mode=True, etc."""
        c = BeadsConfig()
        assert c.enabled is True
        assert c.required is False
        assert c.sync_epic is True
        assert c.hooks_simple_mode is True
        assert c.hooks_workflow is True
        assert c.hooks_review is False
        assert c.hooks_test is False
        assert c.hooks_refactor is False


@pytest.mark.unit
class TestProjectConfig:
    """Test ProjectConfig root model"""

    def test_default_config(self):
        """Test that default config has all required sections"""
        config = ProjectConfig()
        assert config.agents is not None
        assert config.scoring is not None
        assert isinstance(config.agents.reviewer, ReviewerAgentConfig)
        assert isinstance(config.scoring.weights, ScoringWeightsConfig)
        assert isinstance(config.beads, BeadsConfig)
        assert config.beads.enabled is True

    def test_custom_config(self):
        """Test creating config with custom values"""
        config = ProjectConfig(
            project_name="TestProject",
            version="1.0.0",
            agents=AgentsConfig(reviewer=ReviewerAgentConfig(quality_threshold=80.0)),
        )
        assert config.project_name == "TestProject"
        assert config.version == "1.0.0"
        assert config.agents.reviewer.quality_threshold == 80.0

    def test_extra_fields_ignored(self):
        """Test that extra fields in config are ignored"""
        config_dict = {
            "project_name": "Test",
            "unknown_field": "should be ignored",
            "agents": {},
        }
        config = ProjectConfig(**config_dict)
        assert config.project_name == "Test"
        assert not hasattr(config, "unknown_field")


@pytest.mark.unit
class TestLoadConfig:
    """Test configuration loading functions"""

    def test_load_config_defaults(self):
        """Test loading config when no file exists returns defaults"""
        config = load_config(Path("/nonexistent/path/config.yaml"))
        assert isinstance(config, ProjectConfig)
        assert config.agents.reviewer.quality_threshold == 70.0

    def test_load_config_from_file(self, tmp_path: Path):
        """Test loading config from YAML file"""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "project_name": "TestProject",
            "agents": {
                "reviewer": {"quality_threshold": 85.0}
            },
            "scoring": {"quality_threshold": 85.0},
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = load_config(config_file)
        assert config.project_name == "TestProject"
        assert config.agents.reviewer.quality_threshold == 85.0
        assert config.scoring.quality_threshold == 85.0

    def test_load_config_invalid_yaml(self, tmp_path: Path):
        """Test that invalid YAML raises ValueError"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("invalid: yaml: content: [")

        with pytest.raises(ValueError, match="Invalid YAML"):
            load_config(config_file)

    def test_load_config_invalid_values(self, tmp_path: Path):
        """Test that invalid config values raise ValueError"""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "scoring": {
                "weights": {
                    "complexity": 0.5,
                    "security": 0.5,
                    "maintainability": 0.5,  # Will exceed 1.0
                    "test_coverage": 0.5,
                    "performance": 0.5,
                }
            }
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        with pytest.raises(ValueError):
            load_config(config_file)

    def test_load_config_empty_file(self, tmp_path: Path):
        """Test that empty config file returns defaults"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("")

        config = load_config(config_file)
        assert isinstance(config, ProjectConfig)
        assert config.agents.reviewer.quality_threshold == 70.0

    def test_load_config_with_utf8_bom(self, tmp_path: Path):
        """Test loading config file with UTF-8 BOM (common on Windows)."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "project_name": "BOMTestProject",
            "agents": {
                "reviewer": {"quality_threshold": 90.0}
            },
        }
        # Write YAML content with UTF-8 BOM prefix
        yaml_content = yaml.dump(config_data)
        # UTF-8 BOM: \xef\xbb\xbf (bytes) prepended to content
        config_file.write_bytes(b"\xef\xbb\xbf" + yaml_content.encode("utf-8"))

        # Should load successfully despite BOM
        config = load_config(config_file)
        assert config.project_name == "BOMTestProject"
        assert config.agents.reviewer.quality_threshold == 90.0

    def test_get_default_config(self):
        """Test that get_default_config returns a dictionary"""
        config_dict = get_default_config()
        assert isinstance(config_dict, dict)
        assert "agents" in config_dict
        assert "scoring" in config_dict


@pytest.mark.unit
class TestConfigIntegration:
    """Integration tests for configuration system"""

    def test_full_config_example(self, tmp_path: Path):
        """Test loading a complete configuration example"""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "project_name": "MyProject",
            "version": "1.0.0",
            "agents": {
                "reviewer": {
                    "quality_threshold": 75.0,
                    "include_scoring": True,
                    "include_llm_feedback": True,
                    "max_file_size": 2097152,
                }
            },
            "scoring": {
                "weights": {
                    "complexity": 0.14,
                    "security": 0.32,
                    "maintainability": 0.22,
                    "test_coverage": 0.14,
                    "performance": 0.08,
                    "structure": 0.05,
                    "devex": 0.05,
                },
                "quality_threshold": 75.0,
            },
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = load_config(config_file)

        # Verify all values loaded correctly
        assert config.project_name == "MyProject"
        assert config.version == "1.0.0"
        assert config.agents.reviewer.quality_threshold == 75.0
        assert config.agents.reviewer.max_file_size == 2097152
        assert config.scoring.weights.security == 0.32
        assert config.scoring.quality_threshold == 75.0

    def test_config_merging_partial_config(self, tmp_path: Path):
        """Test that partial config merges correctly with defaults (Story 18.3)."""
        # Create a config file with only some fields set
        config_file = tmp_path / "config.yaml"
        config_data = {
            "project_name": "MyProject",
            # Only set some reviewer config, leave others as defaults
            "agents": {
                "reviewer": {
                    "quality_threshold": 80.0,
                    # include_scoring, etc. should use defaults
                }
            },
            # Only set scoring quality_threshold, weights should use defaults
            "scoring": {
                "quality_threshold": 75.0,
            },
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = load_config(config_file)

        # Verify explicitly set values
        assert config.project_name == "MyProject"
        assert config.agents.reviewer.quality_threshold == 80.0
        assert config.scoring.quality_threshold == 75.0

        # Verify defaults are applied for unset values
        assert config.agents.reviewer.include_scoring is True, \
            "include_scoring should use default value when not specified"
        assert config.agents.reviewer.max_file_size == 1024 * 1024, \
            "max_file_size should use default value when not specified"
        
        # Verify scoring weights use defaults (7-weight model)
        assert config.scoring.weights.complexity == 0.18, \
            "scoring.weights.complexity should use default value when not specified"
        assert config.scoring.weights.security == 0.27, \
            "scoring.weights.security should use default value when not specified"
        assert config.scoring.weights.maintainability == 0.24, \
            "scoring.weights.maintainability should use default value when not specified"

    def test_config_default_values_application(self, tmp_path: Path):
        """Test that default values are correctly applied when fields are missing (Story 18.3)."""
        # Create minimal config file (empty dict)
        config_file = tmp_path / "config.yaml"
        config_data = {}
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = load_config(config_file)

        # Verify all default values are applied
        assert config.agents.reviewer.quality_threshold == 70.0, \
            "Reviewer quality_threshold should use default"
        assert config.agents.reviewer.include_scoring is True, \
            "Reviewer include_scoring should use default"
        assert config.agents.reviewer.max_file_size == 1024 * 1024, \
            "Reviewer max_file_size should use default"
        
        # Verify scoring defaults (7-weight model)
        assert config.scoring.weights.complexity == 0.18
        assert config.scoring.weights.security == 0.27
        assert config.scoring.weights.maintainability == 0.24
        assert config.scoring.weights.test_coverage == 0.13
        assert config.scoring.weights.performance == 0.08
        assert config.scoring.weights.structure == 0.05
        assert config.scoring.weights.devex == 0.05
        assert config.scoring.quality_threshold == 70.0
        
        # Verify all 7 weights sum to 1.0
        weights_sum = (
            config.scoring.weights.complexity
            + config.scoring.weights.security
            + config.scoring.weights.maintainability
            + config.scoring.weights.test_coverage
            + config.scoring.weights.performance
            + config.scoring.weights.structure
            + config.scoring.weights.devex
        )
        assert abs(weights_sum - 1.0) < 0.01, \
            f"Default weights should sum to 1.0, got {weights_sum}"

    def test_config_merging_nested_structures(self, tmp_path: Path):
        """Test that nested config structures merge correctly (Story 18.3)."""
        # Create config with partial nested structure
        config_file = tmp_path / "config.yaml"
        config_data = {
            "agents": {
                "reviewer": {
                    "quality_threshold": 85.0,
                    # Don't specify other reviewer fields (should use defaults)
                },
                # Don't specify other agents (should use defaults)
            },
            "scoring": {
                "quality_threshold": 80.0,
                # Don't specify weights (should use defaults)
            },
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = load_config(config_file)

        # Verify overridden values
        assert config.agents.reviewer.quality_threshold == 85.0
        assert config.scoring.quality_threshold == 80.0

        # Verify defaults are applied for unset nested fields
        assert config.agents.reviewer.include_scoring is True, \
            "include_scoring should use default when not specified"
        assert config.agents.reviewer.max_file_size == 1024 * 1024, \
            "max_file_size should use default when not specified"
        
        # Verify default weights are applied (7-weight model)
        assert config.scoring.weights.complexity == 0.18
        assert config.scoring.weights.security == 0.27
        assert config.scoring.weights.maintainability == 0.24
        assert config.scoring.weights.test_coverage == 0.13
        assert config.scoring.weights.performance == 0.08
        assert config.scoring.weights.structure == 0.05
        assert config.scoring.weights.devex == 0.05
        
        # Verify all 7 weights sum to 1.0
        weights_sum = (
            config.scoring.weights.complexity
            + config.scoring.weights.security
            + config.scoring.weights.maintainability
            + config.scoring.weights.test_coverage
            + config.scoring.weights.performance
            + config.scoring.weights.structure
            + config.scoring.weights.devex
        )
        assert abs(weights_sum - 1.0) < 0.01, \
            f"Default weights should sum to 1.0, got {weights_sum}"