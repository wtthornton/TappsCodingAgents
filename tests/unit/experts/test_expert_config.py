"""
Tests for Expert Configuration System.
"""

import shutil
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from tapps_agents.experts.expert_config import (
    ExpertConfigModel,
    ExpertsConfig,
    load_expert_configs,
)


class TestExpertConfigModel:
    """Test ExpertConfigModel Pydantic model."""

    def test_valid_config(self):
        """Test valid expert configuration."""
        config = ExpertConfigModel(
            expert_id="expert-test",
            expert_name="Test Expert",
            primary_domain="test-domain",
        )

        assert config.expert_id == "expert-test"
        assert config.expert_name == "Test Expert"
        assert config.primary_domain == "test-domain"
        assert config.rag_enabled is False  # Default
        assert config.fine_tuned is False  # Default

    def test_config_with_rag(self):
        """Test configuration with RAG enabled."""
        config = ExpertConfigModel(
            expert_id="expert-test",
            expert_name="Test Expert",
            primary_domain="test-domain",
            rag_enabled=True,
        )

        assert config.rag_enabled is True

    def test_missing_required_fields(self):
        """Test that missing required fields raise errors."""
        # Validate that ValidationError is raised with message mentioning missing field
        with pytest.raises(ValidationError) as exc_info:
            ExpertConfigModel(
                expert_name="Test Expert",
                primary_domain="test-domain",
                # Missing expert_id
            )
        # Verify error message mentions the missing field
        error_str = str(exc_info.value)
        assert "expert_id" in error_str or "expert_id" in error_str.lower()

    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden."""
        # Validate that ValidationError is raised with message mentioning extra field
        with pytest.raises(ValidationError) as exc_info:
            ExpertConfigModel(
                expert_id="expert-test",
                expert_name="Test Expert",
                primary_domain="test-domain",
                unknown_field="value",  # Extra field
            )
        # Verify error message mentions the extra field (Pydantic usually includes field names)
        error_str = str(exc_info.value)
        assert "unknown_field" in error_str or "extra" in error_str.lower()


class TestExpertsConfig:
    """Test ExpertsConfig container."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_load_valid_yaml(self, temp_dir):
        """Test loading valid YAML configuration."""
        yaml_file = temp_dir / "experts.yaml"
        yaml_file.write_text(
            """experts:
  - expert_id: expert-test1
    expert_name: Test Expert 1
    primary_domain: domain-1
    rag_enabled: true
  
  - expert_id: expert-test2
    expert_name: Test Expert 2
    primary_domain: domain-2
    rag_enabled: false
""",
            encoding="utf-8",
        )

        config = ExpertsConfig.from_yaml(yaml_file)

        assert len(config.experts) == 2
        assert config.experts[0].expert_id == "expert-test1"
        assert config.experts[0].rag_enabled is True
        assert config.experts[1].expert_id == "expert-test2"
        assert config.experts[1].rag_enabled is False

    def test_load_missing_file(self, temp_dir):
        """Test loading non-existent file raises FileNotFoundError."""
        yaml_file = temp_dir / "nonexistent.yaml"

        # Validate specific error message: "Expert configuration file not found: {path}"
        with pytest.raises(FileNotFoundError, match="Expert configuration file not found: .*nonexistent.yaml"):
            ExpertsConfig.from_yaml(yaml_file)

    def test_load_invalid_yaml(self, temp_dir):
        """Test loading invalid YAML raises ValueError."""
        yaml_file = temp_dir / "experts.yaml"
        yaml_file.write_text("invalid: yaml: [ content", encoding="utf-8")

        with pytest.raises(ValueError, match="Invalid YAML"):
            ExpertsConfig.from_yaml(yaml_file)

    def test_load_missing_experts_key(self, temp_dir):
        """Test missing 'experts' key raises ValueError."""
        yaml_file = temp_dir / "experts.yaml"
        yaml_file.write_text("other_key: value", encoding="utf-8")

        with pytest.raises(ValueError, match="Missing 'experts' key"):
            ExpertsConfig.from_yaml(yaml_file)

    def test_load_experts_not_list(self, temp_dir):
        """Test 'experts' not being a list raises ValueError."""
        yaml_file = temp_dir / "experts.yaml"
        yaml_file.write_text("experts: not_a_list", encoding="utf-8")

        with pytest.raises(ValueError, match="Expected 'experts' to be a list"):
            ExpertsConfig.from_yaml(yaml_file)

    def test_load_invalid_expert_config(self, temp_dir):
        """Test invalid expert configuration raises ValueError."""
        yaml_file = temp_dir / "experts.yaml"
        yaml_file.write_text(
            """experts:
  - expert_name: Missing expert_id
    primary_domain: domain-1
""",
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="Invalid expert configuration"):
            ExpertsConfig.from_yaml(yaml_file)


class TestLoadExpertConfigs:
    """Test load_expert_configs convenience function."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_load_configs(self, temp_dir):
        """Test loading expert configs."""
        yaml_file = temp_dir / "experts.yaml"
        yaml_file.write_text(
            """experts:
  - expert_id: expert-test
    expert_name: Test Expert
    primary_domain: test-domain
""",
            encoding="utf-8",
        )

        configs = load_expert_configs(yaml_file)

        assert len(configs) == 1
        assert configs[0].expert_id == "expert-test"
        assert configs[0].expert_name == "Test Expert"
        assert configs[0].primary_domain == "test-domain"
