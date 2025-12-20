# How to Force YAML Workflow Execution

This guide shows you how to force the AI assistant (or any code generation) to go through the full YAML workflow lifecycle instead of directly creating code.

## The Problem

When you use `@simple-mode *build` in Cursor chat, the AI assistant might bypass the framework and create code directly. This skips:
- ✅ Prompt enhancement (7 stages)
- ✅ Agent orchestration (Planner → Architect → Designer → Implementer)
- ✅ Quality gates and scoring
- ✅ Workflow state management

## Prerequisites

Before using YAML workflows, ensure your project is initialized:

1. **Initialize project** (first time setup):
   ```bash
   tapps-agents init
   ```
   This sets up:
   - `.tapps-agents/config.yaml` - Project configuration
   - `.cursor/rules/` - Cursor Rules for AI assistance
   - `workflows/presets/` - Workflow preset YAML files
   - `.claude/skills/` - Cursor Skills
   - `.cursor/background-agents.yaml` - Background Agents config

2. **Enable Simple Mode** (if using Simple Mode):
   ```bash
   tapps-agents simple-mode on
   ```
   Or run the onboarding wizard:
   ```bash
   tapps-agents simple-mode init
   ```

3. **Verify Simple Mode is enabled**:
   ```bash
   tapps-agents simple-mode status
   ```
   Should show `Enabled: Yes`

## Solutions: 3 Ways to Force YAML Workflow

### Method 1: Use WorkflowExecutor Script (Recommended)

Create a Python script that executes the workflow directly:

```python
# execute_workflow.py
import asyncio
import sys
import os
from pathlib import Path

# CRITICAL: Force headless mode to bypass Cursor mode
os.environ["TAPPS_AGENTS_MODE"] = "headless"

sys.path.insert(0, str(Path(__file__).parent))

from tapps_agents.workflow.executor import WorkflowExecutor
from tapps_agents.workflow.preset_loader import PresetLoader

async def main():
    # Load workflow preset
    loader = PresetLoader()
    workflow = loader.load_preset("simple-new-feature")  # or "full", "rapid", etc.
    
    # Create executor with auto mode
    executor = WorkflowExecutor(
        auto_detect=False,
        auto_mode=True,  # Fully automated
        project_root=Path.cwd()
    )
    
    # Set your prompt
    executor.user_prompt = "create an amazing modern dark html page that features all 2025 detailed, fun and cool features"
    
    # Execute workflow
    result = await executor.execute(workflow=workflow)
    
    if result.status == "completed":
        print("✅ Workflow completed!")
        for name, artifact in result.artifacts.items():
            print(f"  - {name}: {artifact.path}")
    else:
        print(f"❌ Workflow failed: {result.error}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Run it:**
```bash
python execute_workflow.py
```

### Method 2: Use CLI Workflow Command

Execute workflow via CLI (forces YAML execution):

```bash
# Set headless mode
$env:TAPPS_AGENTS_MODE = "headless"

# Execute workflow preset
python -m tapps_agents.cli workflow simple-new-feature --prompt "create an amazing modern dark html page that features all 2025 detailed, fun and cool features" --auto
```

**Available Presets:**
- `simple-new-feature` or `new-feature` - Simple feature workflow (enhance → plan → implement → review → test)
- `full` or `full-sdlc` - Full SDLC workflow
- `rapid` or `rapid-dev` - Rapid development
- `fix` or `maintenance` - Bug fix workflow
- `quality` - Quality improvement
- `hotfix` or `quick-fix` - Quick fixes for urgent issues
- `simple-full` - Simple Mode full lifecycle workflow

**Note:** Preset names support aliases. Use `python -m tapps_agents.cli workflow list` to see all available presets.

### Method 3: Use SimpleModeHandler (Build Orchestrator)

Execute through Simple Mode's BuildOrchestrator (goes through 7-stage enhancement):

```python
# execute_simple_mode_build.py
import asyncio
import sys
import os
from pathlib import Path

os.environ["TAPPS_AGENTS_MODE"] = "headless"
sys.path.insert(0, str(Path(__file__).parent))

from tapps_agents.simple_mode.nl_handler import SimpleModeHandler

async def main():
    handler = SimpleModeHandler(project_root=Path.cwd())
    
    command = "create an amazing modern dark html page that features all 2025 detailed, fun and cool features"
    
    result = await handler.handle(command)
    
    if result.get('success'):
        print("✅ Build workflow completed!")
        print(f"Intent: {result.get('intent')}")
        print(f"Agents executed: {result.get('agents_executed', 0)}")
    else:
        print(f"❌ Failed: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Environment Variable

**CRITICAL:** Always set this to force headless mode:

```python
os.environ["TAPPS_AGENTS_MODE"] = "headless"
```

**Why?** 
- In Cursor mode, workflows use Background Agents (manual execution)
- In headless mode, workflows execute directly with terminal output
- This ensures the full YAML workflow is followed

## What Happens in the YAML Workflow

When you force YAML workflow execution, here's what happens:

### 1. Workflow Loading
- Loads YAML file from `workflows/presets/simple-new-feature.yaml`
- Parses steps, dependencies, and conditions

### 2. Step Execution (in order)
```
enhance → planning → implementation → review → testing → complete
```

### 3. Each Step Uses Agents
- **enhance**: EnhancerAgent (7-stage enhancement)
- **planning**: PlannerAgent (creates user stories)
- **implementation**: ImplementerAgent (generates code)
- **review**: ReviewerAgent (quality scoring + gates)
- **testing**: TesterAgent (generates tests)

### 4. Quality Gates
- Code scoring (complexity, security, maintainability, test coverage, performance)
- If score < threshold → loopback to implementation
- Only proceeds when quality gates pass

### 5. Artifacts Generated
- Enhanced requirements markdown
- User stories
- Source code files
- Test files
- Review reports

## Example: Full Execution Flow

```bash
# 1. Create script
cat > execute_build.py << 'EOF'
import asyncio
import os
from pathlib import Path
import sys

os.environ["TAPPS_AGENTS_MODE"] = "headless"
sys.path.insert(0, str(Path.cwd()))

from tapps_agents.workflow.executor import WorkflowExecutor
from tapps_agents.workflow.preset_loader import PresetLoader

async def main():
    loader = PresetLoader()
    workflow = loader.load_preset("simple-new-feature")
    
    executor = WorkflowExecutor(auto_detect=False, auto_mode=True)
    executor.user_prompt = "create an amazing modern dark html page..."
    
    result = await executor.execute(workflow=workflow)
    print(f"Status: {result.status}")

asyncio.run(main())
EOF

# 2. Run it
python execute_build.py
```

## Verifying YAML Workflow Execution

Check these indicators that YAML workflow was used:

1. **Workflow State Files**: `.tapps-agents/workflows/` directory created
2. **Step-by-step output**: See each step executing
3. **Artifacts**: Multiple files created (stories/, src/, tests/)
4. **Quality scores**: Review step shows scoring output
5. **Loopbacks**: If quality gates fail, you'll see retry attempts

## Troubleshooting

### Workflow doesn't execute
- ✅ **Run project init first**: `tapps-agents init` (sets up workflow presets)
- ✅ **Check `TAPPS_AGENTS_MODE=headless` is set** (required for direct execution)
- ✅ **Verify workflow preset exists**: Check `workflows/presets/simple-new-feature.yaml` exists
- ✅ **Check Simple Mode is enabled**: Run `tapps-agents simple-mode status` or check `.tapps-agents/config.yaml` has `simple_mode.enabled: true`
- ✅ **Verify preset name**: Use `python -m tapps_agents.cli workflow list` to see available presets

### Still bypassing workflow
- ✅ Use Method 1 (WorkflowExecutor script) - most reliable
- ✅ Don't use `@simple-mode` in chat - use CLI or script instead
- ✅ Check you're not in Cursor mode (set headless)

### Want to see what's happening
- ✅ Set `auto_mode=False` to see prompts
- ✅ Check `.tapps-agents/workflows/` for state files
- ✅ Look for step-by-step terminal output

## Summary

**To force YAML workflow execution:**

1. ✅ **Initialize project**: Run `tapps-agents init` (first time only)
2. ✅ **Enable Simple Mode**: Run `tapps-agents simple-mode on` (if using Simple Mode)
3. ✅ **Set environment**: `TAPPS_AGENTS_MODE=headless` (critical for direct execution)
4. ✅ **Use WorkflowExecutor**: Load preset, execute workflow via script or CLI
5. ✅ **Don't rely on chat**: Use CLI or Python scripts instead of Cursor chat
6. ✅ **Verify execution**: Check artifacts and state files in `.tapps-agents/workflows/`

**Key Points:**
- The `TAPPS_AGENTS_MODE=headless` environment variable is **critical** - without it, workflows use Background Agents (manual execution)
- Use `WorkflowExecutor` directly via Python scripts or CLI commands
- Don't rely on `@simple-mode` in Cursor chat - it may bypass the framework
- Always verify Simple Mode is enabled: `tapps-agents simple-mode status`

## Quick Start for New Projects

```bash
# 1. Initialize project (first time)
tapps-agents init

# 2. Enable Simple Mode
tapps-agents simple-mode on

# 3. Verify setup
tapps-agents simple-mode status

# 4. Execute workflow (force YAML execution)
$env:TAPPS_AGENTS_MODE = "headless"  # Windows PowerShell
# export TAPPS_AGENTS_MODE=headless  # Linux/Mac

python -m tapps_agents.cli workflow simple-new-feature --prompt "your description" --auto
```

