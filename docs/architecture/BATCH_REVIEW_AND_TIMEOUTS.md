# Batch Review and Timeout Configuration

**Last Updated**: January 2025  
**Related**: `tapps_agents/agents/reviewer/batch_review.py`, `tapps_agents/agents/reviewer/phased_review.py`

## Overview

The batch review workflow supports reviewing multiple services in parallel with configurable timeouts to prevent hanging operations.

## Timeout Configuration

### Default Timeout

By default, each service review has a **5-minute timeout** (300 seconds):

```python
from tapps_agents.agents.reviewer.batch_review import BatchReviewWorkflow, DEFAULT_REVIEW_TIMEOUT

# Default timeout constant
print(DEFAULT_REVIEW_TIMEOUT)  # 300.0 seconds
```

### Custom Timeout

You can configure a custom timeout when creating a `BatchReviewWorkflow`:

```python
from pathlib import Path
from tapps_agents.agents.reviewer.batch_review import BatchReviewWorkflow

workflow = BatchReviewWorkflow(
    project_root=Path.cwd(),
    max_parallel=4,
    review_timeout=600.0  # 10 minutes per service
)
```

### Timeout Behavior

- **Per-Service Timeout**: Each service review has its own timeout
- **Graceful Failure**: If a timeout occurs, the service review returns a failed result with a timeout error message
- **Parallel Execution**: Other services continue reviewing even if one times out
- **Error Handling**: Timeout errors are logged and included in the batch results

```python
# Timeout handling example
try:
    review_result = await asyncio.wait_for(
        reviewer.review_file(file_path, include_scoring=True),
        timeout=self.review_timeout,
    )
except asyncio.TimeoutError:
    logger.error(f"Review timeout ({self.review_timeout}s) exceeded for service {service.name}")
    return ServiceReviewResult(
        service_name=service.name,
        passed=False,
        overall_score=0.0,
        error=f"Review timeout after {self.review_timeout} seconds",
    )
```

## Batch Review Workflow

### Basic Usage

```python
from pathlib import Path
from tapps_agents.agents.reviewer.batch_review import BatchReviewWorkflow
from tapps_agents.agents.reviewer.service_discovery import ServiceDiscovery

# Discover services
discovery = ServiceDiscovery(project_root=Path.cwd())
services = discovery.discover_services_with_priority(prioritize=True)

# Create workflow with timeout
workflow = BatchReviewWorkflow(
    project_root=Path.cwd(),
    max_parallel=4,  # Max concurrent reviews
    review_timeout=300.0  # 5 minutes per service
)

# Review all services
result = await workflow.review_services(
    services=services,
    parallel=True,  # Use parallel execution
    include_scoring=True,
    include_llm_feedback=True
)

print(f"Services reviewed: {result.services_reviewed}")
print(f"Passed: {result.passed}, Failed: {result.failed}")
print(f"Average score: {result.average_score:.2f}")

# Check for timeout errors
for service_result in result.results:
    if service_result.error and "timeout" in service_result.error.lower():
        print(f"Timeout: {service_result.service_name}")
```

## Phased Review Strategy

Phased reviews also respect the timeout configuration through the underlying `BatchReviewWorkflow`:

```python
from tapps_agents.agents.reviewer.phased_review import PhasedReviewStrategy
from tapps_agents.agents.reviewer.service_discovery import Priority

strategy = PhasedReviewStrategy(
    project_root=Path.cwd(),
    max_parallel=4  # Max parallel reviews per phase
)

# Execute phased review (timeouts apply to each service in each phase)
result = await strategy.execute_phased_review(
    review_id="my-review",
    phases=[Priority.CRITICAL, Priority.HIGH, Priority.MEDIUM, Priority.LOW],
    resume=True,
    parallel=True
)
```

## Best Practices

### Choosing a Timeout

- **Small Services** (< 1000 LOC): 2-5 minutes (120-300 seconds)
- **Medium Services** (1000-5000 LOC): 5-10 minutes (300-600 seconds)
- **Large Services** (> 5000 LOC): 10-15 minutes (600-900 seconds)

### Monitoring Timeouts

Check timeout errors in batch results:

```python
timeout_count = sum(
    1 for r in result.results
    if r.error and "timeout" in r.error.lower()
)

if timeout_count > 0:
    print(f"Warning: {timeout_count} services timed out")
    # Consider increasing timeout or reviewing services individually
```

### Error Handling

All timeout errors are logged with full context:

```python
logger.error(
    f"Review timeout ({self.review_timeout}s) exceeded for service {service.name}"
)
```

Check logs for detailed timeout information during debugging.

## Configuration

### Environment Variables

You can set default timeout via configuration (future enhancement):

```yaml
# .tapps-agents/config.yaml
reviewer:
  batch_review:
    default_timeout: 600.0  # 10 minutes
    max_parallel: 4
```

### Programmatic Configuration

```python
from tapps_agents.core.config import load_config

config = load_config()
# Timeout configuration can be added to ProjectConfig in future versions
```

## Related Components

- **`BatchReviewWorkflow`**: Orchestrates parallel service reviews
- **`PhasedReviewStrategy`**: Reviews services in priority-based phases
- **`ServiceDiscovery`**: Discovers and prioritizes services
- **`ReviewerAgent`**: Performs individual service reviews

## See Also

- [API Reference](../API.md#batch-review-workflow)
- [Service Discovery](SERVICE_DISCOVERY.md)
- [Phased Review Strategy](PHASED_REVIEW.md)

