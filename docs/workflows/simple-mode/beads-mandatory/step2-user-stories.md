# Step 2: User Stories - Beads Mandatory

## Story 1: Add beads.required config
- **As a** project maintainer
- **I want** to set `beads.required: true` in config
- **So that** workflows fail when Beads is unavailable instead of silently skipping
- **Acceptance**: BeadsConfig has `required` field, default False; config loads correctly

## Story 2: Preflight check for *build and *fix
- **As a** user running *build or *fix
- **I want** the workflow to fail early with clear instructions when beads.required and bd unavailable
- **So that** I know I must install/init Beads before proceeding
- **Acceptance**: BuildOrchestrator and FixOrchestrator check before execution; raise with remediation

## Story 3: Preflight check for *epic
- **As a** user running *epic
- **I want** the epic to fail when beads.required and bd unavailable
- **So that** Epic sync and tracking work correctly
- **Acceptance**: EpicOrchestrator checks before load_epic/execute; raise with remediation

## Story 4: Preflight check for CLI workflow
- **As a** user running `tapps-agents workflow`
- **I want** the workflow to fail when beads.required and bd unavailable
- **Acceptance**: WorkflowExecutor/CursorWorkflowExecutor check at start; exit with message

## Story 5: *todo fails when required
- **As a** user running *todo
- **I want** it to fail (not fallback) when beads.required and bd unavailable
- **Acceptance**: TodoOrchestrator returns error result, not guidance fallback

## Story 6: Doctor reports required-but-missing
- **As a** user running doctor
- **I want** doctor to fail or strongly warn when beads.required but bd not found/ready
- **Acceptance**: Doctor check fails with remediation when required + missing

## Story 7: Init enforces bd init when required
- **As a** user running init
- **I want** init to prompt/require bd init when beads.required and .beads missing
- **Acceptance**: Init prints mandatory message; optionally blocks or auto-runs bd init
