# API Reference

**Version**: 2.0.2  
**Last Updated**: January 2026

## Overview

TappsCodingAgents provides:

- a **Python API** (agent classes + workflow engine)
- a **CLI** (`tapps-agents` entrypoint)

## Python API

### Agent Lifecycle

All workflow agents follow the same basic pattern:

```python
import asyncio
from tapps_agents.agents.reviewer.agent import ReviewerAgent

async def main() -> None:
    agent = ReviewerAgent()
    await agent.activate()
    try:
        result = await agent.run("review", file="path/to/file.py")
        print(result)
    finally:
        await agent.close()

asyncio.run(main())
```

### Configuration

Configuration is loaded from `.tapps-agents/config.yaml` (searched upward from the current directory). If not found, defaults are used.

```python
from tapps_agents.core.config import load_config

config = load_config()  # defaults if no file is found
print(config.mal.default_provider)
print(config.agents.reviewer.quality_threshold)
```

See `docs/CONFIGURATION.md` for the full schema.

### Note on MAL vs Cursor

When invoked under Cursor (Skills / Background Agents), this repo’s default policy is **Cursor-only LLM**:
- the framework runs tools-only
- MAL calls are disabled unless you explicitly run with `TAPPS_AGENTS_MODE=headless`

See `docs/HOW_IT_WORKS.md`.

### Project Profiling

```python
from pathlib import Path
from tapps_agents.core.project_profile import ProjectProfileDetector, save_project_profile

profile = ProjectProfileDetector(project_root=Path.cwd()).detect_profile()
path = save_project_profile(profile)
print(path)  # .tapps-agents/project-profile.yaml
```

### Workflow Engine

```python
from pathlib import Path
from tapps_agents.workflow.executor import WorkflowExecutor
from tapps_agents.workflow.parser import WorkflowParser

workflow = WorkflowParser.parse_file(Path("workflows/presets/rapid-dev.yaml"))
executor = WorkflowExecutor(project_root=Path.cwd(), auto_detect=False)
state = executor.start(workflow=workflow)
print(state.workflow_id, state.status)
```

## CLI

### Entry Points

Both of these are supported:

- `tapps-agents ...` (installed console script)
- `python -m tapps_agents.cli ...` (module invocation)

### Top-Level Commands

From `python -m tapps_agents.cli --help`, the CLI exposes:

- **Agent subcommands**: `reviewer`, `planner`, `implementer`, `tester`, `debugger`, `documenter`, `analyst`, `architect`, `designer`, `improver`, `ops`, `enhancer`, `orchestrator`
- **Utility subcommands**: `workflow`, `init`, `doctor`, `score`, `setup-experts`, `analytics`, `create`, `hardware-profile` (or `hardware`)

### Command Naming (with and without `*`)

The CLI accepts **both** forms for many agent commands:

- `reviewer review ...`
- `reviewer *review ...` (alias)

### Common Examples

```bash
# Reviewer
python -m tapps_agents.cli reviewer review path/to/file.py
python -m tapps_agents.cli reviewer score path/to/file.py
python -m tapps_agents.cli reviewer lint path/to/file.py
python -m tapps_agents.cli reviewer type-check path/to/file.py
python -m tapps_agents.cli reviewer report path/to/dir json markdown html

# Quick shortcut (same as reviewer score)
python -m tapps_agents.cli score path/to/file.py

# Workflow presets
python -m tapps_agents.cli workflow list
python -m tapps_agents.cli workflow rapid
python -m tapps_agents.cli workflow full

# Project initialization
python -m tapps_agents.cli init

# Environment diagnostics
python -m tapps_agents.cli doctor
python -m tapps_agents.cli doctor --format json

# Expert setup wizard
python -m tapps_agents.cli setup-experts init
python -m tapps_agents.cli setup-experts add
python -m tapps_agents.cli setup-experts list

# Analytics
python -m tapps_agents.cli analytics dashboard
python -m tapps_agents.cli analytics agents
python -m tapps_agents.cli analytics workflows
python -m tapps_agents.cli analytics trends --metric-type agent_duration --days 30
python -m tapps_agents.cli analytics system

# Create new project (primary use case)
python -m tapps_agents.cli create "Build a task management web app"
python -m tapps_agents.cli create "Create a REST API for user management" --workflow rapid

# Hardware profile management
python -m tapps_agents.cli hardware-profile
python -m tapps_agents.cli hardware-profile --set nuc
python -m tapps_agents.cli hardware-profile --set auto
```

## Related Documentation

- `docs/CONFIGURATION.md`
- `docs/QUICK_WORKFLOW_COMMANDS.md`
- `docs/EXPERT_SETUP_WIZARD.md`
- `docs/PROJECT_PROFILING_GUIDE.md`
- `docs/ARCHITECTURE.md`
