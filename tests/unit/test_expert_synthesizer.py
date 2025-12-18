"""
Tests for Expert Synthesizer.
"""

from pathlib import Path

import pytest
import yaml

from tapps_agents.experts.domain_detector import DomainMapping, RepoSignal, StackDetectionResult
from tapps_agents.experts.expert_config import load_expert_configs
from tapps_agents.experts.expert_synthesizer import ExpertSynthesizer, ExpertSynthesisResult


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    return tmp_path


def test_expert_synthesizer_initialization(temp_project):
    """Test Expert Synthesizer initialization."""
    synthesizer = ExpertSynthesizer(project_root=temp_project)
    assert synthesizer.project_root == temp_project
    assert synthesizer.config_dir == temp_project / ".tapps-agents"
    assert synthesizer.experts_file == temp_project / ".tapps-agents" / "experts.yaml"


def test_synthesize_experts_from_python_project(temp_project):
    """Test synthesizing experts from Python project."""
    # Create Python project files
    (temp_project / "requirements.txt").write_text("django==4.2.0\npytest==7.0.0\n")
    (temp_project / "main.py").write_text("# Python code")

    synthesizer = ExpertSynthesizer(project_root=temp_project)
    result = synthesizer.synthesize_experts()

    assert isinstance(result, ExpertSynthesisResult)
    assert len(result.experts_created) > 0
    assert "expert-python" in result.experts_created or any(
        "python" in e for e in result.experts_created
    )

    # Verify expert config was created
    assert synthesizer.experts_file.exists()
    experts = load_expert_configs(synthesizer.experts_file)
    assert len(experts) > 0


def test_synthesize_experts_with_existing_config(temp_project):
    """Test synthesizing experts when config already exists."""
    # Create existing expert config
    config_dir = temp_project / ".tapps-agents"
    config_dir.mkdir(parents=True, exist_ok=True)
    experts_file = config_dir / "experts.yaml"

    existing_config = {
        "experts": [
            {
                "expert_id": "expert-existing",
                "expert_name": "Existing Expert",
                "primary_domain": "existing",
                "rag_enabled": True,
                "fine_tuned": False,
            }
        ]
    }

    with open(experts_file, "w", encoding="utf-8") as f:
        yaml.dump(existing_config, f)

    # Create project files
    (temp_project / "package.json").write_text('{"name": "test", "dependencies": {}}')

    synthesizer = ExpertSynthesizer(project_root=temp_project)
    result = synthesizer.synthesize_experts(overwrite_existing=False)

    # Should not overwrite existing
    experts = load_expert_configs(experts_file)
    existing_expert = next((e for e in experts if e.expert_id == "expert-existing"), None)
    assert existing_expert is not None


def test_create_knowledge_skeletons(temp_project):
    """Test knowledge skeleton creation."""
    # Create detection result
    detection_result = StackDetectionResult(
        domains=[
            DomainMapping(
                domain="python",
                confidence=0.9,
                signals=[
                    RepoSignal(
                        signal_type="dependency",
                        source="requirements.txt",
                        value="django",
                    )
                ],
            )
        ],
        signals=[],
    )

    synthesizer = ExpertSynthesizer(project_root=temp_project)
    result = synthesizer.synthesize_experts(detection_result=detection_result)

    # Verify knowledge skeletons were created
    assert len(result.knowledge_skeletons_created) > 0

    knowledge_dir = temp_project / ".tapps-agents" / "knowledge" / "python"
    assert knowledge_dir.exists()
    assert (knowledge_dir / "overview.md").exists()
    assert (knowledge_dir / "glossary.md").exists()
    assert (knowledge_dir / "decisions.md").exists()
    assert (knowledge_dir / "pitfalls.md").exists()
    assert (knowledge_dir / "constraints.md").exists()


def test_technical_vs_project_expert_detection(temp_project):
    """Test detection of technical vs project experts."""
    synthesizer = ExpertSynthesizer(project_root=temp_project)

    # Technical domains
    assert synthesizer.is_technical_expert("python") is True
    assert synthesizer.is_technical_expert("django") is True
    assert synthesizer.is_technical_expert("react") is True

    # Project domains
    assert synthesizer.is_project_expert("healthcare") is True
    assert synthesizer.is_project_expert("finance") is True
    assert synthesizer.is_project_expert("e-commerce") is True


def test_generate_expert_name():
    """Test expert name generation."""
    synthesizer = ExpertSynthesizer(project_root=Path("/tmp"))

    assert synthesizer._generate_expert_name("python") == "Python Expert"
    assert synthesizer._generate_expert_name("home-automation") == "Home Automation Expert"
    assert synthesizer._generate_expert_name("health_care") == "Health Care Expert"

