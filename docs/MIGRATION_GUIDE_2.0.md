# Migration Guide: 1.x to 2.0

**Version:** 2.0.6  
**Last Updated:** December 2025

## Overview

TappsCodingAgents 2.0 introduces a comprehensive built-in expert system with 6 new technical domain experts. This guide helps you migrate from version 1.x to 2.0.

## What's New in 2.0

### Built-in Experts

Six new built-in experts are automatically available:

1. **Security Expert** (`expert-security`) - OWASP Top 10, security patterns
2. **Performance Expert** (`expert-performance`) - Optimization, caching, scalability
3. **Testing Expert** (`expert-testing`) - Test strategies, patterns, best practices
4. **Data Privacy Expert** (`expert-data-privacy`) - GDPR, HIPAA, CCPA compliance
5. **Accessibility Expert** (`expert-accessibility`) - WCAG 2.1/2.2, ARIA patterns
6. **User Experience Expert** (`expert-user-experience`) - UX principles, usability heuristics

### Dual-Layer Architecture

- **Built-in Experts**: Framework-controlled, immutable, technical domains
- **Customer Experts**: User-controlled, configurable, business domains
- **Automatic Priority**: Technical domains prioritize built-in, business domains prioritize customer

### Enhanced Expert Registry

- Auto-loads built-in experts on initialization
- Priority-based consultation
- Weighted aggregation with 51% primary authority

## Migration Steps

### Step 1: Update Imports

**Before (1.x):**
```python
from tapps_agents.experts.registry import ExpertRegistry
```

**After (2.0):**
```python
from tapps_agents.experts import ExpertRegistry, BuiltinExpertRegistry, ExpertSupportMixin
```

### Step 2: Update Expert Registry Initialization

**Before (1.x):**
```python
registry = ExpertRegistry(config=config)
```

**After (2.0):**
```python
# Built-in experts are auto-loaded
registry = ExpertRegistry(domain_config=None, load_builtin=True)
```

### Step 3: Update Consultation Calls

**Before (1.x):**
```python
result = await registry.consult(
    domain="security",
    question="How to secure this?",
    context={...}
)
```

**After (2.0):**
```python
# For technical domains, prioritize built-in experts
result = await registry.consult(
    query="How to secure this?",
    domain="security",
    prioritize_builtin=True
)
```

### Step 4: Add Expert Support to Agents

**Before (1.x):**
```python
class MyAgent(BaseAgent):
    async def activate(self, project_root: Optional[Path] = None):
        await super().activate(project_root)
```

**After (2.0):**
```python
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
```

## Breaking Changes

### None!

Version 2.0 is **backward compatible**. All existing code continues to work:

- Existing expert registries still function
- Customer experts still work as before
- Old consultation API still works (with deprecation warnings)

## New Features You Can Use

### 1. Built-in Expert Consultation

```python
from tapps_agents.experts import ExpertRegistry

registry = ExpertRegistry(load_builtin=True)

# Consult security expert
result = await registry.consult(
    query="Review this code for security issues",
    domain="security",
    prioritize_builtin=True
)
```

### 2. Agent Integration with ExpertSupportMixin

```python
from tapps_agents.core.agent_base import BaseAgent
from tapps_agents.experts.agent_integration import ExpertSupportMixin

class ReviewerAgent(BaseAgent, ExpertSupportMixin):
    async def activate(self, project_root: Optional[Path] = None):
        await super().activate(project_root)
        await self._initialize_expert_support(project_root)
    
    async def review_security(self, code: str):
        result = await self._consult_builtin_expert(
            query=f"Review for security: {code}",
            domain="security"
        )
        return result.weighted_answer if result else "No issues found"
```

### 3. Automatic Domain Classification

The system automatically determines if a domain is technical or business:

```python
# Technical domain - built-in expert prioritized automatically
result = await registry.consult(
    query="How to optimize?",
    domain="performance-optimization"  # Technical domain
)

# Business domain - customer expert prioritized automatically
result = await registry.consult(
    query="How to handle checkout?",
    domain="e-commerce"  # Business domain
)
```

## Configuration Updates

### Expert Configuration (No Changes Required)

Your existing `.tapps-agents/experts.yaml` continues to work:

```yaml
experts:
  - expert_id: expert-ecommerce
    expert_name: E-commerce Expert
    primary_domain: e-commerce
    rag_enabled: true
    fine_tuned: false
```

Built-in experts are **not** defined in this file - they're automatically loaded.

### Domain Configuration (No Changes Required)

Your existing `.tapps-agents/domains.md` continues to work. Built-in experts are automatically added to the consultation process for technical domains.

## Knowledge Base Updates

### Built-in Knowledge Bases

Built-in expert knowledge bases are located in the framework package and are automatically available. You don't need to configure them.

### Customer Knowledge Bases

Your existing customer knowledge bases in `.tapps-agents/knowledge/` continue to work as before.

## Testing Updates

### Update Test Imports

```python
# Before
from tapps_agents.experts.registry import ExpertRegistry

# After
from tapps_agents.experts import ExpertRegistry, BuiltinExpertRegistry
```

### Test Built-in Experts

```python
def test_builtin_experts_loaded():
    registry = ExpertRegistry(load_builtin=True)
    assert "expert-security" in registry.builtin_experts
    assert "expert-performance" in registry.builtin_experts
```

## Common Migration Patterns

### Pattern 1: Adding Expert Support to Existing Agent

```python
# Before
class TesterAgent(BaseAgent):
    async def generate_tests(self, file: Path):
        # Generate tests
        pass

# After
class TesterAgent(BaseAgent, ExpertSupportMixin):
    async def activate(self, project_root: Optional[Path] = None):
        await super().activate(project_root)
        await self._initialize_expert_support(project_root)
    
    async def generate_tests(self, file: Path):
        # Consult testing expert
        result = await self._consult_builtin_expert(
            query=f"Best testing strategies for: {file.read_text()[:1000]}",
            domain="testing-strategies"
        )
        # Use expert advice in test generation
        pass
```

### Pattern 2: Using Built-in Experts in Workflows

```python
# Before
async def review_code(code: str):
    # Manual security review
    pass

# After
async def review_code(code: str):
    registry = ExpertRegistry(load_builtin=True)
    result = await registry.consult(
        query=f"Security review: {code}",
        domain="security",
        prioritize_builtin=True
    )
    return result.weighted_answer
```

## Troubleshooting

### Issue: Built-in Experts Not Loading

**Solution:** Ensure `load_builtin=True` when creating registry:

```python
registry = ExpertRegistry(domain_config=None, load_builtin=True)
```

### Issue: Expert Not Found

**Solution:** Check expert ID matches exactly:

```python
# List all available experts
experts = registry.list_experts()
print(experts)  # Check if expert exists
```

### Issue: Consultation Returns None

**Solution:** Ensure expert registry is initialized:

```python
# In agent activate method
await self._initialize_expert_support(project_root)

# Check if initialized
if self._has_expert_support():
    result = await self._consult_expert(...)
```

## Deprecation Warnings

Some old API methods may show deprecation warnings but still work:

- `ExpertRegistry(config=config)` - Use `ExpertRegistry(load_builtin=True)` instead
- Old `consult()` parameter names - Use `query` instead of `question`

## Next Steps

1. **Review Documentation**
   - [Built-in Experts Guide](./BUILTIN_EXPERTS_GUIDE.md)
   - [Expert Knowledge Base Guide](./EXPERT_KNOWLEDGE_BASE_GUIDE.md)
   - [API Documentation](./API.md)

2. **Update Agents**
   - Add `ExpertSupportMixin` to agents
   - Initialize expert support in `activate()` method
   - Use expert consultation in workflows

3. **Test Integration**
   - Test built-in expert consultation
   - Verify customer experts still work
   - Test priority system

## Support

For questions or issues during migration:

1. Check [Troubleshooting Guide](./TROUBLESHOOTING.md)
2. Review [API Documentation](./API.md)
3. See [Built-in Experts Guide](./BUILTIN_EXPERTS_GUIDE.md)

## Summary

- ✅ **Backward Compatible**: No breaking changes
- ✅ **Auto-Loading**: Built-in experts load automatically
- ✅ **Easy Integration**: Use `ExpertSupportMixin` for agents
- ✅ **Automatic Priority**: System determines expert priority
- ✅ **Enhanced Features**: New consultation patterns available

Migration is straightforward - update imports, add expert support to agents, and start using built-in experts!

