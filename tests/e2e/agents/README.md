# E2E Agent Behavior Tests

Comprehensive E2E tests that validate actual agent behavior (command parsing, response generation, error handling) rather than just checking that agents can be activated and mocks can be called.

## Overview

These tests validate:
- **Command Processing**: Command parsing, validation, parameter handling, help output
- **Response Generation**: Response appropriateness, formatting, content completeness, contextual appropriateness
- **Error Handling**: Invalid input, missing files, network errors, permission errors, error message quality
- **Agent-Specific Behavior**: Planner plans, Implementer code, Reviewer reviews, Tester tests
- **Workflow Context**: Agent behavior during workflow execution, context reception, artifact production

## Test Structure

### Test Files

- `test_agent_command_processing.py` - Command parsing and validation tests
- `test_agent_response_generation.py` - Response generation and formatting tests
- `test_agent_error_handling.py` - Error handling and error message tests
- `test_agent_specific_behavior.py` - Agent-specific functionality tests
- `test_agent_behavior_in_workflows.py` - Agent behavior in workflow context (in `tests/e2e/workflows/`)

### Test Helpers

Test utilities are provided in `tests/e2e/fixtures/agent_test_helpers.py`:

- `create_test_agent()` - Create test agent instances with mocked MAL
- `execute_command()` - Execute commands on agents
- `assert_command_parsed()` - Validate command parsing
- `assert_error_message()` - Validate error messages
- `validate_response_structure()` - Validate response structure
- `validate_response_content()` - Validate response content
- `validate_plan_structure()` - Validate plan structure
- `validate_code_quality()` - Validate code quality
- `validate_review_feedback()` - Validate review feedback
- And more...

## Running Tests

### Run All Agent Behavior Tests

```bash
pytest tests/e2e/agents/ -m e2e
```

### Run Specific Test File

```bash
pytest tests/e2e/agents/test_agent_command_processing.py -m e2e
```

### Run Tests for Specific Agent Type

```bash
pytest tests/e2e/agents/ -m e2e -k "planner"
```

## Test Patterns

### Command Processing Tests

Tests validate:
- Star-prefixed commands (`*review file.py`)
- Numbered commands (`1`, `2`, etc.)
- Space-separated commands (`review file.py`)
- Argument extraction
- Invalid command rejection
- Parameter validation
- Help output structure

Example:
```python
async def test_star_prefixed_command_parsing(self, e2e_project, mock_mal, agent_type):
    agent = create_test_agent(agent_type, mock_mal)
    await agent.activate(e2e_project)
    
    parsed = agent.parse_command("*review test_file.py")
    assert_command_parsed(parsed, "review", {"file": "test_file.py"})
```

### Response Generation Tests

Tests validate:
- Response structure (required fields)
- Response formatting
- Response content completeness
- Contextual appropriateness
- Response quality metrics

Example:
```python
async def test_response_structure(self, e2e_project, mock_mal, agent_type, command, expected_fields):
    agent = create_test_agent(agent_type, mock_mal)
    await agent.activate(e2e_project)
    
    result = await execute_command(agent, command, description="test")
    validate_response_structure(result, expected_fields)
```

### Error Handling Tests

Tests validate:
- Invalid input handling
- Missing file handling
- Network error handling (mocked)
- Permission error handling
- Error message clarity and actionability
- Error recovery

Example:
```python
async def test_missing_file_path_handling(self, e2e_project, mock_mal, tmp_path):
    agent = create_test_agent("reviewer", mock_mal)
    await agent.activate(e2e_project)
    
    missing_file = create_missing_file_scenario(tmp_path / "nonexistent.py")
    result = await execute_command(agent, "*review", file=str(missing_file))
    
    if "error" in result:
        validate_error_response(result, "file")
        assert_error_message_quality(str(result["error"]), {"clear": True, "context": True})
```

### Agent-Specific Behavior Tests

Tests validate:
- **Planner**: Plan creation, structure, completeness
- **Implementer**: Code generation, syntax, standards
- **Reviewer**: Review feedback, quality assessments, gate evaluation
- **Tester**: Test generation, execution, results

Example:
```python
async def test_plan_structure_components(self, e2e_project, mock_mal):
    agent = create_test_agent("planner", mock_mal)
    await agent.activate(e2e_project)
    
    result = await execute_command(agent, "*plan", description="Implement a REST API")
    
    if "error" not in result and "plan" in result:
        validate_plan_structure(result["plan"], ["task", "overview", "requirement"])
```

### Workflow Context Tests

Tests validate:
- Agents receive correct context from workflow
- Agents produce artifacts that workflow expects
- Agents handle workflow-specific errors
- Agents integrate correctly with workflow state

Example:
```python
async def test_agents_receive_project_context(self, e2e_project, mock_mal, tmp_path):
    workflow_yaml = tmp_path / "test_workflow.yaml"
    # ... create workflow ...
    
    runner = WorkflowRunner(e2e_project, use_mocks=True)
    workflow = runner.load_workflow(workflow_yaml)
    
    agent = create_test_agent(step.agent, mock_mal)
    await agent.activate(e2e_project)
    
    validate_agent_context(agent, workflow_state, step_context)
```

## Behavioral Mocks

Tests use behavioral mocks from `tests/e2e/fixtures/mock_agents.py` that simulate realistic agent behavior:
- Command parsing and validation
- Response generation based on input
- Error handling and edge cases
- Agent-specific behavior (planner plans, implementer implements, reviewer reviews)

## Windows Compatibility

All tests are Windows-compatible:
- Use `pathlib.Path` for file operations
- No shell commands
- Proper path handling for Windows paths

## Test Markers

Tests use the following markers:
- `@pytest.mark.e2e` - E2E test marker
- `@pytest.mark.template_type("minimal")` - Uses minimal project template
- `@pytest.mark.asyncio` - Async test marker
- `@pytest.mark.parametrize` - Parameterized tests for multiple agent types

## Integration with E2E Foundation

These tests integrate with:
- E2E harness from Epic 8 (`tests/e2e/fixtures/e2e_harness.py`)
- Project templates (`tests/e2e/fixtures/project_templates.py`)
- Workflow runner from Epic 9 (`tests/e2e/fixtures/workflow_runner.py`)
- Behavioral mocks (`tests/e2e/fixtures/mock_agents.py`)

## Success Criteria

Tests validate that:
- ✅ Agents correctly parse and validate commands
- ✅ Agents generate appropriate, well-formatted responses
- ✅ Agents handle errors gracefully with clear messages
- ✅ Agents perform agent-specific functionality correctly
- ✅ Agents integrate properly with workflow execution

## Related Documentation

- [E2E Test Review](../E2E_TEST_REVIEW.md) - Original review that identified gaps
- [Epic 15 Documentation](../../../implementation/cursor/EPIC_15_E2E_Agent_Behavior_Testing.md) - Epic definition
- [E2E README](../README.md) - General E2E test documentation

