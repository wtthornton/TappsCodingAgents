# Epic 6: User Role Templates for Different Team Roles

## Epic Goal

Create role-specific agent interaction templates that customize agent behavior based on user role (senior developer, junior developer, tech lead, product manager, QA engineer), significantly improving UX for non-developers and reducing confusion about agent capabilities.

## Epic Description

### Existing System Context

- **Current relevant functionality**: TappsCodingAgents has one-size-fits-all agent configuration. Agent personas are consistent regardless of user role. No role-specific customization exists
- **Technology stack**: Python 3.13+, YAML configuration, agent system, customization layer (Epic 1)
- **Integration points**: 
  - Agent customization layer (Epic 1)
  - Agent initialization system
  - Project configuration
  - User preferences

### Enhancement Details

- **What's being added/changed**: 
  - Create `templates/user_roles/` directory structure
  - Define user role template format with: verbosity, workflow defaults, expert priorities, documentation preferences, review depth
  - Create templates for: senior-developer, junior-developer, tech-lead, product-manager, qa-engineer
  - Implement role template loader and application
  - Add role selection during project initialization or via config
  - Integrate with agent customization system

- **How it integrates**: 
  - Role templates applied during agent initialization
  - Works with customization layer (Epic 1) - role templates are base, customizations override
  - Role selection during `init_project()` or via config file
  - Agent behaviors adapt to user role
  - Complements Cursor's role-based features

- **Success criteria**: 
  - PM role gets verbose Analyst/Planner, business-focused Architect
  - QA role gets test-first emphasis, edge case focus
  - Junior developer gets learning-focused, detailed explanations
  - Senior developer gets concise, assumption of expertise
  - Tech lead gets architecture-focused, strategic thinking
  - Role templates improve UX for non-developers

## Stories

1. **Story 6.1: User Role Template Format & Structure**
   - Define user role template format (YAML) with sections: verbosity, workflow_defaults, expert_priorities, documentation_preferences, review_depth
   - Create template structure with examples
   - Define role metadata (role_id, description, use_cases)
   - Acceptance criteria: Template format defined, structure created, examples provided

2. **Story 6.2: Core User Role Templates**
   - Create `templates/user_roles/` directory
   - Create templates for: senior-developer, junior-developer, tech-lead
   - Define role-specific agent configurations
   - Acceptance criteria: Directory created, 3+ role templates created, configurations defined

3. **Story 6.3: Additional Role Templates**
   - Create templates for: product-manager, qa-engineer
   - Define PM-specific configurations (verbose Analyst, business context)
   - Define QA-specific configurations (test-first, edge cases)
   - Acceptance criteria: 2+ additional templates created, role-specific configs defined

4. **Story 6.4: Role Template Loader & Application**
   - Implement role template loader
   - Create role application logic (merge with agent config)
   - Add role selection during `init_project()`
   - Support role selection via config file
   - Acceptance criteria: Loader implemented, application logic works, selection integrated

5. **Story 6.5: Integration & Documentation**
   - Integrate role templates with agent customization system
   - Test role template application across agents
   - Document role templates and selection process
   - Create examples of role-specific behaviors
   - Acceptance criteria: Integration complete, testing done, documentation complete

## Compatibility Requirements

- [ ] Existing agent behavior continues without role templates
- [ ] Role templates are optional (backward compatible)
- [ ] Users can override role templates via customization
- [ ] No breaking changes to agent APIs
- [ ] Default behavior maintained for users without role selection

## Risk Mitigation

- **Primary Risk**: Role templates may be too prescriptive
  - **Mitigation**: Templates are defaults, fully customizable, user can override
- **Primary Risk**: Role selection may be confusing
  - **Mitigation**: Clear role descriptions, examples, default to generic if unsure
- **Primary Risk**: Maintaining role templates may be overhead
  - **Mitigation**: Templates are optional, can be community-maintained, simple structure
- **Rollback Plan**: 
  - Remove role template application to revert to defaults
  - Feature flag to disable role templates
  - Role templates are additive, not required

## Definition of Done

- [ ] All stories completed with acceptance criteria met
- [ ] User role template format defined and documented
- [ ] Role template directory structure created
- [ ] 5+ user role templates created (senior-dev, junior-dev, tech-lead, PM, QA)
- [ ] Role template loader implemented
- [ ] Role selection integrated into init_project()
- [ ] Role templates applied to agent behaviors
- [ ] Comprehensive test coverage
- [ ] Documentation complete (role template guide, examples, selection process)
- [ ] No regression in existing agent functionality
- [ ] UX improved for non-developers (measured)

## Implementation Status

**Last Updated:** 2025-01-XX

**Overall Status:** Ready for Review - All stories completed

**Story Status:**
- Story 34.1 (Template Format): Ready for Review - Format defined, documentation and example template created
- Story 34.2 (Core Templates): Ready for Review - Senior-dev, junior-dev, tech-lead templates created
- Story 34.3 (Additional Templates): Ready for Review - PM and QA templates created
- Story 34.4 (Loader & Application): Ready for Review - Loader implemented, integrated into agent_base.py
- Story 34.5 (Integration): Ready for Review - Documentation complete, integration verified

**Notes:**
- Role templates complement customization layer (Epic 1)
- Templates provide sensible defaults that can be customized
- Aligns with Cursor's role-based features for consistency
- All 5 role templates created and documented
- Loader supports project and framework templates
- Config file support for role selection implemented
- Comprehensive guide created with examples and troubleshooting

