# API Reference

**Version**: 1.6.1  
**Last Updated**: December 2025

## Overview

TappsCodingAgents provides both a **Python API** and a **CLI interface** for interacting with workflow agents, experts, and quality analysis tools.

## Python API

### Core Classes

#### `BaseAgent`

Base class for all workflow agents.

```python
from tapps_agents.core.agent_base import BaseAgent
from pathlib import Path

class MyAgent(BaseAgent):
    async def activate(self) -> Dict[str, Any]:
        """Activate the agent (setup, validation)"""
        pass
    
    def get_commands(self) -> List[Dict[str, str]]:
        """Return available commands"""
        return [{"*mycommand": "Description"}]
    
    async def run(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute a command"""
        pass
```

#### `ReviewerAgent`

Code quality review and analysis.

```python
from tapps_agents.agents.reviewer.agent import ReviewerAgent
from pathlib import Path

reviewer = ReviewerAgent()

# Review a file
result = await reviewer.review_file(
    file_path=Path("src/main.py"),
    model="qwen2.5-coder:7b",
    include_scoring=True,
    include_llm_feedback=True
)

# Lint a file
lint_result = await reviewer.lint_file(Path("src/main.py"))

# Type check a file
type_result = await reviewer.type_check_file(Path("src/main.py"))

# Generate quality reports
await reviewer.generate_reports(
    target_path=Path("src/"),
    files=[Path("src/main.py")],
    formats=["json", "markdown", "html"]
)

# Analyze entire project
project_result = await reviewer.analyze_project(
    project_root=Path("."),
    include_comparison=True
)
```

**Available Commands:**
- `*review [file]` - Review code quality
- `*score [file]` - Calculate quality scores
- `*lint [file]` - Run linting (Ruff/ESLint)
- `*type-check [file]` - Run type checking (mypy/tsc)
- `*report [path] [formats]` - Generate quality reports
- `*duplication [file]` - Check code duplication
- `*analyze-project [root]` - Analyze entire project
- `*analyze-services [services]` - Analyze specific services

#### `ImplementerAgent`

Code generation and implementation.

```python
from tapps_agents.agents.implementer.agent import ImplementerAgent

implementer = ImplementerAgent()

# Generate code
result = await implementer.generate_code(
    requirements="Create a REST API endpoint",
    target_file=Path("src/api.py"),
    context_files=[Path("src/models.py")]
)
```

**Available Commands:**
- `*implement [task]` - Generate code for a task
- `*refactor [file]` - Refactor existing code
- `*generate [description]` - Generate code from description

#### `TesterAgent`

Test generation and execution.

```python
from tapps_agents.agents.tester.agent import TesterAgent

tester = TesterAgent()

# Generate tests
result = await tester.generate_tests(
    target_file=Path("src/main.py"),
    test_framework="pytest"
)
```

**Available Commands:**
- `*test [file]` - Generate tests
- `*run-tests [path]` - Run test suite
- `*coverage [path]` - Check test coverage

#### `OrchestratorAgent`

Workflow orchestration and coordination.

```python
from tapps_agents.agents.orchestrator.agent import OrchestratorAgent

orchestrator = OrchestratorAgent()

# Execute workflow
result = await orchestrator.execute_workflow(
    workflow_file=Path("workflows/feature-development.yaml"),
    context={"feature": "user-authentication"}
)
```

**Available Commands:**
- `*execute-workflow [file]` - Execute a workflow
- `*plan [task]` - Plan a multi-agent task
- `*coordinate [agents]` - Coordinate multiple agents

#### `EnhancerAgent`

Prompt enhancement utility with expert integration.

```python
from tapps_agents.agents.enhancer.agent import EnhancerAgent

enhancer = EnhancerAgent()

# Full enhancement (all 7 stages)
result = await enhancer.enhance(
    prompt="Create a login system",
    output_format="markdown"
)

# Quick enhancement (stages 1-3)
result = await enhancer.enhance_quick(
    prompt="Add user authentication"
)

# Stage-by-stage execution
result = await enhancer.enhance_stage(
    prompt="Create payment processing",
    stage="analysis"
)
```

**Available Commands:**
- `*enhance [prompt]` - Full 7-stage enhancement
- `*enhance-quick [prompt]` - Quick enhancement (stages 1-3)
- `*enhance-stage [prompt] [stage]` - Run specific stage
- `*enhance-resume [session_id]` - Resume interrupted enhancement

### Configuration

#### `ProjectConfig`

Project configuration management.

```python
from tapps_agents.core.config import ProjectConfig
from pathlib import Path

# Load configuration
config = ProjectConfig.from_yaml(Path("project_config.yaml"))

# Access settings
print(config.agents.reviewer.quality_threshold)
print(config.model.profiles["default"].model_name)
print(config.quality_tools.ruff_enabled)
```

### Model Abstraction Layer (MAL)

#### `ModelAbstractionLayer`

Unified LLM interface.

```python
from tapps_agents.core.mal import ModelAbstractionLayer

mal = ModelAbstractionLayer()

# Generate completion
response = await mal.generate(
    prompt="Write a function to sort a list",
    model="qwen2.5-coder:7b",
    temperature=0.7
)

# Stream response
async for chunk in mal.stream(prompt="...", model="..."):
    print(chunk, end="")
```

### Expert System

#### `ExpertRegistry`

Expert management and consultation.

```python
from tapps_agents.experts.registry import ExpertRegistry

registry = ExpertRegistry(config=config)

# Consult experts
advice = await registry.consult(
    domain="healthcare",
    question="What are HIPAA compliance requirements?",
    context={"application_type": "patient_portal"}
)

# Get expert weights
weights = registry.get_expert_weights("healthcare")
```

### Context7 Integration

#### `Context7KB`

Library documentation caching and retrieval.

```python
from tapps_agents.context7.kb_cache import Context7KB

kb = Context7KB(config=config)

# Get library documentation
docs = await kb.get_docs(
    library="fastapi",
    topic="routing",
    mode="code"
)

# Refresh cache
await kb.refresh_cache(library="fastapi")
```

## CLI Interface

### Basic Usage

```bash
# Run agent command
python -m tapps_agents.cli [agent] [command] [args...]

# Examples
python -m tapps_agents.cli reviewer review src/main.py
python -m tapps_agents.cli reviewer lint src/main.py
python -m tapps_agents.cli reviewer type-check src/main.py
python -m tapps_agents.cli reviewer report src/ json markdown html

# Analyze project
python -m tapps_agents.cli reviewer analyze-project .

# Generate code
python -m tapps_agents.cli implementer implement "Create REST API"

# Generate tests
python -m tapps_agents.cli tester test src/main.py

# Execute workflow
python -m tapps_agents.cli orchestrator execute-workflow workflows/feature.yaml
```

### Available Agents

```
analyst, planner, architect, designer, implementer, tester,
debugger, documenter, reviewer, improver, ops, orchestrator, enhancer
```

### Command Format

All commands use the star-prefixed format:

- `*review [file]` - Review file
- `*lint [file]` - Lint file
- `*type-check [file]` - Type check file
- `*implement [task]` - Implement task
- `*test [file]` - Generate tests
- `*execute-workflow [file]` - Execute workflow

## Quality Analysis API

### Code Scoring

```python
from tapps_agents.agents.reviewer.scoring import CodeScorer

scorer = CodeScorer()

scores = scorer.score_file(
    file_path=Path("src/main.py"),
    code=source_code
)

print(f"Complexity: {scores['complexity_score']}")
print(f"Security: {scores['security_score']}")
print(f"Maintainability: {scores['maintainability_score']}")
print(f"Overall: {scores['overall_score']}")
```

### TypeScript Scoring

```python
from tapps_agents.agents.reviewer.typescript_scorer import TypeScriptScorer

ts_scorer = TypeScriptScorer(
    eslint_config=".eslintrc.json",
    tsconfig_path="tsconfig.json"
)

scores = ts_scorer.score_file(
    file_path=Path("src/Button.tsx"),
    code=tsx_code
)
```

### Report Generation

```python
from tapps_agents.agents.reviewer.report_generator import ReportGenerator

generator = ReportGenerator(config=config)

# Generate reports
json_path = generator.generate_json_report(file_scores, output_dir)
md_path = generator.generate_markdown_report(file_scores, output_dir)
html_path = generator.generate_html_report(file_scores, output_dir)
```

## Error Handling

All API methods raise exceptions for errors:

```python
from tapps_agents.core.exceptions import (
    AgentActivationError,
    CommandNotFoundError,
    ConfigurationError,
    ModelProviderError
)

try:
    result = await agent.run("*review", file_path="src/main.py")
except AgentActivationError as e:
    print(f"Agent activation failed: {e}")
except CommandNotFoundError as e:
    print(f"Command not found: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Async/Await

All agent methods are async and must be awaited:

```python
import asyncio

async def main():
    reviewer = ReviewerAgent()
    result = await reviewer.review_file(Path("src/main.py"))
    print(result)

asyncio.run(main())
```

## Configuration Schema

See [Configuration Schema](API/CONFIG_SCHEMA.md) for complete configuration reference.

## Agent Commands Reference

See [Agent Commands Reference](API/AGENT_COMMANDS.md) for complete command documentation.

---

**Related Documentation:**
- [Quick Start Guide](../QUICK_START.md)
- [Configuration Guide](CONFIGURATION.md)
- [Developer Guide](DEVELOPER_GUIDE.md)

