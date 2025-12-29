# Simple Mode Guide

## Overview

Simple Mode provides a simplified interface for TappsCodingAgents that hides complexity while showcasing power. Use natural language commands instead of agent-specific syntax.

## Quick Start

### 1. Initialize Project (First Time)

If you haven't initialized your project yet, run:

```bash
tapps-agents init
```

This sets up:
- `.tapps-agents/config.yaml` - Project configuration
- `.cursor/rules/` - Cursor Rules for AI assistance  
- `workflows/presets/` - Workflow preset YAML files
- `.claude/skills/` - Cursor Skills (use in Cursor IDE)
- `.claude/commands/` - Claude Desktop Commands (use in Claude Desktop)
- `.cursor/background-agents.yaml` - Background Agents config

### 2. Enable Simple Mode

```bash
tapps-agents simple-mode on
```

Or run the interactive onboarding wizard:

```bash
tapps-agents simple-mode init
```

### 3. Verify Setup

```bash
tapps-agents simple-mode status
```

Should show `Enabled: Yes`

### 4. Use Natural Language Commands

In Cursor chat or CLI:

```
Build a user authentication feature
Review my authentication code
Fix the error in auth.py
Add tests for service.py
```

## Intent Types

Simple Mode supports five main intent types:

### 1. Build

Create new features and functionality.

**Examples:**
- "Build a user authentication feature"
- "Create a REST API for products"
- "Add login functionality"
- "Implement user registration"

**Workflow:** Enhancer (Full Enhancement - 7 stages) → Planner → Architect → Designer → Implementer

The Enhancer performs comprehensive prompt enhancement through all 7 stages:
1. **Analysis** - Intent, domains, scope, workflow type
2. **Requirements** - Functional/NFR + Expert consultation
3. **Architecture** - Design patterns, technology recommendations
4. **Codebase Context** - Related files, existing patterns
5. **Quality Standards** - Security, testing, performance requirements
6. **Implementation Strategy** - Task breakdown, dependencies
7. **Synthesis** - Combined enhanced prompt

### 2. Review

Review code quality and security.

**Examples:**
- "Review my authentication code"
- "Check the quality of auth.py"
- "Analyze the security of this file"
- "Score the code in service.py"

**Workflow:** Reviewer → Improver (if issues found)

### 3. Fix

Debug and fix bugs and errors.

**Examples:**
- "Fix the error in auth.py"
- "Debug the login issue"
- "Resolve the bug in service.py"
- "Repair the broken authentication"

**Workflow:** Debugger → Implementer → Tester

### 4. Test

Generate and run tests.

**Examples:**
- "Add tests for service.py"
- "Generate tests for auth.py"
- "Verify the authentication code"
- "Create test coverage for user.py"

**Workflow:** Tester

### 5. Epic

Execute Epic workflows - implement all stories in an Epic document.

**Examples:**
- "Execute epic docs/prd/epic-51-yaml-automation-quality-enhancement.md"
- "Run epic epic-8-automated-documentation-generation.md"
- "Implement epic docs/prd/my-epic.md"

**Workflow:** Epic Orchestrator
1. Parses Epic document to extract stories and dependencies
2. Resolves story dependencies (topological sort)
3. Executes stories in dependency order
4. Enforces quality gates after each story (automatic loopback if < 70)
5. Tracks progress across all stories
6. Generates Epic completion report

**Usage:**
```
@simple-mode *epic docs/prd/epic-51-yaml-automation-quality-enhancement.md
```

**Note:** Epic workflows require an Epic document in markdown format with stories, dependencies, and acceptance criteria.

## Command Variations

Simple Mode understands many ways to express the same intent:

- **Build synonyms**: build, create, make, generate, add, implement, develop, write, new, feature
- **Review synonyms**: review, check, analyze, inspect, examine, score, quality, audit, assess, evaluate
- **Fix synonyms**: fix, repair, resolve, debug, error, bug, issue, problem, broken, correct
- **Test synonyms**: test, verify, validate, coverage, testing, tests
- **Epic synonyms**: epic, execute epic, run epic, implement epic, epic workflow

## Using Simple Mode

### In Cursor IDE

Use the `@simple-mode` skill:

```
@simple-mode Build a user authentication feature
@simple-mode Review my authentication code
@simple-mode Fix the error in auth.py
@simple-mode Add tests for service.py
@simple-mode *epic docs/prd/epic-51-yaml-automation-quality-enhancement.md
```

### In CLI

Simple Mode commands work directly in the CLI when enabled:

```bash
# Enable Simple Mode
tapps-agents simple-mode on

# Use natural language (via Simple Mode handler)
# Note: CLI integration for direct natural language parsing is in progress
```

### Via Workflow Presets

Simple Mode also provides simplified workflow presets:

```bash
tapps-agents workflow new-feature --prompt "Add user authentication"
tapps-agents workflow fix --file src/buggy_module.py
tapps-agents workflow improve --file src/legacy_code.py
```

## Configuration

Simple Mode can be configured in `.tapps-agents/config.yaml`:

```yaml
simple_mode:
  enabled: true
  auto_detect: true
  show_advanced: false
  natural_language: true
```

### Configuration Options

- **enabled**: Enable/disable Simple Mode (default: true)
- **auto_detect**: Auto-enable for first-time users (default: true)
- **show_advanced**: Show advanced agent-specific options (default: false)
- **natural_language**: Enable natural language command parsing (default: true)

### Toggle Simple Mode

```bash
# Enable
tapps-agents simple-mode on

# Disable
tapps-agents simple-mode off

# Check status
tapps-agents simple-mode status
```

## Progression

Simple Mode supports progressive disclosure:

- **Beginner** (default): Intent-based commands only
- **Intermediate** (after 10 commands): Agent-specific commands revealed
- **Advanced** (after 50+ commands): Full agent control

Use `*show-advanced` to reveal advanced options at any time.

## Integration with Advanced Features

Simple Mode works alongside other agent skills:

- You can still use `@reviewer *review` for advanced review options
- You can still use `@implementer *implement` for direct code generation
- Simple Mode is a convenience layer, not a replacement

## Examples

### Building Features

```
User: Build a user registration API with email validation

Simple Mode:
✅ Building user registration API...

[Enhancer] Enhancing prompt with full analysis...
  - Analysis: Intent and scope detection
  - Requirements: Gathering functional/NFR requirements
  - Architecture: System design guidance
  - Codebase Context: Analyzing related files
  - Quality Standards: Security and testing requirements
  - Implementation Strategy: Task breakdown
  - Synthesis: Creating enhanced prompt

[Planner] Creating user stories...
[Architect] Designing system architecture...
[Designer] Creating API contracts...
[Implementer] Generating code...

✅ Build complete! Created:
  - src/api/auth.py (registration endpoint)
  - src/models/user.py (user model)
  - src/utils/validation.py (email validation)
```

### Reviewing Code

```
User: Review my authentication code

Simple Mode:
✅ Reviewing authentication code...

[Reviewer] Analyzing code quality...
  - Security: 8.5/10 ✅
  - Maintainability: 7.0/10 ✅
  - Test Coverage: 6.5/10 ⚠️
  - Overall: 72/100 (Good)

Found 3 issues:
  • Security: Use parameterized queries (high)
  • Performance: N+1 query detected (medium)
  • Code Quality: Extract helper function (low)

[Improver] Suggesting improvements...
✅ Review complete!
```

## Troubleshooting

### Simple Mode Not Working

1. Check if Simple Mode is enabled:
   ```bash
   tapps-agents simple-mode status
   ```

2. Enable Simple Mode if disabled:
   ```bash
   tapps-agents simple-mode on
   ```

3. Verify configuration file exists:
   ```bash
   cat .tapps-agents/config.yaml
   ```

### Commands Not Recognized

Simple Mode uses keyword matching. If your command isn't recognized:

1. Try using more explicit keywords (build, review, fix, test)
2. Check command variations (see Command Variations section)
3. Use `*show-advanced` to access agent-specific commands

### Advanced Options

To access advanced agent-specific commands:

- Use `*show-advanced` in Simple Mode
- Or disable Simple Mode: `tapps-agents simple-mode off`
- Or use agent skills directly: `@reviewer *review`, `@implementer *implement`, etc.

## Architecture

Simple Mode uses intent-based orchestration:

1. **Intent Parser** (`tapps_agents/simple_mode/intent_parser.py`): Parses natural language into structured intents
2. **Orchestrators** (`tapps_agents/simple_mode/orchestrators/`): Coordinate multiple agents for each intent type
3. **Natural Language Handler** (`tapps_agents/simple_mode/nl_handler.py`): Routes commands to appropriate orchestrators
4. **Variations** (`tapps_agents/simple_mode/variations.py`): Handles command synonyms and variations

## See Also

- [Cursor Skills Installation Guide](CURSOR_SKILLS_INSTALLATION_GUIDE.md)
- [Cursor Rules Setup](CURSOR_RULES_SETUP.md)
- [Workflow Presets Guide](../.cursor/rules/workflow-presets.mdc)
- [Agent Capabilities Guide](../.cursor/rules/agent-capabilities.mdc)

