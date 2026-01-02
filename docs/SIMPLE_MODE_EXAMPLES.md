# Simple Mode Examples Gallery

**Date**: 2025-01-16  
**Status**: Updated for Phase 2 Features

---

## Table of Contents

1. [Basic Build Workflow](#basic-build-workflow)
2. [Fast Mode Build](#fast-mode-build)
3. [Custom Status Tracking](#custom-status-tracking)
4. [Error Recovery Integration](#error-recovery-integration)
5. [Workflow Preview](#workflow-preview)
6. [Advanced: Custom Callbacks](#advanced-custom-callbacks)

---

## Basic Build Workflow

### Example: Add User Authentication

**Command**:
```bash
tapps-agents simple-mode build --prompt "Add user authentication with JWT tokens"
```

**Output**:
```
============================================================
Simple Mode Build Workflow
============================================================
Feature: Add user authentication with JWT tokens
Mode: Complete (all 7 steps)

============================================================
Workflow Preview
============================================================
Feature: Add user authentication with JWT tokens
Mode: Complete (7 steps)

Steps to Execute:
  1. Enhance prompt (requirements analysis)     ~2s
  2. Create user stories                        ~2s
  3. Design architecture                         ~3s
  4. Design API/data models                      ~3s
  5. Implement code                             ~5s
  6. Review code quality                         ~2s
  7. Generate tests                              ~2s

Estimated Total Time: ~19s
Configuration: automation.level=2, fast_mode=false

============================================================

Executing build workflow...
Runtime mode: headless
Auto-execution: disabled

[OK] Running in headless mode - direct execution with terminal output

[1/7] Enhance prompt (requirements analysis)... [OK] (2.1s)
[2/7] Create user stories... [OK] (1.8s)
[3/7] Design architecture... [OK] (3.2s)
[4/7] Design API/data models... [OK] (2.9s)
[5/7] Implement code... [OK] (5.3s)
[6/7] Review code quality... [OK] (2.0s)
[7/7] Generate tests... [OK] (1.9s)

============================================================
Execution Summary
============================================================
Steps Executed: 7/7
Total Time: 19.2s

Step Details:
  [OK] Step 1: Enhance prompt (requirements analysis) (2.1s)
  [OK] Step 2: Create user stories (1.8s)
  [OK] Step 3: Design architecture (3.2s)
  [OK] Step 4: Design API/data models (2.9s)
  [OK] Step 5: Implement code (5.3s)
  [OK] Step 6: Review code quality (2.0s)
  [OK] Step 7: Generate tests (1.9s)

✅ Build workflow completed successfully!

Workflow ID: build-20250116-143022
Steps executed: 7
```

---

## Fast Mode Build

### Example: Quick Feature Addition

**Command**:
```bash
tapps-agents simple-mode build --prompt "Add password reset endpoint" --fast
```

**Output**:
```
============================================================
Simple Mode Build Workflow
============================================================
Feature: Add password reset endpoint
Mode: Fast (skipping documentation steps 1-4)

============================================================
Workflow Preview
============================================================
Feature: Add password reset endpoint
Mode: Fast (4 steps)

Steps to Execute:
  5. Implement code                             ~5s
  6. Review code quality                         ~2s
  7. Generate tests                              ~2s

Estimated Total Time: ~9s
Configuration: automation.level=2, fast_mode=true

============================================================

Executing build workflow...

[1/4] Implement code... [OK] (5.1s)
[2/4] Review code quality... [OK] (2.0s)
[3/4] Generate tests... [OK] (1.9s)

============================================================
Execution Summary
============================================================
Steps Executed: 3/4
Total Time: 9.0s

Step Details:
  [OK] Step 1: Implement code (5.1s)
  [OK] Step 2: Review code quality (2.0s)
  [OK] Step 3: Generate tests (1.9s)

✅ Build workflow completed successfully!
```

**Note**: Fast mode skips steps 1-4 (enhance, plan, architect, design) for faster execution.

---

## Custom Status Tracking

### Example: Custom Logging with StatusReporter

**Code**:
```python
import logging
from pathlib import Path
from tapps_agents.cli.utils.status_reporter import StatusReporter
from tapps_agents.simple_mode.orchestrators.build_orchestrator import BuildOrchestrator
from tapps_agents.simple_mode.intent_parser import Intent, IntentType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize reporter
reporter = StatusReporter(total_steps=7)

# Custom callbacks with logging
def on_step_start(step_num: int, step_name: str):
    reporter.start_step(step_num, step_name)
    logger.info(f"Starting step {step_num}: {step_name}")

def on_step_complete(step_num: int, step_name: str, status: str):
    reporter.complete_step(step_num, step_name, status)
    logger.info(f"Step {step_num} completed: {status}")

# Create orchestrator
orchestrator = BuildOrchestrator(project_root=Path.cwd())

# Create intent
intent = Intent(
    type=IntentType.BUILD,
    confidence=1.0,
    parameters={"description": "Add user authentication"},
    original_input="Add user authentication",
)

# Execute with custom callbacks
import asyncio
result = asyncio.run(
    orchestrator.execute(
        intent=intent,
        parameters=intent.parameters,
        fast_mode=False,
        on_step_start=on_step_start,
        on_step_complete=on_step_complete,
    )
)

# Print summary
reporter.print_summary()
```

**Output**:
```
INFO: Starting step 1: Enhance prompt (requirements analysis)
[1/7] Enhance prompt (requirements analysis)...
INFO: Step 1 completed: success
[1/7] Enhance prompt (requirements analysis)... [OK] (2.1s)
...
```

---

## Error Recovery Integration

### Example: Automatic Error Recovery

**Code**:
```python
from tapps_agents.cli.utils.error_recovery import ErrorRecoveryHandler
from tapps_agents.simple_mode.orchestrators.build_orchestrator import BuildOrchestrator

# Initialize recovery handler
handler = ErrorRecoveryHandler(interactive=False)

# Track retry attempts
retry_count = {}

def retry_step(step_num: int):
    """Retry a failed step."""
    retry_count[step_num] = retry_count.get(step_num, 0) + 1
    print(f"Retrying step {step_num} (attempt {retry_count[step_num]})")

def skip_step(step_num: int):
    """Skip a failed step."""
    print(f"Skipping step {step_num}")

# Error callback
def on_step_error(step_num: int, step_name: str, error: Exception):
    action = handler.handle_step_error(
        step_num=step_num,
        step_name=step_name,
        error=error,
        retry_callback=lambda: retry_step(step_num),
        skip_callback=lambda: skip_step(step_num),
    )
    
    if action == "fail":
        print(f"Step {step_num} failed and cannot be recovered")
        raise error

# Execute with error recovery
orchestrator = BuildOrchestrator(...)
result = await orchestrator.execute(
    ...,
    on_step_error=on_step_error,
)

# Check recovery summary
summary = handler.get_recovery_summary()
print(f"Total recoveries: {summary['total_recoveries']}")
print(f"Retries: {summary['retries']}")
print(f"Skips: {summary['skips']}")
```

**Example Output** (with timeout error):
```
[3/7] Design architecture...
Connection timeout occurred
Retrying step 3 (attempt 1)
[3/7] Design architecture... [OK] (3.2s)

...

Total recoveries: 1
Retries: 1
Skips: 0
```

---

## Workflow Preview

### Example: Preview Before Execution

**Command**:
```bash
tapps-agents simple-mode build --prompt "Add payment processing" --file src/api/payments.py
```

**Preview Output**:
```
============================================================
Workflow Preview
============================================================
Feature: Add payment processing
Mode: Complete (7 steps)

Steps to Execute:
  1. Enhance prompt (requirements analysis)     ~2s
  2. Create user stories                        ~2s
  3. Design architecture                         ~3s
  4. Design API/data models                      ~3s
  5. Implement code                             ~5s
  6. Review code quality                         ~2s
  7. Generate tests                              ~2s

Estimated Total Time: ~19s
Configuration: automation.level=2, fast_mode=false

============================================================
```

**Note**: Preview only shows in interactive mode (without `--auto` flag).

---

## Advanced: Custom Callbacks

### Example: Metrics Collection

**Code**:
```python
import time
from typing import Dict, List
from tapps_agents.cli.utils.status_reporter import StatusReporter

class MetricsCollector:
    """Collect workflow metrics."""
    
    def __init__(self):
        self.step_metrics: List[Dict] = []
        self.start_time = time.time()
    
    def on_step_start(self, step_num: int, step_name: str):
        """Record step start."""
        self.step_metrics.append({
            "step_num": step_num,
            "step_name": step_name,
            "start_time": time.time(),
        })
    
    def on_step_complete(self, step_num: int, step_name: str, status: str):
        """Record step completion."""
        for metric in self.step_metrics:
            if metric["step_num"] == step_num:
                metric["end_time"] = time.time()
                metric["duration"] = metric["end_time"] - metric["start_time"]
                metric["status"] = status
                break
    
    def get_summary(self) -> Dict:
        """Get metrics summary."""
        total_time = time.time() - self.start_time
        successful = sum(1 for m in self.step_metrics if m.get("status") == "success")
        
        return {
            "total_steps": len(self.step_metrics),
            "successful_steps": successful,
            "total_time": total_time,
            "step_details": self.step_metrics,
        }

# Use metrics collector
metrics = MetricsCollector()
reporter = StatusReporter(total_steps=7)

def on_step_start(step_num: int, step_name: str):
    metrics.on_step_start(step_num, step_name)
    reporter.start_step(step_num, step_name)

def on_step_complete(step_num: int, step_name: str, status: str):
    metrics.on_step_complete(step_num, step_name, status)
    reporter.complete_step(step_num, step_name, status)

# Execute
orchestrator.execute(
    ...,
    on_step_start=on_step_start,
    on_step_complete=on_step_complete,
)

# Print metrics
summary = metrics.get_summary()
print(f"Total steps: {summary['total_steps']}")
print(f"Successful: {summary['successful_steps']}")
print(f"Total time: {summary['total_time']:.1f}s")
```

---

## Real-World Scenarios

### Scenario 1: Building a REST API

**Command**:
```bash
tapps-agents simple-mode build --prompt "Create REST API for product catalog with CRUD operations" --file src/api/products.py
```

**Use Case**: Building a new API endpoint from scratch.

**Expected Output**: 
- Enhanced requirements with API best practices
- User stories for CRUD operations
- RESTful architecture design
- API specification
- Implementation with FastAPI/Flask
- Code review with security checks
- Test generation

---

### Scenario 2: Adding Authentication

**Command**:
```bash
tapps-agents simple-mode build --prompt "Add JWT authentication with refresh tokens" --fast
```

**Use Case**: Quick addition of authentication to existing project.

**Expected Output** (Fast Mode):
- Implementation of JWT auth service
- Code review
- Test generation

**Note**: Fast mode skips documentation steps for faster execution.

---

### Scenario 3: Error Recovery in Action

**Scenario**: Network timeout during architecture design step.

**Automatic Recovery**:
```
[3/7] Design architecture...
TimeoutError: Connection timeout

[Retrying step 3...]
[3/7] Design architecture... [OK] (3.2s)
```

**Recovery Summary**:
```
Total recoveries: 1
Retries: 1
Skips: 0
```

---

## Best Practices Examples

### Example 1: Always Use StatusReporter

```python
# ✅ Good: Use StatusReporter
reporter = StatusReporter(total_steps=7)
orchestrator.execute(..., on_step_start=reporter.start_step, ...)

# ❌ Bad: No status tracking
orchestrator.execute(...)
```

### Example 2: Handle Errors Gracefully

```python
# ✅ Good: Error recovery integrated
handler = ErrorRecoveryHandler()
orchestrator.execute(..., on_step_error=handler.handle_step_error)

# ❌ Bad: Errors cause immediate failure
orchestrator.execute(...)  # No error handling
```

### Example 3: Use Fast Mode Appropriately

```python
# ✅ Good: Fast mode for quick iterations
orchestrator.execute(..., fast_mode=True)  # When documentation not needed

# ✅ Good: Complete mode for new features
orchestrator.execute(..., fast_mode=False)  # When documentation needed

# ❌ Bad: Always using fast mode
orchestrator.execute(..., fast_mode=True)  # Missing valuable documentation
```

---

## Related Documentation

- [Simple Mode Guide](SIMPLE_MODE_GUIDE.md)
- [Phase 2 Features](SIMPLE_MODE_PHASE2_FEATURES.md)
- [Troubleshooting Guide](SIMPLE_MODE_TROUBLESHOOTING.md)
