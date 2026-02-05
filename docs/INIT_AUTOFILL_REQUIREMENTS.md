# Init and Auto-Fill Requirements for TappsCodingAgents

**Date:** 2026-02-04
**Status:** Draft
**Priority:** High
**Source:** Site24x7 Project Evaluation (TAPPS_AGENTS_EVALUATION_2026-02-04.md)

## Overview

This document outlines requirements for automated initialization, reset, and auto-fill capabilities that should be implemented in TappsCodingAgents. These requirements are based on a comprehensive audit of the Site24x7 project, which revealed 10 areas requiring manual intervention that should have been automated.

## Problem Statement

Currently, `tapps-agents init` and `init --reset` require significant manual follow-up work to:
- Populate tech-stack.yaml from project dependencies
- Create and configure domain-specific experts
- Ensure Context7 cache coverage for project libraries
- Keep RAG knowledge synchronized with codebase changes
- Link knowledge files to appropriate experts
- Validate configuration file syntax

**Goal:** Make `tapps-agents init` and `init --reset` fully automatic, with intelligent auto-fill that maintains synchronization between codebase and configuration.

## Core Requirements

### R1: Tech Stack Auto-Detection

**Priority:** P0 (Critical)
**Effort:** Medium

**Description:**
Automatically populate `.tapps-agents/tech-stack.yaml` from project dependencies and code analysis.

**Acceptance Criteria:**
- Parse `requirements.txt` and extract all libraries
- Parse `pyproject.toml` [tool.poetry.dependencies] and [project.dependencies]
- Detect programming languages from file extensions (*.py, *.js, *.ts, etc.)
- Detect frameworks from imports (Django, FastAPI, React, etc.)
- Infer domains from project structure and dependencies (e.g., "monitoring" from "prometheus-client")
- Write complete tech-stack.yaml with: languages, libraries, frameworks, domains, context7_priority

**Implementation Notes:**
- Use static analysis for framework detection (AST parsing for imports)
- Support multiple dependency file formats (requirements.txt, pyproject.toml, setup.py, package.json, Gemfile, etc.)
- Prioritize Context7 libraries based on import frequency and project criticality

### R2: Context7 Cache Auto-Population

**Priority:** P0 (Critical)
**Effort:** High

**Description:**
Automatically ensure all project libraries are in Context7 cache or queued for fetch.

**Acceptance Criteria:**
- On `init` or `init --reset`, scan tech-stack.yaml libraries
- Check each library against `.tapps-agents/kb/context7-cache/libraries/`
- For missing libraries, queue Context7 fetch request
- Log libraries that are queued vs. already cached
- Provide `--skip-context7` flag to bypass this step
- Support priority ordering (fetch critical libraries first)

**Implementation Notes:**
- Need Context7 API integration or local indexing capability
- Handle rate limiting and API errors gracefully
- Store fetch queue in config for resumable operations
- Consider async/background fetching for large dependency sets

### R3: Expert Auto-Generation from Knowledge Files

**Priority:** P1 (High)
**Effort:** High

**Description:**
Automatically create or suggest domain-specific experts when knowledge files exist without corresponding experts.

**Acceptance Criteria:**
- Scan `.tapps-agents/knowledge/` directory for markdown files
- Analyze file content to extract domain, triggers, and key concepts
- Check if an expert exists that covers this domain
- If no expert exists, create expert configuration with:
  - Generated name (expert-{domain}-{topic})
  - Inferred priority (0.70-0.90 based on project analysis)
  - Extracted consultation triggers from file content
  - Reference to knowledge file in knowledge_files list
- Prompt user for confirmation before adding new experts
- Support `--auto-experts` flag for automatic expert creation

**Implementation Notes:**
- Use NLP/LLM to extract domain concepts and triggers from knowledge files
- Follow expert naming conventions from existing experts.yaml
- Set conservative default priority; allow user to adjust
- Generate meaningful expert descriptions from file summaries

### R4: RAG Knowledge Synchronization

**Priority:** P1 (High)
**Effort:** High

**Description:**
Keep RAG knowledge base synchronized with codebase changes (package renames, API changes, architecture updates).

**Acceptance Criteria:**
- Detect package/module renames (e.g., site24x7_client → site24x7)
- Find stale imports in RAG knowledge files (RAG_SUMMARY.md, INDEX.md, etc.)
- Update code examples to match current API patterns
- Sync project-overview.md with actual directory structure
- Flag deprecated references for manual review
- Provide `tapps-agents rag sync` command
- Optionally run on every `init --reset`

**Implementation Notes:**
- AST analysis to extract current imports and API patterns
- Diff old vs. new package structure
- Use regex + NLP to find and replace stale references in markdown
- Generate change report for user review before applying
- Preserve custom documentation while updating technical references

### R5: Expert-Knowledge File Linking

**Priority:** P2 (Medium)
**Effort:** Medium

**Description:**
Automatically link knowledge files to experts when expert description/triggers match file content.

**Acceptance Criteria:**
- For each expert in experts.yaml, analyze description and consultation_triggers
- Search `.tapps-agents/knowledge/` for files with matching concepts
- Suggest adding missing files to expert's knowledge_files list
- Detect when knowledge file exists but isn't referenced by any expert
- Provide interactive prompt for each suggested link
- Support `--auto-link` flag for automatic linking

**Implementation Notes:**
- Use semantic similarity (embeddings) to match expert triggers with file content
- Consider file location in knowledge/ subdirectories for domain matching
- Avoid duplicate links across multiple experts (prefer highest priority expert)
- Preserve manual knowledge_files entries

### R6: Configuration Validation

**Priority:** P1 (High)
**Effort:** Low

**Description:**
Validate all YAML configuration files for syntax errors, missing fields, and broken references.

**Acceptance Criteria:**
- On `init`, `init --reset`, or `tapps-agents validate`, check:
  - experts.yaml: YAML syntax, indentation, required fields (name, description, priority, domain, consultation_triggers, knowledge_files)
  - domains.md: Referenced experts exist, knowledge files exist
  - tech-stack.yaml: Valid structure (languages, libraries, frameworks, domains)
  - config.yaml: Valid configuration keys and values
- Check all knowledge_files paths exist
- Report errors with line numbers and suggested fixes
- Optionally auto-fix common issues (indentation, missing fields)
- Exit with error code if validation fails

**Implementation Notes:**
- Use PyYAML strict parsing with error location
- Validate file paths relative to .tapps-agents/
- Provide actionable error messages (not just "YAML parse error")
- Support `--fix` flag to auto-correct fixable issues

### R7: Project Overview Auto-Generation

**Priority:** P2 (Medium)
**Effort:** Medium

**Description:**
Generate or update project-overview.md from project metadata and directory structure.

**Acceptance Criteria:**
- Extract project name, version, description from pyproject.toml or package.json
- Scan directory structure to identify key components (src/, tests/, docs/, etc.)
- Detect architecture patterns (monolith, microservices, client-library, etc.)
- List main modules and their purposes
- Include dependency summary (frameworks, libraries)
- Generate or update `.tapps-agents/knowledge/general/project-overview.md`
- Preserve manually-added sections (e.g., "Business Context")

**Implementation Notes:**
- Use project layout heuristics (e.g., presence of setup.py, src/, tests/)
- Infer project type from dependencies (web framework → web app, requests → API client, etc.)
- Template-based generation with placeholders for manual content
- Support incremental updates (don't overwrite everything)

### R8: Domain Auto-Detection

**Priority:** P2 (Medium)
**Effort:** Medium

**Description:**
Infer project domains from dependencies, directory structure, and knowledge files.

**Acceptance Criteria:**
- Detect domains from:
  - Library names (e.g., "matplotlib" → visualization domain)
  - Directory names (e.g., "reporting/" → reporting domain)
  - Knowledge file topics (e.g., notification-profile-alerting.md → notification domain)
- Create or update `.tapps-agents/domains.md` with detected domains
- Map experts to domains
- List knowledge files per domain
- Prompt user to confirm detected domains

**Implementation Notes:**
- Use domain taxonomy (predefined mappings like "plotly" → visualization)
- Allow custom domain definitions in config
- Merge detected domains with manually-defined domains
- Preserve domain descriptions when updating

### R9: Incremental Auto-Fill

**Priority:** P2 (Medium)
**Effort:** High

**Description:**
Continuously keep configuration synchronized with codebase changes, not just on `init`.

**Acceptance Criteria:**
- Detect when requirements.txt or pyproject.toml changes
- Detect when new knowledge files are added to .tapps-agents/knowledge/
- Detect when code structure changes (package rename, new modules)
- Offer to update tech-stack.yaml, experts.yaml, and RAG knowledge
- Provide git hook integration (pre-commit, post-merge)
- Support `tapps-agents sync` command for manual sync

**Implementation Notes:**
- File watcher or git hook to trigger sync
- Incremental updates (only sync what changed)
- Background sync with user notification
- Store last-sync timestamp to detect changes

### R10: Interactive Configuration Wizard

**Priority:** P3 (Nice to Have)
**Effort:** Medium

**Description:**
Provide interactive wizard for `tapps-agents init` that asks questions and guides setup.

**Acceptance Criteria:**
- When running `tapps-agents init` in unconfigured project, start wizard
- Ask questions:
  - Project type (library, web app, CLI tool, etc.)
  - Primary domains (monitoring, reporting, data processing, etc.)
  - Tech stack (or auto-detect and confirm)
  - Enable Context7 fetching? (y/n)
  - Create default experts? (y/n)
  - Generate project-overview? (y/n)
- Apply selections to generate complete configuration
- Support `--wizard` flag to force wizard mode
- Support `--no-wizard` for fully automatic mode

**Implementation Notes:**
- Use rich/click for interactive prompts
- Save wizard responses for future re-init
- Provide sensible defaults for all questions
- Allow skipping wizard with `--yes` flag

## Non-Functional Requirements

### NFR1: Performance

- Tech stack detection: < 5 seconds for typical project
- Context7 queuing: < 1 second per library (async)
- Expert auto-generation: < 10 seconds per knowledge file
- RAG sync: < 30 seconds for typical project
- Validation: < 2 seconds

### NFR2: Usability

- Clear progress indicators for long operations
- Actionable error messages with suggested fixes
- Confirmation prompts for destructive changes
- Dry-run mode (`--dry-run`) to preview changes
- Verbose mode (`--verbose`) for debugging

### NFR3: Reliability

- Graceful handling of missing files, network errors
- Transaction-like updates (rollback on error)
- Backup existing configuration before major changes
- Validation before writing changes

### NFR4: Maintainability

- Modular design (separate classes for each requirement)
- Comprehensive unit tests (≥80% coverage)
- Integration tests with sample projects
- Documentation for each auto-fill capability

## Implementation Phases

### Phase 1: Foundation (R6, R1)
1. Configuration validation
2. Tech stack auto-detection

### Phase 2: Context7 Integration (R2)
3. Context7 cache auto-population

### Phase 3: Expert Intelligence (R3, R5, R8)
4. Expert auto-generation
5. Expert-knowledge linking
6. Domain auto-detection

### Phase 4: Knowledge Sync (R4, R7)
7. RAG knowledge synchronization
8. Project overview auto-generation

### Phase 5: Continuous Sync (R9, R10)
9. Incremental auto-fill
10. Interactive configuration wizard

## Success Metrics

- **Reduction in manual setup time:** From ~2 hours to < 5 minutes
- **Configuration accuracy:** ≥95% of auto-detected items are correct
- **User satisfaction:** Positive feedback from ≥80% of users
- **Init coverage:** ≥90% of projects require zero manual fixes after init

## Open Questions

1. How to handle conflicts between auto-detected and manually-configured items?
2. Should Context7 fetching be synchronous (blocking init) or async (background)?
3. What's the priority order for Context7 fetching when many libraries are missing?
4. How to detect when RAG sync is needed vs. when to skip (performance)?
5. Should expert auto-generation create experts immediately or only suggest them?

## References

- [Site24x7 Evaluation](C:\cursor\Site24x7\docs\TAPPS_AGENTS_EVALUATION_2026-02-04.md)
- [Context7 Documentation](docs/CONTEXT7.md) (if exists)
- [Expert System Guide](docs/expert-priority-guide.md)
- [Knowledge Base Guide](docs/knowledge-base-guide.md)
- [Configuration Reference](docs/CONFIGURATION.md)
