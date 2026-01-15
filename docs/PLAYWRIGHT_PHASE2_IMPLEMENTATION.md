# Playwright Phase 2 Implementation: Network Mocking & Trace Viewer

## Overview

Phase 2 implementation adds network mocking/replay capabilities and trace viewer integration to TappsCodingAgents' Playwright integration.

**Implementation Date**: 2025-01-16  
**Status**: ✅ Phase 2 Complete

---

## What Was Implemented

### 1. Network Recorder (`tapps_agents/agents/tester/network_recorder.py`)

**Purpose**: Record and replay network requests for offline testing and faster test execution.

**Key Features**:
- ✅ Record network requests during test runs
- ✅ Save recordings to JSON files
- ✅ Load and replay recorded requests
- ✅ Generate Playwright route configuration for replay
- ✅ List and manage recordings

**Usage**:
```python
from tapps_agents.agents.tester.network_recorder import NetworkRecorder

recorder = NetworkRecorder()
session_id = recorder.start_recording(description="Login flow")
# ... run test ...
recording = recorder.stop_recording()

# Replay
replay_config = recorder.create_replay_config(recording)
```

### 2. Trace Manager (`tapps_agents/agents/tester/trace_manager.py`)

**Purpose**: Generate and manage trace files for debugging test failures.

**Key Features**:
- ✅ Automatic trace file generation
- ✅ Trace viewer link generation
- ✅ Trace report creation for test failures
- ✅ Automatic cleanup of old traces
- ✅ List and manage trace files

**Usage**:
```python
from tapps_agents.agents.tester.trace_manager import TraceManager

trace_manager = TraceManager()
trace_path = trace_manager.start_tracing(context, test_name="test_login")
# ... run test ...
trace_path = trace_manager.stop_tracing(context)

# Generate trace viewer link
link = trace_manager.generate_trace_viewer_link(trace_path)
```

### 3. Enhanced PlaywrightMCPController

**Updates to `tapps_agents/core/playwright_mcp_controller.py`**:
- ✅ Added network recording support
- ✅ Added trace generation support
- ✅ Automatic request recording when enabled
- ✅ Methods: `start_network_recording()`, `stop_network_recording()`, `start_tracing()`, `stop_tracing()`

**Usage**:
```python
from tapps_agents.core.playwright_mcp_controller import PlaywrightMCPController

controller = PlaywrightMCPController(
    enable_network_recording=True,
    enable_tracing=True
)

# Start recording
controller.start_network_recording("test_session")
controller.start_tracing("test_login")

# Run test...
controller.navigate("https://example.com")
requests = controller.get_network_requests()  # Automatically recorded

# Stop and save
recording = controller.stop_network_recording()
trace_path = controller.stop_tracing()
```

### 4. Enhanced Test Generator

**Updates to `tapps_agents/agents/tester/test_generator.py`**:
- ✅ Added network mocking requirements to test generation
- ✅ Added trace generation requirements to test generation
- ✅ Enhanced error reporting with trace viewer links

**Generated Tests Now Include**:
- Network mocking with `page.route()`
- Trace generation with `context.tracing.start()`
- Error reporting with trace viewer commands

---

## Example Generated Test

```python
import pytest
from playwright.sync_api import Page, BrowserContext

def test_login_with_network_mocking(page: Page, context: BrowserContext):
    """Test login flow with network mocking and trace generation."""
    
    # Start tracing
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    trace_path = ".tapps-agents/traces/test_login.zip"
    
    try:
        # Mock API requests
        page.route("**/api/login", lambda route: route.fulfill(
            status=200,
            body='{"token": "mock_token", "user": {"id": 1, "name": "Test User"}}'
        ))
        
        page.route("**/api/user/profile", lambda route: route.fulfill(
            status=200,
            body='{"id": 1, "name": "Test User", "email": "test@example.com"}'
        ))
        
        # Navigate and test
        page.goto("/login")
        
        # Accessibility check
        snapshot = page.snapshot()
        assert accessibility_score(snapshot) >= 90
        
        # Fill form
        page.fill("#username", "testuser")
        page.fill("#password", "testpass")
        page.click("button[type='submit']")
        
        # Verify navigation
        page.wait_for_url("**/dashboard")
        assert page.url.endswith("/dashboard")
        
        # Performance check
        metrics = page.metrics()
        assert metrics["LCP"] < 2.5
        
    except Exception as e:
        # Save trace on failure
        context.tracing.stop(path=trace_path)
        trace_command = f"npx playwright show-trace {trace_path}"
        raise AssertionError(
            f"Test failed: {e}\n"
            f"View trace: {trace_command}"
        ) from e
    finally:
        # Always stop tracing
        if context.tracing:
            context.tracing.stop(path=trace_path)
```

---

## Benefits

### Network Mocking
- ✅ **Offline Testing**: Tests don't depend on live APIs
- ✅ **Faster Execution**: No network latency
- ✅ **Reliable Tests**: Consistent responses
- ✅ **Edge Case Testing**: Test error scenarios, slow networks, etc.

### Trace Viewer
- ✅ **Better Debugging**: Step-by-step test execution analysis
- ✅ **Visual Debugging**: See exactly what happened
- ✅ **Faster Issue Resolution**: Identify problems quickly
- ✅ **Better Failure Reports**: Trace viewer links in error messages

---

## Files Created

1. `tapps_agents/agents/tester/network_recorder.py` - Network recording and replay (300+ lines)
2. `tapps_agents/agents/tester/trace_manager.py` - Trace file management (200+ lines)

## Files Modified

1. `tapps_agents/core/playwright_mcp_controller.py` - Added network recording and tracing support
2. `tapps_agents/agents/tester/test_generator.py` - Enhanced test generation with mocking and tracing

---

## Usage Examples

### Recording Network Requests

```python
from tapps_agents.core.playwright_mcp_controller import PlaywrightMCPController

controller = PlaywrightMCPController(enable_network_recording=True)
controller.start_network_recording("login_flow")

controller.navigate("https://app.example.com/login")
controller.fill_form([...])
controller.click("button[type='submit']")

# Get recorded requests
requests = controller.get_network_requests()

# Stop and save
recording = controller.stop_network_recording()
```

### Replaying Recorded Requests

```python
from tapps_agents.agents.tester.network_recorder import NetworkRecorder

recorder = NetworkRecorder()
recording = recorder.load_recording("login_flow")

# Generate replay config
replay_code = recorder.create_replay_config(recording)

# Use in test
# replay_code contains page.route() calls to mock requests
```

### Generating Trace Files

```python
from tapps_agents.core.playwright_mcp_controller import PlaywrightMCPController

controller = PlaywrightMCPController(enable_tracing=True)
trace_path = controller.start_tracing("test_login")

try:
    controller.navigate("https://example.com")
    # ... test code ...
except Exception as e:
    trace_path = controller.stop_tracing()
    trace_link = f"npx playwright show-trace {trace_path}"
    print(f"Test failed. View trace: {trace_link}")
    raise
```

---

## Configuration

### Enable Network Recording

```python
controller = PlaywrightMCPController(enable_network_recording=True)
```

### Enable Tracing

```python
controller = PlaywrightMCPController(enable_tracing=True)
```

### Both Enabled

```python
controller = PlaywrightMCPController(
    enable_network_recording=True,
    enable_tracing=True
)
```

---

## Trace Viewer Usage

After a test failure, trace files are saved to `.tapps-agents/traces/`.

View trace:
```bash
npx playwright show-trace .tapps-agents/traces/test_login_20250116_143022.zip
```

Or use the trace viewer link from the error message.

---

## Network Recording Storage

Recordings are saved to `.tapps-agents/recordings/` as JSON files.

List recordings:
```python
from tapps_agents.agents.tester.network_recorder import NetworkRecorder

recorder = NetworkRecorder()
recordings = recorder.list_recordings()
for rec in recordings:
    print(f"{rec['session_id']}: {rec['request_count']} requests")
```

---

## Integration with Test Generation

When generating E2E tests, the test generator automatically includes:
- Network mocking setup
- Trace generation setup
- Error handling with trace viewer links

All generated tests are ready to use these features out of the box.

---

## Next Steps

Phase 2 is complete. Future enhancements could include:
- Visual regression testing (Phase 3)
- Multi-tab testing support (Phase 3)
- AI-powered test generation (Phase 4)
- Self-healing tests (Phase 4)

---

**Document Version**: 1.0  
**Date**: 2025-01-16  
**Status**: Phase 2 Complete
