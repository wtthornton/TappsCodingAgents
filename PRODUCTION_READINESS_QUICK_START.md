# Production Readiness - Quick Start Guide

**Goal:** Use tapps-agents to fix this project and achieve 90+/100 quality score

---

## Current Status
- Overall Score: **77.76/100** (Passing but not production-ready)
- Target: **90+/100** (Production-ready)

## Critical Issues
1. **Maintainability: 6.17/10** (Target: 7.0+) - CLI main function has 212 complexity
2. **Test Coverage: 5.04/10** (Target: 7.0+) - Missing tests for critical paths
3. **Linting: 5.0/10** (Target: 7.0+) - Code quality issues
4. **Type Checking: 5.0/10** (Target: 7.0+) - Missing type hints

---

## 7-Day Execution Plan

### Day 1: Assessment & Quick Wins
```powershell
# 1. Get baseline
python -m tapps_agents.cli reviewer analyze-project --format json | Out-File reports/baseline.json -Encoding utf8

# 2. Auto-fix linting
python -m ruff check . --fix

# 3. Run quality workflow
python -m tapps_agents.cli workflow quality
```

**Expected:** +2-3 points (77.76 → 80-81/100)

---

### Day 2-3: Type Checking
```powershell
# Fix type hints in priority files
python -m tapps_agents.cli improver improve-quality tapps_agents/mcp/tool_registry.py --focus "Add type hints"
python -m tapps_agents.cli improver improve-quality tapps_agents/core/ast_parser.py --focus "Add type hints"
python -m tapps_agents.cli improver improve-quality tapps_agents/core/hardware_profiler.py --focus "Add type hints"
# ... (see full plan for all files)
```

**Expected:** +2-3 points (80-81 → 82-84/100)

---

### Day 3-5: Maintainability (Critical)
```powershell
# 1. Refactor CLI main function (212 complexity → <20 per function)
python -m tapps_agents.cli improver refactor tapps_agents/cli.py "Break down main() into smaller functions: extract argument parsing, command routing, result formatting"

# 2. Refactor high-complexity agent functions
python -m tapps_agents.cli improver refactor tapps_agents/agents/architect/agent.py "Break down _design_system() into smaller methods"
python -m tapps_agents.cli improver refactor tapps_agents/agents/designer/visual_designer.py "Break down refine_ui() into smaller methods"

# 3. Run maintenance workflow
python -m tapps_agents.cli workflow maintenance
```

**Expected:** +3-4 points (82-84 → 85-88/100)

---

### Day 5-7: Test Coverage
```powershell
# Generate tests for critical paths
python -m tapps_agents.cli tester test tapps_agents/agents/reviewer/scoring.py --focus "Test all scoring methods, edge cases, tool fallbacks"
python -m tapps_agents.cli tester test tapps_agents/agents/reviewer/report_generator.py --focus "Test JSON/Markdown/HTML generation"
python -m tapps_agents.cli tester test tapps_agents/cli.py --focus "Test command routing, argument parsing"
python -m tapps_agents.cli tester test tapps_agents/agents/reviewer/service_discovery.py --focus "Test service pattern matching"
```

**Expected:** +2-3 points (85-88 → 87-91/100)

---

### Day 7: Validation & CI/CD Setup
```powershell
# Final validation
python -m tapps_agents.cli reviewer analyze-project --format json | Out-File reports/final.json -Encoding utf8

# Set up pre-commit hooks
pip install pre-commit
pre-commit install
```

**Expected:** 90+/100 (Production-ready ✅)

---

## Key Commands Reference

### Assessment
```powershell
python -m tapps_agents.cli reviewer analyze-project --format json
python -m tapps_agents.cli reviewer report tapps_agents json markdown html --output-dir reports
```

### Fixes
```powershell
# Auto-fix linting
python -m ruff check . --fix

# Quality workflow
python -m tapps_agents.cli workflow quality

# Maintenance workflow
python -m tapps_agents.cli workflow maintenance

# Individual file improvements
python -m tapps_agents.cli improver improve-quality <file>
python -m tapps_agents.cli improver refactor <file> "<instructions>"
```

### Testing
```powershell
# Generate tests
python -m tapps_agents.cli tester test <file> --focus "<focus>"

# Run tests
pytest --cov=tapps_agents --cov-report=term-missing
```

### Validation
```powershell
# Re-score after changes
python -m tapps_agents.cli reviewer analyze-project --format json

# Check specific file
python -m tapps_agents.cli reviewer score <file>
```

---

## Success Criteria

✅ **Production-Ready:**
- Overall score ≥ 90/100
- Maintainability ≥ 7.0/10
- Test coverage ≥ 7.0/10
- Linting ≥ 7.0/10
- Type checking ≥ 7.0/10
- All tests passing
- Pre-commit hooks configured
- CI/CD quality gates configured

---

## Full Plan

See `PRODUCTION_READINESS_PLAN.md` for complete details, risk mitigation, and troubleshooting.

---

**Quick Start:** Run Day 1 commands to get started immediately!

