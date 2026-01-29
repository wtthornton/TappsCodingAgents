# Integration Guide: Planning Time & Token Reduction Features

**Date:** 2026-01-29
**Status:** Integration Instructions
**Version:** 1.0

---

## Overview

This guide explains how to integrate the new planning time and token reduction features into your workflows.

**Features Available:**
1. ✅ Token Budget Monitoring with Warnings
2. ✅ mypy 6x Speedup (already active)
3. ✅ Workflow Preset Recommendations
4. ✅ Expert Response Caching
5. ✅ Checkpoint & Resume System

---

## 1. Token Budget Monitoring

### Quick Integration

**Option A: Use TokenAwareWorkflow Wrapper (Recommended)**

```python
from tapps_agents.workflow.executor import WorkflowExecutor
from tapps_agents.workflow.token_integration import TokenAwareWorkflow

# Create standard executor
executor = WorkflowExecutor()

# Wrap with token monitoring
monitored_executor = TokenAwareWorkflow(
    executor,
    token_budget=200000,  # Claude Sonnet 4.5 limit
    enable_auto_checkpoint=True
)

# Execute workflow with monitoring
result = await monitored_executor.execute_with_monitoring(workflow_def)

# Check token status
print(monitored_executor.get_token_status())
```

**Option B: Direct Integration into Workflow Steps**

```python
from tapps_agents.core.token_monitor import TokenMonitor, TokenBudget

class YourWorkflowOrchestrator:
    def __init__(self):
        self.token_monitor = TokenMonitor(TokenBudget(total=200000))

    async def execute_step(self, step):
        # Execute step
        result = await step.execute()

        # Estimate tokens (replace with actual API count)
        tokens = len(str(result)) // 4  # Rough estimate

        # Update monitor
        monitor_result = self.token_monitor.update(tokens)

        # Show warnings
        if monitor_result.message:
            print(monitor_result.message)

        # Auto-checkpoint at 90%
        if monitor_result.should_checkpoint:
            self.create_checkpoint()

        return result
```

### Testing

```bash
# Test token monitoring
python -c "
from tapps_agents.core.token_monitor import create_monitor

monitor = create_monitor(total=100000)
result = monitor.update(50000)  # 50%

print(f'Status: {result.threshold}')
print(f'Message: {result.message}')
"
```

---

## 2. mypy Optimization

**Status:** ✅ Already Active

The mypy optimization is already integrated in `tapps_agents/agents/reviewer/scoring.py`.

**Verification:**

```bash
# Time mypy execution
time python -m mypy --no-incremental --no-error-summary tapps_agents/core/token_monitor.py

# Should complete in <30 seconds (vs 60+ seconds before)
```

**No action needed** - optimization is active in all code reviews.

---

## 3. Workflow Preset Recommendations

### Integration into CLI

**File:** `tapps_agents/cli/commands/simple_mode.py`

```python
from tapps_agents.workflow.preset_recommender import recommend_preset

def simple_mode_build(prompt: str, preset: str = None, auto_recommend: bool = True):
    """Execute simple-mode build with optional preset recommendation."""

    # Auto-recommend if no preset specified
    if preset is None and auto_recommend:
        recommendation = recommend_preset(prompt)

        if recommendation.confidence > 0.8:
            print(f"\n{recommendation.format()}")

            # Ask for confirmation
            response = input("\nUse recommended preset? [Y/n]: ").strip()
            if response.lower() != 'n':
                preset = recommendation.preset
        else:
            preset = "standard"  # Default fallback

    # Execute with chosen preset
    workflow = get_workflow_for_preset(preset)
    return await workflow.execute(prompt)
```

### Testing

```python
from tapps_agents.workflow.preset_recommender import recommend_preset

# Test recommendations
test_cases = [
    "Fix typo in README",
    "Add user authentication system",
    "Refactor database layer",
    "Modify tapps_agents/core/agent.py"
]

for prompt in test_cases:
    rec = recommend_preset(prompt)
    print(f"Prompt: {prompt}")
    print(f"  → Preset: {rec.preset} ({rec.confidence:.0%} confidence)")
    print()
```

---

## 4. Expert Response Caching

### Integration into BaseExpert

**File:** `tapps_agents/experts/base_expert.py`

```python
from tapps_agents.experts.cache import ExpertCache

class BaseExpert:
    """Base expert class with caching support."""

    def __init__(self, cache_ttl_hours: int = 24):
        self.cache = ExpertCache(ttl_hours=cache_ttl_hours)
        self.experts_consulted = []

    async def consult(self, query: str, domain: str, **kwargs):
        """Consult experts with caching."""

        # Check cache first
        cached = self.cache.get(query, domain)
        if cached:
            logger.info(f"Expert cache hit for domain: {domain}")
            return {
                "response": cached.response,
                "experts": cached.experts_consulted,
                "cached": True,
                "timestamp": cached.timestamp
            }

        # Cache miss - consult experts
        logger.info(f"Expert cache miss for domain: {domain}")
        response = await self._consult_experts(query, domain, **kwargs)

        # Cache the response
        self.cache.put(
            query=query,
            domain=domain,
            response=response["data"],
            experts_consulted=response["experts"]
        )

        return {**response, "cached": False}

    async def _consult_experts(self, query: str, domain: str, **kwargs):
        """Original expert consultation logic."""
        # ... existing implementation ...
        pass
```

### Testing

```python
from tapps_agents.experts.cache import ExpertCache

cache = ExpertCache(ttl_hours=24)

# First query - cache miss
response1 = cache.get("performance tips", "async-programming")
print(f"First query: {response1}")  # None

# Cache the response
cache.put(
    query="performance tips",
    domain="async-programming",
    response={"tips": ["use asyncio", "avoid blocking"]},
    experts_consulted=["performance-expert", "async-expert"]
)

# Second query - cache hit!
response2 = cache.get("performance tips", "async-programming")
print(f"Second query: {response2.response}")  # {"tips": [...]}

# Check stats
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate_percentage']:.1f}%")
```

---

## 5. Checkpoint & Resume System

### Integration into CLI

**File:** `tapps_agents/cli/commands/checkpoint.py` (new file)

```python
from tapps_agents.workflow.checkpoint import CheckpointManager

def checkpoint_save_command(workflow_state: dict):
    """Save workflow checkpoint."""
    manager = CheckpointManager()
    checkpoint = manager.create_checkpoint(
        workflow_state,
        reason="user_request"
    )
    print(f"✅ Checkpoint saved: {checkpoint.checkpoint_id}")
    return checkpoint

def checkpoint_list_command():
    """List all checkpoints."""
    manager = CheckpointManager()
    checkpoints = manager.list_checkpoints()

    if not checkpoints:
        print("No checkpoints found.")
        return

    print("Available Checkpoints:")
    print("─" * 60)
    for cp in checkpoints:
        print(cp.format_summary())
        print("─" * 60)

def checkpoint_resume_command(checkpoint_id: str):
    """Resume workflow from checkpoint."""
    manager = CheckpointManager()
    state = manager.resume_from_checkpoint(checkpoint_id)

    # Continue workflow from restored state
    # ... workflow execution logic ...

    return state
```

**CLI Commands:**

```bash
# Save checkpoint during workflow
tapps-agents checkpoint save

# List available checkpoints
tapps-agents checkpoint list

# Resume from checkpoint
tapps-agents resume checkpoint-20260129-143022
```

### Testing

```python
from tapps_agents.workflow.checkpoint import CheckpointManager

manager = CheckpointManager()

# Create test checkpoint
test_state = {
    "workflow_id": "test-workflow-123",
    "workflow_type": "full-sdlc",
    "completed_steps": ["enhance", "requirements"],
    "current_step": "architecture",
    "pending_steps": ["design", "implement", "review"],
    "context": {"prompt": "Add feature"},
    "results": {"enhance": {...}, "requirements": {...}},
    "tokens_consumed": 45000,
    "tokens_remaining": 155000,
    "time_elapsed": 15.5
}

# Save checkpoint
checkpoint = manager.create_checkpoint(test_state, reason="test")
print(f"Checkpoint ID: {checkpoint.checkpoint_id}")

# Resume checkpoint
restored_state = manager.resume_from_checkpoint(checkpoint.checkpoint_id)
print(f"Restored workflow: {restored_state['workflow_type']}")
```

---

## 6. Lightweight SDLC Preset

### Create Preset Definition

**File:** `.tapps-agents/workflow-presets/lightweight.yaml`

```yaml
lightweight:
  name: "Lightweight SDLC"
  description: "Streamlined SDLC for medium-complexity tasks (50% faster)"

  steps:
    - name: enhance
      agent: enhancer
      config:
        mode: quick  # Use quick enhancement (stages 1-3 only)

    - name: requirements
      agent: analyst
      config:
        depth: standard
        skip_stakeholder_analysis: true

    - name: design
      agent: designer
      config:
        skip_architecture: true
        focus: api_design
        include_requirements_summary: true

    - name: implement
      agent: implementer
      config:
        auto_validate: true

    - name: review
      agent: reviewer
      config:
        quick_mode: true

    - name: test
      agent: tester
      config:
        min_coverage: 75

  estimated_time_minutes: 35
  estimated_tokens: 40000

  use_when:
    - "Medium complexity (5-7/10)"
    - "Clear requirements"
    - "No major architecture changes"
    - "Single component changes"
```

**Usage:**

```bash
tapps-agents simple-mode build --preset lightweight --prompt "Add validation logic"
```

---

## Integration Checklist

Use this checklist to track integration progress:

### Phase 1: Core Integration
- [ ] Token monitoring integrated into workflow executor
- [ ] Token warnings display during workflow execution
- [ ] Auto-checkpoint triggers at 90% threshold
- [ ] mypy optimization verified (confirmed working)

### Phase 2: CLI Integration
- [ ] Preset recommender added to `simple-mode build` command
- [ ] Checkpoint commands added (`save`, `list`, `resume`)
- [ ] Token status command added
- [ ] Help text updated with new features

### Phase 3: Expert System Integration
- [ ] Expert cache integrated into BaseExpert
- [ ] Cache statistics displayed in workflow reports
- [ ] Cache hit rate monitored
- [ ] TTL configuration exposed

### Phase 4: Documentation
- [ ] User guide created for each feature
- [ ] API documentation updated
- [ ] Example scripts added
- [ ] Video tutorials created (optional)

---

## Performance Verification

After integration, verify the improvements:

### Token Budget Monitoring
```bash
# Should see warnings at 50%, 75%, 90%
tapps-agents simple-mode full --prompt "test" --verbose
```

### mypy Performance
```bash
# Should complete in <30s
time tapps-agents reviewer review tapps_agents/core/token_monitor.py
```

### Preset Recommendations
```bash
# Should recommend appropriate preset
tapps-agents simple-mode build --prompt "Add authentication" --show-recommendation
```

### Expert Cache Hit Rate
```python
from tapps_agents.experts.cache import ExpertCache
cache = ExpertCache()
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate_percentage']:.1f}%")
# Target: 40-60% after warmup
```

---

## Troubleshooting

### Token Monitor Not Showing Warnings

**Problem:** No warnings displayed at 50%/75%/90%

**Solution:**
```python
# Check if warnings are enabled
monitor.enable_warnings = True

# Manually trigger warning
result = monitor.update(100000)  # Force 50%
print(result.message)
```

### mypy Still Slow

**Problem:** mypy taking >30 seconds

**Solution:**
```bash
# Verify --no-incremental flag is used
python -m mypy --no-incremental --no-error-summary file.py

# Check if running on entire project (should be single file)
# Look in tapps_agents/agents/reviewer/scoring.py
```

### Cache Not Working

**Problem:** Cache hit rate is 0%

**Solution:**
```python
# Check cache is enabled
cache.enable_disk_cache = True

# Verify cache directory exists
cache.cache_dir.mkdir(parents=True, exist_ok=True)

# Test cache manually
cache.put("test", "domain", {"data": "test"}, ["expert1"])
result = cache.get("test", "domain")
print(result)  # Should not be None
```

### Checkpoint Save Fails

**Problem:** Checkpoint creation errors

**Solution:**
```python
# Check directory permissions
checkpoint_dir = Path(".tapps-agents/checkpoints")
checkpoint_dir.mkdir(parents=True, exist_ok=True)

# Verify workflow state has required fields
required_fields = [
    "workflow_id", "workflow_type", "completed_steps",
    "current_step", "pending_steps", "context", "results"
]
for field in required_fields:
    assert field in workflow_state, f"Missing: {field}"
```

---

## Next Steps

1. **Week 1:** Integrate token monitoring and preset recommender
2. **Week 2:** Integrate expert cache and checkpoint system
3. **Week 3:** Performance testing and benchmarking
4. **Week 4:** Documentation and user training

---

**Questions?** See the implementation files:
- [tapps_agents/core/token_monitor.py](../../tapps_agents/core/token_monitor.py)
- [tapps_agents/workflow/preset_recommender.py](../../tapps_agents/workflow/preset_recommender.py)
- [tapps_agents/workflow/checkpoint.py](../../tapps_agents/workflow/checkpoint.py)
- [tapps_agents/experts/cache.py](../../tapps_agents/experts/cache.py)
- [tapps_agents/workflow/token_integration.py](../../tapps_agents/workflow/token_integration.py)

**Status:** Ready for Integration
**Last Updated:** 2026-01-29
