"""
Resource-Aware Executor for Long-Duration Operations

Executes tasks with resource awareness, auto-pause, and graceful degradation.
"""

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from .hardware_profiler import HardwareProfile, HardwareProfiler
from .resource_monitor import ResourceMetrics, ResourceMonitor
from .session_manager import SessionManager, SessionState

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Execution mode based on resource availability."""

    NORMAL = "normal"
    DEGRADED = "degraded"
    PAUSED = "paused"
    SUSPENDED = "suspended"


@dataclass
class ExecutionConfig:
    """Configuration for resource-aware execution."""

    # Monitoring
    monitor_interval: float = 30.0  # seconds
    cpu_threshold: float = 80.0  # %
    memory_threshold: float = 85.0  # %
    disk_threshold: float = 90.0  # %

    # Auto-pause
    auto_pause_enabled: bool = True
    pause_cpu_threshold: float = 90.0  # %
    pause_memory_threshold: float = 95.0  # %
    pause_disk_threshold: float = 95.0  # %

    # Graceful degradation
    degradation_enabled: bool = True
    degrade_cpu_threshold: float = 70.0  # %
    degrade_memory_threshold: float = 75.0  # %

    # Recovery
    recovery_check_interval: float = 60.0  # seconds
    recovery_cpu_threshold: float = 50.0  # %
    recovery_memory_threshold: float = 60.0  # %

    # Hardware-aware adjustments
    hardware_profile: HardwareProfile | None = None


@dataclass
class ExecutionState:
    """Current execution state."""

    mode: ExecutionMode = ExecutionMode.NORMAL
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_check: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    pause_count: int = 0
    degradation_count: int = 0
    resource_history: list[ResourceMetrics] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)

    def add_alert(self, message: str):
        """Add an alert message."""
        self.alerts.append(f"{datetime.now(timezone.utc).isoformat()}: {message}")
        if len(self.alerts) > 100:  # Keep last 100 alerts
            self.alerts = self.alerts[-100:]


class AutoPause:
    """Automatic pause mechanism based on resource constraints."""

    def __init__(self, config: ExecutionConfig):
        """
        Initialize auto-pause.

        Args:
            config: Execution configuration
        """
        self.config = config
        self.is_paused = False
        self.pause_reason: str | None = None

    def should_pause(self, metrics: ResourceMetrics) -> tuple[bool, str | None]:
        """
        Check if execution should be paused.

        Args:
            metrics: Current resource metrics

        Returns:
            Tuple of (should_pause, reason)
        """
        if not self.config.auto_pause_enabled:
            return False, None

        # Check CPU
        if metrics.cpu_percent > self.config.pause_cpu_threshold:
            return (
                True,
                f"CPU usage {metrics.cpu_percent:.1f}% exceeds threshold {self.config.pause_cpu_threshold}%",
            )

        # Check memory
        if metrics.memory_percent > self.config.pause_memory_threshold:
            return (
                True,
                f"Memory usage {metrics.memory_percent:.1f}% exceeds threshold {self.config.pause_memory_threshold}%",
            )

        # Check disk
        if metrics.disk_percent > self.config.pause_disk_threshold:
            return (
                True,
                f"Disk usage {metrics.disk_percent:.1f}% exceeds threshold {self.config.pause_disk_threshold}%",
            )

        return False, None

    def should_resume(self, metrics: ResourceMetrics) -> bool:
        """
        Check if execution should resume.

        Args:
            metrics: Current resource metrics

        Returns:
            True if should resume
        """
        if not self.is_paused:
            return False

        # Resume if resources are below recovery thresholds
        return (
            metrics.cpu_percent < self.config.recovery_cpu_threshold
            and metrics.memory_percent < self.config.recovery_memory_threshold
        )


class ResourceOptimizer:
    """Optimizes resource usage based on current conditions."""

    def __init__(self, config: ExecutionConfig):
        """
        Initialize resource optimizer.

        Args:
            config: Execution configuration
        """
        self.config = config
        self.hardware_profiler = HardwareProfiler()

    def get_optimization_suggestions(self, metrics: ResourceMetrics) -> list[str]:
        """
        Get optimization suggestions based on current metrics.

        Args:
            metrics: Current resource metrics

        Returns:
            List of optimization suggestions
        """
        suggestions = []

        # CPU optimization
        if metrics.cpu_percent > 60:
            suggestions.append("Reduce concurrent operations")
            suggestions.append("Increase checkpoint intervals")

        # Memory optimization
        if metrics.memory_percent > 70:
            suggestions.append("Clear unused caches")
            suggestions.append("Reduce in-memory data structures")
            suggestions.append("Enable compression")

        # Disk optimization
        if metrics.disk_percent > 80:
            suggestions.append("Clean up temporary files")
            suggestions.append("Reduce cache sizes")
            suggestions.append("Archive old checkpoints")

        return suggestions

    def should_degrade(self, metrics: ResourceMetrics) -> tuple[bool, str | None]:
        """
        Check if execution should degrade.

        Args:
            metrics: Current resource metrics

        Returns:
            Tuple of (should_degrade, reason)
        """
        if not self.config.degradation_enabled:
            return False, None

        # Check CPU
        if metrics.cpu_percent > self.config.degrade_cpu_threshold:
            return (
                True,
                f"CPU usage {metrics.cpu_percent:.1f}% exceeds degradation threshold {self.config.degrade_cpu_threshold}%",
            )

        # Check memory
        if metrics.memory_percent > self.config.degrade_memory_threshold:
            return (
                True,
                f"Memory usage {metrics.memory_percent:.1f}% exceeds degradation threshold {self.config.degrade_memory_threshold}%",
            )

        return False, None


class ResourceAwareExecutor:
    """Executes tasks with resource awareness and auto-pause."""

    def __init__(
        self,
        session_manager: SessionManager | None = None,
        config: ExecutionConfig | None = None,
    ):
        """
        Initialize resource-aware executor.

        Args:
            session_manager: Optional session manager for session integration
            config: Execution configuration
        """
        self.session_manager = session_manager
        self.config = config or ExecutionConfig()
        self.resource_monitor = ResourceMonitor(
            cpu_threshold=self.config.cpu_threshold,
            memory_threshold=self.config.memory_threshold,
            disk_threshold=self.config.disk_threshold,
        )
        self.auto_pause = AutoPause(self.config)
        self.optimizer = ResourceOptimizer(self.config)
        self.execution_state = ExecutionState()

        # Hardware-aware adjustments
        if not self.config.hardware_profile:
            hardware_profiler = HardwareProfiler()
            self.config.hardware_profile = hardware_profiler.detect_profile()

        self._apply_hardware_profile()

        # Monitoring thread
        self._monitoring_thread: threading.Thread | None = None
        self._monitoring_active = False
        self._lock = threading.Lock()

    def _apply_hardware_profile(self):
        """Apply hardware profile-specific adjustments."""
        profile = self.config.hardware_profile

        if profile == HardwareProfile.NUC:
            # NUC: More aggressive thresholds, frequent monitoring
            self.config.monitor_interval = 20.0
            self.config.pause_cpu_threshold = 85.0
            self.config.pause_memory_threshold = 90.0
            self.config.degrade_cpu_threshold = 60.0
            self.config.degrade_memory_threshold = 70.0
        elif profile == HardwareProfile.WORKSTATION:
            # Workstation: Less aggressive, can handle more
            self.config.monitor_interval = 60.0
            self.config.pause_cpu_threshold = 95.0
            self.config.pause_memory_threshold = 98.0
            self.config.degrade_cpu_threshold = 80.0
            self.config.degrade_memory_threshold = 85.0

    def start_monitoring(self):
        """Start continuous resource monitoring."""
        if self._monitoring_active:
            return

        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self._monitoring_thread.start()
        logger.info("Resource monitoring started")

    def stop_monitoring(self):
        """Stop resource monitoring."""
        self._monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5.0)
        logger.info("Resource monitoring stopped")

    def _monitoring_loop(self):
        """Continuous monitoring loop."""
        while self._monitoring_active:
            try:
                metrics = self.resource_monitor.get_current_metrics()
                self._check_resources(metrics)
                time.sleep(self.config.monitor_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                time.sleep(self.config.monitor_interval)

    def _check_resources(self, metrics: ResourceMetrics):
        """Check resources and adjust execution mode."""
        with self._lock:
            self.execution_state.last_check = datetime.now(timezone.utc)
            self.execution_state.resource_history.append(metrics)
            if len(self.execution_state.resource_history) > 100:
                self.execution_state.resource_history = (
                    self.execution_state.resource_history[-100:]
                )

            # Check for auto-pause
            should_pause, pause_reason = self.auto_pause.should_pause(metrics)
            if should_pause and not self.auto_pause.is_paused:
                self._pause_execution(pause_reason)
            elif self.auto_pause.should_resume(metrics) and self.auto_pause.is_paused:
                self._resume_execution()

            # Check for degradation
            should_degrade, degrade_reason = self.optimizer.should_degrade(metrics)
            if should_degrade and self.execution_state.mode == ExecutionMode.NORMAL:
                self._degrade_execution(degrade_reason)
            elif (
                not should_degrade
                and self.execution_state.mode == ExecutionMode.DEGRADED
            ):
                self._restore_normal_execution()

    def _pause_execution(self, reason: str):
        """Pause execution due to resource constraints."""
        logger.warning(f"Pausing execution: {reason}")
        self.auto_pause.is_paused = True
        self.auto_pause.pause_reason = reason
        self.execution_state.mode = ExecutionMode.PAUSED
        self.execution_state.pause_count += 1
        self.execution_state.add_alert(f"PAUSED: {reason}")

        # Pause session if available
        if self.session_manager:
            try:
                sessions = self.session_manager.get_active_sessions()
                for session in sessions:
                    self.session_manager.pause_session(session.session_id, reason)
            except Exception as e:
                logger.error(f"Error pausing sessions: {e}", exc_info=True)

    def _resume_execution(self, reason: str | None = None):
        """Resume execution after resource recovery."""
        resume_reason = reason or "Resources recovered"
        logger.info(f"Resuming execution: {resume_reason}")
        self.auto_pause.is_paused = False
        self.auto_pause.pause_reason = None
        self.execution_state.mode = ExecutionMode.NORMAL
        self.execution_state.add_alert(f"RESUMED: {resume_reason}")

        # Resume session if available
        if self.session_manager:
            try:
                sessions = self.session_manager.list_sessions(state=SessionState.PAUSED)
                for session in sessions:
                    self.session_manager.resume_session(session.session_id)
            except Exception as e:
                logger.error(f"Error resuming sessions: {e}", exc_info=True)

    def _degrade_execution(self, reason: str):
        """Degrade execution quality due to resource constraints."""
        logger.warning(f"Degrading execution: {reason}")
        self.execution_state.mode = ExecutionMode.DEGRADED
        self.execution_state.degradation_count += 1
        self.execution_state.add_alert(f"DEGRADED: {reason}")

    def _restore_normal_execution(self):
        """Restore normal execution mode."""
        logger.info("Restoring normal execution mode")
        self.execution_state.mode = ExecutionMode.NORMAL
        self.execution_state.add_alert("RESTORED: Normal execution mode")

    def execute(
        self,
        task: Callable[[], Any],
        task_name: str = "task",
        check_resources: bool = True,
    ) -> Any:
        """
        Execute a task with resource awareness.

        Args:
            task: Task function to execute
            task_name: Name of the task
            check_resources: Whether to check resources before execution

        Returns:
            Task result

        Raises:
            RuntimeError: If execution is paused or suspended
        """
        # Check if execution is paused
        if self.auto_pause.is_paused:
            raise RuntimeError(
                f"Execution is paused: {self.auto_pause.pause_reason}. "
                "Wait for resources to recover or manually resume."
            )

        # Check resources before execution
        if check_resources:
            metrics = self.resource_monitor.get_current_metrics()
            should_pause, pause_reason = self.auto_pause.should_pause(metrics)
            if should_pause:
                self._pause_execution(pause_reason)
                raise RuntimeError(f"Execution paused: {pause_reason}")

        # Execute task
        try:
            logger.info(
                f"Executing task: {task_name} (mode: {self.execution_state.mode.value})"
            )
            result = task()
            return result
        except Exception as e:
            logger.error(f"Task execution failed: {e}", exc_info=True)
            raise

    def get_execution_state(self) -> ExecutionState:
        """Get current execution state."""
        with self._lock:
            return self.execution_state

    def get_current_metrics(self) -> ResourceMetrics:
        """Get current resource metrics."""
        return self.resource_monitor.get_current_metrics()

    def get_optimization_suggestions(self) -> list[str]:
        """Get optimization suggestions based on current metrics."""
        metrics = self.resource_monitor.get_current_metrics()
        return self.optimizer.get_optimization_suggestions(metrics)

    def force_resume(self):
        """Force resume execution (use with caution)."""
        logger.warning("Force resuming execution")
        self._resume_execution("Force resume requested")

    def force_pause(self, reason: str = "Manual pause"):
        """Force pause execution."""
        logger.warning(f"Force pausing execution: {reason}")
        self._pause_execution(reason)

    def __enter__(self):
        """Context manager entry."""
        self.start_monitoring()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_monitoring()
