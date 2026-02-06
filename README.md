# TappsCodingAgents

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/pypi-tapps--agents-blue.svg)](https://pypi.org/project/tapps-agents/)
[![Version](https://img.shields.io/badge/version-3.6.4-blue.svg)](CHANGELOG.md)

**An AI coding agent framework with quality gates, workflow orchestration, and adaptive learning.**

TappsCodingAgents orchestrates 14 specialized agents across the full software development lifecycle. Use natural language commands in Cursor IDE or the CLI to plan, implement, review, test, and ship code with built-in quality enforcement.

---

## Why TappsCodingAgents?

- **Quality by default** - Every workflow includes code review, scoring, and configurable quality gates
- **14 specialized agents** - Analyst, Planner, Architect, Designer, Implementer, Debugger, Tester, Reviewer, Improver, Documenter, Ops, Orchestrator, Enhancer, Evaluator
- **Simple Mode** - Natural language interface: `@simple-mode Build a user auth module`
- **16 built-in experts** - Security, Performance, Testing, Architecture, DevOps, and more
- **Adaptive learning** - Auto-generates experts, adjusts scoring weights, and improves with each use
- **Works where you code** - Cursor IDE (Skills), Claude Desktop (Commands), Claude Code CLI

---

## Quick Start

### 1. Install

```bash
pip install tapps-agents
```

> **Requires Python 3.12+.** On Windows, if `tapps-agents` is not found after install, use `python -m tapps_agents.cli` or a project venv. See [Troubleshooting](docs/TROUBLESHOOTING_CLI_INSTALLATION.md).

### 2. Initialize in your project

```bash
cd /path/to/your-project
tapps-agents init
```

This sets up Cursor Skills, Rules, workflow presets, configuration, and MCP integration.

### 3. Verify

```bash
tapps-agents doctor
```

### 4. Use in Cursor IDE

```
@simple-mode Build a user authentication module
@simple-mode Review src/api/auth.py
@simple-mode Fix the error in auth.py
@simple-mode Add tests for service.py
```

Or use individual agents:

```
@reviewer *review src/api/auth.py
@implementer *implement "Add validation" src/api/auth.py
@tester *test src/api/auth.py
```

### 5. Or use the CLI

```bash
tapps-agents workflow full --prompt "Add user authentication"
tapps-agents workflow fix --prompt "Fix the login timeout bug"
tapps-agents score src/api/auth.py
tapps-agents reviewer review src/api/auth.py
```

---

## How It Works

TappsCodingAgents uses an **instruction-based architecture**:

1. **You describe the task** in natural language (Cursor chat or CLI)
2. **Simple Mode detects your intent** and selects the right agents
3. **Agents prepare structured instructions** (plans, reviews, tests, code)
4. **Cursor Skills execute** using your configured LLM (no API keys needed)
5. **Quality gates enforce standards** before completion

```
User prompt  -->  Intent detection  -->  Agent pipeline  -->  Quality gates  -->  Output
                  (Simple Mode)         (plan/impl/test)     (score >= 70)
```

No local LLM required. Cursor handles all LLM operations via Skills.

---

## What's Included

### 14 Workflow Agents

| Phase | Agents | Purpose |
|-------|--------|---------|
| **Planning** | Analyst, Planner | Requirements, user stories, task breakdown |
| **Design** | Architect, Designer | System architecture, API design, data models |
| **Development** | Implementer, Debugger, Documenter | Code generation, debugging, documentation |
| **Testing** | Tester | Unit/integration tests, coverage analysis |
| **Quality** | Reviewer, Improver | Code review with 7-category scoring, refactoring |
| **Operations** | Ops | Security scanning, compliance, dependency auditing |
| **Orchestration** | Orchestrator, Enhancer, Evaluator | Workflow coordination, prompt enhancement, evaluation |

### 22 Cursor Skills

All 14 agents plus Simple Mode, Expert, Backend/Frontend Patterns, Bug-Fix Agent, Coding Standards, Security Review, and a custom skill example.

### 16 Built-in Experts

Security, Performance, Testing, Data Privacy, Accessibility, UX, Code Quality, Software Architecture, DevOps, Documentation, AI Frameworks, Observability, API Design, Cloud Infrastructure, Database, Agent Learning.

Backed by **119 knowledge files** across 16 domains with RAG integration.

### 7-Category Code Scoring

Every review produces scores (0-10) for: Complexity, Security, Maintainability, Test Coverage, Performance, Structure, and Developer Experience.

---

## Workflow Presets

Choose the right level of rigor for your task:

| Preset | Steps | Best For | Command |
|--------|-------|----------|---------|
| **Fix** | 3-6 | Bug fixes, hotfixes | `tapps-agents workflow fix` |
| **Rapid Dev** | 5-7 | Standard features | `tapps-agents workflow rapid-dev` |
| **Full SDLC** | 5-10 | Complete lifecycle | `tapps-agents workflow full` |
| **Quality** | 6 | Code review cycle | `tapps-agents workflow quality` |
| **Brownfield** | varies | Existing codebase analysis | `tapps-agents workflow brownfield` |

All workflows include **adaptive checkpoints** that optimize execution:
- **Checkpoint 1** (After Enhance): Detects workflow mismatch early
- **Checkpoint 2** (After Planning): Analyzes task complexity, may switch to simpler workflow
- **Checkpoint 3** (After Test): Quality-based early termination (saves 12K-50K tokens)

---

## Simple Mode Commands

Simple Mode is the primary interface for most users:

```
@simple-mode *build "description"       # Feature development (plan/impl/review/test)
@simple-mode *fix <file> "description"  # Bug fixing workflow
@simple-mode *review <file>             # Code quality review
@simple-mode *test <file>               # Test generation
@simple-mode *refactor <file>           # Code modernization
@simple-mode *explore <query>           # Codebase exploration
@simple-mode *enhance "prompt"          # Prompt enhancement
@simple-mode *epic <epic-doc.md>        # Execute Epic with dependency resolution
@simple-mode *full "description"        # Full SDLC (9 steps, for framework dev)
@simple-mode *pr "title"               # Pull request with quality scores
@simple-mode *breakdown "prompt"        # Task breakdown
@simple-mode *todo <bd args>            # Beads-backed task tracking
```

---

## CLI Reference

```bash
# Top-level commands
tapps-agents init                    # Initialize project
tapps-agents doctor                  # Environment diagnostics
tapps-agents score <file>            # Quick quality score
tapps-agents workflow <preset>       # Run workflow preset
tapps-agents health overview         # System health summary
tapps-agents simple-mode <cmd>       # Simple Mode management

# Agent commands (tapps-agents <agent> <command>)
tapps-agents reviewer review <file>  # Code review
tapps-agents reviewer score <file>   # Quick scoring
tapps-agents implementer implement "desc" <file>
tapps-agents tester test <file>
tapps-agents debugger debug "error" --file <file>
tapps-agents enhancer enhance "prompt"
tapps-agents planner plan "description"
tapps-agents architect design "description"

# Epic & Expert
tapps-agents epic status             # Epic progress
tapps-agents expert list             # List available experts
tapps-agents expert consult "query" --domain security

# Workflow state
tapps-agents workflow state list     # List workflow states
tapps-agents workflow resume         # Resume interrupted workflow

# Project management
tapps-agents create "description"    # Create new project
tapps-agents status                  # Active worktrees and progress
tapps-agents continuous-bug-fix      # Automated bug fixing loop
```

---

## Project Structure

```
TappsCodingAgents/
├── tapps_agents/                # Framework source code
│   ├── agents/                  #   14 workflow agents
│   ├── core/                    #   Base classes, config, instructions
│   ├── epic/                    #   Epic orchestration and state management
│   ├── experts/                 #   Expert system (16 built-in + industry)
│   │   └── knowledge/           #     119 knowledge files across 16 domains
│   ├── simple_mode/             #   Natural language orchestration
│   │   └── orchestrators/       #     18 workflow orchestrators
│   ├── workflow/                #   Workflow engine, parsers, handlers
│   ├── context7/                #   Context7 KB integration
│   ├── mcp/                     #   MCP Gateway (5 servers)
│   ├── health/                  #   Health monitoring
│   ├── quality/                 #   Quality gates and enforcement
│   └── continuous_bug_fix/      #   Automated bug fixing
├── workflows/presets/           # 5 YAML workflow presets
├── .claude/skills/              # 22 Cursor Skills
├── .claude/agents/              # 6 Claude Code subagents
├── .cursor/rules/               # 15 Cursor Rules files
├── templates/                   # Agent roles, project types, user roles
├── tests/                       # 377 test files (unit, integration, e2e)
├── docs/                        # Documentation
└── requirements/                # Specifications and requirements
```

---

## Configuration

After running `tapps-agents init`, configuration lives in `.tapps-agents/`:

```yaml
# .tapps-agents/config.yaml
quality:
  overall_threshold: 70        # Minimum overall score
  security_threshold: 6.5      # Minimum security score
  maintainability_threshold: 7.0

simple_mode:
  enabled: true
  enable_checkpoints: true     # Adaptive workflow optimization

epic:
  story_workflow_mode: "full"  # or "story-only"
  max_parallel_stories: 3
  parallel_strategy: "asyncio" # or "agent-teams"
```

See [Configuration Guide](docs/CONFIGURATION.md) for all options.

---

## Epic Orchestration

Execute multi-story epics with dependency resolution:

```bash
# In Cursor
@simple-mode *epic docs/prd/epic-51-feature.md

# CLI
tapps-agents epic status --all
tapps-agents epic approve <story-id>
```

Features: parallel wave execution, story dependency ordering, state persistence, handoff artifacts.

---

## Documentation

### Getting Started
- [Quick Start Guide](docs/guides/QUICK_START.md)
- [Simple Mode Guide](docs/SIMPLE_MODE_GUIDE.md)
- [Cursor Skills Installation](docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md)
- [Configuration Guide](docs/CONFIGURATION.md)

### Architecture
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Architecture Decisions (ADRs)](docs/architecture/decisions/)
- [Source Tree](docs/architecture/source-tree.md)
- [Tech Stack](docs/architecture/tech-stack.md)

### Integration
- [Multi-Tool Integration](docs/tool-integrations.md) (Cursor, Claude Code, VS Code, Codespaces)
- [Custom Skills Guide](docs/CUSTOM_SKILLS_GUIDE.md)
- [Epic Workflow Guide](docs/EPIC_WORKFLOW_GUIDE.md)
- [Hooks Guide](docs/HOOKS_GUIDE.md)
- [Task Management](docs/TASK_MANAGEMENT_GUIDE.md)

### Operations
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Deployment Guide](docs/operations/DEPLOYMENT.md)
- [Release Guide](docs/operations/RELEASE_GUIDE.md)
- [Test Suite](tests/README.md)

### All Documentation
- [Documentation Index](docs/README.md)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Framework Development

When modifying `tapps_agents/`, use the Full SDLC workflow:

```bash
tapps-agents simple-mode full --prompt "Implement [description]" --auto
```

### Version Management

```powershell
.\scripts\update_version.ps1 -Version 3.6.2
```

Updates version across pyproject.toml, __init__.py, README, docs, and metadata.

---

## Platform Support

- **Windows** (primary), **Linux**, **macOS**
- UTF-8 encoding throughout (Windows CP1252 fallback handled)
- See [Troubleshooting](docs/TROUBLESHOOTING.md) for platform-specific issues

---

## License

[MIT](LICENSE)
