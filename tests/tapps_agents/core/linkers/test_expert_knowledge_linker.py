"""Tests for ExpertKnowledgeLinker.

Comprehensive test suite with ≥90% coverage target.
"""

import json
from pathlib import Path

import pytest
import yaml

from tapps_agents.core.linkers.expert_knowledge_linker import (
    ExpertKnowledgeLinker,
    LinkingResult,
    OrphanFile,
)


@pytest.fixture
def temp_project(tmp_path):
    """Create temporary project structure."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()

    # Create .tapps-agents structure
    tapps_dir = project_root / ".tapps-agents"
    tapps_dir.mkdir()

    kb_dir = tapps_dir / "knowledge"
    kb_dir.mkdir()

    return project_root


@pytest.fixture
def linker(temp_project):
    """Create ExpertKnowledgeLinker instance."""
    return ExpertKnowledgeLinker(temp_project)


class TestInitialization:
    """Test ExpertKnowledgeLinker initialization."""

    def test_init_default_paths(self, temp_project):
        """Test initialization with default paths."""
        linker = ExpertKnowledgeLinker(temp_project)

        assert linker.project_root == temp_project
        assert linker.knowledge_base_dir == temp_project / ".tapps-agents" / "knowledge"
        assert linker.experts_file == temp_project / ".tapps-agents" / "experts.yaml"
        assert linker.experts == {}
        assert linker.linked_files == set()

    def test_init_custom_paths(self, temp_project):
        """Test initialization with custom paths."""
        custom_kb = temp_project / "custom_kb"
        custom_experts = temp_project / "custom_experts.yaml"

        linker = ExpertKnowledgeLinker(
            temp_project,
            knowledge_base_dir=custom_kb,
            experts_file=custom_experts,
        )

        assert linker.knowledge_base_dir == custom_kb
        assert linker.experts_file == custom_experts


class TestLoadExperts:
    """Test expert loading."""

    def test_load_experts_success(self, linker, temp_project):
        """Test loading valid experts file."""
        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_data = {
            "experts": [
                {
                    "expert_id": "expert-testing-pytest",
                    "expert_name": "Pytest Testing Expert",
                    "primary_domain": "testing",
                    "knowledge_files": [".tapps-agents/knowledge/testing/pytest-guide.md"],
                },
                {
                    "expert_id": "expert-api-design",
                    "expert_name": "API Design Expert",
                    "primary_domain": "api-design",
                    "knowledge_files": [],
                },
            ]
        }
        with open(experts_file, 'w') as f:
            yaml.safe_dump(experts_data, f)

        experts = linker.load_experts()

        assert len(experts) == 2
        assert "expert-testing-pytest" in experts
        assert "expert-api-design" in experts
        assert experts["expert-testing-pytest"]["expert_name"] == "Pytest Testing Expert"

    def test_load_experts_file_not_found(self, linker):
        """Test loading when experts file doesn't exist."""
        with pytest.raises(FileNotFoundError, match="Experts file not found"):
            linker.load_experts()

    def test_load_experts_invalid_yaml(self, linker, temp_project):
        """Test loading invalid YAML."""
        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_file.write_text("invalid: yaml: syntax:")

        with pytest.raises(ValueError, match="Invalid YAML"):
            linker.load_experts()

    def test_load_experts_not_a_list(self, linker, temp_project):
        """Test loading when experts is not a list."""
        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_file.write_text("experts: not_a_list")

        with pytest.raises(ValueError, match="'experts' must be a list"):
            linker.load_experts()

    def test_load_experts_missing_expert_id(self, linker, temp_project):
        """Test loading experts without expert_id."""
        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_data = {
            "experts": [
                {"expert_name": "No ID Expert"}  # Missing expert_id
            ]
        }
        with open(experts_file, 'w') as f:
            yaml.safe_dump(experts_data, f)

        experts = linker.load_experts()
        assert len(experts) == 0  # Skipped because no expert_id


class TestGetLinkedKnowledgeFiles:
    """Test getting linked knowledge files."""

    def test_get_linked_files_success(self, linker, temp_project):
        """Test getting linked files from experts."""
        # Create knowledge file
        kb_dir = temp_project / ".tapps-agents" / "knowledge" / "testing"
        kb_dir.mkdir(parents=True)
        kf = kb_dir / "pytest-guide.md"
        kf.write_text("# Pytest Guide")

        # Create experts file
        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_data = {
            "experts": [
                {
                    "expert_id": "expert-testing",
                    "knowledge_files": [".tapps-agents/knowledge/testing/pytest-guide.md"],
                }
            ]
        }
        with open(experts_file, 'w') as f:
            yaml.safe_dump(experts_data, f)

        linker.load_experts()
        linked = linker.get_linked_knowledge_files()

        assert len(linked) == 1
        assert kf.resolve() in linked

    def test_get_linked_files_no_experts(self, linker, temp_project):
        """Test getting linked files when no experts loaded."""
        linked = linker.get_linked_knowledge_files()
        assert len(linked) == 0

    def test_get_linked_files_invalid_paths(self, linker, temp_project):
        """Test handling invalid knowledge file paths."""
        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_data = {
            "experts": [
                {
                    "expert_id": "expert-test",
                    "knowledge_files": [
                        "nonexistent/file.md",
                        123,  # Invalid type
                        None,  # Invalid
                    ],
                }
            ]
        }
        with open(experts_file, 'w') as f:
            yaml.safe_dump(experts_data, f)

        linker.load_experts()
        linked = linker.get_linked_knowledge_files()

        assert len(linked) == 0  # All invalid paths skipped


class TestScanKnowledgeBase:
    """Test knowledge base scanning."""

    def test_scan_knowledge_base_success(self, linker, temp_project):
        """Test scanning knowledge base directory."""
        kb_dir = temp_project / ".tapps-agents" / "knowledge"

        # Create knowledge files
        (kb_dir / "testing").mkdir()
        (kb_dir / "testing" / "pytest.md").write_text("# Pytest")
        (kb_dir / "testing" / "unittest.md").write_text("# Unittest")

        (kb_dir / "api").mkdir()
        (kb_dir / "api" / "rest.md").write_text("# REST")

        # Create README (should be excluded)
        (kb_dir / "README.md").write_text("# README")

        files = linker.scan_knowledge_base()

        assert len(files) == 3
        filenames = [f.name for f in files]
        assert "pytest.md" in filenames
        assert "unittest.md" in filenames
        assert "rest.md" in filenames
        assert "README.md" not in filenames

    def test_scan_knowledge_base_missing_dir(self, linker, temp_project):
        """Test scanning when knowledge base directory doesn't exist."""
        # Remove knowledge base directory
        kb_dir = temp_project / ".tapps-agents" / "knowledge"
        if kb_dir.exists():
            import shutil
            shutil.rmtree(kb_dir)

        files = linker.scan_knowledge_base()
        assert len(files) == 0


class TestExtractDomainTopic:
    """Test domain and topic extraction."""

    def test_extract_domain_topic_success(self, linker, temp_project):
        """Test extracting domain and topic from path."""
        kb_dir = temp_project / ".tapps-agents" / "knowledge"
        filepath = kb_dir / "testing" / "pytest-guide.md"

        domain, topic = linker._extract_domain_topic(filepath)

        assert domain == "testing"
        assert topic == "pytest-guide"

    def test_extract_domain_topic_root_level(self, linker, temp_project):
        """Test extracting from root-level file."""
        kb_dir = temp_project / ".tapps-agents" / "knowledge"
        filepath = kb_dir / "guide.md"

        domain, topic = linker._extract_domain_topic(filepath)

        assert domain is None
        assert topic == "guide"

    def test_extract_domain_topic_invalid_path(self, linker, temp_project):
        """Test extracting from path outside knowledge base."""
        filepath = temp_project / "other" / "file.md"

        domain, topic = linker._extract_domain_topic(filepath)

        assert domain is None
        assert topic is None


class TestSuggestExpertsForFile:
    """Test expert suggestion for knowledge files."""

    def test_suggest_experts_domain_match(self, linker, temp_project):
        """Test suggesting experts by domain match."""
        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_data = {
            "experts": [
                {
                    "expert_id": "expert-testing-pytest",
                    "expert_name": "Pytest Expert",
                    "primary_domain": "testing",
                },
                {
                    "expert_id": "expert-api-design",
                    "expert_name": "API Expert",
                    "primary_domain": "api-design",
                },
            ]
        }
        with open(experts_file, 'w') as f:
            yaml.safe_dump(experts_data, f)

        linker.load_experts()

        kb_file = temp_project / ".tapps-agents" / "knowledge" / "testing" / "unittest.md"
        suggestions = linker._suggest_experts_for_file(kb_file, "testing", "unittest")

        assert "expert-testing-pytest" in suggestions
        assert "expert-api-design" not in suggestions

    def test_suggest_experts_topic_match(self, linker, temp_project):
        """Test suggesting experts by topic match."""
        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_data = {
            "experts": [
                {
                    "expert_id": "expert-pytest",
                    "expert_name": "Pytest Testing Expert",
                    "primary_domain": "testing",
                },
            ]
        }
        with open(experts_file, 'w') as f:
            yaml.safe_dump(experts_data, f)

        linker.load_experts()

        kb_file = temp_project / ".tapps-agents" / "knowledge" / "tools" / "pytest.md"
        suggestions = linker._suggest_experts_for_file(kb_file, "tools", "pytest")

        assert "expert-pytest" in suggestions

    def test_suggest_experts_no_match(self, linker, temp_project):
        """Test suggesting when no experts match."""
        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_data = {
            "experts": [
                {
                    "expert_id": "expert-api",
                    "expert_name": "API Expert",
                    "primary_domain": "api",
                },
            ]
        }
        with open(experts_file, 'w') as f:
            yaml.safe_dump(experts_data, f)

        linker.load_experts()

        kb_file = temp_project / ".tapps-agents" / "knowledge" / "testing" / "pytest.md"
        suggestions = linker._suggest_experts_for_file(kb_file, "testing", "pytest")

        assert len(suggestions) == 0


class TestFindOrphanFiles:
    """Test orphan file detection."""

    def test_find_orphans_success(self, linker, temp_project):
        """Test finding orphan knowledge files."""
        # Create knowledge files
        kb_dir = temp_project / ".tapps-agents" / "knowledge" / "testing"
        kb_dir.mkdir(parents=True)
        linked_file = kb_dir / "pytest.md"
        linked_file.write_text("# Pytest")
        orphan_file = kb_dir / "unittest.md"
        orphan_file.write_text("# Unittest")

        # Create experts file (only links pytest.md)
        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_data = {
            "experts": [
                {
                    "expert_id": "expert-testing",
                    "primary_domain": "testing",
                    "knowledge_files": [".tapps-agents/knowledge/testing/pytest.md"],
                }
            ]
        }
        with open(experts_file, 'w') as f:
            yaml.safe_dump(experts_data, f)

        linker.load_experts()
        orphans = linker.find_orphan_files()

        assert len(orphans) == 1
        assert orphans[0].filepath == orphan_file.resolve()
        assert orphans[0].domain == "testing"
        assert orphans[0].topic == "unittest"

    def test_find_orphans_all_linked(self, linker, temp_project):
        """Test when all knowledge files are linked."""
        kb_dir = temp_project / ".tapps-agents" / "knowledge" / "testing"
        kb_dir.mkdir(parents=True)
        kf = kb_dir / "pytest.md"
        kf.write_text("# Pytest")

        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_data = {
            "experts": [
                {
                    "expert_id": "expert-testing",
                    "knowledge_files": [".tapps-agents/knowledge/testing/pytest.md"],
                }
            ]
        }
        with open(experts_file, 'w') as f:
            yaml.safe_dump(experts_data, f)

        linker.load_experts()
        orphans = linker.find_orphan_files()

        assert len(orphans) == 0


class TestSuggestKnowledgeFileAdditions:
    """Test suggesting knowledge_files additions."""

    def test_suggest_additions_success(self, linker, temp_project):
        """Test suggesting knowledge_files additions to experts."""
        # Create orphan knowledge file
        kb_dir = temp_project / ".tapps-agents" / "knowledge" / "testing"
        kb_dir.mkdir(parents=True)
        orphan = kb_dir / "pytest-advanced.md"
        orphan.write_text("# Pytest Advanced")

        # Create experts
        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_data = {
            "experts": [
                {
                    "expert_id": "expert-testing-pytest",
                    "expert_name": "Pytest Expert",
                    "primary_domain": "testing",
                    "knowledge_files": [],
                }
            ]
        }
        with open(experts_file, 'w') as f:
            yaml.safe_dump(experts_data, f)

        linker.load_experts()
        suggestions = linker.suggest_knowledge_file_additions()

        assert "expert-testing-pytest" in suggestions
        assert len(suggestions["expert-testing-pytest"]) == 1
        assert "pytest-advanced.md" in suggestions["expert-testing-pytest"][0]

    def test_suggest_additions_no_orphans(self, linker, temp_project):
        """Test suggestions when no orphans exist."""
        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_data = {"experts": []}
        with open(experts_file, 'w') as f:
            yaml.safe_dump(experts_data, f)

        linker.load_experts()
        suggestions = linker.suggest_knowledge_file_additions()

        assert len(suggestions) == 0


class TestAnalyze:
    """Test complete analysis."""

    def test_analyze_success(self, linker, temp_project):
        """Test successful analysis."""
        # Create knowledge files
        kb_dir = temp_project / ".tapps-agents" / "knowledge" / "testing"
        kb_dir.mkdir(parents=True)
        (kb_dir / "pytest.md").write_text("# Pytest")
        (kb_dir / "unittest.md").write_text("# Unittest")

        # Create experts
        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_data = {
            "experts": [
                {
                    "expert_id": "expert-testing",
                    "primary_domain": "testing",
                    "knowledge_files": [".tapps-agents/knowledge/testing/pytest.md"],
                }
            ]
        }
        with open(experts_file, 'w') as f:
            yaml.safe_dump(experts_data, f)

        result = linker.analyze()

        assert result.success is True
        assert result.total_knowledge_files == 2
        assert result.linked_files == 1
        assert len(result.orphan_files) == 1
        assert result.experts_analyzed == 1
        assert "expert-testing" in result.suggestions

    def test_analyze_error(self, linker, temp_project):
        """Test analysis with error."""
        # No experts file exists
        result = linker.analyze()

        assert result.success is False
        assert result.error is not None
        assert "not found" in result.error.lower()


class TestDataClasses:
    """Test data classes."""

    def test_orphan_file_creation(self):
        """Test OrphanFile dataclass."""
        orphan = OrphanFile(
            filepath=Path("/path/to/file.md"),
            domain="testing",
            topic="pytest",
            suggested_experts=["expert-testing"],
            reason="Not linked"
        )

        assert orphan.filepath == Path("/path/to/file.md")
        assert orphan.domain == "testing"
        assert orphan.suggested_experts == ["expert-testing"]

    def test_linking_result_creation(self):
        """Test LinkingResult dataclass."""
        result = LinkingResult(
            total_knowledge_files=10,
            linked_files=8,
            orphan_files=[],
            experts_analyzed=5,
            success=True,
        )

        assert result.total_knowledge_files == 10
        assert result.linked_files == 8
        assert result.success is True


class TestCLI:
    """Test CLI interface."""

    def test_main_help(self):
        """Test CLI help command."""
        from tapps_agents.core.linkers.expert_knowledge_linker import main
        import sys

        # This test just ensures main() is defined
        assert callable(main)
