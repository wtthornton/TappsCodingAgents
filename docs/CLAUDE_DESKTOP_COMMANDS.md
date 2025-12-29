# Claude Desktop Commands Guide

This guide explains how to use TappsCodingAgents commands in Claude Desktop, which work alongside Cursor Skills for a unified experience across both platforms.

## Overview

TappsCodingAgents provides commands that work in **both** Claude Desktop and Cursor IDE:

- **Claude Desktop**: Use `@command-name` (commands in `.claude/commands/`)
- **Cursor IDE**: Use `@agent-name *command` (skills in `.claude/skills/`)
- **CLI/Terminal**: Use `tapps-agents <agent> <command>`

All three interfaces provide the same functionality, so you can use whichever is most convenient.

## Installation

Claude Desktop commands are automatically installed when you run:

```bash
tapps-agents init
```

This creates the `.claude/commands/` directory with all available commands.

## Quick Start

### In Claude Desktop

Type `@` followed by the command name:

```
@review src/api/auth.py
@build "Create a user authentication feature"
@test src/api/auth.py
```

### In Cursor IDE

Use the agent name followed by the command:

```
@reviewer *review src/api/auth.py
@simple-mode *build "Create a user authentication feature"
@tester *test src/api/auth.py
```

### In Terminal/CLI

Use the CLI syntax:

```bash
tapps-agents reviewer review src/api/auth.py
tapps-agents simple-mode full --prompt "Create a user authentication feature"
tapps-agents tester test src/api/auth.py
```

## Available Commands

### Core Development

#### `@review` - Code Review
Full code review with objective quality metrics.

```
@review src/api/auth.py
@review src/utils/helpers.py
```

**Cursor**: `@reviewer *review <file>`  
**CLI**: `tapps-agents reviewer review <file>`

#### `@score` - Quick Scoring
Fast quality scoring without detailed feedback.

```
@score src/api/auth.py
```

**Cursor**: `@reviewer *score <file>`  
**CLI**: `tapps-agents reviewer score <file>`

#### `@implement` - Code Generation
Generate code from natural language description.

```
@implement "Create a user authentication API" src/api/auth.py
```

**Cursor**: `@implementer *implement "<desc>" <file>`  
**CLI**: `tapps-agents implementer implement "<desc>" <file>`

#### `@test` - Test Generation
Generate and run comprehensive tests.

```
@test src/api/auth.py
```

**Cursor**: `@tester *test <file>`  
**CLI**: `tapps-agents tester test <file>`

#### `@debug` - Error Debugging
Debug errors and find root causes.

```
@debug "Null pointer error on line 42" --file src/api/auth.py
```

**Cursor**: `@debugger *debug "<error>" --file <file>`  
**CLI**: `tapps-agents debugger debug "<error>" --file <file>`

### Workflow Commands (Simple Mode)

#### `@build` - Complete Feature Workflow
Complete 7-step feature development workflow.

```
@build "Create a user authentication API with JWT tokens"
```

**What it does:**
1. Enhances prompt with requirements analysis
2. Creates user stories with acceptance criteria
3. Designs system architecture
4. Designs API and data models
5. Implements code
6. Reviews code quality (loops if score < 70)
7. Generates comprehensive tests

**Cursor**: `@simple-mode *build "<desc>"`  
**CLI**: `tapps-agents simple-mode full --prompt "<desc>" --auto`

#### `@fix` - Bug Fixing Workflow
Systematic bug fixing with debugging.

```
@fix src/api/auth.py "Fix the null pointer error"
```

**What it does:**
1. Debugs error and finds root cause
2. Implements the fix
3. Generates/updates tests
4. Validates the fix

**Cursor**: `@simple-mode *fix <file> "<desc>"`  
**CLI**: `tapps-agents simple-mode fix --file <file> --prompt "<desc>"`

### Code Improvement

#### `@refactor` - Code Refactoring
Refactor code with specific instructions.

```
@refactor src/api/auth.py "Extract helper functions, improve error handling"
```

**Cursor**: `@implementer *refactor <file> "<instructions>"`  
**CLI**: `tapps-agents implementer refactor <file> "<instructions>"`

#### `@improve` - Code Improvement
Improve code quality and maintainability.

```
@improve src/api/auth.py "Add input validation, improve error handling"
```

**Cursor**: `@improver *improve <file> "<instructions>"`  
**CLI**: `tapps-agents improver improve <file> "<instructions>"`

#### `@lint` - Code Linting
Run Ruff linting (10-100x faster).

```
@lint src/api/auth.py
```

**Cursor**: `@reviewer *lint <file>`  
**CLI**: `tapps-agents reviewer lint <file>`

### Planning & Design

#### `@plan` - Development Planning
Create development plan with user stories.

```
@plan "Create a user authentication feature"
```

**Cursor**: `@planner *plan "<desc>"`  
**CLI**: `tapps-agents planner plan "<desc>"`

#### `@design` - System Design
Design system architecture and components.

```
@design "User authentication system with JWT tokens"
```

**Cursor**: `@architect *design "<desc>"`  
**CLI**: `tapps-agents architect design "<desc>"`

#### `@docs` - Documentation
Generate documentation for code.

```
@docs src/api/auth.py
```

**Cursor**: `@documenter *document <file>`  
**CLI**: `tapps-agents documenter document <file>`

### Security & Quality

#### `@security-scan` - Security Scanning
Scan code for security vulnerabilities.

```
@security-scan src/api/auth.py
```

**Cursor**: `@reviewer *security-scan <file>`  
**CLI**: `tapps-agents reviewer security-scan <file>`

#### `@library-docs` - Library Documentation
Get up-to-date library documentation from Context7.

```
@library-docs fastapi
@library-docs fastapi routing
```

**Cursor**: `@reviewer *docs <library> [topic]`  
**CLI**: `tapps-agents reviewer docs <library> [topic]`

## Command Comparison

| Task | Claude Desktop | Cursor IDE | CLI |
|------|---------------|------------|-----|
| Code Review | `@review <file>` | `@reviewer *review <file>` | `tapps-agents reviewer review <file>` |
| Build Feature | `@build "<desc>"` | `@simple-mode *build "<desc>"` | `tapps-agents simple-mode full --prompt "<desc>"` |
| Generate Tests | `@test <file>` | `@tester *test <file>` | `tapps-agents tester test <file>` |
| Debug Error | `@debug "<error>" --file <file>` | `@debugger *debug "<error>" --file <file>` | `tapps-agents debugger debug "<error>" --file <file>` |
| Get Library Docs | `@library-docs fastapi` | `@reviewer *docs fastapi` | `tapps-agents reviewer docs fastapi` |

## Best Practices

### 1. Use `@build` for New Features
The `@build` command provides a complete workflow with all quality gates:

```
@build "Create a user authentication API with JWT tokens"
```

This executes all 7 steps automatically and ensures quality.

### 2. Use `@review` Before Committing
Always review code before committing:

```
@review src/api/auth.py
```

### 3. Use `@test` After Implementation
Generate tests after implementing features:

```
@test src/api/auth.py
```

### 4. Use `@fix` for Bugs
Use the systematic fix workflow for bugs:

```
@fix src/api/auth.py "Fix the null pointer error"
```

### 5. Use `@library-docs` for API Reference
Get up-to-date library documentation:

```
@library-docs fastapi routing
```

## Configuration

Commands use the same configuration as Cursor Skills:

- **Config File**: `.tapps-agents/config.yaml`
- **Context7 Cache**: `.tapps-agents/kb/context7-cache`
- **Quality Gates**: `.tapps-agents/quality-gates.yaml`

## Troubleshooting

### Command Not Found

If a command doesn't work in Claude Desktop:

1. **Check Installation**: Ensure commands are installed:
   ```bash
   ls .claude/commands/
   ```

2. **Reinstall**: Run `tapps-agents init` to reinstall commands

3. **Check Syntax**: Verify command syntax matches examples

### Command Not Working

If a command executes but doesn't produce expected results:

1. **Check Configuration**: Verify `.tapps-agents/config.yaml` exists
2. **Check Dependencies**: Ensure required tools are installed (Ruff, mypy, etc.)
3. **Try CLI Equivalent**: Test with CLI to isolate the issue:
   ```bash
   tapps-agents reviewer review src/api/auth.py
   ```

### Context7 Not Working

If `@library-docs` doesn't work:

1. **Check API Key**: Verify Context7 API key in config
2. **Check Cache**: Ensure cache directory exists
3. **Test CLI**: Try CLI command to verify setup

## Related Documentation

- **Cursor Skills Guide**: `docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md`
- **Command Reference**: `docs/TAPPS_AGENTS_COMMAND_REFERENCE.md`
- **Quick Reference**: `.cursor/rules/quick-reference.mdc`
- **Simple Mode Guide**: `docs/SIMPLE_MODE_GUIDE.md`

## Summary

Claude Desktop commands provide the same functionality as Cursor Skills, allowing you to use TappsCodingAgents in whichever environment you prefer:

- **Claude Desktop**: `@command-name` (natural language friendly)
- **Cursor IDE**: `@agent-name *command` (structured commands)
- **CLI/Terminal**: `tapps-agents <agent> <command>` (automation friendly)

All three interfaces work together seamlessly, sharing the same configuration and providing consistent results.

