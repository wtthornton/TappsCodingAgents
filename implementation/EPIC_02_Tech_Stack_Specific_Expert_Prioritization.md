# Epic 2: Tech Stack-Specific Expert Prioritization

## Epic Goal

Automatically prioritize built-in experts based on detected project technology stack, improving expert selection quality, reducing token usage, and ensuring more relevant guidance for developers. This directly improves agent decision quality by leveraging existing expert system infrastructure.

## Epic Description

### Existing System Context

- **Current relevant functionality**: TappsCodingAgents has expert registry (`tapps_agents/experts/expert_registry.py`), tech stack detection (`tapps_agents/core/init_project.py::detect_tech_stack`), and built-in experts with domain matching
- **Technology stack**: Python 3.13+, existing expert registry, tech stack detection system
- **Integration points**: 
  - Expert registry (`tapps_agents/experts/expert_registry.py`)
  - Tech stack detection (`tapps_agents/core/init_project.py`)
  - Project profile system (`.tapps-agents/project-profile.yaml`)
  - Expert consultation in agent workflows

### Enhancement Details

- **What's being added/changed**: 
  - Extend `detect_tech_stack()` to map frameworks → expert priority mappings
  - Create tech stack → expert priority configuration system
  - Auto-configure expert registry during `init_project()` with stack-specific priorities
  - Add priority override configuration in `.tapps-agents/tech-stack.yaml`
  - Implement priority-based expert selection in expert registry
  - Create default priority mappings for common stacks (FastAPI, Django, React, Next.js, etc.)

- **How it integrates**: 
  - Tech stack detection runs during `init_project()` and persists to config
  - Expert registry reads tech stack config and applies priorities
  - Expert consultation uses prioritized expert list
  - Priority mappings are configurable and override-able
  - Works with existing domain-based expert matching

- **Success criteria**: 
  - Tech stack detection maps to expert priorities
  - Expert registry applies priorities during consultation
  - FastAPI projects prioritize API Design and Observability experts
  - React projects prioritize Frontend and UX experts
  - Priority overrides work correctly
  - Token usage reduced through better expert selection

## Stories

1. **Story 2.1: Tech Stack to Expert Priority Mapping**
   - Create mapping structure for frameworks → expert priorities
   - Define default priority mappings for common stacks (FastAPI: API Design=1.0, Observability=0.9, Performance=0.8)
   - Implement priority mapping lookup function
   - Add priority configuration format (YAML)
   - Acceptance criteria: Mapping structure defined, default priorities for 5+ common stacks, lookup function works correctly

2. **Story 2.2: Tech Stack Config Persistence**
   - Extend tech stack detection to include expert priorities
   - Persist tech stack + priorities to `.tapps-agents/tech-stack.yaml`
   - Add priority override capability in config file
   - Acceptance criteria: Tech stack config includes priorities, config persists correctly, overrides work

3. **Story 2.3: Expert Registry Priority Integration**
   - Extend expert registry to read and apply tech stack priorities
   - Modify `_get_experts_for_domain()` to consider priorities
   - Implement priority-based expert ordering in consultation
   - Maintain backward compatibility (works without priorities)
   - Acceptance criteria: Expert registry applies priorities, expert ordering reflects priorities, backward compatible

4. **Story 2.4: Priority Configuration During Init**
   - Auto-configure expert priorities during `init_project()`
   - Load tech stack config and apply to expert registry
   - Support manual priority configuration
   - Acceptance criteria: Priorities auto-configured during init, manual config works, expert registry updated

5. **Story 2.5: Testing & Documentation**
   - Add unit tests for priority mapping and application
   - Test priority overrides
   - Document priority configuration format
   - Create examples for common tech stacks
   - Acceptance criteria: Comprehensive test coverage, documentation complete, examples provided

## Compatibility Requirements

- [ ] Existing expert consultation continues to work without priorities
- [ ] Domain-based expert matching still works
- [ ] Expert registry API remains backward compatible
- [ ] Tech stack detection remains unchanged (only extended)
- [ ] No breaking changes to existing expert system

## Risk Mitigation

- **Primary Risk**: Priority mappings may be incorrect for some projects
  - **Mitigation**: Configurable overrides, default mappings based on common patterns, user can adjust
- **Primary Risk**: Priority system may exclude relevant experts
  - **Mitigation**: Priorities are weights, not filters - all experts still available, just reordered
- **Primary Risk**: Tech stack detection may miss frameworks
  - **Mitigation**: Extensible mapping system, fallback to default priorities, manual configuration available
- **Rollback Plan**: 
  - Remove priority config to revert to default behavior
  - Feature flag to disable priority-based selection
  - Maintain backward compatibility

## Definition of Done

- [x] All stories completed with acceptance criteria met
- [x] Tech stack detection maps to expert priorities
- [x] Expert registry applies priorities during consultation
- [x] Priority configuration persists to tech-stack.yaml
- [x] Priority overrides work correctly
- [x] Default priorities defined for 5+ common tech stacks (FastAPI, Django, React, Next.js, NestJS)
- [x] Comprehensive test coverage (46 tests total: 22 unit mapping, 10 config, 9 registry, 5 integration)
- [x] Documentation complete (priority config guide, examples)
- [x] No regression in existing expert consultation (fully backward compatible)
- [ ] Token usage reduced through better expert selection (measured) - Requires runtime measurement

## Implementation Status

**Last Updated:** 2025-01-27

**Overall Status:** ✅ Completed

**Story Status:**
- Story 2.1 (Priority Mapping): ✅ Ready for Review - Implementation complete with tests
- Story 2.2 (Config Persistence): ✅ Ready for Review - Implementation complete with tests
- Story 2.3 (Registry Integration): ✅ Ready for Review - Implementation complete with tests
- Story 2.4 (Init Integration): ✅ Ready for Review - Integration complete
- Story 2.5 (Testing & Docs): ✅ Ready for Review - Comprehensive tests and documentation complete

**Notes:**
- Existing expert registry has domain-based matching that can be extended
- Tech stack detection exists and can be extended with priority mappings
- Priority system should be additive (weights) not filtering (all experts still available)

