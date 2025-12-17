# Epic 1: SDLC Quality Engine Improvements

## Epic Goal

Transform the SDLC from a linear pipeline with score-only gates into a self-correcting quality engine that achieves "zero issues" consistently across any codebase. This epic implements pluggable validation, composite gating, bounded loopback remediation, and traceability to ensure functional completeness and adherence to project-specific standards.

## Epic Description

### Existing System Context

- **Current relevant functionality**: TappsCodingAgents has an SDLC workflow system with workflow executor, agent orchestration, and basic quality gates that primarily evaluate numeric scoring
- **Technology stack**: Python 3.13+, existing workflow executor (`tapps_agents/workflow/executor.py`), project profiling (`tapps_agents/core/project_profile.py`), existing agent framework
- **Integration points**: 
  - Existing workflow executor and state management
  - Project profile system (`.tapps-agents/project-profile.yaml`)
  - Current reviewer, tester, and ops agents
  - Existing checkpoint/resume system

### Enhancement Details

- **What's being added/changed**: 
  - Pluggable validation layer that adapts to detected project stack
  - Expansion of "testing" into comprehensive "verification" (tests + linters + config checks)
  - Standardized Issues Manifest schema for machine-actionable remediation
  - Composite gating model (issues + verification outcomes, not just scores)
  - Bounded loopback protocol with deterministic remediation payloads
  - Lightweight traceability matrix (requirements → stories → validations)

- **How it integrates**: 
  - Validation layer loads based on project profile and repo signals
  - Issues Manifest becomes the backbone for all quality checks
  - Composite gates replace score-only gates in workflow executor
  - Loopback protocol integrates with existing checkpoint/resume system
  - Traceability matrix integrates with existing story/requirement tracking

- **Success criteria**: 
  - SDLC can detect project stack and load appropriate validators
  - All quality checks emit standardized Issues Manifest
  - Composite gates correctly block on critical issues and verification failures
  - Loopback protocol successfully remediates issues and re-validates
  - Traceability matrix enables machine-checkable completeness verification
  - Zero critical/high issues before pipeline proceeds (configurable thresholds)

## Stories

1. **Story 1.1: Issues Manifest Schema & Standardization**
   - Define and implement standardized Issues Manifest schema (id, severity, category, evidence, repro, suggested_fix, owner_step)
   - Create Issues Manifest data models with validation
   - Update all existing agents (reviewer, tester, ops) to emit Issues Manifest format
   - Add Issues Manifest serialization/deserialization utilities
   - Acceptance criteria: All agents emit issues in standardized schema, schema validation passes, backward compatibility maintained

2. **Story 1.2: Pluggable Validation Layer Infrastructure**
   - Create validation interface/abstract base class for validators
   - Implement validator registry that loads validators based on project profile
   - Add repo signal detection (languages, frameworks, dependency manifests, build/test tooling, CI config)
   - Create default validator plugin set (Python, TypeScript, general-purpose)
   - Acceptance criteria: Validators load based on project profile, repo signals correctly detected, default validators work for common stacks

3. **Story 1.3: Expand Testing into Comprehensive Verification**
   - Extend verification beyond unit tests to include: build/compile/package checks, integration tests, static analysis (linters/type checks), dependency audit, security scans, policy checks, artifact integrity checks
   - Create verification orchestrator that runs appropriate checks based on project stack
   - Integrate verification results into Issues Manifest
   - Acceptance criteria: Verification runs all applicable checks, results properly categorized in Issues Manifest, stack-specific checks correctly selected

4. **Story 1.4: Composite Gating Model Implementation**
   - Replace score-only gates with composite gate logic
   - Implement hard fail conditions (critical issues, verification failures, missing artifacts)
   - Implement soft fail/loopback conditions (high issues above threshold, regression vs baseline, low expert confidence)
   - Add configurable thresholds and gate policies
   - Acceptance criteria: Gates correctly evaluate composite conditions, hard fails block pipeline, soft fails trigger loopback, thresholds configurable

5. **Story 1.5: Bounded Loopback Protocol**
   - Implement loopback policy (max_attempts, retry_backoff, escalation rules)
   - Create remediation payload structure (issue → fix instructions → implementer)
   - Add deterministic re-validation after remediation
   - Integrate with existing checkpoint/resume system
   - Add issue history persistence
   - Acceptance criteria: Loopback triggers on soft fails, remediation payloads correctly formatted, re-validation runs after fixes, max attempts respected, escalation produces blockers report

6. **Story 1.6: Traceability Matrix Implementation**
   - Create lightweight traceability matrix artifact structure
   - Implement requirements → stories → validations mapping
   - Add acceptance criterion coverage tracking
   - Create machine-checkable completeness verification
   - Acceptance criteria: Traceability matrix correctly maps relationships, coverage tracking works, completeness verification identifies gaps

## Compatibility Requirements

- [ ] Existing workflow execution continues to work with enhanced gates
- [ ] Existing agent APIs remain backward compatible
- [ ] Project profile format remains compatible
- [ ] Checkpoint/resume system enhanced, not replaced
- [ ] Score-based gates can be gradually migrated to composite gates

## Risk Mitigation

- **Primary Risk**: Composite gates may be too strict and block legitimate work
  - **Mitigation**: Configurable thresholds, soft fail conditions, clear escalation paths
- **Primary Risk**: Loopback protocol may create infinite loops
  - **Mitigation**: Bounded retries with max_attempts, escalation to human review, issue history tracking
- **Primary Risk**: Validation layer may not detect all project stacks correctly
  - **Mitigation**: Extensible plugin system, fallback to general-purpose validators, manual override capability
- **Rollback Plan**: 
  - Feature flags to disable composite gates (revert to score-only)
  - Disable loopback protocol if causing issues
  - Maintain backward compatibility with existing workflow definitions

## Definition of Done

- [ ] All stories completed with acceptance criteria met
- [ ] Issues Manifest schema standardized across all agents
- [ ] Validation layer successfully detects and validates multiple project stacks
- [ ] Composite gates correctly block on critical issues
- [ ] Loopback protocol successfully remediates issues within bounded retries
- [ ] Traceability matrix enables completeness verification
- [ ] Comprehensive test coverage for all new components
- [ ] Documentation updated (SDLC guide, validation plugin guide, gating model guide)
- [ ] No regression in existing workflow execution
- [ ] Example workflows demonstrate new capabilities

## Implementation Status

**Last Updated:** 2025-01-XX

**Overall Status:** Not Started - All stories are in Draft status

**Story Status:**
- Story 27.1 (Issues Manifest Schema): Draft - Not implemented
- Story 27.2 (Pluggable Validation Layer): Draft - Not implemented
- Story 27.3 (Comprehensive Verification): Draft - Not implemented
- Story 27.4 (Composite Gating): Draft - Partial: QualityGate exists but only evaluates scores, not issues + verification outcomes
- Story 27.5 (Bounded Loopback): Draft - Partial: Retry logic exists for step execution, but not for issue remediation loopback
- Story 27.6 (Traceability Matrix): Draft - Not implemented

**Notes:**
- Existing QualityGate class (`tapps_agents/quality/quality_gates.py`) provides score-based gating but does not implement composite gate logic with issue evaluation
- RetryConfig and retry logic exist in `tapps_agents/workflow/parallel_executor.py` but is for step retries, not the bounded loopback protocol for issue remediation
- No standardized Issues Manifest schema found - existing SecurityIssue and ReviewComment classes do not match required schema

