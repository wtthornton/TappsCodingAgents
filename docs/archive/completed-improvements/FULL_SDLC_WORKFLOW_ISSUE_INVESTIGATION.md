# Full SDLC Workflow Issue Investigation

## Issue Summary

The `@simple-mode *full` workflow failed with error:
```
Workflow blocked: no ready steps and workflow not complete. 
Completed: 3/10. Blocking issues:
- Step design (architect/design_system): missing ['stories/']
- Step api_design (designer/api_design): missing ['architecture.md']
- Step implementation (implementer/write_code): missing ['architecture.md', 'api-specs/', 'stories/']
- Step review (reviewer/review_code): missing ['src/']
- Step testing (tester/write_tests): missing ['src/']
- Step security (ops/security_scan): missing ['src/']
- Step documentation (documenter/generate_docs): missing ['src/']
```

## Investigation

### Question: Is `@simple-mode *full` Broken or Working as Designed?

**Initial Hypothesis**: The workflow is designed for greenfield projects and requires specific file structures. However, the question is: **Should the agents create these artifacts, or are they expected to exist beforehand?**

### Key Findings

1. **`@simple-mode *full` uses `full-sdlc.yaml` preset**
   - Handler: `handle_simple_mode_full()` in `tapps_agents/cli/commands/simple_mode.py`
   - Uses `WorkflowExecutor` with `full-sdlc.yaml` preset
   - Workflow type: `greenfield` (from YAML)

2. **Workflow Executor Behavior**
   - Uses `CursorWorkflowExecutor` in Cursor mode
   - Checks for required artifacts BEFORE allowing steps to execute
   - Error occurs in `_handle_no_ready_steps()` when artifacts are missing

3. **Artifact Detection**
   - `CursorWorkflowExecutor` uses `check_skill_completion()` to detect artifacts
   - Checks worktree for expected artifacts
   - Artifacts must exist in worktree for steps to proceed

4. **The Planning Step (Step 2 of 10)**
   - Step: `planning` (agent: `planner`, action: `create_stories`)
   - Should create: `stories/` directory
   - The workflow shows "Step 1 completed" (requirements step)
   - Planning step completed (3/10 steps completed)
   - But `stories/` directory not detected

### Possible Root Causes

#### Hypothesis 1: Artifact Detection Bug
**Theory**: The planning step DID create `stories/` directory, but the executor isn't detecting it.

**Evidence to check**:
- Worktree location where artifacts are created
- Artifact detection logic in `check_skill_completion()`
- Worktree vs project root path resolution

#### Hypothesis 2: Agent Didn't Create Artifact
**Theory**: The planner agent didn't actually create the `stories/` directory.

**Evidence to check**:
- Planner agent `create_stories` action implementation
- Does it create `stories/` directory or just files?
- Worktree isolation - are artifacts created in the right location?

#### Hypothesis 3: Expected Behavior (Greenfield Projects)
**Theory**: Full SDLC workflow is designed for projects that already have this structure, or requires manual setup.

**Evidence**:
- Workflow type: `greenfield` (from YAML)
- Documentation says "Best for: Enterprise projects, new applications"
- May require pre-existing file structure

### Critical Question

**Is the Full SDLC workflow supposed to:**
- **A)** Create the file structure automatically (agents create artifacts)
- **B)** Require the file structure to exist beforehand
- **C)** Have a bug where artifacts aren't being created/detected properly

### Recommended Investigation Steps

1. **Check if planning step actually created `stories/` directory**
   - Look in worktree directory: `.tapps-agents/worktrees/workflow-{id}/`
   - Check for `stories/` directory
   - Verify artifact paths in workflow state

2. **Check artifact detection logic**
   - Review `check_skill_completion()` function
   - Verify worktree path resolution
   - Check if directory artifacts are properly detected

3. **Check planner agent implementation**
   - Does `create_stories` action create a directory or files?
   - What artifacts does it actually produce?
   - Does it match the workflow expectation (`stories/`)?

4. **Test Full SDLC workflow on a greenfield project**
   - Create a new project
   - Run `@simple-mode *full` with a simple description
   - Monitor artifact creation step-by-step
   - Verify if artifacts are created and detected

### Comparison with `@simple-mode *build`

**`@simple-mode *build`**:
- Uses `BuildOrchestrator` (skill-based orchestration)
- Doesn't use YAML workflow dependencies
- Creates documentation in `docs/workflows/simple-mode/`
- No strict file structure requirements
- Works with existing project layouts

**`@simple-mode *full`**:
- Uses `WorkflowExecutor` with YAML preset
- Strict artifact dependencies
- Expects specific file structure
- Designed for greenfield projects
- May have artifact detection issues

## Conclusion

**The issue needs investigation to determine if:**
1. Full SDLC workflow has a bug (artifacts not created/detected)
2. Full SDLC workflow is working as designed (requires pre-existing structure)
3. Full SDLC workflow needs fixing (agent handlers don't create expected artifacts)

**Until investigation is complete, recommendation:**
- For React component updates: Use `@simple-mode *build` (verified working, flexible)
- For Full SDLC workflow: Needs investigation to determine if it's broken or requires setup

## Next Steps

1. **Verify artifact creation**: Check if planning step created `stories/` directory
2. **Check artifact detection**: Verify if executor can find artifacts in worktree
3. **Test Full SDLC**: Run on a clean project to see if it works
4. **Fix if broken**: If artifacts are created but not detected, fix detection logic
5. **Document if expected**: If it requires pre-existing structure, document this requirement
