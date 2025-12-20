# Epic 9: Background Agent Config Auto-Generation

## Epic Goal

Automatically generate Background Agent configurations from workflow steps, enabling seamless integration between workflow execution and Cursor Background Agents. This eliminates manual configuration overhead and ensures Background Agents are always aligned with active workflows.

## Epic Description

### Existing System Context

- **Current relevant functionality**:
  - `BackgroundAgentGenerator` class exists and can generate agent configs from workflow steps
  - Background Agents configured manually in `.cursor/background-agents.yaml`
  - Workflow steps define agent, action, and execution requirements
  - Background Agents can auto-execute workflow steps via `.cursor-skill-command.txt` files
  - Generator is not automatically invoked during workflow execution
- **Technology stack**: Python 3.13+, YAML generation, Cursor Background Agents format, workflow engine
- **Integration points**:
  - `tapps_agents/workflow/executor.py` (WorkflowExecutor - workflow execution)
  - `tapps_agents/core/background_agent_generator.py` (BackgroundAgentGenerator - existing generator)
  - `.cursor/background-agents.yaml` (Background Agent configuration)
  - `workflows/presets/*.yaml` (workflow definitions)
  - `docs/YAML_WORKFLOW_ARCHITECTURE_DESIGN.md` (architecture reference)

### Enhancement Details

- **What's being added/changed**:
  - Enhanced `BackgroundAgentGenerator` that generates configs for all workflow steps
  - Automatic config generation when workflow starts
  - Config cleanup when workflow completes
  - Watch paths for auto-execution based on step `requires` and `creates` fields
  - Natural language triggers for Background Agents
  - Config validation to ensure generated configs are valid
  - Integration with workflow execution lifecycle
- **How it integrates**:
  - `BackgroundAgentGenerator` reads workflow YAML and generates configs for each step
  - Configs generated when workflow starts (added to `.cursor/background-agents.yaml`)
  - Configs cleaned up when workflow completes (removed from config file)
  - Watch paths derived from step `requires` and `creates` artifacts
  - Natural language triggers derived from step descriptions and agent actions
- **Success criteria**:
  - Background Agent configs generated automatically from workflows
  - Generated configs are valid and functional
  - Configs align with workflow steps and execution requirements
  - Watch paths enable auto-execution when artifacts change
  - Config cleanup prevents orphaned agents
  - Integration with workflow lifecycle is seamless

## Stories

1. **Story 9.1: Enhanced BackgroundAgentGenerator** ✅
   - Enhance `BackgroundAgentGenerator` to generate configs for all workflow steps
   - Add support for watch paths derived from step `requires` and `creates`
   - Add natural language trigger generation from step metadata
   - Improve config structure and organization
   - Acceptance criteria: Generator creates configs for all workflow steps; watch paths and triggers are accurate

2. **Story 9.2: Watch Path Generation** ✅
   - Extract watch paths from step `requires` fields (artifacts to watch)
   - Extract watch paths from step `creates` fields (outputs to monitor)
   - Generate watch path patterns for file/directory monitoring
   - Add watch path validation and normalization
   - Acceptance criteria: Watch paths correctly derived from step artifacts; patterns are valid and functional

3. **Story 9.3: Natural Language Trigger Generation** ✅
   - Generate natural language triggers from step descriptions
   - Generate triggers from agent actions and commands
   - Create trigger patterns for common workflow operations
   - Add trigger validation and deduplication
   - Acceptance criteria: Triggers are meaningful and accurate; patterns cover common use cases

4. **Story 9.4: Workflow Lifecycle Integration** ✅
   - Integrate config generation on workflow start
   - Integrate config cleanup on workflow completion
   - Add config update on workflow state changes
   - Handle workflow interruption and resume scenarios
   - Acceptance criteria: Configs generated/cleaned up correctly; lifecycle integration is seamless

5. **Story 9.5: Config Validation & Testing** ✅
   - Validate generated configs against Cursor Background Agents schema
   - Test generated configs with Cursor Background Agents
   - Add validation error handling and reporting
   - Create test suite for config generation
   - Acceptance criteria: All generated configs are valid; validation catches errors; tests pass

6. **Story 9.6: Config Management & Organization** ✅
   - Organize generated configs by workflow and step
   - Add config metadata (workflow ID, step ID, generation timestamp)
   - Implement config merging strategy (preserve manual configs)
   - Add config backup before generation
   - Acceptance criteria: Configs are well-organized; manual configs preserved; backups created

7. **Story 9.7: Advanced Features & Optimization** ✅
   - Add config deduplication (avoid duplicate agents)
   - Optimize watch paths (minimize file system monitoring)
   - Add config caching for performance
   - Support multiple workflows running simultaneously
   - Acceptance criteria: Configs are optimized; no duplicates; performance is acceptable

## Execution Notes

### Prerequisites
- Epic 6 complete (YAML schema enforcement ensures reliable parsing)
- Understanding of Cursor Background Agents configuration format
- Access to workflow YAML files and Background Agent config file

### Technical Decisions Required
- Config organization strategy (by workflow, by step, flat)
- Watch path pattern format and optimization
- Natural language trigger patterns
- Config merging strategy (overwrite vs. merge with manual configs)

### Risk Mitigation
- **Primary Risk**: Breaking existing Background Agent configurations
- **Mitigation**: Backup existing configs, validation before write, preserve manual configs, test with Cursor
- **Rollback Plan**: Keep backups of original configs; can revert to manual configuration if needed

## Definition of Done

- [x] Enhanced `BackgroundAgentGenerator` implemented and tested
- [x] Watch paths correctly derived from step artifacts
- [x] Natural language triggers generated accurately
- [x] Workflow lifecycle integration works correctly
- [x] Config validation ensures all generated configs are valid
- [x] Config management preserves manual configs
- [x] Advanced features implemented and optimized
- [x] Test suite covers all generation scenarios
- [x] Documentation on config generation and usage
- [x] Generated configs tested with Cursor Background Agents

## Status: ✅ COMPLETE

**Completed:** 2025-01-XX  
**Implementation:** `tapps_agents/workflow/background_agent_generator.py`  
**Integration:** `tapps_agents/workflow/executor.py`  
**Tests:** `tests/unit/workflow/test_background_agent_generator.py`

### Implementation Summary

- Enhanced `BackgroundAgentGenerator` generates configs for all workflow steps
- Watch paths extracted from `requires` and `creates` artifacts with normalization
- Natural language triggers generated from step metadata and agent actions
- Automatic config generation on workflow start, cleanup on completion/failure
- Config validation ensures all generated configs are valid
- Manual configs preserved during merge operations
- Config backups created before modifications
- Full test suite with comprehensive coverage
- Integrated seamlessly with workflow execution lifecycle

