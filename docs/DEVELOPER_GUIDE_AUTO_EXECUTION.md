# Background Agent Auto-Execution Developer Guide

**TappsCodingAgents Background Agent Auto-Execution Architecture and API Reference**

This guide provides technical documentation for developers working with the auto-execution system.

---

## Architecture

### Overview

The auto-execution system consists of several key components:

```
┌─────────────────────────────────────────────────────────────┐
│                    Workflow Executor                         │
│  (CursorWorkflowExecutor)                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           BackgroundAgentAutoExecutor                        │
│  - Command file creation                                     │
│  - Polling for completion                                    │
│  - Status file monitoring                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Metrics    │ │    Audit     │ │   Health     │
│  Collector   │ │    Logger    │ │   Checker    │
└──────────────┘ └──────────────┘ └──────────────┘
        │              │              │
        ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│              Background Agent (Cursor)                       │
│  - Watches for command files                                  │
│  - Executes commands                                         │
│  - Creates status files                                      │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

**BackgroundAgentAutoExecutor:**
- Creates command files for Background Agents
- Polls for completion status files
- Handles timeouts and errors
- Integrates with metrics and audit logging

**AutoExecutionConfigManager:**
- Loads and validates configuration
- Manages feature flags
- Handles configuration migration
- Supports runtime reload

**ExecutionMetricsCollector:**
- Records execution metrics
- Stores metrics in JSONL format
- Provides metrics aggregation
- Supports filtering and querying

**AuditLogger:**
- Logs all execution events
- Provides structured audit trail
- Supports log rotation
- Enables event querying

**HealthChecker:**
- Validates system health
- Checks configuration validity
- Verifies file system access
- Reports overall status

---

## API Reference

### BackgroundAgentAutoExecutor

**Class:** `tapps_agents.workflow.background_auto_executor.BackgroundAgentAutoExecutor`

**Initialization:**

```python
executor = BackgroundAgentAutoExecutor(
    polling_interval: float = 5.0,
    timeout_seconds: float = 3600.0,
    status_file_name: str = ".cursor-skill-status.json",
    project_root: Path | None = None,
    enable_metrics: bool = True,
    enable_audit: bool = True,
)
```

**Methods:**

```python
async def execute_command(
    self,
    command: str,
    worktree_path: Path,
    workflow_id: str | None = None,
    step_id: str | None = None,
    expected_artifacts: list[str] | None = None,
) -> dict[str, Any]:
    """
    Execute a command via Background Agent auto-execution.

    Returns:
        Dictionary with execution results:
        - status: "completed", "failed", or "timeout"
        - command: The command that was executed
        - worktree: Worktree path
        - artifacts: List of created artifacts
        - error: Error message (if failed)
        - duration_seconds: Execution duration
    """
```

### AutoExecutionConfigManager

**Class:** `tapps_agents.workflow.auto_execution_config.AutoExecutionConfigManager`

**Initialization:**

```python
manager = AutoExecutionConfigManager(
    config_path: Path | None = None,
    project_root: Path | None = None,
)
```

**Methods:**

```python
def load(self, validate: bool = True) -> AutoExecutionConfig:
    """Load configuration from file."""

def save(self, config: AutoExecutionConfig | None = None) -> None:
    """Save configuration to file."""

def validate(self, config: AutoExecutionConfig | None = None) -> None:
    """Validate configuration."""

def reload(self) -> AutoExecutionConfig:
    """Reload configuration from file."""

def get_feature_flag(
    self,
    flag_name: str,
    workflow_override: dict[str, Any] | None = None,
) -> bool:
    """Get feature flag value with workflow override support."""
```

### ExecutionMetricsCollector

**Class:** `tapps_agents.workflow.execution_metrics.ExecutionMetricsCollector`

**Initialization:**

```python
collector = ExecutionMetricsCollector(
    metrics_dir: Path | None = None,
    project_root: Path | None = None,
)
```

**Methods:**

```python
def record_execution(
    self,
    workflow_id: str,
    step_id: str,
    command: str,
    status: str,
    duration_ms: float,
    retry_count: int = 0,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
    error_message: str | None = None,
) -> ExecutionMetric:
    """Record an execution metric."""

def get_metrics(
    self,
    workflow_id: str | None = None,
    step_id: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[ExecutionMetric]:
    """Get execution metrics with optional filtering."""

def get_summary(self) -> dict[str, Any]:
    """Get metrics summary."""
```

### AuditLogger

**Class:** `tapps_agents.workflow.audit_logger.AuditLogger`

**Initialization:**

```python
logger = AuditLogger(
    audit_dir: Path | None = None,
    project_root: Path | None = None,
)
```

**Methods:**

```python
def log_event(
    self,
    event_type: str,
    workflow_id: str | None = None,
    step_id: str | None = None,
    command: str | None = None,
    status: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Log an audit event."""

def log_command_detected(
    self,
    workflow_id: str,
    step_id: str,
    command: str,
    command_file: Path,
) -> None:
    """Log command file detection."""

def log_execution_started(
    self,
    workflow_id: str,
    step_id: str,
    command: str,
) -> None:
    """Log execution start."""

def log_execution_completed(
    self,
    workflow_id: str,
    step_id: str,
    command: str,
    duration_ms: float,
) -> None:
    """Log execution completion."""

def log_execution_failed(
    self,
    workflow_id: str,
    step_id: str,
    command: str,
    error: str,
    duration_ms: float | None = None,
) -> None:
    """Log execution failure."""

def query_events(
    self,
    workflow_id: str | None = None,
    step_id: str | None = None,
    event_type: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Query audit events."""
```

### HealthChecker

**Class:** `tapps_agents.workflow.health_checker.HealthChecker`

**Initialization:**

```python
checker = HealthChecker(project_root: Path | None = None)
```

**Methods:**

```python
def check_all(self) -> list[HealthCheckResult]:
    """Run all health checks."""

def check_configuration(self) -> HealthCheckResult:
    """Check Background Agent configuration validity."""

def check_file_system(self) -> HealthCheckResult:
    """Check file system accessibility."""

def check_status_file_access(self) -> HealthCheckResult:
    """Check if status files can be read."""

def check_command_file_access(self) -> HealthCheckResult:
    """Check if command files can be created."""

def get_overall_status(self) -> str:
    """Get overall health status."""
```

---

## Integration Points

### Workflow Executor Integration

The auto-execution system integrates with `CursorWorkflowExecutor`:

```python
# In CursorWorkflowExecutor.__init__
self.auto_execution_enabled = config.workflow.auto_execution_enabled
self.auto_executor = BackgroundAgentAutoExecutor(
    polling_interval=config.workflow.polling_interval,
    timeout_seconds=config.workflow.timeout_seconds,
    project_root=project_root,
)

# In _execute_step_for_parallel
if use_auto_execution:
    completion_status = await self.auto_executor.execute_and_wait(
        agent_name=agent_name,
        action=action,
        command_string=command,
        step_id=step.id,
        workflow_id=self.workflow.id,
        worktree_path=worktree_path,
    )
```

### Configuration Integration

Configuration is loaded from multiple sources:

1. **Project Config** (`.tapps-agents/config.yaml`):
   ```yaml
   workflow:
     auto_execution_enabled: true
     polling_interval: 5.0
     timeout_seconds: 3600
   ```

2. **Auto-Execution Config** (`.tapps-agents/auto_execution_config.yaml`):
   ```yaml
   auto_execution:
     enabled: true
     retry: {...}
     polling: {...}
     features: {...}
   ```

3. **Workflow Metadata** (in workflow YAML):
   ```yaml
   metadata:
     auto_execution: true
   ```

Precedence: Workflow metadata > Auto-execution config > Project config

---

## Extension Points

### Custom Feature Flags

Add custom feature flags by extending `FeatureFlags`:

```python
@dataclass
class CustomFeatureFlags(FeatureFlags):
    custom_feature: bool = True
```

### Custom Metrics

Extend metrics collection by subclassing `ExecutionMetricsCollector`:

```python
class CustomMetricsCollector(ExecutionMetricsCollector):
    def record_execution(self, ...):
        # Custom logic
        super().record_execution(...)
```

### Custom Health Checks

Add custom health checks:

```python
class CustomHealthChecker(HealthChecker):
    def check_custom_component(self) -> HealthCheckResult:
        # Custom health check
        return HealthCheckResult(...)
    
    def check_all(self) -> list[HealthCheckResult]:
        results = super().check_all()
        results.append(self.check_custom_component())
        return results
```

---

## Testing

### Unit Tests

Unit tests are located in `tests/unit/workflow/`:
- `test_auto_execution_config.py` - Configuration management
- `test_execution_metrics.py` - Metrics collection
- `test_audit_logger.py` - Audit logging
- `test_health_checker.py` - Health checks

### Integration Tests

Integration tests are in `tests/integration/test_auto_execution_integration.py`:
- Auto-executor with mock agents
- Metrics collection integration
- Audit logging integration
- Timeout handling

### End-to-End Tests

End-to-end tests are in `tests/e2e/workflows/test_auto_execution_e2e.py`:
- Complete workflow execution
- Error recovery
- Timeout handling

### Test Fixtures

Test fixtures are in `tests/fixtures/background_agent_fixtures.py`:
- `MockBackgroundAgent` - Simulates Background Agent execution
- Configuration fixtures
- Command and status file fixtures

---

## Design Decisions

### Polling vs Event-Driven

**Decision:** Use polling for completion detection.

**Rationale:**
- Simpler implementation
- No dependency on file system events
- Works across different platforms
- Configurable polling interval

### File-Based Communication

**Decision:** Use files for command and status communication.

**Rationale:**
- Works with Background Agents
- Simple and reliable
- Easy to debug
- No network dependencies

### Metrics Storage Format

**Decision:** Use JSONL (JSON Lines) for metrics storage.

**Rationale:**
- Append-only, efficient writes
- Easy to parse and query
- Supports daily rotation
- Human-readable

### Configuration Versioning

**Decision:** Include version in configuration schema.

**Rationale:**
- Enables migration between versions
- Prevents breaking changes
- Clear upgrade path

---

## Performance Considerations

### Polling Interval

- **Default:** 5 seconds
- **Impact:** Lower interval = faster detection but more CPU usage
- **Recommendation:** Adjust based on expected execution time

### Metrics Storage

- **Format:** Daily JSONL files
- **Retention:** Consider implementing retention policy
- **Performance:** Append-only writes are efficient

### Audit Logging

- **Rotation:** 10MB files, 5 backups
- **Performance:** Async logging recommended for high volume
- **Impact:** Minimal with log rotation

---

## Security Considerations

### Command File Security

- Command files contain executable commands
- Ensure proper file permissions
- Clean up command files after execution

### Status File Security

- Status files may contain execution results
- Validate status file content before processing
- Handle malformed status files gracefully

### Configuration Security

- Configuration files may contain sensitive settings
- Use secure file permissions
- Validate configuration before loading

---

## Future Enhancements

Potential future improvements:

1. **Event-Driven Completion:** Replace polling with file system events
2. **Distributed Execution:** Support remote Background Agents
3. **Advanced Retry Logic:** Exponential backoff, circuit breakers
4. **Metrics Dashboard:** Web-based metrics visualization
5. **Real-Time Monitoring:** WebSocket-based status updates

---

## Contributing

When contributing to the auto-execution system:

1. **Follow Existing Patterns:** Match existing code style and patterns
2. **Add Tests:** Include unit, integration, and e2e tests
3. **Update Documentation:** Keep docs in sync with code changes
4. **Consider Backward Compatibility:** Maintain compatibility with existing workflows
5. **Performance Testing:** Test with realistic workloads

---

## Additional Resources

- **[User Guide](BACKGROUND_AGENTS_AUTO_EXECUTION_GUIDE.md)** - User-facing documentation
- **[Background Agents Guide](BACKGROUND_AGENTS_GUIDE.md)** - General Background Agent setup
- **[Workflow Guide](../workflow/README.md)** - Workflow execution documentation

