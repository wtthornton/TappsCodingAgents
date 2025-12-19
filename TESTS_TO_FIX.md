# Tests That Need Fixing or Enhancement

**Date**: 2025-01-XX  
**Status**: After MAL Removal - Unit Test Analysis  
**Total Tests**: 1923 collected, ~60+ failures identified

## Summary

After removing all MAL (Model Abstraction Layer) references from the codebase, the following tests need to be fixed or enhanced. Tests are categorized by whether they need fixing (test issue) or enhancement (test may be correct but needs improvement).

**Key Issues Identified:**
1. **Enhancer Agent Tests**: Tests mock `_stage_synthesis` to return string, but code expects dict with instruction structure
2. **CLI Tests**: JSON formatting tests failing - may be test expectations or actual code issues
3. **Parser Registration Tests**: Multiple parser registration tests failing - may be import/registration issues
4. **Context7 Analytics**: Dashboard tests failing - may be file path or data structure issues

## Tests Requiring Fixes

### Agent Tests

#### Debugger Agent
- `test_analyze_error_command_missing_error_message` - **FIXED**: Main code updated to make error_message optional (str | None)
- `test_debug_command_path_validation_error` - Test may need to verify path validation error handling

#### Enhancer Agent
- `test_enhance_command_success` - **FIXED**: Updated mock to return dict instead of string
- `test_enhance_command_with_output_file` - **FIXED**: Updated mock to return dict instead of string
- `test_enhance_quick_command_success` - Test needs to verify instruction object return
- `test_enhance_resume_command_success` - Test needs to verify instruction object return
- `test_create_session` - Test needs to verify session creation without MAL
- `test_stage_analysis` - Test needs to verify stage analysis without MAL
- `test_stage_requirements` - Test needs to verify stage requirements without MAL
- `test_stage_architecture` - Test needs to verify stage architecture without MAL
- `test_stage_codebase_context` - Test needs to verify codebase context without MAL
- `test_stage_quality` - Test needs to verify quality stage without MAL
- `test_stage_implementation` - Test needs to verify implementation stage without MAL
- `test_format_output_markdown` - Test needs to verify markdown formatting
- `test_format_output_json` - Test needs to verify JSON formatting

#### Implementer Agent
- `test_review_code_lazy_initialization` - Test needs to verify lazy initialization without MAL

#### Reviewer Agent
- `test_lint_command_file_not_found` - Test needs to verify file not found error handling
- `test_type_check_command_file_not_found` - Test needs to verify file not found error handling
- `test_analyze_project_command_success` - Test needs to verify project analysis
- `test_analyze_services_command_success` - Test needs to verify services analysis

#### Tester Agent
- `test_generate_e2e_tests_command_success` - Test needs to verify E2E test generation instruction
- `test_generate_e2e_tests_command_no_framework` - Test needs to verify no framework handling
- `test_generate_e2e_tests_command_method` - Test needs to verify E2E test method

#### Designer Agent
- All tests in `test_designer_agent.py` - **MAL REMOVED**: Tests need to be updated to work without MAL mocks. Tests expect certain result structures that may not match actual implementation.

#### Analyst Agent
- All tests in `test_analyst_agent.py` - **MAL REMOVED**: Tests need to be updated to work without MAL mocks. Tests expect certain result structures that may not match actual implementation.

#### Architect Agent
- All tests in `test_architect_agent.py` - **MAL REMOVED**: Tests need to be updated to work without MAL mocks. Tests expect certain result structures that may not match actual implementation.

### CLI Tests

#### CLI Base
- `test_format_output_json_dict` - Test needs to verify JSON dict formatting
- `test_format_output_json_string` - Test needs to verify JSON string formatting
- `test_format_error_output_json` - Test needs to verify JSON error formatting
- `test_format_error_output_json_with_details` - Test needs to verify JSON error with details
- `test_handle_agent_error_with_error_json` - Test needs to verify JSON error handling

#### CLI Commands
- `test_review_command_file_not_found` - Test needs to verify file not found handling
- `test_review_command_success_json` - Test needs to verify JSON success response
- `test_review_command_success_text` - Test needs to verify text success response
- `test_review_command_error_handling` - Test needs to verify error handling
- `test_score_command_file_not_found` - Test needs to verify file not found handling
- `test_score_command_success_json` - Test needs to verify JSON success response
- `test_hardware_profile_command_get` - Test needs to verify hardware profile get
- `test_hardware_profile_command_set` - Test needs to verify hardware profile set
- `test_hardware_profile_command_invalid_profile` - Test needs to verify invalid profile handling
- `test_score_command_shortcut` - Test needs to verify score command shortcut
- `test_doctor_command` - Test needs to verify doctor command
- `test_doctor_command_json` - Test needs to verify doctor command JSON output

#### CLI Parsers
- `test_reviewer_parser_aliases` - Test needs to verify parser aliases
- `test_planner_parser_registration` - Test needs to verify parser registration
- `test_implementer_parser_registration` - Test needs to verify parser registration
- `test_debugger_parser_registration` - Test needs to verify parser registration
- `test_analyst_parser_registration` - Test needs to verify parser registration
- `test_architect_parser_registration` - Test needs to verify parser registration
- `test_designer_parser_registration` - Test needs to verify parser registration
- `test_documenter_parser_registration` - Test needs to verify parser registration
- `test_enhancer_parser_registration` - Test needs to verify parser registration
- `test_improver_parser_registration` - Test needs to verify parser registration
- `test_ops_parser_registration` - Test needs to verify parser registration
- `test_orchestrator_parser_registration` - Test needs to verify parser registration

### Context7 Tests

#### Analytics Dashboard
- `test_analytics_dashboard_record_skill_usage` - Test needs to verify skill usage recording
- `test_analytics_dashboard_get_dashboard_metrics` - Test needs to verify dashboard metrics
- `test_analytics_dashboard_save_skill_usage` - Test needs to verify skill usage saving

### Cleanup Tests
- `test_cleanup_by_age` - Test timed out, may need timeout adjustment or fix

## Tests Requiring Enhancement

These tests may be passing but need improvement to better test the actual functionality:

1. **Instruction Object Tests** - Many tests that previously tested direct LLM calls should now test instruction object creation and properties
2. **Error Handling Tests** - Tests should verify proper error handling when instruction objects are returned
3. **Integration Tests** - Tests should verify the full flow from instruction creation to execution

## Notes

- All MAL-related code, documentation, and tests have been removed
- Tests should now verify instruction objects (`CodeGenerationInstruction`, `DocumentationInstruction`, `ErrorAnalysisInstruction`, `TestGenerationInstruction`) instead of direct LLM calls
- Agent tests should verify that agents return instruction objects, not direct results
- CLI tests should verify proper formatting and error handling of instruction objects

## Priority

1. **High Priority**: Tests that prevent test suite from running (import errors, critical failures)
2. **Medium Priority**: Tests that verify core functionality (agent commands, instruction objects)
3. **Low Priority**: Tests that verify edge cases and error handling
