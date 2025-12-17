# Template Conditional Blocks Guide

This guide explains how to use conditional blocks in TappsCodingAgents templates to create adaptive, context-aware configuration.

## Overview

Conditional blocks allow templates to include or exclude sections based on detected project context. This enables templates to adapt to different project types, frameworks, and configurations without requiring separate template files.

## Syntax

### Basic Conditional Block

```yaml
{{#if variable.path}}
# This content is included if variable.path is truthy
key: value
{{/if}}
```

### Conditional with Else Branch

```yaml
{{#if variable.path}}
# Included if variable.path is truthy
key: true_value
{{#else}}
# Included if variable.path is falsy
key: false_value
{{/if}}
```

## Supported Variables

Conditional blocks can evaluate any variable available in the template context:

- **Project variables**: `{{project.name}}`, `{{project.root}}`
- **Tech stack variables**: `{{tech_stack.frameworks}}`, `{{tech_stack.languages}}`
- **Nested paths**: `{{tech_stack.frameworks[0]}}`, `{{project.metadata.type}}`

## Evaluation Rules

### Truthy Values

The following values evaluate to `true`:

- **Boolean `true`**: `enabled: true`
- **Non-empty strings**: `name: "test"` (any non-empty string)
- **Non-empty lists**: `items: [1, 2, 3]`
- **Non-empty dictionaries**: `config: {key: value}`
- **Non-zero numbers**: `count: 42`, `score: 0.5`

### Falsy Values

The following values evaluate to `false`:

- **Boolean `false`**: `enabled: false`
- **Empty strings**: `name: ""`
- **Empty lists**: `items: []`
- **Empty dictionaries**: `config: {}`
- **Zero**: `count: 0`
- **Missing variables**: Variable not found in context

### Safe Evaluation

- **No arbitrary code execution**: Only variable presence and truthiness are checked
- **Missing variables**: Evaluate to `false` (safe default)
- **No expressions**: Cannot use operators like `==`, `!=`, `>`, `<`, etc.
- **No function calls**: Cannot call functions or methods

## Examples

### Example 1: Framework-Specific Configuration

```yaml
# FastAPI template with conditional async support
agent_config:
  reviewer:
    quality_threshold: 75.0
{{#if tech_stack.frameworks}}
  # Only include if frameworks are detected
  implementer:
    async_aware: true
{{/if}}
```

### Example 2: Project Type Detection

```yaml
# Different quality thresholds based on project type
agent_config:
  reviewer:
{{#if project.type}}
    # Use project-type specific threshold
    quality_threshold: 80.0
{{#else}}
    # Default threshold for unknown types
    quality_threshold: 70.0
{{/if}}
```

### Example 3: Conditional Expert Priorities

```yaml
expert_priorities:
  expert-api-design: 1.0
{{#if tech_stack.frameworks}}
  # Only set if frameworks detected
  expert-observability: 0.9
{{/if}}
{{#if project.has_database}}
  expert-database: 0.8
{{/if}}
```

### Example 4: Conditional Context7 Libraries

```yaml
context7_prepop:
  libraries:
    - fastapi
    - pytest
{{#if tech_stack.frameworks}}
    # Add first detected framework to pre-pop
    - "{{tech_stack.frameworks[0]}}"
{{/if}}
```

### Example 5: Testing Strategy Based on Project Type

```yaml
testing_strategy:
  focus_areas:
    - unit
    - integration
{{#if project.type}}
    # Add type-specific focus areas
    - "{{project.type}}-specific"
{{/if}}
```

### Example 6: Multiple Conditionals

```yaml
agent_config:
  reviewer:
    quality_threshold: 70.0
{{#if project.is_api}}
    # API-specific settings
    api_focused: true
    min_confidence_threshold: 0.85
{{/if}}
{{#if project.has_frontend}}
    # Frontend-specific settings
    ui_focused: true
    accessibility_check: true
{{/if}}
{{#if project.is_microservice}}
    # Microservice-specific settings
    service_boundary_check: true
    contract_testing: true
{{/if}}
```

## Real-World Template Example

Here's a complete example showing conditional blocks in a tech stack template:

```yaml
# FastAPI Tech Stack Template with Conditionals
# Template version: 1.0

agent_config:
  reviewer:
    quality_threshold: 75.0
{{#if project.type}}
    # Adjust threshold based on project type
    min_confidence_threshold: 0.85
{{#else}}
    min_confidence_threshold: 0.80
{{/if}}

context7_prepop:
  libraries:
    - fastapi
    - uvicorn
    - pydantic
{{#if tech_stack.frameworks}}
    # Add detected frameworks
    - "{{tech_stack.frameworks[0]}}"
{{/if}}
{{#if project.has_database}}
    - sqlalchemy
    - alembic
{{/if}}

expert_priorities:
  expert-api-design: 1.0
  expert-observability: 0.9
{{#if project.is_microservice}}
  expert-software-architecture: 1.0
  expert-security: 0.9
{{/if}}

test_frameworks:
  primary: pytest
  async_support: true
{{#if project.has_integration_tests}}
  plugins:
    - pytest-asyncio
    - pytest-cov
    - pytest-mock
{{#else}}
  plugins:
    - pytest-asyncio
{{/if}}
```

## Trace Output

When templates are processed with trace enabled, conditional evaluations are recorded:

```json
{
  "template_path": "/path/to/template.yaml",
  "variables_used": {
    "project": {"name": "MyProject", "type": "api-service"},
    "tech_stack": {"frameworks": ["FastAPI"]}
  },
  "conditionals_evaluated": [
    {
      "condition": "{{#if project.type}}",
      "variable_path": "project.type",
      "variable_value": "api-service",
      "evaluated": true,
      "reason": "Variable 'project.type' is non-empty"
    },
    {
      "condition": "{{#if tech_stack.frameworks}}",
      "variable_path": "tech_stack.frameworks",
      "variable_value": ["FastAPI"],
      "evaluated": true,
      "reason": "Variable 'tech_stack.frameworks' is non-empty"
    }
  ],
  "variable_expansions": {
    "project.name": "MyProject",
    "tech_stack.frameworks[0]": "FastAPI"
  }
}
```

To enable trace output during template application:

```python
from tapps_agents.core.template_merger import apply_template_to_config

config, trace = apply_template_to_config(
    template_path=Path("template.yaml"),
    default_config=defaults,
    enable_trace=True,
    trace_output_path=Path(".tapps-agents/template-trace.json"),
)
```

## Limitations

### What You Cannot Do

1. **No complex expressions**: Cannot use `{{#if count > 10}}` or `{{#if name == "test"}}`
2. **No logical operators**: Cannot use `&&`, `||`, `!`
3. **No function calls**: Cannot use `{{#if len(items) > 0}}`
4. **No nested conditionals**: Nested `{{#if}}` blocks are not supported (only one level)
5. **No loops**: Cannot iterate over lists with conditionals

### Workarounds

For complex conditions, consider:

1. **Pre-compute values**: Calculate conditions in detection logic, expose as simple boolean variables
2. **Multiple templates**: Use separate templates for significantly different configurations
3. **User overrides**: Let users override specific values in their config

## Best Practices

1. **Keep conditionals simple**: Use conditionals for clear, binary decisions
2. **Document variables**: Document which variables are available for conditionals
3. **Test conditionals**: Verify both true and false paths work correctly
4. **Use meaningful names**: Variable names should clearly indicate their purpose
5. **Avoid deep nesting**: Prefer multiple simple conditionals over complex nested logic
6. **Provide defaults**: Always have a sensible default when conditionals evaluate to false

## Troubleshooting

### Conditional Not Working

**Problem**: Conditional block content is always included/excluded

**Solutions**:
1. Check variable name matches exactly (case-sensitive)
2. Verify variable exists in template context
3. Check variable value (empty strings/lists evaluate to false)
4. Enable trace output to see evaluation details

### Variable Not Found

**Problem**: Variable evaluates to false even when it should be true

**Solutions**:
1. Verify variable is available in template context
2. Check variable path (use dot notation for nested: `project.name`)
3. Missing variables evaluate to false (safe default)
4. Check trace output to see actual variable values

### YAML Syntax Errors

**Problem**: Template fails to parse after adding conditionals

**Solutions**:
1. Ensure conditional blocks are properly closed: `{{/if}}`
2. Check YAML indentation (conditionals don't affect YAML structure)
3. Verify no unclosed blocks or mismatched braces
4. Test template with `yaml.safe_load()` before using

## Related Documentation

- [Tech Stack Templates README](../templates/tech_stacks/README.md)
- [Project Type Templates README](../templates/project_types/README.md)
- [Template Merging System](stories/31.3.template-merging-system.md)
- [Epic 3: Adaptive Configuration & Templates](prd/epic-3-adaptive-configuration-and-templates.md)

