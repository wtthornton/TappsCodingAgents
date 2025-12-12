"""
Unit tests for ResourceAwareExecutor.
"""

import time
from unittest.mock import Mock, patch

import pytest

from tapps_agents.core.hardware_profiler import HardwareProfile
from tapps_agents.core.resource_aware_executor import (
    AutoPause,
    ExecutionConfig,
    ExecutionMode,
    ExecutionState,
    ResourceAwareExecutor,
    ResourceOptimizer,
)
from tapps_agents.core.resource_monitor import ResourceMetrics
from tapps_agents.core.session_manager import SessionManager

pytestmark = pytest.mark.unit


class TestAutoPause:
    """Test AutoPause functionality."""

    def test_should_pause_on_high_cpu(self):
        """Test pause when CPU exceeds threshold."""
        config = ExecutionConfig(auto_pause_enabled=True, pause_cpu_threshold=80.0)
        auto_pause = AutoPause(config)

        metrics = ResourceMetrics(
            timestamp="2025-01-01T00:00:00Z",
            cpu_percent=90.0,
            memory_percent=50.0,
            memory_used_mb=1000.0,
            memory_available_mb=2000.0,
            disk_percent=50.0,
            disk_used_gb=100.0,
            disk_free_gb=200.0,
        )

        should_pause, reason = auto_pause.should_pause(metrics)
        assert should_pause is True
        assert "CPU" in reason

    def test_should_pause_on_high_memory(self):
        """Test pause when memory exceeds threshold."""
        config = ExecutionConfig(auto_pause_enabled=True, pause_memory_threshold=90.0)
        auto_pause = AutoPause(config)

        metrics = ResourceMetrics(
            timestamp="2025-01-01T00:00:00Z",
            cpu_percent=50.0,
            memory_percent=95.0,
            memory_used_mb=1000.0,
            memory_available_mb=2000.0,
            disk_percent=50.0,
            disk_used_gb=100.0,
            disk_free_gb=200.0,
        )

        should_pause, reason = auto_pause.should_pause(metrics)
        assert should_pause is True
        assert "Memory" in reason

    def test_should_not_pause_when_disabled(self):
        """Test that pause is disabled when auto_pause_enabled is False."""
        config = ExecutionConfig(auto_pause_enabled=False)
        auto_pause = AutoPause(config)

        metrics = ResourceMetrics(
            timestamp="2025-01-01T00:00:00Z",
            cpu_percent=100.0,
            memory_percent=100.0,
            memory_used_mb=1000.0,
            memory_available_mb=0.0,
            disk_percent=100.0,
            disk_used_gb=100.0,
            disk_free_gb=0.0,
        )

        should_pause, reason = auto_pause.should_pause(metrics)
        assert should_pause is False
        assert reason is None

    def test_should_resume_when_resources_recovered(self):
        """Test resume when resources are below recovery thresholds."""
        config = ExecutionConfig(
            recovery_cpu_threshold=50.0, recovery_memory_threshold=60.0
        )
        auto_pause = AutoPause(config)
        auto_pause.is_paused = True

        metrics = ResourceMetrics(
            timestamp="2025-01-01T00:00:00Z",
            cpu_percent=40.0,
            memory_percent=50.0,
            memory_used_mb=1000.0,
            memory_available_mb=2000.0,
            disk_percent=50.0,
            disk_used_gb=100.0,
            disk_free_gb=200.0,
        )

        assert auto_pause.should_resume(metrics) is True

    def test_should_not_resume_when_still_high(self):
        """Test that resume doesn't happen when resources are still high."""
        config = ExecutionConfig(
            recovery_cpu_threshold=50.0, recovery_memory_threshold=60.0
        )
        auto_pause = AutoPause(config)
        auto_pause.is_paused = True

        metrics = ResourceMetrics(
            timestamp="2025-01-01T00:00:00Z",
            cpu_percent=70.0,
            memory_percent=80.0,
            memory_used_mb=1000.0,
            memory_available_mb=2000.0,
            disk_percent=50.0,
            disk_used_gb=100.0,
            disk_free_gb=200.0,
        )

        assert auto_pause.should_resume(metrics) is False


class TestResourceOptimizer:
    """Test ResourceOptimizer functionality."""

    def test_get_optimization_suggestions(self):
        """Test getting optimization suggestions."""
        config = ExecutionConfig()
        optimizer = ResourceOptimizer(config)

        metrics = ResourceMetrics(
            timestamp="2025-01-01T00:00:00Z",
            cpu_percent=70.0,
            memory_percent=75.0,
            memory_used_mb=1000.0,
            memory_available_mb=2000.0,
            disk_percent=85.0,
            disk_used_gb=100.0,
            disk_free_gb=200.0,
        )

        suggestions = optimizer.get_optimization_suggestions(metrics)
        assert len(suggestions) > 0
        assert any(
            "CPU" in s or "cpu" in s.lower() or "concurrent" in s.lower()
            for s in suggestions
        )
        assert any("memory" in s.lower() or "cache" in s.lower() for s in suggestions)
        assert any("disk" in s.lower() or "clean" in s.lower() for s in suggestions)

    def test_should_degrade_on_high_cpu(self):
        """Test degradation when CPU exceeds threshold."""
        config = ExecutionConfig(degradation_enabled=True, degrade_cpu_threshold=70.0)
        optimizer = ResourceOptimizer(config)

        metrics = ResourceMetrics(
            timestamp="2025-01-01T00:00:00Z",
            cpu_percent=80.0,
            memory_percent=50.0,
            memory_used_mb=1000.0,
            memory_available_mb=2000.0,
            disk_percent=50.0,
            disk_used_gb=100.0,
            disk_free_gb=200.0,
        )

        should_degrade, reason = optimizer.should_degrade(metrics)
        assert should_degrade is True
        assert "CPU" in reason

    def test_should_not_degrade_when_disabled(self):
        """Test that degradation is disabled when degradation_enabled is False."""
        config = ExecutionConfig(degradation_enabled=False)
        optimizer = ResourceOptimizer(config)

        metrics = ResourceMetrics(
            timestamp="2025-01-01T00:00:00Z",
            cpu_percent=100.0,
            memory_percent=100.0,
            memory_used_mb=1000.0,
            memory_available_mb=0.0,
            disk_percent=100.0,
            disk_used_gb=100.0,
            disk_free_gb=0.0,
        )

        should_degrade, reason = optimizer.should_degrade(metrics)
        assert should_degrade is False
        assert reason is None


class TestResourceAwareExecutor:
    """Test ResourceAwareExecutor functionality."""

    def test_initialization(self):
        """Test executor initialization."""
        executor = ResourceAwareExecutor()

        assert executor.config is not None
        assert executor.resource_monitor is not None
        assert executor.auto_pause is not None
        assert executor.optimizer is not None
        assert executor.execution_state is not None

    def test_initialization_with_config(self):
        """Test executor initialization with custom config."""
        config = ExecutionConfig(monitor_interval=10.0, cpu_threshold=70.0)
        executor = ResourceAwareExecutor(config=config)

        assert executor.config.monitor_interval == 10.0
        assert executor.config.cpu_threshold == 70.0

    def test_initialization_with_session_manager(self):
        """Test executor initialization with session manager."""
        session_manager = Mock(spec=SessionManager)
        executor = ResourceAwareExecutor(session_manager=session_manager)

        assert executor.session_manager is session_manager

    @patch("tapps_agents.core.resource_aware_executor.HardwareProfiler")
    def test_hardware_profile_adjustments_nuc(self, mock_profiler_class):
        """Test hardware profile adjustments for NUC."""
        mock_profiler = Mock()
        mock_profiler.detect_profile.return_value = HardwareProfile.NUC
        mock_profiler_class.return_value = mock_profiler

        config = ExecutionConfig(hardware_profile=HardwareProfile.NUC)
        executor = ResourceAwareExecutor(config=config)

        # NUC should have more aggressive thresholds
        assert executor.config.monitor_interval == 20.0
        assert executor.config.pause_cpu_threshold == 85.0
        assert executor.config.pause_memory_threshold == 90.0

    @patch("tapps_agents.core.resource_aware_executor.HardwareProfiler")
    def test_hardware_profile_adjustments_workstation(self, mock_profiler_class):
        """Test hardware profile adjustments for workstation."""
        mock_profiler = Mock()
        mock_profiler.detect_profile.return_value = HardwareProfile.WORKSTATION
        mock_profiler_class.return_value = mock_profiler

        config = ExecutionConfig(hardware_profile=HardwareProfile.WORKSTATION)
        executor = ResourceAwareExecutor(config=config)

        # Workstation should have less aggressive thresholds
        assert executor.config.monitor_interval == 60.0
        assert executor.config.pause_cpu_threshold == 95.0
        assert executor.config.pause_memory_threshold == 98.0

    def test_execute_task_success(self):
        """Test successful task execution."""
        executor = ResourceAwareExecutor()

        def task():
            return "result"

        result = executor.execute(task, task_name="test_task")
        assert result == "result"

    def test_execute_task_with_high_resources_raises(self):
        """Test that execution raises when resources are high."""
        config = ExecutionConfig(pause_cpu_threshold=50.0, auto_pause_enabled=True)
        executor = ResourceAwareExecutor(config=config)

        # Mock high CPU usage
        with patch.object(
            executor.resource_monitor, "get_current_metrics"
        ) as mock_metrics:
            mock_metrics.return_value = ResourceMetrics(
                timestamp="2025-01-01T00:00:00Z",
                cpu_percent=90.0,
                memory_percent=50.0,
                memory_used_mb=1000.0,
                memory_available_mb=2000.0,
                disk_percent=50.0,
                disk_used_gb=100.0,
                disk_free_gb=200.0,
            )

            def task():
                return "result"

            with pytest.raises(RuntimeError, match="paused"):
                executor.execute(task, task_name="test_task", check_resources=True)

    def test_monitoring_start_stop(self):
        """Test starting and stopping monitoring."""
        executor = ResourceAwareExecutor()

        executor.start_monitoring()
        assert executor._monitoring_active is True
        assert executor._monitoring_thread is not None

        # Wait a bit for thread to start
        time.sleep(0.1)

        executor.stop_monitoring()
        assert executor._monitoring_active is False

    def test_context_manager(self):
        """Test executor as context manager."""
        executor = ResourceAwareExecutor()

        with executor:
            assert executor._monitoring_active is True

        assert executor._monitoring_active is False

    def test_get_execution_state(self):
        """Test getting execution state."""
        executor = ResourceAwareExecutor()

        state = executor.get_execution_state()
        assert isinstance(state, ExecutionState)
        assert state.mode == ExecutionMode.NORMAL

    def test_get_current_metrics(self):
        """Test getting current resource metrics."""
        executor = ResourceAwareExecutor()

        metrics = executor.get_current_metrics()
        assert isinstance(metrics, ResourceMetrics)

    def test_get_optimization_suggestions(self):
        """Test getting optimization suggestions."""
        executor = ResourceAwareExecutor()

        suggestions = executor.get_optimization_suggestions()
        assert isinstance(suggestions, list)

    def test_force_resume(self):
        """Test force resume."""
        executor = ResourceAwareExecutor()
        executor.auto_pause.is_paused = True

        executor.force_resume()
        assert executor.auto_pause.is_paused is False
        assert executor.execution_state.mode == ExecutionMode.NORMAL

    def test_force_pause(self):
        """Test force pause."""
        executor = ResourceAwareExecutor()

        executor.force_pause("Test pause")
        assert executor.auto_pause.is_paused is True
        assert executor.execution_state.mode == ExecutionMode.PAUSED

    def test_pause_integrates_with_session_manager(self):
        """Test that pause integrates with session manager."""
        session_manager = Mock(spec=SessionManager)
        session_manager.get_active_sessions.return_value = []

        executor = ResourceAwareExecutor(session_manager=session_manager)

        # Mock high CPU usage
        with patch.object(
            executor.resource_monitor, "get_current_metrics"
        ) as mock_metrics:
            mock_metrics.return_value = ResourceMetrics(
                timestamp="2025-01-01T00:00:00Z",
                cpu_percent=95.0,
                memory_percent=50.0,
                memory_used_mb=1000.0,
                memory_available_mb=2000.0,
                disk_percent=50.0,
                disk_used_gb=100.0,
                disk_free_gb=200.0,
            )

            executor._check_resources(mock_metrics.return_value)

            # Should have tried to pause sessions
            session_manager.get_active_sessions.assert_called()

    def test_execution_state_tracking(self):
        """Test that execution state tracks pauses and degradations."""
        executor = ResourceAwareExecutor()

        initial_pause_count = executor.execution_state.pause_count
        initial_degradation_count = executor.execution_state.degradation_count

        executor.force_pause("Test")
        assert executor.execution_state.pause_count == initial_pause_count + 1

        executor.force_resume()

        # Simulate degradation
        with patch.object(
            executor.resource_monitor, "get_current_metrics"
        ) as mock_metrics:
            mock_metrics.return_value = ResourceMetrics(
                timestamp="2025-01-01T00:00:00Z",
                cpu_percent=75.0,
                memory_percent=50.0,
                memory_used_mb=1000.0,
                memory_available_mb=2000.0,
                disk_percent=50.0,
                disk_used_gb=100.0,
                disk_free_gb=200.0,
            )

            executor.config.degrade_cpu_threshold = 70.0
            executor._check_resources(mock_metrics.return_value)

            assert (
                executor.execution_state.degradation_count
                == initial_degradation_count + 1
            )
