# AI Coding Tool Documentation Standards - Implementation Plan

**Date:** 2026-01-20  
**Status:** 📋 Planning Complete - Ready for Review  
**Priority:** High - Aligns with 2025+ AI coding tool standards

## Executive Summary

This implementation plan addresses 16 recommendations from the AI coding tool documentation standards review. The plan covers both **greenfield** (new project setup) and **brownfield** (existing project conversion) scenarios, ensuring TappsCodingAgents meets emerging 2025+ documentation standards for AI coding tools.

**Scope:**
- 6 High Priority items (critical missing files and ADR system)
- 7 Medium Priority items (AI comment tags, CI automation, documentation quality)
- 3 Low Priority items (migration, enhancements)

**Estimated Timeline:** 8-12 weeks (depending on team size and project priorities)

---

## Phase 1: Critical Missing Files (High Priority)

### 1.1: Create `test-stack.md` Documentation

**Priority:** P0 - Critical  
**Effort:** 4-6 hours  
**Dependencies:** None

#### Greenfield Approach
1. Create `docs/test-stack.md` from template
2. Define test types (unit, integration, e2e, contract, performance)
3. Document test infrastructure and CI integration
4. Set coverage thresholds and quality gates
5. Document mock/stub strategies

#### Brownfield Approach
1. Audit existing test documentation (scattered across docs/)
2. Consolidate testing information into unified `test-stack.md`
3. Identify gaps in current testing strategy
4. Update existing docs to reference `test-stack.md`
5. Migrate test-related content from other docs

**Acceptance Criteria:**
- ✅ `docs/test-stack.md` exists with complete testing strategy
- ✅ All test types defined with responsibilities
- ✅ CI integration documented
- ✅ Coverage thresholds specified
- ✅ Existing test docs updated to reference new file

**Files to Create/Modify:**
- `docs/test-stack.md` (new)
- `docs/README.md` (add reference)
- `CONTRIBUTING.md` (add testing section reference)

---

### 1.2: Create `AGENTS.md` File

**Priority:** P0 - Critical  
**Effort:** 2-3 hours  
**Dependencies:** None

#### Greenfield Approach
1. Create `AGENTS.md` at project root
2. Document agent identity and project-specific rules
3. Include agent capabilities overview
4. Add project-specific agent customizations
5. Reference `.cursor/rules/` for detailed rules

#### Brownfield Approach
1. Extract agent-related content from existing docs
2. Consolidate into `AGENTS.md`
3. Update `.cursor/rules/` to reference `AGENTS.md`
4. Ensure consistency with existing agent documentation
5. Add cross-references between `AGENTS.md` and Skills

**Acceptance Criteria:**
- ✅ `AGENTS.md` exists at project root
- ✅ Agent identity and rules documented
- ✅ References to `.cursor/rules/` included
- ✅ Compatible with tools outside Cursor

**Files to Create/Modify:**
- `AGENTS.md` (new)
- `.cursor/rules/agent-capabilities.mdc` (add reference)

---

### 1.3: Create `CLAUDE.md` Master Rule File

**Priority:** P0 - Critical  
**Effort:** 3-4 hours  
**Dependencies:** `.cursor/rules/` structure

#### Greenfield Approach
1. Create `CLAUDE.md` at project root
2. Import/reference `.cursor/rules/*.mdc` files
3. Add Claude Code-specific context
4. Document cross-tool compatibility
5. Include version and status metadata

#### Brownfield Approach
1. Review existing `.cursor/rules/` content
2. Create `CLAUDE.md` that references rules (avoid duplication)
3. Add any Claude Code-specific additions
4. Test compatibility with Claude Desktop
5. Update Cursor settings to include `CLAUDE.md` if needed

**Acceptance Criteria:**
- ✅ `CLAUDE.md` exists at project root
- ✅ References `.cursor/rules/` files (no duplication)
- ✅ Works with Claude Code and other tools
- ✅ Version metadata included

**Files to Create/Modify:**
- `CLAUDE.md` (new)
- `.cursor/rules/` (ensure compatible structure)

---

### 1.4: Create Architecture Shard Files

**Priority:** P0 - Critical  
**Effort:** 8-12 hours  
**Dependencies:** `docs/ARCHITECTURE.md` exists

#### Greenfield Approach
1. Create `docs/architecture/` directory
2. Extract content from `ARCHITECTURE.md` into shards:
   - `tech-stack.md` - Technology stack overview
   - `source-tree.md` - Source code organization
   - `coding-standards.md` - Coding conventions
   - `performance-guide.md` - Performance guidelines
   - `testing-strategy.md` - Testing approach (or link to test-stack.md)
3. Update `ARCHITECTURE.md` to reference shards
4. Ensure BMAD compatibility (already referenced in ARCHITECTURE.md)

#### Brownfield Approach
1. Review `docs/ARCHITECTURE.md` for shardable content
2. Create `docs/architecture/` directory
3. Extract and organize content into shard files
4. Update `ARCHITECTURE.md` to be an index pointing to shards
5. Verify BMAD configuration (`.bmad-core/core-config.yaml`) still works
6. Update any broken references

**Acceptance Criteria:**
- ✅ `docs/architecture/` directory exists
- ✅ All 5 shard files created with content
- ✅ `ARCHITECTURE.md` updated to reference shards
- ✅ BMAD configuration still functional
- ✅ No broken internal links

**Files to Create/Modify:**
- `docs/architecture/tech-stack.md` (new)
- `docs/architecture/source-tree.md` (new)
- `docs/architecture/coding-standards.md` (new)
- `docs/architecture/performance-guide.md` (new)
- `docs/architecture/testing-strategy.md` (new)
- `docs/ARCHITECTURE.md` (update to index format)
- `.bmad-core/core-config.yaml` (verify paths)

---

### 1.5: Create ADR System

**Priority:** P0 - Critical  
**Effort:** 6-8 hours  
**Dependencies:** None

#### Greenfield Approach
1. Create `docs/architecture/decisions/` directory
2. Create ADR template (`ADR-template.md`)
3. Document ADR numbering convention (ADR-001, ADR-002, etc.)
4. Create initial ADRs for major decisions:
   - ADR-001: Instruction-Based Architecture
   - ADR-002: Cursor-First Runtime Policy
   - ADR-003: Expert System Design
   - ADR-004: YAML-First Workflow Architecture

#### Brownfield Approach
1. Create `docs/architecture/decisions/` directory
2. Review existing documentation for major decisions
3. Extract decision rationale from:
   - `docs/HOW_IT_WORKS.md` (Cursor-first model)
   - `docs/ARCHITECTURE.md` (instruction-based, expert system)
   - `docs/YAML_WORKFLOW_ARCHITECTURE_DESIGN.md` (YAML-first)
4. Create ADRs retroactively for key decisions
5. Update existing docs to reference ADRs

**Acceptance Criteria:**
- ✅ `docs/architecture/decisions/` directory exists
- ✅ ADR template created
- ✅ At least 4 major decisions documented as ADRs
- ✅ ADR format includes: title, status, date, context, decision, consequences
- ✅ Existing docs reference relevant ADRs

**Files to Create/Modify:**
- `docs/architecture/decisions/ADR-template.md` (new)
- `docs/architecture/decisions/ADR-001-instruction-based-architecture.md` (new)
- `docs/architecture/decisions/ADR-002-cursor-first-runtime.md` (new)
- `docs/architecture/decisions/ADR-003-expert-system-design.md` (new)
- `docs/architecture/decisions/ADR-004-yaml-first-workflows.md` (new)
- `docs/ARCHITECTURE.md` (add ADR references)

---

### 1.6: Document Existing Major Decisions as ADRs

**Priority:** P0 - Critical  
**Effort:** 4-6 hours  
**Dependencies:** ADR system (1.5)

#### Greenfield Approach
N/A - Covered in 1.5

#### Brownfield Approach
1. Review codebase and documentation for additional decisions:
   - Simple Mode design decisions
   - Context7 integration approach
   - Quality gate thresholds
   - Workflow execution patterns
2. Create ADRs for each significant decision
3. Link ADRs from relevant documentation
4. Update decision logs in code comments to reference ADRs

**Acceptance Criteria:**
- ✅ All major architectural decisions have ADRs
- ✅ ADRs are linked from relevant documentation
- ✅ Code comments reference ADRs where appropriate

**Files to Create/Modify:**
- Additional ADR files as needed
- Update relevant documentation files

---

## Phase 2: AI-Focused Code Documentation (Medium Priority)

### 2.1: Add "Aitiquette" Headers to Critical Files

**Priority:** P1 - High  
**Effort:** 4-6 hours  
**Dependencies:** AI comment guidelines (2.3)

#### Greenfield Approach
1. Identify critical files (core agent base, workflow executor, simple mode handler)
2. Add Aitiquette headers to:
   - `tapps_agents/core/agent_base.py`
   - `tapps_agents/workflow/executor.py`
   - `tapps_agents/simple_mode/handler.py`
   - `tapps_agents/core/instructions.py`
3. Include: `@ai-prime-directive`, `@ai-current-task`, `@ai-constraints`

#### Brownfield Approach
1. Audit existing code for complex sections
2. Add Aitiquette headers to files with:
   - Complex logic that AI tools might modify incorrectly
   - Legacy code that must be preserved
   - Critical execution paths
3. Document why each section is marked
4. Update code review guidelines

**Acceptance Criteria:**
- ✅ At least 5 critical files have Aitiquette headers
- ✅ Headers include prime directive, constraints, current task context
- ✅ Headers are maintained and updated as code evolves

**Files to Create/Modify:**
- `tapps_agents/core/agent_base.py` (add header)
- `tapps_agents/workflow/executor.py` (add header)
- `tapps_agents/simple_mode/handler.py` (add header)
- `tapps_agents/core/instructions.py` (add header)
- Additional critical files as identified

---

### 2.2: Add AI Comment Tags to Complex Code Sections

**Priority:** P1 - High  
**Effort:** 6-8 hours  
**Dependencies:** AI comment guidelines (2.3)

#### Greenfield Approach
1. Identify complex code sections during development
2. Add appropriate tags:
   - `@note[date]:` for architectural decisions
   - `@ai-dont-touch:` for legacy/fragile code
   - `@hint:` for AI code generation guidance
3. Document tag usage in code review

#### Brownfield Approach
1. Review existing codebase for:
   - Complex algorithms
   - Workarounds for bugs
   - Performance optimizations
   - Legacy compatibility code
2. Add appropriate AI comment tags
3. Update existing comments to use standard tags
4. Create tag inventory

**Acceptance Criteria:**
- ✅ Complex sections tagged appropriately
- ✅ Tag usage is consistent across codebase
- ✅ Tags are maintained and updated

**Files to Create/Modify:**
- Multiple files across `tapps_agents/` as identified
- Focus on: workflow execution, instruction handling, expert system

---

### 2.3: Create AI Comment Tag Guidelines

**Priority:** P1 - High  
**Effort:** 2-3 hours  
**Dependencies:** None

#### Greenfield Approach
1. Create `docs/AI_COMMENT_GUIDELINES.md`
2. Document tag conventions:
   - `@note:` / `@note[date]:` - Permanent important context
   - `@hint:` - Temporary AI directives
   - `@ai-dont-touch:` - Guard sections
   - `@ai-prime-directive:` - File-level metadata
   - `@ai-current-task:` - Current development context
   - `@ai-constraints:` - Constraints and limitations
3. Provide examples for each tag type
4. Document when to use each tag

#### Brownfield Approach
1. Review existing comment patterns
2. Create guidelines that accommodate existing patterns
3. Provide migration guide for updating existing comments
4. Add to `CONTRIBUTING.md`

**Acceptance Criteria:**
- ✅ `docs/AI_COMMENT_GUIDELINES.md` exists
- ✅ All tag types documented with examples
- ✅ Guidelines added to `CONTRIBUTING.md`
- ✅ Examples provided for common scenarios

**Files to Create/Modify:**
- `docs/AI_COMMENT_GUIDELINES.md` (new)
- `CONTRIBUTING.md` (add reference)

---

## Phase 3: Documentation Quality & Automation (Medium Priority)

### 3.1: Integrate `verify_docs.py` into CI Pipeline

**Priority:** P1 - High  
**Effort:** 2-3 hours  
**Dependencies:** `scripts/verify_docs.py` exists

#### Greenfield Approach
1. Add documentation validation step to `.github/workflows/ci.yml`
2. Run `verify_docs.py` on PRs
3. Fail CI on broken internal links
4. Add documentation check summary to PR comments

#### Brownfield Approach
1. Test `verify_docs.py` on current codebase
2. Fix any existing broken links
3. Add CI step with appropriate exclusions
4. Configure failure thresholds (warn vs fail)

**Acceptance Criteria:**
- ✅ CI pipeline includes doc validation step
- ✅ Broken links cause CI failure (or warnings)
- ✅ PR comments show doc validation results
- ✅ Existing broken links fixed

**Files to Create/Modify:**
- `.github/workflows/ci.yml` (add doc validation job)
- `scripts/verify_docs.py` (may need updates for CI)

---

### 3.2: Add Documentation Metadata Standards

**Priority:** P1 - High  
**Effort:** 4-6 hours  
**Dependencies:** None

#### Greenfield Approach
1. Create metadata template for docs
2. Add YAML frontmatter to all new docs:
   - `version`, `status`, `last_updated`, `authors`, `tags`
3. Document metadata standards

#### Brownfield Approach
1. Audit existing docs for metadata
2. Add frontmatter to major docs:
   - `docs/ARCHITECTURE.md`
   - `docs/CONFIGURATION.md`
   - `docs/API.md`
   - All guide documents
3. Create migration script if needed
4. Update doc generation templates

**Acceptance Criteria:**
- ✅ Metadata template created
- ✅ All major docs have frontmatter
- ✅ Metadata standards documented
- ✅ Doc generation uses metadata template

**Files to Create/Modify:**
- `docs/` - Add frontmatter to major files
- `tapps_agents/core/document_generator.py` (update templates)
- `docs/DOCUMENTATION_METADATA_STANDARDS.md` (new)

---

### 3.3: Add Doc-Test Execution for Code Examples

**Priority:** P1 - High  
**Effort:** 6-8 hours  
**Dependencies:** None

#### Greenfield Approach
1. Set up doc-test framework
2. Add executable code examples to new docs
3. Configure CI to run doc-tests
4. Document example format

#### Brownfield Approach
1. Identify code examples in existing docs
2. Convert to executable format where possible
3. Add doc-test validation
4. Update examples that can't be executed

**Acceptance Criteria:**
- ✅ Doc-test framework configured
- ✅ Major docs have executable examples
- ✅ CI runs doc-tests
- ✅ Examples are validated

**Files to Create/Modify:**
- `.github/workflows/ci.yml` (add doc-test job)
- `docs/` - Update examples to executable format
- `scripts/run_doc_tests.py` (new, if needed)

---

### 3.4: Create Documentation Synchronization Checks

**Priority:** P1 - High  
**Effort:** 8-10 hours  
**Dependencies:** None

#### Greenfield Approach
1. Create sync check tool
2. Detect when code changes but docs don't
3. Check for outdated API references
4. Validate file path references

#### Brownfield Approach
1. Run initial sync check
2. Identify documentation drift
3. Create baseline
4. Set up automated checks

**Acceptance Criteria:**
- ✅ Sync check tool created
- ✅ Detects code/doc drift
- ✅ CI integration (optional, can be manual)
- ✅ Baseline established

**Files to Create/Modify:**
- `scripts/check_doc_sync.py` (new)
- `.github/workflows/ci.yml` (optional integration)

---

## Phase 4: MCP & Context Standards (Medium Priority)

### 4.1: Document MCP Standards Compliance

**Priority:** P1 - High  
**Effort:** 3-4 hours  
**Dependencies:** None

#### Greenfield Approach
1. Create `docs/MCP_STANDARDS.md`
2. Document JSON-RPC 2.0 usage
3. Document JSON Schema 2020-12 compliance
4. Document versioning strategy
5. Document library ID conventions

#### Brownfield Approach
1. Review existing MCP implementation
2. Document current compliance
3. Identify any gaps
4. Create compliance checklist

**Acceptance Criteria:**
- ✅ `docs/MCP_STANDARDS.md` exists
- ✅ All MCP standards documented
- ✅ Compliance verified
- ✅ Gaps identified (if any)

**Files to Create/Modify:**
- `docs/MCP_STANDARDS.md` (new)
- `.cursor/mcp.json` (verify compliance)

---

### 4.2: Document Context7 Integration Patterns

**Priority:** P1 - High  
**Effort:** 4-5 hours  
**Dependencies:** None

#### Greenfield Approach
1. Create `docs/CONTEXT7_PATTERNS.md`
2. Document best practices for Context7 usage
3. Document library ID resolution
4. Document cache management
5. Document performance optimization

#### Brownfield Approach
1. Review existing Context7 integration
2. Document current patterns
3. Extract lessons learned
4. Create best practices guide

**Acceptance Criteria:**
- ✅ `docs/CONTEXT7_PATTERNS.md` exists
- ✅ Best practices documented
- ✅ Examples provided
- ✅ Performance tips included

**Files to Create/Modify:**
- `docs/CONTEXT7_PATTERNS.md` (new)
- `docs/CONTEXT7_INTEGRATION_GUIDE.md` (update if exists)

---

## Phase 5: Legacy Migration & Enhancements (Low Priority)

### 5.1: Complete `.cursorrules` Migration

**Priority:** P2 - Medium  
**Effort:** 2-3 hours  
**Dependencies:** `.cursor/rules/` structure

#### Greenfield Approach
N/A - No legacy file

#### Brownfield Approach
1. Review `.cursorrules` content
2. Verify all content migrated to `.cursor/rules/*.mdc`
3. Add deprecation notice to `.cursorrules`
4. Update documentation to remove `.cursorrules` references
5. Plan removal after grace period

**Acceptance Criteria:**
- ✅ All `.cursorrules` content migrated
- ✅ Deprecation notice added
- ✅ Documentation updated
- ✅ Removal planned

**Files to Create/Modify:**
- `.cursorrules` (add deprecation notice)
- Documentation files (remove references)

---

### 5.2: Create/Enhance Requirements Documentation

**Priority:** P2 - Medium  
**Effort:** 2-3 hours  
**Dependencies:** None

#### Greenfield Approach
1. Create `requirements/PROJECT_REQUIREMENTS.md`
2. Link to other requirement docs
3. Create requirements index

#### Brownfield Approach
1. Review existing `requirements/` directory
2. Create/update `PROJECT_REQUIREMENTS.md` as index
3. Ensure all requirements are linked
4. Update documentation references

**Acceptance Criteria:**
- ✅ `requirements/PROJECT_REQUIREMENTS.md` exists
- ✅ Serves as requirements index
- ✅ All requirements linked

**Files to Create/Modify:**
- `requirements/PROJECT_REQUIREMENTS.md` (create or update)
- `docs/README.md` (add reference)

---

### 5.3: Enhance Documentation Index

**Priority:** P2 - Medium  
**Effort:** 2-3 hours  
**Dependencies:** None

#### Greenfield Approach
1. Enhance `docs/README.md`
2. Add quick navigation by topic
3. Add "new to project?" quick start paths
4. Add topic-based organization

#### Brownfield Approach
1. Review current `docs/README.md`
2. Add missing navigation
3. Organize by topic
4. Add quick start paths

**Acceptance Criteria:**
- ✅ `docs/README.md` enhanced
- ✅ Topic-based navigation added
- ✅ Quick start paths included

**Files to Create/Modify:**
- `docs/README.md` (enhance)

---

## Implementation Strategy

### Greenfield Projects (New Setup)

**Recommended Order:**
1. Phase 1 (Critical Files) - Weeks 1-2
2. Phase 2 (AI Comments) - Week 3
3. Phase 3 (Quality & Automation) - Weeks 4-5
4. Phase 4 (MCP Standards) - Week 6
5. Phase 5 (Enhancements) - Week 7

**Key Differences:**
- No migration needed
- Can establish standards from start
- Cleaner implementation
- Faster execution

### Brownfield Projects (Existing Conversion)

**Recommended Order:**
1. Phase 1.5 (ADR System) - Week 1 (establishes framework)
2. Phase 1.1-1.4 (Critical Files) - Weeks 2-3 (consolidate existing)
3. Phase 1.6 (Document Decisions) - Week 4 (retroactive ADRs)
4. Phase 2 (AI Comments) - Week 5 (add incrementally)
5. Phase 3 (Quality & Automation) - Weeks 6-7 (fix existing issues first)
6. Phase 4 (MCP Standards) - Week 8
7. Phase 5 (Migration & Enhancements) - Weeks 9-10

**Key Differences:**
- Migration and consolidation required
- Must preserve existing documentation
- Incremental approach recommended
- More testing needed

---

## Dependencies & Prerequisites

### Cross-Phase Dependencies
- Phase 1.5 (ADR System) should be done before 1.6
- Phase 2.3 (AI Guidelines) should be done before 2.1-2.2
- Phase 3.2 (Metadata Standards) helps with 3.3-3.4

### External Dependencies
- CI/CD access for Phase 3.1, 3.3, 3.4
- Documentation review process
- Team approval for standards

---

## Success Metrics

### Quantitative
- ✅ All 16 recommendations implemented
- ✅ 100% of critical files created
- ✅ 0 broken internal documentation links
- ✅ All major docs have metadata
- ✅ CI doc validation passing

### Qualitative
- ✅ Documentation is AI-friendly
- ✅ Standards are consistent
- ✅ Migration is smooth (brownfield)
- ✅ New projects can follow standards easily (greenfield)

---

## Risk Mitigation

### Risks
1. **Documentation drift** - Mitigated by CI validation (3.1, 3.4)
2. **Incomplete migration** - Mitigated by incremental approach and testing
3. **Standards not followed** - Mitigated by guidelines and examples
4. **Time constraints** - Prioritize Phase 1, defer Phase 5

### Rollback Plan
- Keep backups of existing documentation
- Version control all changes
- Can revert individual phases if needed

---

## Next Steps

1. **Review this plan** - Get stakeholder approval
2. **Prioritize phases** - Adjust based on project needs
3. **Assign owners** - Determine who implements each phase
4. **Set timeline** - Establish milestones and deadlines
5. **Begin Phase 1** - Start with critical files

---

## Appendix: File Inventory

### Files to Create (16 new files)
- `docs/test-stack.md`
- `AGENTS.md`
- `CLAUDE.md`
- `docs/architecture/tech-stack.md`
- `docs/architecture/source-tree.md`
- `docs/architecture/coding-standards.md`
- `docs/architecture/performance-guide.md`
- `docs/architecture/testing-strategy.md`
- `docs/architecture/decisions/ADR-template.md`
- `docs/architecture/decisions/ADR-001-*.md` (and others)
- `docs/AI_COMMENT_GUIDELINES.md`
- `docs/DOCUMENTATION_METADATA_STANDARDS.md`
- `docs/MCP_STANDARDS.md`
- `docs/CONTEXT7_PATTERNS.md`
- `requirements/PROJECT_REQUIREMENTS.md` (if needed)
- `scripts/check_doc_sync.py` (if needed)

### Files to Modify (15+ files)
- `docs/ARCHITECTURE.md`
- `docs/README.md`
- `CONTRIBUTING.md`
- `.github/workflows/ci.yml`
- `.cursor/rules/agent-capabilities.mdc`
- `.cursorrules` (deprecation notice)
- Multiple code files (AI comment tags)
- Documentation generator templates
- And others as identified

---

**Document Status:** Ready for Review  
**Last Updated:** 2026-01-20  
**Next Review:** After stakeholder approval
