---
title: Package Distribution Guide
version: 1.0.0
status: active
last_updated: 2026-01-20
tags: [documentation, distribution, packaging, init]
---

# Package Distribution Guide

This document explains which documentation files are shipped with the `tapps-agents` package and which files are generated/rebuild when a project runs `tapps-agents init`.

## Package Distribution (What Ships with tapps-agents)

### ✅ Included in Package (`tapps_agents/resources/`)

**Only files in `tapps_agents/resources/` are included in the PyPI package** (per `MANIFEST.in`):

1. **Cursor Skills** (`tapps_agents/resources/claude/skills/`)
   - 14 agent skills: `analyst/`, `architect/`, `debugger/`, `designer/`, `documenter/`, `enhancer/`, `evaluator/`, `implementer/`, `improver/`, `ops/`, `orchestrator/`, `planner/`, `reviewer/`, `tester/`
   - 1 orchestrator skill: `simple-mode/`
   - **Total: 15 skills** (each with `SKILL.md`)

2. **Claude Desktop Commands** (`tapps_agents/resources/claude/commands/`)
   - Command files: `build.md`, `debug.md`, `design.md`, `docs.md`, `fix.md`, `implement.md`, `improve.md`, `library-docs.md`, `lint.md`, `plan.md`, `refactor.md`, `review.md`, `score.md`, `security-scan.md`, `test.md`, `README.md`
   - **Total: 16 command files**

3. **Cursor Rules** (`tapps_agents/resources/cursor/rules/`)
   - Rule files: `workflow-presets.mdc`, `quick-reference.mdc`, `agent-capabilities.mdc`, `project-context.mdc`, `project-profiling.mdc`, `simple-mode.mdc`, `command-reference.mdc`, `cursor-mode-usage.mdc`
   - `.cursorignore` file
   - **Total: 8 rule files + .cursorignore**

4. **Workflow Presets** (`tapps_agents/resources/workflows/presets/`)
   - Framework-managed presets: `full-sdlc.yaml`, `rapid-dev.yaml`, `maintenance.yaml`, `quality.yaml`, `quick-fix.yaml`, `simple-fix-issues.yaml`, `simple-improve-quality.yaml`, `simple-new-feature.yaml`
   - **Total: 8 preset files**

5. **Customizations** (`tapps_agents/resources/customizations/`)
   - Example customization files

**Package Size Impact:** ~100-200 KB of resources files

### ❌ NOT Included in Package (Excluded per `MANIFEST.in`)

These documentation files are **NOT shipped** with the package (excluded from distribution):

1. **Main Documentation** (`docs/`)
   - `docs/README.md`
   - `docs/ARCHITECTURE.md`
   - `docs/API.md`
   - `docs/CONFIGURATION.md`
   - `docs/AI_COMMENT_GUIDELINES.md`
   - `docs/DOCUMENTATION_METADATA_STANDARDS.md`
   - `docs/MCP_STANDARDS.md`
   - `docs/CONTEXT7_PATTERNS.md`
   - `docs/architecture/` (all shard files)
   - `docs/architecture/decisions/` (all ADRs)
   - `docs/test-stack.md`
   - All other documentation files

2. **Root Documentation Files**
   - `AGENTS.md`
   - `CLAUDE.md`
   - `README.md` (only used as package metadata, not shipped as file)

3. **Requirements Documentation** (`requirements/`)
   - `requirements/PROJECT_REQUIREMENTS.md`
   - `requirements/README.md`
   - `requirements/agent_api.md`
   - `requirements/TECH_STACK.md`
   - All other requirements files

4. **Development Files**
   - `scripts/` (all verification and tooling scripts)
   - `.github/workflows/` (CI/CD workflows)
   - `.cursor/rules/` (repo-root rules, not shipped)
   - `.claude/skills/` (repo-root skills, not shipped)
   - `workflows/` (repo-root presets, not shipped)

**Why Excluded:**
- Documentation files are large (several MB)
- They're framework development docs, not user runtime docs
- They're available on GitHub and don't need to be in the package
- Only runtime resources needed by `init` are shipped

## What Gets Generated/Rebuilt by `tapps-agents init`

When a project runs `tapps-agents init`, the following files are **copied from package resources** to the project:

### Files Copied from Package (Static)

1. **`.cursor/rules/`** (8 rule files)
   - Copied from `tapps_agents/resources/cursor/rules/`
   - Files: `workflow-presets.mdc`, `quick-reference.mdc`, `agent-capabilities.mdc`, `project-context.mdc`, `project-profiling.mdc`, `simple-mode.mdc`, `command-reference.mdc`, `cursor-mode-usage.mdc`

2. **`.claude/skills/`** (15 skills)
   - Copied from `tapps_agents/resources/claude/skills/`
   - One directory per skill with `SKILL.md` file

3. **`.claude/commands/`** (16 command files)
   - Copied from `tapps_agents/resources/claude/commands/`
   - Individual `.md` files for each command

4. **`workflows/presets/`** (8 preset files)
   - Copied from `tapps_agents/resources/workflows/presets/`
   - Framework-managed workflow YAML files

### Files Generated/Regenerated (Dynamic)

1. **`workflow-presets.mdc`** (auto-generated)
   - **Regenerated** from `workflows/presets/*.yaml` files
   - Created by `CursorRulesGenerator` when presets change
   - **Always regenerated** during `init` to ensure sync with YAML files

2. **`.tapps-agents/config.yaml`** (generated with defaults)
   - Created with canonical default configuration
   - Tech stack templates applied if detected
   - User config merged if present

3. **`.cursor/mcp.json`** (generated)
   - Created with Context7 MCP server configuration
   - Merges with existing config if present

4. **`.cursorignore`** (copied from resources)
   - Copied from `tapps_agents/resources/cursor/.cursorignore`
   - Appended to if file already exists

5. **`.tapps-agents/tech-stack.yaml`** (generated)
   - Created from detected project dependencies
   - Includes expert priorities based on detected frameworks

6. **`.tapps-agents/customizations/`** (scaffold created)
   - Directory structure created
   - Example customization files copied

## Summary Table

| Category | Shipped in Package? | Copied by `init`? | Regenerated? |
|----------|---------------------|-------------------|--------------|
| **Cursor Skills** (`resources/claude/skills/`) | ✅ Yes | ✅ Yes | ❌ No (static) |
| **Claude Commands** (`resources/claude/commands/`) | ✅ Yes | ✅ Yes | ❌ No (static) |
| **Cursor Rules** (`resources/cursor/rules/`) | ✅ Yes | ✅ Yes | ⚠️ `workflow-presets.mdc` regenerated |
| **Workflow Presets** (`resources/workflows/presets/`) | ✅ Yes | ✅ Yes | ❌ No (static) |
| **Main Documentation** (`docs/`) | ❌ No | ❌ No | ❌ No (GitHub only) |
| **Root Docs** (`AGENTS.md`, `CLAUDE.md`) | ❌ No | ❌ No | ❌ No (GitHub only) |
| **Requirements** (`requirements/`) | ❌ No | ❌ No | ❌ No (GitHub only) |
| **Scripts** (`scripts/`) | ❌ No | ❌ No | ❌ No (GitHub only) |
| **Config** (`.tapps-agents/config.yaml`) | ❌ No | ✅ Yes | ✅ Yes (generated with defaults) |
| **MCP Config** (`.cursor/mcp.json`) | ❌ No | ✅ Yes | ✅ Yes (generated) |
| **Tech Stack** (`.tapps-agents/tech-stack.yaml`) | ❌ No | ✅ Yes | ✅ Yes (detected) |

## Key Points

1. **Only Runtime Resources Ship**: Only files in `tapps_agents/resources/` are included in the package (~100-200 KB)

2. **Documentation is GitHub-Only**: All `docs/` files are excluded from the package and available on GitHub

3. **`init` Copies Resources**: `tapps-agents init` copies resources from the installed package to the project

4. **One File Regenerated**: `workflow-presets.mdc` is always regenerated from YAML files during `init`

5. **Config is Generated**: Configuration files (`.tapps-agents/config.yaml`, `.cursor/mcp.json`, etc.) are generated with project-specific defaults

## How This Affects Documentation Standards

Since most documentation files are **NOT shipped** with the package:

- ✅ Documentation standards (metadata, tags, etc.) apply to GitHub repository
- ✅ CI validation runs on GitHub repository (not installed package)
- ✅ Users access documentation via GitHub (not from installed package)
- ✅ `init` only copies small runtime resources (~100-200 KB)

The documentation we created (Phase 1-5) is **framework development documentation** that:
- Helps developers understand and contribute to TappsCodingAgents
- Provides standards for users who fork/clone the repository
- Guides framework maintenance and evolution
- Is validated by CI/CD on GitHub

Users who install `tapps-agents` from PyPI get:
- Runtime resources needed for `init` to work
- Framework code
- **NOT** the full documentation repository

Users who need documentation can:
- Visit GitHub repository for full documentation
- Run `tapps-agents init` to get `.cursor/rules/` (which reference GitHub docs)
- Access docs online or clone the repository

## Related Documentation

- **[AI Documentation Standards Implementation Plan](AI_DOCUMENTATION_STANDARDS_IMPLEMENTATION_PLAN.md)** - Original implementation plan
- **[Documentation Metadata Standards](DOCUMENTATION_METADATA_STANDARDS.md)** - Metadata standards
- **[Cursor Skills Installation Guide](CURSOR_SKILLS_INSTALLATION_GUIDE.md)** - How `init` works
- **[Source Tree Organization](architecture/source-tree.md)** - Project structure

---

**Last Updated:** 2026-01-20  
**Maintained By:** TappsCodingAgents Team
