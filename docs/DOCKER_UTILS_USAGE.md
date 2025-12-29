# Docker Utilities Usage Guide

This guide explains how to use the Docker utility functions to safely check container status, avoiding PowerShell table format parsing issues.

## Problem

The command `docker ps --format "table {{.Names}}\t{{.Status}}" | Select-Object -First 35` causes agent crashes because:
- Table format creates a header row that breaks `Select-Object` parsing
- Tab characters aren't properly handled in PowerShell piping
- Table format output doesn't work well with PowerShell cmdlets

## Solution

Use the safe Docker utility functions from `tapps_agents.core.docker_utils` instead.

## Quick Start

```python
from tapps_agents.core.docker_utils import run_docker_ps_json, get_container_status

# Get all containers (most reliable method)
containers = run_docker_ps_json(limit=35)
for container in containers:
    print(f"{container['Names']}: {container['Status']}")

# Check specific container
status = get_container_status("my-container")
if status["found"]:
    print(f"Container is running: {status['running']}")
```

## Available Functions

### `run_docker_ps_json(limit=None)`

**Most reliable method** - Uses JSON format that works perfectly on Windows/PowerShell.

```python
from tapps_agents.core.docker_utils import run_docker_ps_json

# Get all containers
containers = run_docker_ps_json()

# Get first 35 containers
containers = run_docker_ps_json(limit=35)

# Access container data
for container in containers:
    name = container.get("Names", "").lstrip("/")
    status = container.get("Status", "")
    state = container.get("State", "")
    print(f"{name}: {status} ({state})")
```

**Returns**: List of dictionaries with container information:
- `Names`: Container name (may have leading `/`)
- `Status`: Status string (e.g., "Up 2 hours")
- `State`: State (e.g., "running", "exited")
- `ID`: Container ID
- `Image`: Image name
- And other Docker fields

**PowerShell Alternative**:
```powershell
docker ps --format json | ConvertFrom-Json | Select-Object -First 35 | Format-Table Name, Status
```

### `run_docker_ps_simple(limit=None)`

Uses simple format without table header (works better than table format).

```python
from tapps_agents.core.docker_utils import run_docker_ps_simple

containers = run_docker_ps_simple(limit=35)
for container in containers:
    print(f"{container['Names']}: {container['Status']}")
```

**Returns**: List of dictionaries with `Names` and `Status` keys only.

**PowerShell Alternative**:
```powershell
docker ps --format "{{.Names}}\t{{.Status}}" | Select-Object -First 35
```

### `run_docker_ps_native(limit=None)`

Returns raw Docker output (useful for display, harder to parse).

```python
from tapps_agents.core.docker_utils import run_docker_ps_native

output = run_docker_ps_native(limit=35)
print(output)  # Raw Docker table output
```

**Returns**: Raw string output from `docker ps` command.

**PowerShell Alternative**:
```powershell
docker ps | Select-Object -First 35
```

### `get_container_status(container_name=None)`

Check status of a specific container or get all containers.

```python
from tapps_agents.core.docker_utils import get_container_status

# Get all containers
result = get_container_status()
print(f"Total containers: {result['total']}")
for container in result["containers"]:
    print(f"  {container['Names']}: {container['Status']}")

# Check specific container
status = get_container_status("my-container")
if status["found"]:
    print(f"Container found: {status['running']}")
    print(f"Status: {status['container']['Status']}")
else:
    print("Container not found")
```

**Returns**:
- If `container_name` is `None`: `{"total": int, "containers": [...]}`
- If `container_name` is provided: `{"found": bool, "running": bool, "container": {...} | None}`

## Error Handling

All functions handle errors gracefully:

```python
from tapps_agents.core.docker_utils import run_docker_ps_json

containers = run_docker_ps_json()
# Returns empty list [] if:
# - Docker is not installed
# - Docker daemon is not running
# - Command times out
# - Any other error occurs

if not containers:
    print("No containers found or Docker not available")
```

## Examples

### Example 1: List Running Containers

```python
from tapps_agents.core.docker_utils import run_docker_ps_json

containers = run_docker_ps_json()
running = [c for c in containers if c.get("State") == "running"]

print(f"Running containers: {len(running)}")
for container in running:
    name = container.get("Names", "").lstrip("/")
    print(f"  - {name}")
```

### Example 2: Monitor Container Health

```python
from tapps_agents.core.docker_utils import get_container_status
import time

def monitor_container(container_name: str, interval: int = 5):
    """Monitor container status every N seconds."""
    while True:
        status = get_container_status(container_name)
        if status["found"]:
            running = "RUNNING" if status["running"] else "STOPPED"
            print(f"[{time.strftime('%H:%M:%S')}] {container_name}: {running}")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] {container_name}: NOT FOUND")
        time.sleep(interval)
```

### Example 3: Check Multiple Containers

```python
from tapps_agents.core.docker_utils import get_container_status

required_containers = ["web", "api", "db"]
all_running = True

for container_name in required_containers:
    status = get_container_status(container_name)
    if not status["found"] or not status["running"]:
        print(f"❌ {container_name} is not running")
        all_running = False
    else:
        print(f"✅ {container_name} is running")

if all_running:
    print("All required containers are running")
```

## Migration Guide

### Before (Problematic)

```python
# ❌ DON'T USE - Causes crashes on Windows/PowerShell
import subprocess
result = subprocess.run(
    ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}"],
    capture_output=True,
    text=True
)
# Then trying to parse with Select-Object in PowerShell fails
```

### After (Recommended)

```python
# ✅ USE THIS - Works reliably on all platforms
from tapps_agents.core.docker_utils import run_docker_ps_json

containers = run_docker_ps_json(limit=35)
for container in containers:
    print(f"{container['Names']}: {container['Status']}")
```

## Integration with Agents

### Ops Agent Integration

If you're working with the Ops Agent and need to check container status:

```python
from tapps_agents.core.docker_utils import run_docker_ps_json, get_container_status

# In your Ops Agent handler
async def _handle_infrastructure_check(self, **kwargs):
    containers = run_docker_ps_json()
    
    return {
        "message": "Infrastructure check completed",
        "container_count": len(containers),
        "containers": containers,
    }
```

### Simple Mode docker-fix Workflow

If implementing a docker-fix workflow:

```python
from tapps_agents.core.docker_utils import get_container_status

# Check if container exists and is running
status = get_container_status(service_name)
if not status["found"]:
    return {"error": f"Container {service_name} not found"}
if not status["running"]:
    return {"error": f"Container {service_name} is not running"}
```

## Best Practices

1. **Always use `run_docker_ps_json()`** - It's the most reliable method
2. **Handle empty results** - Check if list is empty before processing
3. **Use `get_container_status()`** for specific container checks
4. **Strip leading slashes** - Container names may have leading `/`
5. **Check `State` field** - More reliable than parsing `Status` string

## Related Documentation

- See `docs/STABILIZATION_PLAN.md` for issue details
- See `tapps_agents/core/docker_utils.py` for full API documentation
- See `tests/unit/core/test_docker_utils.py` for usage examples

