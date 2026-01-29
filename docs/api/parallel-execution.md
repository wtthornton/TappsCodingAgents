# Parallel Execution API Documentation

**Module**: `tapps_agents.agents.reviewer.tools.parallel_executor`
**Version**: 3.5.21
**Status**: Stable
**Created**: 2026-01-29

---

## Overview

The Parallel Execution module provides asynchronous, concurrent execution of quality tools for the ReviewerAgent, achieving **2-3x performance improvement** through parallel tool execution with timeout protection and graceful error recovery.

### Key Features

- ✅ **Parallel Execution**: Run Ruff, mypy, bandit, pip-audit concurrently
- ✅ **Timeout Protection**: 30-second default timeout per tool (configurable)
- ✅ **Error Recovery**: Continue execution if individual tools fail
- ✅ **Graceful Degradation**: Automatic fallback to sequential execution
- ✅ **Thread Safety**: Immutable dataclasses prevent race conditions
- ✅ **Comprehensive Logging**: DEBUG, WARNING, ERROR level logging

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   ParallelToolExecutor                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Phase 1: Parallel Batch                                   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌──────────┐  │  │
│  │  │  Ruff  │  │  mypy  │  │ bandit │  │pip-audit │  │  │
│  │  └───┬────┘  └───┬────┘  └───┬────┘  └────┬─────┘  │  │
│  │      └───────────┴───────────┴────────────┘        │  │
│  │              asyncio.gather()                       │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Phase 2: Sequential Batch                                 │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  ┌────────┐                                          │  │
│  │  │ jscpd  │ (requires full project context)         │  │
│  │  └────────┘                                          │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Timeout Protection: asyncio.wait_for()                    │
│  Error Recovery: return_exceptions=True                    │
└─────────────────────────────────────────────────────────────┘
```

### Performance

- **Sequential Execution**: ~23 seconds (sum of all tools)
- **Parallel Execution**: ~12 seconds (max of parallel tools + jscpd)
- **Speedup**: ~1.9x faster (2-3x with optimization)

---

## Data Models

### ToolExecutionConfig

**Immutable configuration for parallel tool execution.**

```python
@dataclass(frozen=True)
class ToolExecutionConfig:
    enabled: bool = True
    timeout_seconds: int = 30
    max_concurrent_tools: int = 4
    fallback_to_sequential: bool = True
    tool_timeouts: Optional[Dict[str, int]] = None
```

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | `bool` | `True` | Master switch for parallel execution |
| `timeout_seconds` | `int` | `30` | Global timeout for all tools (seconds) |
| `max_concurrent_tools` | `int` | `4` | Maximum concurrent subprocesses |
| `fallback_to_sequential` | `bool` | `True` | Auto-fallback on async errors |
| `tool_timeouts` | `Optional[Dict[str, int]]` | `None` | Per-tool timeout overrides |

#### Methods

##### `get_tool_timeout(tool_name: str) -> int`

Get timeout for specific tool with fallback to global timeout.

**Parameters:**
- `tool_name` (str): Name of the tool (ruff, mypy, bandit, pip_audit, jscpd)

**Returns:**
- `int`: Timeout in seconds for the tool

**Example:**
```python
config = ToolExecutionConfig(
    timeout_seconds=30,
    tool_timeouts={"mypy": 45, "bandit": 15}
)

config.get_tool_timeout("mypy")    # Returns: 45 (per-tool override)
config.get_tool_timeout("ruff")    # Returns: 30 (global fallback)
config.get_tool_timeout("bandit")  # Returns: 15 (per-tool override)
```

##### `from_dict(config_dict: Dict[str, Any]) -> ToolExecutionConfig` (classmethod)

Create config from dictionary (loaded from YAML).

**Parameters:**
- `config_dict` (Dict[str, Any]): Configuration dictionary

**Returns:**
- `ToolExecutionConfig`: Configured instance

**Example:**
```python
config = ToolExecutionConfig.from_dict({
    "enabled": True,
    "timeout_seconds": 30,
    "max_concurrent_tools": 4,
    "tool_timeouts": {
        "mypy": 45,
        "jscpd": 60
    }
})
```

**YAML Configuration Example:**
```yaml
# .tapps-agents/config.yaml
reviewer:
  parallel_execution:
    enabled: true
    timeout_seconds: 30
    max_concurrent_tools: 4
    fallback_to_sequential: true
    tool_timeouts:
      mypy: 45
      jscpd: 60
      bandit: 15
```

#### Validation

Configuration is validated on creation (**`__post_init__`**):

- ✅ `timeout_seconds` must be positive (> 0)
- ✅ `max_concurrent_tools` must be positive (> 0)
- ✅ All `tool_timeouts` values must be positive (> 0)

**Raises:**
- `ValueError`: If validation fails

---

### ToolStatus

**Enum representing tool execution status.**

```python
class ToolStatus(str, Enum):
    SUCCESS = "success"
    TIMEOUT = "timeout"
    ERROR = "error"
```

#### Values

| Value | Description |
|-------|-------------|
| `SUCCESS` | Tool executed successfully |
| `TIMEOUT` | Tool exceeded timeout limit |
| `ERROR` | Tool failed with exception |

#### Usage

```python
# Status comparison
if result.status == ToolStatus.SUCCESS:
    print("Tool succeeded")
elif result.status == ToolStatus.TIMEOUT:
    print("Tool timed out")
elif result.status == ToolStatus.ERROR:
    print("Tool failed")

# String comparison (ToolStatus inherits from str)
assert result.status == "success"
assert result.status.value == "success"
```

---

### ToolResult

**Immutable result from single tool execution.**

```python
@dataclass(frozen=True)
class ToolResult:
    tool: str
    status: ToolStatus
    data: Optional[Any]
    duration: float
    error: Optional[str] = None
    exit_code: Optional[int] = None
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `tool` | `str` | Tool name (ruff, mypy, bandit, pip-audit, jscpd) |
| `status` | `ToolStatus` | Execution status (SUCCESS, TIMEOUT, ERROR) |
| `data` | `Optional[Any]` | Tool-specific result data (None if timeout/error) |
| `duration` | `float` | Execution time in seconds |
| `error` | `Optional[str]` | Error message if status != SUCCESS |
| `exit_code` | `Optional[int]` | Tool exit code (None if timeout) |

#### Methods

##### `is_success() -> bool`

Check if tool executed successfully.

**Returns:**
- `bool`: True if status == SUCCESS

**Example:**
```python
result = await executor.execute_with_timeout(run_ruff, Path("file.py"), "ruff")
if result.is_success():
    print(f"Ruff found {len(result.data['issues'])} issues")
```

##### `is_timeout() -> bool`

Check if tool timed out.

**Returns:**
- `bool`: True if status == TIMEOUT

##### `is_error() -> bool`

Check if tool failed with error.

**Returns:**
- `bool`: True if status == ERROR

##### `to_dict() -> Dict[str, Any]`

Convert to dictionary for serialization.

**Returns:**
- `Dict[str, Any]`: Dictionary representation

**Example:**
```python
result_dict = result.to_dict()
# {
#     "tool": "ruff",
#     "status": "success",
#     "data": {"issues": []},
#     "duration": 2.3,
#     "error": None,
#     "exit_code": None
# }
```

#### Examples

**Success Result:**
```python
ToolResult(
    tool="ruff",
    status=ToolStatus.SUCCESS,
    data={"issues": []},
    duration=2.3,
    error=None,
    exit_code=None
)
```

**Timeout Result:**
```python
ToolResult(
    tool="mypy",
    status=ToolStatus.TIMEOUT,
    data=None,
    duration=30.5,
    error="Timeout after 30.5s (limit: 30s)",
    exit_code=None
)
```

**Error Result:**
```python
ToolResult(
    tool="bandit",
    status=ToolStatus.ERROR,
    data=None,
    duration=1.2,
    error="subprocess returned exit code 2",
    exit_code=2
)
```

---

## ParallelToolExecutor

**Coordinates parallel execution of quality tools with timeout protection.**

```python
class ParallelToolExecutor:
    def __init__(self, config: ToolExecutionConfig)
    async def execute_parallel(
        self,
        file_path: Path,
        tool_runners: Optional[Dict[str, Callable]] = None
    ) -> List[ToolResult]
    async def execute_with_timeout(
        self,
        tool_func: Callable[[Path], Any],
        file_path: Path,
        tool_name: Optional[str] = None
    ) -> ToolResult
```

### Constructor

#### `__init__(config: ToolExecutionConfig)`

Initialize parallel tool executor.

**Parameters:**
- `config` (ToolExecutionConfig): Tool execution configuration

**Example:**
```python
config = ToolExecutionConfig(
    enabled=True,
    timeout_seconds=30,
    max_concurrent_tools=4
)
executor = ParallelToolExecutor(config)
```

---

### Methods

#### `execute_parallel(file_path: Path, tool_runners: Optional[Dict[str, Callable]] = None) -> List[ToolResult]` (async)

Execute all quality tools with parallel optimization.

**Parameters:**
- `file_path` (Path): Path to file to review
- `tool_runners` (Optional[Dict[str, Callable]]): Optional dict of tool functions for testing/customization

**Returns:**
- `List[ToolResult]`: List of ToolResult objects (successful, timeout, or error)

**Raises:**
- Never raises - always returns partial results on failures

**Behavior:**

1. **Phase 1 (Parallel)**: Execute Ruff, mypy, bandit, pip-audit concurrently using `asyncio.gather()`
2. **Phase 2 (Sequential)**: Execute jscpd (requires full project context)
3. **Error Recovery**: Continue execution if individual tools fail
4. **Fallback**: If parallel execution fails catastrophically, fall back to sequential execution
5. **Logging**: Log summary of successful/failed tools

**Performance:**
- Sequential: ~23s (sum of all tools)
- Parallel: ~12s (max of parallel tools + jscpd)
- Speedup: ~1.9x faster

**Example:**
```python
config = ToolExecutionConfig(enabled=True, timeout_seconds=30)
executor = ParallelToolExecutor(config)

# Execute with default tool runners (from ReviewerAgent)
results = await executor.execute_parallel(Path("src/example.py"))

# Filter results
successful = [r for r in results if r.is_success()]
failed = [r for r in results if not r.is_success()]

print(f"✅ {len(successful)}/{len(results)} tools successful")
print(f"❌ {len(failed)} tools failed")

# Access individual tool results
for result in results:
    if result.tool == "ruff" and result.is_success():
        print(f"Ruff: {len(result.data['issues'])} issues found")
```

**Custom Tool Runners (for testing):**
```python
# Define custom async tool functions
async def run_ruff_async(file_path: Path) -> Dict[str, Any]:
    # Custom Ruff implementation
    return {"issues": []}

async def run_mypy_async(file_path: Path) -> Dict[str, Any]:
    # Custom mypy implementation
    return {"errors": []}

# Use custom tool runners
tool_runners = {
    "ruff": run_ruff_async,
    "mypy": run_mypy_async,
}

results = await executor.execute_parallel(
    Path("src/example.py"),
    tool_runners=tool_runners
)
```

---

#### `execute_with_timeout(tool_func: Callable[[Path], Any], file_path: Path, tool_name: Optional[str] = None) -> ToolResult` (async)

Execute single tool with timeout protection.

**Parameters:**
- `tool_func` (Callable[[Path], Any]): Async tool function to execute
- `file_path` (Path): Path to file to analyze
- `tool_name` (Optional[str]): Tool name for logging (auto-detected from function name if None)

**Returns:**
- `ToolResult`: Result with status SUCCESS, TIMEOUT, or ERROR

**Timeout Handling:**
- Global timeout: `config.timeout_seconds`
- Per-tool timeout: `config.get_tool_timeout(tool_name)`
- Timeout exception → ToolResult with status=TIMEOUT

**Example:**
```python
# Execute with explicit tool name
result = await executor.execute_with_timeout(
    run_ruff_async,
    Path("src/example.py"),
    "ruff"
)

# Execute with auto-detected tool name (from function name)
async def run_mypy_async(file_path: Path):
    # Implementation
    pass

result = await executor.execute_with_timeout(
    run_mypy_async,
    Path("src/example.py")
)
# Tool name auto-detected as "mypy" (from "run_mypy_async")

# Check result
if result.is_success():
    print(f"{result.tool} completed in {result.duration:.2f}s")
elif result.is_timeout():
    print(f"{result.tool} timed out after {result.duration:.2f}s")
else:
    print(f"{result.tool} failed: {result.error}")
```

---

## Usage Examples

### Basic Usage

```python
import asyncio
from pathlib import Path
from tapps_agents.agents.reviewer.tools.parallel_executor import (
    ParallelToolExecutor,
    ToolExecutionConfig,
    ToolStatus,
)

async def main():
    # Create configuration
    config = ToolExecutionConfig(
        enabled=True,
        timeout_seconds=30,
        max_concurrent_tools=4,
        tool_timeouts={"mypy": 45}  # mypy gets extra time
    )

    # Create executor
    executor = ParallelToolExecutor(config)

    # Execute all tools
    results = await executor.execute_parallel(Path("src/example.py"))

    # Process results
    for result in results:
        if result.is_success():
            print(f"✅ {result.tool}: Success ({result.duration:.2f}s)")
        elif result.is_timeout():
            print(f"⏱️  {result.tool}: Timeout ({result.duration:.2f}s)")
        else:
            print(f"❌ {result.tool}: Error - {result.error}")

    # Calculate total time
    total_time = sum(r.duration for r in results)
    print(f"\nTotal execution time: {total_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
```

### Configuration from YAML

```python
import yaml
from pathlib import Path
from tapps_agents.agents.reviewer.tools.parallel_executor import (
    ParallelToolExecutor,
    ToolExecutionConfig,
)

# Load configuration from YAML
config_path = Path(".tapps-agents/config.yaml")
with open(config_path) as f:
    config_data = yaml.safe_load(f)

# Extract parallel execution config
parallel_config = config_data["reviewer"]["parallel_execution"]

# Create config from dict
config = ToolExecutionConfig.from_dict(parallel_config)

# Create executor
executor = ParallelToolExecutor(config)
```

### Disable Parallel Execution

```python
# Disable parallel execution (use sequential fallback)
config = ToolExecutionConfig(enabled=False)
executor = ParallelToolExecutor(config)

# All tools will run sequentially
results = await executor.execute_parallel(Path("src/example.py"))
```

### Per-Tool Timeout Configuration

```python
# Configure different timeouts for different tools
config = ToolExecutionConfig(
    timeout_seconds=30,  # Default for all tools
    tool_timeouts={
        "mypy": 45,      # mypy needs more time (type checking)
        "jscpd": 60,     # jscpd needs more time (full project scan)
        "bandit": 15,    # bandit is usually fast
    }
)

executor = ParallelToolExecutor(config)
results = await executor.execute_parallel(Path("src/example.py"))
```

### Error Handling

```python
# Parallel execution never raises - always returns results
results = await executor.execute_parallel(Path("src/example.py"))

# Check for failures
successful = [r for r in results if r.is_success()]
timeouts = [r for r in results if r.is_timeout()]
errors = [r for r in results if r.is_error()]

print(f"✅ Successful: {len(successful)}")
print(f"⏱️  Timeouts: {len(timeouts)}")
print(f"❌ Errors: {len(errors)}")

# Handle individual failures
for result in timeouts:
    print(f"Warning: {result.tool} timed out after {result.duration:.2f}s")

for result in errors:
    print(f"Error: {result.tool} failed - {result.error}")
    if result.exit_code:
        print(f"  Exit code: {result.exit_code}")
```

### Performance Monitoring

```python
import time

async def benchmark_parallel_execution():
    config = ToolExecutionConfig(enabled=True)
    executor = ParallelToolExecutor(config)

    # Measure execution time
    start = time.time()
    results = await executor.execute_parallel(Path("src/example.py"))
    wall_clock_time = time.time() - start

    # Calculate individual tool times
    tool_times = {r.tool: r.duration for r in results}
    sequential_time = sum(tool_times.values())

    # Calculate speedup
    speedup = sequential_time / wall_clock_time

    print(f"Individual tool times: {tool_times}")
    print(f"Sequential time (sum): {sequential_time:.2f}s")
    print(f"Wall-clock time (parallel): {wall_clock_time:.2f}s")
    print(f"Speedup: {speedup:.2f}x")
```

---

## Integration with ReviewerAgent

The parallel executor is designed to integrate seamlessly with ReviewerAgent:

```python
from tapps_agents.agents.reviewer.agent import ReviewerAgent
from tapps_agents.agents.reviewer.tools.parallel_executor import (
    ParallelToolExecutor,
    ToolExecutionConfig,
)

class ReviewerAgent:
    def __init__(self, config_path: Path):
        # Load configuration
        self.config = self._load_config(config_path)

        # Initialize parallel executor
        parallel_config = ToolExecutionConfig.from_dict(
            self.config["parallel_execution"]
        )
        self.parallel_executor = ParallelToolExecutor(parallel_config)

    async def review_file(self, file_path: Path) -> dict:
        """Review file with parallel tool execution."""
        # Execute all quality tools in parallel
        results = await self.parallel_executor.execute_parallel(file_path)

        # Aggregate results
        return self._aggregate_results(results)
```

---

## Error Scenarios and Recovery

### Scenario 1: Individual Tool Timeout

**Behavior:** Tool exceeds configured timeout

**Recovery:**
- Tool marked as TIMEOUT
- Other tools continue execution
- ToolResult includes partial duration and error message

**Example:**
```python
# mypy times out after 45 seconds
ToolResult(
    tool="mypy",
    status=ToolStatus.TIMEOUT,
    data=None,
    duration=45.2,
    error="Timeout after 45.2s (limit: 45s)",
    exit_code=None
)
```

### Scenario 2: Individual Tool Error

**Behavior:** Tool raises exception during execution

**Recovery:**
- Tool marked as ERROR
- Other tools continue execution
- ToolResult includes error message and exit code (if available)

**Example:**
```python
# bandit fails with subprocess error
ToolResult(
    tool="bandit",
    status=ToolStatus.ERROR,
    data=None,
    duration=1.2,
    error="subprocess returned exit code 2",
    exit_code=2
)
```

### Scenario 3: Catastrophic Failure

**Behavior:** Parallel execution fails completely (e.g., asyncio error)

**Recovery:**
- Automatic fallback to sequential execution (if `fallback_to_sequential=True`)
- Returns empty list if fallback disabled

**Example:**
```python
# Parallel execution fails, falls back to sequential
executor = ParallelToolExecutor(
    ToolExecutionConfig(fallback_to_sequential=True)
)

# If parallel fails, automatically retries sequentially
results = await executor.execute_parallel(Path("file.py"))
```

### Scenario 4: No Tools Configured

**Behavior:** No tool runners provided

**Recovery:**
- Returns empty list
- Logs warning

---

## Testing

### Unit Testing with Mock Tool Functions

```python
import pytest
from pathlib import Path
from tapps_agents.agents.reviewer.tools.parallel_executor import (
    ParallelToolExecutor,
    ToolExecutionConfig,
    ToolStatus,
)

@pytest.mark.asyncio
async def test_parallel_execution_success():
    """Test successful parallel execution."""
    config = ToolExecutionConfig()
    executor = ParallelToolExecutor(config)

    # Mock tool functions
    async def mock_ruff(path: Path):
        return {"issues": []}

    async def mock_mypy(path: Path):
        return {"errors": []}

    tool_runners = {
        "ruff": mock_ruff,
        "mypy": mock_mypy,
    }

    # Execute
    results = await executor.execute_parallel(
        Path("test.py"),
        tool_runners=tool_runners
    )

    # Verify
    assert len(results) == 2
    assert all(r.status == ToolStatus.SUCCESS for r in results)
    assert {r.tool for r in results} == {"ruff", "mypy"}

@pytest.mark.asyncio
async def test_timeout_handling():
    """Test timeout handling."""
    config = ToolExecutionConfig(timeout_seconds=1)
    executor = ParallelToolExecutor(config)

    # Mock slow tool
    async def slow_tool(path: Path):
        await asyncio.sleep(10)  # Will timeout
        return {}

    tool_runners = {"slow": slow_tool}

    # Execute
    results = await executor.execute_parallel(
        Path("test.py"),
        tool_runners=tool_runners
    )

    # Verify timeout
    assert len(results) == 1
    assert results[0].status == ToolStatus.TIMEOUT
    assert results[0].duration >= 1.0
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_actual_tool_execution():
    """Test with actual quality tools."""
    config = ToolExecutionConfig()
    executor = ParallelToolExecutor(config)

    # Use actual tool runners from ReviewerAgent
    from tapps_agents.agents.reviewer.tools import (
        run_ruff_async,
        run_mypy_async,
    )

    tool_runners = {
        "ruff": run_ruff_async,
        "mypy": run_mypy_async,
    }

    # Execute on real file
    results = await executor.execute_parallel(
        Path("tapps_agents/core/config.py"),
        tool_runners=tool_runners
    )

    # Verify execution
    assert len(results) >= 2
    successful = [r for r in results if r.is_success()]
    assert len(successful) >= 1
```

---

## Performance Characteristics

### Typical Execution Times

| Tool | Sequential | Parallel | Speedup |
|------|------------|----------|---------|
| Ruff | 2-3s | 2-3s | 1x |
| mypy | 8-12s | 8-12s | 1x |
| bandit | 3-5s | 3-5s | 1x |
| pip-audit | 5-8s | 5-8s | 1x |
| jscpd | 2-4s | 2-4s | 1x |
| **Total** | **20-32s** | **10-16s** | **~2x** |

**Note:** Actual speedup depends on:
- Number of CPU cores available
- Tool execution time distribution
- I/O vs CPU-bound operations

### Memory Overhead

- **Sequential**: 1x tool memory usage
- **Parallel**: 4x tool memory usage (max_concurrent_tools=4)
- **Typical overhead**: ~100-200 MB for 4 concurrent tools

### Thread Safety

- ✅ **Immutable dataclasses**: ToolExecutionConfig, ToolResult (frozen=True)
- ✅ **No shared mutable state**: Each tool runs independently
- ✅ **Async-safe logging**: Uses thread-safe logger

---

## Configuration Reference

### Complete YAML Configuration

```yaml
# .tapps-agents/config.yaml
reviewer:
  parallel_execution:
    # Master switch for parallel execution
    enabled: true

    # Global timeout for all tools (seconds)
    timeout_seconds: 30

    # Maximum concurrent subprocess executions
    max_concurrent_tools: 4

    # Auto-fallback to sequential execution on errors
    fallback_to_sequential: true

    # Per-tool timeout overrides (seconds)
    tool_timeouts:
      mypy: 45      # Type checking can be slow
      jscpd: 60     # Full project scan needs more time
      bandit: 15    # Security scan is usually fast
      ruff: 20      # Linting is fast
      pip_audit: 30 # Dependency audit (default)
```

### Environment Variables

```bash
# Disable parallel execution via environment
export TAPPS_AGENTS_PARALLEL_EXECUTION_ENABLED=false

# Override timeout via environment
export TAPPS_AGENTS_PARALLEL_EXECUTION_TIMEOUT=60
```

---

## Troubleshooting

### Issue: "Timeout after Xs"

**Cause:** Tool exceeded configured timeout

**Solution:**
1. Increase timeout for specific tool:
   ```python
   config = ToolExecutionConfig(
       tool_timeouts={"mypy": 60}  # Increase from 30s to 60s
   )
   ```
2. Or increase global timeout:
   ```python
   config = ToolExecutionConfig(timeout_seconds=60)
   ```

### Issue: "Parallel execution failed"

**Cause:** Asyncio error or subprocess issue

**Solution:**
1. Check fallback is enabled:
   ```python
   config = ToolExecutionConfig(fallback_to_sequential=True)
   ```
2. Check logs for specific error:
   ```python
   import logging
   logging.getLogger("tapps_agents.agents.reviewer.tools.parallel_executor").setLevel(logging.DEBUG)
   ```

### Issue: High memory usage

**Cause:** Too many concurrent tools

**Solution:**
1. Reduce max_concurrent_tools:
   ```python
   config = ToolExecutionConfig(max_concurrent_tools=2)
   ```

### Issue: Windows async subprocess issues

**Cause:** Windows has limited asyncio subprocess support

**Solution:**
1. Fallback to sequential execution:
   ```python
   config = ToolExecutionConfig(enabled=False)
   ```

---

## API Stability

**Status**: Stable (v3.5.21)

**Compatibility:**
- ✅ **Backward Compatible**: Safe to upgrade from sequential execution
- ✅ **Immutable API**: Frozen dataclasses prevent accidental modifications
- ✅ **Semantic Versioning**: Breaking changes require major version bump

**Deprecation Policy:**
- No planned deprecations
- Future additions will be backward compatible

---

## Related Documentation

- [Architecture Design](../architecture/enh-001-workflow-enforcement-architecture.md)
- [Configuration Guide](../CONFIGURATION.md)
- [ReviewerAgent Documentation](../api/reviewer.md)
- [Testing Guide](../test-stack.md)

---

**Last Updated**: 2026-01-29
**Maintainer**: TappsCodingAgents Team
**License**: MIT
