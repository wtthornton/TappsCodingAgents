# User Story: Reference Updating Enhancement - Comparison Implementation

**Story ID:** REF-UPDATE-001
**Epic:** Project Cleanup Agent Enhancement
**Created:** 2026-01-29
**Priority:** High
**Story Points:** 5
**Status:** In Progress (Simple Mode Execution)

---

## Story

**As a** developer using the Project Cleanup Agent
**I want** automatic reference updating when files are renamed/moved
**So that** documentation links and cross-references remain intact without manual updates

---

## Context

**Existing Implementation:**
- Manual implementation exists (lines 751-878 in `project_cleanup_agent.py`)
- ReferenceUpdater class with pattern-based detection
- Currently supports markdown links and relative paths
- Integration with RenameStrategy and MoveStrategy complete
- Production-ready with comprehensive testing

**Goal of This Story:**
- Create comparison implementation via Simple Mode workflow
- Validate approach and identify potential improvements
- Document differences and trade-offs
- Determine if any enhancements should be incorporated

---

## Acceptance Criteria

### Primary Criteria

1. ✅ **Pattern Detection**
   - Detect markdown links: `[text](file.md)`
   - Detect relative paths: `docs/file.md`, `./file.md`
   - Detect code imports: `from module import file` (stretch goal)
   - Zero false positives in test scenarios

2. ✅ **Reference Updating**
   - Update references to new filenames
   - Preserve relative path structure
   - Support dry-run mode (preview without modifying)
   - Track number of references updated

3. ✅ **Strategy Integration**
   - Integrate with RenameStrategy
   - Integrate with MoveStrategy
   - Pass `project_root` to strategies
   - Store `references_updated` in OperationResult

4. ✅ **Quality Gates**
   - Overall code score ≥ 70
   - Security score ≥ 7.0
   - Test coverage ≥ 75%
   - Zero security vulnerabilities

5. ✅ **Performance**
   - Scan 1000 files in < 1 second
   - Memory usage < 100MB
   - Async scanning if beneficial

### Comparison Criteria

6. ✅ **Implementation Comparison**
   - Document differences from manual implementation
   - Identify improvements or alternative approaches
   - Analyze performance differences
   - Compare test coverage

7. ✅ **Validation**
   - No regression in functionality
   - Equal or better pattern matching accuracy
   - Equal or better performance
   - Equal or better maintainability

---

## Tasks

### Task 1: Analyze Existing Implementation ⏱️ 15 min

**Objective:** Understand manual implementation approach

**Subtasks:**
- [ ] Read ReferenceUpdater class (lines 751-878)
- [ ] Document pattern detection strategy
- [ ] Analyze integration with strategies
- [ ] Identify strengths and potential improvements

**Deliverable:** Implementation analysis document

---

### Task 2: Design Comparison Implementation ⏱️ 20 min

**Objective:** Design alternative approach if improvements identified

**Subtasks:**
- [ ] Review enhanced prompt and requirements
- [ ] Design pattern detection system
- [ ] Plan strategy integration
- [ ] Document design decisions

**Deliverable:** Architecture design document

---

### Task 3: Implement ReferenceUpdater ⏱️ 30 min

**Objective:** Implement reference updating logic

**Subtasks:**
- [ ] Create ReferenceUpdater class (or enhance existing)
- [ ] Implement pattern detection methods
- [ ] Add scan_and_update_references() method
- [ ] Support dry-run mode
- [ ] Add comprehensive docstrings

**Deliverable:** ReferenceUpdater implementation

---

### Task 4: Integrate with Strategies ⏱️ 20 min

**Objective:** Connect ReferenceUpdater with cleanup strategies

**Subtasks:**
- [ ] Update RenameStrategy.__init__() to accept project_root
- [ ] Update RenameStrategy.execute() to call reference updater
- [ ] Update MoveStrategy.__init__() to accept project_root
- [ ] Update MoveStrategy.execute() to call reference updater
- [ ] Update CleanupExecutor to pass project_root to strategies

**Deliverable:** Strategy integration code

---

### Task 5: Generate Tests ⏱️ 40 min

**Objective:** Comprehensive test coverage ≥75%

**Subtasks:**
- [ ] Unit tests for pattern detection
  - Test markdown link pattern
  - Test relative path pattern
  - Test edge cases (false positives, special characters)
- [ ] Integration tests for workflows
  - Test rename with reference updating
  - Test move with reference updating
  - Test dry-run mode
- [ ] Performance tests
  - Test with 1000 files
  - Measure scan time
- [ ] Comparison tests
  - Compare with manual implementation
  - Validate no regression

**Deliverable:** Test suite with ≥75% coverage

---

### Task 6: Code Review ⏱️ 15 min

**Objective:** Ensure code quality meets standards

**Subtasks:**
- [ ] Run code review (score ≥ 70)
- [ ] Check security score (≥ 7.0)
- [ ] Verify test coverage (≥ 75%)
- [ ] Address any issues found

**Deliverable:** Code review report

---

### Task 7: Compare Implementations ⏱️ 20 min

**Objective:** Document differences and recommendations

**Subtasks:**
- [ ] Compare pattern detection approaches
- [ ] Compare performance metrics
- [ ] Compare test coverage
- [ ] Identify improvements or trade-offs
- [ ] Generate comparison report

**Deliverable:** Implementation comparison report

---

## Technical Specifications

### ReferenceUpdater Class

```python
class ReferenceUpdater:
    """Scan and update file references to maintain link integrity."""

    def __init__(self, project_root: Path):
        """Initialize with project root for reference scanning."""
        pass

    def scan_and_update_references(
        self,
        old_path: Path,
        new_path: Path,
        dry_run: bool = False
    ) -> int:
        """Scan all text files and update references.

        Returns:
            Number of files with updated references
        """
        pass
```

### Pattern Detection

**Patterns to Support:**
1. Markdown links: `r'\[([^\]]+)\]\(([^)]+)\)'`
2. Relative paths: `r'(?:^|\s)(\.?\.?/)?([a-zA-Z0-9_/-]+\.(?:md|json|yaml|yml|txt))'`
3. Code imports (optional): `r'from\s+([a-zA-Z0-9_.]+)\s+import'`

### Integration Points

**RenameStrategy:**
```python
async def execute(self, action, dry_run=False):
    # ... rename logic ...
    references_updated = 0
    if self.reference_updater:
        references_updated = self.reference_updater.scan_and_update_references(
            source, target, dry_run=dry_run
        )
    return OperationResult(..., references_updated=references_updated)
```

**MoveStrategy:**
```python
async def execute(self, action, dry_run=False):
    # ... move logic ...
    references_updated = 0
    if self.reference_updater:
        references_updated = self.reference_updater.scan_and_update_references(
            source, target, dry_run=dry_run
        )
    return OperationResult(..., references_updated=references_updated)
```

---

## Comparison Framework

### Metrics for Comparison

| Metric | Manual Implementation | Simple Mode Implementation | Notes |
|--------|----------------------|---------------------------|-------|
| **Lines of Code** | ~130 | TBD | Fewer is better (if maintains functionality) |
| **Pattern Count** | 2 (markdown, relative) | TBD | More patterns = better coverage |
| **Test Coverage** | TBD | ≥75% | Higher is better |
| **Performance (1000 files)** | TBD | <1s | Faster is better |
| **False Positive Rate** | Low | TBD | Lower is better |
| **Extensibility** | Good (pattern list) | TBD | Ease of adding patterns |
| **Code Quality Score** | TBD | ≥70 | Higher is better |
| **Security Score** | TBD | ≥7.0 | Higher is better |

### Comparison Criteria

**Correctness:**
- Which implementation has fewer edge cases?
- Which handles special characters better?
- Which preserves path structure more accurately?

**Performance:**
- Which is faster for large projects (>1000 files)?
- Which uses less memory?
- Would async scanning help?

**Maintainability:**
- Which is easier to understand?
- Which is easier to extend with new patterns?
- Which has better documentation?

**Test Coverage:**
- Which has more comprehensive tests?
- Which tests more edge cases?
- Which has better integration tests?

---

## Dependencies

**Technical Dependencies:**
- Python 3.10+
- pathlib (standard library)
- re (regular expressions)
- aiofiles (async file operations - optional)

**Code Dependencies:**
- CleanupStrategy (abstract base class)
- RenameStrategy (integration point)
- MoveStrategy (integration point)
- OperationResult (data model)

**External Dependencies:**
- Existing manual implementation (lines 751-878)
- Project Cleanup Agent test suite

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Regression vs manual impl** | High | Low | Comprehensive comparison tests |
| **Performance degradation** | Medium | Medium | Performance benchmarks, async optimization |
| **False positives** | High | Low | Extensive pattern testing, edge case coverage |
| **Integration issues** | Medium | Low | Integration tests with strategies |
| **Pattern conflicts** | Low | Low | Pattern priority and specificity testing |

---

## Acceptance Testing

### Test Scenarios

**Scenario 1: Markdown Link Update**
```markdown
Given: File "OLD_NAME.md" contains content
And: File "referencing.md" contains [link](OLD_NAME.md)
When: OLD_NAME.md is renamed to new-name.md
Then: referencing.md should contain [link](new-name.md)
```

**Scenario 2: Relative Path Update**
```markdown
Given: File "docs/OLD_NAME.md" exists
And: File "README.md" contains "See docs/OLD_NAME.md"
When: docs/OLD_NAME.md is renamed to docs/new-name.md
Then: README.md should contain "See docs/new-name.md"
```

**Scenario 3: Dry-Run Mode**
```markdown
Given: File "OLD_NAME.md" with references in other files
When: Dry-run rename is executed
Then: References are detected and counted
But: No files are actually modified
```

**Scenario 4: Performance Test**
```markdown
Given: Project with 1000 markdown files
And: 100 files contain references to target file
When: Reference scan is executed
Then: Scan completes in < 1 second
And: All 100 references are detected
```

---

## Definition of Done

- [ ] ReferenceUpdater implementation complete
- [ ] Integration with RenameStrategy and MoveStrategy complete
- [ ] Test suite with ≥75% coverage
- [ ] All tests passing
- [ ] Code review score ≥ 70
- [ ] Security score ≥ 7.0
- [ ] Performance benchmark met (<1s for 1000 files)
- [ ] Comparison report complete
- [ ] Differences from manual implementation documented
- [ ] Recommendations documented

---

## Success Metrics

**Primary:**
- ✅ Zero broken links after rename/move operations
- ✅ Quality gates passed (score ≥70, security ≥7.0)
- ✅ Test coverage ≥75%
- ✅ Performance target met (<1s for 1000 files)

**Secondary:**
- ✅ At least 2 improvements identified vs manual implementation
- ✅ Comprehensive comparison report generated
- ✅ Lessons learned documented
- ✅ Recommendations for final implementation

---

## Notes

**Critical Context:**
- This is a comparison implementation, not a replacement
- Manual implementation is production-ready and working
- Goal is validation and improvement identification
- Any enhancements should be backward-compatible

**Follow-Up Actions:**
- Incorporate identified improvements into manual implementation (if beneficial)
- Update feedback document with comparison results
- Document lessons learned for future enhancements
- Consider async scanning if performance gains are significant

---

**Estimated Total Effort:** 2-3 hours
**Story Points:** 5
**Priority:** High
**Created By:** Simple Mode Planner Agent
**Date:** 2026-01-29
