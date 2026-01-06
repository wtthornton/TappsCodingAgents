# Cursor AI Skills & Claude Desktop Commands Installation Guide

**TappsCodingAgents + Cursor AI + Claude Desktop Integration**

This guide explains how to install and use TappsCodingAgents Skills in Cursor AI IDE and Commands in Claude Desktop.

---

## Overview

TappsCodingAgents provides **two unified interfaces** for accessing specialized SDLC agents:

### Cursor Skills (Cursor IDE)
- **14 Cursor Skills** (`.claude/skills/`) - Use `@agent *command` syntax in Cursor IDE
- **Objective Quality Metrics**: Code scoring with 5 metrics (complexity, security, maintainability, test coverage, performance)
- **Quality Tools**: Ruff, mypy, bandit, jscpd, pip-audit integration
- **Context7 Integration**: KB-first library documentation caching (90%+ cache hit rate)
- **13 Specialized Agents**: Reviewer, Implementer, Tester, Debugger, and more

### Claude Desktop Commands (Claude Desktop)
- **16 Claude Desktop Commands** (`.claude/commands/`) - Use `@command` syntax in Claude Desktop
- **Same Functionality**: All commands provide the same features as Cursor Skills
- **Unified Experience**: Choose your preferred interface - both work seamlessly

---

## Prerequisites

1. **Cursor AI IDE** (latest version with Skills support)
2. **Python 3.13+** installed (recommended: latest stable Python)
3. **TappsCodingAgents** installed (see [QUICK_START.md](../QUICK_START.md))
4. **Context7 API Key** (optional, for library documentation)

---

## Installation Steps

### Step 1: Install TappsCodingAgents

```bash
# Clone or navigate to TappsCodingAgents directory
cd TappsCodingAgents

# Install the framework
pip install -e .
```

### Step 2: Install Cursor integration artifacts (Recommended)

Run the project initializer from **your target project** (not from this repo):

```bash
# In your project directory
tapps-agents init
# (or) python -m tapps_agents.cli init
```

This installs (by copying from packaged templates in `tapps_agents/resources/*`):
- **Cursor Skills**: `.claude/skills/` (14 agent skills + Simple Mode skill from `tapps_agents/resources/claude/skills/`)
- **Claude Desktop Commands**: `.claude/commands/` (16 commands from `tapps_agents/resources/claude/commands/`)
- **Cursor Rules**: `.cursor/rules/*.mdc` (7 rule files from `tapps_agents/resources/cursor/rules/`, including `simple-mode.mdc` and `command-reference.mdc`)
- **Workflow presets**: `workflows/presets/*.yaml` (8 presets from `tapps_agents/resources/workflows/presets/`, including 3 Simple Mode workflows)
- **Optional config**: `.tapps-agents/config.yaml`
- **USER Scope Directory**: `~/.tapps-agents/skills/` (created automatically for personal skills)

> **Important**: 
> - Skills and Commands are **model-agnostic**. Cursor/Claude Desktop uses the developer's configured model (Auto or pinned).
> - All LLM operations are handled by Cursor Skills or Claude Desktop - no local LLM or API keys required.
> - Templates are shipped in the package under `tapps_agents/resources/*` and copied to your project during `init`.
> - **Both interfaces work together** - use Skills in Cursor IDE or Commands in Claude Desktop, whichever you prefer.

### Step 3: (Alternative) Manual Installation

If you prefer to install manually, you can copy from the installed package location:

```bash
# Find the package location
python -c "import tapps_agents.resources; import os; print(os.path.dirname(tapps_agents.resources.__file__))"

# Then copy from that location to your project
# (Skills are under tapps_agents/resources/claude/skills/)
```

**Note**: The recommended approach is using `tapps-agents init`, which handles all installation steps automatically.

### Step 3: Configure Context7 (Optional but Recommended)

Context7 provides KB-first caching for library documentation, achieving 90%+ cache hit rates.

**3.1 Create Configuration File**

Create `.tapps-agents/config.yaml` in your project:

```yaml
# .tapps-agents/config.yaml

context7:
  enabled: true
  default_token_limit: 3000
  cache_duration: 3600
  integration_level: "optional"
  bypass_forbidden: true
  
  knowledge_base:
    enabled: true
    location: ".tapps-agents/kb/context7-cache"
    sharding: true
    indexing: true
    max_cache_size: "100MB"
    hit_rate_threshold: 0.7
    fuzzy_match_threshold: 0.7
  
  refresh:
    enabled: true
    default_max_age_days: 30
    check_on_access: true
    auto_queue: true
    auto_process_on_startup: false
```

**3.2 Set Context7 API Key (Optional)**

If you want to fetch library documentation from Context7 API:

```bash
# Set environment variable
export CONTEXT7_API_KEY="your-api-key-here"

# Or add to .env file
echo "CONTEXT7_API_KEY=your-api-key-here" >> .env
```

**3.3 Pre-populate Cache (Recommended)**

Pre-populate the Context7 KB cache with common libraries:

```bash
# Pre-populate with common libraries and project dependencies
python scripts/prepopulate_context7_cache.py

# Or with specific libraries
python scripts/prepopulate_context7_cache.py --libraries fastapi pytest sqlalchemy

# Include common topics
python scripts/prepopulate_context7_cache.py --topics
```

This helps achieve 95%+ cache hit rate from the start.

### Step 4: Verify Installation

**4.1 Check Skills and Commands Directories**

```bash
# Verify Skills are in place
ls .claude/skills/
# Should show: reviewer/, implementer/, tester/, debugger/, simple-mode/, etc.

# Verify Commands are in place
ls .claude/commands/
# Should show: review.md, implement.md, test.md, build.md, etc.
```

**4.2 Test in Cursor AI**

1. Open Cursor AI IDE
2. Open a chat window
3. Type `@reviewer` to activate the Reviewer agent
4. Try a command: `*help`

You should see the Reviewer agent respond with available commands.

**4.3 Test in Claude Desktop**

1. Open Claude Desktop
2. Open a conversation
3. Type `@review src/api/auth.py` (or any file path)
4. Or type `@build "Create a user authentication feature"`

You should see Claude execute the command with the same functionality as Cursor Skills.

---

## Available Skills

### Phase 1: Core Agents (Available Now)

1. **@reviewer** - Code reviewer with objective quality metrics
   - Commands: `*review`, `*score`, `*lint`, `*type-check`, `*security-scan`, `*docs`
   - Features: Code scoring, quality tools, Context7 integration

2. **@implementer** - Code generation and refactoring
   - Commands: `*implement`, `*generate-code`, `*refactor`, `*docs`
   - Features: Code generation, automatic review, Context7 library docs

3. **@tester** - Test generation and execution
   - Commands: `*test`, `*generate-tests`, `*run-tests`, `*docs`
   - Features: Test generation, coverage reporting, Context7 test framework docs

4. **@debugger** - Error analysis and debugging
   - Commands: `*debug`, `*analyze-error`, `*trace`, `*docs`
   - Features: Error analysis, code tracing, Context7 error patterns

### Phase 2-3: Additional Agents (Available)

- @analyst - Requirements gathering
- @planner - Story creation
- @architect - System design
- @designer - API/data model design
- @documenter - Documentation generation
- @improver - Code refactoring
- @ops - Security, deployment
- @orchestrator - Workflow coordination
- @enhancer - Prompt enhancement

### Simple Mode Skill (New Users)

**@simple-mode** - Simplified, task-first interface for new users
- Commands: `*run`, `*build`, `*review`, `*fix`, `*test`, `*init`
- Features: Natural language commands, guided onboarding, zero-config mode
- Hides complexity while showcasing the power of TappsCodingAgents

**Usage:**
```bash
# Enable Simple Mode
tapps-agents simple-mode on

# Run onboarding wizard
tapps-agents simple-mode init

# Use natural language commands
@simple-mode *run "Build a user authentication module"
@simple-mode *build "Create a FastAPI endpoint"
@simple-mode *review src/main.py
@simple-mode *fix src/buggy.py -p "Fix the error"
@simple-mode *test src/api.py
```

See [Simple Mode Guide](SIMPLE_MODE_GUIDE.md) for complete documentation.

---

## Skill System Features

### Multi-Scope Skill Discovery

TappsCodingAgents supports discovering skills from multiple scopes, allowing you to:
- **REPO Scope**: Project-specific skills (`.claude/skills/` in current, parent, or git root)
- **USER Scope**: Personal skills that work across all projects (`~/.tapps-agents/skills/`)
- **SYSTEM Scope**: Built-in framework skills (package directory)

**Scope Precedence**: REPO > USER > SYSTEM (project skills override personal/system skills)

**Creating Personal Skills**:
```bash
# Create personal skill directory (created automatically on init)
mkdir -p ~/.tapps-agents/skills/my-custom-skill

# Create SKILL.md with your custom skill
cat > ~/.tapps-agents/skills/my-custom-skill/SKILL.md << 'EOF'
---
name: my-custom-skill
description: My personal custom skill
version: 1.0.0
author: Your Name
category: custom
tags: [custom, personal]
allowed-tools: Read, Write
---

# My Custom Skill

Your skill instructions here.
EOF
```

The skill will be available in all your projects automatically!

### Enhanced Skill Metadata

Skills now support enhanced metadata fields:
- `version`: Semantic versioning (e.g., "1.0.0")
- `author`: Skill author (e.g., "TappsCodingAgents Team" or your name)
- `category`: Skill category (quality, development, testing, planning, design, documentation, operations, orchestration)
- `tags`: List of tags for organization and searchability

**Example**:
```yaml
---
name: reviewer
description: Code reviewer providing objective quality metrics...
version: 1.0.0
author: TappsCodingAgents Team
category: quality
tags: [review, quality, metrics, security, linting]
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
model_profile: reviewer_profile
---
```

### Progressive Disclosure

Skills use progressive disclosure for efficient loading:
- Only metadata (first 2KB) is read at startup
- Full SKILL.md content is loaded by Cursor when skill is invoked
- Improves startup performance and scalability

---

## Available Claude Desktop Commands

TappsCodingAgents provides **16 Claude Desktop Commands** that work alongside Cursor Skills. Use `@command` syntax in Claude Desktop for the same functionality.

### Core Development Commands

- **@review** - Full code review with scoring (equivalent to `@reviewer *review`)
- **@score** - Quick quality scoring (equivalent to `@reviewer *score`)
- **@implement** - Generate code from description (equivalent to `@implementer *implement`)
- **@test** - Generate and run tests (equivalent to `@tester *test`)
- **@debug** - Debug errors and find root cause (equivalent to `@debugger *debug`)
- **@refactor** - Refactor code with instructions (equivalent to `@implementer *refactor`)
- **@improve** - Improve code quality (equivalent to `@improver *improve`)
- **@lint** - Run code linting (equivalent to `@reviewer *lint`)

### Planning & Design Commands

- **@plan** - Create development plan with user stories (equivalent to `@planner *plan`)
- **@design** - Design system architecture (equivalent to `@architect *design`)
- **@docs** - Generate documentation (equivalent to `@documenter *document`)

### Quality & Security Commands

- **@security-scan** - Scan for security vulnerabilities (equivalent to `@reviewer *security-scan`)
- **@library-docs** - Get library documentation from Context7 (equivalent to `@reviewer *docs`)

### Workflow Commands

- **@build** - Complete feature development workflow (Simple Mode build workflow)
- **@fix** - Fix bugs with systematic debugging (Simple Mode fix workflow)

**See [Claude Desktop Commands Guide](CLAUDE_DESKTOP_COMMANDS.md) for complete documentation.**

---

## Usage Examples

### In Cursor IDE (Skills)

Use `@agent *command` syntax:

### Reviewer Agent (Cursor IDE)

```bash
# Full code review with scoring
@reviewer *review src/api/auth.py

# Score only (faster)
@reviewer *score src/utils/helpers.py

# Linting
@reviewer *lint src/

# Type checking
@reviewer *type-check src/

# Security scan
@reviewer *security-scan src/

# Get library docs from Context7
@reviewer *docs fastapi
```

### Implementer Agent (Cursor IDE)

```bash
# Generate code
@implementer *implement "Create FastAPI endpoint for user registration" api/auth.py

# Get library docs first
@implementer *docs fastapi routing
@implementer *implement "Create FastAPI endpoint" api/endpoint.py

# Refactor code
@implementer *refactor utils/helpers.py "Extract common logic"
```

### Tester Agent (Cursor IDE)

```bash
# Generate and run tests
@tester *test calculator.py

# Get test framework docs
@tester *docs pytest fixtures
@tester *test api.py --integration
```

### Debugger Agent (Cursor IDE)

```bash
# Debug error
@debugger *debug "NameError: name 'x' is not defined" --file code.py --line 42

# Analyze error with stack trace
@debugger *analyze-error "ValueError: invalid literal" --stack-trace "..."
```

### In Claude Desktop (Commands)

Use `@command` syntax (same functionality as Skills):

```bash
# Code review
@review src/api/auth.py

# Quick scoring
@score src/utils/helpers.py

# Generate code
@implement "Create FastAPI endpoint for user registration" api/auth.py

# Generate tests
@test calculator.py

# Debug errors
@debug "NameError: name 'x' is not defined" --file code.py --line 42

# Build complete feature
@build "Create a user authentication feature"

# Get library documentation
@library-docs fastapi routing

# Security scan
@security-scan src/
```
```

---

## Context7 Integration

### How It Works

1. **KB-First Lookup**: Skills check Context7 KB cache first (<0.15s response)
2. **Fuzzy Matching**: If cache miss, tries fuzzy matching
3. **API Fallback**: If still miss, fetches from Context7 API
4. **Auto-Caching**: Results stored in cache for future use

### Benefits

- ✅ **90%+ Cache Hit Rate**: Most lookups served from cache
- ✅ **Fast Response**: <0.15s for cached content
- ✅ **Version-Specific**: Always current documentation
- ✅ **Reduced Hallucinations**: Accurate API references
- ✅ **Cost Efficient**: Fewer API calls

### Commands

All Skills support Context7 commands:

- `*docs {library} [topic]` - Get library docs from KB cache
- `*docs-refresh {library} [topic]` - Refresh library docs
- `*docs-search {query}` - Search for libraries

---

## Troubleshooting

### Skills Not Appearing in Cursor

1. **Check Skills Directory**:
   ```bash
   ls .claude/skills/
   ```

2. **Verify Cursor Version**: Ensure you have the latest Cursor AI with Skills support

3. **Restart Cursor**: Close and reopen Cursor AI IDE

### Context7 Not Working

1. **Check Configuration**:
   ```bash
   cat .tapps-agents/config.yaml
   ```

2. **Verify Cache Directory**:
   ```bash
   ls .tapps-agents/kb/context7-cache/
   ```

3. **Pre-populate Cache**:
   ```bash
   python scripts/prepopulate_context7_cache.py
   ```

### Quality Tools Not Found

1. **Install Tools**:
   ```bash
   pip install ruff mypy bandit jscpd pip-audit
   ```

2. **Verify Installation**:
   ```bash
   ruff --version
   mypy --version
   ```

---

## Advanced Configuration

### Custom Quality Gates

Create `.tapps-agents/quality-gates.yaml`:

```yaml
quality_gates:
  overall_min: 70.0
  security_min: 7.0
  complexity_max: 8.0
  maintainability_min: 7.0
  test_coverage_min: 80.0
```

### Custom Scoring Configuration

Create `.tapps-agents/scoring-config.yaml`:

```yaml
scoring:
  weights:
    complexity: 0.2
    security: 0.3
    maintainability: 0.2
    test_coverage: 0.15
    performance: 0.15
```

---

## Next Steps

1. **Pre-populate Context7 Cache**: Run the pre-population script
2. **Try Core Agents**: Start with `@reviewer` and `@implementer`
3. **Explore Context7**: Use `*docs` commands to explore library documentation
4. **Customize**: Adjust quality gates and scoring weights for your project

---

## Support

- **Documentation**: See [docs/](../docs/) directory
- **Issues**: Report on GitHub
- **Community**: Join discussions

---

## Phase 1 Complete ✅

Phase 1 of the Cursor AI Integration Plan is complete:

- ✅ Enhanced Reviewer Skill with Context7 integration
- ✅ Implementer Skill with library doc lookup
- ✅ Tester Skill with Context7 test framework docs
- ✅ Debugger Skill with error pattern knowledge
- ✅ Context7 KB cache pre-population script
- ✅ Skills installation guide

**Next Phase**: Quality Tools Integration (Phase 2)

