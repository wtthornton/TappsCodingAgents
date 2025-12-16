# Epic 21: Dependency & Packaging Alignment (Single Source of Truth)

## Status

**Complete** - All stories completed and acceptance criteria met.

## Epic Goal

Make dependency management and packaging **consistent, minimal, and non-drifting** so installs are predictable for developers and CI/release behavior is reliable across `pip install`, editable installs, and GitHub Actions.

## Epic Description

### Existing System Context

- **Current relevant functionality**: Packaging exists via `pyproject.toml`, `setup.py`, `MANIFEST.in`, plus `requirements.txt`. CI uses a mix of `pip install -e ".[dev]"` and `pip install -r requirements.txt`.
- **Technology stack**: Python 3.13+, setuptools build backend, GitHub Actions.
- **Integration points**:
  - Packaging metadata: `pyproject.toml`, `setup.py`, `MANIFEST.in`
  - CI: `.github/workflows/ci.yml`, `.github/workflows/test.yml`, `.github/workflows/e2e.yml`
  - CLI distribution: console script `tapps-agents=tapps_agents.cli:main`

### Enhancement Details

- **What’s being improved (no new features)**:
  - Eliminate drift between `pyproject.toml`, `requirements.txt`, and `setup.py`.
  - Ensure runtime installs don’t unnecessarily pull in dev/test tooling.
  - Ensure CI uses one consistent install strategy.
- **How it integrates**:
  - Maintains current CLI and behavior; changes only packaging/dependency plumbing and documentation.
- **2025 standards / guardrails**:
  - **Single source of truth**: `pyproject.toml` is authoritative for dependencies and metadata.
  - **Minimal runtime surface**: avoid shipping test/lint tools as hard runtime deps.
  - **Reproducible CI**: CI installs the same dependency sets developers use locally.
  - **No surprises**: clearly define what is installed in `default` vs `dev` vs `e2e`/`test` extras.
- **Success criteria**:
  - A clean install path with no dependency drift.
  - CI and local developer setup follow the same contract.

## Stories

1. **Story 21.1: Establish a canonical dependency policy**
   - **Goal**: Define and enforce which file is authoritative and what each dependency channel means.
   - **Acceptance Criteria**:
     - `pyproject.toml` is documented as the authoritative source.
     - A written policy exists for `requirements.txt` (e.g., “generated/dev convenience only” or removed).
     - The project documents what belongs in runtime vs dev/test tooling.

2. **Story 21.2: Remove runtime dependency bloat (separate runtime vs dev)**
   - **Goal**: Ensure end users installing the package don’t pull in the full toolchain.
   - **Acceptance Criteria**:
     - Runtime installs do **not** install `pytest`, `ruff`, `mypy`, `black`, etc. unless explicitly requested.
     - CI uses a dedicated dev/test extra (or equivalent) that includes required tooling.
     - The dependency set required for CLI usage is explicit and tested.

3. **Story 21.3: Eliminate `setup.py`/`requirements.txt` drift risk**
   - **Goal**: Prevent conflicting dependency sources from diverging over time.
   - **Acceptance Criteria**:
     - `setup.py` cannot silently define a different dependency set than `pyproject.toml`.
     - A “dependency drift” check is documented and run in CI (fails if the sources disagree per policy).

4. **Story 21.4: CI installation consistency**
   - **Goal**: Make GitHub Actions use one install pattern across workflows.
   - **Acceptance Criteria**:
     - `.github/workflows/ci.yml` and `.github/workflows/test.yml` use the same install method.
     - The chosen method is documented in `docs/DEVELOPER_GUIDE.md` and `CONTRIBUTING.md`.

## Compatibility Requirements

- [x] No change to user-facing CLI commands or agent behavior.
- [x] `tapps-agents init` still ships and installs packaged resources (Cursor Rules/Skills/workflow presets).
- [x] Windows + Linux installs remain supported (Python 3.13+).

## Risk Mitigation

- **Primary Risk**: Breaking installs for contributors/users due to dependency refactor.
- **Mitigation**:
  - Add explicit “install matrix” documentation and verify with CI jobs.
  - Keep a migration note for contributors if install commands change.
- **Rollback Plan**:
  - Revert to previous packaging files while preserving documentation updates.

## Definition of Done

- [x] Dependency policy documented and enforced.
- [x] No drift between dependency definitions per policy.
- [x] CI install method unified and reproducible.
- [x] Runtime install footprint reduced (dev/test tools not pulled by default).

## Integration Verification

- **IV1**: `pip install tapps-agents` works and provides CLI.
- **IV2**: `pip install -e ".[dev]"` (or equivalent) enables lint/type/tests consistently.
- **IV3**: CI workflows use the same install contract and pass.


