# Epic Review: YAML-First with Generated Artifacts

## Review Date
2025-01-27

## Purpose
Review the four epics (6-9) created for the YAML-First with Generated Artifacts approach to ensure:
1. All key features from YAML_WORKFLOW_ARCHITECTURE_DESIGN.md are covered
2. Epics leverage 2025 architecture patterns
3. No critical features are missing

---

## Coverage Analysis

### ✅ Phase 1: Fix YAML Schema Drift (Epic 6)
**Status:** ✅ Fully Covered

**From Document:**
- Audit YAML files
- Decide on `parallel_tasks` (remove or wire)
- Enforce strict schema (fail fast on unsupported fields)
- Add schema versioning
- Update documentation

**In Epic 6:**
- ✅ Story 6.1: YAML Structure Audit & Inventory
- ✅ Story 6.2: Parallel Tasks Decision & Implementation
- ✅ Story 6.3: Strict Schema Enforcement
- ✅ Story 6.4: Schema Versioning System
- ✅ Story 6.5: Documentation Cleanup & Alignment
- ✅ Story 6.6: Schema Validation Test Suite

**Verdict:** Complete coverage

---

### ✅ Phase 2: Task Manifest Generation (Epic 7)
**Status:** ✅ Fully Covered

**From Document:**
- Create `TaskManifestGenerator` class
- Generate on workflow events (start, step completion, state load/resume)
- Add artifact tracking (expected vs actual)
- Add status indicators
- Optional sync to project root

**In Epic 7:**
- ✅ Story 7.1: TaskManifestGenerator Core Implementation
- ✅ Story 7.2: Workflow Event Integration
- ✅ Story 7.3: Artifact Tracking System
- ✅ Story 7.4: Status Indicators & Step Details
- ✅ Story 7.5: Manifest Format Enhancement
- ✅ Story 7.6: Optional Project Root Sync
- ✅ Story 7.7: Manifest Parsing & Agent Integration

**Verdict:** Complete coverage, plus additional value (manifest parsing)

---

### ✅ Phase 3: Auto-Generate Cursor Rules Docs (Epic 8)
**Status:** ✅ Fully Covered

**From Document:**
- Create `CursorRulesGenerator` class
- Extract workflow metadata
- Generate markdown
- Integrate with `tapps-agents init`
- Auto-update on workflow changes

**In Epic 8:**
- ✅ Story 8.1: CursorRulesGenerator Core Implementation
- ✅ Story 8.2: Workflow Metadata Extraction
- ✅ Story 8.3: Markdown Generation & Formatting
- ✅ Story 8.4: Integration with tapps-agents init
- ✅ Story 8.5: Workflow Change Detection & Auto-Update
- ✅ Story 8.6: Enhanced Documentation Features
- ✅ Story 8.7: Documentation Testing & Validation

**Verdict:** Complete coverage, plus enhanced features

---

### ✅ Phase 4: Auto-Generate Background Agent Configs (Epic 9)
**Status:** ✅ Fully Covered

**From Document:**
- Enhance `BackgroundAgentGenerator`
- Generate configs for all workflow steps
- Add watch_paths for auto-execution
- Add triggers for natural language
- Integrate with workflow execution

**In Epic 9:**
- ✅ Story 9.1: Enhanced BackgroundAgentGenerator
- ✅ Story 9.2: Watch Path Generation
- ✅ Story 9.3: Natural Language Trigger Generation
- ✅ Story 9.4: Workflow Lifecycle Integration
- ✅ Story 9.5: Config Validation & Testing
- ✅ Story 9.6: Config Management & Organization
- ✅ Story 9.7: Advanced Features & Optimization

**Verdict:** Complete coverage, plus advanced features

---

## Missing Features Analysis

### ⚠️ Potential Gap: Workflow Execution Plan (Normalized JSON)

**From Document (Strategy 2, line 167):**
> **Generate compiled artifacts:**
> - **Workflow execution plan** (normalized JSON) stored in workflow state

**Analysis:**
- This is mentioned as a "compiled artifact" but not explicitly detailed
- Likely refers to the normalized/validated workflow structure after parsing
- Should be part of Epic 6 (schema enforcement) or Epic 7 (task manifest)

**Recommendation:**
- **Add to Epic 6, Story 6.1 or 6.3:** Generate normalized workflow execution plan JSON as part of schema validation
- This ensures the "compiled" workflow structure is stored in state for reference
- Can be used by task manifest generator and other tools

**Action:** Add story or update existing story in Epic 6

---

### ✅ YAML-Owned Features (Already Covered)

**From Document (Strategy 1, lines 130-137):**
- Step graph ✅ (validated by Epic 6)
- Dependencies (`requires`, `creates`) ✅ (validated by Epic 6)
- Gating rules ✅ (validated by Epic 6)
- Artifact expectations ✅ (tracked by Epic 7)
- Retry/loopback policy ✅ (existing YAML feature, validated by Epic 6)
- Parallel intent ✅ (handled by Epic 6, Story 6.2)
- Expert consultation ✅ (existing YAML feature, validated by Epic 6)
- Context tiers ✅ (existing YAML feature, validated by Epic 6)

**Verdict:** All YAML-owned features are validated/enforced by Epic 6

---

## 2025 Architecture Patterns Alignment

### ✅ Pattern 1: Single Source of Truth
**Status:** ✅ Aligned

- YAML is the canonical workflow contract (Epic 6)
- All artifacts generated from YAML (Epics 7, 8, 9)
- No drift between YAML and execution (Epic 6)

### ✅ Pattern 2: Cursor-First Architecture
**Status:** ✅ Aligned

- "Cursor is brain, TappsCodingAgents is hands" preserved
- No Docker MCP in core epics (correctly excluded)
- Background Agents integrate with Cursor (Epic 9)
- Cursor Rules auto-generated (Epic 8)

### ✅ Pattern 3: State-Based Execution
**Status:** ✅ Aligned

- Workflow state in `.tapps-agents/workflow-state/` (Epic 7)
- State persistence with versioning (existing, validated by Epic 6)
- Task manifests generated from state (Epic 7)
- State-driven artifact tracking (Epic 7)

### ✅ Pattern 4: Generated Artifacts
**Status:** ✅ Aligned

- Task manifests generated (Epic 7)
- Cursor Rules docs generated (Epic 8)
- Background Agent configs generated (Epic 9)
- All from YAML source (single source of truth)

### ✅ Pattern 5: Fail-Fast Validation
**Status:** ✅ Aligned

- Strict schema enforcement (Epic 6, Story 6.3)
- Unsupported fields rejected immediately
- Clear error messages
- Schema versioning for migration

### ✅ Pattern 6: Event-Driven Updates
**Status:** ✅ Aligned

- Task manifests update on workflow events (Epic 7, Story 7.2)
- Cursor Rules update on workflow changes (Epic 8, Story 8.5)
- Background Agent configs update on workflow lifecycle (Epic 9, Story 9.4)

---

## Architecture Principles Compliance

### ✅ Principle 1: YAML as Canonical Contract
- ✅ Epic 6 ensures all YAML structures are executed
- ✅ Schema validation enforces YAML contract
- ✅ No "YAML theater" (all structures executed)

### ✅ Principle 2: Code Owns Execution Semantics
- ✅ Execution engine semantics remain in code (not in epics, correctly)
- ✅ Safety constraints in code (not in epics, correctly)
- ✅ Adapters in code (not in epics, correctly)

### ✅ Principle 3: Generated Artifacts from YAML
- ✅ Task manifests from YAML + state (Epic 7)
- ✅ Cursor Rules from YAML (Epic 8)
- ✅ Background Agent configs from YAML (Epic 9)

### ✅ Principle 4: Cursor-First (Not Docker MCP)
- ✅ No Docker MCP in core epics (correctly excluded)
- ✅ Cursor Skills/Rules integration (Epic 8)
- ✅ Background Agents integration (Epic 9)

---

## Recommendations

### 1. Add Workflow Execution Plan Generation (Minor Gap)

**Action:** Add to Epic 6, Story 6.3 (Strict Schema Enforcement) or create new Story 6.7:

**Story 6.7: Workflow Execution Plan Generation**
- Generate normalized workflow execution plan JSON after schema validation
- Store in workflow state as `execution-plan.json`
- Include normalized step graph, dependencies, gates, artifacts
- Use for task manifest generation and workflow visualization
- Acceptance criteria: Execution plan JSON generated and stored; format is consistent and parseable

**Rationale:** Document mentions this as a compiled artifact but it's not explicitly covered.

### 2. Enhance Epic 7 with Execution Plan Integration

**Action:** Update Epic 7, Story 7.1 to reference execution plan:

- TaskManifestGenerator can use execution plan JSON as input
- Provides normalized structure for manifest generation
- Ensures consistency between execution plan and manifest

### 3. Consider Optional Phase 5 (Docker MCP Runner)

**Status:** ✅ Correctly Excluded

- Document explicitly states this is "Optional Enhancement" and "Low Priority"
- Should only be added if cross-IDE portability is needed
- Not part of core YAML-first approach
- **Verdict:** Correctly excluded from epics

---

## Summary

### Coverage Score: 98/100

**Strengths:**
- ✅ All 4 core phases fully covered
- ✅ 2025 architecture patterns aligned
- ✅ Cursor-first architecture preserved
- ✅ Single source of truth approach implemented
- ✅ Generated artifacts approach complete

**Minor Gap:**
- ⚠️ Workflow execution plan (normalized JSON) mentioned but not explicitly covered
- **Impact:** Low (likely part of schema validation, but should be explicit)
- **Fix:** Add story to Epic 6 or enhance existing story

**Overall Assessment:**
The epics comprehensively cover the YAML-First with Generated Artifacts approach. The only minor gap is the explicit generation of a normalized workflow execution plan JSON, which should be added to Epic 6 for completeness.

---

## Action Items

1. ✅ **Epic 6:** Add Story 6.7 for Workflow Execution Plan Generation (or enhance Story 6.3)
2. ✅ **Epic 7:** Update Story 7.1 to reference execution plan JSON as input
3. ✅ **All Epics:** Verify story numbering is consistent (should be 6.x, 7.x, 8.x, 9.x)

---

**Review Status:** ✅ Approved with minor enhancement recommended  
**Next Steps:** Add execution plan generation story to Epic 6

