# Step 3: Architecture - Beads Mandatory

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Entry Points                                  │
│  *build  *fix  *epic  *todo  workflow  init  doctor              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  require_beads(config, project_root) → None | raises              │
│  - If beads.enabled and beads.required:                           │
│    - Check is_available(project_root)                             │
│    - Optionally: is_ready (project_root) for .beads               │
│  - Raise BeadsRequiredError with remediation if unmet             │
└─────────────────────────┬───────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ BeadsConfig  │  │ beads.client │  │ init/doctor  │
│ .required    │  │ is_available │  │ remediation  │
│ .enabled     │  │ is_ready     │  │ messages     │
└──────────────┘  └──────────────┘  └──────────────┘
```

## Integration Points

| Component | Check Location | Action on Failure |
|-----------|----------------|-------------------|
| BuildOrchestrator | Start of execute() | Raise, return error result |
| FixOrchestrator | Start of execute() | Raise, return error result |
| EpicOrchestrator | load_epic() or execute_epic() start | Raise |
| WorkflowExecutor | start() or execute() | Exit/raise |
| TodoOrchestrator | execute() | Return error dict |
| init | After config load | Print mandatory message, optionally exit |
| doctor | Beads check | Add FAIL when required + missing |

## Centralized Check

Create `tapps_agents.beads.require_beads(config, project_root) -> None`:
- No-op when `not config.beads.enabled` or `not config.beads.required`
- When required: call `is_available`; optionally `is_ready` for .beads
- Raise `BeadsRequiredError` (or use existing feedback/error) with message and remediation
