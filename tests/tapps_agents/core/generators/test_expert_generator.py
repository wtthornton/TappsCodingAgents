"""Tests for ExpertGenerator module.

Module: Phase 3.1 - Expert Generator Tests
Target Coverage: ≥90%
"""

import pytest
import tempfile
from pathlib import Path
import yaml

from tapps_agents.core.generators.expert_generator import (
    ExpertGenerator,
    KnowledgeFileAnalysis,
    ExpertConfig,
)

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


@pytest.fixture
def temp_project():
    """Create temporary project directory with knowledge base."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create directory structure
        kb_dir = project_root / ".tapps-agents" / "knowledge"
        kb_dir.mkdir(parents=True, exist_ok=True)

        # Create test knowledge files
        testing_dir = kb_dir / "testing"
        testing_dir.mkdir()
        test_file = testing_dir / "pytest-guide.md"
        test_file.write_text("""# Pytest Testing Guide

This guide covers pytest testing best practices.

## Test Organization
- Organize tests by feature
- Use fixtures for setup

## Assertions
- Use descriptive assertion messages
""")

        # Create quality knowledge file
        quality_dir = kb_dir / "quality"
        quality_dir.mkdir()
        quality_file = quality_dir / "code-quality.md"
        quality_file.write_text("""# Code Quality Standards

**Source:** Internal standards

## Key Concepts
- Maintainability
- Readability
- Performance
""")

        yield project_root


@pytest.fixture
def generator(temp_project):
    """Create ExpertGenerator instance."""
    return ExpertGenerator(project_root=temp_project)


class TestDataClasses:
    """Test dataclasses."""

    def test_knowledge_file_analysis_creation(self):
        """Test KnowledgeFileAnalysis dataclass."""
        analysis = KnowledgeFileAnalysis(
            filepath=Path("test.md"),
            domain="testing",
            topic="pytest",
            description="Pytest guide",
            consultation_triggers=["pytest", "testing"],
            priority=0.85,
            concepts=["fixtures", "assertions"],
        )
        assert analysis.domain == "testing"
        assert analysis.topic == "pytest"
        assert len(analysis.consultation_triggers) == 2
        assert analysis.priority == 0.85

    def test_expert_config_creation(self):
        """Test ExpertConfig dataclass."""
        config = ExpertConfig(
            expert_id="expert-testing-pytest",
            expert_name="Testing - Pytest Expert",
            primary_domain="testing",
            rag_enabled=True,
            fine_tuned=False,
            knowledge_files=["knowledge/testing/pytest-guide.md"],
            consultation_triggers=["pytest", "testing"],
            priority=0.85,
        )
        assert config.expert_id == "expert-testing-pytest"
        assert config.primary_domain == "testing"
        assert config.rag_enabled is True


class TestInitialization:
    """Test ExpertGenerator initialization."""

    def test_init_default_paths(self):
        """Test initialization with default paths."""
        generator = ExpertGenerator()
        assert generator.project_root == Path.cwd()
        assert generator.knowledge_base_dir == Path.cwd() / ".tapps-agents" / "knowledge"

    def test_init_custom_paths(self, temp_project):
        """Test initialization with custom paths."""
        kb_dir = temp_project / "custom_kb"
        experts_yaml = temp_project / "custom_experts.yaml"

        generator = ExpertGenerator(
            project_root=temp_project,
            knowledge_base_dir=kb_dir,
            experts_yaml_path=experts_yaml,
        )

        assert generator.project_root == temp_project
        assert generator.knowledge_base_dir == kb_dir
        assert generator.experts_yaml_path == experts_yaml


class TestAnalyzeKnowledgeFile:
    """Test analyze_knowledge_file method."""

    def test_analyze_file_basic(self, generator, temp_project):
        """Test basic file analysis."""
        kb_dir = temp_project / ".tapps-agents" / "knowledge"
        test_file = kb_dir / "testing" / "pytest-guide.md"

        analysis = generator.analyze_knowledge_file(test_file)

        assert analysis.filepath == test_file
        assert analysis.domain == "testing"
        assert analysis.topic == "pytest-guide"
        assert "Pytest" in analysis.description or "pytest" in analysis.description.lower()
        assert len(analysis.consultation_triggers) > 0
        assert 0.70 <= analysis.priority <= 0.90

    def test_analyze_file_with_quality_domain(self, generator, temp_project):
        """Test analysis with high-priority domain."""
        kb_dir = temp_project / ".tapps-agents" / "knowledge"
        quality_file = kb_dir / "quality" / "code-quality.md"

        analysis = generator.analyze_knowledge_file(quality_file)

        assert analysis.domain == "quality"
        assert analysis.topic == "code-quality"
        # Quality is a high-priority domain, should have higher priority
        assert analysis.priority >= 0.80

    def test_analyze_nonexistent_file(self, generator, temp_project):
        """Test analysis with nonexistent file."""
        fake_file = temp_project / "nonexistent.md"

        with pytest.raises(ValueError, match="Failed to read"):
            generator.analyze_knowledge_file(fake_file)


class TestCheckExpertExists:
    """Test check_expert_exists method."""

    def test_check_expert_no_yaml(self, generator):
        """Test checking when experts.yaml doesn't exist."""
        result = generator.check_expert_exists("testing")
        assert result is None

    def test_check_expert_exists_exact_match(self, generator, temp_project):
        """Test checking with exact domain match."""
        # Create experts.yaml with existing expert
        experts_yaml = temp_project / ".tapps-agents" / "experts.yaml"
        experts_data = {
            "experts": [
                {
                    "expert_id": "expert-testing",
                    "expert_name": "Testing Expert",
                    "primary_domain": "testing",
                    "rag_enabled": True,
                }
            ]
        }
        experts_yaml.write_text(yaml.dump(experts_data))

        result = generator.check_expert_exists("testing")

        assert result is not None
        assert result["expert_id"] == "expert-testing"
        assert result["primary_domain"] == "testing"

    def test_check_expert_exists_id_match(self, generator, temp_project):
        """Test checking with expert_id containing domain."""
        experts_yaml = temp_project / ".tapps-agents" / "experts.yaml"
        experts_data = {
            "experts": [
                {
                    "expert_id": "expert-api-design",
                    "expert_name": "API Expert",
                    "primary_domain": "api-design-integration",
                }
            ]
        }
        experts_yaml.write_text(yaml.dump(experts_data))

        result = generator.check_expert_exists("api")

        assert result is not None
        assert "api" in result["expert_id"]

    def test_check_expert_not_exists(self, generator, temp_project):
        """Test checking when expert doesn't exist."""
        experts_yaml = temp_project / ".tapps-agents" / "experts.yaml"
        experts_data = {"experts": []}
        experts_yaml.write_text(yaml.dump(experts_data))

        result = generator.check_expert_exists("nonexistent")
        assert result is None


class TestGenerateExpertConfig:
    """Test generate_expert_config method."""

    def test_generate_config_basic(self, generator, temp_project):
        """Test basic config generation."""
        kb_dir = temp_project / ".tapps-agents" / "knowledge"
        test_file = kb_dir / "testing" / "pytest-guide.md"

        analysis = KnowledgeFileAnalysis(
            filepath=test_file,
            domain="testing",
            topic="pytest",
            description="Pytest testing guide",
            consultation_triggers=["pytest", "testing", "fixtures"],
            priority=0.85,
        )

        config = generator.generate_expert_config(analysis)

        assert config.expert_id == "expert-testing-pytest"
        assert "Testing" in config.expert_name
        assert "Pytest" in config.expert_name
        assert config.primary_domain == "testing"
        assert config.rag_enabled is True
        assert config.fine_tuned is False
        assert len(config.knowledge_files) == 1
        assert config.consultation_triggers == ["pytest", "testing", "fixtures"]
        assert config.priority == 0.85

    def test_generate_config_with_hyphens(self, generator, temp_project):
        """Test config generation with hyphenated names."""
        kb_dir = temp_project / ".tapps-agents" / "knowledge"
        test_file = kb_dir / "api-design" / "rest-api.md"
        test_file.parent.mkdir()
        test_file.write_text("# REST API Guide")

        analysis = KnowledgeFileAnalysis(
            filepath=test_file,
            domain="api-design",
            topic="rest-api",
            description="REST API design guide",
        )

        config = generator.generate_expert_config(analysis)

        assert config.expert_id == "expert-api-design-rest-api"
        assert "Api Design" in config.expert_name
        assert "Rest Api" in config.expert_name


class TestAddExpertToYaml:
    """Test add_expert_to_yaml method."""

    def test_add_expert_new_file(self, generator, temp_project):
        """Test adding expert to new experts.yaml file."""
        config = ExpertConfig(
            expert_id="expert-testing-pytest",
            expert_name="Testing - Pytest Expert",
            primary_domain="testing",
            knowledge_files=["knowledge/testing/pytest-guide.md"],
            consultation_triggers=["pytest", "testing"],
        )

        success = generator.add_expert_to_yaml(config, confirm=False, auto_mode=True)

        assert success is True
        assert generator.experts_yaml_path.exists()

        # Verify content
        with open(generator.experts_yaml_path, "r") as f:
            data = yaml.safe_load(f)

        assert "experts" in data
        assert len(data["experts"]) == 1
        expert = data["experts"][0]
        assert expert["expert_id"] == "expert-testing-pytest"
        assert expert["primary_domain"] == "testing"

    def test_add_expert_existing_file(self, generator, temp_project):
        """Test adding expert to existing experts.yaml."""
        # Create existing experts.yaml
        experts_yaml = temp_project / ".tapps-agents" / "experts.yaml"
        existing_data = {
            "experts": [
                {"expert_id": "expert-quality", "expert_name": "Quality Expert", "primary_domain": "quality"}
            ]
        }
        experts_yaml.write_text(yaml.dump(existing_data))

        config = ExpertConfig(
            expert_id="expert-testing",
            expert_name="Testing Expert",
            primary_domain="testing",
        )

        success = generator.add_expert_to_yaml(config, confirm=False, auto_mode=True)

        assert success is True

        # Verify both experts exist
        with open(experts_yaml, "r") as f:
            data = yaml.safe_load(f)

        assert len(data["experts"]) == 2
        expert_ids = [e["expert_id"] for e in data["experts"]]
        assert "expert-quality" in expert_ids
        assert "expert-testing" in expert_ids

    def test_add_expert_duplicate(self, generator, temp_project):
        """Test adding duplicate expert."""
        config = ExpertConfig(
            expert_id="expert-testing",
            expert_name="Testing Expert",
            primary_domain="testing",
        )

        # Add first time
        success1 = generator.add_expert_to_yaml(config, confirm=False, auto_mode=True)
        assert success1 is True

        # Try to add again
        success2 = generator.add_expert_to_yaml(config, confirm=False, auto_mode=True)
        assert success2 is False  # Should return False for duplicate


class TestScanAndGenerate:
    """Test scan_and_generate method."""

    def test_scan_missing_kb_dir(self, temp_project):
        """Test scanning when knowledge base doesn't exist."""
        generator = ExpertGenerator(
            project_root=temp_project,
            knowledge_base_dir=temp_project / "nonexistent",
        )

        result = generator.scan_and_generate(auto_mode=True)

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_scan_and_generate_auto(self, generator):
        """Test automatic scanning and generation."""
        result = generator.scan_and_generate(auto_mode=True, skip_existing=False)

        assert result["success"] is True
        assert result["total_files"] == 2  # pytest-guide.md, code-quality.md
        assert result["generated"] >= 0
        assert "generated_experts" in result

    def test_scan_skip_existing(self, generator, temp_project):
        """Test scanning with skip_existing=True."""
        # Pre-create expert for testing domain
        experts_yaml = temp_project / ".tapps-agents" / "experts.yaml"
        existing_data = {
            "experts": [
                {"expert_id": "expert-testing", "expert_name": "Testing Expert", "primary_domain": "testing"}
            ]
        }
        experts_yaml.write_text(yaml.dump(existing_data))

        result = generator.scan_and_generate(auto_mode=True, skip_existing=True)

        assert result["success"] is True
        # Should have skipped testing domain
        assert result["skipped"] >= 1


class TestHelperMethods:
    """Test private helper methods."""

    def test_extract_description_from_heading(self, generator):
        """Test description extraction from heading."""
        content = """# Pytest Testing Guide

Some content here.
"""
        desc = generator._extract_description(content)
        assert "Pytest" in desc

    def test_extract_description_from_paragraph(self, generator):
        """Test description extraction from paragraph."""
        content = """
This is the first paragraph with description.

More content.
"""
        desc = generator._extract_description(content)
        assert "first paragraph" in desc

    def test_extract_triggers(self, generator):
        """Test trigger extraction."""
        content = """# Testing Guide

## Pytest Fixtures
## Test Organization
"""
        triggers = generator._extract_triggers(content, "testing", "pytest")

        assert "testing" in triggers
        assert "pytest" in triggers
        assert len(triggers) <= 10

    def test_extract_concepts(self, generator):
        """Test concept extraction."""
        content = """# Guide

## Test Organization
## Assertions
## Fixtures
"""
        concepts = generator._extract_concepts(content)

        assert len(concepts) <= 10
        assert any("Organization" in c or "Assertions" in c or "Fixtures" in c for c in concepts)

    def test_calculate_priority_short_file(self, generator):
        """Test priority calculation for short file."""
        content = "Short content" * 10  # < 500 words
        priority = generator._calculate_priority(content, "general")

        assert 0.70 <= priority <= 0.90

    def test_calculate_priority_long_file(self, generator):
        """Test priority calculation for long file."""
        content = "Long content " * 1000  # > 1000 words
        priority = generator._calculate_priority(content, "general")

        assert priority >= 0.80

    def test_calculate_priority_high_priority_domain(self, generator):
        """Test priority calculation for high-priority domain."""
        content = "Content"
        priority = generator._calculate_priority(content, "testing")

        assert priority >= 0.85


class TestEdgeCases:
    """Test edge cases."""

    def test_check_expert_invalid_yaml(self, generator, temp_project):
        """Test checking expert with invalid YAML file."""
        experts_yaml = temp_project / ".tapps-agents" / "experts.yaml"
        experts_yaml.write_text("invalid: yaml: syntax:")

        result = generator.check_expert_exists("testing")
        assert result is None

    def test_add_expert_to_yaml_invalid_existing(self, generator, temp_project):
        """Test adding expert when existing YAML is invalid."""
        experts_yaml = temp_project / ".tapps-agents" / "experts.yaml"
        experts_yaml.write_text("invalid: yaml: syntax:")

        config = ExpertConfig(
            expert_id="expert-testing",
            expert_name="Testing Expert",
            primary_domain="testing",
        )

        with pytest.raises(ValueError, match="Failed to load"):
            generator.add_expert_to_yaml(config, confirm=False, auto_mode=True)

    def test_scan_and_generate_with_error(self, generator, temp_project):
        """Test scan_and_generate with file that causes error."""
        # Create a file in an invalid location
        kb_dir = temp_project / ".tapps-agents" / "knowledge"
        broken_dir = kb_dir / "broken"
        broken_dir.mkdir()
        broken_file = broken_dir / "test.md"
        broken_file.write_text("# Test")

        # Make file unreadable by deleting it after adding to glob results
        import os
        os.chmod(str(broken_file), 0o000)

        try:
            result = generator.scan_and_generate(auto_mode=True, skip_existing=False)
            # Should complete but may have errors
            assert result["success"] is True
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(str(broken_file), 0o644)
            except:
                pass

    def test_extract_description_fallback(self, generator):
        """Test description extraction fallback to default."""
        content = ""  # Empty content
        desc = generator._extract_description(content)
        assert desc == "Knowledge base content"

    def test_extract_triggers_filters_common_words(self, generator):
        """Test that extract_triggers filters common words."""
        content = """# The Testing Guide

## For Testing and with Examples
"""
        triggers = generator._extract_triggers(content, "testing", "guide")

        # Common words like "the", "and", "for", "with" should be filtered
        assert "the" not in triggers
        assert "and" not in triggers
        assert "for" not in triggers
        assert "with" not in triggers


class TestCLIIntegration:
    """Test CLI entry point."""

    def test_main_help(self):
        """Test CLI help command."""
        from tapps_agents.core.generators.expert_generator import main
        import sys

        old_argv = sys.argv
        try:
            sys.argv = ["expert_generator", "--help"]

            with pytest.raises(SystemExit) as exc:
                main()

            assert exc.value.code == 0
        finally:
            sys.argv = old_argv
