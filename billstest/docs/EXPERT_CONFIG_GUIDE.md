# Expert Configuration Guide

**Configuration-Only Expert Definition**

This guide explains how to define Industry Experts using YAML configuration files instead of code classes.

## Overview

Experts are now **configuration-only** - no code classes required! Define them in YAML and the framework handles the rest.

## Configuration File

Create `.tapps-agents/experts.yaml` in your project root:

```yaml
# .tapps-agents/experts.yaml
experts:
  - expert_id: expert-home-automation
    expert_name: Home Automation Expert
    primary_domain: home-automation
    rag_enabled: true
    fine_tuned: false
  
  - expert_id: expert-healthcare
    expert_name: Healthcare Domain Expert
    primary_domain: healthcare
    rag_enabled: true
    fine_tuned: false
```

## Configuration Fields

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `expert_id` | string | Unique identifier, must match domain's primary expert | `expert-home-automation` |
| `expert_name` | string | Human-readable name | `Home Automation Expert` |
| `primary_domain` | string | Domain where expert has 51% authority | `home-automation` |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `rag_enabled` | boolean | `false` | Enable knowledge base RAG retrieval |
| `fine_tuned` | boolean | `false` | Use fine-tuned models (future feature) |
| `confidence_matrix` | object | `null` | Custom confidence weights per domain (usually auto-calculated) |
| `mal_config` | object | `null` | Optional MAL-specific configuration |

## Complete Example

```yaml
# .tapps-agents/experts.yaml
experts:
  # Home Automation Expert
  - expert_id: expert-home-automation
    expert_name: Home Automation Expert
    primary_domain: home-automation
    rag_enabled: true
    fine_tuned: false
  
  # Healthcare Expert
  - expert_id: expert-healthcare
    expert_name: Healthcare Domain Expert
    primary_domain: healthcare
    rag_enabled: true
    fine_tuned: false
  
  # Energy Management Expert
  - expert_id: expert-energy
    expert_name: Energy Management Expert
    primary_domain: energy-management
    rag_enabled: true
    fine_tuned: false
```

## Loading Experts

### From Configuration File

```python
from pathlib import Path
from tapps_agents.experts import ExpertRegistry, DomainConfigParser

# Load domain configuration
domain_config = DomainConfigParser.parse(Path(".tapps-agents/domains.md"))

# Load experts from config file
registry = ExpertRegistry.from_config_file(
    Path(".tapps-agents/experts.yaml"),
    domain_config=domain_config
)

# Experts are now loaded and ready to use
expert = registry.get_expert("expert-home-automation")
```

### Mixed Approach (Config + Code)

You can still register code-based experts if needed:

```python
from tapps_agents.experts import BaseExpert, ExpertRegistry

# Load from config
registry = ExpertRegistry.from_config_file(...)

# Add custom expert (if needed for advanced customization)
custom_expert = BaseExpert(
    expert_id="expert-custom",
    expert_name="Custom Expert",
    primary_domain="custom-domain",
    rag_enabled=True
)
registry.register_expert(custom_expert)
```

## Expert ID Naming Convention

Follow this pattern for `expert_id`:

```
expert-{domain-name}
```

Examples:
- `expert-home-automation`
- `expert-healthcare`
- `expert-energy-management`
- `expert-financial-services`

The `expert_id` must match the `primary_expert_id` in your `domains.md` file for each domain.

## RAG Configuration

When `rag_enabled: true`, the expert automatically:

1. **Looks for knowledge base** in `.tapps-agents/knowledge/{primary_domain}/`
2. **Falls back to** `.tapps-agents/knowledge/` if domain-specific directory doesn't exist
3. **Loads markdown files** (*.md) as knowledge sources
4. **Enables search** via `*consult` and `*provide-context` commands

See [Knowledge Base Guide](KNOWLEDGE_BASE_GUIDE.md) for details.

## Domain Configuration Integration

Experts are linked to domains via `domains.md`:

```markdown
# domains.md

## Project: My Project

### Domain 1: Home Automation
- Primary Expert: expert-home-automation
- Description...
```

The `expert_id` in `experts.yaml` must match the `primary_expert_id` in `domains.md`.

## Validation

The configuration loader validates:

- ✅ Required fields present
- ✅ Expert IDs match domain primary experts
- ✅ YAML syntax correct
- ✅ Type checking (strings, booleans, etc.)

**Validation Errors:**

```python
# Missing required field
ValueError: Invalid expert configuration at index 0: 
Field 'expert_id' is required

# Invalid YAML
ValueError: Invalid YAML in experts.yaml: ...
```

## Best Practices

### 1. One Expert Per Domain

Each domain should have exactly one primary expert:

```yaml
# ✅ Good: One expert per domain
experts:
  - expert_id: expert-home-automation
    primary_domain: home-automation
  - expert_id: expert-healthcare
    primary_domain: healthcare
```

### 2. Enable RAG for Domain Experts

Most experts should have RAG enabled:

```yaml
# ✅ Good: RAG enabled for knowledge retrieval
- expert_id: expert-home-automation
  rag_enabled: true
```

### 3. Consistent Naming

Use consistent naming patterns:

```yaml
# ✅ Good: Consistent naming
- expert_id: expert-home-automation
  expert_name: Home Automation Expert
  primary_domain: home-automation
```

### 4. Version Control

Commit `experts.yaml` to version control:

```bash
# Add to git
git add .tapps-agents/experts.yaml
git commit -m "Add expert configurations"
```

## Troubleshooting

### Expert Not Found

**Problem:** `ValueError: Expert 'expert-id' not found in weight matrix`

**Solution:** Ensure `expert_id` matches `primary_expert_id` in `domains.md`

### RAG Not Working

**Problem:** Knowledge base searches return no results

**Solution:**
1. Check `rag_enabled: true` in config
2. Verify knowledge files exist: `.tapps-agents/knowledge/{domain}/`
3. Check file permissions and encoding (UTF-8)

### Configuration Not Loading

**Problem:** `FileNotFoundError: Expert configuration file not found`

**Solution:**
1. Create `.tapps-agents/experts.yaml`
2. Check file path is correct
3. Ensure YAML syntax is valid

## Migration from Code Classes

If you have existing code-based expert classes:

**Before (Code Class):**
```python
class HomeAutomationExpert(BaseExpert):
    def __init__(self):
        super().__init__(
            expert_id="expert-home-automation",
            expert_name="Home Automation Expert",
            primary_domain="home-automation",
            rag_enabled=True
        )
```

**After (Configuration):**
```yaml
# .tapps-agents/experts.yaml
experts:
  - expert_id: expert-home-automation
    expert_name: Home Automation Expert
    primary_domain: home-automation
    rag_enabled: true
```

Then load from config:
```python
registry = ExpertRegistry.from_config_file(Path(".tapps-agents/experts.yaml"))
```

## See Also

- [Knowledge Base Guide](KNOWLEDGE_BASE_GUIDE.md) - Setting up knowledge bases
- [Domain Configuration](../requirements/PROJECT_REQUIREMENTS.md#12-domain-configuration) - Domain definitions
- [Expert Registry API](EXPERT_REGISTRY_API.md) - Programmatic usage

