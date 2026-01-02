# Step 3: Architecture Design - Automatic Execution System

**Generated**: 2025-01-16  
**Workflow**: Build - Automation System Implementation  
**Agent**: @architect  
**Depends on**: Step 2 - User Stories

---

## System Architecture Overview

The Automatic Execution System follows an **Event-Driven Architecture** with **Observer Pattern**, enabling flexible, extensible automation without tight coupling to specific triggers or commands.

**Architecture Principles**:
- **Separation of Concerns**: Event detection, trigger resolution, and command execution are separate
- **Extensibility**: New trigger types and commands can be added without modifying core logic
- **Non-Blocking**: All automation runs asynchronously to avoid interrupting user workflow
- **Configurability**: All behavior is configurable without code changes
- **Resource-Aware**: System adapts to available resources and user activity

---

## System Components

### 1. Event Monitor Service
**Purpose**: Core event detection and routing

**Responsibilities**:
- Monitor file system events (watchdog-based)
- Monitor git events (hook-based)
- Monitor IDE activity (file open, session state)
- Emit events to event bus
- Filter events (respect .gitignore, file patterns)
- Debounce file system events

**Interfaces**:
- `EventMonitor.start()` - Start monitoring
- `EventMonitor.stop()` - Stop monitoring
- `EventMonitor.subscribe(event_type, handler)` - Subscribe to event types
- `EventMonitor.emit(event)` - Emit event to bus

**Dependencies**:
- FileBasedEventBus (workflow system)
- Configuration System
- Resource Monitor (for throttling)

**Location**: `tapps_agents/automation/event_monitor.py`

---

### 2. Trigger Registry
**Purpose**: Maps events to commands with conditions

**Responsibilities**:
- Store trigger definitions (event → command mappings)
- Evaluate conditions (file patterns, branch names, time constraints)
- Resolve command parameters (file paths, branch names)
- Prioritize triggers (user commands > auto commands)
- Validate triggers (commands exist, parameters valid)

**Interfaces**:
- `TriggerRegistry.register(trigger)` - Register trigger
- `TriggerRegistry.find_triggers(event)` - Find matching triggers for event
- `TriggerRegistry.evaluate_conditions(trigger, event)` - Evaluate trigger conditions
- `TriggerRegistry.resolve_command(trigger, event)` - Resolve command with parameters

**Data Structure**:
```python
Trigger = {
    id: str
    event_type: str  # "file_save", "git_pre_commit", etc.
    conditions: dict  # file_patterns, branch_patterns, etc.
    command: str  # "reviewer score", "tester run-tests"
    parameters: dict  # command parameters
    automation_level: int  # minimum level (0-4)
    priority: int  # trigger priority
}
```

**Dependencies**:
- Configuration System (load triggers from config)
- Event Monitor (receive events)

**Location**: `tapps_agents/automation/trigger_registry.py`

---

### 3. Context Analyzer (Enhanced)
**Purpose**: Analyzes project state and change patterns

**Responsibilities**:
- Detect change patterns (code vs. config vs. docs)
- Classify file types (Python, TypeScript, etc.)
- Analyze commit scope (targeted vs. full analysis)
- Detect branch context (feature branch vs. main)
- Calculate confidence scores (when to auto-run)
- Suggest appropriate commands based on context

**Interfaces**:
- `ContextAnalyzer.analyze_changes(files)` - Analyze changed files
- `ContextAnalyzer.classify_file_type(file)` - Classify file type
- `ContextAnalyzer.analyze_commit_scope(changed_files)` - Analyze commit scope
- `ContextAnalyzer.get_branch_context()` - Get current branch context
- `ContextAnalyzer.suggest_commands(context)` - Suggest commands based on context

**Enhancements to Existing**:
- Extend `tapps_agents/workflow/context_analyzer.py`
- Add change pattern detection methods
- Add file type classification
- Add commit analysis methods
- Add confidence scoring

**Dependencies**:
- Git (for branch/commit analysis)
- File system (for file type detection)

---

### 4. Command Scheduler
**Purpose**: Manages execution queue and prioritization

**Responsibilities**:
- Queue command executions
- Prioritize commands (user commands > auto commands)
- Execute commands asynchronously
- Handle command failures and retries
- Rate limit automatic commands
- Integrate with resource monitor for throttling

**Interfaces**:
- `CommandScheduler.schedule(command, priority)` - Schedule command execution
- `CommandScheduler.execute(command)` - Execute command asynchronously
- `CommandScheduler.get_queue_status()` - Get queue status
- `CommandScheduler.cancel(command_id)` - Cancel scheduled command

**Execution Model**:
- Async execution using `asyncio`
- Priority queue (user commands first)
- Rate limiting (max N commands/hour)
- Resource-aware throttling (pause when CPU high)

**Dependencies**:
- CLI command execution (subprocess/process)
- Resource Monitor
- Notification System (for status updates)

**Location**: `tapps_agents/automation/command_scheduler.py`

---

### 5. Notification Service
**Purpose**: Handles user feedback and results

**Responsibilities**:
- Send toast notifications
- Update status bar indicators
- Post results to results panel
- Integrate with Cursor chat
- Show badge indicators
- Manage notification preferences

**Interfaces**:
- `NotificationService.notify(message, type)` - Send notification
- `NotificationService.update_status(status)` - Update status indicator
- `NotificationService.show_results(command, results)` - Show command results
- `NotificationService.post_to_chat(message)` - Post to Cursor chat

**Notification Channels**:
- Console output (stdout/stderr)
- File-based (results saved to files)
- Chat integration (Cursor chat API if available)
- Status indicators (configurable)

**Dependencies**:
- Configuration System (notification preferences)
- Feedback system (existing)

**Location**: `tapps_agents/automation/notifications.py`

---

### 6. Resource Monitor
**Purpose**: Tracks system resources and adapts execution

**Responsibilities**:
- Monitor CPU usage
- Monitor memory usage
- Detect battery power (laptop)
- Detect user activity (typing, mouse movement)
- Provide resource status to scheduler
- Recommend throttling actions

**Interfaces**:
- `ResourceMonitor.get_cpu_usage()` - Get CPU usage percentage
- `ResourceMonitor.get_memory_usage()` - Get memory usage percentage
- `ResourceMonitor.is_on_battery()` - Check if on battery power
- `ResourceMonitor.is_user_active()` - Check if user is actively working
- `ResourceMonitor.should_throttle()` - Recommend throttling

**Throttling Logic**:
- CPU >80% → pause automation
- Battery power → reduce automation frequency
- User actively typing → pause file watcher
- Memory >90% → defer non-critical commands

**Dependencies**:
- `psutil` library (system resource monitoring)
- File system events (for user activity detection)

**Location**: `tapps_agents/automation/resource_monitor.py`

---

### 7. Configuration Manager
**Purpose**: Manages automation settings

**Responsibilities**:
- Load automation configuration
- Validate configuration schema
- Provide configuration access to components
- Migrate from old config format
- Handle configuration errors

**Interfaces**:
- `AutomationConfig.load()` - Load from config file
- `AutomationConfig.validate()` - Validate configuration
- `AutomationConfig.get_triggers()` - Get trigger definitions
- `AutomationConfig.get_automation_level()` - Get current automation level
- `AutomationConfig.migrate()` - Migrate from old format

**Configuration Schema**:
```yaml
automation:
  level: 2  # 0=manual, 1=suggest, 2=non-blocking, 3=smart, 4=full
  triggers:
    file_save:
      enabled: true
      debounce_seconds: 5
      commands: ["reviewer score"]
      automation_level: 2
    git_pre_commit:
      enabled: true
      commands: ["reviewer lint", "reviewer type-check"]
      automation_level: 2
  notifications:
    enabled: true
    channels: ["console", "chat"]
  resources:
    cpu_threshold: 80
    battery_aware: true
    rate_limit: 10  # max commands per hour
```

**Dependencies**:
- ProjectConfig (extend existing config)
- YAML parser

**Location**: `tapps_agents/core/config.py` (extend), `tapps_agents/automation/config.py`

---

### 8. Git Hook Manager
**Purpose**: Manages git hook installation and execution

**Responsibilities**:
- Install git hooks (pre-commit, post-commit, pre-push, pre-merge)
- Uninstall git hooks
- Validate hook scripts (security)
- Execute hooks via framework CLI
- Handle hook failures gracefully

**Interfaces**:
- `GitHookManager.install_hooks()` - Install all hooks
- `GitHookManager.uninstall_hooks()` - Uninstall all hooks
- `GitHookManager.install_hook(name, script)` - Install specific hook
- `GitHookManager.validate_hook(script)` - Validate hook script

**Hook Scripts**:
- Pre-commit: Fast checks (lint, type-check)
- Post-commit: Comprehensive analysis (background)
- Pre-push: Full quality gates (blocking)
- Pre-merge: Security checks (blocking for main)

**Dependencies**:
- Git repository (.git/hooks/)
- CLI command execution
- Configuration System

**Location**: `tapps_agents/automation/git_hooks.py`

---

## Data Flow

### File Save Event Flow

```
1. User saves file
   ↓
2. File System (OS) emits file change event
   ↓
3. Event Monitor detects event
   ↓
4. Event Monitor filters (respect .gitignore, file patterns)
   ↓
5. Event Monitor debounces (wait 5 seconds)
   ↓
6. Event Monitor emits "file_save" event to Event Bus
   ↓
7. Trigger Registry receives event
   ↓
8. Trigger Registry finds matching triggers (file_save → reviewer score)
   ↓
9. Trigger Registry evaluates conditions (file pattern matches?)
   ↓
10. Trigger Registry resolves command ("reviewer score {file_path}")
    ↓
11. Command Scheduler receives command
    ↓
12. Command Scheduler checks automation level (Level 2: non-blocking)
    ↓
13. Command Scheduler checks resources (CPU OK, user active?)
    ↓
14. Command Scheduler queues command (background execution)
    ↓
15. Command Scheduler executes command asynchronously
    ↓
16. Notification Service sends status ("Running quality check...")
    ↓
17. Command execution completes
    ↓
18. Notification Service shows results (score, issues)
```

### Git Pre-Commit Hook Flow

```
1. User runs "git commit"
   ↓
2. Git calls pre-commit hook
   ↓
3. Git Hook Manager executes hook script
   ↓
4. Hook script calls: "tapps-agents reviewer lint --staged"
   ↓
5. Command executes (blocking, fast)
   ↓
6. If successful: Commit proceeds
   ↓
7. If failed: Commit blocked, show errors
```

---

## Integration Points

### With Existing Systems

**Configuration System**:
- Extend `ProjectConfig` in `tapps_agents/core/config.py`
- Add `AutomationConfig` model
- Integrate with existing config loader

**Event System**:
- Use existing `FileBasedEventBus` from workflow system
- Extend event types for automation events
- Reuse event serialization/deserialization

**CLI Commands**:
- Automation wraps existing CLI commands
- No changes to command implementations
- Commands remain usable standalone

**Workflow System**:
- Automation can trigger workflow executions
- Workflow system can emit events for automation
- Shared event bus for coordination

**Feedback System**:
- Extend existing feedback system for notifications
- Reuse feedback formats (JSON, text, markdown)
- Integrate with progress reporting

---

## Component Dependencies

```
Configuration Manager
  ├─> Event Monitor
  ├─> Trigger Registry
  ├─> Command Scheduler
  ├─> Notification Service
  ├─> Resource Monitor
  └─> Git Hook Manager

Event Monitor
  ├─> Trigger Registry
  └─> Resource Monitor (for throttling)

Trigger Registry
  ├─> Context Analyzer
  └─> Command Scheduler

Command Scheduler
  ├─> Resource Monitor
  └─> Notification Service

Git Hook Manager
  ├─> Configuration Manager
  └─> Command Scheduler

Notification Service
  └─> Configuration Manager

Resource Monitor
  └─> Command Scheduler (for throttling recommendations)
```

---

## Technology Stack

**Core Libraries**:
- `watchdog` - File system monitoring (cross-platform)
- `psutil` - System resource monitoring
- `gitpython` - Git operations (optional, fallback to subprocess)
- `asyncio` - Async execution (Python standard library)
- `yaml` - Configuration parsing (PyYAML, already used)

**Integration**:
- FileBasedEventBus (existing, workflow system)
- ProjectConfig (existing, core system)
- CLI command execution (existing, subprocess)

**Platform Support**:
- Windows (watchdog supports Windows)
- macOS (watchdog supports macOS)
- Linux (watchdog supports Linux)

---

## Scalability Considerations

**Performance**:
- File watcher overhead: <1% CPU when idle
- Event processing: Async to avoid blocking
- Debouncing: Prevents excessive executions
- Rate limiting: Prevents resource exhaustion

**Resource Management**:
- CPU throttling: Pause when CPU >80%
- Memory management: Defer non-critical commands when memory high
- Battery awareness: Reduce frequency on battery
- User activity: Pause when user actively working

**Extensibility**:
- New trigger types: Add to trigger registry
- New commands: No code changes needed (use existing CLI)
- New automation levels: Extend level evaluator
- New notification channels: Extend notification service

---

## Security Considerations

**Git Hooks**:
- Validate hook scripts before installation
- Prevent malicious hook execution
- Use framework CLI commands (not arbitrary scripts)

**File Watching**:
- Respect .gitignore and .cursorignore
- Don't watch sensitive directories
- Filter file patterns to prevent excessive monitoring

**Configuration**:
- Validate configuration schema
- Prevent injection attacks in command parameters
- Rate limiting to prevent resource exhaustion

**User Approval**:
- Level 1 requires user approval
- All automation can be disabled
- Clear feedback on what automation runs

---

## Error Handling

**Event Monitor Failures**:
- Graceful degradation if file watcher fails
- Fallback to polling if watchdog unavailable
- Log errors, don't crash system

**Command Execution Failures**:
- Retry logic for transient failures
- Error notifications to user
- Don't block user workflow

**Resource Exhaustion**:
- Throttle automation when resources low
- Queue commands for later execution
- Clear error messages to user

**Configuration Errors**:
- Validate on load, show clear errors
- Fallback to safe defaults
- Migration tool handles format changes

---

## Testing Strategy

**Unit Tests**:
- Each component tested in isolation
- Mock dependencies (file system, git, resources)
- Test error handling and edge cases

**Integration Tests**:
- Test component interactions
- Test event flow end-to-end
- Test git hook execution

**E2E Tests**:
- Test file watcher scenarios
- Test git hook scenarios
- Test automation level behaviors

**Performance Tests**:
- Measure file watcher overhead
- Measure resource usage
- Test throttling behavior

---

## Migration Path

**From Background Agents**:
1. Read background-agents.yaml configuration
2. Map agents to triggers (Quality Analyzer → file_save trigger)
3. Convert to new automation config format
4. Migrate user preferences
5. Provide migration tool: `tapps-agents migrate-automation-config`

**Backward Compatibility**:
- Existing CLI commands unchanged
- Existing config structure preserved (new section added)
- Background agents config can coexist (deprecated)
