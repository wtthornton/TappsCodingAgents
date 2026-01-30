# Epic: Project Cleanup Agent

**Epic ID:** project-cleanup-001
**Created:** 2026-01-29
**Priority:** P1 (High)
**Total Story Points:** 13 points
**Estimated Duration:** 8-12 hours

---

## Epic Overview

Create an automated Project Cleanup Agent that analyzes and systematically cleans the TappsCodingAgents project structure, with primary focus on the docs/ folder (229 MD files, 3.0MB). The agent will identify cleanup opportunities, generate actionable plans, and execute improvements safely with backups and rollback capabilities.

**Goal:** Reduce docs/ from 229 files to ~120 files (45% reduction), achieve 100% naming consistency, and improve developer experience through better organization.

---

## Stories

### Story 1: ProjectAnalyzer - File Analysis Engine

**Story ID:** PCA-001
**Priority:** High
**Story Points:** 3
**Estimated Effort:** 2-3 hours

**User Story:**
> As a developer maintaining TappsCodingAgents, I want to automatically analyze the project structure to identify cleanup opportunities, so that I can make data-driven decisions about documentation organization.

**Acceptance Criteria:**
1. ✅ Scans project directory recursively using pathlib
2. ✅ Detects duplicate files using content-based hash comparison (MD5/SHA256)
3. ✅ Identifies outdated files (not modified in git for 90+ days)
4. ✅ Analyzes naming patterns and detects inconsistencies
5. ✅ Generates structured analysis report in JSON and Markdown formats
6. ✅ Completes analysis of 229 files in < 10 seconds
7. ✅ Handles edge cases: symlinks, permission errors, empty directories

**Tasks:**
- [ ] Create `ProjectAnalyzer` class with pathlib integration
- [ ] Implement content-based duplicate detection (hashlib)
- [ ] Add git integration to detect file age (GitPython)
- [ ] Implement naming pattern analysis (regex-based)
- [ ] Create report generators (JSON + Markdown)
- [ ] Add performance optimization (async file operations)
- [ ] Write unit tests (≥75% coverage)

**Dependencies:** None

**Technical Notes:**
- Use `pathlib.Path` for cross-platform compatibility
- Stream-based hashing for large files (memory efficiency)
- GitPython for git history analysis

---

### Story 2: CleanupPlanner - Intelligent Categorization

**Story ID:** PCA-002
**Priority:** High
**Story Points:** 3
**Estimated Effort:** 2-3 hours

**User Story:**
> As a developer, I want an intelligent planner that categorizes files and generates cleanup recommendations, so that I can review and approve cleanup actions before execution.

**Acceptance Criteria:**
1. ✅ Categorizes files into: Keep, Archive, Delete, Merge, Rename
2. ✅ Detects content similarity using difflib (80%+ threshold)
3. ✅ Builds dependency map (tracks file references)
4. ✅ Prioritizes actions by impact (high/medium/low)
5. ✅ Generates cleanup plan with rationale for each action
6. ✅ Calculates metrics: space savings, file reduction percentage
7. ✅ Exports plan as JSON and human-readable Markdown

**Tasks:**
- [ ] Create `CleanupPlanner` class
- [ ] Implement file categorization logic with rules engine
- [ ] Add content similarity detection (difflib.SequenceMatcher)
- [ ] Build dependency map (scan for file references)
- [ ] Implement priority scoring algorithm
- [ ] Create plan export functions (JSON + Markdown)
- [ ] Write unit tests with mock file system

**Dependencies:** PCA-001 (ProjectAnalyzer)

**Technical Notes:**
- Use difflib for text similarity (fast for markdown)
- Regex patterns to detect file references: `[filename](path)`, `docs/file.md`
- Priority scoring: impact × confidence × safety

---

### Story 3: CleanupExecutor - Safe Cleanup Operations

**Story ID:** PCA-003
**Priority:** High
**Story Points:** 5
**Estimated Effort:** 3-4 hours

**User Story:**
> As a developer, I want to safely execute cleanup operations with backups and rollback capabilities, so that I can confidently clean up the project without risk of data loss.

**Acceptance Criteria:**
1. ✅ Provides dry-run mode (preview changes without executing)
2. ✅ Creates timestamped backups before destructive operations
3. ✅ Executes file operations: delete, move, rename, merge
4. ✅ Updates cross-references and links automatically
5. ✅ Generates execution report with all changes logged
6. ✅ Supports rollback from backup on failure
7. ✅ Uses proper git operations (git mv) to preserve history
8. ✅ Requires explicit confirmation for deletions

**Tasks:**
- [ ] Create `CleanupExecutor` class
- [ ] Implement dry-run mode with change preview
- [ ] Add backup creation (ZIP archives with timestamps)
- [ ] Implement safe file operations (delete, move, rename)
- [ ] Add reference update logic (scan and replace file paths)
- [ ] Implement rollback mechanism with transaction log
- [ ] Add git integration (use git mv for renames)
- [ ] Create execution report generator
- [ ] Write integration tests (test with fixture directories)

**Dependencies:** PCA-002 (CleanupPlanner)

**Technical Notes:**
- Use shutil for file operations with error handling
- Transaction log: JSON array of operations for rollback
- Git mv preserves file history (better than OS rename)
- Validate all paths to prevent directory traversal

**Security Considerations:**
- ⚠️ Path validation to prevent operations outside project
- ⚠️ Sanitize user inputs (file patterns)
- ⚠️ Secure backup location (no world-writable permissions)

---

### Story 4: CleanupAgent Orchestrator & CLI

**Story ID:** PCA-004
**Priority:** Medium
**Story Points:** 2
**Estimated Effort:** 1-2 hours

**User Story:**
> As a developer, I want a command-line interface to orchestrate the cleanup workflow, so that I can easily run analysis, review plans, and execute cleanup operations.

**Acceptance Criteria:**
1. ✅ Provides CLI with subcommands: analyze, plan, execute, run (full workflow)
2. ✅ Displays rich console output with color-coded categories
3. ✅ Shows progress indicators during long operations
4. ✅ Supports interactive mode with user confirmations
5. ✅ Provides comprehensive logging (debug mode available)
6. ✅ Exports reports to specified output paths

**Tasks:**
- [ ] Create `CleanupAgent` orchestrator class
- [ ] Add argparse for CLI interface
- [ ] Integrate Rich library for console output
- [ ] Implement progress indicators and status updates
- [ ] Add interactive confirmation prompts
- [ ] Configure logging (console + file)
- [ ] Create usage documentation
- [ ] Write CLI integration tests

**Dependencies:** PCA-001, PCA-002, PCA-003

**CLI Commands:**
```bash
# Analyze project structure
python -m tapps_agents.utils.project_cleanup_agent analyze --path ./docs

# Generate cleanup plan
python -m tapps_agents.utils.project_cleanup_agent plan --report analysis.json

# Execute cleanup (dry-run by default)
python -m tapps_agents.utils.project_cleanup_agent execute --plan cleanup-plan.json --dry-run

# Full automated cleanup
python -m tapps_agents.utils.project_cleanup_agent run --path ./docs --backup --interactive
```

---

## Epic-Level Acceptance Criteria

1. ✅ Reduces docs/ folder from 229 files to ~120 files (≥40% reduction)
2. ✅ Achieves 100% naming consistency (all kebab-case.md)
3. ✅ Zero data loss (all operations backed up and reversible)
4. ✅ Test coverage ≥ 75% across all modules
5. ✅ Quality score ≥ 75 (reviewer score)
6. ✅ Security score ≥ 8.5 (file operations are safe)
7. ✅ Performance: Analysis < 10s, Execution < 30s
8. ✅ Documentation complete (docstrings + usage guide)

---

## Dependencies & Execution Order

```
PCA-001 (ProjectAnalyzer)
    ↓
PCA-002 (CleanupPlanner)
    ↓
PCA-003 (CleanupExecutor)
    ↓
PCA-004 (CleanupAgent CLI)
```

**Recommended Approach:** Implement in order (PCA-001 → PCA-002 → PCA-003 → PCA-004) with tests after each story.

---

## Technical Stack

**Core Dependencies:**
- Python 3.10+
- pathlib (standard library)
- hashlib (standard library)
- difflib (standard library)
- GitPython (git operations)
- Rich (console output)
- Pydantic (data validation)
- aiofiles (async file operations)

**Development Dependencies:**
- pytest (testing framework)
- pytest-asyncio (async test support)
- pytest-cov (coverage reporting)
- mypy (type checking)
- ruff (linting)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Data loss during cleanup | High | Mandatory backups, dry-run mode, rollback capability |
| Git history corruption | Medium | Use git mv instead of OS rename |
| Performance issues with large files | Low | Stream-based hashing, async operations |
| False positive duplicates | Medium | Content-based hash + manual review step |
| Permission errors | Low | Graceful error handling, skip problematic files |

---

## Success Metrics

**Quantitative:**
- Files reduced: 229 → ~120 (≥40%)
- Space saved: ~1.5MB (≥50%)
- Naming consistency: 100% (all kebab-case)
- Test coverage: ≥75%
- Quality score: ≥75

**Qualitative:**
- Improved developer experience (easier navigation)
- Reduced documentation maintenance burden
- Clearer project structure
- No data loss incidents

---

**End of Epic**
