# Epic 1: Update-Safe Agent Customization Layer

## Epic Goal

Implement BMAD-style customization files that persist through framework updates, enabling teams to customize agent behaviors without losing their configurations when the framework is updated. This foundation enables all other customization improvements and is critical for user adoption.

## Epic Description

### Existing System Context

- **Current relevant functionality**: TappsCodingAgents has agent definitions in `.claude/skills/` and agent implementations in `tapps_agents/agents/`. BMAD already implements this pattern in `.bmad-core/customizations/` directory
- **Technology stack**: Python 3.13+, YAML configuration, existing agent framework, file-based configuration system
- **Integration points**: 
  - Existing agent initialization in `tapps_agents/core/agent_base.py`
  - Current agent definitions in `.claude/skills/`
  - Project configuration in `.tapps-agents/` directory
  - BMAD pattern reference in `.bmad-core/customizations/`

### Enhancement Details

- **What's being added/changed**: 
  - Create `.tapps-agents/customizations/` directory structure
  - Implement customization file loader that merges base agent config with user customizations
  - Add customization file format (YAML) with persona_overrides, command_overrides, dependency_overrides
  - Implement update-safe merge logic (customizations override defaults, not replace)
  - Add validation for customization files
  - Create customization template generator
  - Add gitignore rules for customization files (optional version control)

- **How it integrates**: 
  - Customization loader runs during agent activation (before persona adoption)
  - Base agent definitions remain in framework (update-safe)
  - Customizations are project-specific and persist through updates
  - Works with existing agent initialization flow
  - Compatible with Cursor Skills system

- **Success criteria**: 
  - Customization files can override agent persona, commands, and dependencies
  - Customizations persist through framework updates
  - Base agent definitions remain untouched by customizations
  - Customization validation catches errors before agent activation
  - Template generator creates starter customization files
  - Gitignore properly excludes customization files by default

## Stories

1. **Story 1.1: Customization Directory Structure & File Format**
   - Create `.tapps-agents/customizations/` directory structure
   - Define YAML customization file format (agent_id, persona_overrides, command_overrides, dependency_overrides, project_context)
   - Create customization file schema/validation
   - Add customization file naming convention (`{agent-id}-custom.yaml`)
   - Acceptance criteria: Directory structure created, YAML schema defined and validated, naming convention documented

2. **Story 1.2: Customization Loader Implementation**
   - Implement customization file loader that checks for `{agent-id}-custom.yaml`
   - Create merge logic that applies customizations over base agent config
   - Add merge rules: persona additions/overrides, command additions/modifications, dependency additions
   - Implement error handling for missing/invalid customization files
   - Acceptance criteria: Loader finds and loads customization files, merge logic correctly applies overrides, errors handled gracefully

3. **Story 1.3: Agent Initialization Integration**
   - Integrate customization loader into agent activation flow
   - Ensure customizations load before persona adoption
   - Add customization validation before agent activation
   - Maintain backward compatibility (agents work without customizations)
   - Acceptance criteria: Customizations load during agent activation, validation catches errors, backward compatibility maintained

4. **Story 1.4: Customization Template Generator**
   - Create CLI command/tool to generate customization file templates
   - Generate templates with commented examples for common customizations
   - Support generating templates for all built-in agents
   - Acceptance criteria: Template generator creates valid customization files, examples are clear and helpful

5. **Story 1.5: Gitignore & Documentation**
   - Add `.tapps-agents/customizations/` to default gitignore patterns
   - Create customization guide documentation
   - Add examples of common customization patterns
   - Document how to share customizations with team (version control opt-in)
   - Acceptance criteria: Gitignore properly configured, documentation complete with examples

## Compatibility Requirements

- [ ] Existing agent initialization continues to work without customizations
- [ ] Base agent definitions remain unchanged and update-safe
- [ ] Customization files are optional (backward compatible)
- [ ] Cursor Skills integration continues to work
- [ ] No breaking changes to existing agent APIs

## Risk Mitigation

- **Primary Risk**: Customization merge logic may incorrectly override base config
  - **Mitigation**: Comprehensive testing of merge scenarios, clear merge rules documentation, validation before activation
- **Primary Risk**: Customization files may become incompatible after framework updates
  - **Mitigation**: Version validation, deprecation warnings, migration guide for breaking changes
- **Primary Risk**: Users may accidentally commit sensitive customizations
  - **Mitigation**: Gitignore by default, clear documentation about what to commit/share
- **Rollback Plan**: 
  - Remove customization files to revert to defaults
  - Feature flag to disable customization loading if issues arise
  - Maintain backward compatibility so agents work without customizations

## Definition of Done

- [ ] All stories completed with acceptance criteria met
- [ ] Customization directory structure created and documented
- [ ] Customization loader successfully merges base config with user customizations
- [ ] Agent initialization integrates customization loading
- [ ] Template generator creates valid customization files
- [ ] Gitignore properly configured
- [ ] Comprehensive test coverage for customization loading and merging
- [ ] Documentation complete (customization guide, examples, migration notes)
- [ ] No regression in existing agent functionality
- [ ] Example customization files demonstrate common patterns

## Implementation Status

**Last Updated:** 2025-01-27

**Overall Status:** Ready for Review - All stories completed

**Story Status:**
- Story 1.1 (Directory Structure): Ready for Review - Completed
- Story 1.2 (Customization Loader): Ready for Review - Completed
- Story 1.3 (Agent Integration): Ready for Review - Completed
- Story 1.4 (Template Generator): Ready for Review - Completed
- Story 1.5 (Gitignore & Docs): Ready for Review - Completed

**Implementation Summary:**
- Created `.tapps-agents/customizations/` directory structure
- Implemented YAML schema validation in `customization_schema.py`
- Implemented customization loader with merge logic in `customization_loader.py`
- Integrated loader into agent activation flow in `agent_base.py`
- Created CLI template generator command `customize init`
- Added gitignore pattern for customizations directory
- Created comprehensive documentation in `CUSTOMIZATION_GUIDE.md`

**Files Created/Modified:**
- `tapps_agents/core/customization_schema.py` - Schema validation
- `tapps_agents/core/customization_loader.py` - Loader and merge logic
- `tapps_agents/core/customization_template.py` - Template generator
- `tapps_agents/core/init_project.py` - Directory initialization and gitignore
- `tapps_agents/core/agent_base.py` - Integration with agent activation
- `tapps_agents/cli/parsers/top_level.py` - CLI parser
- `tapps_agents/cli/commands/top_level.py` - CLI handler
- `tapps_agents/cli/main.py` - Command routing
- `tapps_agents/resources/customizations/example-custom.yaml` - Example template
- `docs/CUSTOMIZATION_GUIDE.md` - Complete documentation

**Notes:**
- BMAD pattern from `.bmad-core/customizations/` used as reference
- Customization format follows BMAD pattern for consistency
- All customizations are backward compatible (agents work without customizations)
- Customizations are gitignored by default, opt-in to version control

