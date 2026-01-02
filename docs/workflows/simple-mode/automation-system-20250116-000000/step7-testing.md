# Step 7: Testing Plan - Automatic Execution System

**Generated**: 2025-01-16  
**Workflow**: Build - Automation System Implementation  
**Agent**: @tester  
**Depends on**: Step 6 - Code Review

---

## Testing Strategy Overview

This document provides a comprehensive testing plan for the Automatic Execution System, covering unit tests, integration tests, E2E tests, and performance tests.

**Test Coverage Goal**: >80%  
**Testing Approach**: Test-driven development where possible, comprehensive coverage for critical paths

---

## Unit Tests

### 1. Configuration System Tests

**File**: `tests/automation/test_config.py`

**Test Cases**:
- ✅ Load automation config from YAML
- ✅ Validate automation level (0-4)
- ✅ Validate trigger configurations
- ✅ Validate notification configurations
- ✅ Validate resource configurations
- ✅ Handle missing automation config (use defaults)
- ✅ Handle invalid automation level (raise error)
- ✅ Handle invalid trigger configuration (raise error)
- ✅ Migration from background-agents.yaml
- ✅ Migration preserves user customizations

**Mock Requirements**:
- Mock file system for config file reading
- Mock YAML parsing

**Coverage Target**: 90%

---

### 2. Event Monitor Tests

**File**: `tests/automation/test_event_monitor.py`

**Test Cases**:
- ✅ Start event monitoring
- ✅ Stop event monitoring
- ✅ Detect file save events
- ✅ Detect file create events
- ✅ Detect file delete events
- ✅ Filter events (respect .gitignore)
- ✅ Debounce file events (wait before emitting)
- ✅ Batch multiple file changes
- ✅ Handle file system errors gracefully
- ✅ Handle missing files/directories
- ✅ Emit events to event bus
- ✅ Handle watchdog library errors

**Mock Requirements**:
- Mock watchdog Observer
- Mock file system events
- Mock event bus
- Mock .gitignore patterns

**Coverage Target**: 85%

---

### 3. Trigger Registry Tests

**File**: `tests/automation/test_trigger_registry.py`

**Test Cases**:
- ✅ Load triggers from configuration
- ✅ Find matching triggers for event
- ✅ Evaluate file pattern conditions
- ✅ Evaluate branch pattern conditions
- ✅ Evaluate time-based conditions
- ✅ Resolve command with parameters
- ✅ Validate command exists
- ✅ Handle invalid triggers (skip)
- ✅ Sort triggers by priority
- ✅ Filter by automation level
- ✅ Handle missing conditions (default to True)

**Mock Requirements**:
- Mock configuration
- Mock events
- Mock command validation

**Coverage Target**: 90%

---

### 4. Command Scheduler Tests

**File**: `tests/automation/test_command_scheduler.py`

**Test Cases**:
- ✅ Schedule command with priority
- ✅ Execute command asynchronously
- ✅ Queue commands by priority
- ✅ Check automation level before execution
- ✅ Check rate limit before execution
- ✅ Handle command execution errors
- ✅ Handle command timeouts
- ✅ Cancel scheduled command
- ✅ Get queue status
- ✅ Handle queue full (reject low priority)
- ✅ Retry failed commands (transient failures)
- ✅ Rate limiting (max N commands/hour)

**Mock Requirements**:
- Mock command execution (subprocess)
- Mock resource monitor
- Mock notification service
- Mock time for rate limiting

**Coverage Target**: 85%

---

### 5. Git Hook Manager Tests

**File**: `tests/automation/test_git_hooks.py`

**Test Cases**:
- ✅ Install pre-commit hook
- ✅ Install post-commit hook
- ✅ Install pre-push hook
- ✅ Install pre-merge hook
- ✅ Uninstall all hooks
- ✅ Validate hook scripts (security)
- ✅ Handle missing .git directory
- ✅ Handle existing hooks (backup)
- ✅ Make hooks executable (Unix)
- ✅ Handle hook installation errors
- ✅ Handle hook validation failures

**Mock Requirements**:
- Mock .git/hooks directory
- Mock file system operations
- Mock git repository detection

**Coverage Target**: 90%

---

### 6. Resource Monitor Tests

**File**: `tests/automation/test_resource_monitor.py`

**Test Cases**:
- ✅ Get CPU usage
- ✅ Get memory usage
- ✅ Detect battery power
- ✅ Detect user activity
- ✅ Recommend throttling (CPU high)
- ✅ Recommend throttling (battery power)
- ✅ Recommend throttling (user active)
- ✅ Handle psutil errors gracefully
- ✅ Cache resource measurements
- ✅ Handle missing psutil (graceful degradation)

**Mock Requirements**:
- Mock psutil for CPU/memory/battery
- Mock file system for user activity
- Mock time for caching

**Coverage Target**: 85%

---

### 7. Notification Service Tests

**File**: `tests/automation/test_notifications.py`

**Test Cases**:
- ✅ Send console notification
- ✅ Send file notification
- ✅ Update status indicator
- ✅ Show command results
- ✅ Handle notification errors gracefully
- ✅ Respect notification preferences (disabled)
- ✅ Format notifications correctly
- ✅ Handle missing notification channels

**Mock Requirements**:
- Mock console output
- Mock file system for file notifications
- Mock chat API (if available)

**Coverage Target**: 80%

---

## Integration Tests

### 1. Event → Trigger → Command Flow

**File**: `tests/automation/test_integration_event_flow.py`

**Test Scenarios**:
- ✅ File save → trigger → command execution
- ✅ Git pre-commit → trigger → command execution
- ✅ Multiple triggers for same event
- ✅ Trigger conditions filter events correctly
- ✅ Command parameters resolved correctly
- ✅ Automation level filtering works
- ✅ Priority ordering works

**Test Setup**:
- Real event monitor (mocked file system)
- Real trigger registry (test config)
- Mocked command execution
- Real event bus

**Coverage Target**: Core integration paths

---

### 2. Git Hook Integration

**File**: `tests/automation/test_integration_git_hooks.py`

**Test Scenarios**:
- ✅ Pre-commit hook runs commands
- ✅ Pre-commit hook blocks commit on failure
- ✅ Post-commit hook runs in background
- ✅ Pre-push hook runs full analysis
- ✅ Hook validation prevents malicious scripts
- ✅ Hook uninstallation removes hooks
- ✅ Multiple hooks can coexist

**Test Setup**:
- Temporary git repository
- Real hook manager
- Mocked command execution
- Real git operations

**Coverage Target**: All git hook types

---

### 3. Resource Management Integration

**File**: `tests/automation/test_integration_resources.py`

**Test Scenarios**:
- ✅ High CPU → automation throttled
- ✅ Battery power → automation reduced
- ✅ User active → file watcher paused
- ✅ Rate limiting → commands rejected
- ✅ Resource recovery → automation resumed

**Test Setup**:
- Real resource monitor (mocked psutil)
- Real command scheduler
- Mocked command execution
- Controlled resource conditions

**Coverage Target**: All resource scenarios

---

### 4. Configuration Migration

**File**: `tests/automation/test_integration_migration.py`

**Test Scenarios**:
- ✅ Migrate background-agents.yaml → automation config
- ✅ Preserve user customizations
- ✅ Handle missing background-agents.yaml
- ✅ Handle invalid background-agents.yaml
- ✅ Backup original config
- ✅ Rollback migration on error

**Test Setup**:
- Sample background-agents.yaml files
- Real migration tool
- Real configuration loader
- Temporary file system

**Coverage Target**: Migration paths

---

## E2E Tests

### 1. File Watcher E2E

**File**: `tests/automation/test_e2e_file_watcher.py`

**Test Scenarios**:
- ✅ Save Python file → quality check runs automatically
- ✅ Save multiple files → batch review runs
- ✅ Save config file → no quality check (filtered)
- ✅ Debounce works (wait before triggering)
- ✅ Resource throttling pauses watcher
- ✅ User activity detection pauses watcher

**Test Setup**:
- Real file system (temporary directory)
- Real event monitor (watchdog)
- Real trigger registry (test config)
- Mocked command execution
- Real resource monitor

**Test Duration**: ~30 seconds per scenario

---

### 2. Git Hook E2E

**File**: `tests/automation/test_e2e_git_hooks.py`

**Test Scenarios**:
- ✅ Install hooks → commit → hooks run
- ✅ Pre-commit fails → commit blocked
- ✅ Pre-commit passes → commit succeeds
- ✅ Post-commit runs in background
- ✅ Pre-push runs full analysis
- ✅ Uninstall hooks → hooks don't run

**Test Setup**:
- Temporary git repository
- Real hook manager
- Real git operations
- Mocked command execution (fast commands)

**Test Duration**: ~10 seconds per scenario

---

### 3. Automation Levels E2E

**File**: `tests/automation/test_e2e_automation_levels.py`

**Test Scenarios**:
- ✅ Level 0: No automation (commands don't run)
- ✅ Level 1: Suggestions only (user approval required)
- ✅ Level 2: Non-blocking automation (runs in background)
- ✅ Level 3: Smart auto (blocks on critical issues)
- ✅ Level 4: Full auto (fully autonomous)

**Test Setup**:
- Real automation system
- Test configuration for each level
- Mocked command execution
- User interaction simulation (for Level 1)

**Test Duration**: ~20 seconds per level

---

### 4. Configuration Migration E2E

**File**: `tests/automation/test_e2e_migration.py`

**Test Scenarios**:
- ✅ Migrate real background-agents.yaml
- ✅ Verify migrated triggers work
- ✅ Verify user customizations preserved
- ✅ Rollback migration
- ✅ Verify backward compatibility

**Test Setup**:
- Real background-agents.yaml files
- Real migration tool
- Real automation system
- Mocked command execution

**Test Duration**: ~15 seconds per scenario

---

## Performance Tests

### 1. File Watcher Performance

**File**: `tests/automation/test_performance_file_watcher.py`

**Performance Criteria**:
- ✅ CPU usage <1% when idle
- ✅ Event processing latency <100ms
- ✅ Debounce delay accuracy (±500ms)
- ✅ Memory usage stable (no leaks)
- ✅ Handle 1000+ file events without degradation

**Test Setup**:
- Real file system (temporary directory)
- Real event monitor
- Performance monitoring (psutil)
- Stress test (rapid file changes)

**Success Criteria**:
- CPU usage <1% when idle
- Memory usage stable over 1 hour
- No performance degradation with 1000+ events

---

### 2. Command Scheduler Performance

**File**: `tests/automation/test_performance_scheduler.py`

**Performance Criteria**:
- ✅ Queue processing latency <50ms
- ✅ Command execution overhead <10ms
- ✅ Rate limiting accuracy (±1 command/hour)
- ✅ Priority queue efficiency (O(log n))

**Test Setup**:
- Real command scheduler
- Mocked command execution (fast)
- Performance monitoring
- Stress test (1000+ queued commands)

**Success Criteria**:
- Queue processing <50ms per command
- Rate limiting accurate within 1 command/hour
- No performance degradation with 1000+ queued commands

---

### 3. Resource Monitor Performance

**File**: `tests/automation/test_performance_resources.py`

**Performance Criteria**:
- ✅ Resource monitoring overhead <1% CPU
- ✅ Monitoring latency <10ms
- ✅ Caching reduces CPU usage
- ✅ Throttling response time <100ms

**Test Setup**:
- Real resource monitor
- Performance monitoring
- Controlled resource conditions
- Stress test (continuous monitoring)

**Success Criteria**:
- Monitoring overhead <1% CPU
- Throttling responds within 100ms
- Caching reduces CPU by >50%

---

## Test Data and Fixtures

### Test Configuration Files

**Location**: `tests/automation/fixtures/`

**Files**:
- `config_automation_level_0.yaml` - Level 0 (manual)
- `config_automation_level_2.yaml` - Level 2 (non-blocking)
- `config_automation_level_4.yaml` - Level 4 (full auto)
- `config_background_agents.yaml` - Sample background-agents.yaml
- `config_invalid.yaml` - Invalid config (error testing)

### Test Event Data

**Location**: `tests/automation/fixtures/events/`

**Files**:
- `file_save_event.json` - File save event sample
- `git_pre_commit_event.json` - Git pre-commit event sample
- `multiple_file_events.json` - Batch file events

### Test Git Repositories

**Location**: `tests/automation/fixtures/git_repos/`

- Temporary git repositories created in tests
- Sample projects with various file types
- Pre-configured hooks for testing

---

## Test Execution Strategy

### Local Development

**Run all tests**:
```bash
pytest tests/automation/ -v
```

**Run specific test category**:
```bash
pytest tests/automation/test_event_monitor.py -v
pytest tests/automation/test_integration_*.py -v
pytest tests/automation/test_e2e_*.py -v
pytest tests/automation/test_performance_*.py -v
```

**Run with coverage**:
```bash
pytest tests/automation/ --cov=tapps_agents.automation --cov-report=html
```

### CI/CD Integration

**Test Stages**:
1. **Unit Tests** (fast, run on every commit)
2. **Integration Tests** (medium, run on PRs)
3. **E2E Tests** (slower, run on main branch)
4. **Performance Tests** (slowest, run nightly)

**CI Configuration**:
- Unit tests: <5 minutes
- Integration tests: <15 minutes
- E2E tests: <30 minutes
- Performance tests: <1 hour

---

## Test Coverage Goals

**Overall Coverage**: >80%

**Component Coverage**:
- Configuration System: 90%
- Event Monitor: 85%
- Trigger Registry: 90%
- Command Scheduler: 85%
- Git Hook Manager: 90%
- Resource Monitor: 85%
- Notification Service: 80%

**Critical Path Coverage**: 100%
- Event → Trigger → Command flow
- Git hook execution
- Resource throttling
- Configuration migration

---

## Test Maintenance

### Adding New Tests

**Guidelines**:
- Follow existing test patterns
- Use fixtures for common setup
- Mock external dependencies
- Clear test names and descriptions
- Add comments for complex scenarios

### Updating Tests

**When to Update**:
- Configuration schema changes
- Component interface changes
- New trigger types added
- New automation levels added

**Update Process**:
1. Update test fixtures if needed
2. Update test cases for new behavior
3. Add tests for new features
4. Verify coverage maintained

---

## Known Test Limitations

1. **File System Events**
   - May be platform-dependent
   - Test on multiple platforms (Windows, macOS, Linux)
   - Handle platform-specific behaviors

2. **Git Operations**
   - Require git repository
   - May be slow in CI/CD
   - Use temporary repositories

3. **Resource Monitoring**
   - May vary by system
   - Use mocked psutil for consistency
   - Test on different system configurations

4. **Time-Dependent Tests**
   - Debouncing, rate limiting depend on time
   - Use mocked time for deterministic tests
   - Use real time for performance tests

---

## Conclusion

This comprehensive testing plan covers all components of the Automatic Execution System with unit, integration, E2E, and performance tests. The plan aims for >80% coverage with focus on critical paths and user-facing functionality.

**Key Testing Areas**:
- ✅ Configuration system (validation, migration)
- ✅ Event monitoring (file system, git)
- ✅ Trigger resolution (matching, conditions)
- ✅ Command execution (scheduling, prioritization)
- ✅ Resource management (throttling, monitoring)
- ✅ Git hook integration (installation, execution)

**Next Steps**:
1. Implement test fixtures and helpers
2. Start with unit tests (foundation)
3. Add integration tests as components integrate
4. Add E2E tests for complete workflows
5. Add performance tests for optimization

---

## Summary

✅ **Test Plan Complete**
- Unit tests: 7 test files, ~100 test cases
- Integration tests: 4 test files, ~20 scenarios
- E2E tests: 4 test files, ~15 scenarios
- Performance tests: 3 test files, performance criteria defined

✅ **Coverage Goals**: >80% overall, 100% critical paths

✅ **Test Execution**: Local and CI/CD strategies defined

✅ **Test Maintenance**: Guidelines and update process documented
