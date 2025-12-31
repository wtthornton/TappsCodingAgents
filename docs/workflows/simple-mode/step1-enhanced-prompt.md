# Step 1: Enhanced Prompt - Automatic Documentation Updates for Framework Changes

## Original Prompt

Implement automatic documentation updates for framework changes in TappsCodingAgents build workflow. This addresses the critical gap identified in the Evaluator Agent Documentation Gap Analysis where new agents are created but project documentation (README.md, API.md, ARCHITECTURE.md, agent-capabilities.mdc) is not automatically updated.

## Enhanced Requirements Analysis

### Problem Statement

When a new agent is created using `@simple-mode *build`, the following occurs:
- ✅ Agent code is created correctly
- ✅ CLI integration works
- ✅ Configuration system integration works
- ❌ **CRITICAL GAP**: Project documentation files are NOT automatically updated
  - README.md still shows old agent count
  - API.md doesn't list the new agent
  - ARCHITECTURE.md doesn't include the new agent
  - agent-capabilities.mdc is missing the new agent section

### Root Causes Identified

1. **Documenter agent not in build workflow sequence** - Current sequence: `["enhancer", "planner", "architect", "designer", "implementer"]` - missing `"documenter"`
2. **No framework change detection** - Build workflow doesn't detect when new agents are added
3. **No documentation completeness validation** - No check that all docs are updated consistently
4. **Workflow designed for features, not framework changes** - Framework changes need special handling

### Requirements

#### Functional Requirements

1. **Framework Change Detection**
   - Detect when new agent directory is created in `tapps_agents/agents/`
   - Detect when agent is registered in CLI (`tapps_agents/cli/main.py`)
   - Detect when agent skill is created in `tapps_agents/resources/claude/skills/`
   - Identify which agent was added/modified

2. **Automatic Documentation Updates**
   - Update README.md:
     - Increment agent count
     - Add agent to agent list
     - Update agent descriptions if needed
   - Update API.md:
     - Add agent to subcommands list
     - Add agent API documentation section
   - Update ARCHITECTURE.md:
     - Add agent to agent list
     - Update architecture diagrams if applicable
   - Update agent-capabilities.mdc:
     - Add agent section with purpose and commands

3. **Documentation Completeness Validation**
   - Verify README.md mentions the new agent
   - Verify API.md documents the new agent
   - Verify ARCHITECTURE.md includes the new agent
   - Verify agent-capabilities.mdc has agent section
   - Verify agent count is consistent across all docs
   - Fail workflow if critical documentation is missing

4. **Integration with Build Workflow**
   - Add `documenter` as Step 8 in build workflow
   - Run documentation updates after implementation step
   - Only run for framework changes (detect automatically)
   - Provide clear feedback on what was updated

#### Non-Functional Requirements

1. **Performance**
   - Documentation updates should be fast (< 5 seconds)
   - Use file parsing instead of full LLM calls where possible
   - Cache agent lists to avoid repeated scans

2. **Reliability**
   - Validate file paths before updating
   - Create backups before modifying files
   - Handle missing files gracefully
   - Provide rollback capability

3. **Maintainability**
   - Use template-based updates for consistency
   - Document update patterns clearly
   - Make it easy to add new documentation files

4. **Windows Compatibility**
   - Handle Windows path separators correctly
   - Use UTF-8 encoding for all file operations
   - Test on Windows environment

### Architecture Guidance

#### Component Design

1. **Framework Change Detector**
   - Location: `tapps_agents/simple_mode/framework_change_detector.py`
   - Responsibilities:
     - Scan `tapps_agents/agents/` for new directories
     - Parse CLI registration files for new commands
     - Compare current state with known state
     - Return list of detected changes

2. **Documentation Updater**
   - Location: `tapps_agents/agents/documenter/framework_doc_updater.py`
   - Responsibilities:
     - Update README.md with new agent info
     - Update API.md with agent documentation
     - Update ARCHITECTURE.md with agent details
     - Update agent-capabilities.mdc with agent section
     - Use templates for consistent formatting

3. **Documentation Validator**
   - Location: `tapps_agents/agents/documenter/doc_validator.py`
   - Responsibilities:
     - Validate all docs mention new agent
     - Check agent count consistency
     - Verify documentation completeness
     - Generate validation report

4. **Build Orchestrator Integration**
   - Location: `tapps_agents/simple_mode/orchestrators/build_orchestrator.py`
   - Changes:
     - Add `documenter` to agent sequence
     - Add framework change detection after implementation
     - Call documentation updater if framework changes detected
     - Run validation after updates

#### Data Flow

```
Build Workflow Execution
  ↓
Step 5: Implementation (creates agent code)
  ↓
Framework Change Detection (detects new agent)
  ↓
Step 8: Documenter (if framework change detected)
  ├─→ Update README.md
  ├─→ Update API.md
  ├─→ Update ARCHITECTURE.md
  └─→ Update agent-capabilities.mdc
  ↓
Documentation Validation
  ├─→ Check all docs updated
  ├─→ Verify agent count consistency
  └─→ Generate validation report
  ↓
Workflow Complete
```

### Quality Standards

1. **Code Quality**
   - Type hints for all functions
   - Comprehensive error handling
   - Unit tests for all components
   - Integration tests for full workflow

2. **Documentation Quality**
   - Clear docstrings for all functions
   - Examples in documentation
   - Update patterns documented
   - Error messages are clear

3. **Testing Requirements**
   - Unit tests for change detection
   - Unit tests for documentation updates
   - Unit tests for validation
   - Integration test: Full workflow with mock agent creation

### Implementation Strategy

#### Phase 1: Framework Change Detection
1. Create `FrameworkChangeDetector` class
2. Implement agent directory scanning
3. Implement CLI registration parsing
4. Add detection to build orchestrator

#### Phase 2: Documentation Updates
1. Create `FrameworkDocUpdater` class
2. Implement README.md update logic
3. Implement API.md update logic
4. Implement ARCHITECTURE.md update logic
5. Implement agent-capabilities.mdc update logic

#### Phase 3: Validation
1. Create `DocValidator` class
2. Implement completeness checks
3. Implement consistency checks
4. Add validation to build workflow

#### Phase 4: Integration
1. Add documenter to build workflow sequence
2. Integrate change detection
3. Integrate documentation updates
4. Integrate validation
5. Test full workflow

### Success Criteria

1. ✅ New agent creation automatically updates all project documentation
2. ✅ Documentation validation catches missing updates
3. ✅ Build workflow fails gracefully if documentation incomplete
4. ✅ All documentation files stay in sync
5. ✅ Agent counts are consistent across all docs
6. ✅ No manual intervention required for documentation updates

### Dependencies

- Existing documenter agent (`tapps_agents/agents/documenter/`)
- Build orchestrator (`tapps_agents/simple_mode/orchestrators/build_orchestrator.py`)
- Project documentation files (README.md, docs/API.md, docs/ARCHITECTURE.md, .cursor/rules/agent-capabilities.mdc)

### Risks and Mitigations

1. **Risk**: File parsing might break with format changes
   - **Mitigation**: Use robust parsing with fallbacks, test with various formats

2. **Risk**: Updates might overwrite user customizations
   - **Mitigation**: Use targeted updates (insert after specific markers), create backups

3. **Risk**: Performance impact on build workflow
   - **Mitigation**: Only run for framework changes, use efficient file operations

4. **Risk**: False positives in change detection
   - **Mitigation**: Use multiple detection methods, validate before updating
