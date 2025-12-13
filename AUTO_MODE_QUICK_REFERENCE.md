# Auto Mode with Timeline - Quick Reference

## What You Want to Do

Run a fully automated workflow that:
1. Takes your prompt as input
2. Executes completely without human intervention
3. Generates a complete, tested application
4. Produces a project timeline showing agent execution

## Current Command (What Works Now)

```bash
# Basic workflow execution (no prompt parameter yet)
python -m tapps_agents.cli workflow full
```

**Limitations**:
- ❌ Cannot pass prompt/description as argument
- ❌ Requirements gathering may be skipped or generic
- ❌ No execution timeline generated
- ❌ Some agent actions not mapped (steps may be skipped)

## Target Command (After Implementation)

```bash
# Full auto mode with prompt
python -m tapps_agents.cli workflow full --auto "Create a detailed interactive web application that is very modern and explains all the detailed information about this application. Contains a users guide, technical specs, technical designs, technical architecture and examples. Needs to be easy to use and a selling point to this application."
```

**What This Will Do**:
- ✅ Accepts your prompt as input
- ✅ Fully automated execution (no prompts)
- ✅ Generates complete application
- ✅ Produces `project-timeline.md` with execution details

## What Needs to Be Implemented

See `REQUIREMENTS_AUTO_MODE_TIMELINE.md` for full details. Key gaps:

### 1. Prompt Parameter (Critical)
- **Gap**: CLI doesn't accept prompt argument
- **Fix**: Add `--prompt` or positional argument
- **Impact**: Cannot pass your description to workflow

### 2. Agent Action Mappings (Critical)
- **Gap**: Only 5 of 13 agents have action mappings
- **Missing**: analyst, planner, architect, designer, ops, documenter
- **Impact**: Many workflow steps are skipped

### 3. Execution Timing (High Priority)
- **Gap**: No per-step timing tracking
- **Fix**: Track start/end time for each agent
- **Impact**: Cannot generate timeline

### 4. Timeline Generation (High Priority)
- **Gap**: No timeline report generation
- **Fix**: Generate `project-timeline.md` on completion
- **Impact**: Cannot see how agents executed

### 5. Auto Mode Flag (High Priority)
- **Gap**: No explicit auto mode
- **Fix**: Add `--auto` flag to prevent prompts
- **Impact**: Workflow may pause for input

## Workaround (Until Implementation)

If you need to use this now, you can:

1. **Run workflow manually**:
   ```bash
   python -m tapps_agents.cli workflow full
   ```

2. **Provide requirements manually**:
   - Create `requirements.md` before running
   - Or edit it after analyst step

3. **Monitor execution**:
   - Check `.tapps-agents/workflow-state/` for state files
   - Manually track timing from logs

4. **Generate timeline manually**:
   - Parse workflow state JSON files
   - Calculate durations from timestamps

## Implementation Status

| Requirement | Status | Priority | Effort |
|------------|--------|----------|--------|
| Prompt Parameter | ❌ Not Implemented | Critical | Low |
| Pass Prompt to Analyst | ❌ Not Implemented | Critical | Medium |
| Agent Action Mappings | ⚠️ Partial (5/13) | Critical | High |
| Execution Timing | ❌ Not Implemented | High | Medium |
| Timeline Generation | ❌ Not Implemented | High | Medium |
| Auto Mode Flag | ❌ Not Implemented | High | Low |
| Enhanced Documentation | ❌ Not Implemented | Medium | Medium |
| Web App Generation | ⚠️ Basic Only | High | High |

## Next Steps

1. **Review Requirements**: Read `REQUIREMENTS_AUTO_MODE_TIMELINE.md`
2. **Prioritize**: Focus on Phase 1 (Critical Path) first
3. **Implement**: Start with prompt parameter and agent mappings
4. **Test**: Verify full workflow execution
5. **Enhance**: Add timing and timeline generation

## Files to Create/Modify

### New Files
- `tapps_agents/workflow/timeline.py` - Timeline generation module

### Modified Files
- `tapps_agents/cli.py` - Add prompt parameter and auto flag
- `tapps_agents/workflow/executor.py` - Add timing, mappings, auto mode
- `tapps_agents/workflow/models.py` - Add StepExecution model

## Estimated Implementation Time

- **Phase 1 (Critical)**: 4-6 hours
- **Phase 2 (Timeline)**: 2-3 hours
- **Phase 3 (Enhanced)**: 4-8 hours
- **Total**: 10-17 hours

## Questions?

- See `REQUIREMENTS_AUTO_MODE_TIMELINE.md` for detailed requirements
- Check workflow executor code in `tapps_agents/workflow/executor.py`
- Review agent implementations in `tapps_agents/agents/`

