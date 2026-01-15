# Playwright MCP Integration

## Overview

This document describes the Playwright MCP integration implemented in tapps-agents. The integration follows the same pattern as Context7 MCP integration, providing detection, setup instructions, agent awareness, and comprehensive documentation.

## Implementation Summary

### 1. Enhanced MCP Detection (`tapps_agents/core/init_project.py`)

**Added Playwright MCP setup instructions** to the `detect_mcp_servers()` function:

- **Location**: Lines 1379-1397
- **Functionality**: Generates setup instructions for Playwright MCP when not detected
- **Pattern**: Follows the same pattern as Context7 MCP setup instructions
- **Content**: Includes configuration example for `.cursor/mcp.json` and notes that it's optional

**Key Features**:
- Detects Playwright MCP in MCP configuration files
- Provides setup instructions when missing
- Notes that Playwright MCP is optional (Cursor may provide it natively)
- Suggests Python Playwright package as alternative

### 2. Doctor Command Enhancement (`tapps_agents/core/doctor.py`)

**Added Playwright MCP status checking** to the doctor command:

- **Location**: Lines 275-340
- **Functionality**: Reports Playwright MCP configuration status
- **Output**:
  - ✅ "Playwright MCP: Configured" (if detected)
  - ✅ "Playwright MCP: Not configured (optional), but Python Playwright package is available" (if Python package installed)
  - ⚠️ "Playwright MCP: Not configured (optional)" (if neither configured)

**Key Features**:
- Checks for Playwright MCP in MCP configuration
- Falls back to checking Python Playwright package availability
- Provides remediation instructions
- Distinguishes between Playwright MCP and Python Playwright package

### 3. Tester Agent Updates (`tapps_agents/agents/tester/test_generator.py`)

**Added Playwright MCP awareness** to E2E test generation:

- **Location**: Lines 530-545
- **Functionality**: Checks for Playwright MCP availability when generating E2E tests
- **Behavior**: Adds note to test generation prompt when Playwright MCP is available

**Key Features**:
- Detects Playwright MCP when generating Playwright-based E2E tests
- Informs test generation that Playwright MCP tools are available
- Works for both "playwright" and "pytest-playwright" frameworks

### 4. Documentation Updates

#### A. Troubleshooting Guide (`docs/TROUBLESHOOTING.md`)

**Enhanced Playwright section** (Lines 107-137):

- Explains difference between Playwright MCP and Python Playwright package
- Provides instructions for checking Playwright MCP status
- Includes configuration example for `.cursor/mcp.json`
- Clarifies when each option should be used

#### B. Quick Reference (`tapps_agents/resources/cursor/rules/quick-reference.mdc`)

**Enhanced Playwright Warning section** (Lines 316-340):

- Expanded explanation of Playwright options
- Added configuration instructions
- Included status check command (`tapps-agents doctor`)
- Clearer distinction between MCP and Python package

## Usage

### Checking Playwright MCP Status

```bash
# Check environment including MCP servers
python -m tapps_agents.cli doctor
```

The doctor command will show:
- Playwright MCP configuration status
- Python Playwright package availability
- Setup instructions if needed

### Configuring Playwright MCP

Add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "Playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp-server"]
    }
  }
}
```

### Using Playwright MCP in E2E Tests

When generating E2E tests with the tester agent, if Playwright MCP is configured:

1. The agent will detect Playwright MCP availability
2. Test generation prompts will include a note about Playwright MCP availability
3. Tests can leverage Playwright MCP tools via Cursor

## Design Principles

1. **Consistency**: Follows the same pattern as Context7 MCP integration
2. **Optional by Default**: Always notes that Playwright MCP is optional
3. **Clear Messaging**: Distinguishes between Python Playwright package and Playwright MCP server
4. **User Guidance**: Provides actionable setup instructions when missing
5. **Agent Awareness**: Makes agents aware of available tools without requiring them to use them

## Files Modified

1. `tapps_agents/core/init_project.py` - Added Playwright MCP setup instructions
2. `tapps_agents/core/doctor.py` - Added Playwright MCP status checking
3. `tapps_agents/agents/tester/test_generator.py` - Added Playwright MCP awareness
4. `docs/TROUBLESHOOTING.md` - Enhanced Playwright documentation
5. `tapps_agents/resources/cursor/rules/quick-reference.mdc` - Enhanced Playwright warning section

## Testing

To verify the implementation:

1. **Test MCP Detection**:
   ```bash
   python -m tapps_agents.cli doctor
   ```
   Should show Playwright MCP status

2. **Test Setup Instructions**:
   - Run `tapps-agents init` and check MCP detection output
   - Verify setup instructions are generated when Playwright MCP is missing

3. **Test Tester Agent**:
   - Generate E2E tests for a project with Playwright
   - Verify that Playwright MCP awareness is included in prompts

## New Capabilities (2026)

### Accessibility Testing
- **WCAG 2.2 Compliance**: Automatic accessibility auditing using `browser_snapshot`
- **Accessibility Auditor**: `tapps_agents/agents/tester/accessibility_auditor.py`
- **Test Generation**: E2E tests automatically include accessibility assertions
- **Compliance Levels**: Reports A, AA, AAA compliance status

### Performance Monitoring
- **Core Web Vitals**: Automatic collection of LCP, FID, CLS, FCP metrics
- **Performance Monitor**: `tapps_agents/agents/tester/performance_monitor.py`
- **Network Analysis**: Automatic network request analysis
- **Test Assertions**: Performance thresholds automatically enforced in tests

### Direct MCP Tool Integration
- **PlaywrightMCPController**: `tapps_agents/core/playwright_mcp_controller.py`
- **Unified Interface**: Works in both Cursor IDE (MCP tools) and CLI (Python Playwright fallback)
- **Full Tool Support**: All MCP Playwright tools available (navigation, interaction, monitoring, debugging)

## Usage Examples

### Accessibility Testing in E2E Tests

When generating E2E tests with Playwright, accessibility checks are automatically included:

```python
# Generated test includes:
def test_login_accessibility(page):
    page.goto("/login")
    snapshot = page.snapshot()  # Get accessibility tree
    assert accessibility_score(snapshot) >= 90
    assert has_alt_text_for_images(snapshot)
    assert keyboard_navigable(snapshot)
```

### Performance Monitoring in E2E Tests

Performance metrics are automatically collected:

```python
# Generated test includes:
def test_dashboard_performance(page):
    page.goto("/dashboard")
    metrics = page.metrics()
    assert metrics["LCP"] < 2.5  # Largest Contentful Paint
    assert metrics["FID"] < 100   # First Input Delay
    assert metrics["CLS"] < 0.1   # Cumulative Layout Shift
```

### Using PlaywrightMCPController Directly

```python
from tapps_agents.core.playwright_mcp_controller import PlaywrightMCPController

# Initialize controller (automatically detects MCP or falls back to Python Playwright)
controller = PlaywrightMCPController(mcp_tool_handler=your_mcp_handler)

# Navigate
controller.navigate("https://example.com")

# Get accessibility snapshot
snapshot = controller.snapshot()

# Take screenshot
controller.take_screenshot("screenshot.png", full_page=True)

# Get network requests
requests = controller.get_network_requests()

# Get console messages
messages = controller.get_console_messages(level="error")
```

## Future Enhancements

Potential future improvements:

1. **Network Mocking**: Record and replay API interactions
2. **Trace Viewer Integration**: Automatic trace files for test failures
3. **Multi-Tab Testing**: Support for multi-tab scenarios
4. **Visual Regression Testing**: Screenshot comparison
5. **AI-Powered Test Generation**: Self-healing tests, natural language to test code
6. **Mobile Device Testing**: Device emulation and mobile-specific tests

## Related Documentation

- [Troubleshooting Guide](TROUBLESHOOTING.md) - Playwright MCP troubleshooting
- [Quick Reference](.cursor/rules/quick-reference.mdc) - Playwright warning section
- [Command Reference](.cursor/rules/command-reference.mdc) - MCP server commands

