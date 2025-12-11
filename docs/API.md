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

Expert management and consultation with built-in and customer experts.

```python
from tapps_agents.experts import ExpertRegistry

# Create registry (auto-loads built-in experts)
registry = ExpertRegistry(domain_config=None, load_builtin=True)

# Consult technical domain (prioritizes built-in experts)
result = await registry.consult(
    query="How to secure this API?",
    domain="security",
    prioritize_builtin=True,
    agent_id="reviewer"  # Optional: for agent-specific confidence threshold
)

# Access confidence information
print(f"Confidence: {result.confidence:.2%}")
print(f"Threshold: {result.confidence_threshold:.2%}")
print(f"Agreement: {result.agreement_level:.2%}")
print(f"All experts agreed: {result.all_experts_agreed}")

# Consult business domain (prioritizes customer experts)
result = await registry.consult(
    query="How to handle checkout?",
    domain="e-commerce",
    prioritize_builtin=False,
    agent_id="architect"
)

# List available experts
experts = registry.list_experts()

# Get specific expert
expert = registry.get_expert("expert-security")
```

#### `BuiltinExpertRegistry`

Access to framework-controlled built-in experts.

```python
from tapps_agents.experts import BuiltinExpertRegistry

# Get all built-in experts
experts = BuiltinExpertRegistry.get_builtin_experts()

# Get expert for domain
expert_config = BuiltinExpertRegistry.get_expert_for_domain("security")

# Check if domain is technical
is_technical = BuiltinExpertRegistry.is_technical_domain("security")
```

#### `ConsultationResult`

Result from expert consultation with confidence metrics.

```python
from tapps_agents.experts.expert_registry import ConsultationResult

# ConsultationResult fields:
result.domain                    # Domain name
result.query                     # Original query
result.responses                 # List of expert responses
result.weighted_answer           # Aggregated weighted answer
result.agreement_level           # Agreement level (0.0-1.0)
result.confidence                # Calculated confidence (0.0-1.0)
result.confidence_threshold      # Agent-specific threshold (0.0-1.0)
result.primary_expert            # Primary expert ID
result.all_experts_agreed        # Whether all experts agreed (bool)

# Check if confidence meets threshold
meets_threshold = result.confidence >= result.confidence_threshold
```

#### `ConfidenceCalculator`

Calculate confidence scores for expert consultations.

```python
from tapps_agents.experts.confidence_calculator import ConfidenceCalculator

# Calculate confidence
confidence, threshold = ConfidenceCalculator.calculate(
    responses=expert_responses,
    domain="security",
    agent_id="reviewer",
    agreement_level=0.85,
    rag_quality=0.9
)

# Get agent-specific threshold
threshold = ConfidenceCalculator.get_threshold("reviewer")

# Check if meets threshold
meets = ConfidenceCalculator.meets_threshold(confidence, "reviewer")
```

#### `ConfidenceMetricsTracker`

Track and analyze confidence metrics.

```python
from tapps_agents.experts.confidence_metrics import get_tracker

tracker = get_tracker()

# Get statistics
stats = tracker.get_statistics(agent_id="reviewer", domain="security")
# Returns: {
#   "count": 150,
#   "avg_confidence": 0.82,
#   "min_confidence": 0.45,
#   "max_confidence": 0.98,
#   "avg_agreement": 0.75,
#   "threshold_meet_rate": 0.87,
#   "low_confidence_count": 12
# }

# Get filtered metrics
metrics = tracker.get_metrics(
    agent_id="reviewer",
    domain="security",
    min_confidence=0.7
)
```

#### `ExpertSupportMixin`

Mixin class for agents to add expert consultation capabilities.

```python
from tapps_agents.core.agent_base import BaseAgent
from tapps_agents.experts.agent_integration import ExpertSupportMixin

class MyAgent(BaseAgent, ExpertSupportMixin):
    async def activate(self, project_root: Optional[Path] = None):
        await super().activate(project_root)
        await self._initialize_expert_support(project_root)
    
    async def my_method(self):
        # Consult built-in expert
        result = await self._consult_builtin_expert(
            query="How to optimize this?",
            domain="performance-optimization"
        )
        
        # Check confidence
        if result.confidence >= result.confidence_threshold:
            # Use expert guidance
            pass
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

### Unified Cache Architecture ✅

#### `UnifiedCache`

Single interface for all caching systems with hardware auto-detection.

```python
from tapps_agents.core import UnifiedCache, create_unified_cache, CacheType, ContextTier

# Create unified cache (auto-detects hardware)
cache = create_unified_cache()

# Get hardware profile
profile = cache.get_hardware_profile()
print(f"Hardware: {profile.value}")  # nuc, development, workstation, server

# Get tiered context
response = cache.get(
    CacheType.TIERED_CONTEXT,
    key="path/to/file.py",
    tier=ContextTier.TIER1
)

# Get Context7 KB entry
response = cache.get(
    CacheType.CONTEXT7_KB,
    key="library-topic",
    library="fastapi",
    topic="routing"
)

# Get RAG knowledge
response = cache.get(
    CacheType.RAG_KNOWLEDGE,
    key="query-id",
    query="agent orchestration patterns"
)

# Store in cache
cache.put(
    CacheType.TIERED_CONTEXT,
    key="path/to/file.py",
    value={"context": "..."},
    tier=ContextTier.TIER1
)

# Get statistics
stats = cache.get_stats()
print(f"Hits: {stats.total_hits}, Misses: {stats.total_misses}")
```

#### `BaseAgent.get_unified_cache()`

Optional unified cache access in agents.

```python
from tapps_agents.core import BaseAgent, CacheType, ContextTier

class MyAgent(BaseAgent):
    async def run(self, command: str, **kwargs):
        # Get unified cache (lazy initialization)
        cache = self.get_unified_cache()
        
        # Use unified cache
        response = cache.get(
            CacheType.TIERED_CONTEXT,
            key=kwargs.get("file", ""),
            tier=ContextTier.TIER1
        )
        
        return {"context": response.data if response else None}
```

**Key Features:**
- Hardware auto-detection (NUC, Development, Workstation, Server)
- Auto-optimization based on hardware profile
- Unified interface for all cache types
- Backward compatible with existing cache systems
- Zero configuration required

See [Unified Cache Integration Guide](../implementation/UNIFIED_CACHE_INTEGRATION_GUIDE.md) for details.

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

