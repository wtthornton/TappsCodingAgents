# Billstest - Real-World Testing Suite for TappsCodingAgents

**Billstest** is a comprehensive, real-world testing and example project for the **TappsCodingAgents** framework. Unlike unit tests that use mocks, billstest contains **100% real-world integration tests** that exercise the full framework with actual LLM calls, external services, and complete workflows.

## 🎯 Purpose

Billstest serves as:

1. **Real-World Test Suite** - Integration tests that verify TappsCodingAgents works end-to-end with actual services
2. **Example Project** - Demonstrates how to use TappsCodingAgents in a real project
3. **Validation Environment** - Tests all 13 agents, workflows, CLI commands, and framework features
4. **Documentation by Example** - Shows best practices and usage patterns

## 📁 Project Structure

```
billstest/
├── docs/                    # Comprehensive documentation
├── tests/
│   ├── unit/               # Unit tests (mocked, fast)
│   │   ├── agents/         # Tests for all 13 agents
│   │   ├── cli/            # CLI parser and command tests
│   │   ├── workflow/       # Workflow component tests
│   │   ├── quality/       # Quality gate tests
│   │   └── ...
│   └── integration/        # Real-world integration tests
│       ├── test_mal_real.py              # Real LLM calls
│       ├── test_reviewer_agent_real.py   # Real agent execution
│       ├── test_e2e_workflow_real.py     # End-to-end workflows
│       ├── test_cli_real.py              # Real CLI execution
│       ├── test_context7_real.py         # Context7 integration
│       └── test_multi_agent_integration.py # Multi-agent workflows
├── workflows/              # Example workflow definitions
│   ├── presets/           # Workflow presets (full-sdlc, rapid-dev, etc.)
│   └── *.yaml             # Custom workflow examples
└── .tapps-agents/         # Framework artifacts and state
```

## 🚀 Getting Started

### Prerequisites

1. **Python 3.13+** (recommended: latest stable)
2. **TappsCodingAgents installed** (see [Installation](#installation))
3. **LLM Service** (one of):
   - **Ollama** (local, recommended for testing)
   - **Anthropic API** (set `ANTHROPIC_API_KEY`)
   - **OpenAI API** (set `OPENAI_API_KEY`)
4. **Context7** (optional, for knowledge base tests - set `CONTEXT7_API_KEY`)

### Installation

Billstest is a subdirectory within the TappsCodingAgents project and uses the root project's initialization. The framework should already be set up:

```bash
# From the TappsCodingAgents root directory
cd C:\cursor\TappsCodingAgents

# Install/update the framework in development mode (if needed)
pip install -e .
```

**Initialization:** Billstest does **NOT** need its own `init` command. It uses the root project's initialization files:
- Root `.tapps-agents/config.yaml` - Framework configuration
- Root `.cursor/rules/` - Cursor Rules for AI context
- Root `.claude/skills/` - Cursor Skills for agent capabilities

### When to Reinstall or Re-Initialize

You should **reinstall** (`pip install -e .`) when:
- ✅ You've modified framework code in `tapps_agents/`
- ✅ You've updated dependencies in `pyproject.toml` or `requirements.txt`
- ✅ You've added new agents or CLI commands
- ✅ You're getting "module not found" or import errors
- ✅ Framework changes aren't being picked up

You should **re-run init** (`python -m tapps_agents.cli init` from **root directory**) when:
- ✅ You've updated Cursor Rules (`.cursor/rules/`)
- ✅ You've updated Cursor Skills (`.claude/skills/`)
- ✅ You've updated workflow presets (`workflows/presets/`)

**Note:** Init should be run from the **root TappsCodingAgents directory**, not from billstest. Billstest uses the root's initialization files.
- ✅ You've modified the init templates
- ✅ Configuration files are missing or outdated
- ✅ You want to refresh project setup

**Quick Check:**
```bash
# Check if framework is installed
python -c "import tapps_agents; print(tapps_agents.__version__)"

# Check if init has been run
ls .tapps-agents/config.yaml  # Should exist
ls .cursor/rules/              # Should exist
ls .claude/skills/             # Should exist
```

**Recommended Workflow:**
1. Make changes to TappsCodingAgents framework
2. Reinstall: `pip install -e .` (from parent directory)
3. Re-run init: `python -m tapps_agents.cli init` (from billstest directory)
4. Run tests to verify: `pytest tests/unit/ -v`

### Verify Installation

```bash
# Check CLI is available
tapps-agents --help

# Run doctor to validate environment
tapps-agents doctor

# Run a quick unit test (fast, no LLM required)
pytest tests/unit/agents/test_analyst_agent.py -v
```

## 🧪 Running Tests

### Unit Tests (Fast, Mocked)

Unit tests use mocks and run quickly without external services:

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/agents/test_analyst_agent.py -v

# Run with coverage
pytest tests/unit/ --cov=tapps_agents --cov-report=html
```

### Integration Tests (Real-World, Requires LLM)

Integration tests use **actual LLM calls** and external services:

```bash
# Run all integration tests (requires LLM)
pytest tests/integration/ -m integration -v

# Run only real LLM tests
pytest tests/integration/ -m requires_llm -v

# Run specific real test
pytest tests/integration/test_mal_real.py -v
pytest tests/integration/test_reviewer_agent_real.py -v
pytest tests/integration/test_e2e_workflow_real.py -v

# Skip real LLM tests (use mocks)
pytest tests/integration/ -m "integration and not requires_llm" -v
```

### Test Markers

Tests are organized with pytest markers:

- `@pytest.mark.unit` - Fast unit tests (mocked)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.requires_llm` - Requires LLM service (Ollama/Anthropic/OpenAI)
- `@pytest.mark.requires_context7` - Requires Context7 API
- `@pytest.mark.e2e` - End-to-end workflow tests

### Automatic Skipping

Tests marked with `@pytest.mark.requires_llm` automatically skip if:
- No LLM service is available
- Ollama is not running
- No API keys are set

This allows the test suite to run successfully even without LLM services.

## 📊 Test Coverage

Billstest provides comprehensive coverage:

### Agents (13/13 tested)
- ✅ Analyst Agent
- ✅ Planner Agent
- ✅ Architect Agent
- ✅ Designer Agent
- ✅ Implementer Agent
- ✅ Reviewer Agent
- ✅ Tester Agent
- ✅ Debugger Agent
- ✅ Documenter Agent
- ✅ Improver Agent
- ✅ Ops Agent
- ✅ Orchestrator Agent
- ✅ Enhancer Agent

### Framework Components
- ✅ CLI parsers and commands
- ✅ Workflow execution and orchestration
- ✅ Artifact management
- ✅ Quality gates (coverage, security, scoring)
- ✅ Context7 integration
- ✅ Multi-agent workflows
- ✅ Background agents
- ✅ Expert system

## 🔧 Configuration

### LLM Setup

#### Option 1: Ollama (Recommended for Testing)

```bash
# Install Ollama (if not already installed)
# https://ollama.ai

# Pull a coding model
ollama pull qwen2.5-coder:7b

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

#### Option 2: Anthropic API

```bash
# Set API key
export ANTHROPIC_API_KEY=your-key-here
# Windows PowerShell:
$env:ANTHROPIC_API_KEY="your-key-here"
```

#### Option 3: OpenAI API

```bash
# Set API key
export OPENAI_API_KEY=your-key-here
# Windows PowerShell:
$env:OPENAI_API_KEY="your-key-here"
```

### Context7 Setup (Optional)

```bash
# Set Context7 API key for knowledge base tests
export CONTEXT7_API_KEY=your-key-here
# Windows PowerShell:
$env:CONTEXT7_API_KEY="your-key-here"
```

## 📝 Example Workflows

Billstest includes example workflows in `workflows/`:

### Preset Workflows

```bash
# Run full SDLC workflow
tapps-agents workflow full

# Run rapid development workflow
tapps-agents workflow rapid

# Run maintenance/refactor workflow
tapps-agents workflow fix

# Run quality improvement workflow
tapps-agents workflow quality

# Run quick fix workflow
tapps-agents workflow hotfix
```

### Custom Workflows

See `workflows/` directory for custom workflow examples:
- `example-feature-development.yaml` - Standard feature development
- `multi-agent-refactor.yaml` - Multi-agent refactoring
- `multi-agent-review-and-test.yaml` - Review and test workflow
- `prompt-enhancement.yaml` - Prompt enhancement workflow

## 🏗️ Using Billstest as a Template

Billstest can serve as a template for your own TappsCodingAgents projects:

1. **Copy the structure** - Use billstest as a starting point
2. **Customize workflows** - Modify or create your own workflows
3. **Add your tests** - Extend the test suite for your use cases
4. **Configure agents** - Set up your expert system and knowledge bases

## 🔍 Understanding Test Results

### Unit Tests
- **Fast** (~0.1-1 second each)
- **Isolated** - No external dependencies
- **Deterministic** - Same results every run
- **Mocked** - Uses mocks for external services

### Integration Tests
- **Slower** (~5-30 seconds each, depending on LLM)
- **Real** - Uses actual LLM calls and services
- **Comprehensive** - Tests end-to-end functionality
- **May be flaky** - Real services may have transient failures

### Test Output

```
✅ PASSED - Test succeeded
❌ FAILED - Test failed (check error message)
⏭️ SKIPPED - Test skipped (missing dependencies)
⚠️ ERROR - Test error (setup/teardown issue)
```

## 🐛 Troubleshooting

### Tests Fail with "LLM not available"
- Ensure Ollama is running: `ollama list`
- Or set API keys: `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
- Tests will auto-skip if no LLM is available

### "Module not found" errors
- Reinstall framework: `pip install -e .` (from parent directory)
- Check Python path: `python -c "import tapps_agents; print(tapps_agents.__file__)"`

### "Config not found" errors
- Run init: `python -m tapps_agents.cli init`
- Check `.tapps-agents/config.yaml` exists

### Tests are slow
- Use unit tests for development: `pytest tests/unit/`
- Run integration tests only when needed: `pytest tests/integration/ -m requires_llm`

## 📚 Documentation

Comprehensive documentation is available in `docs/`:

- **[README_REAL_TESTS.md](tests/integration/README_REAL_TESTS.md)** - Real integration test guide
- **[README_CONTEXT7_REAL_TESTS.md](tests/integration/README_CONTEXT7_REAL_TESTS.md)** - Context7 test guide
- **[API.md](docs/API.md)** - API reference
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture
- **[WORKFLOW_SELECTION_GUIDE.md](docs/WORKFLOW_SELECTION_GUIDE.md)** - Workflow guide

## 🤝 Contributing

When adding new tests:

1. **Unit tests** go in `tests/unit/` - Fast, mocked, isolated
2. **Integration tests** go in `tests/integration/` - Real services, comprehensive
3. **Mark tests appropriately** - Use `@pytest.mark.requires_llm` for LLM tests
4. **Follow naming** - `test_<component>_<scenario>.py`
5. **Document** - Add docstrings explaining what the test verifies

## 📈 CI/CD Considerations

For CI/CD pipelines:

1. **Always run unit tests** - Fast, reliable, no external dependencies
2. **Run integration tests selectively**:
   - Scheduled runs (nightly)
   - Pre-release validation
   - Manual trigger
   - Separate job with LLM service available
3. **Use test markers** to control what runs:
   ```bash
   # CI: Fast unit tests only
   pytest tests/unit/ -v
   
   # Pre-release: All tests including real LLM
   pytest tests/ -m "unit or (integration and requires_llm)" -v
   ```

## 🎓 Learning TappsCodingAgents

Billstest is an excellent way to learn TappsCodingAgents:

1. **Read the tests** - See how agents are used
2. **Run the tests** - Understand what each agent does
3. **Modify workflows** - Experiment with different workflows
4. **Add your own tests** - Test your specific use cases

## 📞 Support

For issues or questions:
- Check [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- Review test output and error messages
- Check framework documentation in parent `docs/` directory

---

**Billstest Version**: 2.0.0  
**TappsCodingAgents Version**: See parent `pyproject.toml`  
**Last Updated**: January 2025

