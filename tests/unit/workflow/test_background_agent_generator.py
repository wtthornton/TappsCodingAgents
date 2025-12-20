"""
Unit tests for Background Agent Generator (Epic 9).

Tests config generation, watch paths, triggers, and lifecycle integration.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tapps_agents.workflow.background_agent_generator import BackgroundAgentGenerator
from tapps_agents.workflow.models import Workflow, WorkflowSettings, WorkflowStep, WorkflowType


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    return tmp_path


@pytest.fixture
def sample_workflow() -> Workflow:
    """Create a sample workflow for testing."""
    return Workflow(
        id="test-workflow",
        name="Test Workflow",
        description="Test workflow for Background Agent generation",
        version="1.0.0",
        type=WorkflowType.BROWNFIELD,
        settings=WorkflowSettings(),
        steps=[
            WorkflowStep(
                id="planning",
                agent="planner",
                action="create_stories",
                requires=[],
                creates=["stories/"],
                notes="Create user stories",
            ),
            WorkflowStep(
                id="implementation",
                agent="implementer",
                action="write_code",
                requires=["stories/"],
                creates=["src/"],
            ),
            WorkflowStep(
                id="review",
                agent="reviewer",
                action="review_code",
                requires=["src/"],
                creates=["reports/review.json"],
            ),
        ],
    )


def test_generator_initialization(tmp_project: Path) -> None:
    """Test BackgroundAgentGenerator initialization."""
    generator = BackgroundAgentGenerator(tmp_project)
    
    assert generator.project_root == tmp_project
    assert generator.config_file == tmp_project / ".cursor" / "background-agents.yaml"
    
    # Config file should be created
    assert generator.config_file.exists()


def test_extract_watch_paths(tmp_project: Path, sample_workflow: Workflow) -> None:
    """Test watch path extraction from workflow steps."""
    generator = BackgroundAgentGenerator(tmp_project)
    
    step = sample_workflow.steps[1]  # implementation step
    watch_paths = generator._extract_watch_paths(step)
    
    # Should include requires and creates
    assert "stories/" in watch_paths or any("stories" in p for p in watch_paths)
    assert "src/" in watch_paths or any("src" in p for p in watch_paths)
    
    # Should be deduplicated
    assert len(watch_paths) == len(set(watch_paths))


def test_generate_triggers(tmp_project: Path, sample_workflow: Workflow) -> None:
    """Test natural language trigger generation."""
    generator = BackgroundAgentGenerator(tmp_project)
    
    step = sample_workflow.steps[0]  # planning step
    triggers = generator._generate_triggers(step, sample_workflow)
    
    # Should have multiple triggers
    assert len(triggers) > 0
    
    # Should include step-specific triggers
    assert any("planning" in t.lower() for t in triggers)
    assert any("planner" in t.lower() for t in triggers)
    
    # Should be deduplicated
    assert len(triggers) == len(set(t.lower() for t in triggers))


def test_generate_workflow_configs(tmp_project: Path, sample_workflow: Workflow) -> None:
    """Test generating configs for all workflow steps."""
    generator = BackgroundAgentGenerator(tmp_project)
    
    configs = generator.generate_workflow_configs(
        workflow=sample_workflow,
        workflow_id="test-workflow-001",
    )
    
    # Should generate config for each step
    assert len(configs) == len(sample_workflow.steps)
    
    # Check first config
    config = configs[0]
    assert config.workflow_id == "test-workflow-001"
    assert config.step_id == "planning"
    assert config.agent == "planner"
    assert config.action == "create_stories"
    assert len(config.commands) > 0
    assert len(config.triggers) > 0
    assert len(config.environment) > 0


def test_apply_workflow_configs(tmp_project: Path, sample_workflow: Workflow) -> None:
    """Test applying configs to background-agents.yaml."""
    generator = BackgroundAgentGenerator(tmp_project)
    
    # Generate configs
    configs = generator.generate_workflow_configs(
        workflow=sample_workflow,
        workflow_id="test-workflow-001",
    )
    
    # Apply configs
    generator.apply_workflow_configs(configs, "test-workflow-001")
    
    # Load and verify
    config = generator._load_config()
    agents = config.get("agents", [])
    
    # Should have agents for each step
    assert len(agents) == len(sample_workflow.steps)
    
    # Check first agent
    agent = agents[0]
    assert agent["name"] == f"TappsCodingAgents Workflow: {sample_workflow.name} - planning"
    assert agent["type"] == "background"
    assert "commands" in agent
    assert "triggers" in agent
    assert agent["metadata"]["workflow_id"] == "test-workflow-001"
    assert agent["metadata"]["generated"] is True


def test_preserve_manual_configs(tmp_project: Path, sample_workflow: Workflow) -> None:
    """Test that manual configs are preserved when applying generated configs."""
    generator = BackgroundAgentGenerator(tmp_project)
    
    # Create manual config
    manual_config = {
        "agents": [
            {
                "name": "Manual Agent",
                "type": "background",
                "commands": ["echo 'manual'"],
                "metadata": {"manual": True},
            }
        ],
        "global": {},
    }
    generator._save_config(manual_config)
    
    # Generate and apply workflow configs
    configs = generator.generate_workflow_configs(
        workflow=sample_workflow,
        workflow_id="test-workflow-001",
    )
    generator.apply_workflow_configs(configs, "test-workflow-001")
    
    # Load and verify
    config = generator._load_config()
    agents = config.get("agents", [])
    
    # Should have manual agent + generated agents
    assert len(agents) >= len(sample_workflow.steps) + 1
    
    # Manual agent should be first
    assert agents[0]["name"] == "Manual Agent"
    assert agents[0]["metadata"].get("manual") is True


def test_cleanup_workflow_configs(tmp_project: Path, sample_workflow: Workflow) -> None:
    """Test cleanup of workflow configs."""
    generator = BackgroundAgentGenerator(tmp_project)
    
    # Generate and apply configs
    configs = generator.generate_workflow_configs(
        workflow=sample_workflow,
        workflow_id="test-workflow-001",
    )
    generator.apply_workflow_configs(configs, "test-workflow-001")
    
    # Verify configs exist
    config = generator._load_config()
    assert len(config.get("agents", [])) == len(sample_workflow.steps)
    
    # Cleanup
    generator.cleanup_workflow_configs("test-workflow-001")
    
    # Verify configs removed
    config = generator._load_config()
    assert len(config.get("agents", [])) == 0


def test_config_validation(tmp_project: Path, sample_workflow: Workflow) -> None:
    """Test config validation."""
    generator = BackgroundAgentGenerator(tmp_project)
    
    # Generate and apply configs
    configs = generator.generate_workflow_configs(
        workflow=sample_workflow,
        workflow_id="test-workflow-001",
    )
    generator.apply_workflow_configs(configs, "test-workflow-001")
    
    # Validate
    is_valid, errors = generator.validate_config()
    
    assert is_valid is True
    assert len(errors) == 0


def test_backup_config(tmp_project: Path, sample_workflow: Workflow) -> None:
    """Test config backup before modification."""
    generator = BackgroundAgentGenerator(tmp_project)
    
    # Create initial config
    initial_config = {"agents": [{"name": "Initial Agent"}], "global": {}}
    generator._save_config(initial_config)
    
    # Generate and apply (should backup)
    configs = generator.generate_workflow_configs(
        workflow=sample_workflow,
        workflow_id="test-workflow-001",
    )
    generator.apply_workflow_configs(configs, "test-workflow-001")
    
    # Backup should exist
    backup_files = list(generator.config_file.parent.glob("background-agents.backup.*.yaml"))
    assert len(backup_files) > 0


def test_normalize_watch_path(tmp_project: Path) -> None:
    """Test watch path normalization."""
    generator = BackgroundAgentGenerator(tmp_project)
    
    # Test directory path
    assert generator._normalize_watch_path("stories/") == "stories/**"
    
    # Test file path
    assert generator._normalize_watch_path("src/main.py") == "src/main.py"
    
    # Test simple name
    assert generator._normalize_watch_path("config.yaml") == "config.yaml"

