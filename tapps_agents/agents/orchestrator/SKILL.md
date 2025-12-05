# Orchestrator Agent - Skill Definition

## Purpose

The Orchestrator Agent coordinates YAML-defined workflows and makes gate decisions. It is responsible for:

- Loading and executing workflows from YAML definitions
- Making gate decisions based on scoring and conditions
- Routing to appropriate workflows (Greenfield/Brownfield)
- Tracking workflow state and progress
- Coordinating agent execution within workflows

## Permissions

- **Read**: ✅
- **Write**: ❌
- **Edit**: ❌
- **Grep**: ✅
- **Glob**: ✅
- **Bash**: ❌

**Type**: Read-only agent (coordination only, no code modification)

## Commands

### `*workflow-list`

List all available workflows in the `workflows/` directory.

**Example:**
```bash
tapps-agents orchestrator *workflow-list
```

**Returns:**
```json
{
  "workflows": [
    {
      "id": "example-feature-development",
      "name": "Example Feature Development Workflow",
      "description": "Standard workflow for new feature implementation",
      "version": "1.0.0",
      "type": "greenfield",
      "file": "workflows/example-feature-development.yaml"
    }
  ]
}
```

### `*workflow-start {workflow_id}`

Start a workflow by ID.

**Example:**
```bash
tapps-agents orchestrator *workflow-start example-feature-development
```

**Returns:**
```json
{
  "success": true,
  "workflow_id": "example-feature-development",
  "workflow_name": "Example Feature Development Workflow",
  "status": "running",
  "current_step": "requirements",
  "message": "Workflow 'Example Feature Development Workflow' started"
}
```

### `*workflow-status`

Get the current workflow execution status.

**Example:**
```bash
tapps-agents orchestrator *workflow-status
```

**Returns:**
```json
{
  "workflow_id": "example-feature-development",
  "status": "running",
  "current_step": "planning",
  "current_step_details": {
    "id": "planning",
    "agent": "planner",
    "action": "create_stories"
  },
  "completed_steps": ["requirements"],
  "skipped_steps": [],
  "artifacts_count": 1,
  "can_proceed": true
}
```

### `*workflow-next`

Get information about the next step in the workflow.

**Example:**
```bash
tapps-agents orchestrator *workflow-next
```

**Returns:**
```json
{
  "next_step": {
    "id": "design",
    "agent": "architect",
    "action": "design_system",
    "context_tier": 2,
    "requires": ["requirements.md", "stories/"],
    "creates": ["architecture.md"]
  }
}
```

### `*workflow-skip {step_id}`

Skip an optional step in the workflow.

**Example:**
```bash
tapps-agents orchestrator *workflow-skip review
```

**Returns:**
```json
{
  "success": true,
  "message": "Step 'review' skipped",
  "current_step": "testing"
}
```

### `*workflow-resume`

Resume an interrupted workflow (loads state from persistence).

**Example:**
```bash
tapps-agents orchestrator *workflow-resume
```

### `*gate {condition}`

Make a gate decision based on condition and scoring data.

**Example:**
```bash
tapps-agents orchestrator *gate --condition "scoring.passed == true" --scoring-data '{"passed": true, "overall_score": 85}'
```

**Returns:**
```json
{
  "passed": true,
  "condition": "scoring.passed == true",
  "scoring": {
    "passed": true,
    "overall_score": 85
  },
  "message": "Gate passed"
}
```

### `*help`

Show help for orchestrator commands.

## Workflow Integration

The Orchestrator Agent integrates with the Workflow Engine to:

1. **Load Workflows**: Parse YAML workflow definitions
2. **Execute Steps**: Coordinate agent execution for each step
3. **Track Artifacts**: Monitor artifact creation and dependencies
4. **Make Gates**: Evaluate conditions and scoring to determine workflow progression
5. **Handle Branching**: Route to different steps based on gate decisions

## Gate Decision Logic

The orchestrator evaluates gate conditions using:

- **Scoring Data**: Results from reviewer agent (overall_score, passed, etc.)
- **Conditions**: String expressions like "scoring.passed == true" or "overall_score >= 70"
- **Thresholds**: Minimum scores for passing gates

**Gate Outcomes:**
- **Pass**: Workflow proceeds to `on_pass` step
- **Fail**: Workflow loops back to `on_fail` step (typically for retry)

## Context Tier Usage

The orchestrator uses **Tier 1** context (minimal) since it only coordinates workflows and doesn't analyze code.

## Integration with Other Agents

The orchestrator coordinates:

- **Planner**: Creates stories and plans
- **Architect**: Designs system architecture
- **Implementer**: Generates code
- **Reviewer**: Reviews code and provides scoring
- **Tester**: Generates and runs tests
- **Debugger**: Analyzes errors
- **Documenter**: Generates documentation

## Example Workflow Execution

```yaml
# workflows/example-feature-development.yaml
workflow:
  id: example-feature-development
  steps:
    - id: review
      agent: reviewer
      action: review_code
      gate:
        condition: "scoring.passed == true"
        on_pass: testing
        on_fail: implementation
```

**Execution Flow:**
1. Orchestrator starts workflow
2. Reviewer agent reviews code
3. Orchestrator evaluates gate: `scoring.passed == true`
4. If passed → proceed to testing
5. If failed → loop back to implementation

