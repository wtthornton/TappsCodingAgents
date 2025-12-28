# TappsCodingAgents Command Reference

Complete reference for all tapps-agents commands, parameters, and usage patterns. This document identifies which commands are **Cursor-first** (designed for Cursor AI chat) vs **CLI-first** (designed for terminal/scripting use).

## Table of Contents

- [Command Classification](#command-classification)
- [Top-Level Commands](#top-level-commands)
- [Agent Commands](#agent-commands)
- [Workflow Commands](#workflow-commands)
- [Epic Commands](#epic-commands)
- [Coverage-Driven Test Commands](#coverage-driven-test-commands)
- [Microservice Commands](#microservice-commands)
- [Docker Commands](#docker-commands)
- [Recommended Command Combinations](#recommended-command-combinations)
- [Cursor vs CLI Usage Guide](#cursor-vs-cli-usage-guide)

---

## Command Classification

### Cursor-First Commands

**Cursor-first** commands are designed to be used in Cursor AI chat using the `@agent-name *command` syntax. These commands:
- Use Cursor Skills (`.claude/skills/`)
- Leverage Cursor's configured LLM
- Work with Background Agents
- Support natural language interaction
- Execute via file-based or API-based modes

**Syntax:** `@agent-name *command [parameters]`

### CLI-First Commands

**CLI-first** commands are designed for terminal/scripting use with the `tapps-agents` CLI. These commands:
- Use argparse-based command parsing
- Support batch processing and automation
- Generate structured output (JSON, text, markdown)
- Work in headless/CI environments
- Can be piped and scripted

**Syntax:** `tapps-agents <agent> <command> [--flags]`

### Dual-Mode Commands

Some commands work in **both** modes:
- Same functionality in Cursor and CLI
- Different syntax but equivalent results
- CLI aliases support `*command` format for compatibility

---

## Global CLI Options (All Commands)

These flags work for **any** CLI command and can be placed **before or after** the subcommand (modern CLI behavior):

```bash
tapps-agents doctor --progress rich
tapps-agents reviewer score README.md --no-progress
tapps-agents --progress plain doctor
```

- `--quiet` / `-q`: Quiet mode (errors + final results)
- `--verbose` / `-v`: Verbose diagnostics
- `--progress {auto,rich,plain,off}`: Progress UI mode
- `--no-progress`: Disable progress UI (same as `--progress off`)

**Environment variables:**
- `TAPPS_PROGRESS=auto|rich|plain|off`
- `TAPPS_NO_PROGRESS=1` (or `NO_PROGRESS=1`)

---

## Top-Level Commands

### `create` - Create New Project (CLI-First, Cursor-Compatible)

**Purpose:** Create a complete, tested application from a natural language description. This is the PRIMARY USE CASE for TappsCodingAgents.

**CLI Syntax:**
```bash
tapps-agents create "<description>" [--workflow <preset>] [--cursor-mode]
```

**Parameters:**
- `description` (required): Natural language description of the project or application
- `--workflow` (optional): Workflow preset - `full` (default), `rapid`, `enterprise`, `feature`
- `--cursor-mode` (flag): Run in Cursor mode (uses Background Agents)

**When to Use:**
- Starting a new project from scratch
- Greenfield development
- Rapid prototyping
- Learning the framework

**Example:**
```bash
tapps-agents create "Build a REST API for a todo app with user authentication"
tapps-agents create "Create a React dashboard with data visualization" --workflow rapid
```

**Cursor Alternative:**
```cursor
@simple-mode full --prompt "Build a REST API for a todo app with user authentication"
# or natural language:
@simple-mode Create a REST API for a todo app with user authentication
```

---

### `init` - Initialize Project (CLI-First)

**Purpose:** Initialize a new project with TappsCodingAgents configuration. Sets up everything needed for Cursor chat commands and CLI commands to work out-of-the-box. **This is the first command you should run on any project** to enable all tapps-agents capabilities in Cursor IDE.

**CLI Syntax:**
```bash
tapps-agents init [--no-rules] [--no-presets] [--no-config] [--no-skills] [--no-background-agents] [--no-cache] [--no-cursorignore] [--reset] [--upgrade] [--no-backup] [--reset-mcp] [--preserve-custom] [--rollback <path>] [--yes] [--dry-run]
```

**When to Use:**
- **First-time setup**: Run `tapps-agents init` when adding TappsCodingAgents to a new or existing project
- **Upgrading framework**: Use `tapps-agents init --reset` to upgrade framework files to latest version
- **Selective setup**: Use `--no-<component>` flags to skip specific components you don't need
- **CI/CD automation**: Use `--yes` flag to skip confirmation prompts

**What Happens When Executed on Other Projects:**

When you run `tapps-agents init` on any project (new or existing), it:

1. **Detects existing installation**: Checks for existing tapps-agents files and warns if found (unless using `--reset`)
2. **Creates directory structure**: Sets up all required directories if they don't exist
3. **Copies framework files**: Installs framework-provided files (Skills, Rules, Presets) from the installed package
4. **Preserves user files**: Never overwrites existing user files unless using `--reset` mode
5. **Detects tech stack**: Automatically detects project dependencies (Python packages, frameworks) and configures experts
6. **Pre-populates cache**: Optionally pre-populates Context7 cache with project dependencies (unless `--no-cache`)
7. **Validates setup**: Runs environment diagnostics to verify everything is configured correctly

**Parameters:**

- `--no-rules`: Skip creating `.cursor/rules/` directory
  - **When to use**: If you want to manage rules manually or use custom rules only
  - **Why**: Reduces setup time if you don't need framework-provided rules

- `--no-presets`: Skip creating workflow presets directory
  - **When to use**: If you only use custom workflows or CLI commands
  - **Why**: Reduces setup time if you don't need preset workflows

- `--no-config`: Skip creating `.tapps-agents/config.yaml`
  - **When to use**: If you have existing config or want to configure manually
  - **Why**: Allows manual configuration without framework defaults

- `--no-skills`: Skip installing Cursor Skills
  - **When to use**: If you only use CLI commands, not Cursor chat
  - **Why**: Reduces setup time, but disables `@agent-name` commands in Cursor

- `--no-background-agents`: Skip creating Background Agents config
  - **When to use**: If you don't want automatic workflow execution
  - **Why**: Manual control over when workflows run

- `--no-cache`: Skip pre-populating Context7 cache
  - **When to use**: If Context7 is not configured or you want to populate manually
  - **Why**: Faster init if Context7 API key not available

- `--no-cursorignore`: Skip creating `.cursorignore` file
  - **When to use**: If you have custom indexing preferences
  - **Why**: Manual control over Cursor indexing patterns

- `--reset` / `--upgrade`: Reset framework-managed files to latest version
  - **When to use**: After upgrading tapps-agents package, to get latest framework files
  - **Why**: Updates Skills, Rules, Presets to match installed package version
  - **Note**: Preserves user data (config, experts, knowledge base, custom files)

- `--no-backup`: Skip backup before reset (not recommended)
  - **When to use**: Only if you're certain you don't need rollback capability
  - **Why**: Faster reset, but no way to undo changes

- `--reset-mcp`: Also reset `.cursor/mcp.json` to framework version
  - **When to use**: If MCP config is corrupted or you want framework defaults
  - **Why**: Restores MCP configuration to framework-provided version

- `--preserve-custom`: Preserve custom Skills, Rules, and presets (default: True)
  - **When to use**: Default behavior - custom files are always preserved
  - **Why**: Protects user customizations during reset

- `--rollback <path>`: Rollback an init reset from a backup
  - **When to use**: If reset caused issues and you need to restore previous state
  - **Why**: Restores files from backup created during reset

- `--yes` / `-y`: Automatically answer 'yes' to all confirmation prompts
  - **When to use**: CI/CD pipelines, automation scripts, non-interactive environments
  - **Why**: Enables fully automated init without user interaction

- `--dry-run`: Preview what would be reset without making changes
  - **When to use**: Before running `--reset` to see what will change
  - **Why**: Safe way to preview reset impact without modifying files

**What `init` Installs:**

1. **Cursor Skills** (`.claude/skills/`): 13 agent skills for `@agent-name *command` syntax in Cursor chat
2. **Cursor Rules** (`.cursor/rules/`): Project context, workflow presets, quick reference, Simple Mode guide
3. **Background Agents** (`.cursor/background-agents.yaml`): Auto-execution configuration for quality checks
4. **MCP Config** (`.cursor/mcp.json`): Context7 MCP server configuration for library documentation lookup
5. **Project Config** (`.tapps-agents/config.yaml`): Framework configuration with tech stack templates
6. **Tech Stack Config** (`.tapps-agents/tech-stack.yaml`): Detected frameworks and expert priorities
7. **Experts Scaffold**:
   - `.tapps-agents/domains.md`: Business domain mapping template
   - `.tapps-agents/experts.yaml`: Project experts configuration stub
   - `.tapps-agents/knowledge/`: Knowledge base directory structure
8. **Workflow Presets** (`workflows/presets/`): Predefined workflow YAML files
9. **Context7 Cache**: Pre-populated with project dependencies + built-in expert libraries
10. **`.cursorignore`**: Performance optimization patterns

**Why Init Matters in Cursor:**

- **Cursor Skills**: Enables `@reviewer`, `@implementer`, `@simple-mode` commands in Cursor chat
- **Cursor Rules**: Provides context to AI about your project structure and workflows
- **Background Agents**: Auto-executes quality checks, testing, and security scans
- **Context7 MCP**: Library documentation lookup (e.g., `@reviewer *docs fastapi routing`)
- **Experts + RAG**: 
  - Built-in technical experts are automatically loaded based on tech stack
  - Project/business experts can be configured in `.tapps-agents/experts.yaml`
  - Knowledge base files in `.tapps-agents/knowledge/<domain>/` provide domain context

**Examples:**
```bash
# Initial setup (recommended for all projects)
tapps-agents init

# Initial setup without Context7 cache (if API key not configured)
tapps-agents init --no-cache

# Upgrade framework files after package update
tapps-agents init --reset

# Preview what would be reset (safe to run)
tapps-agents init --reset --dry-run

# Automated setup for CI/CD
tapps-agents init --yes

# Minimal setup (only Skills and Rules, no presets or cache)
tapps-agents init --no-presets --no-cache

# Rollback from backup
tapps-agents init --rollback .tapps-agents/backups/init-reset-20250116-143022
```

**Simple Mode is Installed by Init:**
- Simple Mode skill (`.claude/skills/simple-mode/`) is automatically installed
- Simple Mode rule (`.cursor/rules/simple-mode.mdc`) is automatically installed
- Simple Mode is enabled by default in config
- Ready to use immediately in Cursor chat after `init`

**After Init:**

**In Cursor Chat (Recommended - Use Simple Mode):**
```cursor
# Natural language commands (Simple Mode auto-detects intent)
@simple-mode Build a user authentication feature
@simple-mode Review my authentication code
@simple-mode Fix the error in auth.py
@simple-mode Add tests for service.py

# Explicit commands (more reliable for complex workflows)
@simple-mode *build "Add user authentication"
@simple-mode *review src/api/auth.py
@simple-mode *fix src/buggy.py "Fix the error"
@simple-mode *epic docs/prd/epic-51.md

# Individual agent commands (when you need specific agents)
@reviewer *score src/main.py
@implementer *implement "Add feature" src/feature.py
@reviewer *docs fastapi routing
```

**In Terminal/CI:**
```bash
# Workflow presets
tapps-agents workflow rapid --prompt "Add feature" --auto
tapps-agents workflow full --prompt "Build API" --auto

# Individual agent commands
tapps-agents reviewer review src/
tapps-agents score src/main.py

# Simple Mode management
tapps-agents simple-mode on
tapps-agents simple-mode status
tapps-agents simple-mode full --prompt "Build feature" --auto
```

---

### `workflow` - Run Preset Workflows (Dual-Mode)

**Purpose:** Execute predefined workflow presets for common development scenarios.

**CLI Syntax:**
```bash
tapps-agents workflow <preset> [--prompt "<description>"] [--file <path>] [--auto]
```

**Available Presets:**
- `full` / `enterprise`: Complete SDLC pipeline
- `rapid` / `feature`: Fast feature development
- `fix` / `refactor`: Maintenance and bug fixing
- `quality` / `improve`: Code quality improvement
- `hotfix` / `urgent`: Quick production fixes
- `new-feature`: Simple new feature workflow
- `list`: List all available presets
- `recommend`: Get AI-powered workflow recommendation
- `state`: Workflow state management (list, show, cleanup, resume)
- `resume`: Resume interrupted workflow

**Common Parameters:**
- `--prompt` / `-p`: Natural language description (required for greenfield workflows)
- `--file`: Target file/directory (required for fix/refactor workflows)
- `--auto`: Enable fully automated execution (skips interactive prompts)

**When to Use:**
- `full`: Enterprise projects, mission-critical features
- `rapid`: Sprint work, well-understood features
- `fix`: Bug fixes, technical debt reduction
- `quality`: Code review cycles, quality improvement sprints
- `hotfix`: Urgent production issues

**Examples:**
```bash
# Full SDLC workflow
tapps-agents workflow full --prompt "Build microservices e-commerce platform" --auto

# Rapid development
tapps-agents workflow rapid --prompt "Add user profile editing" --auto

# Bug fix workflow
tapps-agents workflow fix --file src/buggy_module.py --auto

# Quality improvement
tapps-agents workflow quality --file src/legacy_code.py --auto

# Get recommendation
tapps-agents workflow recommend --non-interactive
```

**Cursor Alternative:**
```cursor
@simple-mode *build "Add user profile editing"
@simple-mode *fix src/buggy_module.py "Fix the error"
@simple-mode *review src/legacy_code.py
```

**Workflow State Management:**
```bash
# List saved workflow states
tapps-agents workflow state list [--workflow-id <id>] [--format json|text]

# Show workflow state details
tapps-agents workflow state show <workflow_id> [--format json|text]

# Cleanup old states
tapps-agents workflow state cleanup [--retention-days 30] [--max-states-per-workflow 10] [--remove-completed] [--dry-run]

# Resume workflow
tapps-agents workflow resume [--workflow-id <id>] [--validate]
```

---

### `score` - Quick Code Scoring (CLI-First, Cursor-Compatible)

**Purpose:** Quick shortcut to score code files (equivalent to `reviewer score`).

**CLI Syntax:**
```bash
tapps-agents score <file> [--format json|text]
```

**Parameters:**
- `file` (required): Path to Python code file
- `--format`: Output format - `json` (default) or `text`

**When to Use:**
- Quick quality check before committing
- CI/CD quality gates
- Pre-review screening

**Example:**
```bash
tapps-agents score src/main.py
tapps-agents score src/main.py --format text
```

**Cursor Alternative:**
```cursor
@reviewer *score src/main.py
```

---

### `doctor` - Environment Diagnostics (CLI-First)

**Purpose:** Validate local development environment and tools.

**CLI Syntax:**
```bash
tapps-agents doctor [--format json|text] [--config-path <path>]
```

**Parameters:**
- `--format`: Output format - `text` (default) or `json`
- `--config-path`: Explicit path to config file if not in default location

**When to Use:**
- Troubleshooting setup issues
- Verifying tool installation
- CI/CD environment validation

**Example:**
```bash
tapps-agents doctor
tapps-agents doctor --format json
```

---

### `health` - Health Checks (CLI-First)

**Purpose:** Comprehensive health checks for TappsCodingAgents.

**CLI Syntax:**
```bash
tapps-agents health <command> [options]
```

**Subcommands:**
- `check [--check <name>] [--format json|text] [--save]`: Run health checks
- `dashboard` / `show [--format json|text]`: Display health dashboard
- `metrics [--check-name <name>] [--status <status>] [--days 30] [--format json|text]`: Show stored metrics
- `trends --check-name <name> [--days 7] [--format json|text]`: Show health trends

**When to Use:**
- System health monitoring
- Performance optimization
- Troubleshooting degradation

**Example:**
```bash
tapps-agents health check
tapps-agents health dashboard
tapps-agents health trends --check-name execution --days 30
```

---

### `simple-mode` - Simple Mode Management (Dual-Mode)

**Purpose:** Manage Simple Mode - simplified natural language interface. Simple Mode is the **primary user interface** for TappsCodingAgents in Cursor, providing natural language commands that automatically orchestrate multiple specialized skills.

**Simple Mode is Installed by `init`:**
- Simple Mode skill (`.claude/skills/simple-mode/`) is automatically installed by `tapps-agents init`
- Simple Mode rule (`.cursor/rules/simple-mode.mdc`) is automatically installed
- Simple Mode is enabled by default in config, but you can run `tapps-agents simple-mode on` to ensure it's active
- **Ready to use immediately after `init`** - no additional setup needed

**CLI Syntax:**
```bash
tapps-agents simple-mode <command> [options]
```

**Subcommands:**
- `on` - Enable Simple Mode
  - **When to use**: After running `tapps-agents init`, to enable Simple Mode
  - **Why**: Activates Simple Mode configuration in `.tapps-agents/config.yaml`
  - **Note**: Simple Mode skill is installed by `init`, but must be enabled via this command

- `off` - Disable Simple Mode
  - **When to use**: If you want to use individual agent commands only
  - **Why**: Disables Simple Mode but keeps skill installed

- `status [--format json|text]` - Check Simple Mode status
  - **When to use**: Verify Simple Mode is enabled and configured
  - **Why**: Shows current configuration and enabled state

- `init` - Run onboarding wizard
  - **When to use**: First time using Simple Mode, or to reconfigure
  - **Why**: Interactive setup with guided configuration
  - **What it does**: Detects project type, configures settings, suggests first command

- `configure` / `config` - Configure settings interactively
  - **When to use**: To change Simple Mode settings after initial setup
  - **Why**: Update configuration without running full onboarding

- `progress` - Show learning progression
  - **When to use**: Track your Simple Mode usage and unlocked features
  - **Why**: Shows learning level, commands used, features unlocked

- `full [--prompt "<desc>"] [--file <path>] [--auto]` - Run full lifecycle workflow
  - **When to use**: Complete SDLC workflow with all quality gates
  - **Why**: Comprehensive workflow with requirements, design, implementation, testing, security, documentation
  - **Parameters**:
    - `--prompt`: Natural language description (required for greenfield)
    - `--file`: Target file/directory (for brownfield/refactoring)
    - `--auto`: Fully automated execution

**When to Use Simple Mode:**
- **New users**: Start with Simple Mode for natural language commands
- **Feature development**: Use `*build` for complete feature workflows
- **Code review**: Use `*review` for quality analysis
- **Bug fixing**: Use `*fix` for systematic debugging
- **Testing**: Use `*test` for test generation
- **Epic execution**: Use `*epic` for implementing entire Epic documents
- **Full lifecycle**: Use `*full` for complete SDLC workflows

**Why Use Simple Mode:**
- **Natural language**: Use plain English instead of learning multiple agent commands
- **Automatic orchestration**: Skills are coordinated automatically in the right sequence
- **Quality gates**: Automatic quality checks with loopback on failures
- **Better outcomes**: Produces higher quality code with comprehensive documentation
- **Workflow enforcement**: Ensures all steps are executed (enhance → plan → design → implement → review → test)

**Example:**
```bash
# Enable Simple Mode (usually already enabled after init)
tapps-agents simple-mode on

# Check status
tapps-agents simple-mode status

# Run full workflow
tapps-agents simple-mode full --prompt "Build authentication feature" --auto

# Run onboarding wizard
tapps-agents simple-mode init
```

**Cursor Usage (Natural Language - Recommended):**
```cursor
@simple-mode Build a user authentication feature
@simple-mode Review my authentication code
@simple-mode Fix the error in auth.py
@simple-mode Add tests for service.py
@simple-mode Execute epic docs/prd/epic-51.md
```

**Cursor Usage (Explicit Commands - More Reliable):**
```cursor
@simple-mode *build "Create a user authentication feature"
@simple-mode *review src/api/auth.py
@simple-mode *fix src/buggy.py "Fix the error"
@simple-mode *test src/api/auth.py
@simple-mode *epic docs/prd/epic-51-yaml-automation-quality-enhancement.md
@simple-mode *full "Build a complete REST API"
```

**Available Simple Mode Commands in Cursor:**
- `*build {description}` - Complete 7-step feature development workflow
- `*review {file}` - Code quality review workflow
- `*fix {file} {description}` - Bug fixing workflow with debugging
- `*test {file}` - Test generation workflow
- `*epic {epic-doc.md}` - Epic execution workflow (all stories in dependency order)
- `*test-coverage {file} --target 80` - Coverage-driven test generation
- `*fix-tests {test-file}` - Auto-fix test failures
- `*microservice {name} --port {port} --type {type}` - Generate complete microservice structure
- `*docker-fix {service} "{error}"` - Debug container errors
- `*integrate-service {service1} --with {service2}` - Service-to-service integration
- `*full {description}` - Full SDLC workflow (9 steps)
- `*help` - Show Simple Mode help
- `*status` - Check Simple Mode status

See the "Simple Mode Workflows" section below for detailed workflow documentation.

---

### `generate-rules` - Generate Cursor Rules from Workflow YAML (CLI-First)

**Purpose:** Generate Cursor Rules documentation (e.g. `.cursor/rules/workflow-presets.mdc`) from workflow YAML definitions.

**CLI Syntax:**
```bash
tapps-agents generate-rules [--output <path>] [--no-backup]
```

**Parameters:**
- `--output`: Output file path (defaults to `.cursor/rules/workflow-presets.mdc`)
- `--no-backup`: Skip backing up any existing rules file

**When to Use:**
- After editing workflow YAML
- Keeping Cursor Rules in sync with workflow presets (avoid documentation drift)

---

### `install-dev` - Install Dev Tools (CLI-First)

**Purpose:** Install development tools and dependencies required by TappsCodingAgents (ruff, mypy, pytest, pip-audit, etc.).

**Note:** `pipdeptree` is now optional and moved to the `[dependency-analysis]` extra due to a dependency conflict. See [Installation Troubleshooting](INSTALLATION_TROUBLESHOOTING.md#11-dependency-conflict-pipdeptree-and-packaging-version) for details.

**CLI Syntax:**
```bash
tapps-agents install-dev [--dry-run]
```

**Parameters:**
- `--dry-run`: Preview packages without installing

---

### `hardware-profile` / `hardware` - Hardware Profile (CLI-First)

**Purpose:** Inspect and configure the detected hardware profile used for performance optimization.

**CLI Syntax:**
```bash
tapps-agents hardware-profile [--set auto|nuc|development|workstation|server] [--format json|text] [--no-metrics]
```

**Parameters:**
- `--set`: Override detected profile (or set back to `auto`)
- `--format`: Output format (default: `text`)
- `--no-metrics`: Hide CPU/memory/disk metrics

---

### `analytics` - Analytics Dashboard (CLI-First)

**Purpose:** View analytics and performance metrics for agents and workflows.

**CLI Syntax:**
```bash
tapps-agents analytics <command> [options]
```

**Subcommands:**
- `dashboard` / `show` `[--format json|text]`
- `agents` `[--agent-id <id>] [--format json|text]`
- `workflows` `[--workflow-id <id>] [--format json|text]`
- `trends` `[--metric-type agent_duration|workflow_duration|agent_success_rate|workflow_success_rate] [--days <n>] [--format json|text]`
- `system` `[--format json|text]`

---

### `customize` - Generate Agent Customization Templates (CLI-First)

**Purpose:** Generate customization templates in `.tapps-agents/customizations/` to override default agent behavior without modifying framework code.

**CLI Syntax:**
```bash
tapps-agents customize init <agent_id> [--overwrite]
```

**Parameters:**
- `agent_id` (required): Agent to customize (e.g., `implementer`, `reviewer`, `tester`, `planner`)
- `--overwrite`: Replace an existing customization template

---

### `skill` - Custom Skill Management (CLI-First)

**Purpose:** Validate custom Skills or generate new Skill templates.

**CLI Syntax:**
```bash
tapps-agents skill validate [--skill <path>] [--no-warnings] [--format text|json]
tapps-agents skill template <skill_name> [--type <agent>] [--description "<text>"] [--tools <tools...>] [--capabilities <caps...>] [--model-profile <name>] [--overwrite] [--interactive]
```

---

### `skill-template` - Legacy Skill Template Generator (CLI-First)

**Purpose:** Legacy alias for `tapps-agents skill template ...` (kept for backward compatibility).

**CLI Syntax:**
```bash
tapps-agents skill-template <skill_name> [--type <agent>] [--description "<text>"] [--tools <tools...>] [--capabilities <caps...>] [--model-profile <name>] [--overwrite] [--interactive]
```

---

### `background-agent-config` / `bg-config` - Background Agent Configuration (CLI-First)

**Purpose:** Generate and validate `.cursor/background-agents.yaml` for Cursor Background Agent auto-execution.

**CLI Syntax:**
```bash
tapps-agents background-agent-config generate [--template <path>] [--minimal] [--overwrite] [--config-path <path>]
tapps-agents background-agent-config validate [--config-path <path>] [--format json|text]
```

---

### `governance` / `approval` - Governance Approval Queue (CLI-First)

**Purpose:** Manage the approval queue for knowledge entries before ingestion into the Knowledge Base.

**CLI Syntax:**
```bash
tapps-agents governance list [--format json|text]
tapps-agents governance show <request_id>
tapps-agents governance approve <request_id> [--auto-ingest]
tapps-agents governance reject <request_id> [--reason "<text>"]
```

---

### `auto-execution` / `auto-exec` / `ae` - Auto-Execution Monitoring (CLI-First)

**Purpose:** Monitor and manage Background Agent auto-execution.

**CLI Syntax:**
```bash
tapps-agents auto-execution status [--workflow-id <id>] [--format json|text]
tapps-agents auto-execution history [--workflow-id <id>] [--limit <n>] [--format json|text]
tapps-agents auto-execution metrics [--format json|text]
tapps-agents auto-execution health [--format json|text]
tapps-agents auto-execution debug <on|off|status>
```

---

### `setup-experts` - Industry Experts Setup Wizard (CLI-First)

**Purpose:** Initialize and manage `.tapps-agents/experts.yaml` via an interactive wizard (supports non-interactive automation).

**CLI Syntax:**
```bash
tapps-agents setup-experts [-y|--yes] [--non-interactive] <init|add|remove|list>
```

**Subcommands:**
- `init` / `initialize`: Create `.tapps-agents/experts.yaml` (initial setup)
- `add`: Add a new expert to `.tapps-agents/experts.yaml`
- `remove`: Remove an expert from `.tapps-agents/experts.yaml`
- `list`: List currently configured experts

**Parameters:**
- `-y` / `--yes`: Auto-confirm prompts
- `--non-interactive`: Never prompt; use defaults where possible and error if input is required

---

### `cursor` - Cursor Integration Verification (CLI-First)

**Purpose:** Verify Cursor Skills, Cursor Rules, and Background Agents are installed and configured correctly.

**CLI Syntax:**
```bash
tapps-agents cursor verify [--format json|text]
```

## Epic Commands (New)

### `*epic` - Execute Epic Workflow (Cursor-First)

**Purpose:** Execute all stories in an Epic document in dependency order with progress tracking and quality gates.

**Cursor Syntax:**
```cursor
@simple-mode *epic docs/prd/epic-51-yaml-automation-quality-enhancement.md
@simple-mode *epic epic-8-automated-documentation-generation.md
```

**Parameters:**
- `epic_path` (required): Path to Epic markdown document
- `--quality-threshold`: Minimum quality score (default: 70)
- `--critical-service-threshold`: Minimum for critical services (default: 80)
- `--enforce-quality-gates`: Enable quality gate enforcement (default: true)
- `--auto-mode`: Fully automated execution
- `--max-iterations`: Maximum quality loopback iterations (default: 3)

**Features:**
- Parses Epic documents to extract stories and dependencies
- Executes stories in topological order (dependency resolution)
- Tracks progress across all stories
- Enforces quality gates with automatic loopback
- Generates Epic completion report

**Example:**
```cursor
@simple-mode *epic docs/prd/epic-51-yaml-automation-quality-enhancement.md
```

**Output:**
- Execution report with completion percentage
- Story-by-story results
- Quality gate status
- Report saved to `docs/prd/epic-{number}-report.json`

---

## Coverage-Driven Test Commands (New)

### `*test-coverage` - Coverage-Driven Test Generation (Cursor-First)

**Purpose:** Generate tests targeting specific uncovered code paths identified by coverage analysis.

**Cursor Syntax:**
```cursor
@simple-mode *test-coverage <file> --target 80
@tester analyze-coverage coverage.json --target 80 --generate-tests
```

**CLI Syntax:**
```bash
tapps-agents tester analyze-coverage <coverage.json> [--target <percentage>] [--generate-tests] [--module <path>]
tapps-agents tester generate-coverage-tests <coverage.json> [--module <path>] [--target-coverage <percentage>] [--focus-uncovered]
```

**Parameters:**
- `coverage.json` (required): Path to coverage.json file
- `--target`: Target coverage percentage (default: 80)
- `--generate-tests`: Automatically generate tests for gaps
- `--module`: Optional module path to focus on
- `--focus-uncovered`: Only generate tests for uncovered code

**Features:**
- Analyzes coverage.json to identify gaps
- Prioritizes gaps (critical paths, error handling, public APIs)
- Generates targeted tests for uncovered code
- Verifies coverage improvement after generation

**Example:**
```bash
# Analyze coverage and generate tests
tapps-agents tester analyze-coverage coverage.json --target 80 --generate-tests

# Generate tests for specific module
tapps-agents tester generate-coverage-tests coverage.json --module src/clients --target-coverage 80
```

### `*fix-tests` - Test Failure Auto-Fix (Cursor-First)

**Purpose:** Analyze test failures and automatically fix common patterns.

**Cursor Syntax:**
```cursor
@simple-mode *fix-tests <test-file>
```

**CLI Syntax:**
```bash
tapps-agents tester fix-failures <test-dir> [--pattern <pattern>] [--auto-fix]
```

**Parameters:**
- `test-dir` (required): Test directory or file
- `--pattern`: Filter by pattern (async, auth, mock, import)
- `--auto-fix`: Automatically apply fixes (default: false)

**Supported Patterns:**
- `async`: TestClient → AsyncClient migration, missing await
- `auth`: Authentication header issues
- `mock`: Mock configuration errors
- `import`: Import path issues

**Example:**
```bash
# Fix async/await issues
tapps-agents tester fix-failures tests/ --pattern async --auto-fix

# Fix all patterns with auto-fix
tapps-agents tester fix-failures tests/ --auto-fix
```

---

## Microservice Commands (New)

### `*microservice` - Generate Microservice (Cursor-First)

**Purpose:** Generate complete microservice structure with Docker, tests, and health checks.

**Cursor Syntax:**
```cursor
@simple-mode *microservice <name> --port <port> --type <fastapi|flask|homeiq>
```

**CLI Syntax:**
```bash
tapps-agents create-microservice <name> [--port <port>] [--type <fastapi|flask|homeiq>] [--features <list>]
```

**Parameters:**
- `name` (required): Service name
- `--port`: Port number (default: 8000)
- `--type`: Service type - `fastapi` (default), `flask`, or `homeiq`
- `--features`: Comma-separated list of features (validation, normalization, etc.)

**What It Generates:**
- Service structure (`src/`, `tests/`, `Dockerfile`, `requirements.txt`)
- Docker Compose integration
- Health check endpoints
- Logging configuration
- API router structure
- Test scaffolding
- README with service docs

**Example:**
```bash
# Generate FastAPI service
tapps-agents create-microservice yaml-validation-service --port 8037 --type fastapi

# Generate HomeIQ service with features
tapps-agents create-microservice data-service --port 8040 --type homeiq --features validation,normalization
```

---

## Docker Commands (New)

### `*docker-fix` - Container Debugging (Cursor-First)

**Purpose:** Debug container errors with automatic fix suggestions.

**Cursor Syntax:**
```cursor
@simple-mode *docker-fix <service> "<error>"
```

**CLI Syntax:**
```bash
tapps-agents debugger docker-fix <service> [--error "<error>"] [--auto-fix]
```

**Parameters:**
- `service` (required): Service/container name
- `--error`: Error message (if not provided, checks container logs)
- `--auto-fix`: Automatically apply fixes with high confidence (>95%)

**Features:**
- Analyzes container logs
- Matches errors to known patterns
- Checks Dockerfile for issues
- Suggests fixes with confidence scores
- Auto-applies high-confidence fixes

**Example:**
```bash
# Debug service error
tapps-agents debugger docker-fix device-intelligence-service --error "ModuleNotFoundError: No module named 'src'"

# Auto-fix with high confidence
tapps-agents debugger docker-fix device-intelligence-service --auto-fix
```

### Dockerfile Analysis

**CLI Syntax:**
```bash
tapps-agents docker analyze <Dockerfile> [--suggest-fixes]
```

**What It Detects:**
- `ModuleNotFoundError: No module named 'src'` (WORKDIR/Python path)
- COPY before WORKDIR
- Missing `python -m` prefix for uvicorn
- Incorrect PYTHONPATH

**Example:**
```bash
tapps-agents docker analyze services/device-intelligence-service/Dockerfile --suggest-fixes
```

---

## Service Integration Commands (New)

### `*integrate-service` - Service Integration (Cursor-First)

**Purpose:** Automate service-to-service integration (client classes, config, DI).

**Cursor Syntax:**
```cursor
@simple-mode *integrate-service <service1> --with <service2>
```

**CLI Syntax:**
```bash
tapps-agents integrate-service <service1> --with <service2>
```

**What It Does:**
- Generates HTTP client classes for target service
- Updates config files with service URLs
- Adds dependency injection setup
- Updates docker-compose.yml with service dependencies
- Generates integration tests
- Updates API documentation

**Example:**
```bash
# Integrate yaml-validation-service with ai-automation-service-new
tapps-agents integrate-service ai-automation-service-new --with yaml-validation-service
```

---

## Agent Commands

**CLI Note:** Every agent supports `help` (and the CLI-only alias `*help`) to list its available subcommands:

```bash
tapps-agents <agent> help
tapps-agents <agent> *help
```

**Cursor Note:** Only some Cursor Skills explicitly document `*help` (notably `@reviewer` and `@simple-mode`). For other agents, use the documented `@agent *command` list in the corresponding `tapps_agents/resources/claude/skills/<agent>/SKILL.md`.

### Reviewer Agent

**Purpose:** Code review and quality analysis with objective metrics.

#### `reviewer review` / `*review` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents reviewer review [<files>...] [--pattern <glob>] [--max-workers <n>] [--format json|text|markdown|html] [--output <file>]
```

**Cursor Syntax:**
```cursor
@reviewer *review <file>
```

**Parameters:**
- `files` (optional): One or more file paths (supports multiple files)
- `--pattern`: Glob pattern to match files (e.g., `**/*.py`)
- `--max-workers`: Concurrent file operations (default: 4)
- `--format`: Output format (default: `json`)
- `--output`: Output file path

**When to Use:**
- Comprehensive code review with AI analysis
- Pre-commit quality checks
- Code quality audits

**Example:**
```bash
tapps-agents reviewer review src/app.py
tapps-agents reviewer review src/app.py --format text
tapps-agents reviewer review file1.py file2.py file3.py
tapps-agents reviewer review --pattern "**/*.py" --max-workers 8
```

---

#### `reviewer score` / `*score` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents reviewer score [<files>...] [--pattern <glob>] [--max-workers <n>] [--format json|text|markdown|html] [--output <file>]
```

**Cursor Syntax:**
```cursor
@reviewer *score <file>
```

**Parameters:** Same as `review`

**When to Use:**
- Fast objective quality metrics (no LLM feedback)
- CI/CD quality gates
- Quick quality screening

**Example:**
```bash
tapps-agents reviewer score src/utils.py
tapps-agents reviewer score src/utils.py --format text
```

---

#### `reviewer lint` / `*lint` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents reviewer lint [<files>...] [--pattern <glob>] [--max-workers <n>] [--format json|text] [--output <file>]
```

**Cursor Syntax:**
```cursor
@reviewer *lint <file>
```

**Parameters:** Similar to `review`, but format limited to `json` or `text`

**When to Use:**
- PEP 8 style violations
- Code style enforcement
- Pre-commit hooks

**Example:**
```bash
tapps-agents reviewer lint src/main.py
tapps-agents reviewer lint src/main.py --format text
```

---

#### `reviewer type-check` / `*type-check` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents reviewer type-check [<files>...] [--pattern <glob>] [--max-workers <n>] [--format json|text] [--output <file>]
```

**Cursor Syntax:**
```cursor
@reviewer *type-check <file>
```

**When to Use:**
- Type annotation validation
- Static type checking
- Type safety verification

**Example:**
```bash
tapps-agents reviewer type-check src/models.py
tapps-agents reviewer type-check src/models.py --format text
```

---

#### `reviewer report` / `*report` (CLI-First)

**CLI Syntax:**
```bash
tapps-agents reviewer report <target> <formats>... [--output-dir <dir>]
```

**Parameters:**
- `target` (required): File or directory path
- `formats` (required): One or more of `json`, `markdown`, `html`, `all`
- `--output-dir`: Directory for reports (default: `reports/quality/`)

**When to Use:**
- Comprehensive project-wide quality reports
- Documentation generation
- Quality trend analysis

**Example:**
```bash
tapps-agents reviewer report src/ json markdown
tapps-agents reviewer report src/ all --output-dir reports/
```

---

#### `reviewer duplication` / `*duplication` (CLI-First)

**CLI Syntax:**
```bash
tapps-agents reviewer duplication <target> [--format json|text]
```

**When to Use:**
- Code duplication detection
- Refactoring opportunities
- Maintainability analysis

**Example:**
```bash
tapps-agents reviewer duplication src/
tapps-agents reviewer duplication src/utils.py --format text
```

---

#### `reviewer analyze-project` / `*analyze-project` (CLI-First)

**CLI Syntax:**
```bash
tapps-agents reviewer analyze-project [--project-root <path>] [--no-comparison] [--format json|text]
```

**When to Use:**
- Comprehensive project analysis
- Quality trend tracking
- Baseline establishment

**Example:**
```bash
tapps-agents reviewer analyze-project
tapps-agents reviewer analyze-project --project-root /path/to/project --format json
```

---

#### `reviewer analyze-services` / `*analyze-services` (CLI-First)

**CLI Syntax:**
```bash
tapps-agents reviewer analyze-services [<services>...] [--project-root <path>] [--no-comparison] [--format json|text]
```

**When to Use:**
- Targeted service/module analysis
- Large project optimization
- Service-specific quality checks

**Example:**
```bash
tapps-agents reviewer analyze-services api auth
tapps-agents reviewer analyze-services --project-root /path/to/project
```

---

#### `reviewer *docs` (Cursor-First)

**Cursor Syntax:**
```cursor
@reviewer *docs <library> [topic]
```

**Purpose:** Get library documentation from Context7 KB cache.

**When to Use:**
- Library API reference lookup
- Best practices research
- Integration guidance

**Example:**
```cursor
@reviewer *docs fastapi routing
@reviewer *docs pytest fixtures
```

---

### Implementer Agent

**Purpose:** Code generation and refactoring.

#### `implementer implement` / `*implement` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents implementer implement "<specification>" <file_path> [--context "<context>"] [--language <lang>] [--output <file>] [--format json|text|markdown]
```

**Cursor Syntax:**
```cursor
@implementer *implement "<specification>" <file_path>
```

**Parameters:**
- `specification` (required): Detailed specification of what to implement
- `file_path` (required): Target file path
- `--context`: Additional context (patterns, dependencies, constraints)
- `--language`: Programming language (default: `python`)
- `--output`: Output file path
- `--format`: Output format (default: `json`)

**When to Use:**
- Generate new code from specifications
- Implement features
- Create new modules

**Example:**
```bash
tapps-agents implementer implement "Create a User model with email and name fields" src/models/user.py
tapps-agents implementer implement "Add authentication endpoint" src/api/auth.py --context "Use JWT tokens"
```

---

#### `implementer generate-code` / `*generate-code` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents implementer generate-code "<specification>" [--file <path>] [--context "<context>"] [--language <lang>] [--output <file>] [--format json|text|markdown]
```

**Cursor Syntax:**
```cursor
@implementer *generate-code "<specification>" [--file <path>]
```

**When to Use:**
- Preview code before writing
- Generate code snippets
- Test specifications

**Example:**
```bash
tapps-agents implementer generate-code "Create a function to validate email addresses"
tapps-agents implementer generate-code "Add error handling" --file src/api.py
```

---

#### `implementer refactor` / `*refactor` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents implementer refactor <file_path> "<instruction>" [--output <file>] [--format json|text|markdown|diff]
```

**Cursor Syntax:**
```cursor
@implementer *refactor <file_path> "<instruction>"
```

**Parameters:**
- `file_path` (required): Source file to refactor
- `instruction` (required): Detailed refactoring instruction
- `--output`: Output file path
- `--format`: Output format (default: `json`)

**When to Use:**
- Code structure improvement
- Design pattern application
- Code smell fixes

**Example:**
```bash
tapps-agents implementer refactor src/utils.py "Extract common logic into helper functions"
tapps-agents implementer refactor src/api.py "Apply dependency injection pattern"
```

---

### Tester Agent

**Purpose:** Test generation and execution.

#### `tester test` / `*test` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents tester test <file> [--test-file <path>] [--integration] [--output <file>] [--format json|text|markdown]
```

**Cursor Syntax:**
```cursor
@tester *test <file>
```

**Parameters:**
- `file` (required): Source code file to test
- `--test-file`: Path for generated test file
- `--integration`: Generate integration tests too
- `--output`: Output file path
- `--format`: Output format (default: `json`)

**When to Use:**
- Generate and run tests immediately
- Test-driven development
- Comprehensive test coverage

**Example:**
```bash
tapps-agents tester test src/utils.py
tapps-agents tester test src/api.py --test-file tests/test_api.py --integration
```

---

#### `tester generate-tests` / `*generate-tests` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents tester generate-tests <file> [--test-file <path>] [--integration] [--output <file>] [--format json|text|markdown]
```

**Cursor Syntax:**
```cursor
@tester *generate-tests <file>
```

**When to Use:**
- Generate tests without running
- Review tests before execution
- Batch test generation

**Example:**
```bash
tapps-agents tester generate-tests src/models.py
tapps-agents tester generate-tests src/api.py --test-file tests/test_api.py
```

---

#### `tester run-tests` / `*run-tests` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents tester run-tests [<test_path>] [--no-coverage] [--output <file>] [--format json|text|markdown]
```

**Cursor Syntax:**
```cursor
@tester *run-tests [path]
```

**Parameters:**
- `test_path` (optional): Test file, directory, or pattern (default: `tests/`)
- `--no-coverage`: Skip coverage analysis
- `--output`: Output file path
- `--format`: Output format (default: `json`)

**When to Use:**
- Run existing test suites
- CI/CD test execution
- Coverage reporting

**Example:**
```bash
tapps-agents tester run-tests
tapps-agents tester run-tests tests/unit/
tapps-agents tester run-tests --no-coverage
```

---

### Debugger Agent

**Purpose:** Error debugging and code analysis.

#### `debugger debug` / `*debug` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents debugger debug "<error_message>" [--file <path>] [--line <n>] [--stack-trace <file|text>] [--output <file>] [--format json|text|markdown]
```

**Cursor Syntax:**
```cursor
@debugger *debug "<error_message>" --file <file> [--line <n>]
```

**Parameters:**
- `error_message` (required): Error message or exception text
- `--file`: Source file where error occurred
- `--line`: Line number where error occurred
- `--stack-trace`: Stack trace file or text
- `--output`: Output file path
- `--format`: Output format (default: `json`)

**When to Use:**
- Debug runtime errors
- Analyze exceptions
- Root cause identification

**Example:**
```bash
tapps-agents debugger debug "KeyError: 'user_id'" --file src/api.py --line 42
tapps-agents debugger debug "Connection timeout" --stack-trace traceback.txt
```

---

#### `debugger analyze-error` / `*analyze-error` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents debugger analyze-error "<error_message>" [--stack-trace <file|text>] [--code-context "<context>"] [--output <file>] [--format json|text|markdown]
```

**When to Use:**
- In-depth error analysis
- Error pattern identification
- Prevention strategies

**Example:**
```bash
tapps-agents debugger analyze-error "ValueError: invalid literal" --stack-trace traceback.txt
```

---

#### `debugger trace` / `*trace` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents debugger trace <file> [--function <name>] [--line <n>] [--output <file>] [--format json|text|markdown]
```

**Cursor Syntax:**
```cursor
@debugger *trace <file>
```

**When to Use:**
- Code execution path analysis
- Control flow understanding
- Logic error identification

**Example:**
```bash
tapps-agents debugger trace src/api.py --function authenticate_user
```

---

### Planner Agent

**Purpose:** Project planning and task breakdown.

#### `planner plan` / `*plan` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents planner plan "<description>" [--output <file>] [--format json|text|markdown]
```

**Cursor Syntax:**
```cursor
@planner *plan "<description>"
```

**Parameters:**
- `description` (required): Feature or requirement description
- `--output`: Output file path
- `--format`: Output format (default: `json`)

**When to Use:**
- Feature planning
- Task breakdown
- Implementation strategy

**Example:**
```bash
tapps-agents planner plan "Add user authentication with OAuth"
tapps-agents planner plan "Implement shopping cart" --format text
```

---

#### `planner create-story` / `*create-story` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents planner create-story "<description>" [--epic <name>] [--priority high|medium|low] [--output <file>] [--format json|text|markdown]
```

**Cursor Syntax:**
```cursor
@planner *create-story "<description>" [--epic <name>] [--priority <level>]
```

**Parameters:**
- `description` (required): User story description
- `--epic`: Epic name or feature area
- `--priority`: Priority level (default: `medium`)
- `--output`: Output file path
- `--format`: Output format (default: `json`)

**When to Use:**
- User story creation
- Agile planning
- Feature organization

**Example:**
```bash
tapps-agents planner create-story "User login functionality"
tapps-agents planner create-story "Export data to CSV" --epic "Data Management" --priority high
```

---

#### `planner list-stories` / `*list-stories` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents planner list-stories [--epic <name>] [--status <status>] [--output <file>] [--format json|text|markdown]
```

**Cursor Syntax:**
```cursor
@planner *list-stories [--epic <name>] [--status <status>]
```

**When to Use:**
- Story management
- Progress tracking
- Epic organization

**Example:**
```bash
tapps-agents planner list-stories
tapps-agents planner list-stories --epic "Authentication" --status todo
```

---

### Enhancer Agent

**Purpose:** Prompt enhancement and specification generation.

#### `enhancer enhance` / `*enhance` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents enhancer enhance "<prompt>" [--format markdown|json|yaml] [--output <file>] [--config <path>]
```

**Cursor Syntax:**
```cursor
@enhancer *enhance "<prompt>"
```

**Parameters:**
- `prompt` (required): Initial prompt to enhance
- `--format`: Output format (default: `markdown`)
- `--output`: Output file path
- `--config`: Custom enhancement configuration

**When to Use:**
- Transform vague requirements into detailed specs
- Full enhancement pipeline (all 7 stages)
- Comprehensive specification generation

**Example:**
```bash
tapps-agents enhancer enhance "Build a todo app"
tapps-agents enhancer enhance "Add user authentication" --format json
```

---

#### `enhancer enhance-quick` / `*enhance-quick` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents enhancer enhance-quick "<prompt>" [--format markdown|json|yaml] [--output <file>]
```

**When to Use:**
- Faster enhancement (stages 1-3 only)
- Initial planning
- Quick specification generation

**Example:**
```bash
tapps-agents enhancer enhance-quick "Add user authentication"
```

---

#### `enhancer enhance-stage` / `*enhance-stage` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents enhancer enhance-stage <stage> [--prompt "<prompt>"] [--session-id <id>]
```

**Cursor Syntax:**
```cursor
@enhancer *enhance-stage <stage> "<prompt>"
```

**Stages:** `analysis`, `requirements`, `architecture`, `implementation`, `testing`, `documentation`

**When to Use:**
- Run specific enhancement stage
- Continue from saved session
- Stage-by-stage enhancement

**Example:**
```bash
tapps-agents enhancer enhance-stage architecture --prompt "Build todo app"
```

---

#### `enhancer enhance-resume` / `*enhance-resume` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents enhancer enhance-resume <session_id>
```

**Cursor Syntax:**
```cursor
@enhancer *enhance-resume <session_id>
```

**When to Use:**
- Resume interrupted enhancement
- Continue after manual review
- Re-run stages with modifications

**Example:**
```bash
tapps-agents enhancer enhance-resume session_abc123
```

---

### Architect Agent

**Purpose:** System architecture and design.

#### `architect design-system` / `*design-system` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents architect design-system "<requirements>" [--context "<context>"] [--output <file>] [--format json|text|markdown]
```

**Cursor Syntax:**
```cursor
@architect *design-system "<requirements>"
```

**When to Use:**
- System architecture design
- Component design
- Technology stack selection

**Example:**
```bash
tapps-agents architect design-system "Microservices e-commerce platform"
tapps-agents architect design-system "Real-time chat application" --output docs/architecture.md
```

---

#### `architect architecture-diagram` / `*architecture-diagram` (CLI-First)

**CLI Syntax:**
```bash
tapps-agents architect architecture-diagram "<description>" [--diagram-type component|sequence|deployment] [--output <file>] [--format json|text|markdown]
```

**When to Use:**
- Visual architecture diagrams
- Component relationships
- Deployment architecture

**Example:**
```bash
tapps-agents architect architecture-diagram "User authentication flow" --diagram-type sequence
```

---

#### `architect tech-selection` / `*tech-selection` (CLI-First)

**CLI Syntax:**
```bash
tapps-agents architect tech-selection "<component_description>" [--requirements "<reqs>"] [--constraints <constraints>...]
```

**When to Use:**
- Technology decision-making
- Component technology selection
- Stack evaluation

**Example:**
```bash
tapps-agents architect tech-selection "Message queue for real-time notifications" --requirements "must support horizontal scaling"
```

---

#### `architect design-security` / `*design-security` (CLI-First)

**CLI Syntax:**
```bash
tapps-agents architect design-security "<system_description>" [--threat-model "<model>"]
```

**When to Use:**
- Security architecture design
- Threat mitigation
- Compliance planning

**Example:**
```bash
tapps-agents architect design-security "User authentication system" --threat-model "SQL injection, XSS"
```

---

#### `architect define-boundaries` / `*define-boundaries` (CLI-First)

**CLI Syntax:**
```bash
tapps-agents architect define-boundaries "<system_description>" [--context "<context>"]
```

**When to Use:**
- System boundary definition
- Interface contracts
- Integration points

**Example:**
```bash
tapps-agents architect define-boundaries "Microservices architecture" --context "Existing monolith integration"
```

---

### Designer Agent

**Purpose:** API, data model, and UI/UX design.

#### `designer api-design` / `*api-design` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents designer api-design "<requirements>" [--api-type REST|GraphQL|gRPC] [--output <file>] [--format json|text|markdown]
```

**Cursor Syntax:**
```cursor
@designer *design-api "<requirements>" [--api-type <type>]
```

**When to Use:**
- API specification design
- REST/GraphQL/gRPC design
- Endpoint planning

**Example:**
```bash
tapps-agents designer api-design "User management API with CRUD operations"
tapps-agents designer api-design "Product catalog API" --api-type GraphQL --output docs/api-spec.yaml
```

---

#### `designer data-model-design` / `*data-model-design` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents designer data-model-design "<requirements>" [--data-source <source>] [--output <file>] [--format json|text|markdown]
```

**When to Use:**
- Database schema design
- Data model design
- Entity relationship design

**Example:**
```bash
tapps-agents designer data-model-design "User, Post, Comment entities with relationships" --data-source PostgreSQL
```

---

#### `designer ui-ux-design` / `*ui-ux-design` (CLI-First)

**CLI Syntax:**
```bash
tapps-agents designer ui-ux-design "<feature_description>" [--user-stories <stories>...] [--output <file>] [--format json|text|markdown]
```

**When to Use:**
- UI/UX design specifications
- User experience design
- Accessibility planning

**Example:**
```bash
tapps-agents designer ui-ux-design "User dashboard with analytics" --user-stories "As a user, I want to see my stats"
```

---

#### `designer wireframes` / `*wireframes` (CLI-First)

**CLI Syntax:**
```bash
tapps-agents designer wireframes "<screen_description>" [--wireframe-type page|component|flow] [--output <file>] [--format json|text|markdown]
```

**When to Use:**
- Wireframe generation
- Layout design
- Component placement

**Example:**
```bash
tapps-agents designer wireframes "Login page with email and password fields" --wireframe-type page
```

---

#### `designer design-system` / `*design-system` (CLI-First)

**CLI Syntax:**
```bash
tapps-agents designer design-system "<project_description>" [--brand-guidelines "<guidelines>"] [--output <file>] [--format json|text|markdown]
```

**When to Use:**
- Design system creation
- Component library design
- Style guide development

**Example:**
```bash
tapps-agents designer design-system "E-commerce platform" --brand-guidelines "Blue and white color scheme"
```

---

### Documenter Agent

**Purpose:** Documentation generation.

#### `documenter document` / `*document` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents documenter document <file> [--output-format markdown|rst|html] [--output <file>]
```

**Cursor Syntax:**
```cursor
@documenter *document <file>
```

**When to Use:**
- Code documentation generation
- Function/class documentation
- Usage examples

**Example:**
```bash
tapps-agents documenter document src/utils.py
tapps-agents documenter document src/api.py --output-format html --output docs/api.html
```

---

#### `documenter generate-docs` / `*generate-docs` (CLI-First)

**CLI Syntax:**
```bash
tapps-agents documenter generate-docs <file> [--output <file>] [--output-format markdown|rst|html|openapi]
```

**When to Use:**
- API documentation generation
- OpenAPI/Swagger generation
- Endpoint documentation

**Example:**
```bash
tapps-agents documenter generate-docs src/api/routes.py --output-format openapi
```

---

#### `documenter update-readme` / `*update-readme` (CLI-First)

**CLI Syntax:**
```bash
tapps-agents documenter update-readme [--project-root <path>] [--context "<context>"]
```

**When to Use:**
- README generation/updates
- Project documentation
- Setup instructions

**Example:**
```bash
tapps-agents documenter update-readme
tapps-agents documenter update-readme --project-root /path/to/project
```

---

#### `documenter update-docstrings` / `*update-docstrings` (CLI-First)

**CLI Syntax:**
```bash
tapps-agents documenter update-docstrings <file> [--docstring-format google|numpy|sphinx] [--write-file]
```

**When to Use:**
- Add missing docstrings
- Update outdated docstrings
- Ensure consistent format

**Example:**
```bash
tapps-agents documenter update-docstrings src/utils.py --docstring-format google --write-file
```

---

### Ops Agent

**Purpose:** DevOps and operations tasks.

#### `ops security-scan` / `*security-scan` (Dual-Mode)

**CLI Syntax:**
```bash
tapps-agents ops security-scan [--target <path>] [--type all|sql_injection|xss|secrets|...]
```

**Cursor Syntax:**
```cursor
@ops *security-scan [--target <path>]
```

**When to Use:**
- Security vulnerability scanning
- Pre-deployment security checks
- Security audits

**Example:**
```bash
tapps-agents ops security-scan
tapps-agents ops security-scan --target src/api/ --type sql_injection
```

---

#### `ops compliance-check` / `*compliance-check` (CLI-First)

**CLI Syntax:**
```bash
tapps-agents ops compliance-check [--type general|GDPR|HIPAA|SOC2|all]
```

**When to Use:**
- Regulatory compliance validation
- GDPR/HIPAA/SOC2 checks
- Compliance audits

**Example:**
```bash
tapps-agents ops compliance-check --type GDPR
tapps-agents ops compliance-check --type all
```

---

#### `ops deploy` / `*deploy` (CLI-First)

**CLI Syntax:**
```bash
tapps-agents ops deploy [--target local|staging|production] [--environment <name>]
```

**When to Use:**
- Application deployment
- Environment management
- Deployment automation

**Example:**
```bash
tapps-agents ops deploy --target staging
tapps-agents ops deploy --environment production
```

---

#### `ops infrastructure-setup` / `*infrastructure-setup` (CLI-First)

**CLI Syntax:**
```bash
tapps-agents ops infrastructure-setup [--type docker|kubernetes|terraform]
```

**When to Use:**
- Infrastructure configuration
- Docker/Kubernetes setup
- Terraform generation

**Example:**
```bash
tapps-agents ops infrastructure-setup --type docker
tapps-agents ops infrastructure-setup --type kubernetes
```

---

#### `ops audit-dependencies` / `*audit-dependencies` (CLI-First)

**CLI Syntax:**
```bash
tapps-agents ops audit-dependencies [--severity-threshold low|medium|high|critical] [--output <file>] [--format json|text|markdown]
```

**When to Use:**
- Dependency vulnerability auditing
- Security dependency checks
- Dependency risk assessment

**Example:**
```bash
tapps-agents ops audit-dependencies --severity-threshold high
tapps-agents ops audit-dependencies --format markdown
```

---

## Additional Commands

### `analyst` Agent

**Purpose:** Requirements gathering and analysis.

**CLI Commands (source: `tapps_agents/cli/parsers/analyst.py`):**
- `analyst gather-requirements` / `*gather-requirements`  
  - **Syntax:** `tapps-agents analyst gather-requirements "<description>" [--context "<text>"] [--output <path>] [--format json|text|markdown] [--no-enhance] [--enhance] [--enhance-mode quick|full]`
- `analyst stakeholder-analysis` / `*stakeholder-analysis`  
  - **Syntax:** `tapps-agents analyst stakeholder-analysis "<description>" [--stakeholders <s...>]`
- `analyst tech-research` / `*tech-research`  
  - **Syntax:** `tapps-agents analyst tech-research "<requirement>" [--context "<text>"] [--criteria <c...>]`
- `analyst estimate-effort` / `*estimate-effort`  
  - **Syntax:** `tapps-agents analyst estimate-effort "<feature_description>" [--context "<text>"]`
- `analyst assess-risk` / `*assess-risk`  
  - **Syntax:** `tapps-agents analyst assess-risk "<feature_description>" [--context "<text>"]`
- `analyst competitive-analysis` / `*competitive-analysis`  
  - **Syntax:** `tapps-agents analyst competitive-analysis "<product_description>" [--competitors <c...>]`

### `improver` Agent

**Purpose:** Code improvement and refactoring.

**CLI Commands (source: `tapps_agents/cli/parsers/improver.py`):**
- `improver refactor` / `*refactor`  
  - **Syntax:** `tapps-agents improver refactor <file_path> [--instruction "<text>"] [--output <path>] [--format json|text|markdown]`
- `improver optimize` / `*optimize`  
  - **Syntax:** `tapps-agents improver optimize <file_path> [--type performance|memory|both] [--output <path>] [--format json|text|markdown]`
- `improver improve-quality` / `*improve-quality`  
  - **Syntax:** `tapps-agents improver improve-quality <file_path> [--focus "<areas>"] [--output <path>] [--format json|text|markdown]`
  - **Parameters:**
    - `--focus`: Comma-separated list of quality aspects to focus on (e.g., `"security, maintainability, type-safety"`). If not provided, performs comprehensive quality improvement.

**Cursor Skill Note (source: `tapps_agents/resources/claude/skills/improver/SKILL.md`):**
- The Skill supports `@improver *improve` as an alias to `*refactor`. The CLI does **not** provide an `improver improve` subcommand.

### `orchestrator` Agent

**Purpose:** Workflow orchestration and coordination.

**CLI Commands (source: `tapps_agents/cli/parsers/orchestrator.py`):**
- `orchestrator workflow-list` / `*workflow-list` (subcommand: `workflow-list`)  
  - **Syntax:** `tapps-agents orchestrator workflow-list`
- `orchestrator workflow-start <workflow_id>` / `*workflow-start <workflow_id>` (subcommand: `workflow-start`)  
  - **Syntax:** `tapps-agents orchestrator workflow-start <workflow_id>`
- `orchestrator workflow-status` / `*workflow-status` (subcommand: `workflow-status`)  
  - **Syntax:** `tapps-agents orchestrator workflow-status`
- `orchestrator workflow-next` / `*workflow-next` (subcommand: `workflow-next`)  
  - **Syntax:** `tapps-agents orchestrator workflow-next`
- `orchestrator workflow-skip <step_id>` / `*workflow-skip <step_id>` (subcommand: `workflow-skip`)  
  - **Syntax:** `tapps-agents orchestrator workflow-skip <step_id>`
- `orchestrator workflow-resume` / `*workflow-resume` (subcommand: `workflow-resume`)  
  - **Syntax:** `tapps-agents orchestrator workflow-resume`
- `orchestrator gate` / `*gate`  
  - **Syntax:** `tapps-agents orchestrator gate [--condition \"<expr>\"] [--scoring-data \"<json>\"]`
- `orchestrator help` / `*help`  
  - **Syntax:** `tapps-agents orchestrator help`

---

## Recommended Command Combinations

### New Feature Development

**Full Workflow (CLI):**
```bash
# 1. Enhance requirements
tapps-agents enhancer enhance "Add user authentication" --format markdown

# 2. Create plan
tapps-agents planner plan "User authentication with JWT tokens"

# 3. Design architecture
tapps-agents architect design-system "User authentication system"

# 4. Design API
tapps-agents designer api-design "Authentication API with login, logout, refresh"

# 5. Implement
tapps-agents implementer implement "JWT authentication service" src/auth/service.py

# 6. Review
tapps-agents reviewer review src/auth/service.py

# 7. Test
tapps-agents tester test src/auth/service.py --integration
```

**Simple Mode (Cursor):**
```cursor
@simple-mode *build "Add user authentication with JWT tokens"
```

**Workflow Preset (CLI):**
```bash
tapps-agents workflow rapid --prompt "Add user authentication" --auto
```

---

### Bug Fix Workflow

**CLI:**
```bash
# 1. Debug
tapps-agents debugger debug "KeyError: 'user_id'" --file src/api.py --line 42

# 2. Fix
tapps-agents implementer refactor src/api.py "Fix KeyError by adding default value"

# 3. Test
tapps-agents tester test src/api.py

# 4. Review
tapps-agents reviewer review src/api.py
```

**Simple Mode (Cursor):**
```cursor
@simple-mode *fix src/api.py "Fix the KeyError on line 42"
```

**Workflow Preset (CLI):**
```bash
tapps-agents workflow fix --file src/api.py --auto
```

---

### Quality Improvement Sprint

**CLI:**
```bash
# 1. Analyze project
tapps-agents reviewer analyze-project

# 2. Generate quality report
tapps-agents reviewer report src/ json markdown html

# 3. Improve code
tapps-agents workflow quality --file src/legacy_code.py --auto

# 4. Verify improvements
tapps-agents reviewer score src/legacy_code.py
```

**Simple Mode (Cursor):**
```cursor
@simple-mode *review src/legacy_code.py
@improver *improve src/legacy_code.py "Address all issues from review"
```

---

### Pre-Commit Quality Checks

**CLI:**
```bash
# Quick checks
tapps-agents reviewer score src/changed_file.py
tapps-agents reviewer lint src/changed_file.py
tapps-agents reviewer type-check src/changed_file.py

# Full review
tapps-agents reviewer review src/changed_file.py --format text
```

**Cursor:**
```cursor
@reviewer *score src/changed_file.py
@reviewer *lint src/changed_file.py
@reviewer *review src/changed_file.py
```

---

## Cursor vs CLI Usage Guide

### When to Use Cursor (Cursor-First)

**Use Cursor when:**
- ✅ Interactive development
- ✅ Natural language commands
- ✅ Learning the framework
- ✅ Quick code reviews
- ✅ Iterative development
- ✅ Using Simple Mode
- ✅ Background Agent automation

**Advantages:**
- Natural language interaction
- Context-aware (file open, selection)
- Integrated with IDE
- Background Agent support
- Skill-based execution

**Example:**
```cursor
@reviewer *review src/api.py
@implementer *implement "Add rate limiting" src/api/middleware.py
@simple-mode Build a user authentication feature
```

---

### When to Use CLI (CLI-First)

**Use CLI when:**
- ✅ Batch processing
- ✅ CI/CD pipelines
- ✅ Scripting/automation
- ✅ Headless environments
- ✅ Structured output (JSON)
- ✅ Project-wide analysis
- ✅ Workflow presets

**Advantages:**
- Scriptable and automatable
- Structured output formats
- Batch file processing
- CI/CD integration
- Workflow state management

**Example:**
```bash
# Batch processing
tapps-agents reviewer review --pattern "**/*.py" --max-workers 8

# CI/CD
tapps-agents reviewer score src/ --format json > quality-report.json

# Workflow automation
tapps-agents workflow full --prompt "Build API" --auto
```

---

### Dual-Mode Commands

**These commands work in both modes:**

| Command | Cursor Syntax | CLI Syntax |
|---------|---------------|------------|
| Review | `@reviewer *review <file>` | `tapps-agents reviewer review <file>` |
| Score | `@reviewer *score <file>` | `tapps-agents reviewer score <file>` |
| Implement | `@implementer *implement "<spec>" <file>` | `tapps-agents implementer implement "<spec>" <file>` |
| Test | `@tester *test <file>` | `tapps-agents tester test <file>` |
| Debug | `@debugger *debug "<error>" --file <file>` | `tapps-agents debugger debug "<error>" --file <file>` |
| Plan | `@planner *plan "<desc>"` | `tapps-agents planner plan "<desc>"` |
| Enhance | `@enhancer *enhance "<prompt>"` | `tapps-agents enhancer enhance "<prompt>"` |

**Choose based on:**
- **Cursor**: Interactive, context-aware, natural language
- **CLI**: Batch, automation, structured output, CI/CD

---

## Experts and RAG (Retrieval-Augmented Generation)

### Built-in Technical Experts

**Automatically Available:** Built-in technical experts are loaded automatically based on your detected tech stack (from `requirements.txt`, `package.json`, etc.). No configuration needed.

**Examples:**
- `expert-python`: Python best practices, PEP 8, type hints
- `expert-fastapi`: FastAPI routing, dependency injection, middleware
- `expert-sqlalchemy`: ORM patterns, query optimization, relationships
- `expert-pytest`: Test fixtures, parametrization, async testing

**How It Works:**
1. `tapps-agents init` detects your tech stack
2. Built-in experts are automatically registered based on detected frameworks
3. Expert priorities are set in `.tapps-agents/tech-stack.yaml`
4. Agents consult relevant experts during code generation and review

### Project/Business Experts

**Configuration Required:** Project-specific business-domain experts are configured in `.tapps-agents/experts.yaml` and use knowledge files in `.tapps-agents/knowledge/<domain>/`.

**Setup:**
1. `tapps-agents init` scaffolds:
   - `.tapps-agents/domains.md`: Domain mapping template
   - `.tapps-agents/experts.yaml`: Expert configuration stub
   - `.tapps-agents/knowledge/`: Knowledge base directory
2. Edit `.tapps-agents/experts.yaml` to add business experts
3. Add knowledge files in `.tapps-agents/knowledge/<domain>/`
4. Or use: `tapps-agents setup-experts add` (interactive)

**Example Expert Configuration:**
```yaml
experts:
  - id: expert-payment-processing
    name: Payment Processing Expert
    description: "Expert in payment gateways, PCI compliance, and transaction processing"
    knowledge_domains:
      - payments
      - compliance
    priority: 0.9
    enabled: true
```

**Knowledge Base Structure:**
```
.tapps-agents/knowledge/
  payments/
    payment-gateways.md
    pci-compliance.md
  inventory/
    stock-management.md
    warehouse-operations.md
```

### Context7 vs RAG Knowledge Base

**Context7 (Library Documentation):**
- **Purpose**: Library API reference lookup
- **Access**: Via MCP server (configured in `.cursor/mcp.json`)
- **Usage**: `@reviewer *docs fastapi routing`
- **Content**: Public library documentation (FastAPI, pytest, SQLAlchemy, etc.)
- **Cache**: Pre-populated during `init` with project dependencies + built-in expert libraries

**RAG Knowledge Base (Project/Domain Knowledge):**
- **Purpose**: Business-domain knowledge and project-specific context
- **Access**: Automatically indexed and available to expert agents
- **Usage**: Agents consult knowledge base during code generation
- **Content**: Project requirements, business rules, domain concepts
- **Location**: `.tapps-agents/knowledge/<domain>/` (markdown files)

**When to Use Each:**
- **Context7**: "How do I use FastAPI routing?" → `@reviewer *docs fastapi routing`
- **RAG KB**: "What are our payment processing business rules?" → Add to `.tapps-agents/knowledge/payments/`

---

## Command Aliases

Many commands support `*command` aliases for Cursor compatibility:

- `review` / `*review`
- `score` / `*score`
- `lint` / `*lint`
- `type-check` / `*type-check`
- `implement` / `*implement`
- `refactor` / `*refactor`
- `test` / `*test`
- `debug` / `*debug`
- `plan` / `*plan`
- `enhance` / `*enhance`

**Usage:**
- CLI: Both formats work (`review` or `*review`)
- Cursor: Use `*command` format (`@agent-name *command`)

---

## Output Formats

Most commands support multiple output formats:

- `json`: Structured data (default for most commands)
- `text`: Human-readable output
- `markdown`: Markdown format
- `html`: HTML reports (reviewer report only)
- `yaml`: YAML format (enhancer only)

**When to use each:**
- `json`: CI/CD, automation, programmatic processing
- `text`: Human reading, terminal output
- `markdown`: Documentation, reports
- `html`: Web-based reports, sharing

---

## Common Parameters

### File Processing

- `--pattern <glob>`: Glob pattern for batch processing (e.g., `**/*.py`)
- `--max-workers <n>`: Concurrent file operations (default: 4)
- `--output <file>`: Output file path

### Format Options

- `--format <format>`: Output format (json, text, markdown, html, yaml)
- `--output-format <format>`: Alternative format flag (documenter)

### Context and Configuration

- `--context "<text>"`: Additional context for commands
- `--config <path>`: Custom configuration file
- `--project-root <path>`: Project root directory

### Automation

- `--auto`: Fully automated execution (skip prompts)
- `--non-interactive`: Non-interactive mode
- `--yes` / `-y`: Auto-answer yes to prompts

---

## Simple Mode Workflows

Simple Mode provides natural language orchestration with structured workflows. Use `@simple-mode` in Cursor chat. **Simple Mode is installed by `tapps-agents init`** - the skill and rule files are automatically set up.

### Build Workflow (`*build`)

**Purpose:** Build new features with complete 7-step workflow. **This is the most commonly used Simple Mode command.**

**Cursor Syntax:**
```cursor
@simple-mode *build "Create a user authentication feature"
```

**When to Use:**
- Creating new features from scratch
- Implementing user stories
- Adding new functionality to existing projects
- Greenfield development

**Workflow Steps (MUST FOLLOW ALL STEPS):**
1. **@enhancer *enhance** - Enhanced prompt with requirements analysis (7-stage pipeline)
   - Creates: `docs/workflows/simple-mode/step1-enhanced-prompt.md`
   - Output: Comprehensive specification with requirements, architecture guidance, quality standards
2. **@planner *plan** - User stories with acceptance criteria
   - Creates: `docs/workflows/simple-mode/step2-user-stories.md`
   - Output: User stories, story points, estimates
3. **@architect *design** - System architecture design
   - Creates: `docs/workflows/simple-mode/step3-architecture.md`
   - Output: Architecture, component design, data flow, performance considerations
4. **@designer *design-api** - Component design specifications
   - Creates: `docs/workflows/simple-mode/step4-design.md`
   - Output: API specifications, data models, component designs
5. **@implementer *implement** - Code implementation
   - Uses: All specifications from previous steps
   - Output: Implemented code following design system and architecture
6. **@reviewer *review** - Code quality review (with scores)
   - Creates: `docs/workflows/simple-mode/step6-review.md`
   - Output: Quality scores (5 metrics), issues found, recommendations
7. **@tester *test** - Testing plan and validation
   - Creates: `docs/workflows/simple-mode/step7-testing.md`
   - Output: Test plan, test cases, validation criteria

**Documentation Created:**
- `docs/workflows/simple-mode/step1-enhanced-prompt.md`
- `docs/workflows/simple-mode/step2-user-stories.md`
- `docs/workflows/simple-mode/step3-architecture.md`
- `docs/workflows/simple-mode/step4-design.md`
- `docs/workflows/simple-mode/step6-review.md`
- `docs/workflows/simple-mode/step7-testing.md`

**Quality Gates:**
- Overall score must be ≥ 70 (configurable)
- Security score must be ≥ 6.5
- If thresholds not met, workflow loops back to improve code

### Review Workflow (`*review`)

**Purpose:** Code quality review with improvement suggestions

**Cursor Syntax:**
```cursor
@simple-mode *review <file>
```

**When to Use:**
- Before committing code
- Code quality audits
- Pre-PR reviews
- Learning best practices

**Workflow Steps:**
1. **@reviewer *review** - Quality scores (5 metrics: complexity, security, maintainability, test coverage, performance)
2. **@improver *improve** - Improvement suggestions (if issues found or score < threshold)

### Fix Workflow (`*fix`)

**Purpose:** Fix bugs and errors with systematic debugging

**Cursor Syntax:**
```cursor
@simple-mode *fix <file> "<description>"
```

**When to Use:**
- Debugging runtime errors
- Fixing bugs reported by users
- Resolving test failures
- Correcting logic errors

**Workflow Steps:**
1. **@debugger *debug** - Root cause analysis
2. **@implementer *refactor** - Fix applied
3. **@tester *test** - Verification

### Test Workflow (`*test`)

**Purpose:** Generate comprehensive tests for code

**Cursor Syntax:**
```cursor
@simple-mode *test <file>
```

**When to Use:**
- After implementing features
- To improve test coverage
- When user asks for tests
- Test-driven development

**Workflow Steps:**
1. **@tester *test** - Tests generated and executed

### Epic Workflow (`*epic`)

**Purpose:** Execute all stories in an Epic document in dependency order

**Cursor Syntax:**
```cursor
@simple-mode *epic <epic-doc.md> [--quality-threshold 70] [--auto-mode]
```

**When to Use:**
- Implementing entire Epic documents
- Executing multiple related stories
- Large feature development
- Project milestones

**Workflow Steps:**
1. Parse Epic document (extract stories, dependencies, acceptance criteria)
2. Resolve story dependencies (topological sort)
3. Execute each story in order with quality gates
4. Track progress across all stories
5. Generate Epic completion report

**Example:**
```cursor
@simple-mode *epic docs/prd/epic-51-yaml-automation-quality-enhancement.md
```

### Full SDLC Workflow (`*full`)

**Purpose:** Complete software development lifecycle with all quality gates

**Cursor Syntax:**
```cursor
@simple-mode *full "<description>"
```

**When to Use:**
- Enterprise projects
- Mission-critical features
- Complete application development
- Full lifecycle management

**Workflow Steps:**
1. **@analyst *gather-requirements** - Requirements gathering
2. **@planner *plan** - User stories
3. **@architect *design** - Architecture design
4. **@designer *design-api** - API design
5. **@implementer *implement** - Code implementation
6. **@reviewer *review** - Quality review (loop if < 70)
7. **@tester *test** - Test generation
8. **@ops *security-scan** - Security scanning
9. **@documenter *document-api** - Documentation

### Natural Language Intent Detection

Simple Mode automatically detects intent from keywords:

- **Build**: build, create, make, generate, add, implement, develop, write, new, feature
- **Review**: review, check, analyze, inspect, examine, score, quality, audit, assess, evaluate
- **Fix**: fix, repair, resolve, debug, error, bug, issue, problem, broken, correct
- **Test**: test, verify, validate, coverage, testing, tests
- **Epic**: epic, implement epic, execute epic, run epic, story, stories
- **Full**: full, complete, sdlc, lifecycle, everything

**Examples:**
```cursor
@simple-mode Build a user authentication feature
@simple-mode Review my authentication code
@simple-mode Fix the error in auth.py
@simple-mode Add tests for service.py
@simple-mode Execute epic docs/prd/epic-51.md
```

### Simple Mode Configuration

Simple Mode is configured in `.tapps-agents/config.yaml` (created by `init`):

```yaml
simple_mode:
  enabled: true                       # Enable Simple Mode (default: true after init)
  auto_detect: true                   # Auto-detect intent from natural language
  show_advanced: false                # Hide advanced features initially
  natural_language: true             # Enable natural language commands
  default_orchestrator: "build"      # Default when intent is ambiguous
  onboarding_enabled: true           # Enable onboarding wizard
  progressive_disclosure_enabled: true # Gradually reveal advanced features
```

**After `init`, Simple Mode is:**
- ✅ Skill installed (`.claude/skills/simple-mode/`)
- ✅ Rule installed (`.cursor/rules/simple-mode.mdc`)
- ✅ Enabled by default in config
- ✅ Ready to use in Cursor chat

**To verify Simple Mode is ready:**
```bash
tapps-agents simple-mode status
```

**To enable/configure:**
```bash
tapps-agents simple-mode on          # Enable (usually already enabled after init)
tapps-agents simple-mode init        # Run onboarding wizard
tapps-agents simple-mode configure   # Configure settings
```

---

## Quick Reference

### Most Common Commands

| Task | Cursor | CLI |
|------|--------|-----|
| Review code | `@reviewer *review <file>` | `tapps-agents reviewer review <file>` |
| Score code | `@reviewer *score <file>` | `tapps-agents score <file>` |
| Generate code | `@implementer *implement "<spec>" <file>` | `tapps-agents implementer implement "<spec>" <file>` |
| Generate tests | `@tester *test <file>` | `tapps-agents tester test <file>` |
| Fix bug | `@debugger *debug "<error>" --file <file>` | `tapps-agents debugger debug "<error>" --file <file>` |
| Build feature | `@simple-mode *build "<desc>"` | `tapps-agents workflow rapid --prompt "<desc>" --auto` |
| Create project | `@simple-mode full --prompt "<desc>"` | `tapps-agents create "<desc>"` |

---

## Getting Help

### CLI Help

```bash
# General help
tapps-agents --help

# Agent-specific help
tapps-agents reviewer help
tapps-agents implementer help
tapps-agents workflow list

# Command-specific help
tapps-agents reviewer review --help
tapps-agents workflow full --help
```

### Cursor Help

```cursor
@reviewer *help
@implementer *help
@simple-mode *help
```

---

## Version Information

```bash
tapps-agents --version
```

---

## Guide for Cursor: When and Why to Use tapps-agents

This section helps Cursor AI understand when to suggest or use tapps-agents commands during development.

### Always Use tapps-agents For:

1. **Code Quality Checks**
   - **When**: Before committing code, reviewing PRs, or when user asks about code quality
   - **Why**: Provides objective metrics and AI-powered feedback
   - **Commands**: `@reviewer *review`, `@reviewer *score`, `@reviewer *lint`, `@reviewer *type-check`
   - **Example**: User says "Is this code good?" → Use `@reviewer *review <file>`

2. **Code Generation**
   - **When**: User asks to implement features, create new files, or generate code
   - **Why**: Follows project patterns, includes tests, meets quality standards
   - **Commands**: `@implementer *implement`, `@simple-mode *build`
   - **Example**: User says "Add user authentication" → Use `@simple-mode *build "Add user authentication"`

3. **Bug Fixing**
   - **When**: User reports errors, exceptions, or bugs
   - **Why**: Systematic debugging with root cause analysis
   - **Commands**: `@debugger *debug`, `@simple-mode *fix`
   - **Example**: User says "Fix the error in auth.py" → Use `@simple-mode *fix src/auth.py "Fix the error"`

4. **Testing**
   - **When**: After implementing features, when user asks for tests, or to improve coverage
   - **Why**: Generates comprehensive tests following project patterns
   - **Commands**: `@tester *test`, `@tester *generate-tests`
   - **Example**: User says "Add tests for this" → Use `@tester *test <file>`

5. **Documentation**
   - **When**: User asks for documentation, or after implementing features
   - **Why**: Maintains consistent documentation standards
   - **Commands**: `@documenter *document`, `@documenter *document-api`
   - **Example**: User says "Document this API" → Use `@documenter *document-api <file>`

6. **Library Documentation Lookup**
   - **When**: User asks "How do I use X library?" or needs API reference
   - **Why**: Provides up-to-date library documentation from Context7
   - **Commands**: `@reviewer *docs <library> [topic]`
   - **Example**: User says "How do I use FastAPI routing?" → Use `@reviewer *docs fastapi routing`

7. **Project Setup**
   - **When**: User is setting up a new project or adding tapps-agents to existing project
   - **Why**: Enables all tapps-agents capabilities in Cursor
   - **Commands**: `tapps-agents init`
   - **Example**: User says "Set up tapps-agents" → Suggest `tapps-agents init`

### Command Selection Guide

**For Interactive Development (Cursor Chat):**
- Prefer Cursor Skills syntax: `@agent-name *command`
- Use Simple Mode for complex workflows: `@simple-mode *build`
- Natural language works: `@simple-mode Build a user authentication feature`

**For Batch/Automation (Terminal/CI):**
- Use CLI commands: `tapps-agents <agent> <command>`
- Use `--auto` flag for non-interactive execution
- Use `--format json` for programmatic processing

**For Quality Gates:**
- Use `@reviewer *score` for quick checks
- Use `@reviewer *review` for comprehensive analysis
- Use `--fail-under` in CI/CD to enforce thresholds

**For Feature Development:**
- Use `@simple-mode *build` for complete feature workflow
- Use `@planner *plan` for planning phase
- Use `@architect *design` for architecture decisions

**For Bug Fixes:**
- Use `@simple-mode *fix` for complete fix workflow
- Use `@debugger *debug` for error analysis
- Use `@tester *test` for verification

### Parameter Selection Guide

**Output Formats:**
- `json`: CI/CD, automation, programmatic processing
- `text`: Human-readable terminal output
- `markdown`: Documentation, reports, PR comments
- `html`: Web-based reports, sharing with team

**Batch Processing:**
- Use `--pattern` for glob patterns across project
- Use `--max-workers` to balance speed vs. resources
- Use multiple files for targeted batch operations

**Automation:**
- Use `--auto` for fully automated workflows
- Use `--yes` for non-interactive commands
- Use `--format json` for structured output

**Quality Gates:**
- Use `--fail-under` to enforce minimum scores
- Use `--fail-on-issues` to fail on lint errors
- Use `--coverage` to require test coverage

### Common Workflows

**New Feature Development:**
1. `@simple-mode *build "<description>"` - Complete workflow
2. Or step-by-step: `@planner *plan` → `@architect *design` → `@implementer *implement` → `@reviewer *review` → `@tester *test`

**Code Review:**
1. `@reviewer *score <file>` - Quick quality check
2. `@reviewer *review <file>` - Comprehensive analysis
3. `@improver *improve <file> "<issues>"` - Apply improvements

**Bug Fixing:**
1. `@simple-mode *fix <file> "<description>"` - Complete workflow
2. Or step-by-step: `@debugger *debug` → `@implementer *refactor` → `@tester *test`

**Testing:**
1. `@tester *test <file>` - Generate and run tests
2. `@tester *generate-tests <file>` - Generate without running
3. `@tester *run-tests` - Run existing test suite

## Related Documentation

- [Quick Reference Guide](.cursor/rules/quick-reference.mdc)
- [Simple Mode Guide](docs/SIMPLE_MODE_GUIDE.md)
- [Workflow Presets](.cursor/rules/workflow-presets.mdc)
- [Cursor Skills Installation](docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md)
- [Background Agents Guide](docs/BACKGROUND_AGENTS_GUIDE.md)

---

*Last updated: 2025-01-16*

