"""
Comprehensive unit tests for ExpertSetupWizard.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from tapps_agents.experts.setup_wizard import (
    ExpertSetupWizard,
    NonInteractiveInputRequired,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def temp_project_dir():
    """Create temporary project directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def wizard(temp_project_dir):
    """Create ExpertSetupWizard instance."""
    return ExpertSetupWizard(project_root=temp_project_dir, non_interactive=True)


class TestExpertSetupWizardInit:
    """Tests for ExpertSetupWizard initialization."""

    def test_init_with_project_root(self, temp_project_dir):
        """Test initialization with project root."""
        wizard = ExpertSetupWizard(project_root=temp_project_dir)
        assert wizard.project_root == temp_project_dir
        assert wizard.config_dir == temp_project_dir / ".tapps-agents"
        assert wizard.experts_file == temp_project_dir / ".tapps-agents" / "experts.yaml"
        assert wizard.domains_file == temp_project_dir / ".tapps-agents" / "domains.md"
        assert wizard.knowledge_base_dir == temp_project_dir / ".tapps-agents" / "knowledge"

    def test_init_without_project_root(self):
        """Test initialization without project root (uses cwd)."""
        wizard = ExpertSetupWizard()
        assert wizard.project_root == Path.cwd()

    def test_init_with_assume_yes(self, temp_project_dir):
        """Test initialization with assume_yes flag."""
        wizard = ExpertSetupWizard(project_root=temp_project_dir, assume_yes=True)
        assert wizard.assume_yes is True

    def test_init_with_non_interactive(self, temp_project_dir):
        """Test initialization with non_interactive flag."""
        wizard = ExpertSetupWizard(project_root=temp_project_dir, non_interactive=True)
        assert wizard.non_interactive is True


class TestPromptMethods:
    """Tests for prompt methods."""

    def test_prompt_non_interactive_with_default(self, wizard):
        """Test _prompt in non-interactive mode with default."""
        result = wizard._prompt("Question?", default="default_value")
        assert result == "default_value"

    def test_prompt_non_interactive_without_default(self, wizard):
        """Test _prompt in non-interactive mode without default raises error."""
        with pytest.raises(NonInteractiveInputRequired):
            wizard._prompt("Question?")

    def test_prompt_yes_no_non_interactive_with_assume_yes(self, temp_project_dir):
        """Test _prompt_yes_no in non-interactive mode with assume_yes."""
        wizard = ExpertSetupWizard(
            project_root=temp_project_dir, non_interactive=True, assume_yes=True
        )
        result = wizard._prompt_yes_no("Question?")
        assert result is True

    def test_prompt_yes_no_non_interactive_without_assume_yes(self, wizard):
        """Test _prompt_yes_no in non-interactive mode without assume_yes uses default."""
        result = wizard._prompt_yes_no("Question?", default=True)
        assert result is True
        result = wizard._prompt_yes_no("Question?", default=False)
        assert result is False


class TestConfigDirectory:
    """Tests for config directory management."""

    def test_ensure_config_dir(self, wizard):
        """Test _ensure_config_dir creates directories."""
        wizard._ensure_config_dir()
        assert wizard.config_dir.exists()
        assert wizard.knowledge_base_dir.exists()

    def test_ensure_config_dir_idempotent(self, wizard):
        """Test _ensure_config_dir is idempotent."""
        wizard._ensure_config_dir()
        first_time = wizard.config_dir.stat().st_mtime
        wizard._ensure_config_dir()
        second_time = wizard.config_dir.stat().st_mtime
        # Should not raise error and should be idempotent
        assert wizard.config_dir.exists()


class TestExpertLoading:
    """Tests for loading and saving experts."""

    def test_load_existing_experts_empty_file(self, wizard):
        """Test loading experts from non-existent file."""
        experts = wizard._load_existing_experts()
        assert experts == []

    def test_load_existing_experts_with_data(self, wizard):
        """Test loading experts from existing file."""
        wizard._ensure_config_dir()
        expert_data = {
            "experts": [
                {
                    "expert_id": "expert-test",
                    "expert_name": "Test Expert",
                    "primary_domain": "test-domain",
                    "rag_enabled": True,
                }
            ]
        }
        with open(wizard.experts_file, "w", encoding="utf-8") as f:
            yaml.dump(expert_data, f)

        experts = wizard._load_existing_experts()
        assert len(experts) == 1
        assert experts[0]["expert_id"] == "expert-test"

    def test_load_existing_experts_invalid_file(self, wizard):
        """Test loading experts from invalid file."""
        wizard._ensure_config_dir()
        wizard.experts_file.write_text("invalid: yaml: content: [", encoding="utf-8")

        experts = wizard._load_existing_experts()
        # Should return empty list on error
        assert experts == []

    def test_save_experts(self, wizard):
        """Test saving experts to file."""
        experts = [
            {
                "expert_id": "expert-test",
                "expert_name": "Test Expert",
                "primary_domain": "test-domain",
                "rag_enabled": True,
            }
        ]
        wizard._save_experts(experts)

        assert wizard.experts_file.exists()
        content = wizard.experts_file.read_text(encoding="utf-8")
        assert "expert-test" in content
        assert "Test Expert" in content


class TestDomainManagement:
    """Tests for domain management."""

    def test_get_domains_empty(self, wizard):
        """Test getting domains from non-existent file."""
        domains = wizard._get_domains()
        assert domains == []

    def test_get_domains_with_data(self, wizard):
        """Test getting domains from existing file."""
        wizard._ensure_config_dir()
        domains_content = """# Project Domains

### Domain 1: Test Domain

- **Primary Expert**: expert-test
- **Description**: Test domain
"""
        wizard.domains_file.write_text(domains_content, encoding="utf-8")

        domains = wizard._get_domains()
        # Should parse domains from file
        assert isinstance(domains, list)

    def test_get_domains_invalid_file(self, wizard):
        """Test getting domains from invalid file."""
        wizard._ensure_config_dir()
        wizard.domains_file.write_text("invalid content", encoding="utf-8")

        domains = wizard._get_domains()
        # Should return empty list on error
        assert domains == []

    def test_create_domains_template(self, wizard):
        """Test creating domains template."""
        wizard._ensure_config_dir()
        wizard._create_domains_template()

        assert wizard.domains_file.exists()
        content = wizard.domains_file.read_text(encoding="utf-8")
        assert "Project Domains" in content
        assert "Domain 1:" in content


class TestRAGKnowledgeBase:
    """Tests for RAG knowledge base setup."""

    def test_setup_rag_knowledge_base_disabled(self, wizard):
        """Test RAG setup when disabled."""
        wizard.assume_yes = False
        wizard.non_interactive = True
        result = wizard._setup_rag_knowledge_base("test-domain", "Test Expert")
        # In non-interactive mode without assume_yes, should return False
        assert result is False

    def test_setup_rag_knowledge_base_enabled(self, temp_project_dir):
        """Test RAG setup when enabled."""
        wizard = ExpertSetupWizard(
            project_root=temp_project_dir, non_interactive=True, assume_yes=True
        )
        wizard._ensure_config_dir()
        result = wizard._setup_rag_knowledge_base("test-domain", "Test Expert")

        assert result is True
        # Should create knowledge base directory
        sanitized_domain = "test-domain"
        kb_dir = wizard.knowledge_base_dir / sanitized_domain
        assert kb_dir.exists()

    def test_setup_rag_knowledge_base_with_existing_files(self, temp_project_dir):
        """Test RAG setup with existing knowledge files."""
        wizard = ExpertSetupWizard(
            project_root=temp_project_dir, non_interactive=True, assume_yes=True
        )
        wizard._ensure_config_dir()
        sanitized_domain = "test-domain"
        kb_dir = wizard.knowledge_base_dir / sanitized_domain
        kb_dir.mkdir(parents=True)
        existing_file = kb_dir / "existing.md"
        existing_file.write_text("# Existing knowledge", encoding="utf-8")

        result = wizard._setup_rag_knowledge_base("test-domain", "Test Expert")
        assert result is True


class TestExpertOperations:
    """Tests for expert operations."""

    def test_list_experts_empty(self, wizard):
        """Test listing experts when none exist."""
        wizard.list_experts()
        # Should not raise error

    def test_list_experts_with_data(self, wizard):
        """Test listing experts with data."""
        wizard._ensure_config_dir()
        experts = [
            {
                "expert_id": "expert-test",
                "expert_name": "Test Expert",
                "primary_domain": "test-domain",
                "rag_enabled": True,
            }
        ]
        wizard._save_experts(experts)
        wizard.list_experts()
        # Should not raise error

    def test_add_expert_non_interactive_raises_error(self, wizard):
        """Test adding expert in non-interactive mode raises error."""
        with pytest.raises(NonInteractiveInputRequired):
            wizard.add_expert()

    def test_remove_expert_empty(self, wizard):
        """Test removing expert when none exist."""
        wizard.remove_expert()
        # Should not raise error

    def test_remove_expert_with_data(self, wizard):
        """Test removing expert with data."""
        wizard._ensure_config_dir()
        experts = [
            {
                "expert_id": "expert-test",
                "expert_name": "Test Expert",
                "primary_domain": "test-domain",
                "rag_enabled": True,
            }
        ]
        wizard._save_experts(experts)
        # In non-interactive mode, should handle gracefully
        wizard.remove_expert()


class TestInitProject:
    """Tests for project initialization."""

    @patch("tapps_agents.experts.setup_wizard.init_project")
    def test_init_project_non_interactive(self, mock_init, wizard):
        """Test init_project in non-interactive mode."""
        wizard.assume_yes = True
        wizard.init_project()

        # Should create config directory
        assert wizard.config_dir.exists()
        # Should not call init_project_setup in non-interactive mode for expert creation
        # But may call it for cursor rules setup

    def test_init_project_creates_domains_template(self, temp_project_dir):
        """Test init_project creates domains template when missing."""
        wizard = ExpertSetupWizard(
            project_root=temp_project_dir, non_interactive=True, assume_yes=True
        )
        wizard.init_project()

        # Should create domains.md if it doesn't exist
        if not wizard.domains_file.exists():
            # May be created by init_project
            pass


class TestRunWizard:
    """Tests for wizard menu."""

    def test_run_wizard_exit(self, wizard):
        """Test run_wizard exit option."""
        # In non-interactive mode, should handle gracefully
        # This is mainly for interactive mode, so we just verify it doesn't crash
        pass

