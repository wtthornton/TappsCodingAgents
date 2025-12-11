# TappsCodingAgents - Configuration Guide

This document describes the configuration system for TappsCodingAgents.

## Overview

TappsCodingAgents uses a YAML-based configuration system with Pydantic models for type-safe validation. Configuration files are optional - sensible defaults are provided for all settings.

## Configuration File Location

The framework looks for configuration in `.tapps-agents/config.yaml` in your project root:

```
your-project/
├── .tapps-agents/
│   ├── config.yaml          # Project configuration
│   ├── domains.md           # Business domain definitions
│   └── customizations/      # Agent-specific customizations
│       └── {agent-id}-custom.yaml
└── src/
    └── ...
```

If no config file is found, the framework uses default values.

## Configuration Schema

### Root Configuration

```yaml
# Project metadata (optional)
project_name: "MyProject"
version: "1.0.0"

# Agent configurations
agents:
  reviewer:
    # Reviewer agent settings (see below)

# Code scoring configuration
scoring:
  # Scoring settings (see below)

# Model Abstraction Layer (MAL) configuration
mal:
  # MAL settings (see below)
```

### Agent Configuration: Reviewer

```yaml
agents:
  reviewer:
    model: "qwen2.5-coder:7b"           # LLM model for code reviews
    quality_threshold: 70.0              # Minimum score (0-100) to pass review
    include_scoring: true                # Include code scoring in review
    include_llm_feedback: true           # Include LLM-generated feedback
    max_file_size: 1048576               # Maximum file size in bytes (1MB)
```

**Options:**
- `model` (string): Model name for Ollama (e.g., "qwen2.5-coder:7b")
- `quality_threshold` (float): Minimum overall score (0-100) to pass review
- `include_scoring` (bool): Whether to calculate and include code scores
- `include_llm_feedback` (bool): Whether to generate LLM feedback
- `max_file_size` (int): Maximum file size in bytes (default: 1MB)

### Scoring Configuration

```yaml
scoring:
  weights:
    complexity: 0.20                     # Weight for complexity score
    security: 0.30                       # Weight for security score
    maintainability: 0.25                # Weight for maintainability score
    test_coverage: 0.15                  # Weight for test coverage score
    performance: 0.10                    # Weight for performance score
  quality_threshold: 70.0                # Minimum overall score (0-100)
```

**Important:** The weights must sum to 1.0. If they don't, configuration loading will fail with a validation error.

**Options:**
- `weights.complexity` (float): Weight for complexity metric (0.0-1.0)
- `weights.security` (float): Weight for security metric (0.0-1.0)
- `weights.maintainability` (float): Weight for maintainability metric (0.0-1.0)
- `weights.test_coverage` (float): Weight for test coverage metric (0.0-1.0)
- `weights.performance` (float): Weight for performance metric (0.0-1.0)
- `quality_threshold` (float): Minimum overall score (0-100) to pass

### MAL Configuration

```yaml
mal:
  ollama_url: "http://localhost:11434"   # Ollama API URL
  default_model: "qwen2.5-coder:7b"      # Default model name
  timeout: 60.0                          # Request timeout in seconds
```

**Options:**
- `ollama_url` (string): Base URL for Ollama API
- `default_model` (string): Default model to use if not specified
- `timeout` (float): Request timeout in seconds (minimum: 1.0)

## Default Values

If no configuration file is provided, the following defaults are used:

```yaml
agents:
  reviewer:
    model: "qwen2.5-coder:7b"
    quality_threshold: 70.0
    include_scoring: true
    include_llm_feedback: true
    max_file_size: 1048576  # 1MB

scoring:
  weights:
    complexity: 0.20
    security: 0.30
    maintainability: 0.25
    test_coverage: 0.15
    performance: 0.10
  quality_threshold: 70.0

mal:
  ollama_url: "http://localhost:11434"
  default_model: "qwen2.5-coder:7b"
  timeout: 60.0
```

## Configuration Loading

Configuration is automatically loaded when agents are activated:

```python
from tapps_agents.agents.reviewer.agent import ReviewerAgent

# Config is automatically loaded from .tapps-agents/config.yaml
reviewer = ReviewerAgent()
await reviewer.activate()  # Loads config during activation
```

You can also load configuration manually:

```python
from tapps_agents.core.config import load_config, ProjectConfig

# Load from default location
config = load_config()

# Load from specific path
config = load_config(Path(".tapps-agents/config.yaml"))

# Access configuration
print(config.agents.reviewer.quality_threshold)
print(config.scoring.weights.complexity)
```

## Validation

The configuration system uses Pydantic for validation:

- **Type checking**: All values are validated for correct types
- **Range validation**: Numeric values are checked against min/max bounds
- **Sum validation**: Scoring weights must sum to 1.0

If validation fails, a `ValueError` is raised with details about what's wrong.

## Example: Custom Configuration

Create `.tapps-agents/config.yaml` in your project:

```yaml
# Custom configuration for stricter code reviews
agents:
  reviewer:
    model: "qwen2.5-coder:7b"
    quality_threshold: 80.0  # Stricter: require 80+ score
    max_file_size: 2097152   # Allow 2MB files

scoring:
  weights:
    complexity: 0.15
    security: 0.40           # Emphasize security
    maintainability: 0.25
    test_coverage: 0.15
    performance: 0.05
  quality_threshold: 80.0

mal:
  ollama_url: "http://localhost:11434"
  timeout: 120.0  # Longer timeout for large files
```

## Using Configuration in Code

Agents automatically access their configuration:

```python
# In your agent code
class MyAgent(BaseAgent):
    async def run(self, command: str, **kwargs):
        # Access config
        threshold = self.config.agents.reviewer.quality_threshold
        model = self.config.agents.reviewer.model
        
        # Use config values
        ...
```

## Template Generation

To generate a default configuration template:

```python
from tapps_agents.core.config import get_default_config
import yaml

config_dict = get_default_config()
with open("config.yaml", "w") as f:
    yaml.dump(config_dict, f, default_flow_style=False)
```

Or simply copy `templates/default_config.yaml` to `.tapps-agents/config.yaml`.

## Troubleshooting

### Configuration Not Loading

- Check that `.tapps-agents/config.yaml` exists in your project root
- Verify YAML syntax is correct (use a YAML validator)
- Check for validation errors in the error message

### Weights Don't Sum to 1.0

The scoring weights must sum to exactly 1.0. If you get an error, check your weights:

```yaml
scoring:
  weights:
    complexity: 0.20
    security: 0.30
    maintainability: 0.25
    test_coverage: 0.15
    performance: 0.10
    # Sum: 0.20 + 0.30 + 0.25 + 0.15 + 0.10 = 1.0 ✓
```

### Type Errors

All numeric values must be numbers (not strings). Use:

```yaml
# ✓ Correct
quality_threshold: 70.0

# ✗ Incorrect
quality_threshold: "70.0"
```

### Unified Cache Configuration ✅

The unified cache automatically detects hardware and optimizes settings. Configuration is optional but can be customized:

```yaml
# Optional: Unified cache configuration
# Location: .tapps-agents/unified-cache-config.yaml

unified_cache:
  enabled: true
  storage_root: ".tapps-agents/kb/unified-cache"
  
  # Hardware auto-detection (automatic on first run)
  hardware:
    auto_detect: true
    profile: "auto"  # auto, nuc, development, workstation, server
    detected_profile: "development"  # Set automatically
  
  # Adaptive settings
  adaptive:
    enabled: true
    check_interval: 60
  
  # Tiered context cache settings (auto-configured based on hardware)
  tiered_context:
    enabled: true
    namespace: "tiered-context"
    # Auto-configured per hardware profile
    max_in_memory_entries: 100  # NUC: 50, Dev: 100, Workstation: 200
    hybrid_mode: true  # NUC: false, Dev/Workstation: true
  
  # Context7 KB cache settings
  context7_kb:
    enabled: true
    namespace: "context7-kb"
    max_cache_size: "200MB"  # NUC: 100MB, Dev: 200MB, Workstation: 500MB
  
  # RAG knowledge base settings
  rag_knowledge:
    enabled: true
    namespace: "rag-knowledge"
```

**Key Points:**
- Configuration is **optional** - unified cache works with defaults
- Hardware profile is **auto-detected** on first run
- Settings are **auto-optimized** based on detected hardware
- Manual override available if needed

See [Unified Cache Architecture Plan](../implementation/UNIFIED_CACHE_ARCHITECTURE_PLAN.md) for complete configuration options.

## Reference

- **Default Template**: `templates/default_config.yaml`
- **Config Models**: `tapps_agents/core/config.py`
- **Project Requirements**: `requirements/PROJECT_REQUIREMENTS.md`
- **Unified Cache Config**: `tapps_agents/core/unified_cache_config.py`

