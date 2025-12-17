# TappsCodingAgents - Developer Guide

This guide explains how to use TappsCodingAgents in a project.

## Install

### For End Users (Runtime Install)

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install tapps-agents
```

This installs only the runtime dependencies needed for CLI usage.

### For Developers (Editable + Dev Tools)

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -e ".[dev]"
```

This installs the package in editable mode with all development tools (pytest, ruff, mypy, black, etc.).

**Note**: `pyproject.toml` is the authoritative source for dependencies. See `docs/DEPENDENCY_POLICY.md` for details.

## Run the CLI

```bash
python -m tapps_agents.cli --help
```

The CLI includes:

- agent subcommands: `reviewer`, `planner`, `implementer`, `tester`, `debugger`, `documenter`, `analyst`, `architect`, `designer`, `improver`, `ops`, `enhancer`, `orchestrator`
- utility subcommands: `workflow`, `init`, `score`, `setup-experts`, `analytics`

## Configuration (optional)

Create `.tapps-agents/config.yaml` in your project root.

Recommended:

```bash
python -m tapps_agents.cli init
```

Or copy the template manually:

```bash
mkdir -p .tapps-agents
cp templates/default_config.yaml .tapps-agents/config.yaml
```

### User Role Templates

You can customize agent behavior based on your role by setting the `user_role` field in your config:

```yaml
# .tapps-agents/config.yaml
user_role: senior-developer  # Options: senior-developer, junior-developer, tech-lead, product-manager, qa-engineer
```

This applies role-specific defaults for verbosity, workflow preferences, expert priorities, and more. See [User Role Templates Guide](USER_ROLE_TEMPLATES_GUIDE.md) for details.

See `docs/CONFIGURATION.md` for complete configuration reference.

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

## Running Tests (For Agents)

When agents need to run unit tests directly (e.g., via terminal commands), they should follow these guidelines:

### Recommended: Parallel Execution

**Always use parallel execution** for optimal performance (5-10x faster):

```bash
# Run all unit tests in parallel (recommended)
python -m pytest tests/ -m unit -n auto

# Run specific test file in parallel
python -m pytest tests/unit/test_file.py -n auto

# With coverage (when needed)
python -m pytest tests/ -m unit -n auto --cov=tapps_agents --cov-report=term
```

### Key Points

- **`-n auto`**: Enables parallel execution using all CPU cores (requires `pytest-xdist`, included in `requirements.txt`)
- **`-m unit`**: Runs only unit tests (faster, excludes integration/e2e tests)
- **Sequential mode**: Only use when debugging test isolation issues: `python -m pytest tests/ -m unit` (no `-n` flag)

### Performance

- **Parallel execution**: ~1-2 minutes for 1200+ unit tests
- **Sequential execution**: ~5-10 minutes for 1200+ unit tests
- **Speedup**: 5-10x faster with parallel execution

### Using Tester Agent

The Tester Agent automatically uses parallel execution when running tests via `*run-tests` command. For direct test execution, use the commands above.

See `docs/TEST_PERFORMANCE_GUIDE.md` for complete performance optimization guide.

## Planned Enhancements

### SDLC Quality Engine Improvements

The framework is being enhanced with a **self-correcting quality engine** that achieves "zero issues" consistently across any codebase.

**Key Features (Planned):**
- **Pluggable Validation Layer**: Stack-agnostic validation that adapts to your project's detected stack
- **Comprehensive Verification**: Expansion beyond unit tests to include linters, type checks, security scans, dependency audits, artifact integrity checks
- **Standardized Issues Manifest**: Machine-actionable issue schema for deterministic remediation
- **Composite Gating Model**: Gates evaluate issues + verification outcomes, not just numeric scores
- **Bounded Loopback Protocol**: Automatic remediation with structured fix plans and re-validation
- **Traceability Matrix**: Requirements → stories → validations mapping for completeness verification

**Status**: Design phase - See [SDLC Improvements Analysis](../SDLC_ISSUES_AND_IMPROVEMENTS_ANALYSIS.md) and [Epic 1: SDLC Quality Engine](prd/epic-1-sdlc-quality-engine.md)

### Dynamic Expert & RAG Engine

An always-on **Dynamic Knowledge/Expert Orchestrator** that automatically detects project domains, creates experts, and populates knowledge bases.

**Key Features (Planned):**
- **Automatic Expert Creation**: Technical experts (framework-controlled) + project/business experts (generated from repo signals)
- **Knowledge Ingestion Pipeline**: Auto-fills RAG from project sources, dependency sources (Context7 KB), and operational sources
- **Expert Engine Runtime**: Continuously detects needed domain knowledge and proactively consults experts
- **Governance & Safety**: Do-not-index filters, prompt-injection handling, retention controls, optional human approval mode
- **Observability**: Metrics tracking with scheduled KB maintenance jobs

**Status**: Design phase - See [SDLC Improvements Analysis](../SDLC_ISSUES_AND_IMPROVEMENTS_ANALYSIS.md) and [Epic 2: Dynamic Expert & RAG Engine](prd/epic-2-dynamic-expert-rag-engine.md)

## Related Docs

- `docs/API.md`
- `docs/ARCHITECTURE.md`
- `docs/CONFIGURATION.md`
- `docs/TEST_PERFORMANCE_GUIDE.md` - Test execution performance optimization
