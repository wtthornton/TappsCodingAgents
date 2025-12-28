# TappsCodingAgents CLI Command Matrix

Complete reference of all CLI commands and parameter combinations for testing.

## Overview

This document provides a comprehensive matrix of all CLI commands, their parameters, and representative test combinations.

## Global Flags

All commands support these global flags:

- `--quiet` / `-q`: Quiet mode (errors + final results)
- `--verbose` / `-v`: Verbose mode (detailed debugging)
- `--progress {auto|rich|plain|off}`: Progress UI mode
- `--no-progress`: Disable progress UI

## Agent Commands

### Reviewer Agent

#### `review` / `*review`
**Description:** Review code with AI analysis

**Parameters:**
- `files` (positional, optional): File paths (supports multiple)
- `--pattern`: Glob pattern to match files
- `--max-workers`: Concurrent operations (default: 4)
- `--format`: Output format - json|text|markdown|html (default: json)
- `--output`: Output file path
- `--fail-under`: Quality threshold (0-100)

**Test Combinations:**
1. Minimal: `reviewer review test_file.py`
2. With format: `reviewer review test_file.py --format text`
3. With pattern: `reviewer review --pattern "**/*.py"`
4. With output: `reviewer review test_file.py --output report.json`
5. With fail-under: `reviewer review test_file.py --fail-under 70`

#### `score` / `*score`
**Description:** Calculate objective code quality scores

**Parameters:** Same as `review`

**Test Combinations:**
1. Minimal: `reviewer score test_file.py`
2. With format: `reviewer score test_file.py --format markdown`
3. Multiple files: `reviewer score file1.py file2.py file3.py`

#### `lint` / `*lint`
**Description:** Run Ruff linting

**Parameters:**
- Same as `review` plus:
- `--fail-on-issues`: Exit with code 1 if issues found

**Test Combinations:**
1. Minimal: `reviewer lint test_file.py`
2. With fail-on-issues: `reviewer lint test_file.py --fail-on-issues`
3. With pattern: `reviewer lint --pattern "src/**/*.py"`

#### `type-check` / `*type-check`
**Description:** Run mypy type checking

**Parameters:** Same as `lint`

**Test Combinations:**
1. Minimal: `reviewer type-check test_file.py`
2. With format: `reviewer type-check test_file.py --format text`

#### `report` / `*report`
**Description:** Generate comprehensive quality reports

**Parameters:**
- `target` (positional, required): File or directory path
- `formats` (positional, required): Output formats - json|markdown|html|all (one or more)
- `--output-dir`: Output directory (default: reports/quality/)

**Test Combinations:**
1. Minimal: `reviewer report src/ json`
2. Multiple formats: `reviewer report src/ json markdown html`
3. All formats: `reviewer report src/ all`
4. With output-dir: `reviewer report src/ json --output-dir custom_reports/`

#### `duplication` / `*duplication`
**Description:** Detect code duplication

**Parameters:**
- `target` (positional, required): File or directory path
- `--format`: Output format - json|text (default: json)

**Test Combinations:**
1. Minimal: `reviewer duplication src/`
2. With format: `reviewer duplication src/ --format text`

#### `docs` / `*docs`
**Description:** Get library documentation from Context7

**Parameters:**
- `library` (positional, required): Library name
- `topic` (positional, optional): Topic name
- `--mode`: Documentation mode - code|info (default: code)
- `--page`: Page number (default: 1)
- `--format`: Output format - json|text|markdown (default: json)
- `--no-cache`: Skip cache

**Test Combinations:**
1. Minimal: `reviewer docs fastapi`
2. With topic: `reviewer docs fastapi routing`
3. With mode: `reviewer docs react --mode info`
4. With format: `reviewer docs pytest --format markdown`

### Planner Agent

#### `plan` / `*plan`
**Description:** Create a detailed plan for a feature

**Parameters:**
- `description` (positional, required): Feature description
- `--format`: Output format - json|text|markdown (default: json)
- `--output`: Output file path
- `--no-enhance`: Disable prompt enhancement
- `--enhance`: Force prompt enhancement
- `--enhance-mode`: Enhancement mode - quick|full

**Test Combinations:**
1. Minimal: `planner plan "Create user authentication"`
2. With format: `planner plan "Add feature" --format markdown`
3. With enhance: `planner plan "Feature" --enhance --enhance-mode full`

#### `create-story` / `*create-story`
**Description:** Generate a user story

**Parameters:**
- `description` (positional, required): Story description
- `--epic`: Epic name
- `--priority`: Priority - high|medium|low (default: medium)
- `--format`: Output format - json|text|markdown (default: json)
- `--output`: Output file path
- Enhancement flags: Same as `plan`

**Test Combinations:**
1. Minimal: `planner create-story "User login"`
2. With epic: `planner create-story "Feature" --epic "Auth"`
3. With priority: `planner create-story "Feature" --priority high`

#### `list-stories` / `*list-stories`
**Description:** List all user stories

**Parameters:**
- `--epic`: Filter by epic
- `--status`: Filter by status
- `--format`: Output format - json|text|markdown (default: json)
- `--output`: Output file path

**Test Combinations:**
1. Minimal: `planner list-stories`
2. With epic: `planner list-stories --epic "Auth"`
3. With status: `planner list-stories --status todo`

### Implementer Agent

#### `implement` / `*implement`
**Description:** Generate and write code to file

**Parameters:**
- `specification` (positional, required): Code specification
- `file_path` (positional, required): Target file path
- `--context`: Additional context
- `--language`: Programming language (default: python)
- `--format`: Output format - json|text|markdown (default: json)
- `--output`: Output file path
- Enhancement flags: Same as `plan`

**Test Combinations:**
1. Minimal: `implementer implement "Create function" test.py`
2. With context: `implementer implement "Feature" test.py --context "Use FastAPI"`
3. With language: `implementer implement "Code" test.js --language javascript`

#### `generate-code` / `*generate-code`
**Description:** Generate code without writing to file

**Parameters:**
- `specification` (positional, required): Code specification
- `--file`: Optional file for context
- `--context`: Additional context
- `--language`: Programming language (default: python)
- `--format`: Output format - json|text|markdown (default: json)
- `--output`: Output file path
- Enhancement flags: Same as `plan`

**Test Combinations:**
1. Minimal: `implementer generate-code "Create function"`
2. With file: `implementer generate-code "Code" --file src/utils.py`

#### `refactor` / `*refactor`
**Description:** Refactor existing code file

**Parameters:**
- `file_path` (positional, required): Source file path
- `instruction` (positional, required): Refactoring instruction
- `--format`: Output format - json|text|markdown|diff (default: json)
- `--output`: Output file path

**Test Combinations:**
1. Minimal: `implementer refactor test.py "Extract function"`
2. With format: `implementer refactor test.py "Refactor" --format diff`

### Tester Agent

#### `test` / `*test`
**Description:** Generate and run tests for a file

**Parameters:**
- `file` (positional, required): Source file path
- `--test-file`: Test file path
- `--integration`: Generate integration tests
- `--focus`: Comma-separated test aspects
- `--format`: Output format - json|text|markdown (default: json)
- `--output`: Output file path

**Test Combinations:**
1. Minimal: `tester test test_file.py`
2. With integration: `tester test test_file.py --integration`
3. With test-file: `tester test src.py --test-file tests/test_src.py`

#### `generate-tests` / `*generate-tests`
**Description:** Generate tests without running them

**Parameters:**
- `file` (positional, required): Source file path
- `--test-file`: Test file path
- `--integration`: Generate integration tests
- `--format`: Output format - json|text|markdown (default: json)
- `--output`: Output file path

**Test Combinations:**
1. Minimal: `tester generate-tests test_file.py`
2. With integration: `tester generate-tests test_file.py --integration`

#### `run-tests` / `*run-tests`
**Description:** Run existing test suite

**Parameters:**
- `test_path` (positional, optional): Test path
- `--no-coverage`: Skip coverage analysis
- `--format`: Output format - json|text|markdown (default: json)
- `--output`: Output file path

**Test Combinations:**
1. Minimal: `tester run-tests`
2. With path: `tester run-tests tests/unit/`
3. With no-coverage: `tester run-tests --no-coverage`

## Top-Level Commands

### `init`
**Description:** Initialize project (Cursor Rules + workflow presets)

**Parameters:**
- `--no-rules`: Skip creating rules
- `--no-presets`: Skip creating presets
- `--no-config`: Skip creating config
- `--no-skills`: Skip installing Skills
- `--no-background-agents`: Skip Background Agents
- `--no-cache`: Skip cache pre-population
- `--no-cursorignore`: Skip .cursorignore
- `--reset`: Reset framework files
- `--upgrade`: Alias for --reset
- `--no-backup`: Skip backup before reset
- `--reset-mcp`: Reset MCP config
- `--preserve-custom`: Preserve custom files (default: True)
- `--rollback`: Rollback from backup
- `--yes`: Auto-answer yes
- `--dry-run`: Preview changes

**Test Combinations:**
1. Minimal: `init`
2. With flags: `init --yes --no-cache`
3. Reset: `init --reset --yes`

### `score`
**Description:** Quick code scoring (shortcut for reviewer score)

**Parameters:**
- `file` (positional, required): File path
- `--format`: Output format - json|text|markdown|html (default: json)

**Test Combinations:**
1. Minimal: `score test_file.py`
2. With format: `score test_file.py --format text`

### `doctor`
**Description:** Validate local environment

**Parameters:**
- `--format`: Output format - json|text (default: text)
- `--config-path`: Config file path

**Test Combinations:**
1. Minimal: `doctor`
2. With format: `doctor --format json`

### `workflow`
**Description:** Run preset workflows

**Subcommands:**
- `list`: List all presets
- `full` / `enterprise`: Full SDLC pipeline
- `rapid` / `feature`: Rapid development
- `fix` / `refactor`: Bug fixing
- `quality` / `improve`: Quality improvement
- `hotfix` / `urgent`: Quick fixes
- `new-feature`: Simple new feature
- `state`: State management (list, show, cleanup, resume)
- `recommend`: Get workflow recommendation

**Common Parameters:**
- `--prompt`: Natural language description
- `--file`: Target file/directory
- `--auto`: Fully automated execution

**Test Combinations:**
1. List: `workflow list`
2. Rapid: `workflow rapid --prompt "Add feature" --auto`
3. Full: `workflow full --prompt "Build API" --auto`
4. Fix: `workflow fix --file src/buggy.py --auto`

### `simple-mode`
**Description:** Simple Mode management

**Subcommands:**
- `on`: Enable Simple Mode
- `off`: Disable Simple Mode
- `status`: Check status
- `init`: Run onboarding
- `configure`: Configure settings
- `progress`: Show progression
- `full`: Run full lifecycle workflow

**Test Combinations:**
1. Status: `simple-mode status`
2. On: `simple-mode on`
3. Full: `simple-mode full --prompt "Build feature" --auto`

## Test Coverage Strategy

### Representative Combinations

For each command, we test:
1. **Minimal**: Required parameters only
2. **Format variants**: Different output formats
3. **Optional params**: Common optional parameters
4. **Edge cases**: Invalid inputs, missing files, etc.

### Test Organization

- `test_agent_commands.py`: All agent commands
- `test_top_level_commands.py`: Top-level commands
- `test_global_flags.py`: Global flags with commands
- `test_error_handling.py`: Error scenarios
- `test_output_formats.py`: Format validation
- `test_demo_scenarios.py`: Demo scenario conversions

## Notes

- All commands support both `command` and `*command` formats (aliases)
- Global flags can appear before or after subcommand
- Format defaults to `json` for most commands
- Network-dependent commands may fail gracefully if offline

