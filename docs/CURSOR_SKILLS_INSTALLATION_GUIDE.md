# Cursor AI Skills Installation Guide

**TappsCodingAgents + Cursor AI Integration**

This guide explains how to install and use TappsCodingAgents Skills in Cursor AI IDE.

---

## Overview

TappsCodingAgents provides **Claude Code Skills** that integrate directly into Cursor AI, giving you access to specialized SDLC agents with:

- ✅ **Objective Quality Metrics**: Code scoring with 5 metrics (complexity, security, maintainability, test coverage, performance)
- ✅ **Quality Tools**: Ruff, mypy, bandit, jscpd, pip-audit integration
- ✅ **Context7 Integration**: KB-first library documentation caching (90%+ cache hit rate)
- ✅ **13 Specialized Agents**: Reviewer, Implementer, Tester, Debugger, and more

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
- **Skills**: `.claude/skills/` (12 agent skills from `tapps_agents/resources/claude/skills/`)
- **Cursor Rules**: `.cursor/rules/*.mdc` (5 rule files from `tapps_agents/resources/cursor/rules/`)
- **Background Agents**: `.cursor/background-agents.yaml` (from `tapps_agents/resources/cursor/background-agents.yaml`)
- **Workflow presets**: `workflows/presets/*.yaml` (5 presets from `tapps_agents/resources/workflows/presets/`)
- **Optional config**: `.tapps-agents/config.yaml`

> **Important**: 
> - Skills are **model-agnostic**. Cursor uses the developer's configured model (Auto or pinned).
> - All LLM operations are handled by Cursor Skills - no local LLM or API keys required.
> - Templates are shipped in the package under `tapps_agents/resources/*` and copied to your project during `init`.

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

**4.1 Check Skills Directory**

```bash
# Verify Skills are in place
ls .claude/skills/
# Should show: reviewer/, implementer/, tester/, debugger/
```

**4.2 Test in Cursor AI**

1. Open Cursor AI IDE
2. Open a chat window
3. Type `@reviewer` to activate the Reviewer agent
4. Try a command: `*help`

You should see the Reviewer agent respond with available commands.

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

### Phase 2-3: Additional Agents (Coming Soon)

- @analyst - Requirements gathering
- @planner - Story creation
- @architect - System design
- @designer - API/data model design
- @documenter - Documentation generation
- @improver - Code refactoring
- @ops - Security, deployment
- @orchestrator - Workflow coordination
- @enhancer - Prompt enhancement

---

## Usage Examples

### Reviewer Agent

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

### Implementer Agent

```bash
# Generate code
@implementer *implement "Create FastAPI endpoint for user registration" api/auth.py

# Get library docs first
@implementer *docs fastapi routing
@implementer *implement "Create FastAPI endpoint" api/endpoint.py

# Refactor code
@implementer *refactor utils/helpers.py "Extract common logic"
```

### Tester Agent

```bash
# Generate and run tests
@tester *test calculator.py

# Get test framework docs
@tester *docs pytest fixtures
@tester *test api.py --integration
```

### Debugger Agent

```bash
# Debug error
@debugger *debug "NameError: name 'x' is not defined" --file code.py --line 42

# Analyze error with stack trace
@debugger *analyze-error "ValueError: invalid literal" --stack-trace "..."
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

