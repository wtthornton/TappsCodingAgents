# Context7 Enhancements - Requirements Document

## Overview

This document provides detailed requirements for enhancing TappsCodingAgents' Context7 integration, focusing on Cursor-first architecture, caching improvements, and prompt enrichment across agents.

## Approved Requirements (Option 1 + R6)

### A. Cursor-first Context7 Integration

#### R1: Cursor-mode Context7 calls must use Cursor MCP tools
**Priority**: High  
**Status**: In Progress

**Requirement**: When running in Cursor mode, Context7 calls should prefer Cursor's MCP tools over the local MCPGateway registry or HTTP fallback.

**Current Behavior**:
- `check_mcp_tools_available()` returns `True` in Cursor mode based on `is_cursor_mode()`
- But `MCPGateway.call_tool()` fails because tools aren't in the local registry
- Code falls back to HTTP, which defeats the purpose of Cursor MCP integration

**Required Behavior**:
1. In Cursor mode, detect that MCP tools are available via Cursor's MCP server (not local gateway)
2. When Python code cannot directly call Cursor MCP tools:
   - Return clear indication that MCP tools should be used by AI assistant
   - Allow HTTP fallback only if API key is available AND operation is from CLI (not AI assistant context)
3. Improve detection logic to distinguish between:
   - Cursor mode with MCP tools available (preferred)
   - Headless mode with local MCPGateway (fallback)
   - Headless mode with HTTP only (last resort)

**Acceptance Criteria**:
- [ ] Cursor mode detection accurately identifies when Cursor MCP tools are available
- [ ] Error messages clearly indicate when MCP tools should be used vs when HTTP fallback is acceptable
- [ ] CLI commands in Cursor mode can still work (with HTTP fallback if needed)
- [ ] AI assistant calls use MCP tools directly (no Python code path)

#### R2: Accurate availability detection and credential validation
**Priority**: High  
**Status**: Pending

**Requirement**: Improve Context7 availability detection to provide accurate, actionable information.

**Current Issues**:
- Credential validation may show false warnings in Cursor mode
- Availability detection doesn't distinguish between "not configured" vs "unavailable" vs "quota exceeded"
- Error messages are not actionable

**Required Behavior**:
1. **Availability Detection**:
   - Check Cursor mode first → MCP tools available
   - Check local MCPGateway → Tools registered
   - Check API key → HTTP fallback available
   - Provide clear status: "available via MCP", "available via API key", "not available"

2. **Credential Validation**:
   - In Cursor mode: Don't warn about missing API key if MCP tools are available
   - In headless mode: Warn only if neither MCPGateway nor API key available
   - Distinguish between:
     - "Not configured" (actionable: set API key or configure MCP)
     - "Unavailable" (service down, network issue)
     - "Quota exceeded" (actionable: upgrade plan or wait)

3. **Error Messages**:
   - Provide actionable guidance based on runtime mode
   - Include setup instructions when appropriate
   - Avoid false warnings in Cursor mode

**Acceptance Criteria**:
- [ ] No false warnings about missing API key in Cursor mode when MCP tools available
- [ ] Clear distinction between different unavailability reasons
- [ ] Actionable error messages with setup instructions
- [ ] Credential validation respects runtime mode

#### R3: Clear error messages when Context7 is unavailable
**Priority**: Medium  
**Status**: Pending

**Requirement**: Provide clear, user-friendly error messages when Context7 operations fail.

**Required Behavior**:
1. **Error Categories**:
   - **Not Configured**: "Context7 is not configured. [Setup instructions]"
   - **Unavailable**: "Context7 service is currently unavailable. [Retry suggestion]"
   - **Quota Exceeded**: "Context7 API quota exceeded. [Upgrade suggestion]"
   - **Network Error**: "Cannot reach Context7 API. [Network troubleshooting]"
   - **Invalid Library**: "Library not found in Context7. [Alternative suggestions]"

2. **Error Message Format**:
   - Clear, concise description
   - Actionable next steps
   - Runtime mode context (Cursor vs headless)
   - Setup instructions when appropriate

3. **Logging**:
   - Debug logs for technical details
   - User-facing messages should be friendly and actionable
   - Avoid exposing API keys or sensitive information

**Acceptance Criteria**:
- [ ] All error messages are clear and actionable
- [ ] Error messages include appropriate context (runtime mode, setup instructions)
- [ ] No sensitive information exposed in error messages
- [ ] Error messages help users resolve issues quickly

### B. Caching Layer Improvements

#### R4: Correct cache metrics instrumentation
**Priority**: Medium  
**Status**: Pending

**Requirement**: Fix cache metrics to accurately track hits, misses, latency, and other performance indicators.

**Current Issues**:
- Cache metrics may not be tracked correctly in `KBLookup`
- Latency metrics may not include all operations
- Hit/miss tracking may be inconsistent

**Required Behavior**:
1. **Cache Hit Tracking**:
   - Record hit when cache entry is found (exact match)
   - Record fuzzy match when fuzzy matching succeeds
   - Record miss when cache lookup fails and API call is made

2. **Latency Tracking**:
   - Track latency for cache lookups (should be <10ms)
   - Track latency for API calls (can be 100-1000ms)
   - Track total lookup time (cache + API if needed)
   - Include latency in `LookupResult`

3. **Metrics Reporting**:
   - Update analytics correctly for all operations
   - Include metrics in agent responses when appropriate
   - Provide accurate hit rate calculations

4. **Metrics Storage**:
   - Persist metrics to `.metrics.yaml`
   - Update metrics atomically
   - Include timestamp for all metric updates

**Acceptance Criteria**:
- [ ] Cache hits are recorded correctly for exact matches
- [ ] Cache misses are recorded correctly when API calls are made
- [ ] Latency is tracked for all operations
- [ ] Hit rate calculations are accurate
- [ ] Metrics are persisted and available for reporting

### C. Prompt Enrichment

#### R6: Reviewer `docs` command
**Priority**: High  
**Status**: Completed ✅

**Requirement**: Implement `reviewer docs` command to retrieve Context7 documentation.

**Implementation**: ✅ Complete
- CLI parser added
- Command handler implemented
- KB-first lookup with fallback
- Format options (json, text, markdown)

#### R7: Implementer agent Context7 integration
**Priority**: Medium  
**Status**: Pending

**Requirement**: Add Context7 documentation to Implementer agent prompts to improve code generation quality.

**Required Behavior**:
1. **Library Detection**:
   - Detect libraries mentioned in user prompt or codebase
   - Resolve library names to Context7 IDs
   - Retrieve relevant documentation snippets

2. **Prompt Enrichment**:
   - Add Context7 documentation to code generation prompts
   - Include relevant examples and API patterns
   - Focus on code mode documentation (not info mode)

3. **Integration Points**:
   - `implement()` method: Add docs before code generation
   - `refactor()` method: Add docs for libraries being refactored
   - Respect `--no-context7` flag if added

4. **Fallback Behavior**:
   - If Context7 unavailable, continue without docs (don't fail)
   - Log warning if Context7 would improve prompt but is unavailable

**Acceptance Criteria**:
- [ ] Implementer detects libraries in prompts
- [ ] Context7 docs are added to code generation prompts
- [ ] Code quality improves with Context7 docs (measurable)
- [ ] Graceful fallback when Context7 unavailable

#### R8: Tester agent Context7 integration
**Priority**: Medium  
**Status**: Pending

**Requirement**: Add Context7 documentation to Tester agent prompts to improve test generation quality.

**Required Behavior**:
1. **Library Detection**:
   - Detect libraries used in code under test
   - Retrieve testing-related documentation
   - Include test examples from Context7

2. **Prompt Enrichment**:
   - Add testing patterns and examples to test generation prompts
   - Include library-specific testing best practices
   - Focus on test code examples

3. **Integration Points**:
   - `test()` method: Add docs before test generation
   - `generate_tests()` method: Add docs for test patterns

**Acceptance Criteria**:
- [ ] Tester detects libraries in code under test
- [ ] Context7 docs improve test generation quality
- [ ] Test examples from Context7 are included
- [ ] Graceful fallback when Context7 unavailable

#### R9: Designer agent Context7 integration
**Priority**: Medium  
**Status**: Pending

**Requirement**: Add Context7 documentation to Designer agent prompts for API and data model design.

**Required Behavior**:
1. **Library Detection**:
   - Detect frameworks/libraries mentioned in design prompts
   - Retrieve design patterns and best practices

2. **Prompt Enrichment**:
   - Add API design patterns from Context7
   - Include data model examples
   - Focus on design best practices

3. **Integration Points**:
   - `design_api()` method: Add API design docs
   - `design_model()` method: Add data model examples

**Acceptance Criteria**:
- [ ] Designer uses Context7 for API design patterns
- [ ] Data model examples from Context7 are included
- [ ] Design quality improves with Context7 docs
- [ ] Graceful fallback when Context7 unavailable

#### R10: Analyst agent Context7 integration
**Priority**: Low  
**Status**: Pending

**Requirement**: Add Context7 documentation to Analyst agent prompts for requirements gathering and technology research.

**Required Behavior**:
1. **Technology Research**:
   - Use Context7 for technology comparison
   - Include library capabilities in requirements analysis
   - Provide technology recommendations based on Context7 data

2. **Prompt Enrichment**:
   - Add library information to requirements documents
   - Include technology options in analysis
   - Focus on info mode documentation (conceptual)

3. **Integration Points**:
   - `gather_requirements()`: Include technology options
   - `research_technology()`: Use Context7 for research
   - `estimate_effort()`: Consider library complexity from Context7

**Acceptance Criteria**:
- [ ] Analyst uses Context7 for technology research
- [ ] Requirements include relevant library information
- [ ] Technology recommendations are informed by Context7
- [ ] Graceful fallback when Context7 unavailable

### D. Testing and Validation

#### R11: Test coverage for Context7 integration paths
**Priority**: Medium  
**Status**: Pending

**Requirement**: Add comprehensive test coverage for Context7 integration.

**Required Tests**:
1. **Unit Tests**:
   - Cache hit/miss scenarios
   - Latency tracking
   - Error handling
   - Credential validation

2. **Integration Tests**:
   - KB-first lookup workflow
   - MCP Gateway fallback
   - HTTP fallback
   - Cache metrics accuracy

3. **Agent Integration Tests**:
   - Reviewer docs command
   - Implementer Context7 integration
   - Tester Context7 integration
   - Designer Context7 integration

**Acceptance Criteria**:
- [ ] All Context7 code paths have test coverage
- [ ] Tests pass in both Cursor and headless modes
- [ ] Mock MCP tools for testing
- [ ] Integration tests use real Context7 API (marked with `@pytest.mark.requires_context7`)

#### R12: Integration tests for Cursor MCP tool calls
**Priority**: Low  
**Status**: Pending

**Requirement**: Add integration tests specifically for Cursor MCP tool calls.

**Required Tests**:
1. **MCP Tool Availability**:
   - Test `check_mcp_tools_available()` in Cursor mode
   - Test fallback behavior when MCP tools not available

2. **Tool Call Paths**:
   - Test `resolve-library-id` via MCP
   - Test `get-library-docs` via MCP
   - Test error handling for MCP tool failures

**Acceptance Criteria**:
- [ ] Tests verify MCP tool calls work in Cursor mode
- [ ] Tests verify fallback behavior when MCP unavailable
- [ ] Tests can run in both Cursor and headless environments

## Implementation Status

- ✅ **R6**: Reviewer docs command - Completed
- 🔄 **R1**: Cursor MCP integration - In Progress
- ⏳ **R2/R3**: Error handling - Pending
- ⏳ **R4**: Cache metrics - Pending
- ⏳ **R7-R10**: Agent integrations - Pending
- ⏳ **R11/R12**: Testing - Pending

## Notes

- All changes must maintain backward compatibility
- Error handling should be graceful (log and continue, don't fail agents)
- Cache metrics should be accurate and useful for debugging
- Cursor mode detection must be reliable
- Agent integrations should improve prompt quality measurably

