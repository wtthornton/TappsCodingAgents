# Step 4: Component Design - Automatic Execution System

**Generated**: 2025-01-16  
**Workflow**: Build - Automation System Implementation  
**Agent**: @designer  
**Depends on**: Step 3 - Architecture Design

---

## Component Design Specifications

This document provides detailed design specifications for each component in the Automatic Execution System.

---

## 1. Configuration Schema

### AutomationConfig Model

**Location**: `tapps_agents/core/config.py` (extension), `tapps_agents/automation/config.py`

**Schema**:
```python
class AutomationConfig(BaseModel):
    """Automation configuration model."""
    
    level: int = 0  # 0=manual, 1=suggest, 2=non-blocking, 3=smart, 4=full
    triggers: dict[str, TriggerConfig] = {}
    notifications: NotificationConfig = NotificationConfig()
    resources: ResourceConfig = ResourceConfig()
    git_hooks: GitHookConfig = GitHookConfig()
    
    @validator('level')
    def validate_level(cls, v):
        if not 0 <= v <= 4:
            raise ValueError('Automation level must be 0-4')
        return v

class TriggerConfig(BaseModel):
    """Trigger configuration."""
    
    enabled: bool = True
    debounce_seconds: float = 5.0
    commands: list[str] = []
    automation_level: int = 2  # Minimum level required
    conditions: dict[str, Any] = {}  # file_patterns, branch_patterns, etc.
    priority: int = 0  # Higher priority = execute first

class NotificationConfig(BaseModel):
    """Notification configuration."""
    
    enabled: bool = True
    channels: list[str] = ["console"]  # console, chat, file
    show_status_bar: bool = True
    show_toast: bool = True
    post_to_chat: bool = False

class ResourceConfig(BaseModel):
    """Resource management configuration."""
    
    cpu_threshold: float = 80.0  # Pause automation if CPU > threshold
    battery_aware: bool = True
    rate_limit: int = 10  # Max auto commands per hour
    user_activity_pause: bool = True  # Pause when user actively typing
```

**YAML Structure**:
```yaml
automation:
  level: 2
  triggers:
    file_save:
      enabled: true
      debounce_seconds: 5
      commands: ["reviewer score"]
      automation_level: 2
      conditions:
        file_patterns: ["**/*.py", "**/*.ts"]
        exclude_patterns: ["**/tests/**", "**/__pycache__/**"]
    git_pre_commit:
      enabled: true
      commands: ["reviewer lint", "reviewer type-check"]
      automation_level: 2
    git_post_commit:
      enabled: true
      commands: ["reviewer analyze-project"]
      automation_level: 2
  notifications:
    enabled: true
    channels: ["console", "chat"]
    show_status_bar: true
  resources:
    cpu_threshold: 80.0
    battery_aware: true
    rate_limit: 10
```

---

## 2. Event Monitor Service

### EventMonitor Class

**Location**: `tapps_agents/automation/event_monitor.py`

**Design**:
```python
class EventMonitor:
    """Monitors file system, git, and IDE events."""
    
    def __init__(
        self,
        config: AutomationConfig,
        event_bus: FileBasedEventBus,
        resource_monitor: ResourceMonitor
    ):
        self.config = config
        self.event_bus = event_bus
        self.resource_monitor = resource_monitor
        self.observers: list[Observer] = []
        self.running = False
        self.debounce_queue: dict[str, asyncio.Task] = {}
    
    async def start(self) -> None:
        """Start monitoring events."""
        # Start file system watcher
        # Start git hook listeners
        # Start IDE activity monitor
        self.running = True
    
    async def stop(self) -> None:
        """Stop monitoring events."""
        # Stop all observers
        # Cancel debounce tasks
        self.running = False
    
    def _on_file_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification event."""
        # Filter (respect .gitignore)
        # Debounce
        # Emit to event bus
    
    def _debounce_event(self, event_type: str, event_data: dict) -> None:
        """Debounce event (wait before emitting)."""
        # Cancel existing debounce task
        # Create new debounce task
        # Emit after delay
```

**Event Types**:
- `file_save` - File saved (debounced)
- `file_create` - New file created
- `file_delete` - File deleted
- `git_pre_commit` - Git pre-commit hook
- `git_post_commit` - Git post-commit hook
- `git_pre_push` - Git pre-push hook
- `session_start` - IDE session started
- `session_end` - IDE session ended

**Event Data Structure**:
```python
Event = {
    "type": str,  # Event type
    "timestamp": datetime,
    "data": dict,  # Event-specific data (file paths, branch name, etc.)
    "source": str  # "file_system", "git", "ide"
}
```

---

## 3. Trigger Registry

### TriggerRegistry Class

**Location**: `tapps_agents/automation/trigger_registry.py`

**Design**:
```python
class TriggerRegistry:
    """Maps events to commands with conditions."""
    
    def __init__(self, config: AutomationConfig):
        self.config = config
        self.triggers: list[Trigger] = []
        self._load_triggers()
    
    def _load_triggers(self) -> None:
        """Load triggers from configuration."""
        # Parse config triggers
        # Create Trigger objects
        # Sort by priority
    
    def find_triggers(self, event: Event) -> list[Trigger]:
        """Find matching triggers for event."""
        # Filter by event type
        # Filter by automation level
        # Evaluate conditions
        # Sort by priority
        return matching_triggers
    
    def evaluate_conditions(self, trigger: Trigger, event: Event) -> bool:
        """Evaluate trigger conditions."""
        # Check file patterns
        # Check branch patterns
        # Check time constraints
        return conditions_met
    
    def resolve_command(self, trigger: Trigger, event: Event) -> Command:
        """Resolve command with parameters."""
        # Substitute parameters ({file_path}, {branch_name})
        # Validate command exists
        # Return Command object
```

**Trigger Matching Logic**:
1. Event type matches trigger event_type
2. Automation level >= trigger automation_level
3. Conditions evaluate to True
4. Command exists and is valid
5. Return triggers sorted by priority

---

## 4. Command Scheduler

### CommandScheduler Class

**Location**: `tapps_agents/automation/command_scheduler.py`

**Design**:
```python
class CommandScheduler:
    """Manages command execution queue and prioritization."""
    
    def __init__(
        self,
        config: AutomationConfig,
        resource_monitor: ResourceMonitor,
        notification_service: NotificationService
    ):
        self.config = config
        self.resource_monitor = resource_monitor
        self.notification_service = notification_service
        self.queue: PriorityQueue = PriorityQueue()
        self.executing: set[str] = set()
        self.rate_limiter = RateLimiter(config.resources.rate_limit)
    
    async def schedule(
        self,
        command: Command,
        priority: int = 0,
        source: str = "automation"
    ) -> str:
        """Schedule command for execution."""
        # Check automation level
        # Check rate limit
        # Add to priority queue
        # Return command ID
    
    async def execute(self, command: Command) -> CommandResult:
        """Execute command asynchronously."""
        # Check resources (CPU, battery)
        # Execute command (subprocess/async)
        # Handle errors
        # Notify completion
        return result
    
    async def _process_queue(self) -> None:
        """Process command queue continuously."""
        # Get next command from queue
        # Check if should execute (resources OK)
        # Execute command
        # Repeat
```

**Command Structure**:
```python
Command = {
    "id": str,
    "command": str,  # "reviewer score"
    "args": list[str],  # Command arguments
    "priority": int,  # Higher = execute first
    "source": str,  # "user" or "automation"
    "automation_level": int  # Minimum level required
}
```

**Priority Levels**:
- User commands: Priority 100
- Critical automation: Priority 50
- Normal automation: Priority 0
- Background automation: Priority -50

---

## 5. Notification Service

### NotificationService Class

**Location**: `tapps_agents/automation/notifications.py`

**Design**:
```python
class NotificationService:
    """Handles user feedback and results."""
    
    def __init__(self, config: AutomationConfig):
        self.config = config.notifications
        self.status: dict[str, Any] = {}
    
    def notify(self, message: str, type: str = "info") -> None:
        """Send notification."""
        # Check if notifications enabled
        # Send to configured channels
        # Console: print
        # Chat: post to Cursor chat (if available)
        # File: write to notification log
    
    def update_status(self, status: dict[str, Any]) -> None:
        """Update status indicator."""
        # Update status dict
        # Write to status file (for status bar integration)
    
    def show_results(self, command: Command, results: CommandResult) -> None:
        """Show command results."""
        # Format results
        # Send notification
        # Update status
        # Post to chat (if enabled)
    
    def post_to_chat(self, message: str) -> None:
        """Post message to Cursor chat."""
        # Check if chat integration enabled
        # Format message
        # Post to chat (if API available)
```

**Notification Types**:
- `info` - Informational message
- `success` - Success message
- `warning` - Warning message
- `error` - Error message
- `progress` - Progress update

---

## 6. Resource Monitor

### ResourceMonitor Class

**Location**: `tapps_agents/automation/resource_monitor.py`

**Design**:
```python
class ResourceMonitor:
    """Tracks system resources and adapts execution."""
    
    def __init__(self, config: ResourceConfig):
        self.config = config
        self.last_activity_time: float = 0
    
    def get_cpu_usage(self) -> float:
        """Get CPU usage percentage."""
        return psutil.cpu_percent(interval=0.1)
    
    def get_memory_usage(self) -> float:
        """Get memory usage percentage."""
        return psutil.virtual_memory().percent
    
    def is_on_battery(self) -> bool:
        """Check if system is on battery power."""
        if hasattr(psutil, 'sensors_battery'):
            battery = psutil.sensors_battery()
            return battery is not None and not battery.power_plugged
        return False
    
    def is_user_active(self) -> bool:
        """Check if user is actively working."""
        # Check last file save time
        # Check last git commit time
        # Check keyboard/mouse activity (if available)
        return time.time() - self.last_activity_time < 30  # 30 seconds
    
    def should_throttle(self) -> bool:
        """Recommend throttling automation."""
        # CPU > threshold
        # On battery and battery_aware enabled
        # User actively working and user_activity_pause enabled
        return (
            self.get_cpu_usage() > self.config.cpu_threshold or
            (self.is_on_battery() and self.config.battery_aware) or
            (self.is_user_active() and self.config.user_activity_pause)
        )
```

---

## 7. Git Hook Manager

### GitHookManager Class

**Location**: `tapps_agents/automation/git_hooks.py`

**Design**:
```python
class GitHookManager:
    """Manages git hook installation and execution."""
    
    def __init__(self, project_root: Path, config: AutomationConfig):
        self.project_root = project_root
        self.config = config
        self.hooks_dir = project_root / ".git" / "hooks"
    
    def install_hooks(self) -> None:
        """Install all configured git hooks."""
        # Check if git repository
        # Create hooks directory if needed
        # Install pre-commit hook
        # Install post-commit hook
        # Install pre-push hook
        # Install pre-merge hook
        # Validate hooks
    
    def uninstall_hooks(self) -> None:
        """Uninstall all git hooks."""
        # Remove hook files
        # Backup existing hooks (if any)
    
    def install_hook(self, name: str, script: str) -> None:
        """Install specific hook."""
        # Validate hook script
        # Write hook file
        # Make executable (Unix)
    
    def validate_hook(self, script: str) -> bool:
        """Validate hook script (security)."""
        # Check for dangerous commands
        # Check for framework CLI commands only
        # Return True if valid
```

**Hook Script Templates**:

**Pre-commit Hook**:
```bash
#!/bin/sh
# Pre-commit hook for TappsCodingAgents
python -m tapps_agents.cli reviewer lint --staged || exit 1
python -m tapps_agents.cli reviewer type-check --staged || exit 1
```

**Post-commit Hook**:
```bash
#!/bin/sh
# Post-commit hook for TappsCodingAgents (non-blocking)
python -m tapps_agents.cli reviewer analyze-project --format json &
```

---

## 8. API Design

### CLI Commands

**New Commands**:
```bash
# Install git hooks
tapps-agents install-hooks

# Uninstall git hooks
tapps-agents uninstall-hooks

# Enable automation
tapps-agents automation enable --level 2

# Disable automation
tapps-agents automation disable

# Show automation status
tapps-agents automation status

# Migrate from background-agents.yaml
tapps-agents migrate-automation-config
```

**Command Structure**:
- `tapps-agents automation <subcommand>` - Automation management
- `tapps-agents install-hooks` - Git hook installation
- Commands remain unchanged (automation wraps them)

---

## 9. Data Models

### Event Model
```python
@dataclass
class Event:
    type: str
    timestamp: datetime
    data: dict[str, Any]
    source: str
```

### Trigger Model
```python
@dataclass
class Trigger:
    id: str
    event_type: str
    conditions: dict[str, Any]
    command: str
    parameters: dict[str, Any]
    automation_level: int
    priority: int
```

### Command Model
```python
@dataclass
class Command:
    id: str
    command: str
    args: list[str]
    priority: int
    source: str
    automation_level: int
```

### CommandResult Model
```python
@dataclass
class CommandResult:
    command_id: str
    success: bool
    output: str
    error: str | None
    duration: float
    timestamp: datetime
```

---

## 10. Integration Points

### With Existing CLI
- Automation wraps existing CLI commands
- No changes to command implementations
- Commands can be called directly or via automation

### With Configuration System
- Extend `ProjectConfig` model
- Add `AutomationConfig` section
- Migrate from background-agents.yaml

### With Event System
- Use existing `FileBasedEventBus`
- Extend event types
- Reuse event serialization

### With Feedback System
- Extend existing feedback system
- Reuse feedback formats
- Integrate with progress reporting

---

## 11. Error Handling

**Event Monitor Errors**:
- Log errors, don't crash
- Graceful degradation (fallback to polling)
- User notification on persistent errors

**Command Execution Errors**:
- Retry logic for transient failures
- Error notifications
- Don't block user workflow

**Configuration Errors**:
- Validate on load
- Clear error messages
- Fallback to safe defaults

**Resource Errors**:
- Throttle when resources unavailable
- Queue commands for later
- Clear user messages

---

## 12. Testing Strategy

**Unit Tests**:
- Each component in isolation
- Mock dependencies
- Test error handling

**Integration Tests**:
- Component interactions
- Event flow
- Git hook execution

**E2E Tests**:
- File watcher scenarios
- Git hook scenarios
- Automation level behaviors

**Performance Tests**:
- File watcher overhead
- Resource usage
- Throttling behavior
