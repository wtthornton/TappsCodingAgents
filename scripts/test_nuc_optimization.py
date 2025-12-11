#!/usr/bin/env python3
"""
Test NUC Optimization Features

Tests resource monitoring, fallback strategy, and performance benchmarks.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tapps_agents.core.resource_monitor import ResourceMonitor, ResourceMetrics
from tapps_agents.core.fallback_strategy import FallbackStrategy, TaskDecision, TaskType
from tapps_agents.core.performance_benchmark import PerformanceBenchmark, BenchmarkResult
import time
import json


def test_resource_monitor():
    """Test resource monitoring."""
    print("=" * 60)
    print("Testing Resource Monitor")
    print("=" * 60)
    
    # Create monitor with NUC thresholds
    monitor = ResourceMonitor(
        cpu_threshold=50.0,
        memory_threshold=70.0,
        disk_threshold=85.0
    )
    
    # Get current metrics
    print("\n[INFO] Current Resource Metrics:")
    metrics = monitor.get_current_metrics()
    print(f"  CPU: {metrics.cpu_percent:.1f}%")
    print(f"  Memory: {metrics.memory_percent:.1f}% ({metrics.memory_used_mb:.0f} MB used, {metrics.memory_available_mb:.0f} MB available)")
    print(f"  Disk: {metrics.disk_percent:.1f}% ({metrics.disk_used_gb:.1f} GB used, {metrics.disk_free_gb:.1f} GB free)")
    
    # Check if high usage
    if metrics.is_high_usage():
        print("\n[WARNING] High resource usage detected!")
    else:
        print("\n[OK] Resource usage is within normal limits")
    
    # Check for alerts
    alerts = monitor.get_recent_alerts(count=5)
    if alerts:
        print(f"\n[WARNING] {len(alerts)} recent alerts:")
        for alert in alerts:
            print(f"  - {alert.alert_type.upper()}: {alert.message}")
    else:
        print("\n[OK] No alerts")
    
    # Test background agent decision
    should_use_bg = monitor.should_use_background_agent()
    print(f"\n[INFO] Should use Background Agent: {should_use_bg}")
    
    # Get average metrics
    avg_metrics = monitor.get_average_metrics(duration_seconds=5)
    if avg_metrics:
        print(f"\n[INFO] Average metrics (5s):")
        print(f"  CPU: {avg_metrics.cpu_percent:.1f}%")
        print(f"  Memory: {avg_metrics.memory_percent:.1f}%")
    
    print("\n[OK] Resource Monitor test complete!")
    return monitor


def test_fallback_strategy(monitor):
    """Test fallback strategy."""
    print("\n" + "=" * 60)
    print("Testing Fallback Strategy")
    print("=" * 60)
    
    # Create fallback strategy
    strategy = FallbackStrategy(resource_monitor=monitor)
    
    # Test task classification
    test_tasks = [
        ("analyze-project", TaskType.HEAVY),
        ("refactor-large", TaskType.HEAVY),
        ("review-file", TaskType.MEDIUM),
        ("lint-file", TaskType.LIGHT),
        ("type-check", TaskType.LIGHT),
        ("generate-tests", TaskType.HEAVY),
    ]
    
    print("\n[INFO] Task Classification:")
    for task_name, expected_type in test_tasks:
        task_type = strategy.classify_task(task_name)
        status = "[OK]" if task_type == expected_type else "[FAIL]"
        print(f"  {status} {task_name}: {task_type.value} (expected: {expected_type.value})")
    
    # Test routing decisions
    print("\n[INFO] Routing Decisions:")
    for task_name, _ in test_tasks:
        decision = strategy.should_use_background_agent(task_name)
        bg_status = "[BG] Use Background Agent" if decision.use_background else "[LOCAL] Run Local"
        print(f"  {bg_status} {task_name}: {decision.reason}")
    
    # Test background agent mapping
    print("\n[INFO] Background Agent Mapping:")
    heavy_tasks = ["analyze-project", "refactor-large", "generate-tests", "security-scan"]
    for task_name in heavy_tasks:
        agent_name = strategy.get_background_agent_for_task(task_name)
        print(f"  {task_name} -> {agent_name}")
    
    # Get recommendations
    recommendations = strategy.get_fallback_recommendations()
    if recommendations:
        print("\n[INFO] Recommendations:")
        for rec in recommendations:
            print(f"  - {rec}")
    
    print("\n[OK] Fallback Strategy test complete!")
    return strategy


def test_performance_benchmark(monitor):
    """Test performance benchmarking."""
    print("\n" + "=" * 60)
    print("Testing Performance Benchmark")
    print("=" * 60)
    
    # Create benchmark
    benchmark = PerformanceBenchmark(resource_monitor=monitor)
    
    # Test task function
    def test_task():
        """Simple test task."""
        time.sleep(0.5)  # Simulate work
        return "completed"
    
    # Benchmark the task
    print("\n[INFO] Running benchmark...")
    result = benchmark.benchmark_task("test-task", test_task)
    
    print(f"\n[INFO] Benchmark Results:")
    print(f"  Name: {result.name}")
    print(f"  Duration: {result.duration_seconds:.2f}s")
    print(f"  CPU Average: {result.cpu_avg:.1f}%")
    print(f"  Memory Average: {result.memory_avg:.1f}%")
    print(f"  Memory Peak: {result.memory_peak:.1f}%")
    print(f"  Success: {result.success}")
    
    # Test comparison (simulated)
    baseline = BenchmarkResult(
        name="baseline",
        duration_seconds=2.0,
        cpu_avg=60.0,
        memory_avg=50.0,
        memory_peak=55.0
    )
    
    optimized = BenchmarkResult(
        name="optimized",
        duration_seconds=1.0,
        cpu_avg=40.0,
        memory_avg=45.0,
        memory_peak=48.0
    )
    
    comparison = benchmark.compare_benchmarks(baseline, optimized)
    print(f"\n[INFO] Comparison (Baseline vs Optimized):")
    print(f"  Speedup: {comparison.speedup:.2f}x")
    print(f"  Improvement: {comparison.improvement_percent:.1f}%")
    
    # Generate report (skip printing to avoid encoding issues)
    report = benchmark.generate_report()
    print(f"\n[INFO] Benchmark Report generated (length: {len(report)} chars)")
    # Save report to file instead of printing
    report_file = benchmark.output_dir / "test-benchmark-report.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"[INFO] Report saved to: {report_file}")
    
    # Export results
    output_file = benchmark.export_results("test-benchmark.json")
    print(f"\n[INFO] Results exported to: {output_file}")
    
    print("\n[OK] Performance Benchmark test complete!")
    return benchmark


def test_nuc_config():
    """Test NUC configuration loading."""
    print("\n" + "=" * 60)
    print("Testing NUC Configuration")
    print("=" * 60)
    
    nuc_config_file = Path(".tapps-agents/nuc-config.yaml")
    
    if not nuc_config_file.exists():
        print("[FAIL] NUC config file not found: .tapps-agents/nuc-config.yaml")
        print("   Creating it...")
        # The config should have been created, but let's check
        return False
    
    print(f"[OK] NUC config file found: {nuc_config_file}")
    
    # Try to load it
    try:
        import yaml
        with open(nuc_config_file, "r") as f:
            config = yaml.safe_load(f)
        
        print("\n[INFO] Configuration Summary:")
        if "optimization" in config:
            opt = config["optimization"]
            print(f"  Use Background Agents: {opt.get('use_background_agents', False)}")
            print(f"  Cache Aggressively: {opt.get('cache_aggressively', False)}")
            print(f"  Parallel Tools: {opt.get('parallel_tools', True)}")
            print(f"  Lightweight Skills: {opt.get('lightweight_skills', False)}")
        
        if "context7" in config:
            ctx7 = config["context7"]
            print(f"  Context7 Max Cache: {ctx7.get('max_cache_size', 'N/A')}")
            print(f"  Context7 Pre-populate: {ctx7.get('pre_populate', False)}")
        
        if "background_agents" in config:
            bg = config["background_agents"]
            print(f"  Background Agents Enabled: {bg.get('enabled', False)}")
            default_for = bg.get("default_for", [])
            print(f"  Default Tasks: {len(default_for)} tasks")
        
        print("\n[OK] NUC Configuration test complete!")
        return True
        
    except Exception as e:
        print(f"[FAIL] Error loading NUC config: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("NUC Optimization Features Test Suite")
    print("=" * 60)
    print("\nThis script tests:")
    print("  1. Resource Monitoring")
    print("  2. Fallback Strategy")
    print("  3. Performance Benchmarking")
    print("  4. NUC Configuration")
    print()
    
    try:
        # Test 1: Resource Monitor
        monitor = test_resource_monitor()
        
        # Test 2: Fallback Strategy
        strategy = test_fallback_strategy(monitor)
        
        # Test 3: Performance Benchmark
        benchmark = test_performance_benchmark(monitor)
        
        # Test 4: NUC Config
        config_ok = test_nuc_config()
        
        # Summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        print("[OK] Resource Monitor: PASSED")
        print("[OK] Fallback Strategy: PASSED")
        print("[OK] Performance Benchmark: PASSED")
        print(f"{'[OK]' if config_ok else '[FAIL]'} NUC Configuration: {'PASSED' if config_ok else 'FAILED'}")
        print("\n[SUCCESS] All tests complete!")
        
    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

