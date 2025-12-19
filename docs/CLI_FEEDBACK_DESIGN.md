# CLI Feedback System Design

## Overview

This document describes a comprehensive design for providing consistent, user-friendly feedback across all CLI commands in TappsCodingAgents. The design addresses current inconsistencies where some commands are silent, others provide minimal feedback, and error messages vary in format.

## Core Principles

### 1. Always Inform the User
- Every command should provide feedback about what it's doing
- Users should never wonder if a command is working or has hung
- Long-running operations must show progress

### 2. Consistent Message Types
- **Info**: Normal operational messages (what's happening)
- **Success**: Successful completion messages
- **Warning**: Non-fatal issues that users should know about
- **Error**: Failures that prevent completion
- **Progress**: Real-time updates during long operations

### 3. Appropriate Verbosity
- **Quiet mode**: Only essential output (errors, final results)
- **Normal mode**: Standard feedback (default)
- **Verbose mode**: Detailed information for debugging

### 4. Format Consistency
- Text output: Human-readable, well-formatted
- JSON output: Structured, parseable, complete
- Both formats should contain the same information

## Message Categories

### Informational Messages
These tell users what the command is doing or what it found.

**Examples:**
- "Checking project configuration..."
- "Found 5 files to review"
- "Running health checks..."
- "Configuration loaded from: /path/to/config"

**Characteristics:**
- Use present tense for ongoing actions
- Use past tense for completed discoveries
- Keep messages concise but descriptive
- Include relevant details (file paths, counts, etc.)

### Success Messages
These confirm successful completion.

**Examples:**
- "Review completed successfully"
- "Health check passed (score: 95/100)"
- "Configuration saved"
- "3 files processed successfully"

**Characteristics:**
- Clear confirmation of success
- Include summary metrics when relevant
- Use positive, confident language
- Appear at the end of successful operations

### Warning Messages
These alert users to potential issues that don't prevent completion.

**Examples:**
- "Warning: Some dependencies are outdated"
- "Note: Using default configuration (no config file found)"
- "Warning: Low disk space detected (2GB remaining)"
- "Skipping file: access denied"

**Characteristics:**
- Clearly marked as warnings
- Explain the issue and potential impact
- Suggest remediation when appropriate
- Don't block execution

### Error Messages
These indicate failures that prevent completion.

**Examples:**
- "Error: File not found: example.py"
- "Error: Invalid configuration (missing required field: api_key)"
- "Error: Connection failed (timeout after 30 seconds)"
- "Error: Permission denied: cannot write to /path/to/file"

**Characteristics:**
- Clearly marked as errors
- Explain what went wrong
- Include relevant context (file paths, values, etc.)
- Provide actionable next steps when possible
- Use appropriate exit codes

### Progress Messages
These show real-time status during long operations.

**Examples:**
- "Processing file 3 of 10: example.py"
- "Reviewing code... [████████░░] 80%"
- "Step 2 of 5: Running tests..."
- "Analyzing dependencies... (this may take a minute)"

**Characteristics:**
- Show current progress (X of Y, percentage)
- Update in real-time
- Don't spam (throttle updates)
- Clear indication of what's happening now

## Feedback Levels

### Level 1: Quiet Mode
**When to use:** Scripts, automation, CI/CD pipelines

**What to show:**
- Errors only (to stderr)
- Final results (to stdout)
- Exit codes

**What to hide:**
- Informational messages
- Progress updates
- Warnings (unless critical)

**Example:**
```
$ tapps-agents review file.py --quiet
{"file": "file.py", "score": 85, "passed": true}
```

### Level 2: Normal Mode (Default)
**When to use:** Interactive terminal use

**What to show:**
- All errors and warnings
- Key informational messages
- Progress for operations > 5 seconds
- Success confirmations
- Summary results

**What to hide:**
- Detailed debugging information
- Internal operation details
- Verbose progress for quick operations

**Example:**
```
$ tapps-agents review file.py
Reviewing file.py...
✓ Review completed
Score: 85/100
Status: Passed
```

### Level 3: Verbose Mode
**When to use:** Debugging, troubleshooting, detailed analysis

**What to show:**
- Everything from normal mode
- Detailed progress for all operations
- Internal state information
- Configuration details
- Timing information
- Step-by-step execution details

**Example:**
```
$ tapps-agents review file.py --verbose
[INFO] Loading configuration from: /path/to/config
[INFO] Initializing ReviewerAgent...
[INFO] Activating agent...
[INFO] Loading model: qwen2.5-coder:7b
[INFO] Analyzing file: file.py (1,234 lines)
[INFO] Running complexity analysis...
[INFO] Running security scan...
[INFO] Running maintainability check...
[INFO] Generating feedback...
✓ Review completed (took 3.2 seconds)
Score: 85/100
Status: Passed
```

## Message Format Standards

### Text Format Structure

**Single-line messages:**
```
[PREFIX] Message text
```

**Multi-line messages:**
```
[PREFIX] Primary message
  Detail line 1
  Detail line 2
```

**Progress indicators:**
```
[PREFIX] Current action... [PROGRESS_BAR] PERCENTAGE%
```

### Prefixes by Message Type

- **Info**: No prefix (or `[INFO]` in verbose mode)
- **Success**: `✓` or `[OK]` or `[SUCCESS]`
- **Warning**: `⚠` or `[WARNING]`
- **Error**: `✗` or `[ERROR]`
- **Progress**: `→` or `[PROGRESS]`

### JSON Format Structure

All JSON output should follow this structure:

```json
{
  "success": true|false,
  "message": "Human-readable summary",
  "data": {
    // Command-specific data
  },
  "metadata": {
    "timestamp": "ISO-8601 timestamp",
    "duration_ms": 1234,
    "command": "review",
    "version": "1.0.0"
  },
  "warnings": [
    // Array of warning messages (if any)
  ],
  "error": {
    // Error details (only if success: false)
    "code": "error_code",
    "message": "Error message",
    "details": {}
  }
}
```

## Command Phases and Feedback

### Phase 1: Initialization
**What users need to know:**
- Command recognized and starting
- Configuration being loaded
- Dependencies being checked

**Feedback:**
- Normal mode: Brief "Starting..." message (only if > 1 second)
- Verbose mode: Detailed initialization steps

### Phase 2: Validation
**What users need to know:**
- Input validation results
- File existence checks
- Configuration validation

**Feedback:**
- Normal mode: Errors only (fail fast)
- Verbose mode: All validation steps

### Phase 3: Execution
**What users need to know:**
- What's happening now
- Progress for long operations
- Estimated time remaining (if available)

**Feedback:**
- Normal mode: Progress for operations > 5 seconds
- Verbose mode: Detailed step-by-step progress

### Phase 4: Results
**What users need to know:**
- Success or failure
- Summary metrics
- Output location (if files created)
- Next steps (if applicable)

**Feedback:**
- Normal mode: Clear summary with key results
- Verbose mode: Detailed results with all data

## Progress Indicators

### For Operations < 5 Seconds
- No progress indicator needed
- Show start message, then results

### For Operations 5-30 Seconds
- Simple progress: "Processing... (step X of Y)"
- Update every 2-3 seconds
- Show completion when done

### For Operations > 30 Seconds
- Detailed progress bar: `[████████░░] 80%`
- Current step information
- Estimated time remaining (if available)
- Update every 1-2 seconds

### Progress Bar Format
```
[████████████████░░░░░░░░] 67% (Step 2 of 3: Running tests...)
```

## Error Message Standards

### Error Message Components

1. **Error Type**: What kind of error (file_not_found, validation_error, etc.)
2. **Error Message**: Human-readable description
3. **Context**: Relevant details (file paths, values, etc.)
4. **Remediation**: Suggested next steps (when applicable)

### Error Message Format

**Text format:**
```
✗ Error: [Error type]
  Message: [Human-readable message]
  Context: [Relevant details]
  Suggestion: [How to fix, if applicable]
```

**JSON format:**
```json
{
  "success": false,
  "error": {
    "code": "file_not_found",
    "message": "File not found: example.py",
    "context": {
      "file_path": "example.py",
      "working_directory": "/current/path"
    },
    "remediation": "Check that the file exists and the path is correct"
  }
}
```

## Success Message Standards

### Success Message Components

1. **Confirmation**: Clear statement of success
2. **Summary**: Key results or metrics
3. **Output Location**: Where results are saved (if applicable)
4. **Next Steps**: What the user can do next (if applicable)

### Success Message Format

**Text format:**
```
✓ [Action] completed successfully
  [Summary metrics]
  [Output location, if applicable]
  [Next steps, if applicable]
```

**JSON format:**
```json
{
  "success": true,
  "message": "Review completed successfully",
  "data": {
    // Command results
  },
  "summary": {
    "files_processed": 1,
    "score": 85,
    "duration_ms": 3200
  }
}
```

## Implementation Guidelines

### 1. Use Centralized Feedback Functions
- Don't use `print()` directly
- Use feedback utility functions from `tapps_agents.cli.feedback`
- Ensures consistency across all commands

### 2. Always Provide Feedback
- Never have silent operations
- At minimum, show start and completion
- For long operations, show progress

### 3. Respect Verbosity Settings
- Check `--quiet`, `--verbose` flags
- Adjust message detail accordingly
- Don't show verbose info in normal mode

### 4. Separate Output Streams
- Errors to `stderr`
- Normal output to `stdout`
- Progress updates to `stderr` (so they don't interfere with JSON parsing)

### 5. Handle Both Formats
- Support both text and JSON output
- JSON should be complete and parseable
- Text should be human-readable
- Use `--format json|text` flag

### 6. Provide Context
- Include file paths, counts, durations
- Show what was checked or processed
- Give users enough info to understand results

### 7. Be Actionable
- Error messages should suggest fixes
- Success messages should indicate next steps
- Warnings should explain impact and remediation

### 8. Time Appropriately
- Show progress updates at reasonable intervals
- Don't spam with too-frequent updates
- Don't leave users waiting without feedback

## Examples by Command Type

### Review Command
**Normal mode:**
```
$ tapps-agents review file.py
Reviewing file.py...
✓ Review completed
Score: 85/100 | Complexity: 7.5 | Security: 9.0 | Maintainability: 8.5
Status: Passed
```

**Verbose mode:**
```
$ tapps-agents review file.py --verbose
[INFO] Loading configuration...
[INFO] Initializing ReviewerAgent...
[INFO] Analyzing file.py (1,234 lines)...
[INFO] Running complexity analysis... [████████████] 100%
[INFO] Running security scan... [████████████] 100%
[INFO] Running maintainability check... [████████████] 100%
✓ Review completed (took 3.2 seconds)
Score: 85/100
  Complexity: 7.5/10
  Security: 9.0/10
  Maintainability: 8.5/10
Status: Passed
```

### Health Check Command
**Normal mode:**
```
$ tapps-agents health
Running health checks...
[✓] Environment: healthy (95/100)
[✓] Automation: healthy (88/100)
[⚠] Execution: degraded (65/100)
  Warning: High failure rate detected
[✓] Context7 Cache: healthy (92/100)
```

**Verbose mode:**
```
$ tapps-agents health --verbose
[INFO] Initializing health check registry...
[INFO] Registering checks...
[INFO] Running EnvironmentHealthCheck...
[INFO] Checking Python version... ✓
[INFO] Checking dependencies... ✓
[✓] Environment: healthy (95/100)
  Python: 3.13.0
  Dependencies: All installed
[INFO] Running AutomationHealthCheck...
...
```

### Error Example
**Normal mode:**
```
$ tapps-agents review missing.py
✗ Error: File not found
  File: missing.py
  Working directory: /current/path
  Suggestion: Check that the file exists and the path is correct
```

**JSON mode:**
```json
{
  "success": false,
  "error": {
    "code": "file_not_found",
    "message": "File not found: missing.py",
    "context": {
      "file_path": "missing.py",
      "working_directory": "/current/path"
    },
    "remediation": "Check that the file exists and the path is correct"
  }
}
```

## Migration Strategy

### Phase 1: Create Feedback Utilities
- Build centralized feedback functions
- Support all message types and formats
- Handle verbosity levels

### Phase 2: Update High-Usage Commands
- Start with most-used commands (review, health, etc.)
- Replace direct print() calls
- Add progress indicators where needed

### Phase 3: Update All Commands
- Systematically update remaining commands
- Ensure consistency across all commands
- Add tests for feedback output

### Phase 4: Documentation and Training
- Document feedback patterns
- Update CLI development guide
- Provide examples for new commands

## Benefits

### For Users
- Clear understanding of what commands are doing
- Confidence that operations are progressing
- Better error messages with actionable guidance
- Consistent experience across all commands

### For Automation
- Reliable JSON output for parsing
- Consistent exit codes
- Structured error information
- Progress information for monitoring

### For Developers
- Clear patterns to follow
- Reusable feedback utilities
- Easier to maintain consistency
- Better debugging with verbose mode

## Summary

This design provides a comprehensive framework for consistent CLI feedback. Key elements:

1. **Message Types**: Info, Success, Warning, Error, Progress
2. **Verbosity Levels**: Quiet, Normal, Verbose
3. **Format Standards**: Consistent text and JSON structures
4. **Progress Indicators**: Appropriate for operation duration
5. **Error Standards**: Actionable error messages with context
6. **Success Standards**: Clear confirmations with summaries

Implementation should be done incrementally, starting with the most-used commands and expanding to cover all CLI functionality.

