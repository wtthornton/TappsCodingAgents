"""
Performance Monitoring for Multi-Agent Orchestration

Tracks and reports performance metrics for parallel agent execution.
"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitors performance of multi-agent execution."""
    
    def __init__(self, task_id: str, output_dir: Path):
        """
        Initialize PerformanceMonitor.
        
        Args:
            task_id: Task identifier
            output_dir: Output directory for metrics
        """
        self.task_id = task_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.metrics: Dict[str, Any] = {
            "task_id": task_id,
            "start_time": None,
            "end_time": None,
            "total_duration": None,
            "agents": {},
            "parallelism": {
                "max_parallel": 0,
                "average_parallel": 0,
                "total_agents": 0
            },
            "throughput": {
                "agents_per_second": 0,
                "total_agents": 0
            },
            "efficiency": {
                "sequential_time_estimate": 0,
                "parallel_time_actual": 0,
                "speedup": 0
            }
        }
        
        self.start_time = None
        self.agent_timings: List[Dict[str, Any]] = []
    
    def start(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.metrics["start_time"] = datetime.utcnow().isoformat()
    
    def record_agent(
        self,
        agent_id: str,
        agent_name: str,
        duration: float,
        success: bool,
        error: Optional[str] = None
    ):
        """
        Record metrics for a single agent execution.
        
        Args:
            agent_id: Agent identifier
            agent_name: Agent name
            duration: Execution duration in seconds
            success: Whether execution was successful
            error: Optional error message
        """
        agent_metric = {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "duration": duration,
            "success": success,
            "start_time": None,
            "end_time": None
        }
        
        if error:
            agent_metric["error"] = error
        
        self.metrics["agents"][agent_id] = agent_metric
        self.agent_timings.append({
            "agent_id": agent_id,
            "duration": duration,
            "success": success
        })
    
    def finish(self, max_parallel: int):
        """
        Finish monitoring and calculate aggregate metrics.
        
        Args:
            max_parallel: Maximum number of parallel agents
        """
        end_time = time.time()
        self.metrics["end_time"] = datetime.utcnow().isoformat()
        
        if self.start_time:
            total_duration = end_time - self.start_time
            self.metrics["total_duration"] = total_duration
        
        # Calculate parallelism metrics
        self.metrics["parallelism"]["max_parallel"] = max_parallel
        self.metrics["parallelism"]["total_agents"] = len(self.agent_timings)
        
        if self.agent_timings:
            # Calculate average parallelism (simplified)
            total_agent_time = sum(t["duration"] for t in self.agent_timings)
            if total_duration > 0:
                self.metrics["parallelism"]["average_parallel"] = total_agent_time / total_duration
        
        # Calculate throughput
        if total_duration > 0:
            self.metrics["throughput"]["agents_per_second"] = len(self.agent_timings) / total_duration
        self.metrics["throughput"]["total_agents"] = len(self.agent_timings)
        
        # Calculate efficiency (speedup)
        sequential_estimate = sum(t["duration"] for t in self.agent_timings)
        parallel_actual = total_duration
        
        self.metrics["efficiency"]["sequential_time_estimate"] = sequential_estimate
        self.metrics["efficiency"]["parallel_time_actual"] = parallel_actual
        
        if parallel_actual > 0:
            speedup = sequential_estimate / parallel_actual
            self.metrics["efficiency"]["speedup"] = speedup
        
        # Save metrics
        self._save_metrics()
    
    def _save_metrics(self):
        """Save performance metrics to file."""
        metrics_file = self.output_dir / f"performance-{self.task_id}.json"
        try:
            with open(metrics_file, "w") as f:
                json.dump(self.metrics, f, indent=2)
            logger.info(f"Performance metrics saved to {metrics_file}")
        except Exception as e:
            logger.error(f"Failed to save performance metrics: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return self.metrics.copy()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        return {
            "task_id": self.task_id,
            "total_duration": self.metrics.get("total_duration"),
            "total_agents": self.metrics["parallelism"]["total_agents"],
            "successful_agents": sum(1 for a in self.metrics["agents"].values() if a.get("success")),
            "failed_agents": sum(1 for a in self.metrics["agents"].values() if not a.get("success")),
            "speedup": self.metrics["efficiency"].get("speedup"),
            "agents_per_second": self.metrics["throughput"].get("agents_per_second")
        }


def create_performance_monitor(task_id: str, output_dir: Path) -> PerformanceMonitor:
    """
    Convenience function to create a performance monitor.
    
    Args:
        task_id: Task identifier
        output_dir: Output directory
    
    Returns:
        PerformanceMonitor instance
    """
    return PerformanceMonitor(task_id, output_dir)

