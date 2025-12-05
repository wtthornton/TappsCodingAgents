# TappsCodingAgents - Complete Implementation Plan

**Date:** December 2025  
**Version:** 1.0  
**Status:** Planning  
**Current Phase:** Spike-First (Reviewer Agent Complete)

---

## Executive Summary

This document outlines the complete implementation plan for TappsCodingAgents, from the current state (1 agent implemented, 0% test coverage) to a production-ready framework with all 12 workflow agents, Industry Experts, and comprehensive testing.

**Current State:**
- ✅ 1/12 workflow agents (reviewer)
- ✅ Basic MAL (Ollama only)
- ✅ Code Scoring (3/5 metrics)
- ✅ Star commands + activation instructions
- ❌ 0% test coverage
- ❌ 11 agents not implemented
- ❌ Major features missing (Tiered Context, MCP Gateway, workflows, etc.)

**Target State:**
- ✅ All 12 workflow agents
- ✅ Complete MAL with cloud fallback
- ✅ Full Code Scoring (5/5 metrics)
- ✅ 80%+ test coverage
- ✅ Tiered Context system
- ✅ MCP Gateway
- ✅ Workflow engine
- ✅ Industry Experts framework
- ✅ Production-ready

---

## Implementation Strategy

### Principles

1. **Test-First Development** - Write tests alongside features
2. **Incremental Delivery** - Each phase delivers working functionality
3. **Spike-Extract Pattern** - Continue spike-first, extract patterns
4. **Quality Gates** - No feature complete without tests
5. **Documentation** - Update docs as we build

### Phases Overview

```
Phase 1: Foundation & Testing (Week 1-2)
  → Test suite setup
  → Fix critical issues
  → Complete reviewer agent

Phase 2: Core Agents (Week 3-6)
  → Implement 5 critical agents
  → Extract common patterns
  → Standardize agent API

Phase 3: Advanced Features (Week 7-10)
  → Tiered Context
  → MCP Gateway
  → Workflow engine

Phase 4: Remaining Agents (Week 11-14)
  → Complete all 12 agents
  → Industry Experts framework
  → RAG integration

Phase 5: Polish & Production (Week 15-16)
  → Performance optimization
  → Comprehensive testing
  → Documentation
  → Release prep
```

---

## Phase 1: Foundation & Testing (Week 1-2)

**Goal:** Establish testing foundation and fix critical issues

### Week 1: Test Suite Setup

#### Day 1-2: Test Infrastructure

**Tasks:**
- [ ] Set up pytest + pytest-asyncio
- [ ] Create `tests/` directory structure
- [ ] Add test configuration (`pytest.ini`, `conftest.py`)
- [ ] Set up test fixtures (mock MAL, test data)
- [ ] Add coverage reporting (pytest-cov)
- [ ] Configure CI/CD test runs (GitHub Actions)

**Deliverables:**
```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_agent_base.py
│   ├── test_scoring.py
│   └── test_mal.py
├── integration/
│   └── test_reviewer_agent.py
└── fixtures/
    └── sample_code.py
```

**Success Criteria:**
- ✅ pytest runs successfully
- ✅ Coverage reporting works
- ✅ CI/CD runs tests on push

---

#### Day 3-4: Critical Fixes

**Tasks:**
- [ ] Fix type hint compatibility (`from __future__ import annotations`)
- [ ] Improve error handling (specific exceptions)
- [ ] Add input validation (path traversal, file size)
- [ ] Extract hardcoded config to config.yaml
- [ ] Remove unused imports
- [ ] Add missing docstrings

**Files to Update:**
- `tapps_agents/core/agent_base.py`
- `tapps_agents/agents/reviewer/agent.py`
- `tapps_agents/agents/reviewer/scoring.py`
- `tapps_agents/core/mal.py`
- `tapps_agents/cli.py`

**Success Criteria:**
- ✅ All type hints work on Python 3.9+
- ✅ Specific exception types used
- ✅ Config loaded from YAML
- ✅ Path validation prevents traversal attacks

---

#### Day 5: Test Reviewer Agent

**Tasks:**
- [ ] Unit tests for CodeScorer
  - Test complexity calculation
  - Test security scanning
  - Test maintainability index
  - Test error handling (no radon/bandit)
- [ ] Unit tests for ReviewerAgent
  - Test command parsing
  - Test activation sequence
  - Test help formatting
- [ ] Integration tests
  - Test full review workflow
  - Test scoring only workflow
  - Test error cases

**Target Coverage:** 80% for reviewer agent

**Success Criteria:**
- ✅ 80%+ test coverage for reviewer agent
- ✅ All edge cases tested
- ✅ Mock LLM responses (no Ollama required for tests)

---

### Week 2: Complete Reviewer + Config System

#### Day 1-2: Configuration System

**Tasks:**
- [ ] Create configuration schema (Pydantic models)
- [ ] Implement config loader (YAML → Config object)
- [ ] Add config validation
- [ ] Update BaseAgent to use config
- [ ] Create default config template
- [ ] Add config documentation

**Files to Create:**
```
tapps_agents/
├── core/
│   ├── config.py          # Config models and loader
│   └── config_schema.yaml # Schema definition
├── templates/
│   └── default_config.yaml
```

**Success Criteria:**
- ✅ Config loaded from `.tapps-agents/config.yaml`
- ✅ Validation on load (type checking, required fields)
- ✅ Sensible defaults if config missing
- ✅ Documentation for config options

---

#### Day 3-4: Complete Scoring Metrics

**Tasks:**
- [ ] Implement test coverage metric
  - Integrate coverage.py or pytest-cov
  - Parse coverage reports
  - Calculate coverage score (0-100%)
- [ ] Implement performance metric
  - Static analysis (function size, nesting depth)
  - Pattern detection (N+1 queries, inefficient loops)
  - Heuristic-based scoring
- [ ] Update scoring weights
- [ ] Add tests for new metrics

**Success Criteria:**
- ✅ All 5 metrics working
- ✅ Tests for new metrics
- ✅ Updated overall score calculation

---

#### Day 5: Reviewer Agent Tests + Refinement

**Tasks:**
- [ ] Complete test coverage for reviewer
- [ ] Test configuration integration
- [ ] Test all scoring metrics
- [ ] Performance testing (large files)
- [ ] Update documentation

**Success Criteria:**
- ✅ 85%+ test coverage
- ✅ All features tested
- ✅ Performance acceptable (<5s for 1000-line file)

---

### Phase 1 Deliverables

- ✅ Test suite infrastructure
- ✅ 80%+ test coverage for reviewer agent
- ✅ Critical issues fixed
- ✅ Configuration system working
- ✅ Complete scoring (5/5 metrics)

---

## Phase 2: Core Agents (Week 3-6)

**Goal:** Implement 5 critical workflow agents and extract patterns

### Agent Selection (Priority Order)

1. **planner** - Story/epic planning (high usage)
2. **implementer** - Code generation (core feature)
3. **tester** - Test generation (complements reviewer)
4. **debugger** - Error diagnosis (high value)
5. **documenter** - Documentation generation (completes cycle)

### Week 3: Planner Agent

**Pattern:** Planning + Story Creation

**Tasks:**
- [ ] Create `tapps_agents/agents/planner/`
- [ ] Implement PlannerAgent extending BaseAgent
- [ ] Add commands: `*plan`, `*create-story`, `*list-stories`
- [ ] Story template (YAML or Markdown)
- [ ] Integration with project structure
- [ ] Tests (unit + integration)

**Agent Capabilities:**
- Parse requirements/PRD
- Generate user stories
- Estimate complexity
- Create story files

**Files:**
```
tapps_agents/agents/planner/
├── __init__.py
├── agent.py
├── story_template.md
└── tests/
    ├── test_planner_agent.py
    └── test_story_generation.py
```

**Success Criteria:**
- ✅ Planner generates valid stories
- ✅ Stories follow template
- ✅ 80%+ test coverage
- ✅ Integration with project structure works

---

### Week 4: Implementer Agent

**Pattern:** Code Generation + File Writing

**Tasks:**
- [ ] Create `tapps_agents/agents/implementer/`
- [ ] Implement ImplementerAgent
- [ ] Add commands: `*implement`, `*generate-code`, `*refactor`
- [ ] Code generation prompts
- [ ] File writing with safety checks
- [ ] Code review before writing (use ReviewerAgent)
- [ ] Tests

**Agent Capabilities:**
- Generate code from specs
- Refactor existing code
- Write files with approval
- Integrate with reviewer for quality

**Files:**
```
tapps_agents/agents/implementer/
├── __init__.py
├── agent.py
├── code_generator.py
└── tests/
    └── test_implementer_agent.py
```

**Success Criteria:**
- ✅ Generates valid code
- ✅ Reviews code before writing
- ✅ Safety checks (no overwrite without approval)
- ✅ 80%+ test coverage

---

### Week 5: Tester Agent

**Pattern:** Test Generation + Execution

**Tasks:**
- [ ] Create `tapps_agents/agents/tester/`
- [ ] Implement TesterAgent
- [ ] Add commands: `*test`, `*generate-tests`, `*run-tests`
- [ ] Test generation from code analysis
- [ ] Integration with pytest
- [ ] Test execution and reporting
- [ ] Tests

**Agent Capabilities:**
- Generate unit tests
- Generate integration tests
- Run test suites
- Report coverage

**Files:**
```
tapps_agents/agents/tester/
├── __init__.py
├── agent.py
├── test_generator.py
└── tests/
    └── test_tester_agent.py
```

**Success Criteria:**
- ✅ Generates working tests
- ✅ Runs pytest successfully
- ✅ Reports results
- ✅ 80%+ test coverage

---

### Week 6: Debugger + Documenter Agents

**Pattern:** Analysis + Documentation

**Debugger Agent:**
- [ ] Create `tapps_agents/agents/debugger/`
- [ ] Implement DebuggerAgent
- [ ] Commands: `*debug`, `*analyze-error`, `*trace`
- [ ] Error analysis (stack traces, logs)
- [ ] Code path tracing
- [ ] Suggestions for fixes

**Documenter Agent:**
- [ ] Create `tapps_agents/agents/documenter/`
- [ ] Implement DocumenterAgent
- [ ] Commands: `*document`, `*generate-docs`, `*update-readme`
- [ ] Generate API docs
- [ ] Generate README
- [ ] Update docstrings

**Success Criteria:**
- ✅ Both agents working
- ✅ 80%+ test coverage each
- ✅ Integration tests pass

---

### Phase 2 Deliverables

- ✅ 5 core agents implemented
- ✅ Common patterns extracted
- ✅ Agent API standardized
- ✅ 80%+ test coverage for all agents
- ✅ Documentation updated

---

## Phase 3: Advanced Features (Week 7-10)

### Week 7: Tiered Context System

**Goal:** Implement 90%+ token savings through intelligent context management

**Tasks:**
- [ ] Design context tier definitions
  - Tier 1: Core (function signatures, class names)
  - Tier 2: Extended (functions + docstrings)
  - Tier 3: Full (entire file)
- [ ] Implement context manager
- [ ] Add caching (LRU cache for parsed AST)
- [ ] Create context builder
- [ ] Integration with agents
- [ ] Tests

**Files:**
```
tapps_agents/core/
├── context_manager.py      # Main context management
├── tiered_context.py       # Tier definitions
└── ast_parser.py           # AST parsing for context
```

**Success Criteria:**
- ✅ Context tiers working
- ✅ 90%+ token savings demonstrated
- ✅ Performance acceptable (caching works)
- ✅ Tests with real codebases

---

### Week 8: MCP Gateway

**Goal:** Unified interface for MCP tool access

**Tasks:**
- [ ] Design MCP Gateway architecture
- [ ] Implement gateway server
- [ ] Add tool registration system
- [ ] Create adapters for common tools
  - Filesystem operations
  - Git operations
  - Code analysis tools
- [ ] Integration with agents
- [ ] Tests

**Files:**
```
tapps_agents/core/
├── mcp_gateway.py          # Gateway server
├── mcp_tools.py            # Tool definitions
└── adapters/
    ├── filesystem.py
    ├── git.py
    └── analysis.py
```

**Success Criteria:**
- ✅ MCP Gateway responds to requests
- ✅ Tools registered and accessible
- ✅ Integration with agents works
- ✅ Tests with mock MCP servers

---

### Week 9-10: Workflow Engine

**Goal:** YAML-based workflow orchestration

**Tasks:**
- [ ] Workflow YAML parser
- [ ] Workflow executor
- [ ] Step execution engine
- [ ] Conditional execution
- [ ] Artifact tracking
- [ ] Greenfield/Brownfield detection
- [ ] `*workflow-init` command
- [ ] Tests

**Files:**
```
tapps_agents/core/
├── workflow/
│   ├── parser.py           # YAML parser
│   ├── executor.py         # Execution engine
│   ├── detector.py         # Project type detection
│   └── workflows/
│       ├── greenfield.yaml
│       ├── brownfield.yaml
│       └── quick-fix.yaml
```

**Success Criteria:**
- ✅ Workflows execute correctly
- ✅ Conditions work
- ✅ Artifacts tracked
- ✅ Auto-detection works
- ✅ 80%+ test coverage

---

### Phase 3 Deliverables

- ✅ Tiered Context system
- ✅ MCP Gateway
- ✅ Workflow engine
- ✅ All features tested
- ✅ Performance validated

---

## Phase 4: Remaining Agents + Experts (Week 11-14)

### Week 11: Analyst + Architect + Designer

**Analyst Agent:**
- [ ] Requirements gathering
- [ ] Stakeholder analysis
- [ ] Competitive research

**Architect Agent:**
- [ ] System design
- [ ] Architecture diagrams
- [ ] Technology selection

**Designer Agent:**
- [ ] UI/UX design
- [ ] Wireframes
- [ ] Design specs

**Success Criteria:**
- ✅ All 3 agents working
- ✅ 80%+ test coverage
- ✅ Integration tests

---

### Week 12: Improver + Ops Agents

**Improver Agent:**
- [ ] Code refactoring
- [ ] Performance optimization
- [ ] Code quality improvements

**Ops Agent:**
- [ ] Deployment planning
- [ ] Infrastructure as code
- [ ] Monitoring setup

**Success Criteria:**
- ✅ Both agents working
- ✅ 80%+ test coverage

---

### Week 13: Orchestrator Agent

**Orchestrator Agent:**
- [ ] Multi-agent coordination
- [ ] Workflow management
- [ ] Task distribution
- [ ] Result aggregation

**Success Criteria:**
- ✅ Orchestrates multiple agents
- ✅ Manages workflows
- ✅ 80%+ test coverage

---

### Week 14: Industry Experts Framework

**Goal:** Business domain knowledge layer

**Tasks:**
- [ ] Expert agent base class
- [ ] Weight distribution algorithm (51% primary)
- [ ] RAG integration per expert
- [ ] Fine-tuning support (LoRA adapters)
- [ ] Domain configuration system
- [ ] Decision aggregation
- [ ] Tests

**Files:**
```
tapps_agents/experts/
├── base_expert.py          # Base class
├── weight_distributor.py   # 51% algorithm
├── rag_interface.py        # RAG integration
└── fine_tuning.py          # LoRA support
```

**Success Criteria:**
- ✅ Experts can be created
- ✅ Weight distribution works correctly
- ✅ RAG integration functional
- ✅ Fine-tuning setup works
- ✅ 80%+ test coverage

---

### Phase 4 Deliverables

- ✅ All 12 workflow agents
- ✅ Industry Experts framework
- ✅ RAG integration
- ✅ Fine-tuning support
- ✅ Complete test coverage

---

## Phase 5: Polish & Production (Week 15-16)

### Week 15: Performance & Optimization

**Tasks:**
- [ ] Performance profiling
- [ ] Optimize slow paths
- [ ] Add caching where needed
- [ ] Memory optimization
- [ ] Concurrent request handling
- [ ] Load testing

**Success Criteria:**
- ✅ All operations <5s
- ✅ Memory usage acceptable
- ✅ Concurrent requests work

---

### Week 16: Final Testing & Documentation

**Tasks:**
- [ ] Complete test suite
  - End-to-end tests
  - Integration tests
  - Performance tests
  - Security tests
- [ ] Achieve 80%+ overall coverage
- [ ] Update all documentation
- [ ] Create migration guide
- [ ] Release notes
- [ ] Quick start guide

**Success Criteria:**
- ✅ 80%+ overall test coverage
- ✅ All documentation updated
- ✅ Release-ready

---

## Testing Strategy

### Test Pyramid

```
        /\
       /  \     E2E Tests (10%)
      /____\
     /      \   Integration Tests (30%)
    /________\
   /          \  Unit Tests (60%)
  /____________\
```

### Test Categories

#### Unit Tests (60% of tests)
- **Coverage:** Individual functions/methods
- **Speed:** Fast (<1s each)
- **Scope:** Isolated, mocked dependencies
- **Examples:**
  - `test_complexity_calculation()`
  - `test_config_loading()`
  - `test_command_parsing()`

#### Integration Tests (30% of tests)
- **Coverage:** Agent workflows
- **Speed:** Medium (1-5s each)
- **Scope:** Real dependencies, mocked LLM
- **Examples:**
  - `test_reviewer_full_workflow()`
  - `test_planner_story_creation()`
  - `test_workflow_execution()`

#### End-to-End Tests (10% of tests)
- **Coverage:** Full system workflows
- **Speed:** Slow (5-30s each)
- **Scope:** Real dependencies (optional Ollama)
- **Examples:**
  - `test_full_development_cycle()`
  - `test_multi_agent_orchestration()`
  - `test_workflow_with_real_code()`

### Test Coverage Goals

| Component | Target Coverage | Priority |
|-----------|----------------|----------|
| **Core Framework** | 90%+ | P0 |
| **Agents** | 80%+ | P0 |
| **MAL** | 85%+ | P0 |
| **Scoring** | 90%+ | P0 |
| **Workflows** | 80%+ | P1 |
| **MCP Gateway** | 75%+ | P1 |
| **Industry Experts** | 75%+ | P2 |

### Test Tools

```python
# Core testing stack
pytest>=7.4.0              # Test framework
pytest-asyncio>=0.21.0     # Async support
pytest-cov>=4.1.0          # Coverage
pytest-mock>=3.12.0        # Mocking
pytest-timeout>=2.2.0      # Timeouts
httpx>=0.25.0              # HTTP testing (for MAL)
faker>=20.0.0              # Test data generation
```

---

## Risk Management

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Ollama unavailable** | High | Medium | Mock in tests, cloud fallback |
| **Performance issues** | Medium | Medium | Profiling, caching, optimization |
| **Test coverage gaps** | High | Low | Coverage gates in CI/CD |
| **Agent integration complexity** | Medium | Medium | Spike-first, extract patterns |

### Schedule Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Underestimated complexity** | High | Buffer time (20% per phase) |
| **Scope creep** | Medium | Strict prioritization |
| **Dependency delays** | Low | Alternative approaches |

---

## Success Metrics

### Phase Completion Criteria

**Each phase is complete when:**
- ✅ All tasks checked off
- ✅ Tests passing (80%+ coverage for new code)
- ✅ Documentation updated
- ✅ Code reviewed
- ✅ Integration tests pass

### Overall Project Success

**Project is production-ready when:**
- ✅ All 12 agents implemented
- ✅ 80%+ overall test coverage
- ✅ All features documented
- ✅ Performance acceptable (<5s operations)
- ✅ Security validated
- ✅ CI/CD pipeline working

---

## Timeline Summary

| Phase | Duration | Agents | Features | Test Coverage |
|-------|----------|--------|----------|---------------|
| **Phase 1** | 2 weeks | 1 (complete) | Config, Scoring | 80% (reviewer) |
| **Phase 2** | 4 weeks | +5 agents | Core agents | 80% (6 agents) |
| **Phase 3** | 4 weeks | 0 | Tiered Context, MCP, Workflows | 75% (features) |
| **Phase 4** | 4 weeks | +6 agents | Industry Experts | 80% (all agents) |
| **Phase 5** | 2 weeks | 0 | Polish, optimization | 80% (overall) |
| **Total** | **16 weeks** | **12 agents** | **All features** | **80%+ coverage** |

---

## Next Steps

1. **Immediate (This Week):**
   - Review and approve this plan
   - Set up project board (GitHub Projects)
   - Create Phase 1 tasks
   - Set up test infrastructure

2. **Short Term (Next 2 Weeks):**
   - Execute Phase 1
   - Daily standups
   - Weekly progress reviews

3. **Medium Term (Next 4 Weeks):**
   - Execute Phase 2
   - Extract patterns from agents
   - Refine agent API

---

## Appendix: Task Breakdown

### Phase 1 Tasks (Detailed)

```
Week 1:
- Day 1: Set up pytest + fixtures
- Day 2: Test infrastructure + CI/CD
- Day 3: Fix type hints + error handling
- Day 4: Input validation + config extraction
- Day 5: Reviewer agent tests

Week 2:
- Day 1: Config system design
- Day 2: Config implementation
- Day 3: Test coverage metric
- Day 4: Performance metric
- Day 5: Complete testing + refinement
```

### Agent Implementation Template

Each agent follows this pattern:

1. **Create agent structure**
   - Agent class extending BaseAgent
   - Agent-specific logic
   - Commands implementation
   - Tests

2. **Define commands**
   - Star-prefixed commands
   - Help text
   - Examples

3. **Implement capabilities**
   - Core functionality
   - Integration with MAL
   - Error handling

4. **Write tests**
   - Unit tests (80%+ coverage)
   - Integration tests
   - Edge cases

5. **Documentation**
   - Agent SKILL.md
   - Usage examples
   - Update main docs

---

**Document Status:** Ready for Review  
**Next Action:** Approve plan and begin Phase 1

