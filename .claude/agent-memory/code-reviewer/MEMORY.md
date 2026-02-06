# Code Reviewer Agent Memory

## Recent Reviews

### 2026-02-06: Dashboard Data Collectors Deep Review
**Full Report:** `dashboard-collectors-review-2026-02-06.md`

**Critical Findings:**
1. **Field Name Mismatch:** HealthMetricsCollector.get_summary() returns "by_check" but DashboardDataCollector expects "checks" → dashboard shows no health checks
2. **Timezone Bug:** ExpertPerformanceTracker uses deprecated `datetime.utcnow()` instead of `datetime.now(UTC)` → incorrect date filtering
3. **Math Error:** AnalyticsCollector.get_trends() incorrect averaging (divides by 2 repeatedly instead of summing and dividing by count) → wrong trend data
4. **Code Duplication:** `_calculate_overall_score()` duplicated in ExpertPerformanceTracker and OutcomeTracker → maintenance burden
5. **Race Condition:** AnalyticsCollector appends to files without locking → possible JSON corruption

**Pattern Strengths:**
- Fault-tolerant design (collectors return defaults on error)
- Good separation of concerns (each collector has single responsibility)
- UTC timezone awareness in most places

**Common Issues Detected:**
- Inefficient file I/O (loads entire files into memory, then reverses)
- No retention policy (metrics accumulate forever)
- Silent error swallowing (broad except with debug-level logging)
- Missing input validation in dual-write functions

### 2026-02-06: TappsCodingAgents Framework Comprehensive Review
**Full Report:** `comprehensive-review-2026-02-06.md`

**Critical Findings:**
1. **MRO Issue:** BaseAgent doesn't call `super().__init__()`, breaking ExpertSupportMixin initialization across 6+ agents
2. **Error Handling Inconsistency:** 3 different error patterns (ErrorEnvelope, plain dict, dict with error_type)
3. **Path Security:** Duplicate path validation logic across agents, inconsistent TOCTOU protection

**Pattern Strengths:**
- Context7 integration (lazy init, graceful degradation)
- Expert system consultation (confidence-based)
- Instruction-based architecture (separation of concerns)

**Common Anti-Patterns Detected:**
- Defensive `hasattr(self, 'expert_registry')` checks everywhere (masks real MRO issue)
- Large methods (167+ lines) lacking decomposition
- Magic strings for commands (no enums)
- Blocking file I/O in async methods

## Framework-Specific Learnings

### Agent Architecture Patterns
- All agents inherit from `BaseAgent`
- Multi-inheritance with mixins (`ExpertSupportMixin`) is common
- Command dispatch pattern: `run(command: str, **kwargs) -> dict`
- Help methods should return `{"type": "help", "content": str}`

### Error Handling Evolution
- **Phase 5.1** introduced `ErrorEnvelopeBuilder`
- Not fully adopted - implementer uses it, reviewer doesn't
- Recommendation: Standardize on ErrorEnvelope framework-wide

### Security Patterns
- Path validation exists but decentralized
- `# nosec` comments properly document subprocess risks
- Need centralized `PathValidator` class

### Performance Patterns
- Parallel tool execution infrastructure exists but underutilized
- Async methods often perform blocking I/O
- Consider `aiofiles` for true async file operations

## Common Code Smells in This Codebase

1. **Excessive Defensive Programming**
   - Pattern: `if hasattr(self, 'attr') and self.attr:`
   - Better: Fix initialization so attribute always exists

2. **Large Command Dispatch Methods**
   - Pattern: Single `run()` method with 10+ elif branches
   - Better: Command pattern or dispatch table

3. **Inline Expert Consultation**
   - Pattern: Try-except around every `expert_registry.consult()`
   - Better: Centralized consultation helper with fallback

## Quality Gates for This Project

**Minimum Scores:**
- Overall: 70 (framework code: 75)
- Security: 7.0 (framework code: 8.5)
- Maintainability: 7.0
- Test Coverage: 75% (framework: 80%)

**Tools:**
- Ruff (linting)
- mypy (type checking)
- bandit (security)
- jscpd (duplication)
- pip-audit (dependencies)

## Review Checklist Template

For future TappsCodingAgents reviews:

### General
- [ ] MRO issue resolved or worked around?
- [ ] Error handling uses ErrorEnvelope?
- [ ] Path validation uses centralized PathValidator?
- [ ] No `hasattr(self, 'expert_registry')` checks?
- [ ] Type annotations on all public methods?
- [ ] Async methods don't block on file I/O?
- [ ] Commands use enums, not magic strings?
- [ ] Methods under 50 lines (or well-justified)?
- [ ] Help method follows standard format?
- [ ] Expert/Context7 integration follows standard pattern?

### Data Collectors (Analytics/Metrics)
- [ ] Uses `datetime.now(UTC)` not `datetime.utcnow()` (deprecated in 3.12+)?
- [ ] Field names match what consumers expect?
- [ ] Aggregation math is correct (sum then divide, not recursive averaging)?
- [ ] File I/O uses efficient patterns (deque, file seeking, not load-all-then-reverse)?
- [ ] Concurrent writes use file locking or atomic operations?
- [ ] Input validation on all external data?
- [ ] Errors logged at appropriate level (not all DEBUG)?
- [ ] Retention policy for old data?
- [ ] No code duplication of score/metric calculations?

## Known Pre-existing Test Failures

From project memory:
- `test_direct_execution_fallback.py::test_execute_command_with_worktree_path` - pre-existing failure
- Expert governance/setup_wizard tests - pre-existing failures
- Beads-dependent tests fail when bd environment not configured

**Do not flag these in reviews** - they are tracked separately.
