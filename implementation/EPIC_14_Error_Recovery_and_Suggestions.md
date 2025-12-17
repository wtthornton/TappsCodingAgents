# Epic 14: Error Recovery and Suggestions

## Epic Goal

Provide intelligent error recovery and actionable suggestions when workflows or agents fail, helping users understand what went wrong and how to fix it. This reduces frustration and improves success rates.

## Epic Description

### Existing System Context

- **Current relevant functionality**: Errors are logged but may not provide actionable guidance. Error handling exists but may not include recovery suggestions. Users may not know how to fix errors when they occur
- **Technology stack**: Python 3.13+, error handling system, logging, workflow executor
- **Integration points**: 
  - `tapps_agents/workflow/executor.py` - Workflow execution
  - Agent error handling
  - Logging system
  - Cursor chat interface

### Enhancement Details

- **What's being added/changed**: 
  - Create error analysis system (understand why errors occurred)
  - Implement error categorization (common error types)
  - Add recovery suggestion engine (how to fix errors)
  - Create automatic retry with suggestions
  - Implement error context collection (what was happening)
  - Add error pattern recognition (learn from past errors)
  - Create user-friendly error messages

- **How it integrates**: 
  - Error handler analyzes errors and generates suggestions
  - Suggestions provided in Cursor chat
  - Works with existing error handling
  - Integrates with logging system
  - Uses workflow execution context

- **Success criteria**: 
  - Errors are analyzed and categorized
  - Recovery suggestions are actionable
  - Automatic retry works with suggestions
  - Error messages are user-friendly
  - Error patterns are recognized

## Stories

1. **Story 14.1: Error Analysis System**
   - Create error analyzer that examines error details
   - Implement error categorization (type, severity, category)
   - Add error context collection (what was happening when error occurred)
   - Create error pattern detection
   - Acceptance criteria: Errors analyzed, categorization works, context collected, patterns detected

2. **Story 14.2: Recovery Suggestion Engine**
   - Implement suggestion engine that generates recovery steps
   - Create suggestion database (common errors and fixes)
   - Add suggestion ranking (most likely to work first)
   - Implement suggestion explanation (why this fix)
   - Acceptance criteria: Suggestions generated, database populated, ranking accurate, explanations clear

3. **Story 14.3: Automatic Retry with Suggestions**
   - Implement automatic retry mechanism
   - Create retry with suggestion application (try suggested fix)
   - Add retry logic (exponential backoff, max attempts)
   - Implement retry success tracking
   - Acceptance criteria: Retry works, suggestions applied, logic sound, success tracked

4. **Story 14.4: User-Friendly Error Messages**
   - Create error message formatting for users
   - Implement error message simplification (remove technical jargon)
   - Add error message context (what was trying to do)
   - Create error message display in Cursor chat
   - Acceptance criteria: Messages formatted, jargon removed, context included, display clear

5. **Story 14.5: Error Pattern Recognition and Learning**
   - Create error pattern database
   - Implement pattern matching (recognize similar errors)
   - Add learning system (improve suggestions from past errors)
   - Create error statistics and trends
   - Acceptance criteria: Patterns recognized, matching works, learning improves, statistics available

## Compatibility Requirements

- [ ] Error recovery is optional (can be disabled)
- [ ] No breaking changes to error handling
- [ ] Works with existing error system
- [ ] Backward compatible with current errors
- [ ] Suggestions don't interfere with manual fixes

## Risk Mitigation

- **Primary Risk**: Suggestions may be incorrect
  - **Mitigation**: Confidence scoring, user feedback, learning system, fallback to manual fix
- **Primary Risk**: Automatic retry may cause infinite loops
  - **Mitigation**: Max retry limits, timeout mechanisms, abort capability, user confirmation
- **Primary Risk**: Error analysis may be slow
  - **Mitigation**: Caching, async analysis, performance optimization, timeout limits
- **Rollback Plan**: 
  - Disable error recovery
  - Remove suggestion system
  - Fall back to basic error messages

## Definition of Done

- [ ] All stories completed with acceptance criteria met
- [ ] Errors are analyzed and categorized
- [ ] Recovery suggestions are actionable
- [ ] Automatic retry works correctly
- [ ] Error messages are user-friendly
- [ ] Error patterns are recognized
- [ ] Comprehensive test coverage
- [ ] Documentation complete (error recovery, troubleshooting)
- [ ] No regression in error handling
- [ ] Suggestions improve user experience

## Implementation Status

**Last Updated:** 2025-01-27

**Overall Status:** ✅ Completed

**Story Status:**
- Story 14.1 (Error Analysis): ✅ Completed
- Story 14.2 (Suggestion Engine): ✅ Completed
- Story 14.3 (Automatic Retry): ✅ Completed
- Story 14.4 (Error Messages): ✅ Completed
- Story 14.5 (Pattern Recognition): ✅ Completed

## Implementation Summary

### Files Created:
- `tapps_agents/workflow/error_recovery.py` - Comprehensive error recovery system with analysis, suggestions, and learning

### Files Modified:
- `tapps_agents/workflow/executor.py` - Integrated error recovery manager for headless mode
- `tapps_agents/workflow/cursor_executor.py` - Integrated error recovery manager for Cursor mode

### Key Features Implemented:

1. **Error Analysis System** (Story 14.1):
   - `ErrorAnalyzer` class with deep error categorization
   - Error type detection (20+ error types: file_not_found, permission_denied, connection_error, timeout, import_error, syntax_error, etc.)
   - Error severity determination (low, medium, high, critical)
   - Pattern matching against known error patterns
   - Error context collection (workflow_id, step_id, agent, action, timestamp, etc.)

2. **Recovery Suggestion Engine** (Story 14.2):
   - `RecoverySuggestionEngine` with suggestion database
   - Recovery suggestions with confidence scoring (0.0-1.0)
   - Step-by-step recovery instructions
   - Explanation generation for why suggestions are recommended
   - Suggestion ranking by confidence and success rate
   - Learning from past successful suggestions

3. **Automatic Retry with Suggestions** (Story 14.3):
   - Enhanced retry mechanism integrated with error recovery
   - Automatic retry decision based on error analysis
   - Exponential backoff with configurable delays
   - Retry delay calculation based on attempt number
   - Integration with auto-progression system

4. **User-Friendly Error Messages** (Story 14.4):
   - Simplified error messages (removes technical jargon)
   - Context-aware error messages (includes step, agent info)
   - Formatted suggestions with step-by-step instructions
   - Markdown formatting for Cursor chat display
   - Clear action items and explanations

5. **Error Pattern Recognition and Learning** (Story 14.5):
   - Error pattern database with regex matching
   - Pattern matching against known error patterns
   - Learning data persistence (`.tapps-agents/error_learning.json`)
   - Success rate tracking for suggestions
   - Confidence boost based on historical success rates
   - Feedback recording mechanism

### Configuration:

Error recovery can be controlled via environment variable:
- `TAPPS_AGENTS_ERROR_RECOVERY=true` (default) - Enable error recovery and suggestions
- `TAPPS_AGENTS_ERROR_RECOVERY=false` - Disable error recovery (fallback to basic error handling)

### Usage:

Error recovery is enabled by default. When errors occur:
- Errors are automatically analyzed and categorized
- Recovery suggestions are generated with confidence scores
- User-friendly error messages are displayed in Cursor chat
- Automatic retry is attempted for recoverable errors
- Suggestions improve over time based on success rates

### Backward Compatibility:

- Error recovery is optional (can be disabled)
- No breaking changes to error handling
- Works with existing error system
- Backward compatible with current errors
- Suggestions don't interfere with manual fixes

