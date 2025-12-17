# Tech Stack Expert Priority Configuration Guide

**Version:** 1.0  
**Last Updated:** January 2026

## Overview

TappsCodingAgents automatically prioritizes built-in experts based on your project's detected technology stack. This improves expert selection quality, reduces token usage, and ensures more relevant guidance for developers.

The priority system:
- Automatically detects your tech stack during project initialization
- Maps frameworks to relevant expert priorities
- Persists priorities to `.tapps-agents/tech-stack.yaml`
- Applies priorities when selecting experts for consultation
- Supports manual overrides for customization

## How It Works

### 1. Tech Stack Detection

During `tapps-agents init`, the system detects frameworks from your project dependencies:

- **Python projects**: Detects FastAPI, Django, Flask, etc. from `requirements.txt` or `pyproject.toml`
- **Node.js projects**: Detects React, Next.js, NestJS, Express, etc. from `package.json`

### 2. Priority Mapping

Each detected framework maps to expert priorities (0.0-1.0 scale):

- **1.0** = Highest priority (most relevant for this stack)
- **0.8-0.9** = High priority (very relevant)
- **0.5-0.7** = Medium priority (somewhat relevant)
- **0.0-0.4** = Low priority (less relevant)

### 3. Configuration File

Priorities are persisted to `.tapps-agents/tech-stack.yaml`:

```yaml
frameworks:
  - FastAPI
  - React

expert_priorities:
  expert-api-design: 1.0
  expert-observability: 0.9
  expert-performance: 0.8
  expert-security: 0.7
  expert-user-experience: 0.9
  expert-software-architecture: 0.5

overrides:
  # User can override default priorities here
  # expert-api-design: 0.8
```

### 4. Expert Selection

When consulting experts, the registry:
1. Finds experts matching the requested domain
2. Applies tech stack priorities to reorder experts
3. Returns experts sorted by priority (higher first)

**Important**: Priorities are weights, not filters. All matching experts are still included, just reordered.

## Supported Frameworks

The following frameworks have default priority mappings:

### FastAPI

- `expert-api-design`: 1.0 (most critical)
- `expert-observability`: 0.9
- `expert-performance`: 0.8
- `expert-security`: 0.7
- `expert-database`: 0.6
- `expert-software-architecture`: 0.5

### Django

- `expert-software-architecture`: 1.0 (web framework patterns)
- `expert-database`: 0.9
- `expert-security`: 0.8
- `expert-performance`: 0.7
- `expert-testing`: 0.6
- `expert-api-design`: 0.5 (if using Django REST)

### React

- `expert-user-experience`: 1.0 (frontend expertise)
- `expert-software-architecture`: 0.9 (frontend architecture)
- `expert-performance`: 0.8
- `expert-accessibility`: 0.7
- `expert-testing`: 0.6

### Next.js

- `expert-software-architecture`: 1.0 (fullstack architecture)
- `expert-user-experience`: 0.9
- `expert-performance`: 0.8
- `expert-api-design`: 0.7 (API routes)
- `expert-observability`: 0.6 (SSR)
- `expert-accessibility`: 0.5

### NestJS

- `expert-api-design`: 1.0 (API framework)
- `expert-software-architecture`: 0.9 (strong patterns)
- `expert-observability`: 0.8
- `expert-security`: 0.7
- `expert-performance`: 0.6
- `expert-database`: 0.5

## Manual Configuration

### Overriding Priorities

You can override default priorities by editing `.tapps-agents/tech-stack.yaml`:

```yaml
frameworks:
  - FastAPI

expert_priorities:
  expert-api-design: 1.0
  expert-observability: 0.9
  expert-performance: 0.8

overrides:
  # Override default priority
  expert-api-design: 0.7
  expert-performance: 0.9  # Promote performance expert
```

Overrides take precedence over default priorities.

### Adding Custom Priorities

You can add priorities for experts not in the default mapping:

```yaml
expert_priorities:
  expert-api-design: 1.0
  expert-custom-expert: 0.8  # Custom expert priority
```

### Manual Framework Configuration

If your framework isn't automatically detected, you can manually configure it:

```yaml
frameworks:
  - FastAPI
  - CustomFramework  # Manually added

expert_priorities:
  expert-api-design: 1.0
  # Add priorities for CustomFramework
```

## Examples

### Example 1: FastAPI Project

For a FastAPI project, the system automatically:

1. Detects FastAPI from `requirements.txt`
2. Creates `.tapps-agents/tech-stack.yaml` with API Design expert prioritized
3. Expert registry loads priorities on initialization
4. When consulting for API design, `expert-api-design` is consulted first

```python
# Expert registry automatically uses priorities
registry = ExpertRegistry(project_root=project_root)

# API design consultation prioritizes expert-api-design
result = await registry.consult(
    query="How should I structure my FastAPI endpoints?",
    domain="api-design-integration"
)
# expert-api-design is consulted first due to priority 1.0
```

### Example 2: React + Next.js Fullstack Project

For a project with both React and Next.js:

1. Both frameworks are detected
2. Priorities are combined (taking maximum for each expert)
3. Fullstack architecture and UX experts are prioritized

```yaml
frameworks:
  - React
  - Next.js

expert_priorities:
  expert-software-architecture: 1.0  # From Next.js
  expert-user-experience: 0.9        # From both
  expert-performance: 0.8            # From both
```

### Example 3: Custom Priority Override

To emphasize security in a FastAPI project:

```yaml
frameworks:
  - FastAPI

expert_priorities:
  expert-api-design: 1.0
  expert-security: 0.7

overrides:
  expert-security: 0.9  # Promote security expert
```

## Troubleshooting

### Priorities Not Applied

**Problem**: Experts aren't being prioritized as expected.

**Solutions**:
1. Verify `.tapps-agents/tech-stack.yaml` exists and contains `expert_priorities`
2. Check that frameworks are detected correctly (run `tapps-agents init` again)
3. Verify expert IDs match exactly (case-sensitive)
4. Check that expert registry is initialized with `project_root` parameter

### Framework Not Detected

**Problem**: Your framework isn't automatically detected.

**Solutions**:
1. Manually add framework to `.tapps-agents/tech-stack.yaml`
2. Verify dependency file exists (`requirements.txt`, `package.json`, etc.)
3. Check framework name matches supported frameworks list
4. Add custom priority mapping manually

### Overrides Not Working

**Problem**: Priority overrides aren't being applied.

**Solutions**:
1. Verify `overrides` section is under root level (not nested)
2. Check YAML syntax is correct (use `yaml.safe_load` to validate)
3. Ensure expert IDs match exactly (including `expert-` prefix)
4. Reinitialize expert registry to reload config

### Invalid Priority Values

**Problem**: Priority values must be between 0.0 and 1.0.

**Valid**:
- `1.0` (highest priority)
- `0.5` (medium priority)
- `0.0` (lowest priority, but expert still included)

**Invalid**:
- `1.5` (exceeds maximum)
- `-0.5` (negative)
- `"1.0"` (string instead of number)

## Backward Compatibility

The priority system is **fully backward compatible**:

- Projects without `.tapps-agents/tech-stack.yaml` work normally
- Expert registry functions without priorities (uses default ordering)
- All existing expert consultation code continues to work
- Priorities are optional enhancements, not requirements

## Best Practices

1. **Let the system auto-detect**: Run `tapps-agents init` to automatically detect and configure priorities
2. **Review generated priorities**: Check `.tapps-agents/tech-stack.yaml` after init to verify priorities make sense
3. **Use overrides sparingly**: Only override when you have specific needs
4. **Version control config**: Commit `.tapps-agents/tech-stack.yaml` to share priorities across team
5. **Update after stack changes**: Re-run `tapps-agents init` if you add/remove frameworks

## Related Documentation

- [Built-in Experts Guide](./BUILTIN_EXPERTS_GUIDE.md) - List of available experts
- [Expert Registry Documentation](../tapps_agents/experts/expert_registry.py) - API reference
- [Project Initialization Guide](./DEPLOYMENT.md) - Setup instructions

## Support

For issues or questions:
1. Check this guide's troubleshooting section
2. Review test examples in `tests/unit/core/test_tech_stack_priorities.py`
3. Check integration tests in `tests/integration/test_tech_stack_priority_integration.py`

