# Epic 8: Automated Documentation Generation

## Epic Goal

Keep Cursor Rules documentation automatically synchronized with workflow YAML by generating documentation from workflow definitions. This eliminates documentation drift and ensures that Cursor Rules accurately reflect available workflows, their steps, quality gates, and usage guidelines.

## Epic Description

### Existing System Context

- **Current relevant functionality**:
  - Workflow YAML files in `workflows/presets/*.yaml` define workflows (full-sdlc, rapid-dev, maintenance, quality, quick-fix)
  - Cursor Rules in `.cursor/rules/workflow-presets.mdc` manually document workflows
  - `tapps-agents init` command installs Cursor Rules/Skills
  - Workflow metadata exists in YAML (name, description, version, steps, gates)
  - Documentation can drift from YAML definitions
- **Technology stack**: Python 3.13+, YAML parsing, markdown generation, Cursor Rules format
- **Integration points**:
  - `tapps_agents/workflow/parser.py` (WorkflowParser - YAML parsing)
  - `tapps_agents/core/init_project.py` (project initialization)
  - `.cursor/rules/workflow-presets.mdc` (Cursor Rules documentation)
  - `workflows/presets/*.yaml` (workflow definitions)
  - `docs/YAML_WORKFLOW_ARCHITECTURE_DESIGN.md` (architecture reference)

### Enhancement Details

- **What's being added/changed**:
  - `CursorRulesGenerator` class that generates `.cursor/rules/workflow-presets.mdc` from workflow YAML
  - Automatic extraction of workflow metadata (name, description, version, step sequence, quality gates, when to use)
  - Markdown generation with workflow descriptions, step sequences, usage examples, quality gate thresholds
  - Integration with `tapps-agents init` to generate rules on initialization
  - Auto-update rules when workflows change (detection and regeneration)
  - Documentation generation from schema definitions (single source of truth)
- **How it integrates**:
  - `CursorRulesGenerator` reads all workflow YAML files
  - Extracts metadata and generates markdown documentation
  - Writes to `.cursor/rules/workflow-presets.mdc`
  - `tapps-agents init` invokes generator during initialization
  - Workflow changes trigger regeneration (manual or automatic)
- **Success criteria**:
  - Cursor Rules docs are auto-generated from YAML (no manual maintenance)
  - Documentation accurately reflects all workflow features
  - Rules generation is integrated with project initialization
  - Documentation updates automatically when workflows change
  - Generated docs are readable and well-formatted

## Stories

1. **Story 8.1: CursorRulesGenerator Core Implementation**
   - Create `CursorRulesGenerator` class in `tapps_agents/workflow/rules_generator.py`
   - Implement YAML parsing to extract workflow metadata
   - Design markdown template for Cursor Rules format
   - Generate basic workflow documentation (name, description, steps)
   - Acceptance criteria: Generator creates valid Cursor Rules markdown; format matches existing `.mdc` structure

2. **Story 8.2: Workflow Metadata Extraction**
   - Extract workflow name, description, version from YAML
   - Extract step sequence with agent, action, dependencies
   - Extract quality gates and thresholds
   - Extract "when to use" guidance from workflow metadata
   - Acceptance criteria: All workflow metadata correctly extracted; extraction handles all workflow types

3. **Story 8.3: Markdown Generation & Formatting**
   - Generate workflow descriptions section
   - Generate step sequences with details
   - Generate usage examples and guidance
   - Generate quality gate thresholds and requirements
   - Format markdown with proper headings, lists, code blocks
   - Acceptance criteria: Generated markdown is well-formatted and readable; all sections populated correctly

4. **Story 8.4: Integration with tapps-agents init**
   - Integrate `CursorRulesGenerator` into `tapps-agents init` workflow
   - Generate rules during project initialization
   - Handle existing rules files (backup, merge, or overwrite strategy)
   - Add configuration option for rules generation
   - Acceptance criteria: Rules generated automatically on init; existing rules handled gracefully

5. **Story 8.5: Workflow Change Detection & Auto-Update**
   - Detect when workflow YAML files change
   - Trigger rules regeneration on workflow changes
   - Add manual regeneration command (`tapps-agents generate-rules`)
   - Add validation to ensure generated rules are valid
   - Acceptance criteria: Rules update when workflows change; manual regeneration works; validation catches errors

6. **Story 8.6: Enhanced Documentation Features**
   - Add workflow comparison table (features, use cases, complexity)
   - Add workflow selection guidance
   - Add step-by-step execution examples
   - Add troubleshooting section for common issues
   - Acceptance criteria: Enhanced documentation provides comprehensive guidance; examples are accurate and helpful

7. **Story 8.7: Documentation Testing & Validation**
   - Create test suite for rules generation
   - Validate generated markdown syntax
   - Test with all workflow types (full-sdlc, rapid-dev, maintenance, quality, quick-fix)
   - Test edge cases (empty workflows, missing metadata)
   - Acceptance criteria: All tests pass; generated docs are valid; edge cases handled

## Execution Notes

### Prerequisites
- Epic 6 complete (YAML schema enforcement ensures reliable parsing)
- Understanding of Cursor Rules markdown format
- Access to all workflow YAML files

### Technical Decisions Required
- Markdown template structure and format
- Rules file update strategy (overwrite vs. merge)
- Change detection mechanism (file watching vs. manual trigger)
- Documentation style and tone

### Risk Mitigation
- **Primary Risk**: Breaking existing Cursor Rules or losing customizations
- **Mitigation**: Backup existing rules, validation before overwrite, option to preserve custom sections
- **Rollback Plan**: Keep backups of original rules; can revert to manual documentation if needed

## Definition of Done

- [x] `CursorRulesGenerator` class implemented and tested
- [x] Workflow metadata extraction works for all workflow types
- [x] Generated markdown is well-formatted and comprehensive
- [x] Integration with `tapps-agents init` works correctly
- [x] Workflow changes trigger rules regeneration (via `tapps-agents generate-rules` command)
- [x] Enhanced documentation features implemented
- [x] Test suite covers all generation scenarios
- [x] Documentation on rules generation process (via CLI help and code documentation)
- [x] Generated rules validated and tested with Cursor

## Status: ✅ COMPLETE

**Completion Date:** 2025-01-XX

**Implementation Summary:**
- Created `CursorRulesGenerator` class in `tapps_agents/workflow/rules_generator.py`
- Integrated automatic generation into `tapps-agents init` workflow
- Added `tapps-agents generate-rules` command for manual regeneration
- Implemented comprehensive test suite (7 unit tests, all passing)
- Generated documentation matches existing format and includes all workflow metadata
- Supports both project and framework resource workflows
- Includes backup functionality for existing rules files

