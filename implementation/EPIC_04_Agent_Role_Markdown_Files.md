# Epic 4: Agent Role Markdown Files

## Epic Goal

Separate agent role definitions into dedicated markdown files, making agent behaviors transparent, customizable, and easier to understand. This enables team-specific agent personalities and better documentation, supporting Cursor Skills integration.

## Epic Description

### Existing System Context

- **Current relevant functionality**: TappsCodingAgents has agent definitions in `.claude/skills/` (SKILL.md files) with personas embedded. BMAD uses markdown agent files (`.bmad-core/agents/*.md`)
- **Technology stack**: Python 3.13+, Markdown files, YAML frontmatter, existing agent system
- **Integration points**: 
  - Existing agent definitions in `.claude/skills/`
  - Agent initialization system
  - Cursor Skills integration
  - BMAD pattern reference

### Enhancement Details

- **What's being added/changed**: 
  - Create `templates/agent_roles/` directory structure
  - Define agent role markdown file format with: Identity, Principles, Communication Style, Expertise Areas, Interaction Patterns
  - Create role files for all built-in agents (analyst, architect, implementer, reviewer, etc.)
  - Implement role file loader that reads during agent initialization
  - Support role file customization via customization layer (Epic 1)
  - Integrate with Cursor Skills system

- **How it integrates**: 
  - Role files loaded during agent activation
  - Role definitions override or extend base agent personas
  - Works with customization layer (Epic 1) for team-specific overrides
  - Cursor Skills can reference role files
  - Maintains backward compatibility with existing SKILL.md files

- **Success criteria**: 
  - Role files define agent identity, principles, communication style
  - All built-in agents have role files
  - Role files load during agent initialization
  - Customization layer can override role files
  - Cursor Skills integration enhanced
  - Documentation improved

## Stories

1. **Story 4.1: Agent Role File Format & Structure**
   - Define markdown role file format with sections: Identity, Principles, Communication Style, Expertise Areas, Interaction Patterns
   - Create role file template with examples
   - Define YAML frontmatter structure (metadata)
   - Acceptance criteria: Role file format defined, template created, structure documented

2. **Story 4.2: Role File Directory & Organization**
   - Create `templates/agent_roles/` directory
   - Organize role files by agent type
   - Create role files for core agents: analyst, architect, implementer, reviewer, tester
   - Acceptance criteria: Directory structure created, 5+ role files created, organization clear

3. **Story 4.3: Role File Loader Implementation**
   - Implement role file loader that reads markdown files
   - Parse YAML frontmatter and markdown content
   - Integrate loader into agent initialization
   - Support role file lookup by agent ID
   - Acceptance criteria: Loader reads and parses role files, integrates with agent init, lookup works

4. **Story 4.4: Agent Initialization Integration**
   - Modify agent activation to load role files
   - Apply role definitions to agent persona
   - Support role file customization (via Epic 1 customization layer)
   - Maintain backward compatibility
   - Acceptance criteria: Role files load during activation, personas applied, customization works, backward compatible

5. **Story 4.5: Additional Role Files & Documentation**
   - Create role files for remaining agents (designer, documenter, planner, etc.)
   - Document role file format and creation process
   - Create examples of role customization
   - Update Cursor Skills documentation
   - Acceptance criteria: All agents have role files, documentation complete, examples provided

## Compatibility Requirements

- [ ] Existing SKILL.md files continue to work
- [ ] Agent initialization backward compatible
- [ ] Role files are optional (agents work without them)
- [ ] Cursor Skills integration maintained
- [ ] No breaking changes to agent APIs

## Risk Mitigation

- **Primary Risk**: Role files may conflict with existing SKILL.md definitions
  - **Mitigation**: Clear precedence rules (role files override SKILL.md), migration path, backward compatibility
- **Primary Risk**: Role file format may be too rigid
  - **Mitigation**: Extensible format, customization layer allows overrides, flexible structure
- **Primary Risk**: Maintaining role files may be overhead
  - **Mitigation**: Role files are optional, can be generated from existing definitions, team-specific
- **Rollback Plan**: 
  - Remove role file loading to revert to SKILL.md
  - Feature flag to disable role files
  - Role files are additive, not required

## Definition of Done

- [ ] All stories completed with acceptance criteria met
- [ ] Agent role file format defined and documented
- [ ] Role file directory structure created
- [ ] Role file loader implemented and integrated
- [ ] All built-in agents have role files
- [ ] Role files load during agent initialization
- [ ] Customization layer can override role files
- [ ] Comprehensive test coverage
- [ ] Documentation complete (role file guide, examples, migration notes)
- [ ] No regression in existing agent functionality
- [ ] Cursor Skills integration enhanced

## Implementation Status

**Last Updated:** 2025-01-XX

**Overall Status:** ✅ Complete - All stories completed and ready for review

**Story Status:**
- ✅ Story 32.1 (File Format): Ready for Review - Role file format defined, template and example created
- ✅ Story 32.2 (Directory Structure): Ready for Review - Directory created, 8 role files created (5 core + 3 additional)
- ✅ Story 32.3 (Role Loader): Ready for Review - Role file loader implemented with error handling
- ✅ Story 32.4 (Init Integration): Ready for Review - Integrated into agent activation flow
- ✅ Story 32.5 (Additional Roles): Ready for Review - Additional role files created, documentation complete

**Implementation Summary:**
- Created standardized role file format with YAML frontmatter and markdown sections
- Implemented role file loader (`tapps_agents/core/role_loader.py`)
- Integrated loader into agent activation (`tapps_agents/core/agent_base.py`)
- Created 8 role files: analyst, architect, implementer, reviewer, tester, designer, documenter, planner
- Documented format in `docs/AGENT_ROLE_FILE_FORMAT.md`
- Created template file for easy role file creation
- All role files follow consistent structure and format

**Files Created/Modified:**
- `templates/agent_roles/` directory (new)
- `templates/agent_roles/ROLE_FILE_TEMPLATE.md` (new)
- `templates/agent_roles/*-role.md` (8 role files, new)
- `templates/agent_roles/README.md` (new)
- `docs/AGENT_ROLE_FILE_FORMAT.md` (new)
- `tapps_agents/core/role_loader.py` (new)
- `tapps_agents/core/agent_base.py` (modified)

**Notes:**
- BMAD pattern exists in `.bmad-core/agents/*.md` and was used as reference
- Existing SKILL.md files continue to work (backward compatible)
- Role files complement customization layer (Epic 1)
- Role files are optional - agents work without them
- Precedence: base (SKILL.md) → role file → customization layer

