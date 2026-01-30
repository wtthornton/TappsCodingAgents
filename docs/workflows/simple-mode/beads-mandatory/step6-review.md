# Step 6: Review - Beads Mandatory Implementation

## Implementation Summary

- **beads.required** config added to BeadsConfig (default False)
- **require_beads()** and **BeadsRequiredError** added to beads.client
- Preflight checks integrated: BuildOrchestrator, FixOrchestrator, EpicOrchestrator, TodoOrchestrator, WorkflowExecutor, CursorWorkflowExecutor
- Doctor: fail when beads.required but bd missing or not initialized
- Documentation: BEADS_INTEGRATION.md updated

## Quality Checklist

- [x] Backward compatible (required=False default)
- [x] Clear error messages with remediation
- [x] Unit tests for require_beads (5 cases)
- [x] Config test updated for required field
- [x] All 62 unit tests passing
