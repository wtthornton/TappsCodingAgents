# Step 4: Design Specifications - Remove Background Agents

## API Changes

### Removed APIs

#### 1. Background Agent API Client
**File:** `tapps_agents/workflow/background_agent_api.py`

**Removed Classes:**
- `BackgroundAgentAPI`
  - `list_agents()` - List configured Background Agents
  - `trigger_agent()` - Trigger Background Agent execution
  - `get_agent_status()` - Get Background Agent status
  - `wait_for_completion()` - Wait for Background Agent to complete

#### 2. Background Agent Configuration
**File:** `tapps_agents/workflow/background_agent_config.py`

**Removed Classes:**
- `BackgroundAgentConfigValidator`
  - `validate_file_exists()` - Validate config file exists
  - `validate_file_permissions()` - Validate file permissions
  - `validate_yaml_syntax()` - Validate YAML syntax
  - `validate_schema()` - Validate configuration schema
  - `validate()` - Complete validation

- `BackgroundAgentConfigGenerator`
  - `generate_from_template()` - Generate config from template
  - `generate_minimal_config()` - Generate minimal config

#### 3. Background Agent Generator
**File:** `tapps_agents/workflow/background_agent_generator.py`

**Removed Classes:**
- `GeneratedAgentConfig` - Configuration data class
- `BackgroundAgentGenerator`
  - `_ensure_config_file()` - Ensure config file exists
  - `_load_config()` - Load configuration
  - `_save_config()` - Save configuration
  - `_backup_config()` - Backup configuration
  - `generate_agent_config()` - Generate agent config
  - `apply_workflow_configs()` - Apply workflow configs
  - `cleanup_workflow_configs()` - Cleanup workflow configs
  - `validate_config()` - Validate config

#### 4. Background Agent Auto Executor
**File:** `tapps_agents/workflow/background_auto_executor.py`

**Removed Classes:**
- `AdaptivePolling` - Adaptive polling strategy
- `BackgroundAgentAutoExecutor`
  - `execute()` - Execute Background Agent
  - `_poll_for_completion()` - Poll for completion
  - `_check_completion()` - Check completion status

#### 5. Background Agent Wrapper
**File:** `tapps_agents/core/background_wrapper.py`

**Removed Classes:**
- `BackgroundAgentWrapper`
  - `setup()` - Setup Background Agent environment
  - `run_command()` - Run Background Agent command
  - `cleanup()` - Cleanup Background Agent resources
  - `get_progress()` - Get Background Agent progress

#### 6. Background Agent Implementation Classes
**Files:** Multiple files in `tapps_agents/workflow/`

**Removed Classes:**
- `BackgroundContextAgent` - Context management Background Agent
- `BackgroundDocsAgent` - Documentation Background Agent
- `BackgroundOpsAgent` - Operations Background Agent
- `BackgroundQualityAgent` - Quality analysis Background Agent
- `BackgroundTestingAgent` - Testing Background Agent

### Modified APIs

#### 1. WorkflowExecutor
**File:** `tapps_agents/workflow/executor.py`

**Changes:**
- Remove `background_agent_generator` parameter from `__init__`
- Remove `BackgroundAgentGenerator` import
- Remove `_cleanup_background_agents()` method
- Remove Background Agent cleanup calls from `mark_step_complete()`

**Before:**
```python
def __init__(self, ..., bg_agent_enabled=True):
    self.background_agent_generator = (
        BackgroundAgentGenerator(self.project_root) if bg_agent_enabled else None
    )

def _cleanup_background_agents(self):
    if self.background_agent_generator and self.state:
        self.background_agent_generator.cleanup_workflow_configs(...)
```

**After:**
```python
def __init__(self, ...):
    # Background Agent Generator removed
    pass
# _cleanup_background_agents() removed
```

#### 2. CursorWorkflowExecutor
**File:** `tapps_agents/workflow/cursor_executor.py`

**Changes:**
- Remove `BackgroundAgentAutoExecutor` import
- Remove Background Agent auto-execution logic
- Use direct execution/Skills only

**Before:**
```python
from .background_auto_executor import BackgroundAgentAutoExecutor

def __init__(self, ...):
    self.auto_executor = BackgroundAgentAutoExecutor(...)
```

**After:**
```python
# BackgroundAgentAutoExecutor import removed
# Direct execution used instead
```

#### 3. SkillInvoker
**File:** `tapps_agents/workflow/skill_invoker.py`

**Changes:**
- Remove `BackgroundAgentAPI` import
- Remove `background_agent_api` parameter
- Remove Background Agent API calls
- Remove Background Agent-specific agent classes imports
- Use `DirectExecutionFallback` only

**Before:**
```python
from .background_agent_api import BackgroundAgentAPI
from .background_quality_agent import BackgroundQualityAgent
from .background_testing_agent import BackgroundTestingAgent

def __init__(self, ..., use_api=True):
    self.background_agent_api = BackgroundAgentAPI() if use_api else None

async def _execute_skill_command(...):
    if self.use_api and self.background_agent_api:
        # Background Agent API calls
        ...
```

**After:**
```python
# Background Agent imports removed
# Direct execution fallback used exclusively
```

#### 4. CLI Commands

##### status.py
**Changes:**
- Remove `BackgroundAgentAPI` import
- Remove Background Agent status checking
- Remove Background Agent status display

**Before:**
```python
from ...workflow.background_agent_api import BackgroundAgentAPI

def show_status(...):
    api = BackgroundAgentAPI()
    agents = api.list_agents()
    # Display Background Agent status
```

**After:**
```python
# Background Agent status removed
# Display other status information only
```

##### top_level.py
**Changes:**
- Remove Background Agent configuration commands
- Remove Background Agent config generation

**Before:**
```python
from ...workflow.background_agent_config import (
    BackgroundAgentConfigGenerator,
    BackgroundAgentConfigValidator,
)
```

**After:**
```python
# Background Agent config imports removed
# Config commands removed
```

##### simple_mode.py
**Changes:**
- Remove Background Agent warnings
- Remove Background Agent availability checks

**Before:**
```python
if is_cursor_mode():
    safe_print("WARNING: Running in Cursor mode - workflow will use Background Agents")
```

**After:**
```python
# Background Agent warnings removed
# Direct execution messages only
```

#### 5. Init Project
**File:** `tapps_agents/core/init_project.py`

**Changes:**
- Remove Background Agent configuration generation
- Keep empty background-agents.yaml for reference only

**Before:**
```python
def init_background_agents(...):
    generator = BackgroundAgentConfigGenerator(...)
    generator.generate_minimal_config(...)
```

**After:**
```python
# Background Agent config generation removed
# Empty config file kept for reference
```

#### 6. Health Checker
**File:** `tapps_agents/workflow/health_checker.py`

**Changes:**
- Remove `BackgroundAgentConfigValidator` import
- Remove Background Agent config validation

**Before:**
```python
from .background_agent_config import BackgroundAgentConfigValidator

def check_background_agents(...):
    validator = BackgroundAgentConfigValidator()
    is_valid, errors, warnings = validator.validate()
```

**After:**
```python
# Background Agent validation removed
# Other health checks remain
```

#### 7. Module Exports
**File:** `tapps_agents/workflow/__init__.py`

**Changes:**
- Remove Background Agent class exports
- Keep artifact class exports (data structures)

**Before:**
```python
# Background Agents (lazy imports - use direct imports when needed)
# "BackgroundDocsAgent",
# "BackgroundOpsAgent",
# ...
```

**After:**
```python
# Background Agent exports removed
# Artifact exports remain (data structures only)
```

## Interface Changes

### Execution Flow Interface

#### Before: Multiple Execution Paths
```
Workflow Step
    ├─→ Cursor Skills (foreground)
    ├─→ Background Agent API
    │       └─→ Background Agent (background process)
    └─→ Direct Execution (fallback)
```

#### After: Simplified Execution Paths
```
Workflow Step
    ├─→ Cursor Skills (foreground)
    └─→ Direct Execution (fallback)
```

### Configuration Interface

#### Before: Background Agent Configuration
```yaml
agents:
  - name: "Quality Analyzer"
    type: "background"
    commands: [...]
    watch_paths: [...]
    triggers: [...]
global:
  max_parallel_agents: 4
  timeout_seconds: 3600
```

#### After: Empty Configuration (Reference Only)
```yaml
agents: []  # Background Agents removed
global:
  # Global settings kept for reference
  context7_cache: ".tapps-agents/kb/context7-cache"
  output_directory: ".tapps-agents/reports"
  worktree_base: ".tapps-agents/worktrees"
```

## Data Structure Changes

### Preserved Structures

#### Artifact Classes (Data Structures Only)
- `DocumentationArtifact` - Documentation results structure
- `OperationsArtifact` - Operations results structure
- `QualityArtifact` - Quality analysis results structure
- `TestingArtifact` - Testing results structure
- `ContextArtifact` - Context management results structure

**Rationale:** These are data structures, not Background Agent implementations. They can be produced by Skills or direct execution.

### Removed Structures

#### Background Agent Config Structures
- `GeneratedAgentConfig` - Generated agent configuration
- Background Agent validation structures
- Background Agent generation structures

## Migration Guide

### For Framework Users

**Before:**
```python
from tapps_agents.workflow.background_agent_api import BackgroundAgentAPI

api = BackgroundAgentAPI()
agents = api.list_agents()
```

**After:**
```python
# Background Agent API removed
# Use direct execution or Cursor Skills instead
```

### For Framework Maintainers

**Before:**
```python
from tapps_agents.workflow.background_agent_generator import BackgroundAgentGenerator

generator = BackgroundAgentGenerator(project_root)
generator.apply_workflow_configs(configs, workflow_id)
```

**After:**
```python
# Background Agent Generator removed
# No Background Agent config generation needed
```

## Backward Compatibility

### Breaking Changes

1. **Background Agent API removed** - Code using Background Agent API will break
2. **Background Agent config generation removed** - Config generation code will break
3. **Background Agent wrapper removed** - Wrapper usage will break

### Compatible Changes

1. **Artifact structures preserved** - Code using artifact classes continues to work
2. **Workflow execution preserved** - Workflows work with direct execution/Skills
3. **Configuration file structure** - Empty config file kept for reference

## Testing Strategy

### Unit Tests

1. Remove Background Agent unit tests
2. Update tests that mock Background Agent APIs
3. Test direct execution paths

### Integration Tests

1. Remove Background Agent integration tests
2. Test workflow execution with direct execution only
3. Test Cursor Skills integration

### Regression Tests

1. Ensure existing workflows still work
2. Ensure artifact structures work correctly
3. Ensure direct execution works correctly
