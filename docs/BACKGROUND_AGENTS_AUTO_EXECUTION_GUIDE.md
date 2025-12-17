# Background Agent Auto-Execution Guide

**TappsCodingAgents Background Agent Auto-Execution User Guide**

This guide explains how to set up and use Background Agent auto-execution for automatic workflow step execution.

---

## Overview

Background Agent auto-execution enables workflows to automatically progress through steps without manual intervention. When enabled, workflow steps are executed by Background Agents that monitor command files and execute them automatically.

**Key Features:**
- ✅ **Automatic Execution**: Workflow steps execute automatically via Background Agents
- ✅ **Polling-Based Completion**: Automatic detection of step completion
- ✅ **Metrics & Monitoring**: Comprehensive execution metrics and audit logging
- ✅ **Configuration Management**: Flexible configuration with feature flags
- ✅ **Health Checks**: System health validation and diagnostics

---

## Quick Start

### 1. Generate Background Agent Configuration

First, generate the Background Agent configuration file:

```bash
tapps-agents background-agent-config generate
```

This creates `.cursor/background-agents.yaml` with default settings.

### 2. Enable Auto-Execution

Enable auto-execution in your project configuration (`.tapps-agents/config.yaml`):

```yaml
workflow:
  auto_execution_enabled: true
  polling_interval: 5.0
  timeout_seconds: 3600
```

Or enable it per-workflow in your workflow YAML:

```yaml
metadata:
  auto_execution: true

steps:
  - step: Gather Requirements
    agent: analyst
    action: gather-requirements
    params:
      target_file: requirements.md
```

### 3. Run a Workflow

Execute a workflow with auto-execution enabled:

```bash
tapps-agents workflow execute --workflow my-workflow.yaml
```

The workflow will automatically progress through steps using Background Agents.

---

## Configuration

### Background Agent Configuration

The Background Agent configuration (`.cursor/background-agents.yaml`) defines which agents watch for command files:

```yaml
agents:
  - name: "TappsCodingAgents Workflow Executor"
    type: "background"
    commands:
      - "python -m tapps_agents.cli workflow execute-skill-command --command-file {command_file_path}"
    watch_paths:
      - ".cursor-skill-command.txt"
    enabled: true
    timeout_seconds: 3600
```

**Key Fields:**
- `name`: Agent name
- `type`: Must be `"background"`
- `commands`: Commands to execute when command file is detected
- `watch_paths`: Paths to watch for command files
- `enabled`: Enable/disable this agent
- `timeout_seconds`: Maximum execution time

### Auto-Execution Configuration

The auto-execution configuration (`.tapps-agents/auto_execution_config.yaml`) controls auto-execution behavior:

```yaml
auto_execution:
  enabled: true
  retry:
    enabled: true
    max_attempts: 3
    backoff_multiplier: 2.0
    initial_delay_seconds: 1.0
  polling:
    enabled: true
    interval_seconds: 5.0
    timeout_seconds: 3600.0
  features:
    artifact_detection: true
    status_tracking: true
    error_handling: true
    metrics_collection: true
    audit_logging: true
  version: "1.0"
```

**Configuration Options:**
- `enabled`: Enable/disable auto-execution globally
- `retry`: Retry configuration for failed executions
- `polling`: Polling interval and timeout settings
- `features`: Feature flags for various capabilities

---

## Monitoring

### Check Execution Status

View current execution status:

```bash
tapps-agents auto-execution status
```

Filter by workflow:

```bash
tapps-agents auto-execution status --workflow-id my-workflow
```

### View Execution History

View execution history:

```bash
tapps-agents auto-execution history
```

Limit results:

```bash
tapps-agents auto-execution history --limit 50
```

### View Metrics Summary

View execution metrics:

```bash
tapps-agents auto-execution metrics
```

Output includes:
- Total executions
- Success rate
- Average duration
- Retry count
- Status breakdown

### Run Health Checks

Check system health:

```bash
tapps-agents auto-execution health
```

Health checks validate:
- Background Agent configuration
- File system accessibility
- Status file access
- Command file access

### Enable Debug Mode

Enable verbose logging:

```bash
tapps-agents auto-execution debug on
```

Disable debug mode:

```bash
tapps-agents auto-execution debug off
```

Check debug status:

```bash
tapps-agents auto-execution debug status
```

---

## Usage Examples

### Example 1: Simple Workflow with Auto-Execution

**Workflow YAML (`my-workflow.yaml`):**

```yaml
id: my-workflow
name: My Workflow
metadata:
  auto_execution: true

steps:
  - step: Gather Requirements
    agent: analyst
    action: gather-requirements
    params:
      target_file: requirements.md

  - step: Design System
    agent: architect
    action: design-system
    params:
      target_file: design.md
```

**Execute:**

```bash
tapps-agents workflow execute --workflow my-workflow.yaml
```

The workflow will automatically execute both steps using Background Agents.

### Example 2: Workflow with Error Handling

**Workflow YAML:**

```yaml
id: robust-workflow
name: Robust Workflow
metadata:
  auto_execution: true

steps:
  - step: Analyze Code
    agent: reviewer
    action: review-code
    params:
      target_file: src/main.py
    on_error: continue  # Continue on error

  - step: Generate Tests
    agent: tester
    action: generate-tests
    params:
      target_file: tests/test_main.py
```

### Example 3: Conditional Execution

**Workflow YAML:**

```yaml
id: conditional-workflow
name: Conditional Workflow
metadata:
  auto_execution: true

steps:
  - step: Check Prerequisites
    agent: analyst
    action: check-prerequisites
    params:
      check_file: prerequisites.md

  - step: Build Application
    agent: implementer
    action: implement-feature
    condition: prerequisites_met  # Only if previous step succeeded
    params:
      target_file: src/app.py
```

---

## Troubleshooting

### Common Issues

#### 1. Auto-Execution Not Starting

**Symptoms:** Workflow steps not executing automatically.

**Solutions:**
- Verify Background Agent configuration exists: `cat .cursor/background-agents.yaml`
- Check auto-execution is enabled: `tapps-agents auto-execution health`
- Verify Background Agents are running in Cursor
- Check command file is created: `ls -la .cursor/.cursor-skill-command.txt`

#### 2. Execution Timeout

**Symptoms:** Steps timing out before completion.

**Solutions:**
- Increase timeout: Set `timeout_seconds` in configuration
- Check Background Agent is processing commands
- Verify status file is being created: `ls -la .cursor/.cursor-skill-status.json`
- Review execution logs: `tapps-agents auto-execution history`

#### 3. Status File Not Found

**Symptoms:** Polling never detects completion.

**Solutions:**
- Verify Background Agent is writing status files
- Check file permissions: `chmod 644 .cursor/.cursor-skill-status.json`
- Verify worktree path is correct
- Enable debug mode: `tapps-agents auto-execution debug on`

#### 4. Metrics Not Collected

**Symptoms:** No metrics in summary.

**Solutions:**
- Verify metrics collection is enabled in configuration
- Check metrics directory exists: `ls -la .tapps-agents/metrics/`
- Review metrics files: `cat .tapps-agents/metrics/executions_*.jsonl`

### Diagnostic Commands

**Check Configuration:**

```bash
tapps-agents background-agent-config validate
```

**Check Health:**

```bash
tapps-agents auto-execution health
```

**View Recent Executions:**

```bash
tapps-agents auto-execution history --limit 10
```

**View Metrics:**

```bash
tapps-agents auto-execution metrics
```

**Enable Debug Logging:**

```bash
tapps-agents auto-execution debug on
```

---

## Best Practices

1. **Start with Defaults**: Use default configuration initially, then customize as needed
2. **Monitor Regularly**: Check execution status and metrics regularly
3. **Set Appropriate Timeouts**: Set timeouts based on expected execution time
4. **Use Health Checks**: Run health checks before important workflows
5. **Enable Audit Logging**: Keep audit logging enabled for troubleshooting
6. **Test Incrementally**: Test with simple workflows before complex ones
7. **Review Metrics**: Regularly review metrics to identify issues early

---

## FAQ

**Q: Can I disable auto-execution for specific steps?**

A: Yes, you can disable auto-execution per-workflow in workflow metadata, or globally in project configuration.

**Q: How do I know if a step is executing?**

A: Use `tapps-agents auto-execution status` to view current executions.

**Q: What happens if a Background Agent fails?**

A: The system will detect the failure via status file or timeout, and mark the step as failed. Retry logic can be configured.

**Q: Can I use auto-execution with existing workflows?**

A: Yes, auto-execution is backward compatible. Existing workflows will continue to work with manual execution unless auto-execution is explicitly enabled.

**Q: How do I debug execution issues?**

A: Enable debug mode with `tapps-agents auto-execution debug on`, then review audit logs and execution history.

---

## Additional Resources

- **[Background Agents Guide](BACKGROUND_AGENTS_GUIDE.md)** - General Background Agent setup
- **[Workflow Guide](../workflow/README.md)** - Workflow execution documentation
- **[Configuration Guide](../config/README.md)** - Configuration management

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review execution history and metrics
3. Enable debug mode and review logs
4. Check health status with `tapps-agents auto-execution health`

