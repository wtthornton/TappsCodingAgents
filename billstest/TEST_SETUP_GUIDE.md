# Billstest Test Setup Guide

This guide ensures the TappsCodingAgents project is ready to execute, fix, and enhance tests in billstest.

## ✅ Current Status Check

### Framework Installation
- **Status**: ✅ Installed (Version 2.0.1)
- **Location**: `C:\cursor\TappsCodingAgents\tapps_agents\`
- **Verification**: 
  ```powershell
  python -c "import tapps_agents; print(tapps_agents.__version__)"
  ```

### Configuration Files
- **Config**: ✅ `.tapps-agents/config.yaml` exists
- **Cursor Rules**: ✅ `.cursor/rules/` exists
- **Cursor Skills**: ✅ `.claude/skills/` exists (if initialized)

### Dependencies
- **Core**: ✅ All installed (pydantic, httpx, pyyaml, aiohttp, psutil)
- **Testing**: ✅ All installed (pytest, pytest-asyncio, pytest-cov, pytest-mock, pytest-timeout, pytest-xdist)
- **Code Quality**: ✅ All installed (black, ruff, mypy, bandit, radon, coverage)

## 🔧 Setup Steps

### 1. Verify Framework Installation

```powershell
# From TappsCodingAgents root directory
cd C:\cursor\TappsCodingAgents

# Check if framework is installed
python -c "import tapps_agents; print(f'Version: {tapps_agents.__version__}')"

# If not installed or need to update after code changes:
pip install -e .
```

**When to reinstall:**
- ✅ After modifying code in `tapps_agents/`
- ✅ After updating dependencies in `pyproject.toml` or `requirements.txt`
- ✅ After adding new agents or CLI commands
- ✅ If getting "module not found" errors

### 2. Verify Project Initialization

```powershell
# Check if config exists
Test-Path .tapps-agents\config.yaml

# Check if Cursor Rules exist
Test-Path .cursor\rules

# If missing, initialize (from root directory):
python -m tapps_agents.cli init
```

**Note**: Billstest uses the **root project's initialization files**, not its own. The `init` command should be run from the root `TappsCodingAgents` directory.

### 3. Verify Test Dependencies

```powershell
# Check pytest and plugins
python -m pytest --version

# Check all test dependencies
pip list | Select-String -Pattern "pytest|httpx|pydantic|aiohttp"

# Install missing dependencies (if needed)
pip install -r requirements.txt
```

### 4. Verify Test Discovery

```powershell
# From billstest directory
cd C:\cursor\TappsCodingAgents\billstest

# Test discovery (should find tests)
python -m pytest --collect-only

# Run a quick unit test
python -m pytest tests/unit/test_analyst_agent.py::TestAnalystAgent::test_help -v
```

## 🧪 Running Tests

### Unit Tests (Fast, Mocked)

```powershell
cd C:\cursor\TappsCodingAgents\billstest

# Run all unit tests
python -m pytest tests/unit/ -v

# Run specific test file
python -m pytest tests/unit/agents/test_analyst_agent.py -v

# Run with coverage
python -m pytest tests/unit/ --cov=tapps_agents --cov-report=html
```

### Integration Tests (Real LLM, Optional)

```powershell
# Run integration tests (requires LLM service)
python -m pytest tests/integration/ -m integration -v

# Run only real LLM tests
python -m pytest tests/integration/ -m requires_llm -v

# Skip real LLM tests (use mocks)
python -m pytest tests/integration/ -m "integration and not requires_llm" -v
```

### Test Markers

Tests are organized with pytest markers:
- `@pytest.mark.unit` - Fast unit tests (mocked)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.requires_llm` - Requires LLM service (auto-skips if unavailable)
- `@pytest.mark.requires_context7` - Requires Context7 API (auto-skips if unavailable)
- `@pytest.mark.e2e` - End-to-end workflow tests

## 🔍 Troubleshooting

### Issue: "Module not found" errors

**Solution:**
```powershell
cd C:\cursor\TappsCodingAgents
pip install -e .
```

### Issue: "Config not found" errors

**Solution:**
```powershell
cd C:\cursor\TappsCodingAgents
python -m tapps_agents.cli init
```

### Issue: Tests fail with import errors

**Solution:**
1. Verify Python path includes parent directory (billstest/pytest.ini sets `pythonpath = ..`)
2. Reinstall framework: `pip install -e .`
3. Check Python version: `python --version` (should be 3.13+)

### Issue: CLI command not found

**Solution:**
```powershell
# Reinstall to register CLI command
cd C:\cursor\TappsCodingAgents
pip install -e .

# Or use Python module directly:
python -m tapps_agents.cli --help
```

### Issue: Tests are slow

**Solution:**
- Use unit tests for development: `pytest tests/unit/`
- Run integration tests selectively: `pytest tests/integration/ -m requires_llm`
- Use pytest-xdist for parallel execution: `pytest tests/unit/ -n auto`

## 📋 Pre-Flight Checklist

Before running tests, verify:

- [ ] Framework installed: `python -c "import tapps_agents"`
- [ ] Config exists: `Test-Path .tapps-agents\config.yaml`
- [ ] Pytest installed: `python -m pytest --version`
- [ ] Test discovery works: `pytest --collect-only` (from billstest directory)
- [ ] At least one unit test passes: `pytest tests/unit/test_analyst_agent.py::TestAnalystAgent::test_help -v`

## 🚀 Optional: LLM Services for Integration Tests

### Ollama (Recommended for Testing)

```powershell
# Install Ollama: https://ollama.ai
# Pull a coding model
ollama pull qwen2.5-coder:7b

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

### Anthropic API

```powershell
$env:ANTHROPIC_API_KEY="your-key-here"
```

### OpenAI API

```powershell
$env:OPENAI_API_KEY="your-key-here"
```

### Context7 (Optional)

```powershell
$env:CONTEXT7_API_KEY="your-key-here"
```

**Note**: Integration tests automatically skip if services are unavailable, so these are optional.

## 📊 Test Structure

```
billstest/
├── tests/
│   ├── unit/              # Fast, mocked tests (105+ files)
│   │   ├── agents/        # All 13 agents tested
│   │   ├── cli/           # CLI tests
│   │   ├── workflow/      # Workflow tests
│   │   ├── context7/      # Context7 tests
│   │   └── ...
│   └── integration/       # Real-world tests (16 files)
│       ├── test_mal_real.py
│       ├── test_reviewer_agent_real.py
│       ├── test_e2e_workflow_real.py
│       └── ...
├── pytest.ini            # Test configuration
└── conftest.py           # Shared fixtures
```

## 🛠️ Enhancing Tests

### Adding New Unit Tests

1. Create test file in `tests/unit/` following naming: `test_<component>_<scenario>.py`
2. Use `@pytest.mark.unit` marker
3. Use fixtures from `conftest.py` (mock_mal, sample_python_code, etc.)
4. Keep tests fast (< 1 second each)

### Adding New Integration Tests

1. Create test file in `tests/integration/`
2. Use `@pytest.mark.integration` marker
3. Use `@pytest.mark.requires_llm` if LLM needed (auto-skips if unavailable)
4. Document requirements in test docstring

### Test Best Practices

- **Unit tests**: Fast, isolated, mocked, deterministic
- **Integration tests**: Real services, comprehensive, may be slower
- **Mark tests appropriately**: Use markers for filtering
- **Document requirements**: State what services are needed
- **Handle flakiness**: Real services may have transient failures

## 📈 CI/CD Considerations

For CI/CD pipelines:

1. **Always run unit tests**: Fast, reliable, no external dependencies
2. **Run integration tests selectively**:
   - Scheduled runs (nightly)
   - Pre-release validation
   - Manual trigger
   - Separate job with LLM service available

```powershell
# CI: Fast unit tests only
pytest tests/unit/ -v

# Pre-release: All tests including real LLM
pytest tests/ -m "unit or (integration and requires_llm)" -v
```

## ✅ Verification Commands

Run these to verify everything is set up correctly:

```powershell
# 1. Framework installed
python -c "import tapps_agents; print('✅ Framework installed')"

# 2. Config exists
Test-Path .tapps-agents\config.yaml

# 3. Pytest works
python -m pytest --version

# 4. Test discovery works
cd billstest
python -m pytest --collect-only -q

# 5. Unit test passes
python -m pytest tests/unit/test_analyst_agent.py::TestAnalystAgent::test_help -v
```

## 📚 Additional Resources

- **README**: `billstest/README.md` - Comprehensive billstest documentation
- **Installation Status**: `billstest/INSTALLATION_STATUS.md` - Current setup status
- **Real Tests Guide**: `billstest/tests/integration/README_REAL_TESTS.md`
- **Framework Docs**: `docs/` directory in root project

---

**Last Updated**: January 2025  
**Framework Version**: 2.0.1  
**Python Version**: 3.13+

