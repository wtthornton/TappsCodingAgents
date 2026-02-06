# Phase 4: Knowledge Synchronization - Planning Complete

**Date:** 2026-02-05
**Status:** ✅ Planning Complete | ⏳ Implementation Pending
**Workflow:** Full SDLC (Steps 1-4 Complete)

## Executive Summary

Phase 4 planning is complete with comprehensive requirements, user stories, and architecture design. This document captures all planning artifacts for implementation execution.

**Planning Artifacts:**
- ✅ Enhanced Prompt (7-stage enhancement)
- ✅ Requirements Analysis (11 FR + 4 NFR)
- ✅ User Stories (14 stories, 34 points)
- ✅ Architecture Design (complete system design)

**Ready for Implementation:**
- Clear specifications for RagSynchronizer module
- Clear specifications for ProjectOverviewGenerator module
- Data models defined and validated
- Security and performance architecture complete
- Test strategy defined (50+ tests, ≥90% coverage)

---

## 1. Enhanced Prompt

### Metadata
- **Intent:** Implementation (build new modules)
- **Scope:** Medium-Large (2 modules + CLI + integration)
- **Domains:** automation, configuration, documentation, file-io
- **Workflow Type:** Full SDLC (framework development)
- **Complexity:** High (AST analysis, diff generation, backup/rollback)

### Summary

Implement Phase 4: Knowledge Synchronization - RAG sync and project overview generation for TappsCodingAgents framework.

**Context:** Phase 4 of 5 for Init Auto-Fill. Phases 1-3.2 complete. Implements RAG knowledge synchronization to keep knowledge files up-to-date when code changes.

**Scope:**
- 2 core modules (RagSynchronizer, ProjectOverviewGenerator)
- 1 CLI command (`tapps-agents rag sync`)
- Integration with init --reset workflow

**Quality Targets:**
- Test coverage: ≥90%
- Overall quality: ≥75
- Security score: ≥8.5
- All functions: <100 lines

---

## 2. Requirements Analysis

### Functional Requirements

#### FR1: Package Rename Detection
- Detect package/module renames using AST analysis
- Compare current vs. historical imports
- Return `List[Rename]` with confidence scores
- Execution time < 5 seconds

#### FR2: Stale Import Finding
- Scan RAG knowledge files for outdated imports
- Use regex to extract imports from markdown
- Return `List[StaleReference]` with suggestions
- Execution time < 3 seconds

#### FR3: Code Example Updates
- Update code blocks in knowledge files
- Use regex + AST validation
- Preserve formatting and indentation
- Generate detailed change log

#### FR4: Change Reporting
- Generate comprehensive change report
- Include file list, diff view, summary
- Save to `.tapps-agents/sync-reports/`
- Support `--report-only` flag

#### FR5: Backup and Rollback
- Backup to `.tapps-agents/backups/{timestamp}/`
- Generate manifest with SHA256 checksums
- Automatic rollback on error
- Manual rollback: `tapps-agents rag rollback {timestamp}`
- Keep last 5 backups

#### FR6: User Confirmation
- Display change report in terminal
- Prompt: "Apply changes? [y/N/view/select]"
- Support `--auto-apply` flag
- Detect conflicts (file modified since sync)

#### FR7: Project Metadata Extraction
- Read pyproject.toml (tomllib) and package.json (json)
- Extract: name, version, description, authors, license
- Handle missing/malformed files gracefully
- Fallback to `.git/config` for name

#### FR8: Architecture Pattern Detection
- Detect: library, web app, CLI, MVC, microservices, monolith
- Use directory structure heuristics
- Return confidence score (0.0-1.0)
- List indicators

#### FR9: Component Mapping
- Identify main modules
- Infer purposes from names/docstrings
- Detect inter-module dependencies
- Generate Mermaid graph

#### FR10: Project Overview Generation
- Generate comprehensive project-overview.md
- Include: metadata, architecture, components
- Preserve manually-added sections
- Support incremental updates

#### FR11: CLI Integration
- Command: `tapps-agents rag sync [OPTIONS]`
- Flags: `--dry-run`, `--auto-apply`, `--report-only`, `--backup-dir`
- Exit codes: 0 (success), 1 (no changes), 2 (cancelled), 3 (error)
- Integrate with `init --reset`

### Non-Functional Requirements

#### NFR1: Performance
- Package rename detection: <5s
- Stale import finding: <3s
- Total RAG sync: <30s
- Backup creation: <5s

#### NFR2: Quality
- Test coverage: ≥90%
- Overall quality: ≥75
- Security score: ≥8.5
- Maintainability: ≥7.0
- All functions: <100 lines

#### NFR3: Reliability
- Zero data loss during sync
- 100% successful rollback on errors
- Backup integrity: 100% verification
- Atomic operations: all-or-nothing

#### NFR4: Maintainability
- Modular design: <100 lines per method
- Type hints: 100% coverage
- Docstrings: 100% public methods
- Configuration-driven behavior

### Effort Estimation

| Task | Complexity | Hours |
|------|------------|-------|
| RagSynchronizer | Complex | 6 |
| ProjectOverviewGenerator | Medium | 3 |
| CLI command | Simple | 2 |
| init integration | Simple | 1 |
| Unit tests (50+) | Medium | 3 |
| Integration tests | Medium | 1 |
| Documentation | Simple | 1 |
| **Total** | | **17** |

**With Buffer (20%):** 20 hours

---

## 3. User Stories

### Epic: INIT-PHASE4

**Total Story Points:** 34
**Estimated Effort:** 21 hours (17 dev + 4 testing)
**Priority:** P0 (Critical - Framework Development)

### Story Summary

| ID | Story | Points | Effort | Priority | Dependencies |
|----|-------|--------|--------|----------|--------------|
| 001 | Package Rename Detection | 5 | 3h | P0 | None |
| 002 | Stale Import Finding | 3 | 2h | P0 | 001 |
| 003 | Backup and Rollback | 5 | 3h | P0 | None |
| 004 | Change Reporting | 3 | 2h | P1 | 001, 002 |
| 005 | Code Example Updates | 5 | 3h | P0 | 001, 002 |
| 006 | User Confirmation | 3 | 2h | P1 | 003, 004, 005 |
| 007 | Metadata Extraction | 2 | 1.5h | P1 | None |
| 008 | Architecture Detection | 3 | 2h | P2 | None |
| 009 | Component Mapping | 3 | 2h | P2 | None |
| 010 | Overview Generation | 3 | 2h | P1 | 007, 008, 009 |
| 011 | CLI Command | 2 | 1.5h | P0 | 001-006 |
| 012 | init Integration | 1 | 1h | P0 | 001-011 |
| 013 | Configuration & Docs | 1 | 1h | P1 | 001-012 |
| 014 | Comprehensive Testing | 5 | 4h | P0 | 001-013 |

### Implementation Order

1. Story 003 (Backup system - critical for safety)
2. Story 001 (Package rename detection - foundation)
3. Story 002 (Stale import finding)
4. Story 004 (Change reporting)
5. Story 005 (Code example updates)
6. Story 006 (User confirmation)
7. Story 007 (Metadata extraction)
8. Story 008 (Architecture detection)
9. Story 009 (Component mapping)
10. Story 010 (Project overview)
11. Story 011 (CLI command)
12. Story 012 (init integration)
13. Story 013 (Documentation)
14. Story 014 (Testing - continuous)

---

## 4. Architecture Design

### Architecture Pattern

**Pattern:** Modular Layered Architecture with Command Pattern
**Design Philosophy:** Separation of Concerns, Single Responsibility, Fail-Safe Operations

### Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Interface Layer                         │
│  ┌──────────────────┐         ┌─────────────────────────────┐  │
│  │  CLI Command     │         │  init_project.py            │  │
│  │  rag.py          │────────▶│  Integration                │  │
│  └──────────────────┘         └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Application Layer                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │            RagSynchronizer (Orchestrator)                  │ │
│  │  • Coordinates sync workflow                               │ │
│  │  • Manages backup/rollback                                 │ │
│  │  • Generates change reports                                │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │        ProjectOverviewGenerator (Generator)                │ │
│  │  • Extracts metadata                                       │ │
│  │  • Detects architecture patterns                           │ │
│  │  • Generates component map                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Data Models

```python
@dataclass
class Rename:
    old_name: str
    new_name: str
    file_path: Path
    confidence: float  # 0.0-1.0

@dataclass
class StaleReference:
    file_path: Path
    line_number: int
    old_import: str
    suggested_import: str
    context: str

@dataclass
class ChangeReport:
    timestamp: str
    total_files: int
    total_changes: int
    renames: List[Rename]
    stale_refs: List[StaleReference]
    diff_preview: str
    backup_path: Optional[Path]

@dataclass
class ProjectMetadata:
    name: str
    version: str
    description: str
    authors: List[str]
    license: str
    dependencies: Dict[str, str]

class ArchitectureType(Enum):
    LIBRARY = "library"
    WEB_APP = "web_app"
    CLI_TOOL = "cli_tool"
    MVC = "mvc"
    MICROSERVICES = "microservices"
    MONOLITH = "monolith"

@dataclass
class ArchitecturePattern:
    pattern: ArchitectureType
    confidence: float
    indicators: List[str]

@dataclass
class BackupManifest:
    timestamp: str
    backup_dir: Path
    files: List[Path]
    checksums: Dict[str, str]  # file -> SHA256
```

### Security Architecture

| Threat | Impact | Mitigation |
|--------|--------|------------|
| Path Traversal | Critical | Use `Path().resolve()` and validate within project |
| Backup Corruption | High | SHA256 checksums, integrity verification |
| Malicious Code Injection | High | AST validation, no eval()/exec() |
| Data Loss | Critical | Mandatory backups, atomic operations, rollback |
| Unintended Deletion | High | Backup before changes, confirmation, dry-run |

### Performance Targets

| Operation | Target | Strategy |
|-----------|--------|----------|
| Package Rename Detection | <5s | Cache AST, parallel processing |
| Stale Import Finding | <3s | Regex scanning, file batching |
| Backup Creation | <5s | Async file copy |
| Total Sync | <30s | Pipeline optimization |

---

## 5. File Structure

```
tapps_agents/
├── core/
│   ├── sync/
│   │   ├── __init__.py
│   │   └── rag_synchronizer.py          # NEW
│   ├── generators/
│   │   ├── __init__.py (updated)
│   │   └── project_overview_generator.py # NEW
│   └── init_project.py (modified)
├── cli/
│   └── rag.py                           # NEW

tests/
└── tapps_agents/
    ├── core/
    │   ├── sync/
    │   │   └── test_rag_synchronizer.py # NEW (30+ tests)
    │   └── generators/
    │       └── test_project_overview_generator.py # NEW (20+ tests)
    └── cli/
        └── test_rag.py                  # NEW (5+ tests)

.tapps-agents/
├── backups/
│   └── {timestamp}/
├── sync-reports/
│   └── {timestamp}.md
└── config.yaml (add rag section)
```

---

## 6. Configuration

```yaml
rag:
  # Sync Settings
  sync_on_init_reset: true
  preserve_custom_content: true
  backup_before_sync: true

  # Backup Settings
  backup_dir: .tapps-agents/backups
  backup_retention: 5

  # Detection Settings
  confidence_threshold: 0.7

  # Report Settings
  report_dir: .tapps-agents/sync-reports
  report_format: markdown

  # Performance Settings
  max_file_size: 1048576  # 1MB
  cache_ast_analysis: true
```

---

## 7. Technology Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| AST Analysis | Python `ast` | Built-in, reliable |
| TOML Parsing | `tomllib` (3.11+) | Built-in, standard |
| JSON Parsing | `json` | Built-in, standard |
| Regex | `re` | Built-in, sufficient |
| Checksums | `hashlib` (SHA256) | Built-in, secure |
| File Operations | `pathlib`, `shutil` | Built-in, modern |
| CLI | `argparse` | Built-in, sufficient |

**Python Version:** ≥3.11 (for tomllib)
**External Dependencies:** Minimal (prefer stdlib)
**Optional:** `rich` for enhanced CLI

---

## 8. Testing Strategy

### Test Pyramid

```
           ┌──────────┐
           │    E2E   │  (10 tests)
           └──────────┘
         ┌──────────────┐
         │ Integration  │  (15 tests)
         └──────────────┘
      ┌────────────────────┐
      │   Unit Tests       │  (30+ tests)
      └────────────────────┘
```

### Test Categories

1. **Unit Tests (30+)**
   - Each method tested independently
   - Mock file system operations
   - Test edge cases and errors

2. **Integration Tests (15)**
   - Component interactions
   - Real file system (tmp_path)
   - End-to-end workflows

3. **E2E Tests (10)**
   - Complete user journeys
   - CLI execution
   - Rollback scenarios

4. **Performance Tests (5)**
   - Execution time validation
   - Large codebase testing
   - Cache effectiveness

**Target:** 50+ tests, ≥90% coverage

---

## 9. Quality Gates

```python
QUALITY_GATES = {
    "test_coverage": 0.90,      # ≥90%
    "overall_quality": 75,       # ≥75
    "security_score": 8.5,       # ≥8.5
    "maintainability": 7.0,      # ≥7.0
    "max_function_lines": 100,   # <100 lines
}
```

**Enforcement:**
- Run coverage analysis
- Run quality review (@reviewer)
- Run security scan (@ops)
- Verify all gates pass before merge

---

## 10. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Data Loss | Low | Critical | Mandatory backups, atomic ops |
| Performance Issues | Medium | High | AST caching, parallel processing |
| False Positives | Medium | Medium | Confidence scoring, user review |
| Rollback Failure | Low | High | Integrity verification, checksums |
| Git History Analysis | Medium | Medium | Fallback to simple detection |

---

## 11. Success Metrics

1. ✅ All 11 functional requirements implemented
2. ✅ All 4 non-functional requirements met
3. ✅ 50+ unit tests passing
4. ✅ Test coverage ≥90%
5. ✅ Quality score ≥75
6. ✅ Security score ≥8.5
7. ✅ Zero data loss in testing
8. ✅ 100% successful rollback on errors
9. ✅ CLI functional with all flags
10. ✅ init --reset integration working

---

## 12. Implementation Guide

### Step-by-Step Implementation

**Phase 1: Data Models (1 hour)**
1. Create data classes in `rag_synchronizer.py`
2. Add validation to `__post_init__`
3. Write unit tests for data models

**Phase 2: Backup System (3 hours)**
1. Implement `backup_knowledge_files()`
2. Implement `BackupManifest` generation
3. Add SHA256 checksum calculation
4. Implement rollback logic
5. Write backup tests (10+ tests)

**Phase 3: Detection Logic (5 hours)**
1. Implement `detect_package_renames()` with AST
2. Implement `find_stale_imports()` with regex
3. Add confidence score calculation
4. Write detection tests (18+ tests)

**Phase 4: Update Logic (3 hours)**
1. Implement `update_code_examples()`
2. Add atomic file writes
3. Implement `generate_change_report()`
4. Write update tests (12+ tests)

**Phase 5: Overview Generator (5 hours)**
1. Implement metadata extraction
2. Implement architecture detection
3. Implement component mapping
4. Implement overview generation
5. Write generator tests (20+ tests)

**Phase 6: CLI & Integration (3 hours)**
1. Create `tapps_agents/cli/rag.py`
2. Add sync_command with all flags
3. Integrate with init_project.py
4. Write CLI tests (5+ tests)

**Phase 7: Documentation (1 hour)**
1. Create RAG_SYNC_GUIDE.md
2. Update INIT_AUTOFILL_IMPLEMENTATION_SUMMARY.md
3. Update CLI_REFERENCE.md

**Total:** 21 hours

---

## 13. Next Steps

### Immediate (Ready for Implementation)

1. **Start Implementation**
   - Use this planning document as guide
   - Follow implementation order
   - Start with backup system (critical)

2. **Create Branch**
   ```bash
   git checkout -b tapps-agents/phase-4-knowledge-sync
   ```

3. **Implement in Order**
   - Data models → Backup → Detection → Update → Generator → CLI

4. **Run Quality Gates**
   - Test coverage ≥90%
   - Quality score ≥75
   - Security score ≥8.5

5. **Merge to Main**
   - Create PR with quality scores
   - Verify all tests passing
   - Update version/changelog

### Future Phases

**Phase 5: Continuous Sync and UX (Weeks 10-12)**
- Incremental auto-fill monitor
- Interactive configuration wizard
- Git hook integration
- Background sync

---

## 14. Documentation References

**Related Documents:**
- `docs/INIT_AUTOFILL_DETAILED_REQUIREMENTS.md` - Full requirements spec
- `docs/INIT_AUTOFILL_IMPLEMENTATION_SUMMARY.md` - Overall progress
- `docs/implementation/phases-1-2-3-complete-summary.md` - Previous phases
- `docs/lessons-learned/phase-3-implementation-anti-pattern.md` - Lessons learned

**Architecture Documents:**
- See Section 4 above for complete architecture
- See Section 5 for file structure
- See Section 8 for testing strategy

---

## 15. Appendix: Detailed Requirements

### FR1: Package Rename Detection (Detailed)

**Implementation Details:**
```python
def detect_package_renames(self) -> List[Rename]:
    """Detect package renames using AST analysis."""
    # 1. Extract current imports
    current_imports = self._extract_current_imports()

    # 2. Extract historical imports from Git
    historical_imports = self._extract_historical_imports()

    # 3. Compare and detect renames
    renames = self._compare_imports(current_imports, historical_imports)

    # 4. Calculate confidence scores
    return [self._add_confidence(r) for r in renames]
```

**Edge Cases:**
- Aliased imports (`import foo as bar`)
- Relative imports (`from . import foo`)
- Star imports (`from foo import *`)
- Multi-line imports
- Commented imports

**Testing:**
- Test with real package renames
- Test with false positives
- Test confidence scoring
- Test performance with large codebases

---

**Status:** ✅ Planning Complete
**Last Updated:** 2026-02-05
**Next Review:** Implementation kickoff
