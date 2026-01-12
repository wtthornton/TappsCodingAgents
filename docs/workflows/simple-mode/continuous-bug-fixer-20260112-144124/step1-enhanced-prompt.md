# Step 1: Enhanced Prompt - Continuous Bug Finder and Fixer

## Original Prompt
Continuously search for a bug and then pass it to bug-fix-agent to solve it and check it in

## Enhanced Prompt with Requirements Analysis

### Intent Analysis
**Primary Goal**: Create an automated system that continuously monitors the codebase for bugs (test failures), automatically fixes them using the bug-fix-agent, and commits the fixes.

**Scope**: 
- Automated bug detection (via test execution)
- Integration with existing bug-fix-agent
- Automatic commit workflow
- Continuous operation (loop-based execution)

### Functional Requirements

1. **Bug Detection Module**
   - Execute test suite (pytest) programmatically
   - Parse test failure output to extract:
     - File path containing the bug
     - Error message/description
     - Test name that failed
   - Identify which source files (not test files) need fixing
   - Filter out test setup/configuration errors (focus on code bugs)

2. **Bug-Fix Integration**
   - Call bug-fix-agent for each detected bug
   - Pass file path and error description to bug-fix-agent
   - Handle bug-fix-agent execution results
   - Verify fixes (re-run tests)

3. **Commit Workflow**
   - Automatically commit fixes after bug-fix-agent succeeds
   - Create meaningful commit messages
   - Support batch commits (multiple bugs) or individual commits

4. **Continuous Operation**
   - Loop execution: run tests → find bugs → fix → commit → repeat
   - Configurable iteration limits
   - Stop conditions: no bugs found, max iterations, manual stop
   - Progress reporting

5. **Error Handling**
   - Handle cases where bug-fix-agent fails to fix a bug
   - Skip bugs that can't be fixed after max iterations
   - Log all attempts and results
   - Continue with next bug if one fails

### Non-Functional Requirements

1. **Performance**
   - Efficient test execution (use pytest parallel execution if available)
   - Minimize redundant test runs
   - Cache test results when appropriate

2. **Reliability**
   - Robust error handling for pytest execution
   - Handle edge cases (no tests, all tests pass, parsing failures)
   - Safe git operations (no force push, validate before commit)

3. **Usability**
   - CLI command with clear interface
   - Progress indicators
   - Summary reports (bugs found, fixed, failed)
   - Configurable options (max iterations, commit strategy)

4. **Integration**
   - Reuse existing pytest infrastructure from TesterAgent
   - Integrate with bug-fix-agent (FixOrchestrator)
   - Use existing git operations from core.git_operations
   - Follow TappsCodingAgents patterns and architecture

### Architecture Guidance

1. **Component Structure**
   - `BugFinder`: Test execution and failure parsing
   - `ContinuousBugFixer`: Main orchestrator
   - `BugFixCoordinator`: Integration with bug-fix-agent
   - `CommitManager`: Git commit handling

2. **Integration Points**
   - Use `TesterAgent._run_pytest()` pattern for test execution
   - Use `FixOrchestrator.execute()` for bug fixing
   - Use `commit_changes()` from `core.git_operations`
   - Follow CLI command pattern from other agents

3. **Data Flow**
   ```
   Test Execution → Parse Failures → Extract Bug Info → 
   Call Bug-Fix-Agent → Verify Fix → Commit → Repeat
   ```

### Quality Standards

1. **Code Quality**
   - Follow TappsCodingAgents code style
   - Type hints for all functions
   - Comprehensive error handling
   - Logging for debugging and monitoring

2. **Testing**
   - Unit tests for bug parsing logic
   - Integration tests with mock test failures
   - E2E tests with real pytest execution
   - Test error handling and edge cases

3. **Documentation**
   - CLI help text
   - Usage examples
   - Configuration options
   - Integration guide

### Implementation Strategy

1. **Phase 1: Core Bug Detection**
   - Implement test execution wrapper
   - Parse pytest output for failures
   - Extract file paths and error messages

2. **Phase 2: Bug-Fix Integration**
   - Integrate with FixOrchestrator
   - Handle bug-fix-agent results
   - Verify fixes with re-test

3. **Phase 3: Commit Workflow**
   - Implement commit logic
   - Create commit messages
   - Handle batch commits

4. **Phase 4: Continuous Loop**
   - Implement main loop
   - Add iteration limits
   - Add progress reporting

5. **Phase 5: CLI Integration**
   - Create CLI command parser
   - Add to main CLI
   - Add help text and examples

### Constraints and Considerations

1. **Test Execution**
   - Must work with existing pytest setup
   - Handle pytest plugins and markers
   - Support test paths and filters

2. **Bug-Fix-Agent Integration**
   - Bug-fix-agent requires file path and error description
   - Must handle async execution
   - Respect quality thresholds

3. **Git Operations**
   - Must validate git repository
   - Handle uncommitted changes
   - Support different commit strategies (one per bug, batch)

4. **Edge Cases**
   - No tests in project
   - All tests passing
   - Test failures in test files themselves
   - Bugs that can't be fixed (max iterations)
   - Network/LLM failures during bug fixing

### Success Criteria

1. System can detect bugs from test failures
2. System can automatically fix bugs using bug-fix-agent
3. System commits fixes automatically
4. System runs continuously until no bugs remain or max iterations
5. System provides clear progress and summary reporting
6. System handles errors gracefully
