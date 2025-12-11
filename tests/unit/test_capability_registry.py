"""
Unit tests for Capability Registry.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from tapps_agents.core.capability_registry import (
    CapabilityRegistry,
    CapabilityMetric,
    RefinementRecord,
    LearningIntensity
)
from tapps_agents.core.hardware_profiler import HardwareProfile


class TestCapabilityMetric:
    """Tests for CapabilityMetric."""
    
    def test_metric_creation(self):
        """Test metric creation."""
        metric = CapabilityMetric(
            capability_id="test-capability",
            agent_id="test-agent",
            success_rate=0.8,
            average_duration=1.5,
            quality_score=0.75,
            usage_count=10
        )
        
        assert metric.capability_id == "test-capability"
        assert metric.success_rate == 0.8
        assert metric.quality_score == 0.75
    
    def test_update_metrics(self):
        """Test updating metrics."""
        metric = CapabilityMetric(
            capability_id="test",
            agent_id="agent",
            success_rate=0.5,
            average_duration=1.0,
            quality_score=0.5,
            usage_count=0
        )
        
        # Update with success
        metric.update_metrics(success=True, duration=0.8, quality_score=0.9)
        
        assert metric.success_rate > 0.5
        assert metric.average_duration < 1.0
        assert metric.quality_score > 0.5
        assert metric.usage_count == 1
    
    def test_record_refinement(self):
        """Test recording refinement."""
        metric = CapabilityMetric(
            capability_id="test",
            agent_id="agent",
            success_rate=0.5,
            average_duration=1.0,
            quality_score=0.5,
            usage_count=10
        )
        
        metric.record_refinement(
            improvement_type="prompt_optimization",
            improvement_percent=15.0,
            learned_patterns=["pattern1", "pattern2"]
        )
        
        assert len(metric.refinement_history) == 1
        assert metric.last_improved is not None
        assert metric.refinement_history[0].improvement_percent == 15.0


class TestCapabilityRegistry:
    """Tests for CapabilityRegistry."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)
    
    def test_registry_creation(self, temp_dir):
        """Test registry creation."""
        registry = CapabilityRegistry(storage_dir=temp_dir)
        
        assert len(registry.metrics) == 0
        assert registry.storage_dir == temp_dir
    
    def test_register_capability(self, temp_dir):
        """Test registering capability."""
        registry = CapabilityRegistry(storage_dir=temp_dir)
        
        metric = registry.register_capability(
            capability_id="test-cap",
            agent_id="test-agent",
            initial_quality=0.7
        )
        
        assert metric.capability_id == "test-cap"
        assert metric.agent_id == "test-agent"
        assert metric.quality_score == 0.7
        assert "test-cap" in registry.metrics
    
    def test_update_capability_metrics(self, temp_dir):
        """Test updating capability metrics."""
        registry = CapabilityRegistry(storage_dir=temp_dir)
        
        registry.register_capability("test-cap", "agent", initial_quality=0.5)
        registry.update_capability_metrics(
            capability_id="test-cap",
            success=True,
            duration=1.0,
            quality_score=0.8
        )
        
        metric = registry.get_capability("test-cap")
        assert metric is not None
        assert metric.usage_count > 0
        assert metric.quality_score > 0.5
    
    def test_get_agent_capabilities(self, temp_dir):
        """Test getting agent capabilities."""
        registry = CapabilityRegistry(storage_dir=temp_dir)
        
        registry.register_capability("cap1", "agent1")
        registry.register_capability("cap2", "agent1")
        registry.register_capability("cap3", "agent2")
        
        agent1_caps = registry.get_agent_capabilities("agent1")
        assert len(agent1_caps) == 2
    
    def test_get_top_capabilities(self, temp_dir):
        """Test getting top capabilities."""
        registry = CapabilityRegistry(storage_dir=temp_dir)
        
        registry.register_capability("cap1", "agent", initial_quality=0.9)
        registry.register_capability("cap2", "agent", initial_quality=0.7)
        registry.register_capability("cap3", "agent", initial_quality=0.8)
        
        top = registry.get_top_capabilities(agent_id="agent", limit=2)
        assert len(top) == 2
        assert top[0].quality_score >= top[1].quality_score
    
    def test_get_improvement_candidates(self, temp_dir):
        """Test getting improvement candidates."""
        registry = CapabilityRegistry(storage_dir=temp_dir)
        
        registry.register_capability("cap1", "agent", initial_quality=0.5)
        registry.register_capability("cap2", "agent", initial_quality=0.8)
        
        # Update cap1 to have usage
        metric = registry.get_capability("cap1")
        for _ in range(15):
            metric.update_metrics(success=True, duration=1.0, quality_score=0.5)
        
        candidates = registry.get_improvement_candidates(min_usage=10, max_quality=0.7)
        assert len(candidates) == 1
        assert candidates[0].capability_id == "cap1"
    
    def test_learning_intensity(self, temp_dir):
        """Test learning intensity based on hardware."""
        registry_nuc = CapabilityRegistry(
            storage_dir=temp_dir / "nuc",
            hardware_profile=HardwareProfile.NUC
        )
        assert registry_nuc.get_learning_intensity() == LearningIntensity.LOW
        
        registry_ws = CapabilityRegistry(
            storage_dir=temp_dir / "ws",
            hardware_profile=HardwareProfile.WORKSTATION
        )
        assert registry_ws.get_learning_intensity() == LearningIntensity.HIGH
    
    def test_persistence(self, temp_dir):
        """Test metric persistence."""
        registry = CapabilityRegistry(storage_dir=temp_dir)
        
        registry.register_capability("test-cap", "agent", initial_quality=0.7)
        registry.update_capability_metrics("test-cap", success=True, duration=1.0)
        
        # Create new registry and load
        registry2 = CapabilityRegistry(storage_dir=temp_dir)
        metric = registry2.get_capability("test-cap")
        
        assert metric is not None
        assert metric.quality_score == 0.7

