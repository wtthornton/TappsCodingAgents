# Step 1: Enhanced Prompt - Doctor Cache Status Feature

## Original Prompt
Add basic Context7 cache status checks to doctor command: check if Context7 is enabled, cache directory is accessible, and cache is populated (entry count). Keep detailed metrics in health check. Add doctor --full flag to run both doctor and health checks.

## Enhanced Specification

### Intent Analysis
- **Primary Intent**: Extend doctor command with lightweight cache status validation
- **Scope**: Framework enhancement (modifying `tapps_agents/core/doctor.py` and CLI handlers)
- **Workflow Type**: Feature enhancement (build workflow)
- **Domains**: CLI, health monitoring, cache management

### Requirements

#### Functional Requirements
1. **Basic Cache Status in Doctor**
   - Check if Context7 is enabled in config
   - Verify cache directory exists and is accessible
   - Report cache population status (entry count only)
   - Provide basic remediation if issues found

2. **Doctor --full Flag**
   - Add `--full` flag to doctor command parser
   - When `--full` is used, run both doctor checks AND health checks
   - Maintain backward compatibility (default behavior unchanged)

3. **Separation of Concerns**
   - Keep detailed cache metrics in health check system (already exists)
   - Doctor provides only basic status (enabled/disabled, accessible, populated)
   - Health check provides detailed metrics (hit rate, response time, staleness, etc.)

#### Non-Functional Requirements
- **Performance**: Doctor checks must remain fast (<2s)
- **Backward Compatibility**: Existing doctor behavior unchanged
- **Error Handling**: Graceful degradation if Context7 not configured
- **Windows Compatibility**: All file operations must work on Windows

### Architecture Guidance

#### Integration Points
- `tapps_agents/core/doctor.py` - Add cache status checks to `collect_doctor_report()`
- `tapps_agents/cli/commands/top_level.py` - Modify `handle_doctor_command()` to support `--full`
- `tapps_agents/cli/parsers/top_level.py` - Add `--full` argument to doctor parser
- `tapps_agents/context7/analytics.py` - Reuse `Analytics.get_cache_metrics()` for entry count
- `tapps_agents/context7/cache_structure.py` - Reuse for cache directory validation

#### Design Patterns
- **Reuse Existing Components**: Leverage `Context7CacheHealthCheck` logic but simplified
- **Fail-Safe**: If Context7 not configured, report as "not configured" (warn, not error)
- **Lazy Loading**: Only initialize Context7 components if Context7 is enabled

### Codebase Context

#### Related Files
- `tapps_agents/core/doctor.py` - Main doctor implementation (add cache checks here)
- `tapps_agents/cli/commands/top_level.py` - Doctor command handler (add --full support)
- `tapps_agents/cli/parsers/top_level.py` - Doctor parser (add --full argument)
- `tapps_agents/health/checks/context7_cache.py` - Reference for cache validation logic
- `tapps_agents/context7/analytics.py` - For getting cache metrics
- `tapps_agents/context7/cache_structure.py` - For cache directory structure

#### Existing Patterns
- Doctor uses `DoctorFinding` dataclass for findings
- Findings have severity: "ok", "warn", "error"
- Findings include remediation messages
- Health checks use `HealthCheckResult` with status and score

### Quality Standards

#### Security
- No sensitive data exposure in cache status
- Validate file paths to prevent directory traversal

#### Testing
- Unit tests for cache status checks
- Integration tests for --full flag
- Test with Context7 enabled/disabled
- Test with cache empty/populated
- Test cache directory permission errors

#### Documentation
- Update doctor command help text
- Document --full flag behavior
- Update command reference documentation

### Implementation Strategy

#### Task Breakdown
1. Add cache status helper function to `doctor.py`
2. Integrate cache checks into `collect_doctor_report()`
3. Add `--full` argument to doctor parser
4. Modify `handle_doctor_command()` to support --full
5. Add tests for new functionality
6. Update documentation

#### Dependencies
- Context7 integration must be importable (optional dependency)
- Cache structure must be accessible
- Health check system must be available for --full flag

### Synthesis

**Enhanced Prompt:**
Extend the doctor command with lightweight Context7 cache status validation. Add three basic checks: (1) Context7 enabled in config, (2) cache directory accessible, (3) cache populated (entry count). Keep detailed metrics in health check system. Add `--full` flag to run both doctor and health checks together. Maintain backward compatibility and fast execution time. Use existing Context7 components for validation logic but keep doctor checks minimal and fast.
