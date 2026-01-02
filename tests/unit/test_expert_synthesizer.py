"""
Tests for Expert Synthesizer.
"""

from pathlib import Path

import pytest
import yaml

from tapps_agents.experts.expert_config import load_expert_configs
from tapps_agents.experts.expert_synthesizer import ExpertSynthesizer


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    return tmp_path


@pytest.mark.unit
def test_expert_synthesizer_initialization(temp_project):
    """Test Expert Synthesizer initialization."""
    synthesizer = ExpertSynthesizer(project_root=temp_project)
    assert synthesizer.project_root == temp_project
    assert synthesizer.experts_file == temp_project / ".tapps-agents" / "experts.yaml"
    assert synthesizer.domains_file == temp_project / ".tapps-agents" / "domains.md"
    assert synthesizer.knowledge_base == temp_project / ".tapps-agents" / "knowledge"


@pytest.mark.unit
def test_synthesize_from_domains(temp_project):
    """Test synthesizing experts from domains list."""
    domains = ["python", "django", "react"]
    
    synthesizer = ExpertSynthesizer(project_root=temp_project)
    synthesizer.synthesize_from_domains(domains)

    # Verify domains.md was created
    assert synthesizer.domains_file.exists()
    domains_content = synthesizer.domains_file.read_text(encoding="utf-8")
    assert "python" in domains_content
    assert "django" in domains_content
    assert "react" in domains_content

    # Verify experts.yaml was created
    assert synthesizer.experts_file.exists()
    experts = load_expert_configs(synthesizer.experts_file)
    assert len(experts) > 0
    
    # Verify expert IDs were created
    expert_ids = [expert.expert_id for expert in experts]
    assert "expert-python" in expert_ids or any("python" in eid for eid in expert_ids)


@pytest.mark.unit
def test_synthesize_from_domains_creates_knowledge_skeletons(temp_project):
    """Test that knowledge skeletons are created for each domain."""
    domains = ["python", "django"]
    
    synthesizer = ExpertSynthesizer(project_root=temp_project)
    synthesizer.synthesize_from_domains(domains)

    # Verify knowledge skeletons were created for each domain
    for domain in domains:
        knowledge_dir = synthesizer.knowledge_base / domain
        assert knowledge_dir.exists()
        assert (knowledge_dir / "overview.md").exists()
        assert (knowledge_dir / "glossary.md").exists()
        assert (knowledge_dir / "decisions.md").exists()
        assert (knowledge_dir / "pitfalls.md").exists()
        assert (knowledge_dir / "constraints.md").exists()


@pytest.mark.unit
def test_synthesize_from_domains_with_existing_files(temp_project):
    """Test that existing knowledge files are not overwritten."""
    domains = ["python"]
    
    synthesizer = ExpertSynthesizer(project_root=temp_project)
    
    # Create existing knowledge file
    knowledge_dir = synthesizer.knowledge_base / "python"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    existing_file = knowledge_dir / "overview.md"
    existing_content = "# Existing Overview\n\nThis is existing content."
    existing_file.write_text(existing_content, encoding="utf-8")
    
    synthesizer.synthesize_from_domains(domains)
    
    # Verify existing file was not overwritten
    assert existing_file.exists()
    assert existing_file.read_text(encoding="utf-8") == existing_content

