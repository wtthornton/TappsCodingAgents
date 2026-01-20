---
title: Configuration Guide
version: 3.3.0
status: active
last_updated: 2026-01-20
tags: [configuration, setup, yaml, pydantic, settings]
---

# TappsCodingAgents - Configuration Guide

This document describes the configuration system for TappsCodingAgents.

## Overview

TappsCodingAgents uses a YAML-based configuration file validated by Pydantic models. Configuration is **optional**; if no file is found, the framework uses defaults.

## Configuration File Location

The framework looks for configuration at `.tapps-agents/config.yaml` in your project root (or any parent directory of the current working directory):

```
your-project/
├── .tapps-agents/
│   ├── config.yaml            # Project configuration
│   ├── domains.md             # Business domain definitions (optional)
│   ├── experts.yaml           # Industry experts (optional)
│   ├── project-profile.yaml   # Project profile (auto-generated)
│   └── knowledge/             # Expert knowledge base (optional)
└── src/
    └── ...
```

If no config file is found, the framework uses default values.

## Configuration Schema

### Root Configuration

```yaml
# Project metadata (optional)
project_name: "MyProject"
version: "1.0.0"

# User role template (optional)
# Selects a role template to customize agent behavior based on your role
# Available roles: senior-developer, junior-developer, tech-lead, product-manager, qa-engineer
# See docs/USER_ROLE_TEMPLATES_GUIDE.md for details
user_role: senior-developer

# Tooling targets/policy (optional, used by `doctor`)
tooling:
  targets:
    python: 3.13.3
    python_requires: ">=3.13"
    os_targets: ["windows", "linux"]
  policy:
    external_tools_mode: soft   # soft=warn/skip, hard=fail
    mypy_staged: true
    mypy_stage_paths: ["tapps_agents/core", "tapps_agents/workflow", "tapps_agents/context7"]

# Agent configurations
agents:
  reviewer:
    # Reviewer agent settings (see below)

# Code scoring configuration
scoring:
  # Scoring settings (see below)

# Note: MAL configuration has been removed. All LLM operations are handled by Cursor Skills.
# Agents prepare instruction objects that are executed via Cursor Skills.

# Context7 integration (optional)
context7:
  # Context7 settings (see below)

# Phase 6 quality tools (optional)
quality_tools:
  # Quality tools settings (see below)
```

### Tooling (`doctor`) configuration

The `doctor` command reads `.tapps-agents/config.yaml` and reports mismatches (Python version targets, missing tools like ruff/mypy/pytest). It also reports **Beads (bd) status** (optional: available, not found, or not checked). See [Beads Integration](BEADS_INTEGRATION.md).

- `tooling.targets.python`: the “pinned” Python version you expect for this repo/project.
- `tooling.targets.python_requires`: the PEP 440 requires-python constraint (should match your packaging config).
- `tooling.policy.external_tools_mode`: soft-degrade (warn/skip) vs hard-fail for missing tools.

### Agent Configuration: Reviewer

```yaml
agents:
  reviewer:
    quality_threshold: 70.0             # Minimum score (0-100) to pass review
    include_scoring: true               # Include code scoring in review
    max_file_size: 1048576              # Maximum file size in bytes (1MB)
    min_confidence_threshold: 0.8       # Minimum expert confidence (0.0-1.0)
```

**Reviewer Agent Features (2026-01-16):**
- ✅ **Test Coverage Detection:** Returns 0.0% when no tests exist (previously 5.0-6.0)
- ✅ **Maintainability Issues:** Provides specific issues with line numbers, severity, and suggestions
- ✅ **Structured Feedback:** Always provides actionable feedback (summary, strengths, issues, recommendations)
- ✅ **Performance Issues:** Tracks performance bottlenecks with line numbers and context
- ✅ **Type Checking Scores:** Reflects actual mypy errors (not static 5.0)
- ✅ **Context-Aware Quality Gates:** Adapts thresholds based on file status (new/modified/existing):
  - **New files:** Lenient thresholds (overall: 5.0, security: 6.0, coverage: 0%)
  - **Modified files:** Standard thresholds (overall: 8.0, security: 8.5, coverage: 70%)
  - **Existing files:** Strict thresholds (overall: 8.0, security: 8.5, coverage: 80%)

### Agent Configuration: All Agents

All agents support `min_confidence_threshold`. Note: `model` configuration has been removed as all LLM operations are handled by Cursor Skills.

```yaml
agents:
  architect:
    min_confidence_threshold: 0.75

  implementer:
    min_confidence_threshold: 0.7

  designer:
    min_confidence_threshold: 0.65

  tester:
    min_confidence_threshold: 0.7

  ops:
    min_confidence_threshold: 0.75

  enhancer:
    min_confidence_threshold: 0.6

  analyst:
    min_confidence_threshold: 0.65

  planner:
    min_confidence_threshold: 0.6

  debugger:
    min_confidence_threshold: 0.7

  documenter:
    min_confidence_threshold: 0.5

  orchestrator:
    min_confidence_threshold: 0.6
```

### Scoring Configuration

```yaml
scoring:
  weights:
    complexity: 0.20
    security: 0.30
    maintainability: 0.25
    test_coverage: 0.15
    performance: 0.10
  quality_threshold: 70.0
```

**Important:** The weights must sum to ~1.0 (a small floating point tolerance is allowed). If they don't, configuration loading will fail.

### Note on LLM Configuration

**MAL configuration has been removed.** All LLM operations are now handled by Cursor Skills. Agents prepare instruction objects that are executed via Cursor Skills, which use the developer's configured model in Cursor. No local LLM (Ollama) or API keys are required.

### Context7 Configuration (optional)

```yaml
context7:
  enabled: true
  default_token_limit: 3000
  cache_duration: 3600
  integration_level: "optional"      # mandatory | optional
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

### Quality Tools Configuration (Phase 6)

```yaml
quality_tools:
  ruff_enabled: true
  ruff_config_path: null

  mypy_enabled: true
  mypy_strict: false
  mypy_config_path: null

  jscpd_enabled: true
  duplication_threshold: 3.0
  min_duplication_lines: 5

  typescript_enabled: true
  eslint_config: null
  tsconfig_path: null

  pip_audit_enabled: true
  dependency_audit_threshold: "high"   # low | medium | high | critical
```

### Simple Mode Configuration

Simple Mode provides a streamlined, task-first interface for new users, hiding complexity while showcasing the power of TappsCodingAgents.

```yaml
simple_mode:
  enabled: true                       # Enable Simple Mode (default: true)
  default_orchestrator: "build"      # Default orchestrator (build, review, fix, test)
  onboarding_enabled: true           # Enable guided onboarding wizard
  natural_language_enabled: true     # Enable natural language command processing
  progressive_disclosure_enabled: true # Gradually reveal advanced features
  auto_detect_project_type: true    # Automatically detect project type
  show_advanced_tips: true            # Show tips for advanced features
  max_history_entries: 10            # Maximum command history entries
  feedback_collection_enabled: true  # Enable anonymous feedback collection
```

**Configuration Options:**

- `enabled`: Enable or disable Simple Mode (default: `true`)
- `default_orchestrator`: Default orchestrator to use when intent is ambiguous (`build`, `review`, `fix`, `test`)
- `onboarding_enabled`: Enable the interactive onboarding wizard (`tapps-agents simple-mode init`)
- `natural_language_enabled`: Enable natural language command parsing
- `progressive_disclosure_enabled`: Gradually reveal advanced features as users gain experience
- `auto_detect_project_type`: Automatically detect project type for tailored suggestions
- `show_advanced_tips`: Show tips for advanced features as users progress
- `max_history_entries`: Maximum number of command history entries to store (1-100)
- `feedback_collection_enabled`: Enable anonymous feedback collection for UX improvements

**Usage:**

```bash
# Enable Simple Mode
tapps-agents simple-mode on

# Run onboarding wizard
tapps-agents simple-mode init

# Use Simple Mode commands
tapps-agents simple-mode build -p "Create a new feature"
tapps-agents simple-mode review --file src/main.py
tapps-agents simple-mode fix --file src/buggy.py
tapps-agents simple-mode test --file src/api.py

# Auto-detect intent
tapps-agents simple-mode run -p "Build a REST API endpoint"
```

See [Simple Mode Guide](SIMPLE_MODE_GUIDE.md) for complete documentation.

### Continuous Bug Fix Configuration

Configuration for the continuous bug finding and fixing feature.

```yaml
continuous_bug_fix:
  max_iterations: 10              # Maximum loop iterations (1-100)
  commit_strategy: "one-per-bug"  # Commit strategy: "one-per-bug" or "batch"
  auto_commit: true                # Automatically commit fixes after bug-fix-agent succeeds
  test_path: "tests/"              # Default test directory or file to run
  skip_patterns: []                # Patterns for bugs to skip (not yet implemented)
```

**Configuration Options:**
- `max_iterations`: Maximum number of loop iterations before stopping (default: `10`, range: 1-100)
- `commit_strategy`: How to commit fixes - `one-per-bug` (one commit per bug) or `batch` (one commit for all bugs) (default: `one-per-bug`)
- `auto_commit`: Whether to automatically commit fixes after bug-fix-agent succeeds (default: `true`)
- `test_path`: Default test directory or file to run (default: `tests/`)
- `skip_patterns`: List of patterns for bugs to skip (not yet implemented, reserved for future use)

**Usage:**
```bash
# Basic usage (uses config defaults)
tapps-agents continuous-bug-fix

# Override config with CLI arguments
tapps-agents continuous-bug-fix --test-path tests/unit/ --max-iterations 5

# Dry run (no commits)
tapps-agents continuous-bug-fix --no-commit
```

**How It Works:**
1. Runs pytest to detect test failures
2. Parses failures to extract bug information (file path, error message)
3. Calls bug-fix-agent (FixOrchestrator) to fix each bug
4. Commits fixes automatically (if enabled)
5. Repeats until no bugs remain or max iterations reached

**Integration:**
- Integrates with bug-fix-agent (FixOrchestrator) for fixing bugs
- Uses git operations from `core.git_operations` for commits
- Respects bug-fix-agent quality thresholds and configuration

### Automatic Prompt Enhancement (auto_enhancement)

When **auto_enhancement** is enabled, the CLI middleware can enhance short or low-quality prompts before they reach an agent (implementer, planner, analyst, etc.). Workflows (e.g. full-sdlc, rapid-dev, Epic) can also run enhancement via the EnhancerHandler when an `enhancer` step is present.

```yaml
auto_enhancement:
  enabled: true
  quality_threshold: 50.0       # Enhance when score < this (0-100)
  min_prompt_length: 20
  commands:
    implementer:
      enabled: true
      synthesis_mode: full      # full | quick
    planner:
      enabled: true
      synthesis_mode: quick
    analyst:
      enabled: true
      synthesis_mode: quick
    architect:
      enabled: false            # Off by default to avoid over-use
    designer:
      enabled: false            # Off by default to avoid over-use
```

- **enabled**: Turn auto-enhancement on or off globally.
- **quality_threshold**: Prompts with `assess_prompt_quality` score below this are enhanced. Higher values mean more prompts are enhanced.
- **min_prompt_length**: Prompts shorter than this get score 0 and are enhanced (when enabled for that command).
- **commands**: Per-agent settings. `synthesis_mode`: `full` (7-stage) or `quick` (3-stage). `architect` and `designer` default to `enabled: false`.

**Prompt argument map:** `PROMPT_ARGUMENT_MAP` in `tapps_agents/cli/utils/prompt_enhancer.py` defines which `(agent, command)` pairs are eligible and which CLI argument holds the prompt (e.g. `specification`, `description`, `requirements`). Commands with value `None` are never enhanced (e.g. `(debugger, debug)`, `(implementer, refactor)`). To support auto-enhancement for a new agent/command, add an entry there and in `auto_enhancement.commands` if you want non-default behavior.

## Default Values

If no configuration file is provided, defaults are loaded from the Pydantic models in `tapps_agents/core/config.py`.

## Configuration Loading

Configuration is loaded via `tapps_agents.core.config.load_config()` and is also loaded when agents are activated.

```python
from tapps_agents.core.config import load_config

config = load_config()  # searches for .tapps-agents/config.yaml upward, else defaults
```

## Reference

- **Default template**: `templates/default_config.yaml`
- **Config models**: `tapps_agents/core/config.py`
- **Expert setup**: `docs/EXPERT_SETUP_WIZARD.md`
- **Project profiling**: `docs/PROJECT_PROFILING_GUIDE.md`
- **Beads (bd) integration**: [BEADS_INTEGRATION.md](BEADS_INTEGRATION.md) (optional `beads` config: `enabled`, `sync_epic`, `hooks_simple_mode`; doctor reports status; init hints `bd init` when detected)
