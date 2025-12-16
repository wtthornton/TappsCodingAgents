# Epic 24: Security Policy Reality & Path Enforcement (Align Claims With Code)

## Epic Goal

Make security posture **accurate, enforceable, and testable** by aligning documentation with actual behavior and strengthening existing safety controls (especially filesystem access boundaries) without adding new product capabilities.

## Epic Description

### Existing System Context

- **Current relevant functionality**:
  - Security documentation exists in `SECURITY.md`.
  - Path validation exists in `tapps_agents/core/agent_base.py` and agent-specific checks.
  - CI safety controls exist for real-service tests (`tests/e2e/fixtures/ci_safety.py`).
- **Technology stack**: Python 3.13+, Pydantic config, filesystem operations, GitHub Actions.
- **Integration points**:
  - Security docs: `SECURITY.md`, `docs/CONTEXT7_SECURITY_PRIVACY.md`, `docs/CONFIGURATION.md`
  - Path validation: `tapps_agents/core/agent_base.py`, `tapps_agents/agents/*`
  - Worktrees/state/artifacts under `.tapps-agents/`

### Enhancement Details

- **What’s being improved (no new features)**:
  - Remove placeholders and contradictions in security documentation.
  - Define and enforce a clear filesystem access policy consistent across agents.
  - Reduce duplication in security-critical validation logic.
- **How it integrates**:
  - Keeps current behavior and feature set; makes security promises verifiable and reduces risk from unsafe inputs.
- **2025 standards / guardrails**:
  - **Security claims must be testable**: docs match implementation, with explicit boundaries.
  - **Least privilege**: restrict writes/reads to configured allowed roots (workspace/project + `.tapps-agents/`).
  - **No secret leakage**: artifacts/logs are redacted; CI failure bundles scrub sensitive values.
  - **No placeholder security policy**: real contact and supported versions.
- **Success criteria**:
  - Security documentation is credible and reflects reality.
  - Path traversal/out-of-bounds access is blocked by design (not just string heuristics).

## Stories

1. **Story 24.1: Make `SECURITY.md` real and accurate** ✅ **COMPLETE**
   - **Goal**: Remove placeholders and reconcile contradictory guidance.
   - **Acceptance Criteria**:
     - ✅ Supported versions table reflects actual supported releases (updated to 2.0.x).
     - ✅ Security contact mechanism is real (updated to use GitHub Security Advisories).
     - ✅ Guidance about env-var substitution matches actual config behavior (documented limitation).
   - **Status**: Completed - SECURITY.md updated with accurate version table, GitHub Security Advisories contact, and env-var substitution documentation.

2. **Story 24.2: Define a filesystem access policy for agents** ✅ **COMPLETE**
   - **Goal**: Establish clear rules for what agents may read/write.
   - **Acceptance Criteria**:
     - ✅ Policy defines allowed roots (project root and `.tapps-agents/`), and how temporary/test paths are handled.
     - ✅ Policy is documented and referenced from developer docs.
   - **Status**: Completed - Created `docs/SECURITY_FILESYSTEM_ACCESS_POLICY.md` with comprehensive policy and referenced from SECURITY.md.

3. **Story 24.3: Enforce allowlisted roots for path operations** ✅ **COMPLETE**
   - **Goal**: Strengthen existing path validation beyond heuristic string checks.
   - **Acceptance Criteria**:
     - ✅ Resolved paths are verified to be within allowed roots for read/write operations (where applicable).
     - ✅ Worktree/state/report paths cannot escape `.tapps-agents/` even with hostile input.
     - ✅ Agent-specific duplicate path checks are removed in favor of the centralized implementation.
   - **Status**: Completed - Created `tapps_agents/core/path_validator.py` with root-based validation and updated `BaseAgent._validate_path()` to use it.

4. **Story 24.4: Security regression tests** ✅ **COMPLETE**
   - **Goal**: Prevent future regressions in path safety and redaction.
   - **Acceptance Criteria**:
     - ✅ Tests cover traversal attempts (`..`, encoded variants), absolute path escapes, and symlink edge cases (where supported).
     - ✅ Tests cover that redaction is applied before uploading CI artifacts when applicable.
   - **Status**: Completed - Created `tests/unit/core/test_path_validator.py` with comprehensive path validation tests and redaction tests.

## Compatibility Requirements

- [x] No breaking changes to normal agent workflows that operate within the project.
- [x] Developer escape hatches (if any) must be explicit and documented (no implicit bypasses).

## Risk Mitigation

- **Primary Risk**: Over-restricting paths could break legitimate workflows.
- **Mitigation**:
  - Stage enforcement: warn-first mode, then hard enforcement once tests and docs are aligned.
  - Provide clear error messages explaining how to configure allowed roots.
- **Rollback Plan**:
  - Revert enforcement to warn-only while keeping documentation fixes and tests.

## Definition of Done

- [x] Security documentation has no placeholders and matches implementation.
- [x] A clear filesystem access policy exists and is enforced centrally.
- [x] Path traversal and out-of-bounds access are blocked with tests.

## Integration Verification

- **IV1**: ✅ Agents can read/write expected project files and `.tapps-agents/` outputs.
- **IV2**: ✅ Traversal attempts are blocked consistently across agents.
- **IV3**: ✅ CI artifacts do not leak secrets/PII based on redaction policy.

## Status

**COMPLETE** - All stories (24.1, 24.2, 24.3, 24.4) have been implemented and verified.

### Completed Stories

1. **Story 24.1: Make `SECURITY.md` real and accurate** ✅
   - Updated version table to reflect 2.0.x (current version)
   - Replaced placeholder email with GitHub Security Advisories
   - Documented env-var substitution limitation

2. **Story 24.2: Define a filesystem access policy for agents** ✅
   - Created `docs/SECURITY_FILESYSTEM_ACCESS_POLICY.md`
   - Documented allowed roots (project root and `.tapps-agents/`)
   - Documented temporary/test path handling
   - Referenced from SECURITY.md

3. **Story 24.3: Enforce allowlisted roots for path operations** ✅
   - Created `tapps_agents/core/path_validator.py` with root-based validation
   - Updated `BaseAgent._validate_path()` to use centralized validator
   - All agents now use centralized path validation

4. **Story 24.4: Security regression tests** ✅
   - Created `tests/unit/core/test_path_validator.py` with comprehensive tests
   - Tests cover traversal attempts, absolute path escapes, symlink edge cases
   - Tests cover redaction functionality for CI artifacts

### Deliverables

- ✅ Updated `SECURITY.md` with accurate information
- ✅ Created `docs/SECURITY_FILESYSTEM_ACCESS_POLICY.md`
- ✅ Created `tapps_agents/core/path_validator.py`
- ✅ Updated `tapps_agents/core/agent_base.py` to use centralized validator
- ✅ Created `tests/unit/core/test_path_validator.py` with security regression tests


