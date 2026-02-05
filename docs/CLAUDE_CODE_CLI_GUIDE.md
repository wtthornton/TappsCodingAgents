# Claude Code CLI Integration Guide

**Version:** 1.0.0
**Last Updated:** 2026-02-05
**Status:** Active

## Overview

This guide explains how to use TappsCodingAgents from **Claude Code CLI** (not Cursor IDE). The CLI provides the same workflow orchestration and quality gates as Cursor Skills, but through command-line interface.

## Quick Reference

| Task | Command |
|------|---------|
| **Framework Development** | `tapps-agents simple-mode full --prompt "..." --auto` |
| **Feature Development** | `tapps-agents simple-mode build --prompt "..."` |
| **Bug Fixes** | `tapps-agents simple-mode fix --file <path> --description "..."` |
| **Code Review** | `tapps-agents reviewer review --file <path> --score` |
| **Test Generation** | `tapps-agents tester test --file <path>` |
| **Project Init** | `tapps-agents init --auto-experts` |

## Environment Differences

### Cursor IDE vs Claude Code CLI

| Feature | Cursor IDE | Claude Code CLI |
|---------|------------|-----------------|
| **Skill Invocation** | `@simple-mode *build` | `tapps-agents simple-mode build` |
| **Agent Calls** | `@reviewer *review <file>` | `tapps-agents reviewer review --file <path>` |
| **Interactive** | Yes (chat interface) | No (command line) |
| **Auto Mode** | Optional | Recommended (`--auto` flag) |
| **Background Execution** | Yes | No (unless using `&` or nohup) |

## Critical Rules for Claude Code CLI

### Rule 1: ALWAYS Use Workflows for Framework Code

**Framework code** = any file in `tapps_agents/` package

```bash
# ✅ CORRECT: Use Full SDLC workflow
tapps-agents simple-mode full \
  --prompt "Implement Phase 3.2: Expert-Knowledge Linker..." \
  --auto

# ❌ WRONG: Direct file editing
claude-code "Edit tapps_agents/core/generators/expert_linker.py"
```

**Why?**
- **Dogfooding** - Framework must develop itself
- **Quality Gates** - Automatic review, scoring (≥75 required)
- **Traceability** - Complete artifacts (plan, design, review)
- **Validation** - Proves workflows work

### Rule 2: Prefer Workflows for User Project Code

For regular project code (not framework), workflows are **recommended** but not mandatory:

```bash
# ✅ RECOMMENDED: Use build workflow
tapps-agents simple-mode build \
  --prompt "Add user authentication with JWT tokens"

# ⚠️ ACCEPTABLE: Direct implementation (if user requests)
# But explain workflow benefits first
```

**Workflow Benefits:**
- Automatic test generation (≥80% coverage)
- Quality scoring (≥70 required)
- Documentation artifacts
- Security validation
- Loopback if quality is low

### Rule 3: Use `--auto` Flag for Non-Interactive Execution

Claude Code CLI cannot interact with confirmation prompts, so always use `--auto`:

```bash
# ✅ CORRECT: Auto mode
tapps-agents simple-mode build --prompt "..." --auto

# ❌ WRONG: Will hang waiting for input
tapps-agents simple-mode build --prompt "..."
```

## Common Workflows

### 1. Feature Development

```bash
# Step 1: Enhance prompt (optional but recommended)
tapps-agents enhancer enhance \
  --prompt "Add user authentication" \
  --output enhanced.md

# Step 2: Build feature (full 7-step workflow)
tapps-agents simple-mode build \
  --prompt "$(cat enhanced.md)" \
  --auto

# Alternative: One-step build (no enhancement)
tapps-agents simple-mode build \
  --prompt "Add user authentication with login, logout, session management" \
  --auto
```

**Steps Executed:**
1. Enhance → Plan → Design → Implement → Review → Test → (Complete)

**Quality Gates:**
- Review score ≥ 70 (configurable)
- Test coverage ≥ 80%
- Loopback if gates fail

### 2. Framework Development (tapps_agents/ package)

```bash
# REQUIRED: Use Full SDLC workflow
tapps-agents simple-mode full \
  --prompt "Implement Phase 3.2: Expert-Knowledge Linker. Link knowledge files to appropriate experts, find orphan files, suggest knowledge_files additions. Target: ≥90% test coverage." \
  --auto
```

**Steps Executed:**
1. Enhance → Analyze → Plan → Architect → Design → Implement → Review → Test → Security → Docs

**Quality Gates:**
- Overall score ≥ 75 (higher for framework)
- Security score ≥ 8.5
- Test coverage ≥ 80%
- Loopback if gates fail

### 3. Bug Fixes

```bash
# Quick fix workflow
tapps-agents simple-mode fix \
  --file src/api/auth.py \
  --description "Fix null pointer error in token validation" \
  --auto
```

**Steps Executed:**
1. Debug → Implement → Test

### 4. Code Review

```bash
# Get comprehensive review with score
tapps-agents reviewer review \
  --file src/api/auth.py \
  --score

# Quick score only
tapps-agents reviewer score \
  --file src/api/auth.py
```

**Output:**
- Quality score (0-100)
- Security score (0-10)
- Maintainability score (0-10)
- Issues with severity (critical, high, medium, low)

### 5. Test Generation

```bash
# Generate tests with coverage target
tapps-agents tester test \
  --file src/api/auth.py \
  --coverage-target 80

# Generate and run tests
tapps-agents tester test \
  --file src/api/auth.py \
  --run
```

## Project Initialization

### First-Time Setup

```bash
# Navigate to your project
cd /path/to/your/project

# Initialize TappsCodingAgents
tapps-agents init --auto-experts
```

**What This Does:**
1. **Phase 1: Configuration Validation**
   - Validates `.tapps-agents/` structure
   - Auto-creates missing directories
   - Checks YAML syntax

2. **Phase 1: Tech Stack Detection**
   - Scans project files (requirements.txt, package.json, etc.)
   - Generates `.tapps-agents/tech-stack.yaml`

3. **Phase 2: Context7 Cache Population**
   - Reads libraries from tech-stack.yaml
   - Pre-populates documentation cache

4. **Phase 3: Expert Auto-Generation**
   - Scans `.tapps-agents/knowledge/` for markdown files
   - Generates experts following `expert-{domain}-{topic}` convention
   - Adds to `experts.yaml`

### Upgrade Existing Installation

```bash
# Reset framework files (preserves custom files)
tapps-agents init --reset

# Reset including MCP config
tapps-agents init --reset --reset-mcp
```

## Advanced Usage

### Manual Agent Invocation

For fine-grained control, invoke agents directly:

```bash
# 1. Enhance prompt
tapps-agents enhancer enhance --prompt "Add auth" --output enhanced.md

# 2. Create plan
tapps-agents planner plan --prompt "$(cat enhanced.md)" --output plan.yaml

# 3. Design architecture
tapps-agents architect design --spec "$(cat plan.yaml)" --output design.md

# 4. Implement
tapps-agents implementer implement \
  --spec "$(cat design.md)" \
  --file src/api/auth.py

# 5. Review
tapps-agents reviewer review --file src/api/auth.py --score

# 6. Test
tapps-agents tester test --file src/api/auth.py
```

### Workflow Presets

```bash
# Minimal (2 steps): Implement → Test
tapps-agents simple-mode build --preset minimal --prompt "..." --auto

# Standard (4 steps): Plan → Implement → Review → Test [DEFAULT]
tapps-agents simple-mode build --preset standard --prompt "..." --auto

# Comprehensive (7 steps): Full analysis and design
tapps-agents simple-mode build --preset comprehensive --prompt "..." --auto

# Full SDLC (9 steps): Complete lifecycle
tapps-agents simple-mode full --prompt "..." --auto
```

### Background Execution

```bash
# Run in background (Unix/Linux/Mac)
nohup tapps-agents simple-mode build --prompt "..." --auto > build.log 2>&1 &

# Run in background (Windows PowerShell)
Start-Job -ScriptBlock {
  tapps-agents simple-mode build --prompt "..." --auto
}

# Check job status
Get-Job

# Get job output
Receive-Job -Id 1
```

## Integration with Claude Code

### As Claude Code Assistant

When working as Claude Code assistant, you should:

1. **Detect if code is framework code**
   ```
   Is this file in tapps_agents/ package?
   → YES: Use Full SDLC workflow
   → NO: Suggest build workflow
   ```

2. **Suggest workflow before direct edits**
   ```
   Before making direct edits, I recommend using:
   tapps-agents simple-mode build --prompt "..." --auto

   Benefits:
   - Automatic test generation
   - Quality scoring and gates
   - Documentation artifacts
   ```

3. **Run post-implementation validation**
   ```bash
   # After direct implementation, validate quality
   tapps-agents reviewer review --file <path> --score
   ```

### Pre-Edit Checklist

Before ANY file edits, check:

- [ ] **Is this framework code?** (`tapps_agents/` package)
  - ✅ YES → MUST use Full SDLC workflow
  - ❌ NO → Continue

- [ ] **Is this a feature/enhancement?**
  - Consider: `tapps-agents simple-mode build`

- [ ] **Is this a bug fix?**
  - Consider: `tapps-agents simple-mode fix`

- [ ] **Did user explicitly request direct edit?**
  - Suggest workflow first, get confirmation

## Troubleshooting

### Issue: Command hangs waiting for input

**Problem:** Workflow is waiting for confirmation prompt

**Solution:** Add `--auto` flag:
```bash
tapps-agents simple-mode build --prompt "..." --auto
```

### Issue: Quality gate failed

**Problem:** Code review score < threshold

**Solution:** Workflow will automatically loop back to implementation. Check review report for issues.

### Issue: Tests failing

**Problem:** Generated tests are failing

**Solution:** Workflow will loop back to test generation. Check test output for failures.

### Issue: Can't find tapps-agents command

**Problem:** tapps-agents not in PATH

**Solution:** Install or activate virtual environment:
```bash
# Install globally
pip install tapps-agents

# Or activate project venv
source .venv/bin/activate  # Unix/Linux/Mac
.venv\Scripts\activate     # Windows
```

## Best Practices

### 1. Always Use Workflows for Framework Code

Never skip workflows when modifying `tapps_agents/` package.

### 2. Use `--auto` Flag

Claude Code CLI is non-interactive, so always use `--auto`.

### 3. Check Quality Scores

After implementation, verify quality meets thresholds:
```bash
tapps-agents reviewer score --file <path>
```

### 4. Run Tests Before Committing

```bash
# Run tests
pytest tests/

# Check coverage
pytest --cov=tapps_agents tests/
```

### 5. Validate Setup

```bash
# Check system health
tapps-agents health overview

# Validate configuration
python -m tapps_agents.core.validators.config_validator
```

## Resources

- **CLAUDE.md** - Master rules file
- **docs/INIT_AUTOFILL_DETAILED_REQUIREMENTS.md** - Phases 1-3 requirements
- **docs/lessons-learned/phase-3-implementation-anti-pattern.md** - What NOT to do
- **docs/HOOKS_GUIDE.md** - Hooks configuration
- **docs/TASK_MANAGEMENT_GUIDE.md** - Task management

## Conclusion

Using tapps-agents from Claude Code CLI is straightforward:
1. **Framework code → Full SDLC workflow (MANDATORY)**
2. **User code → Build workflow (RECOMMENDED)**
3. **Always use `--auto` flag**
4. **Check quality scores**
5. **Run tests before committing**

**Key Principle:** Workflows aren't overhead—they enforce quality, generate documentation, and catch issues early.
