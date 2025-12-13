# Real Integration Tests

These tests use **ACTUAL LLM calls** and external services, not mocks.

## Requirements

### For Ollama Tests
- Ollama must be running locally: `http://localhost:11434`
- At least one model installed (e.g., `qwen2.5-coder:7b`)

### For Anthropic Tests
- Set environment variable: `ANTHROPIC_API_KEY=your-key-here`

### For OpenAI Tests
- Set environment variable: `OPENAI_API_KEY=your-key-here`

## Running Real Integration Tests

### Run All Real Integration Tests
```bash
# Run all integration tests (including real LLM tests)
pytest tests/integration/ -m "integration and requires_llm" -v

# Or run specific test files
pytest tests/integration/test_mal_real.py -v
pytest tests/integration/test_reviewer_agent_real.py -v
pytest tests/integration/test_cli_real.py -v
pytest tests/integration/test_e2e_workflow_real.py -v
```

### Run Only Real LLM Tests
```bash
pytest tests/integration/ -m requires_llm -v
```

### Skip Real LLM Tests (Use Mocks)
```bash
# Run integration tests but skip real LLM tests
pytest tests/integration/ -m "integration and not requires_llm" -v
```

## Test Files

### `test_mal_real.py`
- Tests MAL with actual Ollama/Anthropic/OpenAI calls
- Tests provider switching and fallback
- Tests performance and concurrent requests

### `test_reviewer_agent_real.py`
- Tests Reviewer Agent with real LLM calls
- Tests code review and scoring with actual LLM
- Tests error handling with real services

### `test_cli_real.py`
- Tests CLI commands with real agents and LLM
- Tests subprocess execution of CLI
- Tests error handling

### `test_e2e_workflow_real.py`
- End-to-end workflow tests
- Complete agent workflows from start to finish
- Multiple file processing

## Automatic Skipping

Tests marked with `@pytest.mark.requires_llm` will automatically be skipped if:
- No LLM service is available
- Ollama is not running
- No API keys are set

This allows the test suite to run successfully even without LLM services available.

## CI/CD Considerations

In CI/CD pipelines:
1. **Unit tests** (mocked) - Always run, fast
2. **Integration tests** (mocked) - Run on every commit
3. **Real integration tests** (actual LLM) - Run on:
   - Scheduled runs (nightly)
   - Pre-release
   - Manual trigger
   - Separate job with LLM service available

## Performance

Real integration tests are **much slower** than mocked tests:
- Mocked tests: ~0.1-1 second each
- Real LLM tests: ~5-30 seconds each (depending on LLM response time)

## Best Practices

1. **Use real tests sparingly** - Only for critical paths
2. **Use mocks for development** - Faster feedback
3. **Run real tests before release** - Verify actual functionality
4. **Monitor test duration** - Real tests can be slow
5. **Handle flakiness** - Real services may have transient failures

