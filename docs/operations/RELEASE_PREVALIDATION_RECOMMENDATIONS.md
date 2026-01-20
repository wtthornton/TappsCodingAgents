# Release Pre-Validation Failure: Recommendations

When the **Pre-Release Validation** job fails in the [Release workflow](.github/workflows/release.yml), use this guide to identify the cause and fix it.

## 1. Identify Which Step Failed

In **GitHub Actions → Release → Pre-Release Validation**, expand the failed run and find the **first failed step**. Validation runs in this order:

| Order | Step | Common causes |
|-------|------|----------------|
| 1 | Extract version from tag | Tag format not `vX.Y.Z` (e.g. `v3.5.22`) |
| 2 | Verify version format | Version doesn’t match `^\d+\.\d+\.\d+$` |
| 3 | **Verify version matches code** | `pyproject.toml` or `__init__.py` version ≠ tag |
| 4 | Install GitHub CLI | (Rare) Runner/network |
| 5 | Check for existing release | (Rare) `gh` auth; usually continues |
| 6 | **Run linting** | `ruff check .` finds issues |
| 7 | **Run type checking** | `mypy` errors in `core`, `workflow`, `context7` |
| 8 | **Run full test suite** | Test failures or **coverage &lt; 75%** |
| 9 | Security scan | `continue-on-error: true` — does not fail the job |

---

## 2. Most Likely Cause: Coverage Below 75%

**Release** uses `--cov-fail-under=75`; **CI** uses `--cov-fail-under=40`.  
CI can be green while release fails on coverage.

### Recommendations

**A. Short-term: Align release with current quality gate**

If 75% is not achievable yet, lower the release threshold to match CI (or an agreed value) so releases are unblocked while you raise coverage:

```yaml
# .github/workflows/release.yml, in "Run full test suite"
--cov-fail-under=40 \   # or 50, 60, etc., to match CI or a stepped target
```

Then raise it over time (e.g. 50 → 60 → 75) as coverage improves.

**B. Long-term: Reach 75% and keep it**

- Run locally (with `.[dev]` installed):

  ```bash
  python -m pytest tests/ --cov=tapps_agents --cov-report=term-missing --cov-fail-under=75 -v
  ```

- Add/expand tests for:
  - `tapps_agents/core`
  - `tapps_agents/workflow`
  - `tapps_agents/context7`
- Use `coverage report` / `coverage html` to find low‑coverage files and priorities.
- Optionally add a **separate CI job** with `--cov-fail-under=75` so main branch is validated at release-level coverage before you tag.

**C. Make the gap explicit in CI**

CI already mentions the 75% target. You can add a non-blocking job that fails only for coverage &lt; 75% and reports in the UI, so you see release-style coverage on every PR without blocking merge.

---

## 3. Run Linting (Ruff)

Release runs:

```bash
ruff check .
```

(It does **not** run `ruff format --check`; that’s only in the main CI lint job.)

### Recommendations

- **Reproduce locally:**

  ```bash
  pip install -e ".[dev]"
  ruff check .
  ```

- Fix all reported issues; if you need to relax a rule, do it via `[tool.ruff.lint]` in `pyproject.toml` and document why.
- Optionally, add `ruff format --check` to the release workflow so formatting can’t pass CI but fail a manual release.

---

## 4. Run Type Checking (Mypy)

Release runs:

```bash
python -m mypy tapps_agents/core tapps_agents/workflow tapps_agents/context7
```

### Recommendations

- **Reproduce locally:**

  ```bash
  pip install -e ".[dev]"
  python -m mypy tapps_agents/core tapps_agents/workflow tapps_agents/context7
  ```

- Fix reported errors; for justified ignores, use `# type: ignore[code]` with a short comment.
- Ensure `[tool.mypy]` in `pyproject.toml` is aligned with what you want for `core`, `workflow`, and `context7` (paths, strictness, excludes).

---

## 5. Run Full Test Suite (Pytest)

Release runs:

```bash
python -m pytest tests/ \
  --junitxml=junit-release.xml \
  --cov=tapps_agents \
  --cov-report=xml \
  --cov-report=term-missing \
  --cov-fail-under=75 \
  --tb=short \
  -v
```

`pytest.ini` addopts (e.g. `-m unit`, `--timeout=30`, `-p tests.pytest_rich_progress`) also apply.

### Recommendations

- **Reproduce locally (as close to release as possible):**

  ```bash
  pip install -e ".[dev]"
  python -m pytest tests/ --cov=tapps_agents --cov-report=term-missing --cov-fail-under=75 -v
  ```

- **If a test fails:**
  - Inspect the traceback and fix the test or the code.
  - If a test is flaky, make it stable or move it to a separate, non-blocking job.

- **If the failure is from `pytest.ini` addopts** (e.g. `--timeout`, `-p tests.pytest_rich_progress`):
  - Ensure `pytest-timeout` and any custom plugin are in `[dev]` and installed in the release job.
  - If a plugin is optional, consider making it optional in `pytest.ini` (e.g. only when the plugin is available) so the release job does not fail on import/registration errors.

- **Use artifacts:** The workflow uploads `junit-release.xml` and `coverage.xml` on failure. Download them from the run to see exactly which tests failed and the coverage report.

---

## 6. Version Mismatch (Verify version matches code)

The job checks that the tag-derived version matches both `pyproject.toml` and `tapps_agents.__version__`.

### Recommendations

- Before tagging:
  - Run `.\scripts\update_version.ps1 -Version X.Y.Z`.
  - Commit `pyproject.toml`, `tapps_agents/__init__.py`, and any other files that script updates.
  - Then create and push the tag (see [RELEASE_GUIDE.md](RELEASE_GUIDE.md)).
- If the tag already exists and points at an older commit: delete the tag, fix the version, commit, and recreate the tag, as in [RELEASE_GUIDE.md](RELEASE_GUIDE.md#version-mismatch-in-tag-critical-issue).

---

## 7. Process Improvements

### A. Run release-style validation before tagging

Add a pre-tag check that mirrors the release validation (version, ruff, mypy, pytest with 75%):

```powershell
# Example: scripts/run_release_validation.ps1
pip install -e ".[dev]"
ruff check .
python -m mypy tapps_agents/core tapps_agents/workflow tapps_agents/context7
python -m pytest tests/ --cov=tapps_agents --cov-report=term-missing --cov-fail-under=75 -v
```

Run this (or integrate into `validate_release_readiness.ps1`) before `git tag` / `git push origin v*`.

### B. Align CI with release

- Add a **“release gate”** CI job that runs the same ruff, mypy, and pytest (with `--cov-fail-under=75`) as the release. It can be:
  - **Blocking on `main`** so you never tag a commit that would fail release, or
  - **Non-blocking** but always run and reported (e.g. in the PR and in `main`).

### C. Clearer failure reporting

- In the **Run full test suite** step, add a short summary when the run fails, e.g.:

  ```yaml
  - name: Run full test suite
    run: |
      python -m pytest tests/ ... || (echo "::error::Tests or coverage failed. Check junit-release.xml and coverage.xml."; exit 1)
  ```

- Optionally, use ` pytest --junitxml=...` and a follow-up step that parses `junit-release.xml` and posts a short summary (e.g. “X failures, Y% coverage”) as a job summary or comment.

### D. Lower release coverage temporarily and track progress

- Set `--cov-fail-under` in the release workflow to the current achievable value (e.g. 40 or 50).
- In the same workflow or in project/docs, record the desired target (75%) and a short plan (e.g. “Raise to 60 in Q1, 75 in Q2”).
- Schedule periodic bumps of `--cov-fail-under` as coverage improves, and run the release-style gate in CI to avoid regression.

---

## 8. Quick Reference: Local Commands to Mirror Release

From the project root, with `.[dev]` installed:

```bash
# 1. Lint
ruff check .

# 2. Type check
python -m mypy tapps_agents/core tapps_agents/workflow tapps_agents/context7

# 3. Tests + coverage (release threshold)
python -m pytest tests/ --cov=tapps_agents --cov-report=term-missing --cov-fail-under=75 -v
```

If all three succeed, pre-release validation is likely to pass, assuming the same Python version (3.13) and dependencies as in the workflow.

---

## 9. Related Docs

- [RELEASE_GUIDE.md](RELEASE_GUIDE.md) — Release process, versioning, tagging.
- [RELEASE_VERSION_TAG_WARNING.md](RELEASE_VERSION_TAG_WARNING.md) — Version/tag requirements.
- [.github/workflows/release.yml](../../.github/workflows/release.yml) — Release and pre-release job definitions.
