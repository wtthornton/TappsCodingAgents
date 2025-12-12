# TappsCodingAgents - Developer Guide

This guide explains how to use TappsCodingAgents in a project.

## Install

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -e .
```

## Run the CLI

```bash
python -m tapps_agents.cli --help
```

The CLI includes:

- agent subcommands: `reviewer`, `planner`, `implementer`, `tester`, `debugger`, `documenter`, `analyst`, `architect`, `designer`, `improver`, `ops`, `enhancer`, `orchestrator`
- utility subcommands: `workflow`, `init`, `score`, `setup-experts`, `analytics`

## Configuration (optional)

Create `.tapps-agents/config.yaml` in your project root.

```bash
mkdir -p .tapps-agents
cp templates/default_config.yaml .tapps-agents/config.yaml
```

See `docs/CONFIGURATION.md`.

## Core Usage

### Reviewer

```bash
python -m tapps_agents.cli reviewer score path/to/file.py
python -m tapps_agents.cli reviewer review path/to/file.py
python -m tapps_agents.cli reviewer lint path/to/file.py
python -m tapps_agents.cli reviewer type-check path/to/file.py
python -m tapps_agents.cli reviewer report path/to/dir json markdown html
```

### Planner

```bash
python -m tapps_agents.cli planner plan "Add user authentication"
python -m tapps_agents.cli planner create-story "User can log in" --epic auth --priority high
python -m tapps_agents.cli planner list-stories
```

### Implementer

```bash
python -m tapps_agents.cli implementer implement "Add health endpoint" src/health.py
python -m tapps_agents.cli implementer refactor src/service.py "Add type hints"
```

### Tester

```bash
python -m tapps_agents.cli tester test src/service.py
python -m tapps_agents.cli tester run-tests
```

## Workflow Presets

List and run workflow presets:

```bash
python -m tapps_agents.cli workflow list
python -m tapps_agents.cli workflow rapid
```

Workflow state is persisted under:

- `.tapps-agents/workflow-state/`

## Experts (optional)

Use the interactive wizard:

```bash
python -m tapps_agents.cli setup-experts init
python -m tapps_agents.cli setup-experts add
python -m tapps_agents.cli setup-experts list
```

This creates/updates:

- `.tapps-agents/experts.yaml`
- `.tapps-agents/domains.md`
- `.tapps-agents/knowledge/<domain>/*.md` (if RAG is enabled for an expert)

See `docs/EXPERT_SETUP_WIZARD.md` and `docs/EXPERT_CONFIG_GUIDE.md`.

## Project Profiling

Project profiling is persisted to:

- `.tapps-agents/project-profile.yaml`

See `docs/PROJECT_PROFILING_GUIDE.md`.

## Analytics

The CLI exposes an analytics dashboard:

```bash
python -m tapps_agents.cli analytics dashboard
python -m tapps_agents.cli analytics system
```

Analytics history is stored under:

- `.tapps-agents/analytics/history/`

## Cursor Integration

If you’re using Cursor, see:

- `docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md`
- `docs/BACKGROUND_AGENTS_GUIDE.md`
- `docs/MULTI_AGENT_ORCHESTRATION_GUIDE.md`

## Extending the Framework

- **Add a new agent**: implement a new agent under `tapps_agents/agents/<agent>/agent.py` and wire it into the CLI if you want CLI access.
- **Add a new project expert**: use `.tapps-agents/experts.yaml` + `.tapps-agents/domains.md` + `.tapps-agents/knowledge/<domain>/*.md`.

## Related Docs

- `docs/API.md`
- `docs/ARCHITECTURE.md`
- `docs/CONFIGURATION.md`
