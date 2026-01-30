# Step 1: Enhanced Prompt - Make Beads Mandatory in TappsCodingAgents

## Original Prompt

Implement the Beads mandatory feature: add `beads.required` config, enforce preflight checks so *build, *fix, *epic and CLI workflow fail when Beads is required but unavailable, update init and doctor accordingly.

## Enhanced Prompt with Requirements Analysis

### Intent Analysis
- **Primary Intent**: Make Beads (bd) mandatory when configured, failing workflows instead of silently skipping
- **Scope**: Framework enhancement (config, orchestration, init, doctor)
- **Workflow Type**: Brownfield (enhancing existing Beads integration)
- **Domains**: Configuration, workflow orchestration, CLI

### Functional Requirements

1. **Configuration**
   - Add `beads.required: bool` to `BeadsConfig` (default `False` for backward compatibility)
   - When `required=True`, workflows must fail if bd is unavailable or .beads not initialized

2. **Preflight Checks**
   - *build, *fix, *epic: Before execution, check `beads.required` and `is_available`/`is_ready`; abort with clear message if unmet
   - CLI workflow: Same check in WorkflowExecutor / CursorWorkflowExecutor
   - Provide remediation: install bd, run `bd init`, or set `beads.required: false`

3. **Init and Doctor**
   - `init`: When `beads.required=true` and bd available but `.beads` missing, strongly prompt for `bd init`; consider auto-running or blocking
   - `doctor`: Fail or warn when `beads.required=true` but bd not found or not ready

4. ***todo Command**
   - When `beads.required=true`, *todo must not fallback; fail with install/init instructions

5. **Beads Hooks**
   - Hooks (create_build_issue, etc.) remain best-effort when `required=false`; when `required=true`, preflight already blocks, so hooks always run when we reach execution

### Non-Functional Requirements

- **Backward compatibility**: Default `required=False` so existing projects unchanged
- **Clear errors**: User-friendly messages with remediation steps
- **Consistent behavior**: Same check logic across all entry points

### Architecture Guidance

- Centralize check in `tapps_agents.beads` or a new `require_beads(config, project_root) -> None` that raises with clear message
- Call from BuildOrchestrator, FixOrchestrator, EpicOrchestrator, WorkflowExecutor, TodoOrchestrator, init, doctor
