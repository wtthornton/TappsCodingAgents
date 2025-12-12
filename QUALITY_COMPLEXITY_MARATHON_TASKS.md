# Quality & Complexity Marathon — Task Tracker

**Repo:** `TappsCodingAgents`  
**Purpose:** Track a long-running, interruption-tolerant cleanup of **quality + complexity** with **checkpoints** and measurable **gates**.  
**Status:** ⏳ Pending approval to execute (this file is the pre-flight checklist).

---

## How to use this file

- Update checkboxes as work is completed.
- Record key metrics each checkpoint (baseline + after each major batch).
- Do not start “execution” phases until the **Approval Gate** is checked.

---

## Definitions (what we mean by “quality”)

We will measure and trend these signals:

- **Lint**: Ruff (`ruff check`)
- **Format**: Black (`black`)
- **Types**: mypy (`mypy`)
- **Complexity**: radon CC + MI (`radon cc`, `radon mi`)
- **Tests/Coverage**: pytest + `coverage.xml` (`pytest --cov ... --cov-report=xml`)
- **Security**: bandit + pip-audit (`bandit`, `pip-audit`)
- **Duplication (optional)**: jscpd (only if Node tooling exists and it’s stable)

---

## Approval Gate (must be checked before running the marathon)

- [x] **Approval**: You approve execution of the marathon runner (tools, gates, and scope) after reviewing the summary and baseline results.

---

## Phase 0 — Pre-flight (determinism + scope)

### 0.1 Tooling determinism
- [ ] **Add project tool config**: Create `pyproject.toml` (preferred) or equivalent config files to stabilize:
  - [ ] Ruff (rules, excludes, line length, per-file ignores for tests)
  - [ ] mypy (initially non-strict; allow gradual tightening)
  - [ ] pytest defaults (timeouts, coverage settings)

### 0.2 Ensure project-wide analysis includes `tapps_agents/`
- [ ] **Service discovery coverage**: Update the service discovery / analysis flow so “analyze project” actually analyzes the main package (`tapps_agents/`), not just `services/*/`, `src/*/`, etc.
  - Notes:
    - Current `ServiceDiscovery` patterns do not include `tapps_agents/`.

### 0.3 Reporting directory + artifacts
- [ ] Create/standardize `reports/` outputs:
  - [ ] `reports/baseline/`
  - [ ] `reports/checkpoints/`
  - [ ] `reports/quality/` (if using ReviewerAgent report generator)

---

## Phase 1 — Baseline (collect metrics, no refactors)

### 1.1 Environment setup
- [ ] Install dependencies (`requirements.txt`) into a clean environment
- [ ] Verify tool availability and versions:
  - [ ] `ruff`
  - [ ] `black`
  - [ ] `mypy`
  - [ ] `radon`
  - [ ] `bandit`
  - [ ] `pip-audit`
  - [ ] `pytest`

### 1.2 Baseline runs (save outputs)
- [ ] **Black**: run format (no refactor intent)
- [ ] **Ruff**: run lint and export JSON report to `reports/baseline/ruff.json`
- [ ] **mypy**: run and export text report to `reports/baseline/mypy.txt`
- [ ] **pytest + coverage.xml**: run tests and produce `coverage.xml` in repo root
- [ ] **radon CC + MI**:
  - [ ] `reports/baseline/radon_cc.txt`
  - [ ] `reports/baseline/radon_mi.txt`
- [ ] **bandit**: JSON to `reports/baseline/bandit.json`
- [ ] **pip-audit**: JSON to `reports/baseline/pip_audit.json`
- [ ] **ReviewerAgent report** (optional but recommended): generate JSON/Markdown/HTML into `reports/quality/`

### 1.3 Baseline checkpoint record (fill this in)

| Timestamp | Ruff issues | mypy errors | Coverage % | Radon CC hotspots (count) | Bandit (H/M/L) | pip-audit vulns | Notes |
|---|---:|---:|---:|---:|---|---:|---|
| (fill) |  |  |  |  |  |  |  |

---

## Phase 2 — Marathon execution (batch + checkpoint + resume)

### 2.1 Marathon runner behavior (requirements)
- [ ] **Batching**: process work in small batches (e.g., 10–30 files or one module slice).
- [ ] **Checkpointing**: after each batch, record:
  - processed files
  - remaining queue
  - last successful tool run results
  - generated artifacts paths (reports, coverage.xml, etc.)
- [ ] **Resume**: if interrupted, restart continues from last checkpoint.
- [ ] **Safety**: always keep repo in a “green” state at checkpoints (tests/lint/type within agreed gates).

### 2.2 Cleanup order (safe → risky)
- [ ] **Step A — Formatting**: Black across repo
- [ ] **Step B — Ruff safe fixes**: enable safe auto-fixes (no behavioral changes)
- [ ] **Step C — Ruff non-safe fixes** (only after review of config + impact)
- [ ] **Step D — Type fixes**: reduce mypy error count (module-by-module)
- [ ] **Step E — Complexity reduction** (radon-driven):
  - For each hotspot above threshold, apply:
    - [ ] extract helpers
    - [ ] reduce nesting (guard clauses)
    - [ ] simplify conditionals / loops
    - [ ] add tests around behavior changes
- [ ] **Step F — Coverage increases**: tests for hotspots + critical paths
- [ ] **Step G — Security**: bandit/pip-audit remediation (highest severity first)

---

## Gates (the marathon should enforce these)

### 3.1 Complexity gate
- Target: **No new hotspots above threshold** (set threshold after baseline)
- Directional goal: hotspot count decreases over time

### 3.2 Lint gate (Ruff)
- Target: Ruff errors decrease; “must-fix” rules do not regress

### 3.3 Type gate (mypy)
- Target: mypy error count trends down; stricter rules added gradually

### 3.4 Coverage gate
- Target: coverage must not drop below baseline; raise threshold incrementally

### 3.5 Security gate
- Target: no new High/Critical vulnerabilities; existing ones trend down

---

## Checkpoint log (fill in each batch checkpoint)

| Checkpoint ID | Timestamp | Batch scope | Ruff Δ | mypy Δ | Coverage Δ | Complexity Δ | Tests pass? | Notes |
|---|---|---|---:|---:|---:|---:|---|---|
| CP-000 | (baseline) | baseline | 0 | 0 | 0 | 0 | (fill) | baseline captured |

---

## Exit criteria (done means done)

- [ ] **Lint**: Ruff meets agreed threshold (ideally “0 errors”, warnings minimized)
- [ ] **Types**: mypy clean for selected scope (or error budget agreed)
- [ ] **Complexity**: hotspots above threshold eliminated/reduced to agreed count
- [ ] **Coverage**: meets target and is stable
- [ ] **Security**: bandit and pip-audit issues resolved to agreed severity threshold
- [ ] **Documentation**: short “Quality Marathon Results” summary committed in `reports/` or `docs/`

---

## Notes / constraints

- This repo currently has strong internal scoring infrastructure (`CodeScorer`), but missing external tool config files.
- The multi-service analyzer may not discover `tapps_agents/` as a “service” without pattern updates.


