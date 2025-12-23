# CLI Feedback Implementation Guide

## Overview

This guide provides specific implementation details for enhancing CLI user feedback indicators, addressing the issues identified in the enhancement plan.

## Key Issues to Fix

1. **JSON output confusion**: Info messages output as JSON to stdout, causing PowerShell parsing errors
2. **No progress indicators**: Long operations show no progress
3. **Unclear status**: Users can't tell if commands are running, stuck, or completed
4. **Missing error clarity**: Errors not clearly distinguished

## Implementation Strategy

### 1. Fix Stream Separation (Critical)

**Problem**: JSON info messages go to stdout, causing PowerShell errors.

**Solution**: All status messages go to stderr, only final result to stdout.

**Current Code** (`tapps_agents/cli/feedback.py`):
```python
def info(self, message: str, details: dict[str, Any] | None = None) -> None:
    if self.format_type == "json":
        output = {
            "type": "info",
            "message": message,
        }
        print(json.dumps(output), file=sys.stderr)  # Already correct!
```

**Issue**: The `info()` method already outputs to stderr, but the problem is in how it's called. The report command outputs JSON to stdout during execution.

**Fix**: Ensure `feedback.info()` is used instead of direct JSON output, and ensure final result uses `output_result()` which properly separates streams.

### 2. Enhance Report Command Progress

**Current Code** (`tapps_agents/cli/commands/reviewer.py`, lines 953-967):
```python
elif command == "report":
    feedback.start_operation("Report")
    feedback.info("Generating report...")
    formats = getattr(args, "formats", ["all"])
    if "all" in formats:
        format_type = "all"
    else:
        format_type = ",".join(formats)
    reviewer = ReviewerAgent()
    result = run_async_command(
        run_report(reviewer, args.target, format_type, getattr(args, "output_dir", None))
    )
    check_result_error(result)
    feedback.clear_progress()
    feedback.output_result(result, message="Report generated successfully")
```

**Enhanced Code**:
```python
elif command == "report":
    feedback.start_operation("Report Generation")
    feedback.info(f"Starting report generation for: {args.target}")
    
    formats = getattr(args, "formats", ["all"])
    if "all" in formats:
        format_type = "all"
    else:
        format_type = ",".join(formats)
    
    # Show what formats will be generated
    format_list = format_type.split(",") if format_type != "all" else ["JSON", "Markdown", "HTML"]
    feedback.info(f"Generating reports in format(s): {', '.join(format_list)}")
    
    reviewer = ReviewerAgent()
    
    # Use progress tracker for multi-step operation
    from ..feedback import ProgressTracker
    progress = ProgressTracker(
        total_steps=5,  # discover, analyze, aggregate, generate, save
        operation_name="Report Generation",
        feedback_manager=feedback,
    )
    
    try:
        # Step 1: Discover files
        progress.update(1, "Discovering files...")
        result = await run_report_with_progress(
            reviewer, 
            args.target, 
            format_type, 
            getattr(args, "output_dir", None),
            progress_callback=lambda step, message: progress.update(step, message)
        )
        
        check_result_error(result)
        progress.complete("Report generation completed")
        feedback.clear_progress()
        
        # Show generated files
        if "reports" in result:
            feedback.info("Generated reports:")
            for report_type, report_path in result.get("reports", {}).items():
                feedback.info(f"  - {report_path}")
        
        feedback.output_result(result, message="Report generated successfully")
    except Exception as e:
        progress.complete(f"Report generation failed: {str(e)}")
        feedback.error(
            f"Report generation failed: {str(e)}",
            error_code="report_generation_failed",
            remediation="Check that the target path exists and is accessible",
        )
```

### 3. Add Progress Callbacks to Report Generation

**New Function** (`tapps_agents/cli/commands/reviewer.py`):
```python
async def run_report_with_progress(
    reviewer: ReviewerAgent,
    target: str,
    format_type: str,
    output_dir: str | None,
    progress_callback: Callable[[int, str], None] | None = None,
) -> dict[str, Any]:
    """Run report generation with progress callbacks."""
    try:
        await reviewer.activate()
        
        # Step 1: Discover files
        if progress_callback:
            progress_callback(1, "Discovering files...")
        
        # Step 2: Analyze files
        if progress_callback:
            progress_callback(2, "Analyzing code quality...")
        
        # Step 3: Aggregate scores
        if progress_callback:
            progress_callback(3, "Aggregating scores...")
        
        # Step 4: Generate reports
        if progress_callback:
            progress_callback(4, "Generating reports...")
        
        result = await reviewer.run("report", target=target, format=format_type, output_dir=output_dir)
        
        # Step 5: Complete
        if progress_callback:
            progress_callback(5, "Saving reports...")
        
        return result
    finally:
        await reviewer.close()
```

### 4. Enhance Report Generator with Progress Callbacks

**Modify** `tapps_agents/agents/reviewer/report_generator.py`:

Add progress callback parameter to `generate_all_reports()`:

```python
def generate_all_reports(
    self,
    scores: dict[str, Any],
    files: list[dict[str, Any]] | None = None,
    metadata: dict[str, Any] | None = None,
    progress_callback: Callable[[str, int], None] | None = None,
) -> dict[str, Path]:
    """Generate all report formats with progress callbacks."""
    if metadata is None:
        metadata = {}
    
    if "timestamp" not in metadata:
        metadata["timestamp"] = datetime.now()
    
    reports = {}
    
    # Generate JSON report
    if progress_callback:
        progress_callback("Generating JSON report...", 25)
    reports["json"] = self.generate_json_report(scores, files, metadata)
    
    # Generate Markdown report
    if progress_callback:
        progress_callback("Generating Markdown report...", 50)
    reports["markdown"] = self.generate_summary_report(scores, files, metadata)
    
    # Generate HTML report
    if progress_callback:
        progress_callback("Generating HTML report...", 75)
    reports["html"] = self.generate_html_report(scores, files, metadata)
    
    # Save historical data
    if progress_callback:
        progress_callback("Saving historical data...", 100)
    reports["historical"] = self.save_historical_data(scores, metadata)
    
    return reports
```

### 5. Improve Error Display

**Enhance** `tapps_agents/cli/feedback.py` error method:

```python
def error(
    self,
    message: str,
    error_code: str = "error",
    context: dict[str, Any] | None = None,
    remediation: str | None = None,
    exit_code: int = 1,
) -> None:
    """Output error message and exit."""
    # Always use stderr for errors
    if self.format_type == "json":
        output = {
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
            },
        }
        if context:
            output["error"]["context"] = context
        if remediation:
            output["error"]["remediation"] = remediation
        # Error JSON goes to stderr, not stdout
        print(json.dumps(output, indent=2), file=sys.stderr)
    else:
        # Text format with visual indicators
        print(f"\n[ERROR] ❌ {message}", file=sys.stderr)
        if error_code != "error":
            print(f"  Error Code: {error_code}", file=sys.stderr)
        if context:
            print("  Context:", file=sys.stderr)
            for key, value in context.items():
                print(f"    {key}: {value}", file=sys.stderr)
        if remediation:
            print(f"  💡 Suggestion: {remediation}", file=sys.stderr)
        print("", file=sys.stderr)  # Blank line for readability
    
    # Stop heartbeat on error
    self._stop_heartbeat()
    
    sys.exit(exit_code)
```

### 6. Add Visual Status Indicators

**Enhance** `tapps_agents/cli/feedback.py` success method:

```python
def success(
    self,
    message: str,
    data: dict[str, Any] | None = None,
    summary: dict[str, Any] | None = None,
) -> None:
    """Output success message."""
    if self.verbosity == VerbosityLevel.QUIET and data is None:
        return
        
    # Stop heartbeat when operation completes
    self._stop_heartbeat()
    
    if self.format_type == "json":
        output = {
            "success": True,
            "message": message,
        }
        if data:
            output["data"] = data
        if summary:
            output["summary"] = summary
        if self.operation_start_time:
            duration_ms = int((time.time() - self.operation_start_time) * 1000)
            output["metadata"] = {
                "timestamp": datetime.now(UTC).isoformat(),
                "duration_ms": duration_ms,
                "version": PACKAGE_VERSION,
            }
        # Success JSON goes to stdout (final result)
        print(json.dumps(output, indent=2), file=sys.stdout)
        sys.stdout.flush()
    else:
        # Text format with visual indicators
        duration_str = ""
        if self.operation_start_time:
            duration = time.time() - self.operation_start_time
            duration_str = f" (took {duration:.1f}s)"
        print(f"[SUCCESS] ✅ {message}{duration_str}", file=sys.stderr)
        if summary and self.verbosity != VerbosityLevel.QUIET:
            print("  Summary:", file=sys.stderr)
            for key, value in summary.items():
                print(f"    {key}: {value}", file=sys.stderr)
        # Data goes to stdout for parsing
        if data and self.verbosity == VerbosityLevel.QUIET:
            print(json.dumps(data, indent=2), file=sys.stdout)
        sys.stderr.flush()
        sys.stdout.flush()
```

### 7. Enhance Progress Display

**Modify** `tapps_agents/cli/feedback.py` progress method to show better indicators:

```python
def progress(
    self,
    message: str,
    percentage: int | None = None,
    show_progress_bar: bool = False,
) -> None:
    """Output progress message."""
    if self.verbosity == VerbosityLevel.QUIET:
        return
        
    if self.format_type == "json":
        # Progress updates in JSON mode go to stderr as plain text
        # (not JSON) to avoid confusion
        print(f"[PROGRESS] {message}", file=sys.stderr, end="\r")
        sys.stderr.flush()
        return
    
    # Text mode with visual indicators
    mode = self._resolve_progress_mode()
    if mode == ProgressMode.OFF:
        return

    if mode == ProgressMode.RICH:
        try:
            if self._rich is None:
                self._rich = _RichProgressRenderer()
            self._rich.update(message, percentage, show_progress_bar)
            return
        except Exception:
            # Never fail a command due to progress rendering.
            self._rich = None
            mode = ProgressMode.PLAIN

    # Plain text fallback
    from ..core.unicode_safe import safe_print, safe_format_progress_bar

    spinner = self._plain_spinner.next()
    if show_progress_bar and percentage is not None:
        bar = safe_format_progress_bar(percentage, width=24)
        safe_print(f"[RUNNING] {spinner} {message} {bar} {percentage}%", file=sys.stderr, end="\r")
    else:
        safe_print(f"[RUNNING] {spinner} {message}", file=sys.stderr, end="\r")
    sys.stderr.flush()
```

## Testing Checklist

### Manual Testing

1. **Test JSON Mode**:
   ```bash
   python -m tapps_agents.cli reviewer report . json --output-dir reports/quality
   ```
   - ✅ No JSON parsing errors in PowerShell
   - ✅ Status messages visible on stderr
   - ✅ Final result JSON on stdout only

2. **Test Text Mode**:
   ```bash
   python -m tapps_agents.cli reviewer report . text --output-dir reports/quality
   ```
   - ✅ Progress indicators visible
   - ✅ Success message with duration
   - ✅ Generated files listed

3. **Test Error Handling**:
   ```bash
   python -m tapps_agents.cli reviewer report nonexistent json
   ```
   - ✅ Clear error message
   - ✅ Error code shown
   - ✅ Remediation suggestion provided

4. **Test Long Operations**:
   ```bash
   python -m tapps_agents.cli reviewer report . json --output-dir reports/quality
   ```
   - ✅ Progress updates every 1-2 seconds
   - ✅ Heartbeat shows "still working"
   - ✅ Progress bar for operations > 30 seconds

### Automated Testing

1. **Unit Tests**: Test feedback system components
2. **Integration Tests**: Test full command execution
3. **PowerShell Tests**: Verify no JSON parsing errors
4. **Progress Tests**: Verify progress updates work correctly

## Migration Plan

### Phase 1: Critical Fixes (Week 1)
1. Fix stream separation (status to stderr, data to stdout)
2. Fix JSON output confusion
3. Add basic progress indicators

### Phase 2: Enhanced Progress (Week 2)
1. Add progress callbacks to report generation
2. Add multi-step progress tracking
3. Enhance error display

### Phase 3: Visual Improvements (Week 3)
1. Add visual status indicators (emojis, colors)
2. Add progress bars for long operations
3. Add operation timeline

### Phase 4: Advanced Features (Week 4)
1. Add resource usage display
2. Add summary dashboard
3. Add next steps suggestions

## Success Metrics

1. **Zero PowerShell Errors**: No JSON parsing errors in PowerShell
2. **Clear Status**: Users can always tell if command is running
3. **Progress Visibility**: Long operations show progress
4. **Error Clarity**: Errors are immediately obvious
5. **User Satisfaction**: Users report improved experience

## Related Files

- `tapps_agents/cli/feedback.py` - Feedback system
- `tapps_agents/cli/commands/reviewer.py` - Report command
- `tapps_agents/agents/reviewer/report_generator.py` - Report generation
- `tapps_agents/cli/progress_heartbeat.py` - Heartbeat system
- `docs/implementation/CLI_USER_FEEDBACK_ENHANCEMENT_PLAN.md` - Enhancement plan

