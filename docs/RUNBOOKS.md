# Operational Runbooks

**Version**: 2.4.1  
**Last Updated**: January 2026

This document provides operational procedures for common failure scenarios and data management in TappsCodingAgents.

## Table of Contents

1. [Agent Failures and Recovery](#agent-failures-and-recovery)
2. [Retry/Timeout Handling](#retrytimeout-handling)
3. [Dead Letter Queue (DLQ) Handling](#dead-letter-queue-dlq-handling)
4. [Cache Invalidation and Recovery](#cache-invalidation-and-recovery)
5. [Worktree Cleanup and Management](#worktree-cleanup-and-management)
6. [Workflow Stuck/Failed Recovery](#workflow-stuckfailed-recovery)
7. [Log and Trace Field Conventions](#log-and-trace-field-conventions)
8. [Data Retention Policies](#data-retention-policies)
9. [Cleanup Tools](#cleanup-tools)

## Agent Failures and Recovery

### Symptoms

- Agent execution returns `success: false` in results
- Error envelope in agent result with `recoverable: true` or `recoverable: false`
- Workflow step marked as `failed`

### Diagnosis

1. Check agent result for error envelope:
   ```python
   result = await agent.run(command, **kwargs)
   if not result.get("success"):
       error = result.get("error", {})
       print(f"Error code: {error.get('code')}")
       print(f"Error category: {error.get('category')}")
       print(f"Recoverable: {error.get('recoverable', False)}")
   ```

2. Review logs with correlation IDs:
   ```bash
   # Filter logs by workflow_id and step_id
   grep "workflow_id=workflow-123" logs.txt
   ```

3. Check error category:
   - **configuration**: Fix configuration and retry
   - **external_dependency**: Service may be temporarily unavailable
   - **validation**: Fix input parameters
   - **execution**: May require code changes
   - **permission**: Fix file permissions
   - **timeout**: Increase timeout or optimize operation

### Recovery Procedures

#### Recoverable Errors

If `recoverable: true` in error envelope:

1. **Configuration Errors**:
   ```bash
   # Fix configuration
   vim .tapps-agents/config.yaml
   # Retry workflow step
   python -m tapps_agents.cli workflow resume --workflow-id <id>
   ```

2. **External Dependency Errors**:
   - Wait for service to become available
   - Check service status
   - Retry with exponential backoff (automatic in workflow executor)

3. **Timeout Errors**:
   - Increase timeout in workflow step metadata
   - Optimize operation if possible
   - Retry workflow step

#### Non-Recoverable Errors

If `recoverable: false`:

1. Review error message and details
2. Check logs for full stack trace (if available)
3. Fix underlying issue (code, configuration, etc.)
4. Restart workflow from beginning or from failed step

### Prevention

- Enable quality gates in workflows
- Use appropriate timeout values
- Validate inputs before agent execution
- Monitor external dependencies

## Retry/Timeout Handling

### Automatic Retries

Workflow executor automatically retries failed steps based on retry configuration:

```yaml
steps:
  - id: critical-step
    agent: implementer
    action: generate-code
    retry:
      max_attempts: 3
      backoff_strategy: exponential
      initial_delay: 5  # seconds
      max_delay: 60     # seconds
    timeout: 300  # 5 minutes
```

### Manual Retry Procedures

1. **Resume Workflow**:
   ```bash
   python -m tapps_agents.cli workflow resume --workflow-id <id>
   ```

2. **Retry Specific Step**:
   - Edit workflow state to mark step as not completed
   - Resume workflow

3. **Skip Failed Step**:
   - Mark step as skipped in workflow state
   - Continue with next step

### Timeout Configuration

- **Default timeout**: 900 seconds (15 minutes)
- **Per-step timeout**: Configure in step metadata
- **Workflow timeout**: Configure at workflow level

## Dead Letter Queue (DLQ) Handling

### Overview

Failed workflow steps that cannot be automatically retried are recorded in workflow state with error envelopes.

### DLQ Inspection

1. **Check workflow state**:
   ```bash
   cat .tapps-agents/workflow-state/current_state.json | jq '.step_executions[] | select(.status == "failed")'
   ```

2. **Review error envelopes**:
   - Error code and category
   - Recoverable status
   - Correlation IDs

### DLQ Processing

1. **Categorize failures**:
   - Recoverable: Fix and retry
   - Non-recoverable: Requires investigation

2. **Batch processing**:
   - Group by error category
   - Process similar errors together

3. **Manual intervention**:
   - Review error details
   - Fix underlying issues
   - Retry or skip steps

## Cache Invalidation and Recovery

### Context7 Cache

#### Invalidation

1. **Manual invalidation**:
   ```bash
   # Clear specific library cache
   rm -rf .tapps-agents/context7/cache/<library-id>
   ```

2. **Full cache clear**:
   ```bash
   # Clear entire cache (use with caution)
   rm -rf .tapps-agents/context7/cache/*
   ```

#### Recovery

1. **Cache corruption**:
   - Remove corrupted cache entries
   - Cache will be repopulated on next access

2. **Cache warming**:
   - Run cache warming operation:
   ```bash
   python -m tapps_agents.cli context7 warm-cache
   ```

### Unified Cache

#### Invalidation

1. **Clear tiered context cache**:
   ```bash
   rm -rf .tapps-agents/cache/tiered-context/*
   ```

2. **Clear project profile cache**:
   ```bash
   rm -rf .tapps-agents/project-profile.yaml
   ```

## Worktree Cleanup and Management

### Automatic Cleanup

Worktrees are automatically cleaned up after workflow completion. Stuck worktrees may require manual cleanup.

### Manual Cleanup Procedures

1. **List worktrees**:
   ```bash
   ls -la .tapps-agents/worktrees/
   ```

2. **Remove specific worktree**:
   ```bash
   # Remove worktree directory
   rm -rf .tapps-agents/worktrees/<worktree-name>
   
   # Remove git worktree (if still registered)
   git worktree remove <worktree-path>
   ```

3. **Bulk cleanup**:
   ```bash
   # Remove all worktrees older than 7 days
   find .tapps-agents/worktrees -type d -mtime +7 -exec rm -rf {} +
   ```

### Prevention

- Ensure workflows complete successfully
- Monitor worktree directory size
- Set up automated cleanup jobs

## Workflow Stuck/Failed Recovery

### Symptoms

- Workflow status is `running` but no progress
- Workflow status is `failed` with error
- Workflow state file exists but workflow not executing

### Diagnosis

1. **Check workflow state**:
   ```bash
   cat .tapps-agents/workflow-state/current_state.json | jq '.status'
   ```

2. **Review step executions**:
   ```bash
   cat .tapps-agents/workflow-state/current_state.json | jq '.step_executions[] | select(.status == "running")'
   ```

3. **Check for locks**:
   ```bash
   ls -la .tapps-agents/workflow-state/*.lock
   ```

### Recovery Procedures

1. **Resume Workflow**:
   ```bash
   python -m tapps_agents.cli workflow resume --workflow-id <id>
   ```

2. **Reset Workflow State**:
   - Backup current state
   - Edit state file to reset status
   - Resume from appropriate step

3. **Force Cleanup**:
   - Remove lock files (if safe)
   - Clean up stuck worktrees
   - Restart workflow

### Prevention

- Use appropriate timeouts
- Monitor workflow execution
- Set up alerts for stuck workflows

## Log and Trace Field Conventions

### Standard Fields

All workflow and agent logs include these correlation fields:

- **workflow_id**: Unique workflow execution identifier
- **step_id**: Current workflow step identifier
- **agent**: Agent name executing the step
- **trace_id**: Distributed tracing identifier (optional)

### Field Naming Conventions

- Use snake_case for field names
- Use descriptive names (e.g., `workflow_id` not `wf_id`)
- Include units in field names when applicable (e.g., `duration_seconds`)

### Required vs Optional Fields

- **Required**: `workflow_id` (when in workflow context)
- **Optional**: `step_id`, `agent`, `trace_id`

### Examples

```python
# Workflow logger with all fields
logger = WorkflowLogger(
    workflow_id="workflow-123",
    step_id="step-1",
    agent="implementer",
    trace_id="trace-456"
)

logger.info("Step started", duration_seconds=5.2)
```

### JSON Structured Logging

When `TAPPS_AGENTS_STRUCTURED_LOGGING=true`:

```json
{
  "timestamp": "2026-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "tapps_agents.workflow.executor",
  "message": "Step started",
  "workflow_id": "workflow-123",
  "step_id": "step-1",
  "agent": "implementer",
  "trace_id": "trace-456",
  "duration_seconds": 5.2
}
```

## Data Retention Policies

### Artifacts

- **Workflow artifacts**: Retain for 30 days
- **Quality reports**: Retain for 90 days
- **Test results**: Retain for 30 days
- **Documentation artifacts**: Retain for 90 days

### Logs

- **Application logs**: Retain for 30 days
- **Structured logs (JSON)**: Retain for 90 days
- **Debug logs**: Retain for 7 days

### Metrics

- **Analytics history**: Retain for 90 days
- **Performance metrics**: Retain for 180 days
- **Confidence metrics**: Retain for 90 days

### Cache

- **Context7 cache**: No automatic expiration (manual cleanup)
- **Tiered context cache**: Retain for 30 days
- **Project profile**: Retain indefinitely (updated on changes)

### Worktrees

- **Completed worktrees**: Clean up immediately after workflow completion
- **Failed worktrees**: Retain for 7 days for debugging
- **Stuck worktrees**: Manual cleanup required

## Cleanup Tools

### Automated Cleanup Script

Create a cleanup script (`scripts/cleanup.py`):

```python
#!/usr/bin/env python3
"""Cleanup tool for TappsCodingAgents artifacts."""

import argparse
from datetime import datetime, timedelta
from pathlib import Path

def cleanup_artifacts(base_path: Path, days: int = 30, dry_run: bool = False):
    """Clean up artifacts older than specified days."""
    cutoff = datetime.now() - timedelta(days=days)
    
    # Clean up old worktrees
    worktrees_dir = base_path / ".tapps-agents" / "worktrees"
    if worktrees_dir.exists():
        for worktree in worktrees_dir.iterdir():
            if worktree.is_dir():
                mtime = datetime.fromtimestamp(worktree.stat().st_mtime)
                if mtime < cutoff:
                    if dry_run:
                        print(f"Would remove: {worktree}")
                    else:
                        print(f"Removing: {worktree}")
                        # Remove worktree safely
                        # (implementation depends on git worktree management)
    
    # Clean up old analytics
    analytics_dir = base_path / ".tapps-agents" / "analytics" / "history"
    if analytics_dir.exists():
        for log_file in analytics_dir.glob("*.jsonl"):
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if mtime < cutoff:
                if dry_run:
                    print(f"Would remove: {log_file}")
                else:
                    print(f"Removing: {log_file}")
                    log_file.unlink()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cleanup TappsCodingAgents artifacts")
    parser.add_argument("--days", type=int, default=30, help="Days to retain")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root")
    args = parser.parse_args()
    
    cleanup_artifacts(args.project_root, args.days, args.dry_run)
```

### Usage

```bash
# Dry run (preview)
python scripts/cleanup.py --days 30 --dry-run

# Actual cleanup
python scripts/cleanup.py --days 30
```

### Manual Cleanup Commands

```bash
# Remove old worktrees (older than 7 days)
find .tapps-agents/worktrees -type d -mtime +7 -exec rm -rf {} +

# Remove old analytics (older than 90 days)
find .tapps-agents/analytics/history -name "*.jsonl" -mtime +90 -delete

# Remove old quality reports (older than 90 days)
find reports/quality -name "*.html" -mtime +90 -delete
```

## Related Documentation

- `docs/DEPLOYMENT.md` - Deployment and configuration
- `docs/TROUBLESHOOTING.md` - Common issues and solutions
- `docs/CONFIGURATION.md` - Configuration reference
