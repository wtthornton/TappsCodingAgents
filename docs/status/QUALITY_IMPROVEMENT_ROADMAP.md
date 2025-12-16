# Quality & Complexity Improvement Roadmap

**Current Status (2025-12-12):**
- ✅ **Overall Score: 77.76/100** (PASSING - above 70 threshold)
- ✅ **Security: 10.0/10** (excellent - Bandit integration fixed)
- ✅ **Performance: 9.29/10** (excellent)
- ✅ **Duplication: 10.0/10** (excellent)
- ✅ **Complexity: 2.26/10** (good - lower is better)

**Areas Needing Improvement:**
- ⚠️ **Maintainability: 6.17/10** (below 7.0 threshold, 25% weight)
- ⚠️ **Test Coverage: 5.04/10** (below target, 15% weight)
- ⚠️ **Linting: 5.0/10** (neutral, needs attention)
- ⚠️ **Type Checking: 5.0/10** (neutral, needs attention)

---

## Phase 1: Immediate Wins (Target: 80+ overall score)

### 1.1 Fix Linting Issues (Expected: +2-3 points)
**Current:** 5.0/10 → **Target:** 7.0+/10

**Actions:**
- Run `ruff check .` and fix auto-fixable issues
- Address remaining linting violations systematically
- Focus on high-impact files first (CLI, core modules)

**Command:**
```bash
ruff check . --fix
ruff check . --output-format json > reports/ruff_issues.json
```

**Impact:** Low effort, medium impact (10% weight in overall score)

---

### 1.2 Improve Type Checking Score (Expected: +2-3 points)
**Current:** 5.0/10 → **Target:** 7.0+/10

**Actions:**
- Fix mypy errors (currently shows "Success: no issues found" but score is 5.0)
- Add missing type annotations to untyped functions
- Enable `--check-untyped-defs` for stricter checking

**Command:**
```bash
mypy tapps_agents --check-untyped-defs > reports/mypy_strict.txt
```

**Files with untyped function bodies (from baseline):**
- `tapps_agents/mcp/tool_registry.py:37-38`
- `tapps_agents/core/ast_parser.py:49`
- `tapps_agents/core/hardware_profiler.py:138-139`
- `tapps_agents/core/visual_feedback.py:592-593`
- `tapps_agents/core/task_memory.py:109-113`
- `tapps_agents/context7/cross_references.py:104,107`
- `tapps_agents/core/agent_learning.py:385`
- `tapps_agents/experts/base_expert.py:104`
- `tapps_agents/experts/agent_integration.py:40`

**Impact:** Medium effort, medium impact (type checking contributes to overall score)

---

## Phase 2: Maintainability Improvements (Target: 7.0+)

### 2.1 Refactor High-Complexity Functions
**Current Maintainability:** 6.17/10 → **Target:** 7.0+/10

**Critical Complexity Hotspots:**

#### 🔴 **P0 - CLI Main Function (F - 212 complexity)**
**File:** `tapps_agents/cli.py:277`
- **Issue:** Monolithic `main()` function with 212 complexity
- **Impact:** Largest drag on maintainability score
- **Solution:** Break into smaller functions:
  - Extract argument parsing logic
  - Extract command routing
  - Extract result formatting

**Expected Impact:** +0.5-1.0 maintainability points

#### 🟡 **P1 - Architect Agent (D - 24 complexity)**
**File:** `tapps_agents/agents/architect/agent.py:152` - `_design_system()`
- **Issue:** Very high complexity method
- **Solution:** Extract sub-methods for:
  - Component identification
  - Relationship mapping
  - Technology selection logic

#### 🟡 **P1 - Visual Designer (D - 29 complexity)**
**File:** `tapps_agents/agents/designer/visual_designer.py:96` - `refine_ui()`
- **Issue:** Extremely high complexity (29)
- **Solution:** Break into smaller iteration steps

#### 🟢 **P2 - Other B-level Functions**
- `tapps_agents/agents/analyst/agent.py:69` - `run()` (B-8)
- `tapps_agents/agents/architect/agent.py:361` - `_select_technology()` (C-20)
- `tapps_agents/agents/designer/agent.py:299` - `_design_ui()` (C-14)

**Impact:** High effort, high impact (25% weight in overall score)

---

### 2.2 Improve Code Structure
**Actions:**
- Reduce long lines (Radon MI penalizes lines > 100 chars)
- Improve function length (break down functions > 50 lines)
- Add docstrings to improve maintainability index

**Command:**
```bash
radon mi tapps_agents -s
```

**Files with lowest MI scores:**
- `tapps_agents/cli.py` - C (0.00) - needs major refactoring
- `tapps_agents/agents/reviewer/scoring.py` - A (21.77)
- `tapps_agents/agents/enhancer/agent.py` - A (22.83)
- `tapps_agents/agents/reviewer/agent.py` - A (24.53)

---

## Phase 3: Test Coverage Improvements (Target: 7.0+)

### 3.1 Add Tests for Critical Paths
**Current:** 5.04/10 → **Target:** 7.0+/10

**Priority Areas:**
1. **Scoring System** (`tapps_agents/agents/reviewer/scoring.py`)
   - Test all scoring methods
   - Test edge cases (empty files, syntax errors)
   - Test tool fallbacks (when radon/bandit unavailable)

2. **Report Generation** (`tapps_agents/agents/reviewer/report_generator.py`)
   - Test JSON/Markdown/HTML generation
   - Test historical data saving
   - Test error handling

3. **CLI Commands** (`tapps_agents/cli.py`)
   - Test command routing
   - Test argument parsing
   - Test error handling

4. **Service Discovery** (`tapps_agents/agents/reviewer/service_discovery.py`)
   - Test service pattern matching
   - Test exclusion logic
   - Test edge cases

**Command:**
```bash
pytest --cov=tapps_agents --cov-report=xml --cov-report=term
```

**Target Coverage:** 70%+ for core modules

**Impact:** High effort, medium impact (15% weight in overall score)

---

## Phase 4: Continuous Improvement

### 4.1 Set Up Quality Gates
**Actions:**
- Add CI/CD quality gates:
  - Fail if `overall_score < 70`
  - Warn if `maintainability_score < 7.0`
  - Warn if `test_coverage_score < 7.0`
  - Block PRs with new complexity violations (F/D level)

**Example CI Check:**
```yaml
- name: Quality Gate
  run: |
    python -m tapps_agents.cli reviewer analyze-project --format json > quality.json
    python -c "import json; d=json.load(open('quality.json')); assert d['aggregated']['average_scores']['overall_score'] >= 70, 'Quality score below threshold'"
```

### 4.2 Regular Quality Reviews
**Schedule:**
- Weekly: Run quality analysis and track trends
- Monthly: Review complexity hotspots
- Quarterly: Full quality audit

**Tracking:**
- Store historical reports in `reports/quality/historical/`
- Track score trends over time
- Identify regressions early

---

## Quick Reference: Commands

### Run Quality Analysis
```bash
# Full project analysis
python -m tapps_agents.cli reviewer analyze-project --format json

# Generate reports
python -m tapps_agents.cli reviewer report tapps_agents all --output-dir reports/quality

# Check specific metrics
python -m tapps_agents.cli reviewer score tapps_agents/cli.py
```

### Run Quality Tools
```bash
# Complexity analysis
radon cc tapps_agents -s -a

# Maintainability index
radon mi tapps_agents -s

# Security scan
bandit -r tapps_agents -f json

# Linting
ruff check . --output-format json

# Type checking
mypy tapps_agents --check-untyped-defs
```

### Run Tests with Coverage
```bash
pytest --cov=tapps_agents --cov-report=xml --cov-report=term-missing
```

---

## Expected Outcomes

**Phase 1 Completion:**
- Overall Score: **77.76 → 82-85/100**
- Linting: **5.0 → 7.0+/10**
- Type Checking: **5.0 → 7.0+/10**

**Phase 2 Completion:**
- Overall Score: **82-85 → 85-88/100**
- Maintainability: **6.17 → 7.0+/10**

**Phase 3 Completion:**
- Overall Score: **85-88 → 88-92/100**
- Test Coverage: **5.04 → 7.0+/10**

**Final Target: 90+/100** (Excellent quality)

---

## Notes

- **Security score is now 10.0** ✅ (Bandit integration fixed)
- **Performance score is 9.29** ✅ (excellent)
- **Duplication score is 10.0** ✅ (excellent)
- **Complexity is low (2.26)** ✅ (good, but some functions still need refactoring)

**Focus areas:**
1. Maintainability (biggest impact, 25% weight)
2. Test Coverage (15% weight)
3. Linting/Type Checking (easier wins, 10% combined)

