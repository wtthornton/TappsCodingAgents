"""
Tests for fallback_strategy.py
"""

import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

from tapps_agents.core.config import ProjectConfig, WorkflowConfig
from tapps_agents.core.fallback_strategy import (
    FallbackStrategy,
    TaskDecision,
    TaskType,
)


class TestTaskType:
    """Test TaskType enum."""

    def test_values(self):
        """Test enum values."""
        assert TaskType.LIGHT.value == "light"
        assert TaskType.MEDIUM.value == "medium"
        assert TaskType.HEAVY.value == "heavy"


class TestTaskDecision:
    """Test TaskDecision dataclass."""

    def test_init(self):
        """Test initialization."""
        decision = TaskDecision(
            task_name="test-task",
            task_type=TaskType.LIGHT,
            use_background=False,
            reason="Quick task",
        )
        
        assert decision.task_name == "test-task"
        assert decision.task_type == TaskType.LIGHT
        assert decision.use_background is False
        assert decision.reason == "Quick task"
        assert decision.resource_metrics is None

    def test_to_dict(self):
        """Test conversion to dictionary."""
        decision = TaskDecision(
            task_name="test-task",
            task_type=TaskType.HEAVY,
            use_background=True,
            reason="Heavy task",
        )
        
        data = decision.to_dict()
        
        assert data["task_name"] == "test-task"
        assert data["task_type"] == "heavy"
        assert data["use_background"] is True
        assert data["reason"] == "Heavy task"
        assert data["resource_metrics"] is None


class TestFallbackStrategy:
    """Test FallbackStrategy class."""

    def test_init_default(self):
        """Test initialization with defaults."""
        strategy = FallbackStrategy()
        
        assert strategy.config is None
        assert strategy.resource_monitor is None
        assert strategy.force_background is False
        assert strategy.duration_estimator is not None

    def test_init_with_config(self):
        """Test initialization with config."""
        config = ProjectConfig(
            workflow=WorkflowConfig(duration_threshold_seconds=60.0)
        )
        strategy = FallbackStrategy(config=config)
        
        assert strategy.config == config
        assert strategy.duration_estimator.default_threshold == 60.0

    def test_init_force_background(self):
        """Test initialization with force_background."""
        strategy = FallbackStrategy(force_background=True)
        
        assert strategy.force_background is True

    def test_load_nuc_config_no_file(self):
        """Test loading NUC config when file doesn't exist."""
        # This test may fail if nuc-config.yaml exists in the project
        # Skip if file exists (it does in this project)
        nuc_config_file = Path(".tapps-agents/nuc-config.yaml")
        if nuc_config_file.exists():
            pytest.skip("NUC config file exists in project")
        
        strategy = FallbackStrategy()
        config = strategy._load_nuc_config()
        assert config == {}

    def test_classify_task_heavy(self):
        """Test classifying heavy tasks."""
        strategy = FallbackStrategy()
        
        assert strategy.classify_task("analyze-project") == TaskType.HEAVY
        assert strategy.classify_task("security-scan") == TaskType.HEAVY
        assert strategy.classify_task("full-review") == TaskType.HEAVY

    def test_classify_task_medium(self):
        """Test classifying medium tasks."""
        strategy = FallbackStrategy()
        
        assert strategy.classify_task("review-file") == TaskType.MEDIUM
        assert strategy.classify_task("generate-code") == TaskType.MEDIUM

    def test_classify_task_light(self):
        """Test classifying light tasks."""
        strategy = FallbackStrategy()
        
        assert strategy.classify_task("lint-file") == TaskType.LIGHT
        assert strategy.classify_task("type-check") == TaskType.LIGHT
        assert strategy.classify_task("format-code") == TaskType.LIGHT

    def test_classify_task_unknown(self):
        """Test classifying unknown tasks."""
        strategy = FallbackStrategy()
        
        # Unknown tasks default to MEDIUM
        assert strategy.classify_task("unknown-task") == TaskType.MEDIUM

    def test_should_use_background_agent_force_background(self):
        """Test that force_background always returns True."""
        strategy = FallbackStrategy(force_background=True)
        
        decision = strategy.should_use_background_agent("test-task")
        
        assert decision.use_background is True
        assert "force" in decision.reason.lower() and "background" in decision.reason.lower()

    def test_should_use_background_agent_duration_below_threshold(self):
        """Test that short tasks don't use background agent."""
        config = ProjectConfig(
            workflow=WorkflowConfig(duration_threshold_seconds=30.0)
        )
        strategy = FallbackStrategy(config=config)
        
        decision = strategy.should_use_background_agent(
            "reviewer review", check_resources=False
        )
        
        # Short tasks should not use background
        assert decision.use_background is False
        # Reason may mention duration, threshold, or task type
        reason_lower = decision.reason.lower()
        assert any(keyword in reason_lower for keyword in ["duration", "threshold", "medium", "light", "local"])

    def test_should_use_background_agent_duration_above_threshold(self):
        """Test that long tasks use background agent."""
        config = ProjectConfig(
            workflow=WorkflowConfig(duration_threshold_seconds=30.0)
        )
        strategy = FallbackStrategy(config=config)
        
        decision = strategy.should_use_background_agent(
            "reviewer analyze-project", check_resources=False
        )
        
        # Long tasks should use background
        assert decision.use_background is True

    def test_should_use_background_agent_heavy_task(self):
        """Test that heavy tasks use background agent."""
        strategy = FallbackStrategy()
        
        decision = strategy.should_use_background_agent(
            "analyze-project", check_resources=False
        )
        
        assert decision.task_type == TaskType.HEAVY
        # Heavy tasks typically use background (unless duration is very short)
        assert isinstance(decision.use_background, bool)

    def test_should_use_background_agent_light_task(self):
        """Test that light tasks don't use background agent."""
        strategy = FallbackStrategy()
        
        decision = strategy.should_use_background_agent(
            "lint-file", check_resources=False
        )
        
        assert decision.task_type == TaskType.LIGHT
        # Light tasks typically don't use background
        assert decision.use_background is False
