# Background Process Validation and Monitoring Enhancement

**Issue Type:** Enhancement
**Priority:** High
**Component:** Core / Workflow Execution
**Labels:** enhancement, workflow, background-execution, user-experience

## Problem Statement

Currently, when launching background processes (workflows, tasks, agents), the system returns immediately to the user without validating that the process can actually execute successfully. This leads to silent failures where:

1. **Pre-execution validation is missing**: No check for required files, dependencies, or permissions before launching
2. **Silent failures**: Background processes fail without user notification
3. **Poor monitoring**: No way to check process status without manually reading output files
4. **Missing artifacts**: Workflows expect files (requirements.md, stories/) that don't exist, causing cascading failures
5. **No progress tracking**: Users can't see what's happening in real-time

### Example Failure Case

```bash
# User launches full SDLC workflow
tapps-agents simple-mode full --prompt "..." --auto

# Returns immediately with:
# "Command running in background with ID: bff52f4"

# But workflow fails silently with:
# "Workflow blocked: no ready steps. Missing: requirements.md, stories/, etc."

# User has no idea it failed until they check the output file manually
```

## Current Behavior

### What Happens Now:
1. User launches background process
2. System spawns subprocess and returns immediately
3. Process runs (or fails) in background
4. User must manually check output file to see status
5. No notification on completion or failure

### Issues:
- ❌ No pre-flight validation
- ❌ No notification on completion
- ❌ No notification on failure
- ❌ No real-time progress monitoring
- ❌ No way to list running background processes
- ❌ No process health checks
- ❌ Output files can be hard to find

## Desired Behavior

### Pre-Execution Validation:
1. ✅ Check all required files exist before launching
2. ✅ Validate permissions and access
3. ✅ Verify dependencies are available
4. ✅ Check configuration validity
5. ✅ Fail fast with clear error message if validation fails

### During Execution:
1. ✅ Real-time progress notifications
2. ✅ Health checks every N seconds
3. ✅ Automatic failure detection
4. ✅ Status endpoint for checking progress

### Post-Execution:
1. ✅ Desktop notification on completion
2. ✅ Desktop notification on failure
3. ✅ Summary report with key metrics
4. ✅ Automatic cleanup of successful process artifacts

## Proposed Solution

### Phase 1: Pre-Execution Validation (Weeks 1-2)

#### 1.1: Background Process Validator
**File:** `tapps_agents/core/background/validator.py`

```python
class BackgroundProcessValidator:
    """Validates background process can execute before launching."""

    def validate_workflow_execution(
        self,
        workflow_type: str,
        prompt: str,
        config: dict
    ) -> ValidationResult:
        """Validate workflow can execute successfully."""
        errors = []

        # Check required files based on workflow type
        if workflow_type == "full":
            required = ["pyproject.toml"]  # Minimal requirement
            for file in required:
                if not Path(file).exists():
                    errors.append(f"Missing required file: {file}")

        # Check dependencies
        if not self._check_dependencies():
            errors.append("Missing required dependencies")

        # Check permissions
        if not self._check_write_permissions():
            errors.append("Insufficient write permissions")

        # Validate config
        if not self._validate_config(config):
            errors.append("Invalid configuration")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors
        )

    def _check_dependencies(self) -> bool:
        """Check all required dependencies are available."""
        # Check Python version
        # Check required packages
        # Check system tools (git, etc.)
        pass

    def _check_write_permissions(self) -> bool:
        """Check can write to required directories."""
        # Check .tapps-agents/ writable
        # Check output directory writable
        pass

    def _validate_config(self, config: dict) -> bool:
        """Validate configuration is correct."""
        # Check config.yaml valid
        # Check experts.yaml valid
        # Check required config keys present
        pass
```

#### 1.2: Enhanced Background Launch
**File:** `tapps_agents/core/background/launcher.py`

```python
class BackgroundLauncher:
    """Launches background processes with validation."""

    def __init__(self):
        self.validator = BackgroundProcessValidator()
        self.monitor = BackgroundProcessMonitor()

    def launch_workflow(
        self,
        workflow_type: str,
        prompt: str,
        auto: bool = False
    ) -> LaunchResult:
        """Launch workflow with pre-flight validation."""

        # Step 1: Validate
        validation = self.validator.validate_workflow_execution(
            workflow_type, prompt, config
        )

        if not validation.valid:
            return LaunchResult(
                success=False,
                errors=validation.errors,
                message="Validation failed. Fix issues and try again."
            )

        # Step 2: Launch background process
        process_id = self._spawn_subprocess(workflow_type, prompt, auto)

        # Step 3: Register with monitor
        self.monitor.register_process(
            process_id=process_id,
            workflow_type=workflow_type,
            prompt=prompt,
            started_at=datetime.now()
        )

        # Step 4: Return success with monitoring info
        return LaunchResult(
            success=True,
            process_id=process_id,
            output_file=self._get_output_file(process_id),
            monitor_command=f"tapps-agents bg status {process_id}",
            message=f"✅ Workflow launched successfully (ID: {process_id})"
        )
```

### Phase 2: Process Monitoring (Weeks 3-4)

#### 2.1: Background Process Monitor
**File:** `tapps_agents/core/background/monitor.py`

```python
class BackgroundProcessMonitor:
    """Monitors background processes and provides status."""

    def __init__(self):
        self.db = BackgroundProcessDB()  # SQLite or JSON
        self.notifier = BackgroundNotifier()

    def register_process(
        self,
        process_id: str,
        workflow_type: str,
        prompt: str,
        started_at: datetime
    ) -> None:
        """Register new background process for monitoring."""
        self.db.insert_process({
            "process_id": process_id,
            "workflow_type": workflow_type,
            "prompt": prompt,
            "status": "running",
            "started_at": started_at,
            "last_health_check": started_at,
            "progress": 0.0
        })

    def health_check(self, process_id: str) -> HealthStatus:
        """Check if process is still running and healthy."""
        process = self.db.get_process(process_id)

        # Check if process is still alive
        if not psutil.pid_exists(process.pid):
            self._mark_failed(process_id, "Process died unexpectedly")
            self.notifier.notify_failure(process_id)
            return HealthStatus.DEAD

        # Check output file for progress
        progress = self._parse_progress_from_output(process.output_file)
        self.db.update_progress(process_id, progress)

        # Check for errors in output
        if self._has_errors_in_output(process.output_file):
            self._mark_failed(process_id, "Errors detected in output")
            self.notifier.notify_failure(process_id)
            return HealthStatus.ERROR

        # Check for completion
        if self._is_complete(process.output_file):
            self._mark_completed(process_id)
            self.notifier.notify_completion(process_id)
            return HealthStatus.COMPLETE

        # Update last health check
        self.db.update_health_check(process_id, datetime.now())
        return HealthStatus.HEALTHY

    def run_health_checks(self) -> None:
        """Run health checks on all running processes."""
        running_processes = self.db.get_running_processes()

        for process in running_processes:
            self.health_check(process.process_id)

    def get_status(self, process_id: str) -> ProcessStatus:
        """Get detailed status of background process."""
        process = self.db.get_process(process_id)

        return ProcessStatus(
            process_id=process_id,
            workflow_type=process.workflow_type,
            status=process.status,
            progress=process.progress,
            started_at=process.started_at,
            elapsed_time=datetime.now() - process.started_at,
            output_file=process.output_file,
            errors=process.errors
        )

    def list_processes(self, status: str = None) -> List[ProcessStatus]:
        """List all background processes, optionally filtered by status."""
        processes = self.db.get_processes(status=status)
        return [self.get_status(p.process_id) for p in processes]
```

#### 2.2: Background Notifier
**File:** `tapps_agents/core/background/notifier.py`

```python
class BackgroundNotifier:
    """Sends notifications about background process events."""

    def __init__(self):
        self.config = load_config()

    def notify_completion(self, process_id: str) -> None:
        """Notify user that process completed successfully."""
        process = self._get_process(process_id)

        # Desktop notification
        if self.config.notifications.desktop_enabled:
            self._send_desktop_notification(
                title="TappsCodingAgents - Workflow Complete",
                message=f"{process.workflow_type} workflow completed successfully",
                icon="success"
            )

        # Terminal notification (if available)
        if self._is_terminal_available():
            self._send_terminal_notification(
                f"✅ Workflow {process_id} completed successfully"
            )

        # Log file
        self._log_notification(process_id, "completed")

    def notify_failure(self, process_id: str) -> None:
        """Notify user that process failed."""
        process = self._get_process(process_id)

        # Desktop notification
        if self.config.notifications.desktop_enabled:
            self._send_desktop_notification(
                title="TappsCodingAgents - Workflow Failed",
                message=f"{process.workflow_type} workflow failed. Check logs.",
                icon="error"
            )

        # Terminal notification
        if self._is_terminal_available():
            self._send_terminal_notification(
                f"❌ Workflow {process_id} failed: {process.error}"
            )

        # Log file
        self._log_notification(process_id, "failed")

    def notify_progress(self, process_id: str, progress: float) -> None:
        """Notify user of progress update (optional, configurable)."""
        if not self.config.notifications.progress_enabled:
            return

        # Only notify on significant progress (e.g., every 25%)
        if progress % 25 == 0:
            self._send_terminal_notification(
                f"📊 Workflow {process_id}: {progress:.0f}% complete"
            )

    def _send_desktop_notification(
        self,
        title: str,
        message: str,
        icon: str
    ) -> None:
        """Send desktop notification using platform-specific method."""
        try:
            # Windows: Use plyer or win10toast
            if sys.platform == "win32":
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(title, message, duration=5)

            # macOS: Use osascript
            elif sys.platform == "darwin":
                os.system(f"""
                    osascript -e 'display notification "{message}" with title "{title}"'
                """)

            # Linux: Use notify-send
            else:
                os.system(f'notify-send "{title}" "{message}"')
        except Exception as e:
            logger.warning(f"Failed to send desktop notification: {e}")
```

### Phase 3: CLI Integration (Week 5)

#### 3.1: Background Process Commands
**File:** `tapps_agents/cli/background.py`

```python
@click.group("bg")
def background_commands():
    """Background process management commands."""
    pass

@background_commands.command("status")
@click.argument("process_id", required=False)
def status(process_id: str = None):
    """Show status of background process(es)."""
    monitor = BackgroundProcessMonitor()

    if process_id:
        # Show single process status
        status = monitor.get_status(process_id)
        _print_process_status(status)
    else:
        # Show all running processes
        running = monitor.list_processes(status="running")
        if not running:
            click.echo("No running background processes")
            return

        click.echo(f"Running background processes ({len(running)}):\n")
        for proc in running:
            _print_process_summary(proc)

@background_commands.command("list")
@click.option("--status", type=click.Choice(["running", "completed", "failed", "all"]), default="all")
def list_processes(status: str):
    """List background processes."""
    monitor = BackgroundProcessMonitor()

    if status == "all":
        processes = monitor.list_processes()
    else:
        processes = monitor.list_processes(status=status)

    if not processes:
        click.echo(f"No {status} background processes")
        return

    # Table format
    table = Table(title=f"{status.title()} Background Processes")
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Progress", style="blue")
    table.add_column("Started", style="magenta")
    table.add_column("Duration", style="white")

    for proc in processes:
        table.add_row(
            proc.process_id[:8],
            proc.workflow_type,
            proc.status,
            f"{proc.progress:.0f}%",
            proc.started_at.strftime("%H:%M:%S"),
            str(proc.elapsed_time)
        )

    console = Console()
    console.print(table)

@background_commands.command("logs")
@click.argument("process_id")
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
@click.option("--tail", "-n", type=int, default=50, help="Number of lines to show")
def logs(process_id: str, follow: bool, tail: int):
    """Show logs for background process."""
    monitor = BackgroundProcessMonitor()
    process = monitor.get_status(process_id)

    if not process.output_file.exists():
        click.echo(f"Output file not found: {process.output_file}")
        return

    if follow:
        # Follow mode (like tail -f)
        _follow_log_file(process.output_file)
    else:
        # Show last N lines
        _show_log_tail(process.output_file, tail)

@background_commands.command("stop")
@click.argument("process_id")
@click.confirmation_option(prompt="Are you sure you want to stop this process?")
def stop(process_id: str):
    """Stop a running background process."""
    monitor = BackgroundProcessMonitor()
    monitor.stop_process(process_id)
    click.echo(f"✅ Stopped process {process_id}")

@background_commands.command("cleanup")
@click.option("--older-than", type=int, default=7, help="Remove processes older than N days")
@click.option("--status", type=click.Choice(["completed", "failed", "all"]), default="completed")
def cleanup(older_than: int, status: str):
    """Clean up old background process records."""
    monitor = BackgroundProcessMonitor()
    removed = monitor.cleanup_old_processes(
        older_than_days=older_than,
        status=status
    )
    click.echo(f"✅ Removed {removed} old process records")
```

### Phase 4: Background Health Check Daemon (Week 6)

#### 4.1: Health Check Daemon
**File:** `tapps_agents/core/background/daemon.py`

```python
class BackgroundHealthDaemon:
    """Daemon that runs periodic health checks on background processes."""

    def __init__(self):
        self.monitor = BackgroundProcessMonitor()
        self.running = False
        self.interval = 30  # seconds

    def start(self) -> None:
        """Start the health check daemon."""
        if self.running:
            return

        self.running = True
        self._daemon_thread = threading.Thread(
            target=self._run_daemon,
            daemon=True
        )
        self._daemon_thread.start()
        logger.info("Background health check daemon started")

    def stop(self) -> None:
        """Stop the health check daemon."""
        self.running = False
        if hasattr(self, "_daemon_thread"):
            self._daemon_thread.join(timeout=5)
        logger.info("Background health check daemon stopped")

    def _run_daemon(self) -> None:
        """Daemon main loop."""
        while self.running:
            try:
                self.monitor.run_health_checks()
            except Exception as e:
                logger.error(f"Health check failed: {e}")

            time.sleep(self.interval)
```

**Auto-start daemon on CLI init:**
```python
# In tapps_agents/cli/__init__.py
def initialize_cli():
    """Initialize CLI environment."""
    # Start health check daemon
    daemon = BackgroundHealthDaemon()
    daemon.start()

    # Register cleanup on exit
    atexit.register(daemon.stop)
```

## Configuration

### New Config Section
**File:** `.tapps-agents/config.yaml`

```yaml
background_processes:
  # Validation
  validation_enabled: true
  strict_validation: false  # Fail on warnings, not just errors

  # Monitoring
  monitoring_enabled: true
  health_check_interval: 30  # seconds
  auto_cleanup_days: 7  # Auto-remove completed processes after N days

  # Notifications
  notifications:
    desktop_enabled: true
    terminal_enabled: true
    progress_enabled: false  # Notify on progress updates
    progress_interval: 25  # Percent (notify every 25%)

  # Process limits
  max_concurrent_processes: 3
  max_process_runtime: 7200  # seconds (2 hours)

  # Storage
  process_db: .tapps-agents/background_processes.db
  output_dir: .tapps-agents/output
```

## Implementation Checklist

### Phase 1: Pre-Execution Validation
- [ ] Create `BackgroundProcessValidator` class
- [ ] Implement dependency checking
- [ ] Implement permission checking
- [ ] Implement config validation
- [ ] Add validation to workflow launch
- [ ] Add validation to agent launch
- [ ] Write unit tests
- [ ] Write integration tests

### Phase 2: Process Monitoring
- [ ] Create `BackgroundProcessMonitor` class
- [ ] Implement process registration
- [ ] Implement health check logic
- [ ] Implement progress tracking
- [ ] Implement error detection
- [ ] Implement completion detection
- [ ] Create `BackgroundNotifier` class
- [ ] Implement desktop notifications (Windows, macOS, Linux)
- [ ] Implement terminal notifications
- [ ] Write unit tests
- [ ] Write integration tests

### Phase 3: CLI Integration
- [ ] Create `bg` command group
- [ ] Implement `bg status` command
- [ ] Implement `bg list` command
- [ ] Implement `bg logs` command
- [ ] Implement `bg stop` command
- [ ] Implement `bg cleanup` command
- [ ] Add rich table formatting
- [ ] Write CLI tests

### Phase 4: Health Check Daemon
- [ ] Create `BackgroundHealthDaemon` class
- [ ] Implement daemon thread
- [ ] Auto-start daemon on CLI init
- [ ] Register cleanup on exit
- [ ] Add daemon status to `bg status`
- [ ] Write daemon tests

### Phase 5: Documentation & Testing
- [ ] Update user documentation
- [ ] Create background process guide
- [ ] Add examples to docs
- [ ] Comprehensive integration tests
- [ ] Performance tests
- [ ] User acceptance testing

## Success Criteria

1. **Pre-execution validation catches 95% of issues** before launching
2. **Health checks detect failures within 30 seconds**
3. **Desktop notifications work on Windows, macOS, Linux**
4. **Users can check status without reading output files**
5. **Failed processes are detected and user is notified**
6. **Background process list command shows all processes**
7. **Zero silent failures** - all failures are detected and reported

## Acceptance Tests

### Test 1: Pre-execution Validation
```bash
# Try to launch workflow without required files
$ tapps-agents simple-mode full --prompt "..." --auto

# Expected: Immediate error message
❌ Validation failed:
  - Missing required dependencies: tiktoken
  - Insufficient write permissions for .tapps-agents/

Fix these issues and try again.
```

### Test 2: Background Process Monitoring
```bash
# Launch workflow
$ tapps-agents simple-mode full --prompt "..." --auto
✅ Workflow launched successfully (ID: abc123)
Monitor: tapps-agents bg status abc123

# Check status
$ tapps-agents bg status abc123
Process ID: abc123
Type: full-sdlc
Status: running
Progress: 45% (Step 5/10: Implementation)
Started: 10:30:15
Elapsed: 5m 32s
Output: /tmp/.../abc123.output

# List all processes
$ tapps-agents bg list
Running Background Processes (2):
ID       Type        Status   Progress  Started   Duration
abc123   full-sdlc   running  45%       10:30:15  5m 32s
def456   build       running  80%       10:28:00  7m 47s
```

### Test 3: Notifications
```bash
# When workflow completes
[Desktop Notification]
Title: TappsCodingAgents - Workflow Complete
Message: full-sdlc workflow completed successfully

[Terminal Output]
✅ Workflow abc123 completed successfully

# When workflow fails
[Desktop Notification]
Title: TappsCodingAgents - Workflow Failed
Message: full-sdlc workflow failed. Check logs.

[Terminal Output]
❌ Workflow abc123 failed: Workflow blocked: no ready steps
```

## Related Issues

- #XXX - Silent workflow failures
- #XXX - No way to monitor background processes
- #XXX - Missing file validation

## References

- [Background Process Output](C:\Users\tappt\AppData\Local\Temp\claude\c--cursor-TappsCodingAgents\tasks\bff52f4.output)
- [Workflow Execution Documentation](docs/WORKFLOW_EXECUTION.md)
- [Configuration Reference](docs/CONFIGURATION.md)

---

**Created:** 2026-02-04
**Author:** TappsCodingAgents Team
**Priority:** High
**Estimated Effort:** 6 weeks
