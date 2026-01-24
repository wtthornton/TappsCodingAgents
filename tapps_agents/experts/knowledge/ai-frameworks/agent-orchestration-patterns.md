# Agent Orchestration Patterns

## Overview

This guide covers patterns for orchestrating multiple AI agents to work together on complex tasks, including workflow management, context passing, and error handling.

## Core Patterns

### Pattern 1: Sequential Workflow

**Linear Execution:**
```python
async def sequential_workflow(agents: list, steps: list[dict]):
    """Execute agents in sequence."""
    context = {}
    
    for step in steps:
        agent = agents[step['agent_id']]
        result = await agent.execute(
            step['command'],
            context=context
        )
        context.update(result)
    
    return context
```

**Use Cases:**
- Requirements → Design → Implementation
- Analysis → Planning → Execution
- Review → Fix → Test

### Pattern 2: Parallel Execution

**Concurrent Agents:**
```python
import asyncio

async def parallel_workflow(agents: list, tasks: list[dict]):
    """Execute multiple agents in parallel."""
    tasks_list = [
        agents[task['agent_id']].execute(task['command'])
        for task in tasks
    ]
    results = await asyncio.gather(*tasks_list)
    return dict(zip([t['id'] for t in tasks], results))
```

**Use Cases:**
- Multiple file reviews
- Independent feature development
- Parallel testing

### Pattern 3: Conditional Execution

**Branching Workflows:**
```python
async def conditional_workflow(agents: list, workflow: dict):
    """Execute workflow with conditional branches."""
    result = await agents[workflow['start']].execute()
    
    if result['status'] == 'success':
        next_step = workflow['on_success']
    else:
        next_step = workflow['on_failure']
    
    return await agents[next_step].execute(context=result)
```

**Use Cases:**
- Quality gates (pass → continue, fail → fix)
- Error handling (success → next, error → retry)
- Feature flags (enabled → implement, disabled → skip)

### Pattern 4: Loop Until Success

**Iterative Improvement:**
```python
async def loop_until_success(agent, task: dict, max_iterations: int = 3):
    """Execute agent until success or max iterations."""
    for iteration in range(max_iterations):
        result = await agent.execute(task)
        
        if result['quality_score'] >= 70:
            return result
        
        # Improve based on feedback
        task['feedback'] = result['issues']
    
    raise Exception(f"Failed after {max_iterations} iterations")
```

**Use Cases:**
- Code quality improvement
- Test coverage improvement
- Security score improvement

### Pattern 5: Expert Consultation Integration

**Expert-Aware Orchestration:**
```python
class ExpertAwareOrchestrator:
    """Orchestrator that consults experts."""
    
    async def execute_with_expert_guidance(
        self,
        agent,
        task: dict,
        domain: str
    ):
        """Execute agent with expert consultation."""
        # Consult expert first
        expert_result = await self.expert_registry.consult(
            query=f"How should I {task['description']}?",
            domain=domain
        )
        
        # Include expert guidance in task
        task['expert_guidance'] = expert_result.weighted_answer
        
        # Execute agent with expert context
        return await agent.execute(task)
```

---

## Workflow Patterns

### Simple Mode Workflow

**7-Step Feature Development:**
```
1. Enhancer → Enhanced prompt with requirements
2. Planner → User stories with acceptance criteria
3. Architect → System architecture design
4. Designer → Component specifications
5. Implementer → Code implementation
6. Reviewer → Quality review (loop if < 70)
7. Tester → Test generation and execution
```

### Full SDLC Workflow

**9-Step Complete Lifecycle:**
```
1. Analyst → Requirements gathering
2. Planner → User stories
3. Architect → Architecture design
4. Designer → API design
5. Implementer → Code implementation
6. Reviewer → Quality review (loop if < 70)
7. Tester → Test generation
8. Ops → Security scanning
9. Documenter → Documentation generation
```

### Adaptive Learning Integration

**Self-Improving Workflow:**
```
1. Execute workflow
2. Track outcomes (scores, iterations, success)
3. Analyze patterns
4. Adjust weights (scoring, expert voting)
5. Generate new experts (if domains detected)
6. Improve knowledge bases
7. Repeat with better performance
```

---

## Best Practices

1. **Context Passing:**
   - Pass results between agents
   - Include relevant context
   - Maintain traceability
   - Track dependencies

2. **Error Handling:**
   - Graceful degradation
   - Retry logic
   - Fallback strategies
   - Clear error messages

3. **Quality Gates:**
   - Set thresholds
   - Loop on failure
   - Track improvements
   - Enforce standards

4. **Expert Integration:**
   - Consult proactively
   - Use expert knowledge
   - Track performance
   - Generate automatically

---

## References

- TappsCodingAgents Workflow System
- Simple Mode Documentation
- Adaptive Learning System
