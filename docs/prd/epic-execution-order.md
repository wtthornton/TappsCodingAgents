# Epic Execution Order: YAML-First with Generated Artifacts

## Execution Sequence

### Phase 1: Foundation (CRITICAL PATH - Must Complete First)

**Epic 6: YAML Schema Enforcement & Drift Resolution**
- **Timeline:** 1-2 weeks
- **Priority:** Critical
- **Dependencies:** None (foundational)
- **Why First:** 
  - Establishes YAML as single source of truth
  - Ensures reliable parsing for all subsequent epics
  - Fixes "YAML theater" issue
  - Provides schema versioning foundation

**Must Complete Before:**
- ✅ Epic 7 (needs reliable YAML parsing)
- ✅ Epic 8 (needs reliable YAML parsing)
- ✅ Epic 9 (needs reliable YAML parsing)

---

### Phase 2: Artifact Generation (Can Run in Parallel)

After Epic 6 is complete, Epics 7, 8, and 9 can run **in parallel** because they:
- Generate different artifacts from the same YAML source
- Don't depend on each other
- Only depend on Epic 6 (reliable YAML parsing)

#### Option A: Parallel Execution (Recommended)

**Run simultaneously after Epic 6:**
- **Epic 7:** Task Manifest Generation (1-2 weeks)
- **Epic 8:** Automated Documentation Generation (1 week)
- **Epic 9:** Background Agent Config Auto-Generation (1 week)

**Total Phase 2 Time:** 1-2 weeks (longest epic determines duration)

#### Option B: Sequential Execution (If Resources Limited)

**Run one at a time after Epic 6:**
1. **Epic 7:** Task Manifest Generation (1-2 weeks)
2. **Epic 8:** Automated Documentation Generation (1 week)
3. **Epic 9:** Background Agent Config Auto-Generation (1 week)

**Total Phase 2 Time:** 3-4 weeks

---

## Visual Execution Order

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Foundation (CRITICAL PATH)                     │
│                                                          │
│  Epic 6: YAML Schema Enforcement                        │
│  ⏱️  1-2 weeks                                          │
│  📋 Must complete before Phase 2                        │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ (Epic 6 Complete)
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Phase 2:      │    │ Phase 2:      │    │ Phase 2:      │
│ Artifact Gen  │    │ Artifact Gen  │    │ Artifact Gen  │
│               │    │               │    │               │
│ Epic 7:       │    │ Epic 8:       │    │ Epic 9:       │
│ Task Manifest │    │ Documentation │    │ Background    │
│               │    │               │    │ Agents        │
│ ⏱️  1-2 weeks │    │ ⏱️  1 week    │    │ ⏱️  1 week    │
│               │    │               │    │               │
│ ✅ Can run    │    │ ✅ Can run    │    │ ✅ Can run    │
│    parallel   │    │    parallel   │    │    parallel   │
└───────────────┘    └───────────────┘    └───────────────┘
```

---

## Detailed Execution Plan

### Week 1-2: Epic 6 (Foundation)

**Stories (Sequential):**
1. Story 6.1: YAML Structure Audit & Inventory
2. Story 6.2: Parallel Tasks Decision & Implementation
3. Story 6.3: Strict Schema Enforcement
4. Story 6.4: Schema Versioning System
5. Story 6.5: Documentation Cleanup & Alignment
6. Story 6.6: Schema Validation Test Suite
7. Story 6.7: Workflow Execution Plan Generation

**Deliverables:**
- ✅ All YAML structures executed (no "YAML theater")
- ✅ Schema validation fails fast on unsupported fields
- ✅ Schema versioning with migration support
- ✅ Normalized execution plan JSON generation

**Gate:** Epic 6 must be complete before starting Phase 2

---

### Week 3-4: Epics 7, 8, 9 (Parallel Execution)

#### Epic 7: Task Manifest Generation

**Stories (Can parallelize within epic):**
- Story 7.1: TaskManifestGenerator Core Implementation
- Story 7.2: Workflow Event Integration
- Story 7.3: Artifact Tracking System
- Story 7.4: Status Indicators & Step Details
- Story 7.5: Manifest Format Enhancement
- Story 7.6: Optional Project Root Sync
- Story 7.7: Manifest Parsing & Agent Integration

**Deliverables:**
- ✅ TaskManifestGenerator class
- ✅ Auto-updating task manifests
- ✅ Artifact tracking
- ✅ Status indicators

#### Epic 8: Automated Documentation Generation

**Stories (Can parallelize within epic):**
- Story 8.1: CursorRulesGenerator Core Implementation
- Story 8.2: Workflow Metadata Extraction
- Story 8.3: Markdown Generation & Formatting
- Story 8.4: Integration with tapps-agents init
- Story 8.5: Workflow Change Detection & Auto-Update
- Story 8.6: Enhanced Documentation Features
- Story 8.7: Documentation Testing & Validation

**Deliverables:**
- ✅ CursorRulesGenerator class
- ✅ Auto-generated Cursor Rules docs
- ✅ Auto-update on workflow changes

#### Epic 9: Background Agent Config Auto-Generation

**Stories (Can parallelize within epic):**
- Story 9.1: Enhanced BackgroundAgentGenerator
- Story 9.2: Watch Path Generation
- Story 9.3: Natural Language Trigger Generation
- Story 9.4: Workflow Lifecycle Integration
- Story 9.5: Config Validation & Testing
- Story 9.6: Config Management & Organization
- Story 9.7: Advanced Features & Optimization

**Deliverables:**
- ✅ Enhanced BackgroundAgentGenerator
- ✅ Auto-generated Background Agent configs
- ✅ Workflow lifecycle integration

---

## Timeline Summary

### Option A: Parallel Execution (Recommended)

| Phase | Epics | Duration | Total Time |
|-------|-------|----------|------------|
| Phase 1 | Epic 6 | 1-2 weeks | 1-2 weeks |
| Phase 2 | Epics 7, 8, 9 (parallel) | 1-2 weeks | 1-2 weeks |
| **Total** | | | **2-4 weeks** |

### Option B: Sequential Execution

| Phase | Epics | Duration | Total Time |
|-------|-------|----------|------------|
| Phase 1 | Epic 6 | 1-2 weeks | 1-2 weeks |
| Phase 2 | Epic 7 | 1-2 weeks | 1-2 weeks |
| Phase 2 | Epic 8 | 1 week | 1 week |
| Phase 2 | Epic 9 | 1 week | 1 week |
| **Total** | | | **4-6 weeks** |

**Recommendation:** Use Option A (parallel execution) to minimize total time.

---

## Dependency Matrix

| Epic | Depends On | Blocks | Can Run With |
|------|------------|--------|--------------|
| Epic 6 | None | Epics 7, 8, 9 | None (foundational) |
| Epic 7 | Epic 6 | None | Epics 8, 9 |
| Epic 8 | Epic 6 | None | Epics 7, 9 |
| Epic 9 | Epic 6 | None | Epics 7, 8 |

---

## Critical Path

**Epic 6 is the critical path** - it must complete before any other epic can start.

**Total minimum time:** 2 weeks (Epic 6: 1 week + Phase 2 parallel: 1 week)  
**Total maximum time:** 4 weeks (Epic 6: 2 weeks + Phase 2 parallel: 2 weeks)

---

## Execution Recommendations

### 1. Start with Epic 6
- **Why:** Foundation for all other work
- **Risk:** Breaking existing workflows
- **Mitigation:** Comprehensive testing, schema versioning, backward compatibility

### 2. Run Phase 2 in Parallel
- **Why:** Epics 7, 8, 9 are independent
- **Benefit:** Reduces total time from 4-6 weeks to 2-4 weeks
- **Requirement:** Need 3 developers/teams or sequential execution

### 3. Integration Testing After Phase 2
- **Why:** Ensure all generators work together
- **When:** After all Phase 2 epics complete
- **Focus:** End-to-end workflow execution, artifact validation

---

## Success Criteria by Phase

### Phase 1 Success (Epic 6)
- ✅ All YAML structures executed
- ✅ Schema validation fails fast
- ✅ Schema versioning works
- ✅ Execution plan JSON generated

### Phase 2 Success (Epics 7-9)
- ✅ Task manifests sync with state
- ✅ Cursor Rules docs auto-generated
- ✅ Background Agent configs auto-generated
- ✅ All artifacts stay in sync with YAML

---

**Last Updated:** 2025-01-27  
**Status:** Ready for Execution

