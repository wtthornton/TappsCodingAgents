# CLI Feedback Enhancement - All Commands Implementation Plan

## Overview

This document outlines the plan to enhance user feedback indicators across all CLI commands in TappsCodingAgents, following the improvements made to the `reviewer report` command.

## Goals

1. **Consistent Status Indicators** - All commands show clear [START], [RUNNING], [SUCCESS], [ERROR] indicators
2. **Progress Tracking** - Multi-step operations show step-by-step progress
3. **Stream Separation** - Status messages to stderr, data to stdout (prevents PowerShell JSON parsing errors)
4. **Better Error Visibility** - Errors are clearly distinguished with visual indicators
5. **Operation Context** - Operations show what they're doing with descriptive messages

## Commands to Enhance

### 1. Tester Commands (`tapps_agents/cli/commands/tester.py`)
- ✅ `test` - Run/generate tests
- ✅ `generate-tests` - Generate test files
- ✅ `run-tests` - Execute test suite

**Improvements:**
- Add step-by-step progress for test generation
- Show test file paths in success message
- Better error messages for test failures

### 2. Planner Commands (`tapps_agents/cli/commands/planner.py`)
- ✅ `plan` - Create development plan
- ✅ `create-story` - Generate user story
- ✅ `list-stories` - List all stories

**Improvements:**
- Add descriptive operation messages
- Show story details in success messages
- Progress indicators for plan creation

### 3. Implementer Commands (`tapps_agents/cli/commands/implementer.py`)
- ✅ `implement` - Implement code in file
- ✅ `generate-code` - Generate code without writing
- ✅ `refactor` - Refactor existing code

**Improvements:**
- Show file paths and operation status
- Progress for code generation steps
- Clear warnings about instruction-based execution

### 4. Analyst Commands (`tapps_agents/cli/commands/analyst.py`)
- ✅ `gather-requirements` - Gather requirements
- ✅ `stakeholder-analysis` - Analyze stakeholders
- ✅ `tech-research` - Research technology
- ✅ `estimate-effort` - Estimate effort
- ✅ `assess-risk` - Assess risks
- ✅ `competitive-analysis` - Competitive analysis

**Improvements:**
- Add operation descriptions for each command
- Progress indicators for analysis steps
- Better success messages with output file paths

### 5. Top-Level Commands (`tapps_agents/cli/commands/top_level.py`)
- ✅ `hardware-profile` - Hardware profiling
- ✅ `create` - Create new project
- ✅ `workflow` - Execute workflow

**Improvements:**
- Progress tracking for workflow execution
- Step-by-step progress for project creation
- Better status for hardware profiling

### 6. Simple Mode Commands (`tapps_agents/cli/commands/simple_mode.py`)
- ✅ `on` - Enable Simple Mode
- ✅ `off` - Disable Simple Mode
- ✅ `status` - Check Simple Mode status
- ✅ `full` - Run full lifecycle workflow

**Improvements:**
- Clear status messages for mode changes
- Progress tracking for full workflow
- Better success messages

### 7. Health Commands (`tapps_agents/cli/commands/health.py`)
- ✅ `check` - Run health checks
- ✅ `dashboard` - Generate health dashboard
- ✅ `metrics` - Collect health metrics
- ✅ `trends` - Analyze health trends

**Improvements:**
- Progress for health check execution
- Better visualization of health status
- Clear error indicators for failed checks

## Implementation Pattern

For each command, apply these patterns:

### 1. Enhanced `start_operation()` Calls
```python
# Before
feedback.start_operation("Test")

# After
feedback.start_operation("Test Generation", f"Generating tests for {file_path}...")
```

### 2. Use `running()` for Multi-Step Operations
```python
feedback.running("Discovering files...", step=1, total_steps=4)
feedback.running("Analyzing code...", step=2, total_steps=4)
feedback.running("Generating tests...", step=3, total_steps=4)
feedback.running("Writing test file...", step=4, total_steps=4)
```

### 3. Enhanced Success Messages
```python
# Before
feedback.output_result(result, message="Tests generated successfully")

# After
feedback.clear_progress()
summary = {
    "test_file": result.get("test_file"),
    "tests_generated": result.get("test_count", 0)
}
feedback.output_result(result, message="Tests generated successfully", summary=summary)
```

### 4. Better Error Handling
```python
# Errors are already handled by check_result_error(), but ensure clear messages
try:
    result = await agent.run(...)
    check_result_error(result)
except Exception as e:
    feedback.error(
        f"Failed to generate tests: {str(e)}",
        error_code="test_generation_failed",
        context={"file": file_path}
    )
```

## Implementation Order

1. ✅ **Tester Commands** - High usage, clear multi-step operations
2. ✅ **Planner Commands** - Simple operations, good for pattern validation
3. ✅ **Implementer Commands** - Important for code generation feedback
4. ✅ **Analyst Commands** - Multiple commands, good for consistency
5. ✅ **Top-Level Commands** - Complex workflows, need careful progress tracking
6. ✅ **Simple Mode Commands** - User-facing, needs clear status
7. ✅ **Health Commands** - System monitoring, needs clear status indicators

## Testing Strategy

After implementation, test each command:
1. **Normal execution** - Verify status indicators appear correctly
2. **JSON output mode** - Verify status messages go to stderr, data to stdout
3. **Error cases** - Verify error indicators are clear
4. **Quiet mode** - Verify quiet mode suppresses status messages
5. **Verbose mode** - Verify verbose mode shows additional details

## Success Criteria

- ✅ All commands show [START] indicator when beginning
- ✅ Multi-step operations show [RUNNING] with step information
- ✅ All commands show [SUCCESS] or [ERROR] on completion
- ✅ Status messages go to stderr (not stdout) in all modes
- ✅ JSON output mode doesn't cause PowerShell parsing errors
- ✅ Users can clearly see if commands are running, stuck, or completed
- ✅ Error states are immediately obvious

## Notes

- The `feedback.py` module already has all necessary methods (`start_operation()`, `running()`, `success()`, `error()`)
- Stream separation is already handled - status messages go to stderr
- We just need to update command implementations to use these methods consistently
- Some commands may need progress callbacks added to agent methods for true step-by-step progress

