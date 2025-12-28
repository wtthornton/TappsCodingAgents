# Test Suite Fix Plan

## Summary
20 tests in `test_all_commands.py` are failing due to missing fixtures (`cli_harness`, `test_project`, `test_file`). These function-based tests need to be converted to use the `CLICommandTestBase` class approach.

## Failed Tests

### Reviewer Agent (5 tests)
1. `test_reviewer_lint_command` - Line 71
2. `test_reviewer_type_check_command` - Line 81
3. `test_reviewer_security_scan_command` - Line 92
4. `test_reviewer_duplication_command` - Line 103
5. `test_reviewer_report_command` - Line 115

### Planner Agent (3 tests)
6. `test_planner_plan_command` - Line 129
7. `test_planner_create_story_command` - Line 140
8. `test_planner_list_stories_command` - Line 151

### Implementer Agent (3 tests)
9. `test_implementer_implement_command` - Line 166
10. `test_implementer_refactor_command` - Line 178
11. `test_implementer_generate_code_command` - Line 189

### Tester Agent (3 tests)
12. `test_tester_test_command` - Line 204
13. `test_tester_generate_tests_command` - Line 215
14. `test_tester_run_tests_command` - Line 226

### Debugger Agent (2 tests)
15. `test_debugger_debug_command` - Line 241
16. `test_debugger_analyze_error_command` - Line 252

### Documenter Agent (3 tests)
17. `test_documenter_document_command` - Line 267
18. `test_documenter_generate_docs_command` - Line 278 (duplicate function name at line 289)
19. `test_documenter_update_readme_command` - Line 300

### Analyst Agent (1 test)
20. `test_analyst_gather_requirements_command` - Line 315

## Root Cause
Function-based tests are using fixtures that don't exist:
- `cli_harness` - Should use `self.cli_harness` from `CLICommandTestBase`
- `test_project` - Should use `self.test_project` from `CLICommandTestBase`
- `test_file` - Should use `self.get_test_file()` from `CLICommandTestBase`

## Solution
Convert all function-based tests to class-based tests using `CLICommandTestBase`.

### Conversion Pattern

**Before (Function-based):**
```python
@pytest.mark.e2e_cli
def test_reviewer_lint_command(cli_harness, test_project, test_file):
    """Test reviewer lint command."""
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "reviewer", "lint", str(test_file), "--format", "json"],
        cwd=test_project,
    )
    assert_success(result)
```

**After (Class-based):**
```python
@pytest.mark.e2e_cli
class TestReviewerCommandsLegacy(CLICommandTestBase):
    """Legacy reviewer command tests."""
    
    def test_reviewer_lint_command(self):
        """Test reviewer lint command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "lint", str(test_file), "--format", "json"]
        )
        assert_success_exit(result)
```

## Fix Steps

1. **Group tests by agent** - Create class-based test classes for each agent
2. **Convert function signatures** - Remove fixture parameters, add `self`
3. **Update method calls**:
   - `cli_harness.run_command(...)` → `self.run_command(...)`
   - `test_project` → `self.test_project`
   - `test_file` → `self.get_test_file()`
   - `assert_success(result)` → `assert_success_exit(result)` (from validation_helpers)
4. **Fix duplicate function name** - Line 289 has duplicate `test_documenter_generate_docs_command`
5. **Update imports** - Ensure `assert_success_exit` is imported from `validation_helpers`

## Additional Issues to Fix

1. **Missing import** - Add `assert_success_exit` import (currently using `assert_success` which doesn't exist)
2. **Duplicate function** - Line 289 has duplicate function name `test_documenter_generate_docs_command`
3. **Timeout handling** - Line 111 checks for exit code 124 (timeout), but should use `result.timed_out` attribute

## Testing After Fix

Run:
```bash
pytest tests/e2e/cli/test_all_commands.py -m e2e_cli -v
```

Expected: All 20 tests should pass (or gracefully handle network errors with exit codes 0 or 1).

