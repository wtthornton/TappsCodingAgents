# Context7 Enhancements Implementation Plan

## Overview

This document outlines the implementation plan for Option 1 requirements plus R6 (Reviewer docs command) to improve TappsCodingAgents' Context7 integration, caching, and prompt enrichment capabilities.

## Requirements Summary

### A. Cursor-first Context7 Integration
- **R1**: Cursor-mode Context7 calls must use Cursor MCP tools (not local gateway)
- **R2**: Accurate availability detection and credential validation
- **R3**: Clear error messages when Context7 is unavailable

### B. Caching Layer Improvements
- **R4**: Correct cache metrics instrumentation (hit/miss/latency)
- **R5**: Cache key normalization (deferred to Option 2)

### C. Prompt Enrichment
- **R6**: Reviewer `docs` command (NEW - explicitly requested)
- **R7**: Implementer agent Context7 integration
- **R8**: Tester agent Context7 integration
- **R9**: Designer agent Context7 integration
- **R10**: Analyst agent Context7 integration

### D. Testing and Validation
- **R11**: Test coverage for Context7 integration paths
- **R12**: Integration tests for Cursor MCP tool calls

## Implementation Order

### Phase 1: Reviewer Docs Command (R6) - Priority 1
**Status**: In Progress

**Tasks**:
1. Add `docs` subcommand to reviewer CLI parser (`tapps_agents/cli/parsers/reviewer.py`)
2. Add `docs` command handler to ReviewerAgent (`tapps_agents/agents/reviewer/agent.py`)
3. Implement KB-first lookup with fallback behavior
4. Add format options (json, text, markdown)
5. Update command reference documentation

**Files to Modify**:
- `tapps_agents/cli/parsers/reviewer.py` - Add docs parser
- `tapps_agents/agents/reviewer/agent.py` - Add docs command handler
- `tapps_agents/cli/commands/reviewer.py` - Add docs command execution
- `.claude/skills/reviewer/SKILL.md` - Update skill definition

### Phase 2: Cursor MCP Integration (R1) - Priority 2
**Status**: Pending

**Tasks**:
1. Enhance `backup_client.py` to properly detect Cursor MCP availability
2. Update `KBLookup` to use Cursor MCP tools when in Cursor mode
3. Ensure MCP tool calls go through Cursor's MCP runtime (not local gateway)
4. Add runtime mode checks before MCP tool calls

**Files to Modify**:
- `tapps_agents/context7/backup_client.py` - Improve MCP detection
- `tapps_agents/context7/lookup.py` - Use Cursor MCP in Cursor mode
- `tapps_agents/context7/agent_integration.py` - Pass runtime mode info

### Phase 3: Error Handling (R2/R3) - Priority 3
**Status**: Pending

**Tasks**:
1. Improve credential validation messages
2. Add clear error messages for Context7 unavailability
3. Distinguish between "not configured" vs "unavailable" vs "quota exceeded"
4. Update availability detection logic

**Files to Modify**:
- `tapps_agents/context7/credential_validation.py` - Better error messages
- `tapps_agents/context7/agent_integration.py` - Improved availability detection
- `tapps_agents/context7/backup_client.py` - Clearer error reporting

### Phase 4: Cache Metrics (R4) - Priority 4
**Status**: Pending

**Tasks**:
1. Fix cache hit/miss tracking in `KBLookup`
2. Add latency metrics to cache operations
3. Update analytics to track correct metrics
4. Ensure metrics are reported in agent responses

**Files to Modify**:
- `tapps_agents/context7/lookup.py` - Track cache metrics correctly
- `tapps_agents/context7/analytics.py` - Fix metrics collection
- `tapps_agents/context7/kb_cache.py` - Add latency tracking

### Phase 5: Agent Integrations (R7-R10) - Priority 5
**Status**: Pending

**Tasks**:
1. **Implementer**: Add Context7 docs to code generation prompts
2. **Tester**: Add Context7 docs to test generation prompts
3. **Designer**: Add Context7 docs to API design prompts
4. **Analyst**: Add Context7 docs to requirements gathering prompts

**Files to Modify**:
- `tapps_agents/agents/implementer/agent.py` - Context7 integration
- `tapps_agents/agents/tester/agent.py` - Context7 integration
- `tapps_agents/agents/designer/agent.py` - Context7 integration
- `tapps_agents/agents/analyst/agent.py` - Context7 integration

### Phase 6: Testing (R11/R12) - Priority 6
**Status**: Pending

**Tasks**:
1. Add unit tests for Context7 integration paths
2. Add integration tests for Cursor MCP tool calls
3. Add tests for cache metrics
4. Add tests for error handling

**Files to Create**:
- `tests/context7/test_cursor_mcp_integration.py`
- `tests/context7/test_cache_metrics.py`
- `tests/context7/test_error_handling.py`
- `tests/agents/test_reviewer_docs.py`

## Current Status

- ✅ Requirements documented
- ✅ Implementation plan created
- 🔄 Phase 1 in progress (Reviewer docs command)

## Notes

- All changes must maintain backward compatibility
- Error handling should be graceful (log and continue, don't fail agents)
- Cache metrics should be accurate and useful for debugging
- Cursor mode detection must be reliable

