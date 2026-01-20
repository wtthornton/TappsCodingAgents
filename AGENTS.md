---
title: Agent Identity and Project Rules
version: 1.0.0
status: active
last_updated: 2026-01-20
tags: [agents, ai-assistance, cursor, claude]
---

# Agent Identity and Project Rules

This document defines the agent identity and project-specific rules for AI assistants working on TappsCodingAgents.

## Agent Identity

**Project:** TappsCodingAgents  
**Type:** Software Development Framework  
**Primary Purpose:** Provide a comprehensive SDLC agent framework with Cursor AI integration

**You are an AI assistant helping develop TappsCodingAgents**, a framework that provides:
- 14 workflow agents covering the complete software development lifecycle
- Expert system with built-in technical domains and optional project-defined business experts
- Cursor Skills integration (model-agnostic)
- Code quality analysis tools
- Workflow orchestration with CLI and Python API

## Project-Specific Rules

### ⚠️ CRITICAL: Default to @simple-mode

**For ALL development tasks, DEFAULT to using `@simple-mode` unless the user explicitly requests a specific agent.**

**Why?** Simple Mode provides:
- Automatic orchestration of multiple specialized skills
- Quality gates with automatic loopbacks
- Comprehensive test generation (80%+ coverage)
- Full documentation artifacts
- Better outcomes than direct implementation

**Default Commands:**

| User Request | Default Response |
|-------------|------------------|
| "Add/implement/create a feature" | `@simple-mode *build "description"` |
| "Fix this bug/error" | `@simple-mode *fix <file> "description"` |
| "Review this code" | `@simple-mode *review <file>` |
| "Add tests" | `@simple-mode *test <file>` |
| "Refactor this code" | `@simple-mode *refactor <file>` |
| "Score this file" (quick check) | `@reviewer *score <file>` (exception: simple operation) |

**Example:**
```
User: "Add user authentication to my app"

✅ CORRECT: "I'll use the Simple Mode build workflow:
@simple-mode *build 'Add user authentication with login, logout, and session management'"

❌ WRONG: "I'll implement this directly..." [starts editing files without workflow]
```

### Dual Nature of This Project

**This project has TWO distinct roles:**

#### 1. Framework Development (Primary Role)

**When working on framework development:**
- You're modifying the framework code itself (`tapps_agents/` package)
- You're adding new agents, features, or capabilities
- You're fixing bugs or improving the framework
- Focus on: `tapps_agents/`, `tests/`, `requirements/`, `docs/`

**⚠️ CRITICAL: Framework Changes MUST Use Full SDLC Workflow**

When modifying the TappsCodingAgents framework itself, you **MUST** use Simple Mode Full SDLC workflow:

```bash
# CLI
tapps-agents simple-mode full --prompt "Implement [enhancement description]" --auto

# Or in Cursor chat
@simple-mode *full "Implement [enhancement description]"
```

**Why?** The full SDLC workflow ensures:
- ✅ Proper requirements analysis (analyst)
- ✅ Architecture design (architect)
- ✅ Quality gates with automatic loopbacks (reviewer)
- ✅ Test generation and execution (tester)
- ✅ Security validation (ops)
- ✅ Complete documentation (documenter)
- ✅ Full traceability (requirements → stories → architecture → implementation)

**DO NOT:**
- ❌ Directly implement code without using the workflow
- ❌ Skip planning, design, or architecture phases
- ❌ Validate only afterward (use quality gates during development)
- ❌ Skip test generation (tests should be part of workflow)

#### 2. Self-Hosting (Secondary Role)

**TappsCodingAgents uses its own framework** for its own development:
- Configuration: `.tapps-agents/` directory
- Industry Experts configured
- Context7 integration for library documentation
- Workflow presets for common tasks

**When working on self-hosted development:**
- You're using the framework to develop the framework itself
- You're using agents via CLI or Python API
- You're configuring experts and knowledge bases
- Focus on: `.tapps-agents/`, `workflows/`, project-specific tasks

### Context Awareness

**When AI assistants work in this project, they should:**

1. **Understand the dual context:**
   - Framework code (`tapps_agents/`) = developing the framework
   - Project configuration (`.tapps-agents/`) = using the framework

2. **Distinguish between:**
   - **Framework users**: People who install and use TappsCodingAgents in their projects
   - **Framework developers**: People working on TappsCodingAgents itself (us)

3. **Documentation clarity:**
   - User-facing docs should focus on "how to use the framework"
   - Developer docs should focus on "how the framework works"

## Agent Capabilities Overview

TappsCodingAgents provides **14 specialized workflow agents**:

### Planning Agents
- **analyst**: Requirements gathering, analysis, project understanding
- **planner**: User story creation, development planning

### Design Agents
- **architect**: System architecture design, architecture pattern detection (*detect-patterns)
- **designer**: API and data model design

### Development Agents
- **implementer**: Code generation and refactoring
- **debugger**: Error analysis and debugging
- **documenter**: Documentation generation

### Testing Agent
- **tester**: Test generation and execution

### Quality Agents
- **reviewer**: Code quality review with 7-category scoring (complexity, security, maintainability, test_coverage, performance, structure, devex)
- **improver**: Code improvement suggestions
- **evaluator**: Framework effectiveness evaluation

### Operations Agent
- **ops**: Security scanning, compliance checking, deployment planning

### Orchestration Agent
- **orchestrator**: YAML workflow coordination

### Enhancement Agent
- **enhancer**: Prompt enhancement (7-stage pipeline). Workflow integration: full-sdlc (optional enhance before requirements), rapid-dev, and Epic story workflows run enhancer steps via **EnhancerHandler** when an `enhance` step is present. CLI auto-enhancement for implementer, planner, analyst: `auto_enhancement` in [CONFIGURATION.md](docs/CONFIGURATION.md#automatic-prompt-enhancement-auto_enhancement); `PROMPT_ARGUMENT_MAP` and `commands` control eligibility.

**For detailed agent capabilities, see:** `.cursor/rules/agent-capabilities.mdc`

## Simple Mode (Primary Interface)

**Simple Mode** is the primary user interface for TappsCodingAgents in Cursor. It provides natural language commands that automatically orchestrate multiple specialized skills.

### Simple Mode Commands

```cursor
@simple-mode *build "description"     # 7-step feature workflow (RECOMMENDED)
@simple-mode *review <file>             # Code quality review
@simple-mode *fix <file> "error"       # Bug fixing workflow
@simple-mode *test <file>              # Test generation
@simple-mode *refactor <file>          # Refactoring workflow
@simple-mode *full "description"       # Full 9-step SDLC (for framework development)
@simple-mode *epic <epic-doc.md>       # Execute Epic documents
@simple-mode *enhance "prompt"         # Prompt enhancement (EnhancerAgent)
@simple-mode *breakdown "prompt"       # Task breakdown (PlannerAgent)
@simple-mode *todo <bd args>           # Beads-backed todo (e.g. *todo ready, *todo create "Title")
```

**Human oversight (plan 2.3):** For `*build` and `*full`, when `human_oversight.branch_for_agent_changes` is true (default), work runs on a branch `tapps-agents/build-{workflow_id}`; merge to main only after human review. Optional step checkpoints (`checkpoints_before_steps`, e.g. `["implementer","designer"]`) prompt before running those steps unless `--auto`.

**For complete Simple Mode documentation, see:** `.cursor/rules/simple-mode.mdc`

## Individual Agent Commands (Advanced)

Use these only for targeted, single-purpose operations:

### Code Review
```cursor
@reviewer *review {file}
@reviewer *score {file}
@reviewer *lint {file}
@reviewer *type-check {file}
@reviewer *security-scan {file}
@reviewer *docs {library} [topic]
```

### Code Generation
```cursor
@implementer *implement "description" {file}
@implementer *refactor {file} "instructions"
@implementer *docs {library} [topic]
```

### Testing
```cursor
@tester *test {file}
@tester *generate-tests {file}
@tester *run-tests
```

**For complete command reference, see:** `.cursor/rules/command-reference.mdc`

### Beads (bd) – Task Tracking

Use **bd** for dependency-aware task tracking and agent memory. On this project the binary is at `tools\bd\bd.exe` (Windows); add `tools\bd` to PATH to run `bd` directly.

**Essential commands:** `bd ready` (tasks with no open blockers), `bd create "Title" -p 0`, `bd dep add <child> <parent>`, `bd show <id>`. Run `bd quickstart` for an intro. This repo uses stealth mode (`.beads/` is local only).

**Create/close bd issues:** When the relevant `beads.*` flags are on, the following create and close bd issues automatically: *build, *fix (via `hooks_simple_mode`); *epic (`sync_epic` + per-story close + optional Epic parent); *review, *test, *refactor (when `hooks_review`, `hooks_test`, `hooks_refactor` are enabled); continuous-bug-fix and @bug-fix-agent \*fix-bug (they use FixOrchestrator); and CLI `workflow` (when `hooks_workflow` is true). See [docs/BEADS_INTEGRATION.md](docs/BEADS_INTEGRATION.md).

**Conventions:** Run `bd ready` at session start when doing long-horizon or multi-session work. After completing a *build, *fix, or an epic story, create or close a bd issue when hooks are enabled, or manually (e.g. `bd create "Done: …"` or `bd close <id>`).

**Init and doctor:** `tapps-agents init` prints a hint to run `bd init` or `bd init --stealth` when bd is available and `.beads` is missing, or "Beads is ready. Use `bd ready` to see unblocked tasks." when `.beads` exists. `tapps-agents doctor` reports Beads (bd) status and config (enabled, sync_epic, hooks_*).

## Detailed Rules

**For detailed project rules and guidelines, see:**

- **`.cursor/rules/simple-mode.mdc`** - Simple Mode usage and workflow enforcement
- **`.cursor/rules/agent-capabilities.mdc`** - Complete agent capabilities guide
- **`.cursor/rules/project-context.mdc`** - Dual nature context and framework development rules
- **`.cursor/rules/command-reference.mdc`** - Complete command reference
- **`.cursor/rules/workflow-presets.mdc`** - Workflow preset documentation
- **`.cursor/rules/quick-reference.mdc`** - Quick command reference

## Cross-Tool Compatibility

**This document is compatible with:**
- **Cursor IDE** (primary): Uses Cursor Skills (`.claude/skills/`) and Rules (`.cursor/rules/`)
- **Claude Desktop**: Can use `CLAUDE.md` (see `CLAUDE.md` for Claude-specific rules)
- **Other AI tools**: Rules in `.cursor/rules/` are tool-agnostic markdown files

**For Claude Desktop compatibility, see:** `CLAUDE.md`

## Configuration

**Skills:** `.claude/skills/` (14 agent skills + simple-mode)  
**Rules:** `.cursor/rules/` (8 rule files)  
**Background Agents:** `.cursor/background-agents.yaml`  
**Indexing:** `.cursorignore` (performance optimization)

## Getting Started

1. Skills are already installed in `.claude/skills/`
2. Try: `@reviewer *help` in Cursor chat
3. Try: `@simple-mode *build "description"` for feature development
4. Try: `@simple-mode *review <file>` for code quality review

**For full setup instructions, see:** `docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md`

## Version Management

**Always use the automated version update script** when changing versions:

```powershell
.\scripts\update_version.ps1 -Version 3.0.4
```

This script updates version numbers in:
- Core files: `pyproject.toml`, `tapps_agents/__init__.py`
- Documentation: `README.md`, `docs/README.md`, `docs/API.md`, `docs/ARCHITECTURE.md`
- Metadata: `docs/implementation/IMPROVEMENT_PLAN.json`

**After updating version:**
1. Update `CHANGELOG.md` with release notes
2. Commit changes
3. Create and push git tag
4. See `docs/operations/RELEASE_GUIDE.md` for complete process

---

**Last Updated:** 2026-01-20  
**Maintained By:** TappsCodingAgents Team
