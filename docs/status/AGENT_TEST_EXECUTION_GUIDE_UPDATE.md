# Agent Test Execution Guide - Updates

**Date**: 2025-01-15  
**Status**: ✅ Complete

---

## Summary

Updated documentation and code to ensure agents know how to run unit tests efficiently using parallel execution.

---

## Changes Made

### 1. ✅ Updated Tester Agent SKILL.md

**File**: `.claude/skills/tester/SKILL.md`

**Added Section**: "Running Unit Tests (For Agents)"

**Key Instructions**:
- Always use parallel execution: `python -m pytest tests/ -m unit -n auto`
- Use unit test marker (`-m unit`) to run only fast unit tests
- Sequential mode only for debugging test isolation issues
- Performance expectations: 5-10x faster with parallel execution

**Impact**: Agents using the Tester Skill will see clear instructions on how to run tests efficiently.

---

### 2. ✅ Updated Tester Agent Code

**File**: `tapps_agents/agents/tester/agent.py`

**Changes**:
- Modified `_run_pytest()` method to use parallel execution (`-n auto`)
- When running all tests (no specific path): Uses `-m unit -n auto` (unit tests only, parallel)
- When running specific test path: Uses `-n auto` (parallel, but allows any test type)

**Code Changes**:
```python
# Before
cmd: list[str] = ["pytest", "-v"]

# After
cmd: list[str] = ["pytest", "-v"]
if not test_path:
    cmd.extend(["-m", "unit", "-n", "auto"])  # All tests: unit only, parallel
else:
    cmd.extend(["-n", "auto"])  # Specific path: parallel, any test type
```

**Impact**: The Tester Agent now automatically uses parallel execution when running tests via `*run-tests` command.

---

### 3. ✅ Updated Developer Guide

**File**: `docs/DEVELOPER_GUIDE.md`

**Added Section**: "Running Tests (For Agents)"

**Content**:
- Recommended commands for parallel execution
- Key points about `-n auto` and `-m unit` flags
- Performance expectations
- Note about Tester Agent automatic parallel execution
- Link to Test Performance Guide

**Impact**: Developers and agents have clear guidance on how to run tests efficiently.

---

## Agent Test Execution Guidelines

### For Agents Running Tests Directly

**Recommended Command**:
```bash
python -m pytest tests/ -m unit -n auto
```

**Key Flags**:
- `-m unit`: Run only unit tests (faster, excludes integration/e2e)
- `-n auto`: Parallel execution using all CPU cores (5-10x faster)
- `--cov=tapps_agents`: Add coverage when needed

**Examples**:
```bash
# All unit tests (parallel)
python -m pytest tests/ -m unit -n auto

# Specific test file (parallel)
python -m pytest tests/unit/test_file.py -n auto

# With coverage (parallel)
python -m pytest tests/ -m unit -n auto --cov=tapps_agents --cov-report=term

# Sequential (debugging only)
python -m pytest tests/ -m unit  # No -n flag
```

### For Agents Using Tester Agent

The Tester Agent (`*run-tests` command) now automatically:
- Uses parallel execution (`-n auto`)
- Uses unit test marker when running all tests (`-m unit`)
- Allows any test type when a specific path is provided

**No changes needed** - the agent handles optimization automatically.

---

## Performance Impact

### Before Updates
- Tests run sequentially (slow)
- No guidance for agents on optimal test execution
- Tester Agent didn't use parallel execution

### After Updates
- ✅ Tester Agent uses parallel execution automatically
- ✅ Clear documentation for agents running tests directly
- ✅ 5-10x faster test execution expected

---

## Documentation Structure

```
.claude/skills/tester/SKILL.md
  └─> "Running Unit Tests (For Agents)" section
       └─> Clear instructions with examples

docs/DEVELOPER_GUIDE.md
  └─> "Running Tests (For Agents)" section
       └─> Comprehensive guide with performance notes

tapps_agents/agents/tester/agent.py
  └─> _run_pytest() method
       └─> Automatic parallel execution
```

---

## Verification

✅ Tester Agent SKILL.md updated with test execution guidelines  
✅ Tester Agent code updated to use parallel execution  
✅ Developer Guide updated with agent test execution section  
✅ No linting errors  
✅ Consistent messaging across all documentation  

---

## Related Documentation

- `docs/TEST_PERFORMANCE_GUIDE.md` - Complete test performance optimization guide
- `TEST_PERFORMANCE_ANALYSIS.md` - Detailed analysis of performance issues
- `TEST_PERFORMANCE_FIXES_APPLIED.md` - Summary of performance fixes

---

**Update Complete**: 2025-01-15  
**Files Updated**: 3  
**Status**: ✅ Ready for Use

