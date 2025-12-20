# Multi-Agent Orchestration Guide

**TappsCodingAgents + Cursor AI Multi-Agent System**

This guide explains how to use TappsCodingAgents with Cursor AI's multi-agent system for parallel execution of multiple agents.

---

## Overview

Multi-Agent Orchestration enables parallel execution of multiple agents, significantly reducing execution time for complex tasks. TappsCodingAgents provides:

- ✅ **Parallel Execution**: Run 4-8 agents simultaneously
- ✅ **Conflict Resolution**: Git worktrees prevent file conflicts
- ✅ **Result Aggregation**: Automatic aggregation of results from all agents
- ✅ **Performance Monitoring**: Track execution time, speedup, and throughput
- ✅ **Workflow Definitions**: YAML-based multi-agent workflows

---

## Prerequisites

1. **Cursor AI IDE** with multi-agent support
2. **TappsCodingAgents** installed (see [QUICK_START.md](../QUICK_START.md))
3. **Git repository** initialized (for worktree support)

---

## Multi-Agent Workflows

### Workflow Structure

Multi-agent workflows are defined in YAML format using standard `steps` with dependency-based parallelism:

```yaml
workflow:
  id: multi-agent-review-and-test
  name: "Multi-Agent Review and Test Workflow"
  version: "2.0"
  
  steps:
    - id: auth-reviewer
      agent: reviewer
      action: review_code
      requires: []  # No dependencies = runs immediately in parallel
      creates: [auth-review-report.json]
      
    - id: api-reviewer
      agent: reviewer
      action: review_code
      requires: []  # No dependencies = runs in parallel with auth-reviewer
      creates: [api-review-report.json]
```

### Available Multi-Agent Workflows

1. **Multi-Agent Review and Test** (`multi-agent-review-and-test.yaml`)
   - Reviews multiple services in parallel
   - Generates tests for each service
   - Creates documentation

2. **Multi-Agent Refactor** (`multi-agent-refactor.yaml`)
   - Refactors multiple components concurrently
   - Reviews refactored code
   - Aggregates results

---

## Usage

### Triggering Multi-Agent Workflows

Multi-agent workflows can be triggered via:

1. **Orchestrator Agent**:
   ```
   @orchestrator *workflow-start multi-agent-review-and-test
   ```

2. **Natural Language**:
   ```
   "Review all services and generate tests in parallel"
   ```

3. **CLI**:
   ```bash
   python -m tapps_agents.cli orchestrator workflow-start multi-agent-review-and-test
   ```

### Programmatic Usage

```python
from tapps_agents.core.multi_agent_orchestrator import execute_multi_agent_workflow

# Define agent tasks
agent_tasks = [
    {
        "agent_id": "auth-reviewer",
        "agent": "reviewer",
        "command": "review",
        "target": "services/auth/",
        "args": {"format": "json"}
    },
    {
        "agent_id": "api-reviewer",
        "agent": "reviewer",
        "command": "review",
        "target": "services/api/",
        "args": {"format": "json"}
    }
]

# Execute in parallel
results = await execute_multi_agent_workflow(
    agent_tasks,
    max_parallel=8
)
```

---

## Conflict Resolution

### Git Worktrees

Each agent runs in its own git worktree to prevent file conflicts:

- **Worktree Creation**: Automatic worktree creation per agent
- **Isolation**: Each agent has isolated working directory
- **Cleanup**: Worktrees automatically removed after execution

### Worktree Structure

```
.tapps-agents/worktrees/
├── auth-reviewer/      # Worktree for auth reviewer
├── api-reviewer/       # Worktree for api reviewer
└── payment-reviewer/   # Worktree for payment reviewer
```

---

## Result Aggregation

Results from all agents are automatically aggregated:

### Aggregated Result Structure

```json
{
  "success": true,
  "timestamp": "2025-12-10T10:00:00Z",
  "total_agents": 6,
  "successful_agents": 6,
  "failed_agents": 0,
  "results": {
    "auth-reviewer": {
      "agent_id": "auth-reviewer",
      "agent": "reviewer",
      "success": true,
      "result": {...}
    },
    "api-reviewer": {
      "agent_id": "api-reviewer",
      "agent": "reviewer",
      "success": true,
      "result": {...}
    }
  },
  "summary": {
    "reviewer": {
      "total": 3,
      "successful": 3,
      "failed": 0
    },
    "tester": {
      "total": 3,
      "successful": 3,
      "failed": 0
    }
  },
  "performance_summary": {
    "total_duration": 45.2,
    "speedup": 3.5,
    "agents_per_second": 0.13
  }
}
```

### Result Files

- **Aggregated Results**: `.tapps-agents/reports/{task-id}-aggregated.json`
- **Performance Metrics**: `.tapps-agents/reports/performance-{task-id}.json`
- **Progress Reports**: `.tapps-agents/reports/progress-{task-id}.json`

---

## Performance Monitoring

### Performance Metrics

The system tracks:

- **Total Duration**: Time for all agents to complete
- **Speedup**: Ratio of sequential time to parallel time
- **Throughput**: Agents executed per second
- **Per-Agent Metrics**: Duration, success status, errors

### Performance Summary

```json
{
  "task_id": "multi-agent-123",
  "total_duration": 45.2,
  "total_agents": 6,
  "successful_agents": 6,
  "failed_agents": 0,
  "speedup": 3.5,
  "agents_per_second": 0.13
}
```

### Speedup Calculation

```
Speedup = Sequential Time / Parallel Time

Example:
- Sequential: 158 seconds (6 agents × ~26s each)
- Parallel: 45 seconds
- Speedup: 3.5x
```

---

## Best Practices

### 1. Task Granularity

Break tasks into independent, parallelizable units:

```
# Good
- Review service A
- Review service B
- Review service C

# Avoid
- Review entire project (too large)
- Tasks with dependencies (must be sequential)
```

### 2. Parallelism Limits

- **Recommended**: 4-8 parallel agents
- **Maximum**: 8-12 agents (system dependent)
- **Consider**: System resources (CPU, memory, I/O)

### 3. Dependency Management

Use `requires` dependencies to handle step ordering:

```yaml
steps:
  - id: refactor
    agent: improver
    action: refactor_code
    requires: []
    creates: [services/auth/]
    
  - id: review
    agent: reviewer
    action: review_code
    requires: [services/auth/]  # Wait for refactor to complete
    creates: [review-report.json]
```

### 4. Resource Management

- **Worktree Cleanup**: Automatic cleanup after execution
- **Memory Usage**: Monitor memory for large parallel executions
- **I/O Bottlenecks**: Consider I/O limits when running many agents

---

## Examples

### Example 1: Parallel Service Review

**Workflow**: `multi-agent-review-and-test.yaml`

**Execution**:
```bash
python -m tapps_agents.cli orchestrator workflow-start multi-agent-review-and-test
```

**Result**:
- 3 services reviewed in parallel
- 3 test suites generated in parallel
- Documentation generated
- Results aggregated
- **Speedup**: 3.5x faster than sequential

### Example 2: Parallel Refactoring

**Workflow**: `multi-agent-refactor.yaml`

**Execution**:
```bash
python -m tapps_agents.cli orchestrator workflow-start multi-agent-refactor
```

**Result**:
- 3 services refactored in parallel
- 3 reviews completed after refactoring
- Results aggregated
- **Speedup**: 4.2x faster than sequential

---

## Troubleshooting

### Agents Not Running in Parallel

1. **Check Dependencies**: Steps with no `requires` dependencies run in parallel automatically
2. **Check Limits**: Default max parallel is 8 steps (configurable via `ParallelStepExecutor`)
3. **Check Dependencies**: Remove unnecessary `requires` constraints to enable parallelism

### File Conflicts

1. **Worktree Issues**: Check worktree creation/cleanup
2. **Git Status**: Ensure git repository is clean
3. **Manual Cleanup**: Remove worktrees manually if needed

### Performance Issues

1. **Too Many Parallel Steps**: Reduce `max_parallel` in `ParallelStepExecutor` (default: 8)
2. **Resource Limits**: Check CPU/memory usage
3. **I/O Bottlenecks**: Consider disk I/O limits

---

## Advanced Configuration

### Custom Multi-Agent Workflow

Create custom workflow in `workflows/`:

```yaml
workflow:
  id: custom-multi-agent
  name: "Custom Multi-Agent Workflow"
  version: "2.0"
  
  steps:
    - id: task1
      agent: reviewer
      action: review_code
      requires: []  # No dependencies = runs immediately
      creates: [task1-report.json]
    
    - id: task2
      agent: reviewer
      action: review_code
      requires: []  # Runs in parallel with task1
      creates: [task2-report.json]
```

### Performance Tuning

Parallelism is controlled by the `ParallelStepExecutor` class (default: 8 concurrent steps). To adjust:

- Modify `max_parallel` parameter in `ParallelStepExecutor` initialization
- Steps automatically run in parallel when dependencies allow (up to the limit)
- No workflow-level configuration needed - parallelism is automatic based on dependencies

---

## See Also

- [BACKGROUND_AGENTS_GUIDE.md](BACKGROUND_AGENTS_GUIDE.md) - Background Agents
- [CURSOR_AI_INTEGRATION_PLAN_2025.md](CURSOR_AI_INTEGRATION_PLAN_2025.md) - Full integration plan
- [QUICK_START.md](../QUICK_START.md) - Quick start guide

