# API Reference

**Version**: 2.0.8  
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
# MAL configuration removed - all LLM operations handled by Cursor Skills
print(config.agents.reviewer.quality_threshold)
```

See `docs/CONFIGURATION.md` for the full schema.

### Note on LLM Operations

All LLM operations are handled by Cursor Skills, which use the developer's configured model in Cursor.
- Agents prepare instruction objects that are executed via Cursor Skills
- No local LLM or API keys required
- Cursor handles all model selection and execution

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
# Reviewer - Single File
python -m tapps_agents.cli reviewer review path/to/file.py
python -m tapps_agents.cli reviewer score path/to/file.py
python -m tapps_agents.cli reviewer lint path/to/file.py
python -m tapps_agents.cli reviewer type-check path/to/file.py
python -m tapps_agents.cli reviewer report path/to/dir json markdown html

# Reviewer - Batch Operations (Multiple Files)
python -m tapps_agents.cli reviewer score file1.py file2.py file3.py
python -m tapps_agents.cli reviewer review file1.py file2.py --max-workers 4
python -m tapps_agents.cli reviewer lint file1.py file2.py --output results.json

# Reviewer - Glob Patterns
python -m tapps_agents.cli reviewer score --pattern "src/**/*.py"
python -m tapps_agents.cli reviewer review --pattern "tests/*.py" --max-workers 8
python -m tapps_agents.cli reviewer lint --pattern "**/*.ts" --output lint-report.html

# Reviewer - Output Formats
python -m tapps_agents.cli reviewer score file.py --output report.json
python -m tapps_agents.cli reviewer score file.py --output report.md --format markdown
python -m tapps_agents.cli reviewer score file.py --output report.html --format html

# Quick shortcut (same as reviewer score)
python -m tapps_agents.cli score path/to/file.py

# Enhancer - Prompt Enhancement
python -m tapps_agents.cli enhancer enhance "Create a user authentication feature"
python -m tapps_agents.cli enhancer enhance "Fix the bug in login.py" --output enhanced.md
python -m tapps_agents.cli enhancer enhance-quick "Quick enhancement" --output quick.md

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

## Batch Operations

The reviewer agent now supports batch processing for multiple files:

### Multiple Files
```bash
# Score multiple files at once
python -m tapps_agents.cli reviewer score file1.py file2.py file3.py

# Review multiple files with custom concurrency
python -m tapps_agents.cli reviewer review file1.py file2.py --max-workers 4
```

### Glob Patterns
```bash
# Process all Python files in a directory
python -m tapps_agents.cli reviewer score --pattern "src/**/*.py"

# Process test files only
python -m tapps_agents.cli reviewer lint --pattern "tests/*.py"
```

### Output Formats
```bash
# Save results to JSON file
python -m tapps_agents.cli reviewer score file.py --output report.json

# Generate HTML report
python -m tapps_agents.cli reviewer score file.py --output report.html --format html

# Generate Markdown report
python -m tapps_agents.cli reviewer score file.py --output report.md --format markdown

# Save lint results to file
python -m tapps_agents.cli reviewer lint file.py --output lint-report.json

# Save type-check results to file
python -m tapps_agents.cli reviewer type-check file.py --output type-check.json

# Batch lint with output file
python -m tapps_agents.cli reviewer lint file1.py file2.py --output batch-lint.json

# Batch type-check with HTML output
python -m tapps_agents.cli reviewer type-check --pattern "src/**/*.py" --output type-check.html --format html
```

## Enhancer Improvements

The enhancer agent now provides complete output with all stage data:

### Enhanced Output
The enhancer now displays:
- **Analysis**: Intent, scope, workflow type, complexity, domains, technologies
- **Requirements**: Gathered requirements from analyst and experts
- **Architecture Guidance**: Architecture recommendations and patterns
- **Codebase Context**: Related files and detected patterns
- **Quality Standards**: Quality thresholds and standards
- **Implementation Strategy**: Step-by-step implementation plan

### Example Output
```markdown
# Enhanced Prompt: Create a user authentication feature

## Analysis
- **Intent**: feature
- **Scope**: medium
- **Workflow Type**: greenfield
- **Complexity**: medium
- **Detected Domains**: security, user-management

## Requirements
1. Requirement 1: User authentication
2. Requirement 2: Password hashing

## Architecture Guidance
Use FastAPI with JWT tokens
Patterns: REST API, JWT

## Codebase Context
Related Files: auth.py, models.py
Patterns: MVC

## Quality Standards
Standards: PEP 8, Type hints
Thresholds: complexity < 5.0

## Implementation Strategy
Step 1: Create auth module
Step 2: Add JWT handling
```

## Related Documentation

- `docs/CONFIGURATION.md`
- `docs/QUICK_WORKFLOW_COMMANDS.md`
- `docs/EXPERT_SETUP_WIZARD.md`
- `docs/PROJECT_PROFILING_GUIDE.md`
- `docs/ARCHITECTURE.md`
