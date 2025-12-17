# Epic 3: Dynamic Tech Stack Templates

## Epic Goal

Generate project-specific configuration templates based on detected technology stack, reducing setup time by 80%+ and ensuring consistency across projects. This complements expert prioritization and provides zero-config setup experience.

## Epic Description

### Existing System Context

- **Current relevant functionality**: TappsCodingAgents has tech stack detection, project initialization (`init_project()`), and static configuration templates. Tech stack detection identifies frameworks and libraries
- **Technology stack**: Python 3.13+, YAML templates, tech stack detection system
- **Integration points**: 
  - Tech stack detection (`tapps_agents/core/init_project.py`)
  - Project initialization flow
  - Configuration file generation
  - Template system

### Enhancement Details

- **What's being added/changed**: 
  - Create `templates/tech_stacks/` directory with stack-specific templates
  - Templates for: FastAPI, Django, Next.js, React, Express, NestJS, Flask, etc.
  - Auto-merge stack templates with default config during `init_project()`
  - Include in templates: agent thresholds, Context7 cache pre-population, expert priorities, test framework defaults
  - Template variable expansion for project-specific values
  - Template selection logic based on detected stack

- **How it integrates**: 
  - During `init_project()`, detect tech stack and select appropriate template
  - Merge template with default configuration
  - Apply template values to project config
  - Works with existing init flow
  - Complements Epic 2 (Expert Prioritization)

- **Success criteria**: 
  - FastAPI projects get FastAPI-specific config automatically
  - Next.js projects get Next.js-specific settings
  - Templates include agent thresholds, Context7 pre-pop, expert priorities
  - Template merging works correctly
  - Setup time reduced significantly

## Stories

1. **Story 3.1: Tech Stack Template Structure**
   - Create `templates/tech_stacks/` directory
   - Define template file format (YAML) with sections: agent_config, context7_prepop, expert_priorities, test_frameworks
   - Create template for FastAPI (example/reference)
   - Create template for Next.js (example/reference)
   - Acceptance criteria: Directory structure created, template format defined, 2+ example templates created

2. **Story 3.2: Template Selection Logic**
   - Implement template selection based on detected tech stack
   - Create mapping: detected frameworks → template files
   - Handle multiple framework detection (select best match or merge)
   - Add fallback to default template if no match
   - Acceptance criteria: Template selection works for detected stacks, multiple frameworks handled, fallback works

3. **Story 3.3: Template Merging System**
   - Implement template merge logic (stack template + default config)
   - Handle nested configuration merging
   - Support template variable expansion ({{project.name}}, etc.)
   - Preserve user overrides
   - Acceptance criteria: Templates merge correctly, variables expand, user overrides preserved

4. **Story 3.4: Init Integration**
   - Integrate template system into `init_project()` flow
   - Auto-select and apply template during initialization
   - Generate project config with template values
   - Acceptance criteria: Templates applied during init, config generated correctly, init flow enhanced

5. **Story 3.5: Additional Stack Templates & Documentation**
   - Create templates for Django, React, Express, NestJS, Flask
   - Document template format and creation process
   - Add examples of template customization
   - Acceptance criteria: 5+ stack templates created, documentation complete, examples provided

## Compatibility Requirements

- [ ] Existing `init_project()` continues to work without templates
- [ ] Default configuration remains as fallback
- [ ] Template application is optional
- [ ] No breaking changes to existing config format
- [ ] User can override template values

## Risk Mitigation

- **Primary Risk**: Template selection may choose wrong template
  - **Mitigation**: Clear mapping rules, user can override, fallback to default
- **Primary Risk**: Template merging may overwrite user config
  - **Mitigation**: User overrides take precedence, merge logic preserves existing values
- **Primary Risk**: Templates may become outdated
  - **Mitigation**: Version tracking, update mechanism, documentation of template maintenance
- **Rollback Plan**: 
  - Remove template application to revert to default config
  - Feature flag to disable template system
  - Templates are additive, not required

## Definition of Done

- [ ] All stories completed with acceptance criteria met
- [ ] Tech stack template directory structure created
- [ ] Template selection works for detected stacks
- [ ] Template merging correctly applies stack-specific config
- [ ] Templates integrated into init_project() flow
- [ ] 5+ stack templates created (FastAPI, Next.js, Django, React, Express)
- [ ] Comprehensive test coverage
- [ ] Documentation complete (template guide, creation process, examples)
- [ ] No regression in existing init_project() functionality
- [ ] Setup time reduced (measured)

## Implementation Status

**Last Updated:** 2025-12-16

**Overall Status:** ✅ Completed - All stories implemented and ready for review

**Story Status:**
- Story 3.1 (Template Structure): ✅ Ready for Review - Template directory, format, FastAPI/Next.js templates created
- Story 3.2 (Selection Logic): ✅ Ready for Review - Template selection with mapping, priority, fallback implemented
- Story 3.3 (Merging System): ✅ Ready for Review - Deep merge, variable expansion, user override preservation implemented
- Story 3.4 (Init Integration): ✅ Ready for Review - Template system integrated into init_project() flow with CLI output
- Story 3.5 (Additional Templates): ✅ Ready for Review - Django, React, Express, NestJS, Flask templates created, documentation enhanced

**Implementation Summary:**
- Created `templates/tech_stacks/` directory with 7 templates (FastAPI, Next.js, Django, React, Express, NestJS, Flask)
- Implemented `template_selector.py` module for framework-to-template mapping and selection
- Implemented `template_merger.py` module for deep merging and variable expansion
- Integrated template system into `init_project()` with automatic selection and application
- Enhanced CLI output to show template application status
- Created comprehensive README with examples, troubleshooting, and best practices

**Notes:**
- All templates follow consistent format with agent_config, context7_prepop, expert_priorities, test_frameworks sections
- Template system is backward compatible - init works without templates
- User config overrides are preserved (highest priority in merge order)
- Template selection handles single and multiple framework detection with priority-based selection

