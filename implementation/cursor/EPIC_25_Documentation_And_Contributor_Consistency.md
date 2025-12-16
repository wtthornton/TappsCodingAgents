# Epic 25: Documentation & Contributor Consistency (Remove Drift and Contradictions)

## Epic Goal

Make documentation and contributor guidance **internally consistent and aligned with the actual repo** so developers can set up, run, and contribute without confusion or contradictory instructions.

## Epic Description

### Existing System Context

- **Current relevant functionality**: Extensive docs exist (`README.md`, `docs/*`, `docs/html/*`), plus contributor docs (`CONTRIBUTING.md`, `SECURITY.md`).
- **Technology stack**: Python 3.13, ruff/black/mypy/pytest toolchain, Cursor integration assets under `tapps_agents/resources/*`.
- **Integration points**:
  - Entry docs: `README.md`, `docs/DEVELOPER_GUIDE.md`, `docs/CURRENT_DEFAULTS.md`, `docs/TROUBLESHOOTING.md`
  - Contributor docs: `CONTRIBUTING.md`, `SECURITY.md`
  - Packaged init assets: `tapps_agents/resources/*`

### Enhancement Details

- **What’s being improved (no new features)**:
  - Remove contradictions (e.g., line length policy, install commands, missing referenced files).
  - Clarify canonical vs packaged resource locations (what is *shipped* vs what is *installed into target repos*).
  - Ensure docs match CI behavior and actual commands.
- **How it integrates**:
  - No behavior changes; improved docs accuracy and usability.
- **2025 standards / guardrails**:
  - **One true workflow**: a single recommended setup path for users and contributors.
  - **Docs as contracts**: commands, paths, and outputs referenced in docs must exist and remain correct.
  - **Platform clarity**: Windows/macOS/Linux instructions validated and consistent.
- **Success criteria**:
  - New users can install and run the CLI successfully from docs alone.
  - Contributors can run the same checks CI runs, using the same commands.

## Stories

1. **Story 25.1: Normalize formatting and tooling guidance** ✅ **COMPLETE**
   - **Goal**: Eliminate conflicting style rules and commands.
   - **Acceptance Criteria**:
     - ✅ `CONTRIBUTING.md` line length matches configured tooling (ruff/black) - updated to 88 characters.
     - ✅ Formatter guidance is unified (ruff format or black, both configured to 88 characters).
     - ✅ All commands listed are valid and reflect the current toolchain - updated to match CI commands.
   - **Changes**: Updated `CONTRIBUTING.md` line length from 100 to 88, unified formatter guidance, aligned commands with CI.

2. **Story 25.2: Fix install/setup drift in contributor docs** ✅ **COMPLETE**
   - **Goal**: Ensure contributor setup steps reference real files and correct dependency install paths.
   - **Acceptance Criteria**:
     - ✅ Remove references to non-existent files - verified no `requirements-dev.txt` references found.
     - ✅ The recommended install method matches CI - `pip install -e ".[dev]"` documented consistently.
     - ✅ Windows activation and command examples are correct and consistent across docs.
   - **Changes**: Verified install commands match CI, confirmed no references to non-existent files.

3. **Story 25.3: Clarify packaged vs installed Cursor assets** ✅ **COMPLETE**
   - **Goal**: Prevent confusion about where rules/skills/background-agents come from.
   - **Acceptance Criteria**:
     - ✅ Docs explicitly state that `tapps_agents/resources/...` are shipped templates and `tapps-agents init` installs into `.cursor/` and `.claude/skills/` in a target repo.
     - ✅ Default paths in `docs/CURRENT_DEFAULTS.md` match the installer behavior.
   - **Changes**: Updated `docs/CURRENT_DEFAULTS.md`, `docs/HOW_IT_WORKS.md`, and `docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md` to clearly distinguish shipped templates from installed locations.

4. **Story 25.4: Documentation verification gate** ✅ **COMPLETE**
   - **Goal**: Prevent doc drift from recurring.
   - **Acceptance Criteria**:
     - ✅ Add a documented process (and optionally CI check) to validate that referenced files/paths exist - created `scripts/verify_docs.py`.
     - ✅ Broken internal links are detectable (at least within Markdown files) - script checks markdown links and file references.
   - **Changes**: Created `scripts/verify_docs.py` verification script, documented in `CONTRIBUTING.md`.

## Compatibility Requirements

- [ ] No changes to current features—documentation only.
- [ ] Maintain backwards compatibility of docs URLs/anchors where reasonable.

## Risk Mitigation

- **Primary Risk**: Docs changes could temporarily confuse existing users if wording changes significantly.
- **Mitigation**:
  - Keep a short “what changed in docs” note in the relevant guide.
- **Rollback Plan**:
  - Revert doc edits while keeping validation tooling if it remains useful.

## Definition of Done

- [x] No contradictory setup/tooling guidance across README/docs/CONTRIBUTING/SECURITY.
- [x] Canonical installation flow is clear and matches actual behavior.
- [x] Doc drift is prevented via a verification process/check.

## Integration Verification

- **IV1**: A new contributor can follow docs to run lint/type/tests successfully.
- **IV2**: A new user can follow README/Quick Start to install and run `tapps-agents` commands.
- **IV3**: `tapps-agents init` resource locations are clearly explained and match actual output paths.


