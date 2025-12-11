"""
Resource Usage Monitoring

Monitors CPU, memory, and disk usage for NUC optimization.
"""

import psutil
import time
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json
import yaml


@dataclass
class ResourceMetrics:
    """Current resource usage metrics."""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_free_gb: float
    network_sent_mb: float = 0.0
    network_recv_mb: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def is_high_usage(self, cpu_threshold: float = 50.0, memory_threshold: float = 80.0) -> bool:
        """
        Check if resource usage is high.
        
        Args:
            cpu_threshold: CPU usage threshold (default: 50%)
            memory_threshold: Memory usage threshold (default: 80%)
        
        Returns:
            True if usage exceeds thresholds
        """
        return (
            self.cpu_percent > cpu_threshold or
            self.memory_percent > memory_threshold
        )


@dataclass
class ResourceAlert:
    """Resource usage alert."""
    timestamp: str
    alert_type: str  # "cpu", "memory", "disk"
    severity: str  # "warning", "critical"
    message: str
    current_value: float
    threshold: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class ResourceMonitor:
    """Monitors system resource usage."""
    
    def __init__(
        self,
        cpu_threshold: float = 50.0,
        memory_threshold: float = 80.0,
        disk_threshold: float = 90.0,
        log_file: Optional[Path] = None
    ):
        """
        Initialize resource monitor.
        
        Args:
            cpu_threshold: CPU usage threshold for alerts (%)
            memory_threshold: Memory usage threshold for alerts (%)
            disk_threshold: Disk usage threshold for alerts (%)
            log_file: Optional file to log metrics
        """
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold
        self.log_file = log_file
        
        self.metrics_history: List[ResourceMetrics] = []
        self.alerts: List[ResourceAlert] = []
        self.max_history = 1000  # Keep last 1000 measurements
    
    def get_current_metrics(self) -> ResourceMetrics:
        """
        Get current resource usage metrics.
        
        Returns:
            ResourceMetrics instance
        """
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        memory_available_mb = memory.available / (1024 * 1024)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used_gb = disk.used / (1024 * 1024 * 1024)
        disk_free_gb = disk.free / (1024 * 1024 * 1024)
        
        # Network usage (optional)
        try:
            net_io = psutil.net_io_counters()
            network_sent_mb = net_io.bytes_sent / (1024 * 1024)
            network_recv_mb = net_io.bytes_recv / (1024 * 1024)
        except Exception:
            network_sent_mb = 0.0
            network_recv_mb = 0.0
        
        metrics = ResourceMetrics(
            timestamp=datetime.utcnow().isoformat(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            memory_available_mb=memory_available_mb,
            disk_percent=disk_percent,
            disk_used_gb=disk_used_gb,
            disk_free_gb=disk_free_gb,
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb
        )
        
        # Add to history
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history:
            self.metrics_history = self.metrics_history[-self.max_history:]
        
        # Check for alerts
        self._check_alerts(metrics)
        
        # Log if file specified
        if self.log_file:
            self._log_metrics(metrics)
        
        return metrics
    
    def _check_alerts(self, metrics: ResourceMetrics):
        """Check for resource usage alerts."""
        # CPU alert
        if metrics.cpu_percent > self.cpu_threshold:
            severity = "critical" if metrics.cpu_percent > 80 else "warning"
            alert = ResourceAlert(
                timestamp=metrics.timestamp,
                alert_type="cpu",
                severity=severity,
                message=f"CPU usage is {metrics.cpu_percent:.1f}% (threshold: {self.cpu_threshold}%)",
                current_value=metrics.cpu_percent,
                threshold=self.cpu_threshold
            )
            self.alerts.append(alert)
        
        # Memory alert
        if metrics.memory_percent > self.memory_threshold:
            severity = "critical" if metrics.memory_percent > 90 else "warning"
            alert = ResourceAlert(
                timestamp=metrics.timestamp,
                alert_type="memory",
                severity=severity,
                message=f"Memory usage is {metrics.memory_percent:.1f}% (threshold: {self.memory_threshold}%)",
                current_value=metrics.memory_percent,
                threshold=self.memory_threshold
            )
            self.alerts.append(alert)
        
        # Disk alert
        if metrics.disk_percent > self.disk_threshold:
            severity = "critical" if metrics.disk_percent > 95 else "warning"
            alert = ResourceAlert(
                timestamp=metrics.timestamp,
                alert_type="disk",
                severity=severity,
                message=f"Disk usage is {metrics.disk_percent:.1f}% (threshold: {self.disk_threshold}%)",
                current_value=metrics.disk_percent,
                threshold=self.disk_threshold
            )
            self.alerts.append(alert)
    
    def _log_metrics(self, metrics: ResourceMetrics):
        """Log metrics to file."""
        if not self.log_file:
            return
        
        log_file = Path(self.log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Append to JSONL file
        with open(log_file, "a") as f:
            f.write(json.dumps(metrics.to_dict()) + "\n")
    
    def get_average_metrics(self, duration_seconds: int = 60) -> Optional[ResourceMetrics]:
        """
        Get average metrics over a duration.
        
        Args:
            duration_seconds: Duration to average over
        
        Returns:
            Average ResourceMetrics or None if insufficient data
        """
        if not self.metrics_history:
            return None
        
        # Get metrics within duration
        cutoff_time = time.time() - duration_seconds
        recent_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m.timestamp.replace('Z', '+00:00')).timestamp() > cutoff_time
        ]
        
        if not recent_metrics:
            return None
        
        # Calculate averages
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory_used = sum(m.memory_used_mb for m in recent_metrics) / len(recent_metrics)
        avg_memory_available = sum(m.memory_available_mb for m in recent_metrics) / len(recent_metrics)
        avg_disk = sum(m.disk_percent for m in recent_metrics) / len(recent_metrics)
        avg_disk_used = sum(m.disk_used_gb for m in recent_metrics) / len(recent_metrics)
        avg_disk_free = sum(m.disk_free_gb for m in recent_metrics) / len(recent_metrics)
        
        return ResourceMetrics(
            timestamp=datetime.utcnow().isoformat(),
            cpu_percent=avg_cpu,
            memory_percent=avg_memory,
            memory_used_mb=avg_memory_used,
            memory_available_mb=avg_memory_available,
            disk_percent=avg_disk,
            disk_used_gb=avg_disk_used,
            disk_free_gb=avg_disk_free
        )
    
    def get_recent_alerts(self, count: int = 10) -> List[ResourceAlert]:
        """
        Get recent alerts.
        
        Args:
            count: Number of alerts to return
        
        Returns:
            List of recent alerts
        """
        return self.alerts[-count:]
    
    def should_use_background_agent(self) -> bool:
        """
        Determine if background agent should be used based on resource usage.
        
        Returns:
            True if resources are constrained
        """
        metrics = self.get_current_metrics()
        return metrics.is_high_usage(
            cpu_threshold=self.cpu_threshold,
            memory_threshold=self.memory_threshold
        )
    
    def export_metrics(self, output_file: Path, format: str = "json"):
        """
        Export metrics to file.
        
        Args:
            output_file: Output file path
            format: Export format ("json" or "yaml")
        """
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "metrics": [m.to_dict() for m in self.metrics_history],
            "alerts": [a.to_dict() for a in self.alerts],
            "summary": {
                "total_measurements": len(self.metrics_history),
                "total_alerts": len(self.alerts),
                "cpu_threshold": self.cpu_threshold,
                "memory_threshold": self.memory_threshold,
                "disk_threshold": self.disk_threshold
            }
        }
        
        if format == "json":
            with open(output_file, "w") as f:
                json.dump(data, f, indent=2)
        elif format == "yaml":
            with open(output_file, "w") as f:
                yaml.safe_dump(data, f, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported format: {format}")


def create_resource_monitor(
    cpu_threshold: float = 50.0,
    memory_threshold: float = 80.0,
    disk_threshold: float = 90.0,
    log_file: Optional[Path] = None
) -> ResourceMonitor:
    """
    Convenience function to create a resource monitor.
    
    Args:
        cpu_threshold: CPU usage threshold
        memory_threshold: Memory usage threshold
        disk_threshold: Disk usage threshold
        log_file: Optional log file path
    
    Returns:
        ResourceMonitor instance
    """
    return ResourceMonitor(
        cpu_threshold=cpu_threshold,
        memory_threshold=memory_threshold,
        disk_threshold=disk_threshold,
        log_file=log_file
    )

