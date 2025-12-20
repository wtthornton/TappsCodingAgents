# Simple Mode Guide

## Overview

Simple Mode provides a simplified interface for TappsCodingAgents that hides complexity while showcasing power. Use natural language commands instead of agent-specific syntax.

## Quick Start

### Enable Simple Mode

```bash
tapps-agents simple-mode on
```

### Use Natural Language Commands

In Cursor chat or CLI:

```
Build a user authentication feature
Review my authentication code
Fix the error in auth.py
Add tests for service.py
```

## Intent Types

Simple Mode supports four main intent types:

### 1. Build

Create new features and functionality.

**Examples:**
- "Build a user authentication feature"
- "Create a REST API for products"
- "Add login functionality"
- "Implement user registration"

**Workflow:** Enhancer → Planner → Architect → Designer → Implementer

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

## Command Variations

Simple Mode understands many ways to express the same intent:

- **Build synonyms**: build, create, make, generate, add, implement, develop, write, new, feature
- **Review synonyms**: review, check, analyze, inspect, examine, score, quality, audit, assess, evaluate
- **Fix synonyms**: fix, repair, resolve, debug, error, bug, issue, problem, broken, correct
- **Test synonyms**: test, verify, validate, coverage, testing, tests

## Using Simple Mode

### In Cursor IDE

Use the `@simple-mode` skill:

```
@simple-mode Build a user authentication feature
@simple-mode Review my authentication code
@simple-mode Fix the error in auth.py
@simple-mode Add tests for service.py
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

