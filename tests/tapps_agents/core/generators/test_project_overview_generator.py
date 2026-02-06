"""Comprehensive tests for ProjectOverviewGenerator module.

Tests cover:
- Data class validation (ProjectMetadata, ArchitecturePattern, ComponentMap)
- Initialization and path validation
- Metadata extraction from pyproject.toml and package.json
- Architecture pattern detection
- Component map generation with Mermaid diagrams
- Overview generation
- Incremental update functionality
- Error handling and edge cases
- Integration tests
- Performance tests

Target: ≥90% coverage
"""

import json
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tapps_agents.core.generators.project_overview_generator import (
    ArchitecturePattern,
    ArchitectureType,
    ComponentMap,
    ProjectMetadata,
    ProjectOverviewGenerator,
)


# ============================================================================
# Data Class Tests
# ============================================================================


@pytest.mark.unit
class TestProjectMetadataDataClass:
    """Test ProjectMetadata data class."""

    def test_metadata_creation_with_all_fields(self):
        """Test ProjectMetadata creation with all fields."""
        metadata = ProjectMetadata(
            name="test-project",
            version="1.0.0",
            description="A test project",
            authors=["Author One", "Author Two"],
            license="MIT",
            dependencies={"requests": ">=2.0", "pytest": ">=7.0"},
            python_version=">=3.10",
        )
        assert metadata.name == "test-project"
        assert metadata.version == "1.0.0"
        assert metadata.description == "A test project"
        assert len(metadata.authors) == 2
        assert metadata.license == "MIT"
        assert len(metadata.dependencies) == 2
        assert metadata.python_version == ">=3.10"

    def test_metadata_creation_minimal(self):
        """Test ProjectMetadata with only required fields."""
        metadata = ProjectMetadata(
            name="minimal-project",
            version="0.1.0",
        )
        assert metadata.name == "minimal-project"
        assert metadata.version == "0.1.0"
        assert metadata.description == ""
        assert metadata.authors == []
        assert metadata.license == ""
        assert metadata.dependencies == {}
        assert metadata.python_version == ""

    def test_metadata_to_dict(self):
        """Test ProjectMetadata to_dict method."""
        metadata = ProjectMetadata(
            name="test",
            version="1.0.0",
            description="desc",
            authors=["author"],
            license="MIT",
            dependencies={"pkg": "1.0"},
            python_version="3.10",
        )
        result = metadata.to_dict()

        assert result["name"] == "test"
        assert result["version"] == "1.0.0"
        assert result["description"] == "desc"
        assert result["authors"] == ["author"]
        assert result["license"] == "MIT"
        assert result["dependencies"] == {"pkg": "1.0"}
        assert result["python_version"] == "3.10"


@pytest.mark.unit
class TestArchitecturePatternDataClass:
    """Test ArchitecturePattern data class validation."""

    def test_pattern_valid_confidence(self):
        """Test ArchitecturePattern with valid confidence score."""
        pattern = ArchitecturePattern(
            pattern=ArchitectureType.MVC,
            confidence=0.85,
            indicators=["models", "views", "controllers"],
        )
        assert pattern.confidence == 0.85
        assert pattern.pattern == ArchitectureType.MVC
        assert len(pattern.indicators) == 3

    def test_pattern_invalid_confidence_too_high(self):
        """Test ArchitecturePattern rejects confidence > 1.0."""
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            ArchitecturePattern(
                pattern=ArchitectureType.CLEAN,
                confidence=1.5,
            )

    def test_pattern_invalid_confidence_too_low(self):
        """Test ArchitecturePattern rejects confidence < 0.0."""
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            ArchitecturePattern(
                pattern=ArchitectureType.LAYERED,
                confidence=-0.1,
            )

    def test_pattern_confidence_boundary_values(self):
        """Test ArchitecturePattern accepts boundary confidence values."""
        # Test 0.0
        pattern_min = ArchitecturePattern(
            pattern=ArchitectureType.UNKNOWN,
            confidence=0.0,
        )
        assert pattern_min.confidence == 0.0

        # Test 1.0
        pattern_max = ArchitecturePattern(
            pattern=ArchitectureType.CQRS,
            confidence=1.0,
        )
        assert pattern_max.confidence == 1.0

    def test_all_architecture_types(self):
        """Test all ArchitectureType enum values."""
        expected_types = [
            "layered", "mvc", "clean", "hexagonal",
            "microservices", "monolith", "cqrs", "event-driven", "unknown"
        ]
        actual_types = [t.value for t in ArchitectureType]
        assert set(actual_types) == set(expected_types)


@pytest.mark.unit
class TestComponentMapDataClass:
    """Test ComponentMap data class."""

    def test_component_map_creation(self):
        """Test ComponentMap creation with all fields."""
        component_map = ComponentMap(
            components=["api", "core", "utils"],
            dependencies={"api": ["core"], "core": ["utils"]},
            mermaid_diagram="graph TD\n    api --> core\n    core --> utils",
        )
        assert len(component_map.components) == 3
        assert "api" in component_map.dependencies
        assert component_map.mermaid_diagram.startswith("graph TD")

    def test_component_map_defaults(self):
        """Test ComponentMap with default values."""
        component_map = ComponentMap()
        assert component_map.components == []
        assert component_map.dependencies == {}
        assert component_map.mermaid_diagram == ""


# ============================================================================
# ProjectOverviewGenerator Initialization Tests
# ============================================================================


@pytest.mark.unit
class TestProjectOverviewGeneratorInit:
    """Test ProjectOverviewGenerator initialization."""

    def test_init_with_defaults(self, tmp_path):
        """Test initialization with default output file."""
        generator = ProjectOverviewGenerator(tmp_path)
        assert generator.project_root == tmp_path
        assert generator.output_file == tmp_path / "PROJECT_OVERVIEW.md"

    def test_init_with_custom_output(self, tmp_path):
        """Test initialization with custom output file."""
        output_file = tmp_path / "custom_overview.md"
        generator = ProjectOverviewGenerator(tmp_path, output_file=output_file)
        assert generator.output_file == output_file

    def test_init_invalid_project_root(self, tmp_path):
        """Test initialization with non-existent project root."""
        non_existent = tmp_path / "does_not_exist"
        with pytest.raises(ValueError, match="Project root does not exist"):
            ProjectOverviewGenerator(non_existent)

    def test_init_resolves_path(self, tmp_path):
        """Test that project root path is resolved."""
        generator = ProjectOverviewGenerator(tmp_path)
        assert generator.project_root.is_absolute()


# ============================================================================
# Metadata Extraction Tests
# ============================================================================


@pytest.mark.unit
class TestExtractProjectMetadataPyproject:
    """Test metadata extraction from pyproject.toml."""

    def test_extract_from_pyproject_project_section(self, tmp_path):
        """Test extraction from [project] section."""
        pyproject_content = """
[project]
name = "test-project"
version = "1.2.3"
description = "A test project description"
authors = [
    {name = "Author One", email = "one@test.com"},
    {name = "Author Two", email = "two@test.com"}
]
license = {text = "MIT"}
requires-python = ">=3.10"

[project.dependencies]
requests = ">=2.28.0"
click = ">=8.0.0"
"""
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text(pyproject_content)

        generator = ProjectOverviewGenerator(tmp_path)
        metadata = generator.extract_project_metadata()

        assert metadata.name == "test-project"
        assert metadata.version == "1.2.3"
        assert metadata.description == "A test project description"
        assert metadata.python_version == ">=3.10"

    def test_extract_from_pyproject_poetry_section(self, tmp_path):
        """Test extraction from [tool.poetry] section."""
        pyproject_content = """
[tool.poetry]
name = "poetry-project"
version = "2.0.0"
description = "A poetry managed project"
authors = ["Poet One <poet@test.com>"]
license = "Apache-2.0"

[tool.poetry.dependencies]
python = "^3.10"
pydantic = "^2.0"
"""
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text(pyproject_content)

        generator = ProjectOverviewGenerator(tmp_path)
        metadata = generator.extract_project_metadata()

        assert metadata.name == "poetry-project"
        assert metadata.version == "2.0.0"
        assert metadata.description == "A poetry managed project"
        assert metadata.license == "Apache-2.0"

    def test_extract_pyproject_project_takes_precedence(self, tmp_path):
        """Test [project] takes precedence over [tool.poetry]."""
        pyproject_content = """
[project]
name = "project-name"
version = "1.0.0"

[tool.poetry]
name = "poetry-name"
version = "2.0.0"
"""
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text(pyproject_content)

        generator = ProjectOverviewGenerator(tmp_path)
        metadata = generator.extract_project_metadata()

        assert metadata.name == "project-name"
        assert metadata.version == "1.0.0"

    def test_extract_pyproject_minimal(self, tmp_path):
        """Test extraction with minimal pyproject.toml."""
        pyproject_content = """
[project]
name = "minimal"
version = "0.1.0"
"""
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text(pyproject_content)

        generator = ProjectOverviewGenerator(tmp_path)
        metadata = generator.extract_project_metadata()

        assert metadata.name == "minimal"
        assert metadata.version == "0.1.0"
        assert metadata.description == ""

    def test_extract_pyproject_invalid_format(self, tmp_path):
        """Test extraction with invalid pyproject.toml."""
        pyproject_content = "this is not valid toml {"
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text(pyproject_content)

        generator = ProjectOverviewGenerator(tmp_path)
        with pytest.raises(ValueError, match="Invalid pyproject.toml"):
            generator.extract_project_metadata()


@pytest.mark.unit
class TestExtractProjectMetadataPackageJson:
    """Test metadata extraction from package.json."""

    def test_extract_from_package_json_full(self, tmp_path):
        """Test extraction from complete package.json."""
        package_json = {
            "name": "node-project",
            "version": "3.0.0",
            "description": "A Node.js project",
            "author": "Node Author",
            "contributors": ["Contrib One", "Contrib Two"],
            "license": "ISC",
            "dependencies": {
                "express": "^4.18.0",
                "lodash": "^4.17.0"
            }
        }
        package_path = tmp_path / "package.json"
        package_path.write_text(json.dumps(package_json))

        generator = ProjectOverviewGenerator(tmp_path)
        metadata = generator.extract_project_metadata()

        assert metadata.name == "node-project"
        assert metadata.version == "3.0.0"
        assert metadata.description == "A Node.js project"
        assert len(metadata.authors) == 3  # author + 2 contributors
        assert metadata.license == "ISC"
        assert "express" in metadata.dependencies

    def test_extract_from_package_json_minimal(self, tmp_path):
        """Test extraction from minimal package.json."""
        package_json = {
            "name": "minimal-node",
            "version": "0.0.1"
        }
        package_path = tmp_path / "package.json"
        package_path.write_text(json.dumps(package_json))

        generator = ProjectOverviewGenerator(tmp_path)
        metadata = generator.extract_project_metadata()

        assert metadata.name == "minimal-node"
        assert metadata.version == "0.0.1"

    def test_extract_package_json_invalid(self, tmp_path):
        """Test extraction with invalid package.json."""
        package_path = tmp_path / "package.json"
        package_path.write_text("not valid json {")

        generator = ProjectOverviewGenerator(tmp_path)
        with pytest.raises(ValueError, match="Invalid package.json"):
            generator.extract_project_metadata()

    def test_pyproject_preferred_over_package_json(self, tmp_path):
        """Test pyproject.toml is preferred over package.json."""
        pyproject_content = """
[project]
name = "python-project"
version = "1.0.0"
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)
        (tmp_path / "package.json").write_text('{"name": "node-project", "version": "2.0.0"}')

        generator = ProjectOverviewGenerator(tmp_path)
        metadata = generator.extract_project_metadata()

        assert metadata.name == "python-project"

    def test_no_config_file_found(self, tmp_path):
        """Test error when no config file exists."""
        generator = ProjectOverviewGenerator(tmp_path)
        with pytest.raises(FileNotFoundError, match="Neither pyproject.toml nor package.json"):
            generator.extract_project_metadata()


# ============================================================================
# Architecture Pattern Detection Tests
# ============================================================================


@pytest.mark.unit
class TestDetectArchitecturePatterns:
    """Test architecture pattern detection."""

    def test_detect_mvc_pattern(self, tmp_path):
        """Test MVC pattern detection."""
        (tmp_path / "models").mkdir()
        (tmp_path / "views").mkdir()
        (tmp_path / "controllers").mkdir()

        generator = ProjectOverviewGenerator(tmp_path)
        patterns = generator.detect_architecture_patterns()

        mvc_pattern = next((p for p in patterns if p.pattern == ArchitectureType.MVC), None)
        assert mvc_pattern is not None
        assert mvc_pattern.confidence == 1.0
        assert "models" in mvc_pattern.indicators

    def test_detect_layered_pattern(self, tmp_path):
        """Test layered architecture detection."""
        (tmp_path / "presentation").mkdir()
        (tmp_path / "business").mkdir()
        (tmp_path / "data").mkdir()

        generator = ProjectOverviewGenerator(tmp_path)
        patterns = generator.detect_architecture_patterns()

        layered_pattern = next((p for p in patterns if p.pattern == ArchitectureType.LAYERED), None)
        assert layered_pattern is not None
        assert layered_pattern.confidence == 0.6  # 3/5 indicators

    def test_detect_clean_pattern(self, tmp_path):
        """Test clean architecture detection."""
        (tmp_path / "domain").mkdir()
        (tmp_path / "application").mkdir()
        (tmp_path / "infrastructure").mkdir()
        (tmp_path / "interfaces").mkdir()

        generator = ProjectOverviewGenerator(tmp_path)
        patterns = generator.detect_architecture_patterns()

        clean_pattern = next((p for p in patterns if p.pattern == ArchitectureType.CLEAN), None)
        assert clean_pattern is not None
        assert clean_pattern.confidence == 1.0

    def test_detect_microservices_pattern(self, tmp_path):
        """Test microservices pattern detection."""
        (tmp_path / "services").mkdir()
        (tmp_path / "api-gateway").mkdir()
        (tmp_path / "user-service").mkdir()
        (tmp_path / "order-service").mkdir()

        generator = ProjectOverviewGenerator(tmp_path)
        patterns = generator.detect_architecture_patterns()

        micro_pattern = next((p for p in patterns if p.pattern == ArchitectureType.MICROSERVICES), None)
        assert micro_pattern is not None

    def test_detect_cqrs_pattern(self, tmp_path):
        """Test CQRS pattern detection."""
        (tmp_path / "commands").mkdir()
        (tmp_path / "queries").mkdir()

        generator = ProjectOverviewGenerator(tmp_path)
        patterns = generator.detect_architecture_patterns()

        cqrs_pattern = next((p for p in patterns if p.pattern == ArchitectureType.CQRS), None)
        assert cqrs_pattern is not None
        assert cqrs_pattern.confidence == 1.0

    def test_detect_unknown_pattern(self, tmp_path):
        """Test unknown pattern when no indicators match."""
        (tmp_path / "random").mkdir()
        (tmp_path / "stuff").mkdir()

        generator = ProjectOverviewGenerator(tmp_path)
        patterns = generator.detect_architecture_patterns()

        assert len(patterns) == 1
        assert patterns[0].pattern == ArchitectureType.UNKNOWN
        assert patterns[0].confidence == 1.0

    def test_patterns_sorted_by_confidence(self, tmp_path):
        """Test patterns are sorted by confidence (highest first)."""
        # Create partial matches for multiple patterns
        (tmp_path / "models").mkdir()  # MVC partial
        (tmp_path / "domain").mkdir()  # Clean/Layered partial

        generator = ProjectOverviewGenerator(tmp_path)
        patterns = generator.detect_architecture_patterns()

        # Verify sorting
        for i in range(len(patterns) - 1):
            assert patterns[i].confidence >= patterns[i + 1].confidence

    def test_ignores_hidden_directories(self, tmp_path):
        """Test that hidden directories are ignored."""
        (tmp_path / ".git").mkdir()
        (tmp_path / ".vscode").mkdir()
        (tmp_path / "models").mkdir()

        generator = ProjectOverviewGenerator(tmp_path)
        patterns = generator.detect_architecture_patterns()

        # Should only detect MVC partial, not include hidden dirs
        all_indicators = []
        for p in patterns:
            all_indicators.extend(p.indicators)

        assert ".git" not in all_indicators
        assert ".vscode" not in all_indicators


# ============================================================================
# Component Map Generation Tests
# ============================================================================


@pytest.mark.unit
class TestGenerateComponentMap:
    """Test component map generation."""

    def test_generate_component_map_basic(self, tmp_path):
        """Test basic component map generation."""
        (tmp_path / "api").mkdir()
        (tmp_path / "core").mkdir()
        (tmp_path / "utils").mkdir()

        generator = ProjectOverviewGenerator(tmp_path)
        component_map = generator.generate_component_map()

        assert len(component_map.components) == 3
        assert "api" in component_map.components
        assert "core" in component_map.components
        assert "utils" in component_map.components

    def test_generate_mermaid_diagram(self, tmp_path):
        """Test Mermaid diagram generation."""
        (tmp_path / "frontend").mkdir()
        (tmp_path / "backend").mkdir()

        generator = ProjectOverviewGenerator(tmp_path)
        component_map = generator.generate_component_map()

        assert component_map.mermaid_diagram.startswith("graph TD")
        assert "frontend" in component_map.mermaid_diagram
        assert "backend" in component_map.mermaid_diagram

    def test_mermaid_sanitizes_names(self, tmp_path):
        """Test Mermaid diagram sanitizes component names."""
        (tmp_path / "my-component").mkdir()
        (tmp_path / "another_component").mkdir()

        generator = ProjectOverviewGenerator(tmp_path)
        component_map = generator.generate_component_map()

        # Hyphens should be replaced with underscores in Mermaid
        assert "my_component" in component_map.mermaid_diagram

    def test_ignores_hidden_and_underscore_dirs(self, tmp_path):
        """Test that hidden and underscore-prefixed directories are ignored."""
        (tmp_path / ".hidden").mkdir()
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "_private").mkdir()
        (tmp_path / "public").mkdir()

        generator = ProjectOverviewGenerator(tmp_path)
        component_map = generator.generate_component_map()

        assert ".hidden" not in component_map.components
        assert "__pycache__" not in component_map.components
        assert "_private" not in component_map.components
        assert "public" in component_map.components

    def test_empty_project(self, tmp_path):
        """Test component map for empty project."""
        generator = ProjectOverviewGenerator(tmp_path)
        component_map = generator.generate_component_map()

        assert component_map.components == []
        assert component_map.mermaid_diagram == "graph TD"


# ============================================================================
# Overview Generation Tests
# ============================================================================


@pytest.mark.unit
class TestGenerateOverview:
    """Test overview generation."""

    def test_generate_overview_complete(self, tmp_path):
        """Test complete overview generation."""
        # Setup project structure
        pyproject_content = """
[project]
name = "test-app"
version = "1.0.0"
description = "A test application"
authors = ["Test Author"]
license = {text = "MIT"}
requires-python = ">=3.10"

[project.dependencies]
requests = ">=2.0"
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)
        (tmp_path / "models").mkdir()
        (tmp_path / "views").mkdir()
        (tmp_path / "controllers").mkdir()
        (tmp_path / "utils").mkdir()

        generator = ProjectOverviewGenerator(tmp_path)
        overview = generator.generate_overview()

        # Check sections exist
        assert "# test-app" in overview
        assert "**Version:** 1.0.0" in overview
        assert "## Description" in overview
        assert "A test application" in overview
        assert "## Authors" in overview
        assert "Test Author" in overview
        assert "**License:** MIT" in overview
        assert "## Architecture" in overview
        assert "**Primary Pattern:** Mvc" in overview
        assert "## Components" in overview
        assert "```mermaid" in overview
        assert "## Dependencies" in overview
        assert "---" in overview
        assert "*Generated:" in overview

    def test_generate_overview_minimal(self, tmp_path):
        """Test overview generation with minimal project."""
        pyproject_content = """
[project]
name = "minimal"
version = "0.1.0"
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        generator = ProjectOverviewGenerator(tmp_path)
        overview = generator.generate_overview()

        assert "# minimal" in overview
        assert "**Version:** 0.1.0" in overview

    def test_generate_overview_multiple_patterns(self, tmp_path):
        """Test overview with multiple detected patterns."""
        pyproject_content = """
[project]
name = "multi-pattern"
version = "1.0.0"
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)
        (tmp_path / "domain").mkdir()
        (tmp_path / "application").mkdir()
        (tmp_path / "models").mkdir()

        generator = ProjectOverviewGenerator(tmp_path)
        overview = generator.generate_overview()

        assert "**Other Patterns Detected:**" in overview


# ============================================================================
# Update Overview Tests
# ============================================================================


@pytest.mark.unit
class TestUpdateOverview:
    """Test incremental overview updates."""

    def test_update_creates_new_file(self, tmp_path):
        """Test update creates overview file if it doesn't exist."""
        pyproject_content = """
[project]
name = "new-project"
version = "1.0.0"
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        generator = ProjectOverviewGenerator(tmp_path)
        result = generator.update_overview()

        assert result is True
        assert generator.output_file.exists()
        content = generator.output_file.read_text()
        assert "# new-project" in content

    def test_update_skips_if_up_to_date(self, tmp_path):
        """Test update skips if file is up-to-date."""
        pyproject_content = """
[project]
name = "existing-project"
version = "1.0.0"
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        generator = ProjectOverviewGenerator(tmp_path)

        # First update
        generator.update_overview()

        # Wait a moment and update again
        time.sleep(0.1)
        result = generator.update_overview()

        # Should skip since config hasn't changed
        assert result is False

    def test_update_force(self, tmp_path):
        """Test force update."""
        pyproject_content = """
[project]
name = "force-project"
version = "1.0.0"
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        generator = ProjectOverviewGenerator(tmp_path)
        generator.update_overview()

        # Force update
        result = generator.update_overview(force=True)
        assert result is True

    def test_update_when_config_changes(self, tmp_path):
        """Test update detects config file changes."""
        pyproject_content = """
[project]
name = "changing-project"
version = "1.0.0"
"""
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text(pyproject_content)

        generator = ProjectOverviewGenerator(tmp_path)
        generator.update_overview()

        # Modify pyproject.toml
        time.sleep(0.1)
        pyproject_content_v2 = """
[project]
name = "changing-project"
version = "2.0.0"
"""
        pyproject_path.write_text(pyproject_content_v2)

        # Update should detect change
        result = generator.update_overview()
        assert result is True

        content = generator.output_file.read_text()
        assert "**Version:** 2.0.0" in content


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling scenarios."""

    def test_extract_metadata_handles_empty_pyproject(self, tmp_path):
        """Test handling of empty pyproject.toml."""
        (tmp_path / "pyproject.toml").write_text("")

        generator = ProjectOverviewGenerator(tmp_path)
        metadata = generator.extract_project_metadata()

        # Should use defaults for missing data
        assert metadata.name == "unknown"
        assert metadata.version == "0.0.0"

    def test_generate_overview_handles_extraction_failure(self, tmp_path):
        """Test overview generation fails gracefully on extraction error."""
        generator = ProjectOverviewGenerator(tmp_path)

        with pytest.raises(FileNotFoundError):
            generator.generate_overview()

    def test_update_overview_returns_false_on_error(self, tmp_path):
        """Test update_overview returns False on error."""
        generator = ProjectOverviewGenerator(tmp_path)

        # No config files, should return False (not raise)
        result = generator.update_overview()
        assert result is False


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.integration
class TestProjectOverviewGeneratorIntegration:
    """Integration tests for complete workflow."""

    def test_full_workflow_python_project(self, tmp_path):
        """Test full workflow for a Python project."""
        # Setup realistic Python project structure
        pyproject_content = """
[project]
name = "my-python-app"
version = "2.5.0"
description = "A comprehensive Python application"
authors = ["Dev Team <team@example.com>"]
license = {text = "MIT"}
requires-python = ">=3.10"

[project.dependencies]
fastapi = ">=0.100.0"
pydantic = ">=2.0.0"
sqlalchemy = ">=2.0.0"
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        # Create typical project structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "api").mkdir(parents=True)
        (tmp_path / "src" / "core").mkdir()
        (tmp_path / "src" / "models").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "docs").mkdir()

        generator = ProjectOverviewGenerator(tmp_path)

        # Run full workflow
        metadata = generator.extract_project_metadata()
        patterns = generator.detect_architecture_patterns()
        component_map = generator.generate_component_map()
        overview = generator.generate_overview()
        updated = generator.update_overview()

        # Verify results
        assert metadata.name == "my-python-app"
        assert len(patterns) >= 1
        assert len(component_map.components) >= 3
        assert len(overview) > 100
        assert updated is True
        assert generator.output_file.exists()

    def test_full_workflow_node_project(self, tmp_path):
        """Test full workflow for a Node.js project."""
        package_json = {
            "name": "my-node-app",
            "version": "1.0.0",
            "description": "A Node.js application",
            "author": "Node Developer",
            "license": "ISC",
            "dependencies": {
                "express": "^4.18.0",
                "mongoose": "^7.0.0"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package_json, indent=2))

        # Create typical Node.js structure
        (tmp_path / "src").mkdir()
        (tmp_path / "routes").mkdir()
        (tmp_path / "controllers").mkdir()
        (tmp_path / "models").mkdir()
        (tmp_path / "middleware").mkdir()

        generator = ProjectOverviewGenerator(tmp_path)
        updated = generator.update_overview()

        assert updated is True
        content = generator.output_file.read_text()
        assert "my-node-app" in content
        assert "express" in content


# ============================================================================
# Performance Tests
# ============================================================================


@pytest.mark.performance
class TestProjectOverviewGeneratorPerformance:
    """Performance tests for ProjectOverviewGenerator."""

    def test_large_project_structure(self, tmp_path):
        """Test performance with many directories."""
        pyproject_content = """
[project]
name = "large-project"
version = "1.0.0"
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        # Create 100 directories
        for i in range(100):
            (tmp_path / f"component_{i}").mkdir()

        generator = ProjectOverviewGenerator(tmp_path)

        start_time = time.time()
        component_map = generator.generate_component_map()
        elapsed = time.time() - start_time

        assert len(component_map.components) == 100
        assert elapsed < 2.0  # Should complete in under 2 seconds

    def test_overview_generation_performance(self, tmp_path):
        """Test overview generation performance."""
        pyproject_content = """
[project]
name = "perf-test"
version = "1.0.0"
description = "Performance test project"

[project.dependencies]
"""
        # Add many dependencies
        deps = "\n".join([f'dep{i} = ">=1.0.0"' for i in range(50)])
        pyproject_content += deps

        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        # Create structure
        for i in range(20):
            (tmp_path / f"module_{i}").mkdir()

        generator = ProjectOverviewGenerator(tmp_path)

        start_time = time.time()
        overview = generator.generate_overview()
        elapsed = time.time() - start_time

        assert len(overview) > 500
        assert elapsed < 3.0  # Should complete in under 3 seconds
