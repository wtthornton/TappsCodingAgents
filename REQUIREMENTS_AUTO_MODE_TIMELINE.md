# Requirements: Auto Mode with Prompt Input and Project Timeline

## Overview

Enable fully automated workflow execution with:
1. **Prompt-based workflow initiation**: Accept user description as command argument
2. **Auto mode**: Fully automated execution without human intervention
3. **Project timeline**: Track and report agent execution times and sequence
4. **Complete application delivery**: Fully working, tested application

## Current State Analysis

### What Works
- ✅ Workflow presets exist (`full`, `rapid`, `fix`, `quality`, `hotfix`)
- ✅ Workflow executor can run workflows end-to-end
- ✅ Analyst agent can gather requirements via `gather-requirements` command
- ✅ State management tracks workflow progress
- ✅ Quality gates and scoring work

### Gaps Identified

1. **No prompt/description parameter in workflow CLI**
   - Current: `python -m tapps_agents.cli workflow full`
   - Needed: `python -m tapps_agents.cli workflow full "Create a detailed interactive web application..."`
   - Impact: User must manually provide requirements later or workflow skips requirements gathering

2. **Analyst agent not called with user prompt in workflow**
   - Current: `gather_requirements` action exists but workflow executor doesn't pass user prompt
   - Needed: Workflow executor must pass user prompt to analyst agent's `gather_requirements`
   - Impact: Requirements step may fail or produce generic requirements

3. **No execution timing/metrics tracking**
   - Current: WorkflowState tracks `started_at` but not per-step timing
   - Needed: Track start/end time for each agent execution
   - Impact: Cannot generate project timeline

4. **No project timeline generation**
   - Current: No timeline report generation
   - Needed: Generate timeline report showing agent execution sequence and duration
   - Impact: User cannot see how agents executed and how long each took

5. **No auto mode flag**
   - Current: Workflow may prompt for input or wait for confirmation
   - Needed: Explicit auto mode that prevents all prompts/interruptions
   - Impact: Workflow may pause waiting for user input

6. **Missing agent action mappings in executor**
   - Current: Only `debugger`, `implementer`, `reviewer`, `tester`, `orchestrator` are mapped
   - Needed: Map `analyst`, `planner`, `architect`, `designer`, `ops`, `documenter` actions
   - Impact: Many workflow steps are skipped

## Detailed Requirements

### REQ-1: Prompt Parameter in Workflow CLI

**Priority**: Critical  
**Effort**: Low

**Requirement**:
- Add `--prompt` or positional argument to workflow command
- Accept user description/prompt as input
- Store in workflow state variables for use by agents

**Implementation**:
```python
# CLI changes
workflow_parser.add_argument(
    "--prompt", "-p",
    help="User prompt/description for the project",
    required=False
)
# Or as positional after preset name
workflow_subparsers.add_argument(
    "prompt",
    nargs="?",
    help="User prompt/description (optional)"
)
```

**Acceptance Criteria**:
- [ ] Command accepts prompt: `workflow full "Create a web app..."`
- [ ] Prompt stored in `state.variables["user_prompt"]`
- [ ] Prompt available to all agents via workflow state

---

### REQ-2: Pass Prompt to Analyst Agent

**Priority**: Critical  
**Effort**: Medium

**Requirement**:
- Workflow executor must call analyst agent's `gather_requirements` with user prompt
- Analyst agent should use prompt as the description parameter
- Requirements should be generated automatically without user input

**Implementation**:
```python
# In executor._execute_step()
elif agent_name == "analyst" and action in {"gather_requirements", "gather-requirements"}:
    user_prompt = self.state.variables.get("user_prompt", "")
    if not user_prompt:
        # Fallback: prompt user (but should not happen in auto mode)
        user_prompt = "Generate requirements for this project"
    
    requirements_result = await run_agent(
        "analyst",
        "gather-requirements",
        description=user_prompt,
        output_file="requirements.md"
    )
    self.state.variables["analyst_result"] = requirements_result
    
    # Create requirements.md artifact
    if "requirements.md" in (step.creates or []):
        req_path = self.project_root / "requirements.md"
        # Analyst agent should have created this, but verify
        created_artifacts.append({"name": "requirements.md", "path": str(req_path)})
```

**Acceptance Criteria**:
- [ ] Analyst agent receives user prompt as description
- [ ] Requirements generated automatically from prompt
- [ ] `requirements.md` file created in project root
- [ ] Requirements step completes without user input

---

### REQ-3: Execution Timing and Metrics

**Priority**: High  
**Effort**: Medium

**Requirement**:
- Track start and end time for each agent execution
- Store timing data in workflow state
- Calculate duration for each step

**Implementation**:
```python
# Add to WorkflowState model
@dataclass
class StepExecution:
    step_id: str
    agent: str
    action: str
    started_at: datetime
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    status: str = "running"  # running, completed, failed, skipped
    error: str | None = None

# In WorkflowState
step_executions: list[StepExecution] = field(default_factory=list)

# In executor._execute_step()
step_execution = StepExecution(
    step_id=step.id,
    agent=agent_name,
    action=action,
    started_at=datetime.now()
)
self.state.step_executions.append(step_execution)

try:
    # Execute agent...
    step_execution.completed_at = datetime.now()
    step_execution.duration_seconds = (
        step_execution.completed_at - step_execution.started_at
    ).total_seconds()
    step_execution.status = "completed"
except Exception as e:
    step_execution.completed_at = datetime.now()
    step_execution.duration_seconds = (
        step_execution.completed_at - step_execution.started_at
    ).total_seconds()
    step_execution.status = "failed"
    step_execution.error = str(e)
    raise
```

**Acceptance Criteria**:
- [ ] Each step execution tracked with start/end time
- [ ] Duration calculated for each step
- [ ] Timing data persisted in workflow state
- [ ] Timing data available for timeline generation

---

### REQ-4: Project Timeline Generation

**Priority**: High  
**Effort**: Medium

**Requirement**:
- Generate project timeline report showing:
  - Agent execution sequence
  - Start/end times for each agent
  - Duration for each agent
  - Total workflow duration
  - Status (completed/failed/skipped)
- Output formats: Markdown, JSON, HTML
- Save to `project-timeline.md` (and optionally JSON/HTML)

**Implementation**:
```python
# In executor or new timeline module
def generate_timeline(state: WorkflowState, workflow: Workflow) -> dict:
    """Generate project timeline from workflow state."""
    timeline = {
        "workflow_id": state.workflow_id,
        "workflow_name": workflow.name,
        "started_at": state.started_at.isoformat(),
        "completed_at": state.variables.get("completed_at"),
        "total_duration_seconds": None,
        "steps": []
    }
    
    for step_exec in state.step_executions:
        step_info = {
            "step_id": step_exec.step_id,
            "agent": step_exec.agent,
            "action": step_exec.action,
            "started_at": step_exec.started_at.isoformat(),
            "completed_at": step_exec.completed_at.isoformat() if step_exec.completed_at else None,
            "duration_seconds": step_exec.duration_seconds,
            "duration_formatted": format_duration(step_exec.duration_seconds),
            "status": step_exec.status
        }
        timeline["steps"].append(step_info)
    
    # Calculate total duration
    if timeline["completed_at"]:
        total = datetime.fromisoformat(timeline["completed_at"]) - state.started_at
        timeline["total_duration_seconds"] = total.total_seconds()
    
    return timeline

def format_timeline_markdown(timeline: dict) -> str:
    """Format timeline as Markdown."""
    lines = [
        "# Project Timeline",
        "",
        f"**Workflow**: {timeline['workflow_name']}",
        f"**Started**: {timeline['started_at']}",
        f"**Total Duration**: {format_duration(timeline['total_duration_seconds'])}",
        "",
        "## Agent Execution Timeline",
        "",
        "| Step | Agent | Action | Started | Duration | Status |",
        "|------|-------|--------|---------|----------|--------|"
    ]
    
    for step in timeline["steps"]:
        lines.append(
            f"| {step['step_id']} | {step['agent']} | {step['action']} | "
            f"{step['started_at']} | {step['duration_formatted']} | {step['status']} |"
        )
    
    return "\n".join(lines)
```

**Acceptance Criteria**:
- [ ] Timeline report generated automatically on workflow completion
- [ ] Report includes all agent executions with timing
- [ ] Report saved as `project-timeline.md`
- [ ] Report shows total duration and per-step durations
- [ ] Report formatted in readable Markdown

---

### REQ-5: Auto Mode Flag

**Priority**: High  
**Effort**: Low

**Requirement**:
- Add `--auto` or `--no-prompt` flag to workflow command
- Prevent all prompts, confirmations, and user input requests
- Agents should use defaults or auto-generate when input needed

**Implementation**:
```python
# CLI changes
common_workflow_args.add_argument(
    "--auto",
    action="store_true",
    help="Auto mode: no prompts, fully automated execution"
)

# In executor
def __init__(self, ..., auto_mode: bool = False):
    self.auto_mode = auto_mode

# In agent calls
if self.auto_mode:
    # Pass auto_mode to agents
    result = await run_agent(..., auto_mode=True)
```

**Acceptance Criteria**:
- [ ] `--auto` flag prevents all prompts
- [ ] Workflow completes without user interaction
- [ ] Agents use sensible defaults when input needed

---

### REQ-6: Complete Agent Action Mappings

**Priority**: Critical  
**Effort**: High

**Requirement**:
- Map all agent actions in workflow executor:
  - `analyst`: `gather_requirements`, `analyze`, `research_technology`
  - `planner`: `create_stories`, `plan`, `breakdown`
  - `architect`: `design_system`, `design_architecture`
  - `designer`: `api_design`, `design_api`
  - `implementer`: `write_code`, `implement`, `refactor` (already exists)
  - `reviewer`: `review_code`, `score` (already exists)
  - `tester`: `write_tests`, `test` (already exists)
  - `ops`: `security_scan`, `audit`
  - `documenter`: `generate_docs`, `document`

**Implementation**:
```python
# In executor._execute_step()
# Add mappings for each agent type

elif agent_name == "analyst":
    if action in {"gather_requirements", "gather-requirements"}:
        user_prompt = self.state.variables.get("user_prompt", "")
        result = await run_agent("analyst", "gather-requirements", description=user_prompt)
        # Handle result...
    
elif agent_name == "planner":
    if action in {"create_stories", "create-stories", "plan"}:
        requirements_path = self.project_root / "requirements.md"
        requirements = requirements_path.read_text() if requirements_path.exists() else ""
        result = await run_agent("planner", "create-stories", requirements=requirements)
        # Handle result...

elif agent_name == "architect":
    if action in {"design_system", "design-system", "design_architecture"}:
        requirements_path = self.project_root / "requirements.md"
        stories_dir = self.project_root / "stories"
        # Gather inputs...
        result = await run_agent("architect", "design-system", ...)
        # Handle result...

# ... similar for other agents
```

**Acceptance Criteria**:
- [ ] All agent actions from full-sdlc.yaml workflow mapped
- [ ] Each agent receives correct inputs from previous steps
- [ ] Artifacts created correctly
- [ ] Workflow can complete full SDLC without skipping steps

---

### REQ-7: Enhanced Documentation Generation

**Priority**: Medium  
**Effort**: Medium

**Requirement**:
- Documenter agent should generate comprehensive documentation:
  - User guide
  - Technical specifications
  - Technical design
  - Technical architecture
  - Examples
- Documentation should be interactive web-based (if requested)
- Documentation should be a "selling point" for the application

**Implementation**:
- Extend documenter agent to generate:
  - Interactive web documentation (HTML/JS)
  - User guide with examples
  - Technical specs
  - Architecture diagrams (Mermaid/PlantUML)
  - API documentation
  - Code examples

**Acceptance Criteria**:
- [ ] Comprehensive documentation generated
- [ ] Documentation includes all requested sections
- [ ] Documentation is easy to use and visually appealing
- [ ] Documentation serves as selling point

---

### REQ-8: Web Application Generation

**Priority**: High (for user's specific request)  
**Effort**: High

**Requirement**:
- Implementer agent should generate complete web application
- Application should be:
  - Modern and interactive
  - Fully functional
  - Well-tested
  - Production-ready

**Implementation**:
- Implementer agent should:
  - Generate modern web framework (React/Vue/Next.js or Flask/FastAPI)
  - Create complete UI components
  - Implement all features from requirements
  - Generate configuration files
  - Create deployment scripts

**Acceptance Criteria**:
- [ ] Complete web application generated
- [ ] Application is modern and interactive
- [ ] Application is fully functional
- [ ] Application passes all tests
- [ ] Application can be run immediately

---

## Implementation Priority

### Phase 1: Critical Path (Enable Basic Auto Mode)
1. REQ-1: Prompt parameter in CLI
2. REQ-2: Pass prompt to analyst agent
3. REQ-6: Complete agent action mappings
4. REQ-5: Auto mode flag

### Phase 2: Timeline and Metrics
5. REQ-3: Execution timing
6. REQ-4: Timeline generation

### Phase 3: Enhanced Features
7. REQ-7: Enhanced documentation
8. REQ-8: Web application generation

## Testing Requirements

1. **Unit Tests**:
   - Test prompt parameter parsing
   - Test prompt passing to analyst
   - Test timing tracking
   - Test timeline generation

2. **Integration Tests**:
   - Test full workflow with prompt
   - Test auto mode execution
   - Test timeline generation on completion

3. **End-to-End Tests**:
   - Run full workflow with user prompt
   - Verify complete application generated
   - Verify timeline report generated
   - Verify no user prompts during execution

## Example Usage

After implementation, user should be able to run:

```bash
python -m tapps_agents.cli workflow full --auto "Create a detailed interactive web application that is very modern and explains all the detailed information about this application. Contains a users guide, technical specs, technical designs, technical architecture and examples. Needs to be easy to use and a selling point to this application."
```

Expected output:
1. Workflow executes fully automated
2. Complete web application generated
3. All tests pass
4. `project-timeline.md` generated showing:
   - Agent execution sequence
   - Duration for each agent
   - Total execution time

## Files to Modify

1. `tapps_agents/cli.py` - Add prompt parameter and auto flag
2. `tapps_agents/workflow/executor.py` - Add timing, agent mappings, auto mode
3. `tapps_agents/workflow/models.py` - Add StepExecution model
4. `tapps_agents/workflow/timeline.py` - New module for timeline generation
5. Agent modules - Ensure they support auto mode

## Dependencies

- No new external dependencies required
- Use existing datetime, json modules
- Timeline can use Markdown formatting (no special library needed)

