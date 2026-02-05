# Background Process Enhancements - Summary

**Created:** 2026-02-04
**Status:** Proposed
**Priority:** High
**GitHub Issue:** [Link to be added]

## Quick Summary

Enhance TappsCodingAgents background process execution with:
1. **Pre-flight validation** - Check everything before launching
2. **Real-time monitoring** - Track process health and progress
3. **Smart notifications** - Desktop/terminal alerts on completion/failure
4. **CLI management** - `tapps-agents bg` commands for process control

## The Problem

When you run:
```bash
tapps-agents simple-mode full --prompt "..." --auto
```

Current behavior:
- ✅ Returns immediately with process ID
- ❌ No validation before launch
- ❌ Process can fail silently
- ❌ No notification when done/failed
- ❌ Must manually check output files

Result: **Silent failures that waste user time**

Example from today's session:
```
[ERROR] Workflow blocked: no ready steps
Missing: requirements.md, stories/, architecture.md, etc.
```

User had no idea until manually checking the output file.

## The Solution

### Phase 1: Pre-Flight Validation
**Before** launching background process:
- ✅ Check required files exist
- ✅ Validate permissions
- ✅ Verify dependencies
- ✅ Validate configuration
- ✅ **Fail fast** with clear error message

### Phase 2: Real-Time Monitoring
**During** process execution:
- ✅ Health checks every 30 seconds
- ✅ Progress tracking (0-100%)
- ✅ Automatic failure detection
- ✅ Process database tracking

### Phase 3: Smart Notifications
**After** process completes/fails:
- ✅ Desktop notification (Windows/macOS/Linux)
- ✅ Terminal notification
- ✅ Summary with key metrics
- ✅ Auto-cleanup completed processes

### Phase 4: CLI Management
**New commands:**
```bash
# Check status of specific process
tapps-agents bg status abc123

# List all processes
tapps-agents bg list
tapps-agents bg list --status running
tapps-agents bg list --status failed

# Follow logs in real-time
tapps-agents bg logs abc123 --follow

# Stop running process
tapps-agents bg stop abc123

# Clean up old processes
tapps-agents bg cleanup --older-than 7
```

## Configuration

New section in `.tapps-agents/config.yaml`:

```yaml
background_processes:
  validation_enabled: true
  monitoring_enabled: true
  health_check_interval: 30  # seconds

  notifications:
    desktop_enabled: true      # Desktop notifications
    terminal_enabled: true     # Terminal notifications
    progress_enabled: false    # Progress updates (optional)

  max_concurrent_processes: 3
  max_process_runtime: 7200   # 2 hours
  auto_cleanup_days: 7        # Remove old processes after 7 days
```

## User Experience - Before and After

### Before (Current):
```bash
$ tapps-agents simple-mode full --prompt "..." --auto
Command running in background with ID: bff52f4
Output: /tmp/.../bff52f4.output

# [User waits... no idea what's happening]
# [Process fails silently]
# [User checks file manually 30 minutes later]
# [Discovers it failed in first 5 seconds]
# [Wasted 30 minutes]
```

### After (Enhanced):
```bash
$ tapps-agents simple-mode full --prompt "..." --auto

# Pre-flight validation
✅ Validating workflow requirements...
✅ Checking dependencies... OK
✅ Checking permissions... OK
✅ Validating configuration... OK

# Launch
✅ Workflow launched successfully (ID: abc123)
📊 Monitor: tapps-agents bg status abc123

# [Process runs in background]
# [Health checks every 30 seconds]

# 15 minutes later...
[Desktop Notification]
✅ Workflow Complete
full-sdlc workflow completed successfully

# Or if it fails...
[Desktop Notification]
❌ Workflow Failed
full-sdlc workflow failed after 5 seconds
Run: tapps-agents bg logs abc123
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Background Launcher                     │
│  (Pre-flight validation before launching)               │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ├──────────────────────────────┐
                      │                              │
              ┌───────▼────────┐          ┌─────────▼────────┐
              │  Process        │          │  Health Check    │
              │  Database       │◄─────────│  Daemon          │
              └───────┬────────┘          └─────────┬────────┘
                      │                              │
                      │                    Every 30 seconds
                      │                              │
              ┌───────▼────────┐          ┌─────────▼────────┐
              │  Status         │          │  Notifier        │
              │  Tracker        │──────────►  (Desktop/Term)  │
              └────────────────┘          └──────────────────┘
```

## Components

### Core Modules
1. **BackgroundProcessValidator** - Pre-flight validation
2. **BackgroundProcessMonitor** - Health checks and tracking
3. **BackgroundNotifier** - Desktop and terminal notifications
4. **BackgroundHealthDaemon** - Automatic health check daemon

### CLI Commands
1. **bg status** - Show process status
2. **bg list** - List all processes
3. **bg logs** - Show/follow process logs
4. **bg stop** - Stop running process
5. **bg cleanup** - Remove old processes

### Database
- SQLite database: `.tapps-agents/background_processes.db`
- Tracks: process_id, status, progress, started_at, completed_at, errors
- Indexes: status, started_at for fast queries

## Implementation Timeline

### Phase 1: Validation (Weeks 1-2)
- BackgroundProcessValidator
- File/dependency/permission checking
- Integration with launch commands

### Phase 2: Monitoring (Weeks 3-4)
- BackgroundProcessMonitor
- Health check logic
- Progress tracking
- Process database

### Phase 3: Notifications (Week 5)
- BackgroundNotifier
- Desktop notifications (Windows/macOS/Linux)
- Terminal notifications
- Log formatting

### Phase 4: CLI (Week 6)
- bg command group
- status, list, logs, stop, cleanup commands
- Rich table formatting

### Phase 5: Testing (Week 7)
- Unit tests (90% coverage)
- Integration tests
- Cross-platform testing
- User acceptance testing

## Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Pre-launch validation catches errors | 95% | 0% |
| Failure detection time | < 30s | Never |
| User notification on completion | 100% | 0% |
| User notification on failure | 100% | 0% |
| User satisfaction | ≥ 80% | Low |

## Breaking Changes

**None** - This is backward compatible:
- Old behavior still works (no validation if disabled)
- New features opt-in via config
- Existing output files still work

## Migration Path

### For Users
1. Update TappsCodingAgents to v3.6.0
2. Run `tapps-agents init --reset` to get new config section
3. Enable notifications in config (or keep defaults)
4. Start using `tapps-agents bg` commands

### For Developers
1. Import new modules
2. Use `BackgroundLauncher` instead of direct subprocess
3. Register processes with monitor
4. Update tests to use new validation

## Testing Plan

### Unit Tests
- ✅ Validator checks all conditions
- ✅ Monitor detects failures
- ✅ Notifier sends notifications
- ✅ Daemon runs health checks

### Integration Tests
- ✅ Full workflow with validation
- ✅ Health checks detect failure
- ✅ Notifications sent on completion/failure
- ✅ CLI commands work correctly

### Platform Tests
- ✅ Windows: Desktop notifications work
- ✅ macOS: Desktop notifications work
- ✅ Linux: Desktop notifications work
- ✅ All: Terminal notifications work

### User Acceptance Tests
- ✅ User launches workflow
- ✅ Validation catches missing files
- ✅ User gets notified when done
- ✅ User checks status easily
- ✅ User reviews logs easily

## Related Issues

- **Silent workflow failures** - Workflows fail without notification
- **No process monitoring** - Can't check status without reading files
- **Missing validation** - Processes launch even when guaranteed to fail
- **Poor UX** - Users waste time waiting for failed processes

## Next Steps

1. **Create GitHub issue** from template
2. **Get team approval** on design
3. **Start Phase 1** (Validation)
4. **Weekly progress updates**
5. **Alpha testing** after Phase 3
6. **Beta release** in v3.6.0-beta
7. **Final release** in v3.6.0

## Questions & Answers

### Q: Will this slow down background process launch?
**A:** Validation adds ~100ms. Totally worth it to avoid silent failures.

### Q: What if I don't want notifications?
**A:** Disable in config: `notifications.desktop_enabled: false`

### Q: Will this work with existing workflows?
**A:** Yes! Backward compatible. Old workflows still work.

### Q: Can I monitor multiple processes?
**A:** Yes! `tapps-agents bg list` shows all processes.

### Q: What about process limits?
**A:** Configurable: `max_concurrent_processes: 3`

## Documentation Updates

### New Docs
- `docs/BACKGROUND_PROCESSES.md` - Complete guide
- `docs/BACKGROUND_PROCESS_CLI.md` - CLI reference
- `docs/BACKGROUND_NOTIFICATIONS.md` - Notification setup

### Updated Docs
- `docs/GETTING_STARTED.md` - Add bg commands
- `docs/CLI_REFERENCE.md` - Add bg command group
- `docs/CONFIGURATION.md` - Add bg config section
- `docs/TROUBLESHOOTING.md` - Add bg troubleshooting

## Contact

**Issue:** [Link to GitHub issue]
**Design Doc:** [This file]
**Discussion:** [Link to discussion]
**Status:** Proposed (pending team approval)

---

**Last Updated:** 2026-02-04
**Author:** TappsCodingAgents Team
**Reviewers:** [To be added]
**Approved:** [Pending]
