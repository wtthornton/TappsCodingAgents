# Connection Error Recommendations - Request ID: c060f8cb-7f9b-4831-bbd4-e36d3387c3ac

**Date:** January 2026  
**Request ID:** c060f8cb-7f9b-4831-bbd4-e36d3387c3ac  
**Status:** Active Issue  
**Priority:** High

---

## Issue Summary

Connection error occurred during workflow execution:
- **Command:** `python -m tapps_agents.cli create "Create a simple hello.py file that prints 'Hello, World!'" --workflow rapid`
- **Workflow State:** Status: unknown, Current Step: requirements
- **Error:** Connection failed (Request ID: c060f8cb-7f9b-4831-bbd4-e36d3387c3ac)
- **Root Cause:** Network request failed during agent activation in requirements step

---

## Immediate Actions (Do These First)

### 1. Check Current Workflow State

```bash
# List all workflow states
python -m tapps_agents.cli workflow state list --format text

# Show details of the most recent workflow
python -m tapps_agents.cli workflow state show --format text
```

**Expected Output:**
- Workflow ID
- Current step (should be "requirements")
- Completed steps
- Artifacts created so far

### 2. Verify Network Connectivity

```bash
# Test basic connectivity
ping 8.8.8.8

# Test Context7 API (if using)
curl -I https://api.context7.com/health

# Check if VPN is required
# (Some organizations require VPN for API access)
```

**Common Issues:**
- VPN not connected
- Firewall blocking outbound connections
- Proxy settings not configured
- DNS resolution failures

### 3. Enable Offline Mode (If Network Unavailable)

If network is unavailable or unreliable:

```bash
# Set offline mode environment variable
export TAPPS_AGENTS_OFFLINE=1

# Or on Windows PowerShell:
$env:TAPPS_AGENTS_OFFLINE=1

# Then retry the command
python -m tapps_agents.cli create "Create a simple hello.py file that prints 'Hello, World!'" --workflow rapid
```

**What Offline Mode Does:**
- Skips network API calls
- Uses local fallbacks
- Prevents connection errors
- Note: Some features may be limited without network

### 4. Resume Workflow (If State Was Saved)

If the workflow state was persisted before the error:

```bash
# Resume the most recent workflow
python -m tapps_agents.cli workflow resume

# Or resume a specific workflow by ID
python -m tapps_agents.cli workflow resume --workflow-id <workflow-id>

# Validate state before resuming
python -m tapps_agents.cli workflow resume --validate
```

**What Resume Does:**
- Loads saved workflow state
- Continues from the last completed step
- Skips already-completed steps
- Preserves artifacts created so far

---

## Short-Term Solutions

### Option A: Retry with Network Connection

1. **Ensure Network is Available:**
   ```bash
   # Check network
   ping google.com
   ```

2. **Retry the Command:**
   ```bash
   python -m tapps_agents.cli create "Create a simple hello.py file that prints 'Hello, World!'" --workflow rapid
   ```

3. **Monitor for Connection Errors:**
   - If error persists, proceed to Option B or C

### Option B: Use Offline Mode

1. **Enable Offline Mode:**
   ```bash
   export TAPPS_AGENTS_OFFLINE=1  # Linux/Mac
   $env:TAPPS_AGENTS_OFFLINE=1     # Windows PowerShell
   ```

2. **Run Command:**
   ```bash
   python -m tapps_agents.cli create "Create a simple hello.py file that prints 'Hello, World!'" --workflow rapid
   ```

3. **Note Limitations:**
   - Some LLM-driven steps may not execute
   - Context7 API calls will be skipped
   - Background agent API calls will use local fallbacks

### Option C: Resume from Checkpoint

1. **Check if State Was Saved:**
   ```bash
   python -m tapps_agents.cli workflow state list
   ```

2. **Resume Workflow:**
   ```bash
   python -m tapps_agents.cli workflow resume
   ```

3. **Verify Progress:**
   ```bash
   python -m tapps_agents.cli workflow state show
   ```

---

## Long-Term Prevention Strategies

### 1. Configure Offline Mode Detection

The system automatically enables offline mode after 2 connection failures. To configure:

```python
# In your project config (.tapps-agents/config.yaml)
offline_mode:
  auto_enable: true
  failure_threshold: 2  # Enable after 2 failures
  retry_attempts: 3     # Retry before going offline
```

### 2. Use Network Health Checks

Before running workflows, check network:

```bash
# Create a network check script
python -c "
import requests
try:
    response = requests.get('https://api.context7.com/health', timeout=5)
    print('Network OK')
except:
    print('Network unavailable - use offline mode')
"
```

### 3. Configure Proxy/VPN Settings

If your organization requires VPN or proxy:

```bash
# Set proxy environment variables
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080

# Or configure in config.yaml
network:
  proxy:
    http: http://proxy.example.com:8080
    https: http://proxy.example.com:8080
```

### 4. Use Workflow Checkpoints

Enable automatic checkpointing:

```yaml
# .tapps-agents/config.yaml
workflow:
  checkpoint:
    enabled: true
    interval: 1  # Checkpoint after each step
    on_error: true  # Checkpoint on errors
```

This ensures workflows can always be resumed after failures.

---

## Troubleshooting Steps

### Step 1: Diagnose Network Issue

```bash
# Test DNS resolution
nslookup api.context7.com

# Test HTTP connectivity
curl -v https://api.context7.com/health

# Check firewall rules
# (OS-specific commands)
```

### Step 2: Check TappsCodingAgents Configuration

```bash
# Verify configuration
python -m tapps_agents.cli doctor

# Check for configuration errors
cat .tapps-agents/config.yaml
```

### Step 3: Review Error Logs

```bash
# Check for detailed error messages
python -m tapps_agents.cli create "test" --workflow rapid --verbose

# Look for connection error details in output
```

### Step 4: Test Individual Components

```bash
# Test Context7 API (if configured)
python -c "
from tapps_agents.context7.client import Context7Client
client = Context7Client()
try:
    result = client.get_library_docs('python')
    print('Context7 OK')
except Exception as e:
    print(f'Context7 Error: {e}')
"

# Test agent activation
python -m tapps_agents.cli analyst --help
```

---

## Error Recovery Workflow

### Automatic Recovery

The system includes automatic error recovery:

1. **Connection Failure Detection:**
   - First failure: Recorded, retry attempted
   - Second failure: Offline mode enabled automatically

2. **Workflow State Persistence:**
   - State saved after each step
   - Can resume from any checkpoint

3. **Error Envelope System:**
   - Structured error information
   - Recovery suggestions provided
   - Correlation IDs for tracking

### Manual Recovery

If automatic recovery doesn't work:

1. **Check Workflow State:**
   ```bash
   python -m tapps_agents.cli workflow state list
   ```

2. **Resume or Restart:**
   ```bash
   # Try resume first
   python -m tapps_agents.cli workflow resume
   
   # If resume fails, restart from beginning
   python -m tapps_agents.cli create "..." --workflow rapid
   ```

3. **Clean Up Failed State (if needed):**
   ```bash
   python -m tapps_agents.cli workflow state cleanup --remove-completed
   ```

---

## Best Practices

### 1. Always Enable Checkpointing

```yaml
# .tapps-agents/config.yaml
workflow:
  checkpoint:
    enabled: true
    on_error: true
```

### 2. Monitor Network Before Long Workflows

```bash
# Quick network check
ping -c 3 8.8.8.8 && echo "Network OK" || echo "Network issue - use offline mode"
```

### 3. Use Offline Mode for Development

When developing locally without network:

```bash
export TAPPS_AGENTS_OFFLINE=1
python -m tapps_agents.cli create "..." --workflow rapid
```

### 4. Keep Workflow States for Recovery

Don't clean up workflow states immediately:

```bash
# Keep states for at least 7 days
python -m tapps_agents.cli workflow state cleanup --retention-days 7
```

### 5. Use Verbose Mode for Debugging

```bash
# Get detailed error information
python -m tapps_agents.cli create "..." --workflow rapid --verbose
```

---

## Related Documentation

- **Connection Error Issue:** `docs/implementation/TAPPS_AGENTS_CONNECTION_ERROR_ISSUE.md`
- **Offline Mode Solution:** `docs/implementation/OFFLINE_MODE_SOLUTION.md`
- **Workflow Resume Guide:** `docs/CHECKPOINT_RESUME_GUIDE.md`
- **Troubleshooting Guide:** `docs/TROUBLESHOOTING.md`
- **Runbooks:** `docs/RUNBOOKS.md`

---

## Quick Reference Commands

```bash
# Check workflow state
python -m tapps_agents.cli workflow state list

# Resume workflow
python -m tapps_agents.cli workflow resume

# Enable offline mode
export TAPPS_AGENTS_OFFLINE=1

# Check system health
python -m tapps_agents.cli doctor

# Clean up old states
python -m tapps_agents.cli workflow state cleanup
```

---

## Next Steps

1. ✅ **Immediate:** Check workflow state and network connectivity
2. ✅ **Short-term:** Resume workflow or retry with offline mode
3. ✅ **Long-term:** Configure checkpointing and offline mode detection
4. ✅ **Prevention:** Set up network health checks and proxy configuration

---

**Last Updated:** January 2026  
**Status:** Active - Recommendations provided

