"""
Performance Benchmarks for NUC Optimization

Measures and compares performance before/after optimization.
"""

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .resource_monitor import ResourceMonitor


@dataclass
class BenchmarkResult:
    """Result of a performance benchmark."""

    name: str
    duration_seconds: float
    cpu_avg: float
    memory_avg: float
    memory_peak: float
    cache_hits: int = 0
    cache_misses: int = 0
    api_calls: int = 0
    success: bool = True
    error: str | None = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class BenchmarkComparison:
    """Comparison between two benchmark runs."""

    baseline: BenchmarkResult
    optimized: BenchmarkResult
    improvement_percent: float
    speedup: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "baseline": self.baseline.to_dict(),
            "optimized": self.optimized.to_dict(),
            "improvement_percent": self.improvement_percent,
            "speedup": self.speedup,
        }


class PerformanceBenchmark:
    """Performance benchmarking for NUC optimization."""

    def __init__(
        self,
        resource_monitor: ResourceMonitor | None = None,
        output_dir: Path | None = None,
    ):
        """
        Initialize performance benchmark.

        Args:
            resource_monitor: Optional ResourceMonitor instance
            output_dir: Output directory for benchmark results
        """
        self.resource_monitor = resource_monitor or ResourceMonitor()
        self.output_dir = output_dir or Path(".tapps-agents/benchmarks")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.results: list[BenchmarkResult] = []

    def benchmark_task(self, name: str, task_func, *args, **kwargs) -> BenchmarkResult:
        """
        Benchmark a task function.

        Args:
            name: Benchmark name
            task_func: Function to benchmark
            *args: Arguments for task function
            **kwargs: Keyword arguments for task function

        Returns:
            BenchmarkResult
        """
        # Start resource monitoring
        if self.resource_monitor:
            self.resource_monitor.get_current_metrics()  # Initial measurement

        # Run task and measure time
        start_time = time.time()
        start_metrics = (
            self.resource_monitor.get_current_metrics()
            if self.resource_monitor
            else None
        )

        try:
            task_func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            success = False
            error = str(e)

        end_time = time.time()
        duration = end_time - start_time

        # Get resource metrics
        if self.resource_monitor:
            end_metrics = self.resource_monitor.get_current_metrics()

            # Get average metrics during task
            avg_metrics = self.resource_monitor.get_average_metrics(
                duration_seconds=int(duration)
            )

            cpu_avg = avg_metrics.cpu_percent if avg_metrics else 0.0
            memory_avg = avg_metrics.memory_percent if avg_metrics else 0.0
            memory_peak = max(
                start_metrics.memory_percent if start_metrics else 0.0,
                end_metrics.memory_percent if end_metrics else 0.0,
            )
        else:
            cpu_avg = 0.0
            memory_avg = 0.0
            memory_peak = 0.0

        benchmark_result = BenchmarkResult(
            name=name,
            duration_seconds=duration,
            cpu_avg=cpu_avg,
            memory_avg=memory_avg,
            memory_peak=memory_peak,
            success=success,
            error=error,
        )

        self.results.append(benchmark_result)
        return benchmark_result

    def compare_benchmarks(
        self, baseline: BenchmarkResult, optimized: BenchmarkResult
    ) -> BenchmarkComparison:
        """
        Compare two benchmark results.

        Args:
            baseline: Baseline benchmark result
            optimized: Optimized benchmark result

        Returns:
            BenchmarkComparison
        """
        if baseline.duration_seconds == 0:
            speedup = 0.0
            improvement = 0.0
        else:
            speedup = baseline.duration_seconds / optimized.duration_seconds
            improvement = (
                (baseline.duration_seconds - optimized.duration_seconds)
                / baseline.duration_seconds
            ) * 100

        return BenchmarkComparison(
            baseline=baseline,
            optimized=optimized,
            improvement_percent=improvement,
            speedup=speedup,
        )

    def export_results(self, filename: str | None = None):
        """
        Export benchmark results to file.

        Args:
            filename: Optional filename (default: benchmarks-{timestamp}.json)
        """
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
            filename = f"benchmarks-{timestamp}.json"

        output_file = self.output_dir / filename

        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "results": [r.to_dict() for r in self.results],
            "summary": {
                "total_benchmarks": len(self.results),
                "successful": sum(1 for r in self.results if r.success),
                "failed": sum(1 for r in self.results if not r.success),
                "avg_duration": (
                    sum(r.duration_seconds for r in self.results) / len(self.results)
                    if self.results
                    else 0.0
                ),
                "avg_cpu": (
                    sum(r.cpu_avg for r in self.results) / len(self.results)
                    if self.results
                    else 0.0
                ),
                "avg_memory": (
                    sum(r.memory_avg for r in self.results) / len(self.results)
                    if self.results
                    else 0.0
                ),
            },
        }

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        return output_file

    def generate_report(self) -> str:
        """
        Generate a text report of benchmark results.

        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 60)
        report.append("Performance Benchmark Report")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.utcnow().isoformat()}")
        report.append("")

        if not self.results:
            report.append("No benchmark results available.")
            return "\n".join(report)

        # Summary
        report.append("Summary:")
        report.append("-" * 60)
        successful = sum(1 for r in self.results if r.success)
        failed = len(self.results) - successful
        report.append(f"  Total Benchmarks: {len(self.results)}")
        report.append(f"  Successful: {successful}")
        report.append(f"  Failed: {failed}")

        if successful > 0:
            avg_duration = (
                sum(r.duration_seconds for r in self.results if r.success) / successful
            )
            avg_cpu = sum(r.cpu_avg for r in self.results if r.success) / successful
            avg_memory = (
                sum(r.memory_avg for r in self.results if r.success) / successful
            )
            report.append(f"  Average Duration: {avg_duration:.2f}s")
            report.append(f"  Average CPU: {avg_cpu:.1f}%")
            report.append(f"  Average Memory: {avg_memory:.1f}%")

        report.append("")

        # Individual results
        report.append("Benchmark Results:")
        report.append("-" * 60)
        for result in self.results:
            status = "[OK]" if result.success else "[FAIL]"
            report.append(f"{status} {result.name}:")
            report.append(f"    Duration: {result.duration_seconds:.2f}s")
            report.append(f"    CPU: {result.cpu_avg:.1f}%")
            report.append(
                f"    Memory: {result.memory_avg:.1f}% (peak: {result.memory_peak:.1f}%)"
            )
            if result.error:
                report.append(f"    Error: {result.error}")
            report.append("")

        report.append("=" * 60)

        return "\n".join(report)


def create_performance_benchmark(
    resource_monitor: ResourceMonitor | None = None,
    output_dir: Path | None = None,
) -> PerformanceBenchmark:
    """
    Convenience function to create a performance benchmark.

    Args:
        resource_monitor: Optional ResourceMonitor
        output_dir: Optional output directory

    Returns:
        PerformanceBenchmark instance
    """
    return PerformanceBenchmark(
        resource_monitor=resource_monitor, output_dir=output_dir
    )
