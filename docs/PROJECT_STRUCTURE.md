---
title: Project Structure Guide
version: 1.0.0
status: active
last_updated: 2026-01-24
tags: [project-structure, organization, cleanup, best-practices]
---

# Project Structure Guide

This document provides a comprehensive guide to the TappsCodingAgents project structure, file organization, and best practices for maintaining a clean codebase.

## Overview

TappsCodingAgents follows a well-organized directory structure that separates:
- **Framework code** (`tapps_agents/`) - Core framework implementation
- **Documentation** (`docs/`) - User and developer documentation
- **Configuration** (`.tapps-agents/`, `.cursor/`, `.claude/`) - Runtime configuration
- **Scripts** (`scripts/`) - Utility and maintenance scripts
- **Tests** (`tests/`) - Comprehensive test suite
- **Templates** (`templates/`) - Agent roles, project types, tech stacks

## Root Directory

The root directory should contain **only essential project files**:

### Required Files

- `README.md` - Project overview and quick start
- `LICENSE` - License file
- `CHANGELOG.md` - Version history
- `CONTRIBUTING.md` - Contribution guidelines
- `SECURITY.md` - Security policy
- `pyproject.toml` - Python package configuration (sole source of package metadata)
- `requirements.txt` - Python dependencies
- `pytest.ini` - Pytest configuration
- `MANIFEST.in` - Package manifest
- `.gitignore` - Git ignore patterns
- `.cursorignore` - Cursor IDE ignore patterns
- `.cursorrules` - Cursor IDE rules (legacy)

### Files That Should NOT Be in Root

The following files should be moved to appropriate directories:

- **Release notes** → `docs/releases/`
  - Pattern: `RELEASE_NOTES_*.md`
  - Example: `RELEASE_NOTES_v3.5.28.md` → `docs/releases/RELEASE_NOTES_v3.5.28.md`

- **Python scripts** → `scripts/`
  - Pattern: `*.py`
  - Example: `site24x7_client.py` → `scripts/site24x7_client.py`

- **Test files** → `tests/`
  - Pattern: `test_*.py`
  - All test files should be in the `tests/` directory

- **PowerShell scripts** → `scripts/`
  - Pattern: `*.ps1`
  - Utility scripts should be organized in `scripts/`

- **Execution artifacts** → Should be ignored (see `.gitignore`)
  - Pattern: `*_SUMMARY.md`, `*_REPORT.md`, `*_EXECUTION*.md`
  - These are generated during workflow execution and should not be committed

## Directory Structure

### Framework Code: `tapps_agents/`

The main package containing all framework code:

```
tapps_agents/
├── agents/              # 14 workflow agents
│   ├── analyst/         # Requirements gathering
│   ├── planner/         # User story creation
│   ├── architect/       # System architecture design
│   ├── designer/        # API and data model design
│   ├── implementer/     # Code generation
│   ├── debugger/        # Error analysis
│   ├── documenter/      # Documentation generation
│   ├── tester/          # Test generation
│   ├── reviewer/        # Code quality review
│   ├── improver/        # Code improvement
│   ├── ops/             # Security and operations
│   ├── orchestrator/    # YAML workflow coordination
│   ├── enhancer/        # Prompt enhancement
│   └── evaluator/       # Framework effectiveness evaluation
├── core/                # Core framework components
├── context7/            # Context7 KB integration
├── experts/            # Industry experts framework
├── workflow/            # Workflow engine
├── simple_mode/         # Simple Mode orchestration
├── cli/                 # Command-line interface
├── mcp/                 # MCP Gateway
├── quality/             # Quality gates and enforcement
├── health/              # Health monitoring
└── resources/           # Framework resources (Skills, Rules, Presets)
```

**See**: `docs/architecture/source-tree.md` for detailed module documentation.

### Documentation: `docs/`

Organized documentation following best practices:

```
docs/
├── architecture/        # Architecture documentation
│   ├── source-tree.md   # Source code organization
│   ├── coding-standards.md
│   ├── tech-stack.md
│   └── decisions/       # Architecture Decision Records (ADRs)
├── implementation/      # EPIC/PHASE plans, implementation notes
├── archive/             # Archived summaries, cleanup docs
│   └── stories/         # Archived user stories
├── releases/            # Release notes
│   ├── RELEASE_NOTES_*.md
│   └── RELEASE_*_INSTRUCTIONS.md
├── context7/            # Context7 integration docs
├── operations/          # Deployment, release, package distribution
├── guides/              # User guides
├── prd/                 # Product requirements documents
└── workflows/           # Workflow documentation
```

**Key Documentation Files:**
- `README.md` - Documentation index
- `ARCHITECTURE.md` - Architecture overview
- `PROJECT_CONTEXT.md` - Framework vs. self-hosting context
- `SIMPLE_MODE_GUIDE.md` - Simple Mode usage
- `CONFIGURATION.md` - Configuration reference

### Scripts: `scripts/`

Utility and maintenance scripts:

```
scripts/
├── checks/              # Validation and check scripts
├── README.md            # Scripts documentation
├── site24x7_client.py   # Example API client (moved from root)
├── update_version.ps1   # Version management
├── validate_*.py        # Validation scripts
└── ...                  # Other utility scripts
```

**Script Categories:**
- **Validation**: `validate_*.py` - Framework validation
- **Maintenance**: `update_*.py`, `check_*.py` - Maintenance tasks
- **Testing**: `run_*_tests.py` - Test execution
- **Release**: `create_github_release.ps1`, `upload_to_pypi.ps1` - Release automation

### Configuration: `.tapps-agents/`

Runtime configuration (not committed to git):

```
.tapps-agents/
├── config.yaml          # Main configuration (gitignored)
├── experts.yaml         # Industry expert definitions
├── project-profile.yaml # Project profiling results
├── workflow-state/      # Workflow state persistence
├── context7-docs/       # Context7 cache
├── health/              # Health metrics
├── evaluations/         # Framework evaluations
├── knowledge/           # Knowledge base cache
└── workflows/           # Workflow execution artifacts
```

**Note**: Most files in `.tapps-agents/` are gitignored. Only framework-managed files are tracked.

### Cursor Integration: `.cursor/` and `.claude/`

Cursor IDE integration files:

```
.cursor/
├── rules/               # Cursor Rules (.mdc files)
│   ├── simple-mode.mdc
│   ├── command-reference.mdc
│   ├── agent-capabilities.mdc
│   └── ...
├── commands/            # Cursor commands
├── background-agents.yaml
└── mcp.json            # MCP server configuration (gitignored if contains secrets)

.claude/
├── skills/              # Cursor Skills (14 agent skills + simple-mode)
│   ├── analyst/
│   ├── planner/
│   └── ...
└── commands/            # Claude Desktop commands
```

**Installation**: These files are installed by `tapps-agents init`.

### Tests: `tests/`

Comprehensive test suite:

```
tests/
├── unit/                # Unit tests (fast, isolated)
├── integration/         # Integration tests (with real services)
└── e2e/                 # End-to-end tests
    ├── smoke/           # Fast smoke tests
    ├── workflows/       # Workflow execution tests
    ├── scenarios/       # User journey tests
    └── cli/             # CLI command tests
```

**See**: `tests/README.md` for complete test suite documentation.

### Templates: `templates/`

Framework templates:

```
templates/
├── agent_roles/         # Agent role templates
├── project_types/       # Project type templates
├── tech_stacks/         # Tech stack templates
├── user_roles/          # User role templates
└── cursor-rules-template/ # Cursor Rules template
```

## File Organization Best Practices

### 1. Root Directory Cleanliness

**Validation**: Run `scripts/validate_root_structure.py` to check root directory structure:

```bash
python scripts/validate_root_structure.py
```

**Rules**:
- ✅ Only essential project files in root
- ✅ Release notes in `docs/releases/`
- ✅ Utility scripts in `scripts/`
- ✅ Test files in `tests/`
- ❌ No execution artifacts in root

### 2. Documentation Organization

**Structure**:
- **User-facing docs** → `docs/` (guides, API, configuration)
- **Architecture docs** → `docs/architecture/`
- **Release notes** → `docs/releases/`
- **Archived docs** → `docs/archive/`

**Naming Conventions**:
- Use descriptive names: `SIMPLE_MODE_GUIDE.md` not `guide.md`
- Use UPPERCASE for major guides: `README.md`, `ARCHITECTURE.md`
- Use lowercase for subdirectories: `guides/`, `operations/`

### 3. Script Organization

**Categories**:
- **Validation scripts** → `scripts/checks/` or root `scripts/`
- **Maintenance scripts** → `scripts/`
- **Test scripts** → `tests/` (not `scripts/`)
- **Release scripts** → `scripts/` (PowerShell scripts OK)

### 4. Git Ignore Patterns

The `.gitignore` file includes patterns for:
- **Backup files**: `*.backup_*`, `*.backup`
- **Execution artifacts**: `*_SUMMARY.md`, `*_REPORT.md`, `*_EXECUTION*.md`
- **Test artifacts**: `coverage.json`, `*.test-results.xml`
- **Runtime config**: `.tapps-agents/config.yaml`, `.cursor/mcp.json` (if contains secrets)

**See**: `.gitignore` for complete patterns.

## Cleanup Checklist

When cleaning up the project:

1. **Run validation**:
   ```bash
   python scripts/validate_root_structure.py
   ```

2. **Move misplaced files**:
   - Release notes → `docs/releases/`
   - Scripts → `scripts/`
   - Test files → `tests/`

3. **Update references**:
   - Search for file references in documentation
   - Update paths in code and docs

4. **Verify .gitignore**:
   - Ensure execution artifacts are ignored
   - Check backup file patterns

5. **Document changes**:
   - Update this document if structure changes
   - Update `docs/architecture/source-tree.md` if needed

## Validation Script

The `scripts/validate_root_structure.py` script checks:

- ✅ Allowed files in root (README.md, LICENSE, etc.)
- ❌ Forbidden patterns (RELEASE_NOTES*.md, test_*.py, etc.)
- ⚠️ Python scripts in root (should be in scripts/)
- ⚠️ PowerShell scripts in root (should be in scripts/)

**Usage**:
```bash
python scripts/validate_root_structure.py
```

**Exit Codes**:
- `0` - Valid structure (may have warnings)
- `1` - Invalid structure (errors found)

## Related Documentation

- **[Source Tree Organization](architecture/source-tree.md)** - Detailed source code organization
- **[Architecture Overview](ARCHITECTURE.md)** - System architecture
- **[Project Context](PROJECT_CONTEXT.md)** - Framework vs. self-hosting
- **[Contributing Guidelines](../CONTRIBUTING.md)** - Contribution guidelines

---

**Last Updated:** 2026-01-24  
**Maintained By:** TappsCodingAgents Team
