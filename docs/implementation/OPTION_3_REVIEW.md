# Option 3: Context7 Strict On-Demand Usage and Per-Agent Caps - Detailed Review

**Review Date:** 2026-02-04
**Status:** Recommended for Implementation
**Priority:** Medium-High
**Estimated Effort:** 1-2 days

## Executive Summary

Option 3 addresses Context7 cache health issues (currently FAIL at 65/100) by enforcing:
1. **Topic-required fetches** - Prevent "whole library" fetches
2. **Per-agent token caps** - Limit Context7 docs per agent (Architect: 4K, Implementer: 3K, Tester: 2.5K)
3. **Lazy loading** - Fetch docs only when needed, not preemptively

**Recommendation:** ✅ **Implement Option 3** - Low risk, medium impact, addresses real performance issue

---

## Current State Analysis

### Health Metrics (From Health Check)
- **Context7 Cache Score:** 65/100 (FAIL)
- **Hit Rate:** 79.1% (Target: ≥80%)
- **Response Time:** 465 ms (Target: <100 ms for cache hits)
- **Cache Size:** 277 entries, 211 libraries

### Current Implementation Issues

1. **No Topic Enforcement**
   - Context7 fetches can request entire libraries without specifying topics
   - Leads to fetching unnecessary documentation
   - Increases cache misses and response times

2. **No Per-Agent Token Caps**
   - CONTEXT7_PATTERNS.md documents recommended limits but doesn't enforce them
   - Agents can receive unlimited Context7 content
   - Can cause context window overflow

3. **Pre-Injection vs. Lazy Loading**
   - Current pattern: Auto-detect libraries and fetch docs upfront
   - Better pattern: Fetch only when agent actually needs the docs
   - Pre-warm cache for performance, but don't stuff prompts

### Code Locations

**Context7 Integration:**
- `tapps_agents/context7/agent_integration.py` - Context7AgentHelper
- `tapps_agents/context7/lookup.py` - KB lookup logic
- `tapps_agents/context7/backup_client.py` - Backup client

**Usage in Orchestrators:**
- `tapps_agents/simple_mode/orchestrators/build_orchestrator.py` - `context7_docs` auto-detection

---

## Implementation Plan

### Task 1: Require Topic at Fetch ⭐ HIGH PRIORITY

**Goal:** Prevent "whole library" fetches by requiring topic specification

**Changes Required:**

1. **Add Configuration** (`tapps_agents/core/config.py`)
```python
class Context7Config(BaseModel):
    # ... existing fields ...

    require_topic: bool = Field(
        default=True,
        description="Require topic when fetching Context7 documentation"
    )
    allow_full_library_libraries: list[str] = Field(
        default_factory=list,
        description="Libraries allowed to fetch without topic (e.g. ['python-stdlib'])"
    )
```

2. **Enforce in agent_integration.py**
```python
# In Context7AgentHelper.get_documentation_for_libraries or similar
def get_library_docs(self, library: str, topic: str | None = None) -> str:
    if self.config.require_topic and topic is None:
        if library not in self.config.allow_full_library_libraries:
            logger.warning(f"Context7 fetch for '{library}' rejected: topic required")
            return f"Context7: Please specify a topic for {library} documentation"

    # Continue with fetch...
```

3. **Audit Call Sites**
- Find all calls to Context7 that don't pass topic
- Add default topics (e.g., "overview", "usage", "api")
- Document which libraries are in allowlist and why

**Estimated Effort:** 4-6 hours

---

### Task 2: Per-Agent Token Caps ⭐ HIGH PRIORITY

**Goal:** Enforce maximum Context7 tokens per agent per turn

**Changes Required:**

1. **Add Configuration** (`tapps_agents/core/config.py`)
```python
class Context7Config(BaseModel):
    # ... existing fields ...

    per_agent_max_tokens: dict[str, int] = Field(
        default_factory=lambda: {
            "architect": 4000,
            "implementer": 3000,
            "tester": 2500,
            "reviewer": 3000,
            "analyst": 2000,
            "planner": 2000,
            "designer": 3000,
            "default": 2500,
        },
        description="Maximum Context7 tokens per agent per turn"
    )
```

2. **Token Capping in Context7AgentHelper**
```python
def get_documentation_for_libraries(
    self,
    libraries: list[str],
    agent_id: str | None = None,
    topics: dict[str, str] | None = None
) -> dict[str, str]:
    """
    Get documentation with per-agent token capping.

    Args:
        libraries: List of library names
        agent_id: Agent requesting docs (e.g., 'implementer')
        topics: Optional dict of library -> topic

    Returns:
        Dict of library -> documentation (capped to agent's token limit)
    """
    max_tokens = self._get_agent_token_limit(agent_id)

    results = {}
    tokens_used = 0

    for library in libraries:
        topic = topics.get(library) if topics else None
        docs = self.get_library_docs(library, topic)

        # Estimate tokens using same method as ArtifactContextBuilder
        from tapps_agents.core.artifact_context_builder import ArtifactContextBuilder
        builder = ArtifactContextBuilder()
        estimated_tokens = builder.estimate_tokens(docs)

        remaining = max_tokens - tokens_used
        if estimated_tokens <= remaining:
            results[library] = docs
            tokens_used += estimated_tokens
        else:
            # Truncate to fit remaining budget
            truncated = self._truncate_to_tokens(docs, remaining)
            results[library] = truncated + "\n\n[Documentation truncated to fit agent token limit]"
            tokens_used += remaining
            logger.info(f"Context7 docs for {library} truncated: {estimated_tokens} -> {remaining} tokens")
            break

    logger.info(f"Context7 docs for {agent_id}: {tokens_used}/{max_tokens} tokens used")
    return results

def _get_agent_token_limit(self, agent_id: str | None) -> int:
    """Get token limit for agent from config."""
    if not agent_id:
        return self.config.per_agent_max_tokens.get("default", 2500)
    return self.config.per_agent_max_tokens.get(agent_id,
        self.config.per_agent_max_tokens.get("default", 2500))
```

3. **Update Orchestrator Calls**
- Pass `agent_id` parameter to Context7 calls
- Example in BuildOrchestrator:
```python
context7_docs = await context7_helper.get_documentation_for_libraries(
    libraries=detected_libraries,
    agent_id="implementer",  # NEW: Pass agent ID
    topics=topics_map,       # NEW: Pass topics
)
```

**Estimated Effort:** 6-8 hours

---

### Task 3: Lazy Loading ⭐ MEDIUM PRIORITY

**Goal:** Fetch Context7 docs only when agent needs them, not upfront

**Current Pattern (BuildOrchestrator):**
```python
# In _run_step_with_confirmation():
# Auto-detect libraries and fetch docs upfront for all steps
context7_docs = await self._fetch_context7_docs(libraries)
```

**Proposed Pattern:**
```python
# Fetch Context7 docs only for steps that use them
if step_name in ["implementer", "reviewer", "tester"]:
    context7_docs = await self._fetch_context7_docs(
        libraries=detected_libraries,
        agent_id=step_name,
        topics=self._get_relevant_topics(step_name)
    )
```

**Changes Required:**

1. **Identify Which Steps Need Context7**
   - Implementer: Yes (needs library APIs)
   - Reviewer: Yes (needs best practices)
   - Tester: Yes (needs test framework docs)
   - Planner: No
   - Architect: Maybe (depends on library-specific patterns)
   - Designer: Maybe (depends on API patterns)

2. **Refactor Orchestrator Context7 Logic**
   - Move Context7 fetch into step execution
   - Pass agent-specific topics
   - Apply per-agent token caps

3. **Keep Pre-Warming**
   - Pre-warm cache in `tapps-agents init`
   - Keep `scripts/prepopulate_context7_cache.py`
   - Update health check remediation to reference these

**Estimated Effort:** 4-6 hours

---

### Task 4: Documentation & Health Updates ⭐ LOW PRIORITY

**Changes Required:**

1. **Update CONTEXT7_PATTERNS.md**
   - Document topic-required pattern
   - Document per-agent token caps (now enforced)
   - Document lazy loading pattern
   - Add examples of good vs bad usage

2. **Update CONFIGURATION.md**
   - Add `context7.require_topic` documentation
   - Add `context7.per_agent_max_tokens` documentation
   - Add `context7.allow_full_library_libraries` documentation
   - Add usage examples

3. **Update Health Check Remediation**
   - Add clear instructions for cache pre-population
   - Reference `python scripts/prepopulate_context7_cache.py`
   - Reference `tapps-agents init`
   - Document expected metrics (>80% hit rate, <100ms response time)

**Estimated Effort:** 2-3 hours

---

### Task 5: Tests ⭐ MEDIUM PRIORITY

**Test Cases Required:**

1. **Unit Tests** (`tests/tapps_agents/context7/test_topic_enforcement.py`)
   - Test fetch with topic → success
   - Test fetch without topic + require_topic=True → warning/empty
   - Test fetch without topic + library in allowlist → success
   - Test per-agent token cap enforcement
   - Test token estimation and truncation

2. **Integration Tests** (`tests/integration/test_context7_caps.py`)
   - Run build workflow with Context7 enabled
   - Verify implementer receives ≤3000 tokens of Context7 docs
   - Verify reviewer receives ≤3000 tokens of Context7 docs
   - Verify cache hit rate and response time
   - Verify lazy loading (no docs fetched for planner step)

**Estimated Effort:** 6-8 hours

---

## Implementation Timeline

| Task | Priority | Effort | Dependencies |
|------|----------|--------|--------------|
| 1. Require Topic | HIGH | 4-6 hrs | None |
| 2. Per-Agent Caps | HIGH | 6-8 hrs | Task 1 (uses same token estimation) |
| 3. Lazy Loading | MEDIUM | 4-6 hrs | Tasks 1 & 2 |
| 4. Documentation | LOW | 2-3 hrs | Tasks 1-3 |
| 5. Tests | MEDIUM | 6-8 hrs | Tasks 1-3 |

**Total Effort:** 22-31 hours (3-4 days)
**Minimum Viable Implementation:** Tasks 1 + 2 = 10-14 hours (1.5-2 days)

---

## Acceptance Criteria

1. ✅ **Topic Required Enforcement**
   - Context7 fetches without topic (and not in allowlist) return warning
   - All call sites pass topics or use allowlist
   - Config `context7.require_topic` controls behavior

2. ✅ **Per-Agent Token Caps**
   - Context7 docs truncated to agent's `per_agent_max_tokens`
   - Token estimation matches ArtifactContextBuilder method
   - Logging shows when caps are hit

3. ✅ **Lazy Loading**
   - Context7 docs not fetched for steps that don't use them
   - Cache pre-warming still works
   - Docs fetched only when agent needs them

4. ✅ **Health Improvements**
   - Cache hit rate ≥80%
   - Response time <100ms for cache hits
   - Health check shows PASS for Context7 cache

5. ✅ **Documentation**
   - CONTEXT7_PATTERNS.md updated
   - CONFIGURATION.md updated
   - Health remediation clear

6. ✅ **Tests**
   - Unit tests for topic enforcement and token caps
   - Integration tests verify workflow behavior
   - All tests passing

---

## Risks and Mitigations

### Risk 1: Breaking Existing Workflows
**Probability:** Medium
**Impact:** High
**Mitigation:**
- Feature flag `require_topic` (can disable if needed)
- Allowlist for libraries that need full docs
- Comprehensive testing before rollout

### Risk 2: Token Estimation Inaccuracy
**Probability:** Low
**Impact:** Medium
**Mitigation:**
- Reuse proven token estimation from ArtifactContextBuilder
- Use tiktoken when available
- Add 10% safety margin

### Risk 3: Reduced Context7 Effectiveness
**Probability:** Low
**Impact:** Medium
**Mitigation:**
- Per-agent caps are generous (2.5K-4K tokens)
- Truncation adds clear message
- Agents can request specific topics to get relevant content

---

## Recommendation

✅ **APPROVE Option 3 for Implementation**

**Rationale:**
1. **Real Problem:** Context7 cache health is failing (65/100)
2. **Low Risk:** Mostly configuration and enforcement, feature-flagged
3. **Medium-High Impact:** Improves cache performance, reduces token waste
4. **Moderate Effort:** 1.5-2 days for MVP (tasks 1+2), 3-4 days for complete
5. **Synergy with Option 2:** Uses same token estimation method

**Implementation Strategy:**
- Phase 1 (MVP): Tasks 1 + 2 (topic enforcement + per-agent caps)
- Phase 2 (Complete): Add tasks 3-5 (lazy loading, docs, tests)
- Rollout: Feature-flag enabled, monitor metrics, adjust as needed

**Success Metrics:**
- Context7 cache hit rate increases from 79.1% to ≥80%
- Response time decreases from 465ms to <100ms for hits
- Cache health score increases from 65/100 to ≥75/100
- No workflow failures due to Context7 changes

---

## Next Steps

1. ✅ Review and approve this document
2. ⏳ Create implementation plan for Phase 1 (MVP)
3. ⏳ Implement tasks 1 + 2 (topic enforcement + caps)
4. ⏳ Test and validate
5. ⏳ Implement tasks 3-5 (lazy loading, docs, tests)
6. ⏳ Monitor metrics and iterate

**Estimated Start Date:** 2026-02-05
**Estimated Completion:** 2026-02-07 (MVP) or 2026-02-09 (Complete)
