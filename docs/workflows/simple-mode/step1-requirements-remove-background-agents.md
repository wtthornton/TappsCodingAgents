# Step 1: Requirements Analysis - Remove Background Agents

## Overview
Remove all Background Agents code and infrastructure from the TappsCodingAgents framework while maintaining backward compatibility for existing workflows that may reference Background Agents concepts.

## Functional Requirements

### FR1: Remove Background Agent Implementation Files
- Remove all Background Agent implementation modules
- Remove Background Agent API client code
- Remove Background Agent configuration generators
- Remove Background Agent auto-execution infrastructure
- Remove Background Agent wrapper utilities

### FR2: Remove Background Agent Dependencies
- Remove imports of Background Agent modules from all files
- Update files that depend on Background Agent functionality
- Remove Background Agent references from CLI commands
- Remove Background Agent references from workflow executors

### FR3: Maintain Artifact Classes
- Keep artifact classes (docs_artifact, ops_artifact, quality_artifact, testing_artifact, context_artifact)
- These represent data structures, not Background Agent implementations
- Artifacts can be produced by foreground agents (Cursor Skills) or direct execution

### FR4: Update Configuration
- Remove Background Agent configuration from init_project
- Update config schema to remove Background Agent settings
- Keep background-agents.yaml file structure for reference (empty agents list)
- Update documentation to reflect Background Agents removal

### FR5: Update Workflow Execution
- Remove Background Agent routing from workflow executor
- Update CursorWorkflowExecutor to use direct execution only
- Remove Background Agent cleanup code
- Update Simple Mode to not reference Background Agents

## Non-Functional Requirements

### NFR1: Backward Compatibility
- Existing workflows should continue to work
- Artifact structures remain unchanged
- Workflow YAML files remain valid (just won't use Background Agents)

### NFR2: Code Quality
- All removed code must be cleanly removed (no dead imports)
- Update all references to removed modules
- Maintain code organization and structure

### NFR3: Documentation
- Update all documentation that references Background Agents
- Add migration notes if needed
- Update command references

### NFR4: Testing
- Remove Background Agent tests
- Update tests that depend on Background Agent infrastructure
- Ensure remaining tests pass

## Technical Constraints

### TC1: Keep Cursor Skills Integration
- Cursor Skills continue to work (they're foreground agents)
- Skill invoker continues to work (just won't use Background Agent API)
- Direct execution fallback continues to work

### TC2: Keep Worktree Management
- Worktree manager is used by other features, not just Background Agents
- Keep worktree infrastructure for direct execution isolation

### TC3: Keep Progress Reporting
- Progress reporting is used by multiple execution modes
- Keep progress infrastructure for direct execution and Skills

## Files to Remove

### Core Modules
- `tapps_agents/workflow/background_agent_api.py`
- `tapps_agents/workflow/background_agent_config.py`
- `tapps_agents/workflow/background_agent_generator.py`
- `tapps_agents/workflow/background_auto_executor.py`
- `tapps_agents/workflow/background_context_agent.py`
- `tapps_agents/workflow/background_docs_agent.py`
- `tapps_agents/workflow/background_ops_agent.py`
- `tapps_agents/workflow/background_quality_agent.py`
- `tapps_agents/workflow/background_testing_agent.py`
- `tapps_agents/core/background_wrapper.py`

### Files to Update (Remove Background Agent References)
- `tapps_agents/workflow/executor.py`
- `tapps_agents/workflow/cursor_executor.py`
- `tapps_agents/workflow/skill_invoker.py`
- `tapps_agents/cli/commands/top_level.py`
- `tapps_agents/cli/commands/status.py`
- `tapps_agents/cli/commands/simple_mode.py`
- `tapps_agents/core/init_project.py`
- `tapps_agents/workflow/health_checker.py`
- `tapps_agents/core/fallback_strategy.py` (may contain Background Agent logic)
- `tapps_agents/workflow/__init__.py`

### Test Files to Remove/Update
- `tests/unit/workflow/test_background_agent_generator.py`
- `tests/unit/workflow/test_background_auto_executor.py`
- `tests/integration/workflow/test_background_agents.py`
- Update any tests that import Background Agent modules

### Documentation to Update
- `docs/BACKGROUND_AGENTS_GUIDE.md`
- `docs/BACKGROUND_AGENTS_MIGRATION_GUIDE.md`
- `docs/BACKGROUND_AGENTS_TROUBLESHOOTING.md`
- `docs/BACKGROUND_AGENTS_USE_CASE_GUIDE.md`
- `README.md`
- `.cursor/rules/quick-reference.mdc`
- `.cursor/rules/command-reference.mdc`
- `docs/ARCHITECTURE.md`

## Out of Scope

### Keep These (Not Background Agent Specific)
- Artifact classes (data structures)
- Worktree manager (used by other features)
- Progress reporting (used by multiple execution modes)
- Cursor Skills integration (foreground agents)
- Direct execution fallback
- Skill invoker (for Cursor Skills, not Background Agents)

## Success Criteria

1. All Background Agent implementation files removed
2. No imports of Background Agent modules in codebase
3. All tests pass (with Background Agent tests removed)
4. Documentation updated to reflect removal
5. Workflows continue to work using direct execution or Cursor Skills
6. No runtime errors when executing workflows
