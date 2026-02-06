# Code Reviewer Agent Memory

## Recent Reviews

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

## Known Pre-existing Test Failures

From project memory:
- `test_direct_execution_fallback.py::test_execute_command_with_worktree_path` - pre-existing failure
- Expert governance/setup_wizard tests - pre-existing failures
- Beads-dependent tests fail when bd environment not configured

**Do not flag these in reviews** - they are tracked separately.
