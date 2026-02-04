"""
Unit tests for ExpertConfigGenerator
"""

from pathlib import Path

import pytest
import yaml

from tapps_agents.core.expert_config_generator import (
    ExpertConfig,
    ExpertConfigGenerator,
)
from tapps_agents.experts.domain_detector import DomainMapping


@pytest.fixture
def sample_project_root(tmp_path: Path) -> Path:
    """Create a sample project with .tapps-agents directory."""
    config_dir = tmp_path / ".tapps-agents"
    config_dir.mkdir()
    return tmp_path


@pytest.fixture
def sample_domains():
    """Create sample domain mappings."""
    return [
        DomainMapping(
            domain="python",
            confidence=0.9,
            signals=[],
            reasoning="Detected via dependency signals"
        ),
        DomainMapping(
            domain="api-design-integration",
            confidence=0.8,
            signals=[],
            reasoning="Detected via framework signals"
        ),
        DomainMapping(
            domain="low-confidence",
            confidence=0.2,  # Below threshold
            signals=[],
            reasoning="Low confidence domain"
        ),
    ]


class TestExpertConfigGenerator:
    """Test cases for ExpertConfigGenerator"""

    def test_init(self, sample_project_root):
        """Test generator initialization."""
        generator = ExpertConfigGenerator(project_root=sample_project_root)
        assert generator.project_root == sample_project_root.resolve()
        assert generator.config_dir == sample_project_root / ".tapps-agents"
        assert generator.experts_yaml == generator.config_dir / "experts.yaml"

    def test_generate_expert_configs(self, sample_project_root, sample_domains):
        """Test expert config generation."""
        generator = ExpertConfigGenerator(project_root=sample_project_root)
        configs = generator.generate_expert_configs(sample_domains)
        
        assert len(configs) == 2  # Low confidence domain should be skipped
        assert any(c.expert_id == "expert-python" for c in configs)
        assert any(c.expert_id == "expert-api-design-integration" for c in configs)
        assert not any(c.expert_id == "expert-low-confidence" for c in configs)

    def test_generate_expert_configs_skips_low_confidence(self, sample_project_root, sample_domains):
        """Test that low confidence domains are skipped."""
        generator = ExpertConfigGenerator(project_root=sample_project_root)
        configs = generator.generate_expert_configs(sample_domains)
        
        # Should skip domain with confidence < 0.3
        expert_ids = [c.expert_id for c in configs]
        assert "expert-low-confidence" not in expert_ids

    def test_generate_expert_configs_skips_existing(self, sample_project_root, sample_domains):
        """Test that existing experts are skipped."""
        # Create existing experts.yaml
        experts_yaml = sample_project_root / ".tapps-agents" / "experts.yaml"
        experts_yaml.write_text(yaml.dump({
            "experts": [
                {
                    "expert_id": "expert-python",
                    "expert_name": "Python Expert",
                    "primary_domain": "python",
                    "rag_enabled": True,
                }
            ]
        }))
        
        generator = ExpertConfigGenerator(project_root=sample_project_root)
        configs = generator.generate_expert_configs(sample_domains)
        
        # Should skip existing expert-python
        expert_ids = [c.expert_id for c in configs]
        assert "expert-python" not in expert_ids
        assert "expert-api-design-integration" in expert_ids

    def test_write_expert_configs_new(self, sample_project_root, sample_domains):
        """Test writing new expert configs."""
        generator = ExpertConfigGenerator(project_root=sample_project_root)
        configs = generator.generate_expert_configs(sample_domains)
        
        generator.write_expert_configs(configs, merge=False)
        
        # Verify file was created
        experts_yaml = sample_project_root / ".tapps-agents" / "experts.yaml"
        assert experts_yaml.exists()
        
        # Verify content
        with open(experts_yaml, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            assert "experts" in data
            assert len(data["experts"]) == 2
            expert_ids = [e["expert_id"] for e in data["experts"]]
            assert "expert-python" in expert_ids
            assert "expert-api-design-integration" in expert_ids

    def test_write_expert_configs_merge(self, sample_project_root, sample_domains):
        """Test merging with existing configs."""
        # Create existing experts.yaml
        experts_yaml = sample_project_root / ".tapps-agents" / "experts.yaml"
        experts_yaml.write_text(yaml.dump({
            "experts": [
                {
                    "expert_id": "expert-existing",
                    "expert_name": "Existing Expert",
                    "primary_domain": "existing",
                    "rag_enabled": True,
                }
            ]
        }))
        
        generator = ExpertConfigGenerator(project_root=sample_project_root)
        configs = generator.generate_expert_configs(sample_domains)
        
        generator.write_expert_configs(configs, merge=True)
        
        # Verify merged content
        with open(experts_yaml, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            expert_ids = [e["expert_id"] for e in data["experts"]]
            assert "expert-existing" in expert_ids  # Existing preserved
            assert "expert-api-design-integration" in expert_ids  # New added

    def test_validate_config_valid(self, sample_project_root):
        """Test validation of valid config."""
        generator = ExpertConfigGenerator(project_root=sample_project_root)
        config = ExpertConfig(
            expert_id="expert-python",
            expert_name="Python Expert",
            primary_domain="python",
            rag_enabled=True,
        )
        assert generator.validate_config(config) is True

    def test_validate_config_missing_fields(self, sample_project_root):
        """Test validation of config with missing fields."""
        generator = ExpertConfigGenerator(project_root=sample_project_root)
        
        # Missing expert_id
        config = ExpertConfig(
            expert_id="",
            expert_name="Python Expert",
            primary_domain="python",
        )
        assert generator.validate_config(config) is False
        
        # Missing expert_name
        config = ExpertConfig(
            expert_id="expert-python",
            expert_name="",
            primary_domain="python",
        )
        assert generator.validate_config(config) is False
        
        # Missing primary_domain
        config = ExpertConfig(
            expert_id="expert-python",
            expert_name="Python Expert",
            primary_domain="",
        )
        assert generator.validate_config(config) is False

    def test_generate_expert_name(self, sample_project_root):
        """Test expert name generation."""
        generator = ExpertConfigGenerator(project_root=sample_project_root)
        
        name1 = generator._generate_expert_name("python")
        assert name1 == "Python Expert"
        
        name2 = generator._generate_expert_name("api-design-integration")
        assert name2 == "Api Design Integration Expert"
        
        name3 = generator._generate_expert_name("user_experience")
        assert name3 == "User Experience Expert"

    def test_write_expert_configs_creates_directory(self, tmp_path, sample_domains):
        """Test that write_expert_configs creates .tapps-agents directory if needed."""
        generator = ExpertConfigGenerator(project_root=tmp_path)
        configs = generator.generate_expert_configs(sample_domains)
        
        generator.write_expert_configs(configs, merge=False)
        
        # Verify directory and file were created
        assert (tmp_path / ".tapps-agents").exists()
        assert (tmp_path / ".tapps-agents" / "experts.yaml").exists()
