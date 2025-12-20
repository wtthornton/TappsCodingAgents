# YAML-First with Generated Artifacts - Epic Summary

## Overview

This document summarizes the four epics created to implement the **Primary Recommendation: YAML-First with Generated Artifacts** approach from the YAML Workflow Architecture Design document. These epics transform TappsCodingAgents to make YAML the single source of truth for workflow definitions, with all derived artifacts automatically generated.

## Epic Structure

### Epic 6: YAML Schema Enforcement & Drift Resolution
**Priority:** Critical  
**Timeline:** 1-2 weeks  
**Goal:** Eliminate "YAML theater" by ensuring all YAML structures are executed and enforcing strict schema validation.

**Key Stories:**
- YAML Structure Audit & Inventory
- Parallel Tasks Decision & Implementation
- Strict Schema Enforcement
- Schema Versioning System
- Documentation Cleanup & Alignment
- Schema Validation Test Suite

**Deliverables:**
- Updated `WorkflowParser` with strict validation
- Updated `WorkflowExecutor` (if implementing `parallel_tasks`)
- Schema versioning with migration support
- Comprehensive test suite

---

### Epic 7: Task Manifest Generation System
**Priority:** High Value  
**Timeline:** 1-2 weeks  
**Goal:** Generate human-readable task checklists from workflow YAML + state for TODO-driven execution.

**Key Stories:**
- TaskManifestGenerator Core Implementation
- Workflow Event Integration
- Artifact Tracking System
- Status Indicators & Step Details
- Manifest Format Enhancement
- Optional Project Root Sync
- Manifest Parsing & Agent Integration

**Deliverables:**
- `TaskManifestGenerator` class
- Task manifest files in workflow state directory
- Optional sync to project root
- Manifest parsing utilities

---

### Epic 8: Automated Documentation Generation
**Priority:** Medium Value  
**Timeline:** 1 week  
**Goal:** Keep Cursor Rules documentation automatically synchronized with workflow YAML.

**Key Stories:**
- CursorRulesGenerator Core Implementation
- Workflow Metadata Extraction
- Markdown Generation & Formatting
- Integration with tapps-agents init
- Workflow Change Detection & Auto-Update
- Enhanced Documentation Features
- Documentation Testing & Validation

**Deliverables:**
- `CursorRulesGenerator` class
- Auto-generated `.cursor/rules/workflow-presets.mdc`
- Integration with project initialization
- Change detection and auto-update

---

### Epic 9: Background Agent Config Auto-Generation
**Priority:** Medium Value  
**Timeline:** 1 week  
**Goal:** Automatically generate Background Agent configurations from workflow steps.

**Key Stories:**
- Enhanced BackgroundAgentGenerator
- Watch Path Generation
- Natural Language Trigger Generation
- Workflow Lifecycle Integration
- Config Validation & Testing
- Config Management & Organization
- Advanced Features & Optimization

**Deliverables:**
- Enhanced `BackgroundAgentGenerator`
- Auto-generated `.cursor/background-agents.yaml` entries
- Workflow lifecycle integration
- Config validation and testing

---

## Epic Dependencies

```
Epic 6 (Schema Enforcement)
  ↓
Epic 7 (Task Manifest) ──┐
Epic 8 (Documentation) ──┤ (Can run in parallel after Epic 6)
Epic 9 (Background Agents) ──┘
```

**Dependency Rationale:**
- **Epic 6 is foundational** - All other epics depend on reliable YAML parsing and schema enforcement
- **Epics 7, 8, and 9 can run in parallel** - They generate different artifacts from the same YAML source
- **All epics share the same YAML source** - Ensuring schema consistency (Epic 6) is critical

## Implementation Strategy

### Phase 1: Foundation (Epic 6)
1. Complete Epic 6 to establish YAML as authoritative source
2. Ensure all YAML structures are executed
3. Implement strict schema validation
4. Establish schema versioning

### Phase 2: Artifact Generation (Epics 7-9)
1. Run Epics 7, 8, and 9 in parallel (after Epic 6 complete)
2. Generate task manifests (Epic 7)
3. Generate Cursor Rules docs (Epic 8)
4. Generate Background Agent configs (Epic 9)

### Phase 3: Integration & Testing
1. Integrate all generators with workflow lifecycle
2. Test end-to-end workflow execution
3. Validate generated artifacts
4. Update documentation

## Success Criteria

### Overall Success
- ✅ YAML is the single source of truth for workflows
- ✅ All YAML structures are executed (no "YAML theater")
- ✅ Task manifests are always in sync with workflow state
- ✅ Cursor Rules docs are auto-generated from YAML
- ✅ Background Agent configs are auto-generated from workflows
- ✅ Zero drift between YAML definitions and generated artifacts

### Epic-Specific Success
- **Epic 6:** Schema validation fails fast on unsupported fields; all structures executed
- **Epic 7:** Task manifests accurately reflect workflow state; auto-update on events
- **Epic 8:** Cursor Rules docs match workflow YAML; auto-update on changes
- **Epic 9:** Background Agent configs align with workflows; lifecycle integration works

## Risk Mitigation

### Common Risks
1. **Breaking existing workflows** - Mitigated by schema versioning and comprehensive testing
2. **Artifact drift** - Mitigated by automatic generation and validation
3. **Performance impact** - Mitigated by efficient generation and caching
4. **User confusion** - Mitigated by clear documentation and migration guides

### Epic-Specific Risks
- **Epic 6:** Breaking existing workflows → Schema versioning, backward compatibility
- **Epic 7:** Manifest drift → Automatic generation, validation checks
- **Epic 8:** Breaking Cursor Rules → Backup existing rules, validation
- **Epic 9:** Breaking Background Agents → Backup configs, validation, testing

## Timeline Estimate

- **Epic 6:** 1-2 weeks (Critical, must complete first)
- **Epic 7:** 1-2 weeks (Can run in parallel with 8-9 after Epic 6)
- **Epic 8:** 1 week (Can run in parallel with 7-9 after Epic 6)
- **Epic 9:** 1 week (Can run in parallel with 7-8 after Epic 6)

**Total Timeline:** 3-4 weeks (with Epic 6 as critical path, then parallel execution)

## Next Steps

1. **Review and approve epics** - Validate epic goals and stories align with architecture vision
2. **Prioritize Epic 6** - Begin with schema enforcement as foundation
3. **Plan parallel execution** - Schedule Epics 7-9 to run after Epic 6
4. **Set up tracking** - Create stories from epics and track progress
5. **Begin implementation** - Start with Epic 6, Schema Enforcement

## Related Documents

- `docs/YAML_WORKFLOW_ARCHITECTURE_DESIGN.md` - Architecture design document
- `docs/prd/epic-6-yaml-schema-enforcement.md` - Epic 6 details
- `docs/prd/epic-7-task-manifest-generation.md` - Epic 7 details
- `docs/prd/epic-8-automated-documentation-generation.md` - Epic 8 details
- `docs/prd/epic-9-background-agent-auto-generation.md` - Epic 9 details

---

**Status:** Epics Created  
**Last Updated:** 2025-01-27  
**Next Review:** After Epic approval and story creation

