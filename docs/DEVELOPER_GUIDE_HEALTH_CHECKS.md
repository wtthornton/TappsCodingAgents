# Developer Guide: Extending Health Checks

Guide for developers on how to add new health checks to the TappsCodingAgents health check system.

## Architecture Overview

The health check system consists of:

1. **Base Classes** (`health/base.py`): Abstract interface for health checks
2. **Registry** (`health/registry.py`): Manages health check registration and discovery
3. **Orchestrator** (`health/orchestrator.py`): Coordinates check execution and aggregation
4. **Dashboard** (`health/dashboard.py`): Renders health status
5. **Metrics Collector** (`health/collector.py`): Stores health metrics for trend analysis
6. **Check Modules** (`health/checks/`): Individual health check implementations

## Creating a New Health Check

### Step 1: Create Check Module

Create a new file in `tapps_agents/health/checks/`:

```python
"""Custom Health Check Example."""

from __future__ import annotations

from pathlib import Path

from ..base import HealthCheck, HealthCheckResult


class CustomHealthCheck(HealthCheck):
    """Health check for custom system component."""

    def __init__(self, project_root: Path | None = None):
        """
        Initialize custom health check.

        Args:
            project_root: Project root directory
        """
        super().__init__(
            name="custom",
            dependencies=["environment"]  # Optional: list of check names that must run first
        )
        self.project_root = project_root or Path.cwd()

    def run(self) -> HealthCheckResult:
        """
        Run the health check.

        Returns:
            HealthCheckResult with status, score, and details
        """
        try:
            # Perform health check logic
            # ...

            # Calculate score (0-100)
            score = 100.0  # Your calculation

            # Determine status
            if score >= 85.0:
                status = "healthy"
            elif score >= 70.0:
                status = "degraded"
            else:
                status = "unhealthy"

            return HealthCheckResult(
                name=self.name,
                status=status,
                score=score,
                message="Custom check message",
                details={
                    "key_metric": value,
                    # ... other details
                },
                remediation=["Action 1", "Action 2"] if issues else None,
            )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                score=0.0,
                message=f"Custom check failed: {e}",
                details={"error": str(e)},
                remediation=["Check system configuration"],
            )
```

### Step 2: Register Check

Add to `tapps_agents/health/checks/__init__.py`:

```python
from .custom import CustomHealthCheck

__all__ = [
    # ... existing checks
    "CustomHealthCheck",
]
```

### Step 3: Register in CLI

Update `tapps_agents/cli/commands/health.py`:

```python
from ...health.checks.custom import CustomHealthCheck

# In handle_health_check_command and handle_health_dashboard_command:
registry.register(CustomHealthCheck(project_root=project_root))
```

### Step 4: Add to CLI Parser (Optional)

If you want the check to be selectable via `--check`:

Update `tapps_agents/cli/parsers/top_level.py`:

```python
health_check_parser.add_argument(
    "--check",
    choices=[
        # ... existing choices
        "custom",
    ],
    help="Run a specific health check (default: all checks)",
)
```

## Health Check Interface

### HealthCheck Base Class

All health checks must inherit from `HealthCheck` and implement:

```python
def run(self) -> HealthCheckResult:
    """Run the health check and return result."""
    pass
```

### HealthCheckResult

The result must include:

- **name**: Check name (should match class name)
- **status**: "healthy", "degraded", or "unhealthy"
- **score**: 0-100 numeric score
- **message**: Human-readable status message
- **details**: Dictionary with check-specific metrics
- **remediation**: Optional list of remediation actions

### Status Thresholds

Standard thresholds:
- **Green (≥85)**: Healthy, all critical aspects working
- **Yellow (70-84)**: Degraded, functional but needs attention
- **Red (<70)**: Unhealthy, critical issues

### Dependencies

Health checks can declare dependencies:

```python
super().__init__(
    name="my_check",
    dependencies=["environment", "execution"]
)
```

Dependencies ensure checks run in the correct order. The orchestrator uses topological sorting to respect dependencies.

## Metrics Storage Format

Health metrics are stored as JSONL files in `.tapps-agents/health/metrics/`:

```json
{
  "check_name": "execution",
  "status": "healthy",
  "score": 95.5,
  "timestamp": "2025-01-15T10:30:00Z",
  "details": {
    "success_rate": 97.2,
    "total_executions": 150
  },
  "remediation": null,
  "message": "Success rate: 97.2% (146/150 workflows)"
}
```

## Integration Patterns

### Using Existing Systems

Health checks should leverage existing systems rather than duplicating logic:

```python
# Good: Use existing doctor report
from ...core.doctor import collect_doctor_report
report = collect_doctor_report()

# Good: Use existing metrics collector
from ...workflow.execution_metrics import ExecutionMetricsCollector
collector = ExecutionMetricsCollector()
metrics = collector.get_metrics()

# Bad: Don't duplicate doctor logic
# (implementing tool checks from scratch)
```

### Error Handling

Always wrap health check logic in try/except:

```python
def run(self) -> HealthCheckResult:
    try:
        # Check logic
        ...
    except Exception as e:
        return HealthCheckResult(
            name=self.name,
            status="unhealthy",
            score=0.0,
            message=f"Check failed: {e}",
            details={"error": str(e)},
        )
```

### Performance Considerations

- Health checks should complete quickly (<5 seconds)
- Use caching for expensive operations
- Consider parallel execution for independent checks
- Don't block on external services (use timeouts)

## Testing Health Checks

### Unit Tests

Test health checks independently:

```python
def test_custom_health_check():
    check = CustomHealthCheck(project_root=tmp_path)
    result = check.run()
    
    assert result.name == "custom"
    assert result.status in ["healthy", "degraded", "unhealthy"]
    assert 0 <= result.score <= 100
    assert result.message
```

### Integration Tests

Test with real systems:

```python
def test_custom_health_check_integration():
    # Setup test environment
    ...
    
    check = CustomHealthCheck(project_root=test_project)
    result = check.run()
    
    # Verify results match expected state
    ...
```

## Best Practices

1. **Clear Status Messages**: Messages should be actionable and specific
2. **Detailed Metrics**: Include key metrics in `details` for debugging
3. **Prioritized Remediation**: List most important actions first
4. **Graceful Degradation**: Handle missing dependencies gracefully
5. **Documentation**: Document what the check measures and why
6. **Consistent Scoring**: Use standard thresholds (85/70) for consistency

## Examples

See existing health checks for patterns:

- `health/checks/environment.py` - Extends existing doctor command
- `health/checks/execution.py` - Queries execution metrics
- `health/checks/context7_cache.py` - Uses Context7 analytics
- `health/checks/knowledge_base.py` - Checks file system and RAG status

## Metrics Storage Format

Health metrics use JSONL format (one JSON object per line):

```
{"check_name": "environment", "status": "healthy", "score": 95.0, ...}
{"check_name": "execution", "status": "degraded", "score": 78.5, ...}
```

Files are rotated daily: `health_YYYY-MM-DD.jsonl`

## Querying Metrics

Use `HealthMetricsCollector` to query stored metrics:

```python
from ...health.collector import HealthMetricsCollector

collector = HealthMetricsCollector()
metrics = collector.get_metrics(
    check_name="execution",
    status="unhealthy",
    days=7
)

summary = collector.get_summary(days=30)
trends = collector.get_trends(check_name="execution", days=7)
```

## See Also

- [Health Checks User Guide](HEALTH_CHECKS.md) - User-facing documentation
- [Base Health Check](tapps_agents/health/base.py) - Base class implementation
- [Health Orchestrator](tapps_agents/health/orchestrator.py) - Orchestration logic

