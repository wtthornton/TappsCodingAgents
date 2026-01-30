# Step 4: Design - Beads Mandatory

## Component Specifications

### 1. BeadsConfig (config.py)
- Add `required: bool = False`
- Description: "When true, workflows fail if bd is unavailable or .beads not initialized."

### 2. beads/require.py (new module or in client.py)
- `require_beads(config: ProjectConfig, project_root: Path) -> None`
- Raises `BeadsRequiredError` when beads.enabled and beads.required but (not is_available or not is_ready)
- Exception message: "Beads (bd) is required but not available. Install bd to tools/bd or PATH, run 'bd init' or 'bd init --stealth', then 'bd doctor --fix'. Or set beads.required: false in .tapps-agents/config.yaml. See docs/BEADS_INTEGRATION.md."

### 3. Orchestrator Integration
- BuildOrchestrator: Call require_beads at start of _execute_build_workflow (before beads create)
- FixOrchestrator: Call require_beads at start
- EpicOrchestrator: Call require_beads in load_epic (before sync) when sync_epic would run
- TodoOrchestrator: Call require_beads; on exception return error result
- WorkflowExecutor: Call require_beads in start() or at execute begin

### 4. Doctor
- When beads.enabled and beads.required and (not is_available or not is_ready): add FAIL result with remediation

### 5. Init
- When beads.required and bd available but .beads missing: print mandatory message (upgrade from hint)
- Optionally: exit 1 when required and bd not found (configurable)
