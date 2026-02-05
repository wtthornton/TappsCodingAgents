---
title: Claude Code Master Rules
version: 1.0.0
status: active
last_updated: 2026-01-20
tags: [claude, rules, ai-assistance]
---

# Claude Code Master Rules

This file serves as the master rule file for Claude Code and other AI coding tools. It references detailed rules in `.cursor/rules/` to avoid duplication while providing Claude Code-specific context.

## Project Overview

**TappsCodingAgents** is a software development framework that provides:
- 14 workflow agents covering the complete software development lifecycle
- Expert system with built-in technical domains and optional project-defined business experts
- **Adaptive Learning System** that auto-generates experts, adjusts scoring weights, and improves expert voting for first-pass code correctness
- Cursor Skills integration (model-agnostic)
- Code quality analysis tools
- Workflow orchestration with CLI and Python API

## Quick Start

**For AI assistants working on this project:**

1. **Default to @simple-mode** for all development tasks
2. **Understand dual nature**: Framework development vs. self-hosting
3. **Follow workflow enforcement**: Use workflows for feature development, bug fixes, reviews
4. **Respect quality gates**: Tests, reviews, and documentation are mandatory

## ⚠️ CRITICAL: Workflow Enforcement for Claude Code CLI

**If you are Claude Code CLI (not Cursor IDE), you MUST use tapps-agents CLI for framework development:**

### When to Use tapps-agents CLI

| Code Location | Requirement | Command |
|---------------|-------------|---------|
| **`tapps_agents/` package** | **MANDATORY** | `tapps-agents simple-mode full --prompt "..." --auto` |
| **Framework tests** | **MANDATORY** | `tapps-agents simple-mode test --file <path>` |
| **Framework docs** | **MANDATORY** | `tapps-agents simple-mode review --file <path>` |
| **User project code** | Recommended | `tapps-agents simple-mode build --prompt "..."` |

### Why This Matters

**Framework development REQUIRES workflows because:**
1. ✅ **Dogfooding** - Framework must develop itself
2. ✅ **Quality Gates** - Automatic review, scoring (≥75), loopback
3. ✅ **Validation** - Proves workflows work in production
4. ✅ **Traceability** - Complete artifacts (plan, design, review)
5. ✅ **Best Practices** - Follows our own documented patterns

### Pre-Edit Checklist (MANDATORY)

**Before ANY direct file edits, check:**

- [ ] **Is this framework code?** (`tapps_agents/` package)
  - ✅ YES → STOP. Use `tapps-agents simple-mode full --prompt "..." --auto`
  - ❌ NO → Continue with checklist

- [ ] **Is this a feature/bug fix?**
  - Consider: `tapps-agents simple-mode build --prompt "..."`
  - Benefits: Tests, quality gates, documentation

- [ ] **Is this a review task?**
  - Use: `tapps-agents reviewer review --file <path> --score`

**Direct edits are ONLY acceptable for:**
- Documentation typos
- Simple configuration changes
- User explicitly requests direct edit after workflow suggestion

## Detailed Rules

This file references detailed rules in `.cursor/rules/` to keep the master file lean while providing comprehensive guidance.

### Core Rules

**`.cursor/rules/simple-mode.mdc`** - **CRITICAL: READ FIRST**
- Default to @simple-mode for ALL development tasks
- Workflow interceptor pattern (suggest workflows before direct edits)
- Complete workflow execution (all steps, documentation artifacts)
- Natural language intent detection

**`.cursor/rules/project-context.mdc`**
- Dual nature of project (framework development + self-hosting)
- Framework changes MUST use Full SDLC workflow
- Context awareness guidelines
- Self-hosting configuration
- **Feedback on tapps-agents:** When asked for feedback on how well tapps-agents helps (e.g. as an LLM), include health metrics in the report: run `tapps-agents health overview` and include the output or summary.

**`.cursor/rules/agent-capabilities.mdc`**
- Complete guide to all 14 workflow agents
- When to use each agent
- Common usage patterns
- Command reference

**`.cursor/rules/command-reference.mdc`**
- Complete command reference for all agents
- CLI and Cursor Skills syntax
- Parameter guides
- Examples and use cases

### Quick References

**`.cursor/rules/quick-reference.mdc`**
- Quick command reference
- Common workflows
- Default behaviors

**`.cursor/rules/workflow-presets.mdc`**
- Workflow preset documentation
- Available presets (full, rapid, fix, quality, etc.)
- When to use each preset

**`.cursor/rules/cursor-mode-usage.mdc`**
- Cursor mode vs CLI mode
- When to use Cursor Skills vs CLI commands
- Command mapping

**`.cursor/rules/project-profiling.mdc`**
- Automatic project profiling system
- Context-aware recommendations
- Tech stack detection

## Claude Code-Specific Context

### File Organization

**Rules Location:** `.cursor/rules/*.mdc`
- Markdown files with YAML frontmatter
- Tool-agnostic format (works with Cursor, Claude Code, and other tools)
- Organized by topic for easy navigation

**Skills Location:** `.claude/skills/`
- Cursor Skills definitions (YAML + markdown)
- 14 agent skills + simple-mode skill
- Model-agnostic (uses Cursor's configured LLM)

### Cross-Tool Compatibility

**This project is designed to work with:**
- **Cursor IDE** (primary): Uses Cursor Skills and Rules
- **Claude Desktop**: Can use this `CLAUDE.md` file
- **Other AI tools**: Rules in `.cursor/rules/` are tool-agnostic

**Key Principle:** Rules are stored in `.cursor/rules/` as markdown files. This `CLAUDE.md` file provides a master index and Claude Code-specific context without duplicating content.

### Local overrides

You can add `CLAUDE.local.md` for machine- or project-specific rules. It is loaded together with this file when **"Include CLAUDE.md in context"** is enabled. Copy from `CLAUDE.local.example.md`; `CLAUDE.local.md` is in `.gitignore`.

### Version and Status

**Version:** 3.5.39
**Status:** Active
**Last Updated:** 2026-01-30

**Important:** Beads integration is **MANDATORY** for TappsCodingAgents development. See `docs/BEADS_GITHUB_BEST_PRACTICES.md` for complete workflow guide.

**Related Files:**
- `AGENTS.md` - Agent identity and project-specific rules
- `docs/test-stack.md` - Testing strategy and infrastructure
- `docs/ARCHITECTURE.md` - System architecture overview
- `docs/BEADS_GITHUB_BEST_PRACTICES.md` - **Mandatory** Beads + GitHub workflow guide

## Essential Guidelines

### 1. Default to @simple-mode

**For ALL development tasks, DEFAULT to using `@simple-mode` unless the user explicitly requests a specific agent.**

**Why?** Simple Mode provides:
- Automatic orchestration of multiple specialized skills
- Quality gates with automatic loopbacks
- Comprehensive test generation (80%+ coverage)
- Full documentation artifacts
- Better outcomes than direct implementation
- **Adaptive learning** that improves with each use (auto-generates experts, adjusts scoring)

### 1.5 Adaptive Learning System

**TappsCodingAgents continuously learns and improves from usage:**
- **Auto-Generates Experts**: New experts are automatically created when domains are detected in prompts or code
- **Adaptive Scoring**: Scoring weights adjust based on outcome analysis to maximize first-pass code correctness
- **Expert Voting Improvement**: Expert voting weights adapt based on performance tracking
- **First-Pass Optimization**: System predicts and optimizes for code correctness on the first attempt
- **Knowledge Enhancement**: Expert knowledge bases are automatically enhanced based on usage patterns

**Goal**: Write code fast and correct the first time, beating other LLMs (Cursor, Claude, etc.) through continuous learning.

**Example:**
```
User: "Add user authentication to my app"

✅ CORRECT: @simple-mode *build 'Add user authentication with login, logout, and session management'
❌ WRONG: Directly implement without workflow
```

### 2. Framework Development Rules

**When modifying the TappsCodingAgents framework itself (`tapps_agents/` package), you MUST use Full SDLC workflow:**

```bash
# CLI
tapps-agents simple-mode full --prompt "Implement [enhancement description]" --auto

# Or in Cursor chat
@simple-mode *full "Implement [enhancement description]"
```

**Why?** Framework changes require:
- Requirements analysis before implementation
- Architecture design for integration patterns
- Quality gates (≥75 score) with automatic loopbacks
- Test generation and execution
- Security validation
- Complete documentation
- Full traceability

### 3. Workflow Enforcement

**BEFORE making any code edits for feature implementation, bug fixes, or new functionality, you MUST:**

1. **Suggest Simple Mode workflow FIRST** - Do not proceed with direct edits
2. **Explain workflow benefits** - Tests, quality gates, documentation
3. **Only proceed with direct edits if user explicitly overrides** - Get confirmation first

**Pre-Edit Checklist:**
- [ ] Is this a new feature/component? → Use `@simple-mode *build`
- [ ] Is this a bug fix? → Use `@simple-mode *fix`
- [ ] Is this code review? → Use `@simple-mode *review`
- [ ] Is this test generation? → Use `@simple-mode *test`
- [ ] **Only skip if:** Simple one-off operation OR user explicitly requests direct edit

### 4. Quality Gates

**All code changes must meet quality thresholds:**
- **Overall Score:** ≥ 70 (fail if below)
- **Security Score:** ≥ 6.5 (warn if below)
- **Maintainability Score:** ≥ 7.0 (warn if below)
- **Test Coverage:** ≥ 75% (enforced in pytest.ini)

**Framework Development Quality Gates:**
- **Overall Score:** ≥ 75 (higher threshold for framework code)
- **Security Score:** ≥ 8.5 (critical for framework security)
- **Test Coverage:** ≥ 80% for core modules

## Adaptive Workflow Checkpoints (v3.5.37+)

**All workflows now include adaptive checkpoints that optimize execution based on task complexity and quality.**

### How Checkpoints Work

**3 Strategic Checkpoints:**

1. **After Enhance** (Checkpoint 1)
   - Early mismatch detection using prompt analysis
   - Switches workflows before expensive Planning step
   - **Confidence:** 70% (lower for early detection)
   - **Example:** "*full" workflow for simple bug fix → switches to "*fix"
   - **Saves:** Up to 40K tokens by switching early

2. **After Planning** (Checkpoint 2)
   - Comprehensive analysis using story points, files affected, complexity
   - Detects when workflow is overkill for task complexity
   - **Confidence:** 85% (high from planning data)
   - **Example:** "*full" for 8-point task affecting 3 files → switches to "*build"
   - **Saves:** 20K-40K tokens

3. **After Test** (Checkpoint 3)
   - Quality-based early termination
   - Skips optional steps (security, docs) when quality is excellent
   - **Confidence:** 90% (very high from quality metrics)
   - **Example:** Code scores 85/100 → skips security scan and docs
   - **Saves:** 12K-13K tokens

### Checkpoint Decision Criteria

**Checkpoint 1 (After Enhance):**
- Bug fix keywords + low complexity → recommend `*fix`
- Simple task (< 30 words, simple keywords) → recommend `*build`
- Complex task indicators → continue with `*full`

**Checkpoint 2 (After Planning):**
- Story points ≤ 5 + files ≤ 3 → recommend `*fix`
- Story points 8-13 + low scope → recommend `*build`
- Story points > 13 OR high scope → continue with `*full`

**Checkpoint 3 (Quality Gate):**
- Quality score ≥ 80 → skip security AND docs
- Quality score 75-79 → skip docs only
- Quality score < 75 → complete all remaining steps

### Configuration

**Enabled by default** - Disable with:

```bash
# CLI
tapps-agents simple-mode build --prompt "..." --no-auto-checkpoint

# Config (.tapps-agents/config.yaml)
simple_mode:
  enable_checkpoints: false
  checkpoint_confidence_threshold: 0.70
```

**Debug mode:**
```bash
tapps-agents simple-mode build --prompt "..." --checkpoint-debug
```

**See:** [Checkpoint System Guide](docs/CHECKPOINT_SYSTEM_GUIDE.md) for complete documentation

---

## Workflow Presets - Choose the Right Level

**TappsCodingAgents provides 4 workflow presets to match task complexity. Using the right preset saves time and tokens!**

**Note:** With checkpoints enabled (default), workflows automatically adapt - you may get fewer steps than listed if task is simpler than expected.

### ⚡ Minimal (2 steps, ~5 min, ~15K tokens)

**Best for:** Simple fixes, typos, documentation updates

```bash
@simple-mode *fix "description" --preset minimal
tapps-agents simple-mode fix --prompt "description" --preset minimal
```

**Steps:** Implement → Test
**Use when:** Clear requirements, low risk, quick change

**Examples:**
- Fix typo in docstring
- Add logging statement
- Update configuration value
- Simple bug fix with obvious solution

---

### ⚙️ Standard (4 steps, ~15 min, ~30K tokens) **[DEFAULT]**

**Best for:** Regular features, bug fixes, refactoring

```bash
@simple-mode *build "description"  # Default preset
tapps-agents simple-mode build --prompt "description"
```

**Steps:** Plan → Implement → Review → Test
**Use when:** Most development tasks, typical features

**Examples:**
- Add new API endpoint
- Implement validation logic
- Refactor existing function
- Add new feature with tests

---

### 🎯 Comprehensive (7 steps, ~45 min, ~60K tokens)

**Best for:** Complex features, API changes, security-sensitive code

```bash
@simple-mode *build "description" --preset comprehensive
tapps-agents simple-mode build --prompt "description" --preset comprehensive
```

**Steps:** Enhance → Analyze → Plan → Design → Implement → Review → Test
**Use when:** High complexity, multiple stakeholders, critical functionality

**Examples:**
- New authentication system
- Database schema changes
- Public API design
- Multi-component features

---

### 🏗️ Full SDLC (9 steps, ~2 hours, ~80K tokens)

**Best for:** Framework development, major architectural changes

```bash
@simple-mode *full "description"
tapps-agents simple-mode full --prompt "description" --auto
```

**Steps:** Full Comprehensive + Architecture + Security + Documentation
**Use when:** Modifying `tapps_agents/` package, breaking changes, framework development

**Examples:**
- Add new agent to framework
- Modify workflow engine
- Security-critical framework changes
- Major architectural refactoring

---

### Preset Selection Guide

| Task Type | Estimated Complexity | Preset | Why |
|-----------|---------------------|--------|-----|
| Fix typo | Very Low | **minimal** | No planning needed |
| Add logging | Low | **minimal** | Simple, low risk |
| Add validation | Low-Medium | **standard** | Needs review & tests |
| New API endpoint | Medium | **standard** | Standard feature |
| Auth system | Medium-High | **comprehensive** | Security-sensitive, design needed |
| Refactor auth | High | **comprehensive** | High impact, multiple components |
| Framework changes | Very High | **full-sdlc** | **MANDATORY** for `tapps_agents/` |

**💡 Tip:** Not sure which preset? Use **standard** (default) for most tasks. The system will warn if a different preset is more appropriate.

---

## Project Initialization

**For users setting up a new project with TappsCodingAgents:**

### First-Time Setup

```bash
# Navigate to your project directory
cd /path/to/your/project

# Initialize TappsCodingAgents (auto-detects tech stack, populates cache, generates experts)
tapps-agents init --auto-experts

# Or with hooks templates
tapps-agents init --hooks
```

### What `init` Does Automatically (Phases 1-3)

The init process now includes automatic configuration:

1. **✅ Configuration Validation** (Phase 1)
   - Validates `.tapps-agents/` structure
   - Auto-creates missing directories
   - Checks YAML syntax and required fields

2. **✅ Tech Stack Detection** (Phase 1)
   - Scans project files (requirements.txt, package.json, etc.)
   - Detects languages, frameworks, libraries
   - Generates `.tapps-agents/tech-stack.yaml`

3. **✅ Context7 Cache Population** (Phase 2)
   - Reads libraries from tech-stack.yaml
   - Pre-populates documentation cache
   - Async concurrent fetching (5 max concurrent)

4. **✅ Expert Auto-Generation** (Phase 3)
   - Scans `.tapps-agents/knowledge/` for markdown files
   - Generates experts following `expert-{domain}-{topic}` convention
   - Adds to `experts.yaml` with priority 0.70-0.90

### Upgrade Existing Installation

```bash
# Reset framework files to latest version (preserves custom files)
tapps-agents init --reset

# Reset and also update MCP config
tapps-agents init --reset --reset-mcp
```

### Manual Expert Generation

```bash
# Generate experts from knowledge base
python -m tapps_agents.core.generators.expert_generator --auto

# Force regeneration even if experts exist
python -m tapps_agents.core.generators.expert_generator --auto --force
```

### Validation

```bash
# Validate project configuration
python -m tapps_agents.core.validators.config_validator --auto-fix

# Check setup health
tapps-agents health overview
```

## Common Commands

### Simple Mode (Primary Interface)

```cursor
@simple-mode *build "description"     # 7-step feature workflow
@simple-mode *review <file>           # Code quality review
@simple-mode *fix <file> "error"     # Bug fixing workflow
@simple-mode *test <file>            # Test generation
@simple-mode *refactor <file>       # Refactoring workflow
@simple-mode *enhance "prompt"       # Prompt enhancement
@simple-mode *breakdown "prompt"     # Task breakdown
@simple-mode *todo <bd args>         # Beads todo (e.g. ready, create "Title")
@simple-mode *full "description"      # Full 9-step SDLC (framework development)
```

### Individual Agents (Advanced)

```cursor
@reviewer *review <file>              # Comprehensive code review
@reviewer *score <file>               # Quick quality scoring
@implementer *implement "desc" <file> # Code generation
@tester *test <file>                  # Test generation
@debugger *debug "error" --file <file> # Error analysis
```

**For complete command reference, see:** `.cursor/rules/command-reference.mdc`

### Hooks and task management

- **Hooks** (opt-in): Configure `.tapps-agents/hooks.yaml` to run shell commands at UserPromptSubmit, PostToolUse, SessionStart, SessionEnd, and WorkflowComplete. Use `tapps-agents init --hooks` to create a template. See [docs/HOOKS_GUIDE.md](docs/HOOKS_GUIDE.md).
- **Task management**: Task specs in `.tapps-agents/task-specs/`; CLI: `tapps-agents task create <id> --title "..."`, `task list`, `task show <id>`, `task update <id> --status in-progress`, `task close <id>`, `task hydrate`, `task dehydrate`, `task run <id>`. See [docs/TASK_MANAGEMENT_GUIDE.md](docs/TASK_MANAGEMENT_GUIDE.md).

## Documentation

**Key Documentation Files:**
- `AGENTS.md` - Agent identity and project-specific rules
- `docs/test-stack.md` - Testing strategy and infrastructure
- `docs/ARCHITECTURE.md` - System architecture overview
- `docs/README.md` - Documentation index (and where to place new docs: canonical vs [docs/archive/](docs/archive/README.md))
- `docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md` - Skills setup guide
- `docs/HOOKS_GUIDE.md` - Hooks (events, config, env vars, templates)
- `docs/TASK_MANAGEMENT_GUIDE.md` - Task specs, hydration, task CLI

**Expert System & Knowledge Base:**
- `docs/expert-priority-guide.md` - Expert priority configuration guidelines
- `docs/knowledge-base-guide.md` - Knowledge base organization for RAG optimization
- `docs/CONFIGURATION.md` - Complete configuration reference

**Tool Integration:**
- `docs/tool-integrations.md` - Using TappsCodingAgents with Cursor, Claude Code CLI, VS Code, etc.

**For complete documentation, see:** `docs/README.md`

## Configuration

**Skills:** `.claude/skills/` (14 agent skills + simple-mode)  
**Rules:** `.cursor/rules/` (8 rule files)  
**Background Agents:** `.cursor/background-agents.yaml`  
**Indexing:** `.cursorignore` (performance optimization)  
**auto_enhancement and PROMPT_ARGUMENT_MAP:** [docs/CONFIGURATION.md](docs/CONFIGURATION.md#automatic-prompt-enhancement-auto_enhancement) — CLI prompt enhancement; workflow EnhancerHandler for full-sdlc (optional enhance), rapid-dev, Epic.

## Getting Started

1. **Read this file** for essential guidelines
2. **Review `.cursor/rules/simple-mode.mdc`** for workflow enforcement
3. **Review `.cursor/rules/project-context.mdc`** for dual nature context
4. **Try commands:** `@simple-mode *build "description"` or `@reviewer *help`

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
4. Build packages: `python -m build`
5. Publish to PyPI (see PyPI Credentials below)
6. See `docs/operations/RELEASE_GUIDE.md` for complete process

### PyPI Credentials

**PyPI Token Location:** `.env` file (git-ignored)

The PyPI API token for publishing packages is stored in the `.env` file:

```bash
# PyPI / Twine (for publishing to PyPI)
TWINE_PASSWORD=pypi-AgEIcHlwaS5vcmcC...
```

**To publish to PyPI:**

```bash
# Load environment variables from .env
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=$(grep TWINE_PASSWORD .env | cut -d '=' -f2)

# Upload to PyPI
python -m twine upload dist/tapps_agents-<version>*
```

**Security Notes:**
- `.env` file is in `.gitignore` - NEVER commit it
- Token is project-specific and should be regenerated if compromised
- Token has write access to `tapps-agents` package on PyPI
- For CI/CD, use GitHub Secrets instead of `.env` file

**Obtaining a new token:**
1. Log in to [pypi.org](https://pypi.org)
2. Go to Account Settings → API tokens
3. Create token with scope limited to `tapps-agents` project
4. Copy token to `.env` file as `TWINE_PASSWORD`

---

**Last Updated:** 2026-01-20  
**Maintained By:** TappsCodingAgents Team  
**Compatible With:** Claude Code, Cursor IDE, and other AI coding tools
