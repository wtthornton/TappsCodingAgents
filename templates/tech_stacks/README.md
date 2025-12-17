# Tech Stack Templates

This directory contains technology stack-specific configuration templates that are automatically applied during project initialization.

## Template Format

Each template is a YAML file with the following structure:

```yaml
# Agent configuration overrides
agent_config:
  reviewer:
    quality_threshold: 75.0
    min_confidence_threshold: 0.85
  implementer:
    min_confidence_threshold: 0.75
  # ... other agents

# Context7 pre-population settings
context7_prepop:
  libraries:
    - library1
    - library2
  topics:
    library1:
      - topic1
      - topic2

# Expert priorities (0.0-1.0)
expert_priorities:
  expert-api-design: 1.0
  expert-observability: 0.9
  # ... other experts

# Test framework defaults
test_frameworks:
  primary: pytest
  async_support: true
  plugins:
    - plugin1
  coverage_target: 85.0
```

## Template Sections

### `agent_config`

Overrides default agent configuration values for the specific tech stack. Each agent can have stack-specific thresholds and settings.

**Available agents:**
- `reviewer`: Code review settings
- `implementer`: Code generation settings
- `tester`: Test generation settings
- `debugger`: Debugging settings
- `documenter`: Documentation settings
- `planner`: Planning settings

### `context7_prepop`

Defines libraries and topics to pre-populate in the Context7 knowledge base cache during initialization.

- `libraries`: List of library names to cache
- `topics`: Map of library names to topic lists for focused caching

### `expert_priorities`

Maps expert IDs to priority values (0.0-1.0) indicating how relevant each expert is for this tech stack.

- `1.0`: Highest priority (most relevant)
- `0.0`: No priority (not relevant)

### `test_frameworks`

Defines default test framework configuration for the tech stack.

- `primary`: Primary test framework
- `e2e`: End-to-end testing framework (optional)
- `async_support`: Whether async testing is supported
- `plugins`: List of test plugins/frameworks
- `default_markers`: Default test markers/tags
- `coverage_target`: Target test coverage percentage
- `test_pattern`: File pattern for test files (optional)

## Available Templates

- **fastapi.yaml**: FastAPI/async Python API projects
- **nextjs.yaml**: Next.js fullstack React projects
- **django.yaml**: Django web framework projects
- **react.yaml**: React frontend projects
- **express.yaml**: Express.js backend projects
- **nestjs.yaml**: NestJS TypeScript API projects
- **flask.yaml**: Flask Python web projects

## Template Selection

Templates are automatically selected during `tapps-agents init` based on detected technology stack:

1. Tech stack detection runs
2. Detected frameworks are mapped to template files
3. Template is merged with default configuration
4. Merged config is written to `.tapps-agents/config.yaml`

## Creating New Templates

To create a new template:

1. Copy an existing template as a starting point
2. Update `agent_config` with stack-specific thresholds
3. Add relevant libraries to `context7_prepop.libraries`
4. Set appropriate `expert_priorities` based on stack needs
5. Configure `test_frameworks` for the stack's testing approach
6. Name the file `{framework}.yaml` (lowercase, no spaces)
7. Update this README with the new template

## Template Variables

Templates support variable expansion using `{{variable.name}}` syntax:

- `{{project.name}}`: Project name (from project root directory)
- `{{project.root}}`: Project root directory path
- `{{tech_stack.frameworks}}`: List of detected frameworks
- `{{tech_stack.languages}}`: List of detected languages
- `{{tech_stack.libraries}}`: List of detected libraries
- `{{tech_stack.package_managers}}`: List of detected package managers

### Variable Expansion Examples

```yaml
# In template file
context7_prepop:
  libraries:
    - "{{tech_stack.frameworks[0]}}"  # First detected framework
    - fastapi
    - pytest

# After expansion (if frameworks = ["FastAPI"])
context7_prepop:
  libraries:
    - "FastAPI"
    - fastapi
    - pytest
```

Variables that cannot be resolved are left as-is (e.g., `{{unknown.var}}` remains unchanged).

## Customization Examples

### Example 1: Override Agent Thresholds

If you want to customize agent thresholds for your project, create or edit `.tapps-agents/config.yaml`:

```yaml
agents:
  reviewer:
    quality_threshold: 80.0  # Higher than template default
  tester:
    coverage_threshold: 90.0  # Higher coverage target
```

User config overrides template values, so your customizations are preserved.

### Example 2: Add Additional Libraries to Context7 Pre-pop

```yaml
context7:
  knowledge_base:
    enabled: true
  # Template libraries are merged with your additions
```

### Example 3: Override Expert Priorities

```yaml
# In .tapps-agents/tech-stack.yaml (or config.yaml)
expert_priorities:
  expert-api-design: 0.9  # Lower than template default
  expert-custom: 1.0      # Add custom expert
```

## Troubleshooting

### Template Not Applied

**Problem**: Template is selected but not applied during `tapps-agents init`

**Solutions**:
1. Check that template file exists in `templates/tech_stacks/`
2. Verify template YAML is valid (use `yaml.safe_load()` to test)
3. Check init output for template selection reason
4. Ensure tech stack detection found your framework

### Wrong Template Selected

**Problem**: System selects wrong template for your project

**Solutions**:
1. Check detected frameworks in init output
2. Verify framework name matches template mapping (case-insensitive)
3. For multiple frameworks, check template priority order
4. Manually override by editing `.tapps-agents/config.yaml`

### User Config Overridden

**Problem**: Your custom config is being overwritten

**Solutions**:
1. User config should have highest priority - check merge order
2. Ensure you're editing `.tapps-agents/config.yaml` (not template file)
3. User config is merged last, so your values should be preserved
4. Check for YAML syntax errors that might cause parsing to fail

### Variable Expansion Not Working

**Problem**: Template variables like `{{project.name}}` not expanding

**Solutions**:
1. Verify variable syntax: `{{variable.name}}` (double curly braces)
2. Check variable name matches available variables (see Template Variables section)
3. Missing variables are left as-is (not an error)
4. Nested paths like `{{tech_stack.frameworks[0]}}` are supported

## Best Practices

1. **Keep templates focused**: Each template should target one primary framework
2. **Use sensible defaults**: Templates should work out-of-the-box
3. **Document priorities**: Expert priorities should reflect real-world usage
4. **Update regularly**: Keep templates aligned with framework best practices
5. **Test templates**: Verify templates work with actual projects
6. **Version templates**: Include version field for future compatibility
7. **Preserve user overrides**: Always allow user customization

## Versioning

Templates include a version field for future compatibility:

```yaml
# Template version: 1.0
```

When template format changes, increment the version and update the merge logic accordingly.

