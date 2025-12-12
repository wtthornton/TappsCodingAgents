# Reviewer Agent Implementation Plan

> **Status Note (2025-12-11):** This file is a historical snapshot.  
> **Canonical status:** See `implementation/IMPLEMENTATION_STATUS.md`.

**Approach:** Spike-First (Option B)  
**Goal:** Build working reviewer agent to extract API patterns  
**Status:** In Progress

---

## Phase 1: Proof of Concept (Week 1) - UPDATED with BMAD Patterns

### Goal
Build a minimal working reviewer agent that can:
- Review code files
- Generate Code Scores
- Provide feedback
- Use star-prefixed commands (`*review`, `*score`, `*help`)
- Follow activation instructions pattern

### Deliverables

1. **Core Package Structure**
   ```
   tapps_agents/
   ├── __init__.py
   ├── core/
   │   ├── __init__.py
   │   ├── agent.py          # Base agent class
   │   └── mal.py            # Model Abstraction Layer (simplified)
   ├── agents/
   │   ├── __init__.py
   │   └── reviewer/
   │       ├── __init__.py
   │       ├── agent.py      # Reviewer agent implementation
   │       └── scoring.py    # Code scoring logic
   └── cli.py                # Command-line interface
   ```

2. **Minimal Reviewer Agent**
   - Read code files
   - Calculate basic scores (complexity, security)
   - Generate review output

3. **Simple MAL**
   - Route to Ollama (local)
   - Basic fallback to cloud (optional)

### Acceptance Criteria

- [ ] Can invoke reviewer via CLI: `python -m tapps_agents review path/to/file.py`
- [ ] Returns JSON with scores and feedback
- [ ] Works with local Ollama model
- [ ] Basic code scoring implemented (complexity, security)

---

## Phase 2: Extract API Patterns (Week 1-2)

### Goal
Based on reviewer implementation, formalize:
- Agent interface (`run()`, `validate()`)
- Input/output schemas
- Error handling

### Deliverables

1. **Agent API Contract** (`agent_api.md`)
2. **JSON Schemas** (input, output, error)
3. **Base Agent Class** (for reuse)

---

## Phase 3: Enhance Reviewer (Week 2)

### Goal
Add missing features from requirements:
- Tiered Context (Tier 2 for reviewer)
- Full Code Scoring (5 metrics)
- Quality Gates

---

## Implementation Steps

### Step 1: Setup (Today)
- [x] Create implementation plan
- [ ] Create Python package structure
- [ ] Setup dependencies (requirements.txt)
- [ ] Create minimal reviewer agent skeleton

### Step 2: Core Reviewer (Days 1-2)
- [x] Implement file reading
- [x] Implement basic scoring (complexity, security)
- [x] Implement MAL routing to Ollama
- [x] Create CLI interface

### Step 2a: BMAD Patterns (Days 2-3) - NEW
- [ ] Add star-prefixed commands (`*review`, `*score`, `*help`)
- [ ] Implement activation instructions in agent definition
- [ ] Add command discovery system (numbered lists)
- [ ] Update CLI to support both `*command` and `command` formats

### Step 3: Test & Iterate (Days 2-3)
- [ ] Test with real code files
- [ ] Refine scoring algorithms
- [ ] Extract API patterns

### Step 4: Documentation (Day 3)
- [ ] Document API patterns found
- [ ] Update agent_api.md
- [ ] Create usage examples

---

## Technical Decisions (TBD during implementation)

1. **Scoring Library**: Use existing (radon, pylint) or build custom?
2. **LLM Integration**: Direct Ollama API or wrapper library?
3. **Output Format**: JSON, Markdown, or both?
4. **Configuration**: YAML config file or CLI flags?

---

## Success Metrics

- ✅ Reviewer works end-to-end on real code
- ✅ Scores are meaningful and useful
- ✅ API patterns extracted and documented
- ✅ Can be used as template for other agents
- ✅ Star commands work (`*review`, `*help`)
- ✅ Activation instructions followed
- ✅ Command discovery shows numbered options

---

## BMAD-METHOD Integration (NEW)

### High Priority Patterns to Implement

1. **Star-Prefixed Commands** (P0) - ✅ In progress
   - CLI: `*review file.py`
   - Agent: `*help` shows numbered list
   
2. **Activation Instructions** (P0) - ✅ In progress
   - Standardized startup sequence
   - Load config, greet, run *help, wait
   
3. **Workflow Enhancements** (P0) - ⏳ Next
   - Conditions, optional_steps, notes, repeats

4. **Scale-Adaptive** (P1) - ⏳ Next
   - `*workflow-init` command
   - Auto-detect project type

---

**Next Action:** Implement star commands and activation instructions for reviewer agent.

