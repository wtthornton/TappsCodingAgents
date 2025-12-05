"""
Unit tests for configuration system.
"""

import pytest
from pathlib import Path
import yaml
import tempfile

from tapps_agents.core.config import (
    ProjectConfig,
    ScoringWeightsConfig,
    ScoringConfig,
    MALConfig,
    ReviewerAgentConfig,
    AgentsConfig,
    load_config,
    get_default_config,
)


@pytest.mark.unit
class TestScoringWeightsConfig:
    """Test ScoringWeightsConfig model"""
    
    def test_default_weights(self):
        """Test that default weights are valid"""
        weights = ScoringWeightsConfig()
        assert weights.complexity == 0.20
        assert weights.security == 0.30
        assert weights.maintainability == 0.25
        assert weights.test_coverage == 0.15
        assert weights.performance == 0.10
    
    def test_weights_sum_validation(self):
        """Test that weights must sum to 1.0"""
        # Valid: sums to 1.0
        weights = ScoringWeightsConfig(
            complexity=0.25,
            security=0.25,
            maintainability=0.25,
            test_coverage=0.15,
            performance=0.10
        )
        assert sum([weights.complexity, weights.security, weights.maintainability,
                   weights.test_coverage, weights.performance]) == 1.0
        
        # Invalid: doesn't sum to 1.0
        with pytest.raises(ValueError, match="must sum to 1.0"):
            ScoringWeightsConfig(
                complexity=0.3,
                security=0.3,
                maintainability=0.3,
                test_coverage=0.3,
                performance=0.3
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
        assert config.model == "qwen2.5-coder:7b"
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
class TestMALConfig:
    """Test MALConfig model"""
    
    def test_default_values(self):
        """Test default MAL configuration"""
        config = MALConfig()
        assert config.ollama_url == "http://localhost:11434"
        assert config.default_model == "qwen2.5-coder:7b"
        assert config.timeout == 60.0
    
    def test_timeout_validation(self):
        """Test timeout minimum validation"""
        with pytest.raises(ValueError):
            MALConfig(timeout=0.5)  # Below minimum 1.0


@pytest.mark.unit
class TestProjectConfig:
    """Test ProjectConfig root model"""
    
    def test_default_config(self):
        """Test that default config has all required sections"""
        config = ProjectConfig()
        assert config.agents is not None
        assert config.scoring is not None
        assert config.mal is not None
        assert isinstance(config.agents.reviewer, ReviewerAgentConfig)
        assert isinstance(config.scoring.weights, ScoringWeightsConfig)
        assert isinstance(config.mal, MALConfig)
    
    def test_custom_config(self):
        """Test creating config with custom values"""
        config = ProjectConfig(
            project_name="TestProject",
            version="1.0.0",
            agents=AgentsConfig(
                reviewer=ReviewerAgentConfig(quality_threshold=80.0)
            )
        )
        assert config.project_name == "TestProject"
        assert config.version == "1.0.0"
        assert config.agents.reviewer.quality_threshold == 80.0
    
    def test_extra_fields_ignored(self):
        """Test that extra fields in config are ignored"""
        config_dict = {
            "project_name": "Test",
            "unknown_field": "should be ignored",
            "agents": {}
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
                "reviewer": {
                    "quality_threshold": 85.0,
                    "model": "custom-model:7b"
                }
            },
            "scoring": {
                "quality_threshold": 85.0
            }
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        config = load_config(config_file)
        assert config.project_name == "TestProject"
        assert config.agents.reviewer.quality_threshold == 85.0
        assert config.agents.reviewer.model == "custom-model:7b"
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
                    "performance": 0.5
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
    
    def test_get_default_config(self):
        """Test that get_default_config returns a dictionary"""
        config_dict = get_default_config()
        assert isinstance(config_dict, dict)
        assert "agents" in config_dict
        assert "scoring" in config_dict
        assert "mal" in config_dict


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
                    "model": "qwen2.5-coder:7b",
                    "quality_threshold": 75.0,
                    "include_scoring": True,
                    "include_llm_feedback": True,
                    "max_file_size": 2097152
                }
            },
            "scoring": {
                "weights": {
                    "complexity": 0.15,
                    "security": 0.35,
                    "maintainability": 0.25,
                    "test_coverage": 0.15,
                    "performance": 0.10
                },
                "quality_threshold": 75.0
            },
            "mal": {
                "ollama_url": "http://localhost:11434",
                "default_model": "qwen2.5-coder:7b",
                "timeout": 120.0
            }
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        config = load_config(config_file)
        
        # Verify all values loaded correctly
        assert config.project_name == "MyProject"
        assert config.version == "1.0.0"
        assert config.agents.reviewer.model == "qwen2.5-coder:7b"
        assert config.agents.reviewer.quality_threshold == 75.0
        assert config.agents.reviewer.max_file_size == 2097152
        assert config.scoring.weights.security == 0.35
        assert config.scoring.quality_threshold == 75.0
        assert config.mal.timeout == 120.0

