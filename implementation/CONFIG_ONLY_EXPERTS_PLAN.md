# Configuration-Only Experts Implementation Plan

**Date:** December 2025  
**Purpose:** Simplify expert creation by making experts purely configuration-driven instead of requiring code classes

## Problem Statement

Currently, creating a new expert requires writing a Python class that just wraps `BaseExpert.__init__()` with configuration parameters. This adds unnecessary boilerplate with no functional benefit.

**Current Pattern:**
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

**Proposed Pattern:**
```yaml
# .tapps-agents/experts.yaml
experts:
  - expert_id: expert-home-automation
    expert_name: Home Automation Expert
    primary_domain: home-automation
    rag_enabled: true
```

## Benefits

1. **Simpler**: No code required, just YAML
2. **Version Control Friendly**: Easy to see diffs
3. **Dynamic**: Add experts without code changes
4. **Consistent**: All experts use same BaseExpert logic
5. **Discoverable**: All experts in one config file

## Implementation Steps

### Phase 1: Update Core Components

1. **Create ExpertConfig Pydantic Model**
   - Define schema for expert configuration
   - Validation for required fields
   - Default values where appropriate

2. **Create Expert Config Loader**
   - Parse YAML config file
   - Validate against schema
   - Return list of ExpertConfig objects

3. **Remove Abstract Class Requirement**
   - Change `BaseExpert` from `ABC` to concrete class
   - All methods already have implementations (no abstract methods remain)

4. **Update ExpertRegistry**
   - Add `load_from_config()` method
   - Create `BaseExpert` instances from config
   - Register automatically

### Phase 2: Update Documentation

1. **Update PROJECT_REQUIREMENTS.md**
   - Change section 6.4 to show config-based approach
   - Update examples to use YAML

2. **Update KNOWLEDGE_BASE_GUIDE.md**
   - Replace code class examples with YAML
   - Show config-based expert creation

3. **Create EXPERT_CONFIG_GUIDE.md**
   - Complete guide for expert configuration
   - Examples and best practices

### Phase 3: Update Tests & Examples

1. **Update Unit Tests**
   - Test config loading
   - Test registry loading from config
   - Ensure backward compatibility (code classes still work)

2. **Update Examples**
   - Replace code examples with YAML
   - Add example expert config files

## Technical Details

### ExpertConfig Schema

```python
@dataclass
class ExpertConfig:
    expert_id: str
    expert_name: str
    primary_domain: str
    rag_enabled: bool = False
    fine_tuned: bool = False
    confidence_matrix: Optional[Dict[str, float]] = None
    mal_config: Optional[Dict[str, Any]] = None
```

### Config File Format

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

### ExpertRegistry Enhancement

```python
class ExpertRegistry:
    @classmethod
    def from_config_file(cls, config_file: Path) -> 'ExpertRegistry':
        """Load experts from YAML config file."""
        configs = load_expert_configs(config_file)
        registry = cls()
        for config in configs:
            expert = BaseExpert(
                expert_id=config.expert_id,
                expert_name=config.expert_name,
                primary_domain=config.primary_domain,
                rag_enabled=config.rag_enabled,
                fine_tuned=config.fine_tuned
            )
            registry.register_expert(expert)
        return registry
```

## Backward Compatibility

- Code-based expert classes still work (optional)
- Existing `register_expert(expert)` method unchanged
- Can mix config-based and code-based experts
- No breaking changes to BaseExpert API

## Files to Create/Modify

### New Files
- `tapps_agents/experts/expert_config.py` - Pydantic models and loader
- `docs/EXPERT_CONFIG_GUIDE.md` - Configuration guide

### Modified Files
- `tapps_agents/experts/base_expert.py` - Remove ABC, make concrete
- `tapps_agents/experts/expert_registry.py` - Add config loading
- `tapps_agents/experts/__init__.py` - Export ExpertConfig
- `requirements/PROJECT_REQUIREMENTS.md` - Update examples
- `docs/KNOWLEDGE_BASE_GUIDE.md` - Update examples
- `tests/unit/experts/` - Add config loading tests

## Testing Strategy

1. **Config Loading Tests**
   - Valid config parsing
   - Invalid config validation
   - Missing fields handling

2. **Registry Integration Tests**
   - Load from config
   - Mixed config + code experts
   - Weight matrix integration

3. **Backward Compatibility Tests**
   - Code-based experts still work
   - Existing tests pass

## Success Criteria

- ✅ Experts can be defined in YAML config
- ✅ ExpertRegistry loads from config file
- ✅ No code classes required for standard experts
- ✅ Backward compatible with code classes
- ✅ Documentation updated with examples
- ✅ All tests pass

