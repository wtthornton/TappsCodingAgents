# TappsCodingAgents - Part 3: Communication Architecture

**Version:** 2.0  
**Date:** December 14, 2025  
**Status:** Recommended Architecture

---

## Table of Contents

1. [Communication Overview](#communication-overview)
2. [Git Worktree Communication](#git-worktree-communication)
3. [Message Passing System](#message-passing-system)
4. [Knowledge Sharing](#knowledge-sharing)
5. [Complete Communication Flow](#complete-communication-flow)

---

## Communication Overview

### Communication Methods

| Method | Purpose | Speed | Persistence | Use Case |
|--------|---------|-------|-------------|----------|
| **Git Worktree** | Result sharing | Medium | ✅ Yes | Code changes, reports |
| **File Messages** | Coordination | Fast | ✅ Yes | Task assignments, status |
| **Context7 RAG** | Knowledge | Very Fast | ✅ Cached | Library docs |
| **Expert RAG** | Domain knowledge | Fast | ✅ Cached | Business expertise |
| **PR Comments** | Human review | Slow | ✅ Yes | Code review |

---

## Git Worktree Communication

### How It Works

Agents work in isolated git worktrees, committing results to separate branches. The orchestrator merges results.

```
Main Branch (main)
    ├─→ worktree/quality-001    → commits quality_results.json
    ├─→ worktree/testing-002    → commits test_results.json
    ├─→ worktree/code-003       → commits feature.py
    └─→ worktree/docs-004       → commits README.md

Orchestrator:
    - Monitors worktree commits
    - Reads result JSON files
    - Merges changes
    - Resolves conflicts
    - Creates final PR
```

### File Structure

```
.tapps-agents/
├── state/                           # Shared state files
│   ├── quality_results.json         # Quality → Review
│   ├── test_results.json            # Testing → Review
│   ├── code_scores.json             # Review → Orchestrator
│   ├── architecture.json            # Design → Code
│   ├── feature_plan.json            # Planning → Design
│   └── workflow_state.json          # Orchestrator state
├── messages/                        # Agent messaging
│   ├── inbox/                       # Orchestrator → Agents
│   │   ├── quality-001.json
│   │   ├── testing-002.json
│   │   └── code-003.json
│   └── outbox/                      # Agents → Orchestrator
│       ├── quality-001.json
│       ├── testing-002.json
│       └── code-003.json
└── reports/                         # Final reports
    ├── quality/latest.html
    ├── coverage/latest.html
    └── review/pr-comments.md
```

### Advantages
- ✅ Version controlled (full audit trail)
- ✅ No network infrastructure needed
- ✅ Works offline
- ✅ Cursor's native support
- ✅ Easy rollback and debugging

### Disadvantages
- ⚠️ File I/O latency (slower than message queues)
- ⚠️ Potential merge conflicts (mitigated by worktrees)
- ⚠️ Requires frequent git operations

---

## Message Passing System

### Inbox/Outbox Pattern

**Orchestrator → Agent (Task Assignment):**
```json
{
  "message_type": "task_assignment",
  "task_id": "generate-tests-001",
  "assigned_to": "testing-002",
  "priority": "high",
  "dependencies": ["quality-001"],
  "inputs": {
    "files": ["src/api/users.py"],
    "test_framework": "pytest",
    "coverage_target": 80
  },
  "timeout_seconds": 1800,
  "retry_policy": {
    "max_retries": 2,
    "backoff_seconds": 60
  }
}
```

**Agent → Orchestrator (Status Update):**
```json
{
  "message_type": "status_update",
  "task_id": "generate-tests-001",
  "agent_id": "testing-002",
  "status": "in_progress",
  "progress_percent": 45,
  "estimated_completion": "2025-12-14T10:35:00Z",
  "current_step": "Generating integration tests",
  "metadata": {
    "tests_generated": 12,
    "coverage_current": 67.3
  }
}
```

**Agent → Orchestrator (Completion):**
```json
{
  "message_type": "task_complete",
  "task_id": "generate-tests-001",
  "agent_id": "testing-002",
  "status": "completed",
  "timestamp": "2025-12-14T10:35:00Z",
  "results": {
    "output_file": ".tapps-agents/state/test_results.json",
    "tests_generated": 15,
    "coverage": 87.3,
    "tests_passed": 13,
    "tests_failed": 2
  },
  "next_agents": ["review-001"],
  "metadata": {
    "duration_seconds": 845,
    "files_analyzed": 23
  }
}
```

### Message Flow

```
1. Orchestrator writes task to inbox:
   .tapps-agents/messages/inbox/testing-002.json

2. Testing Agent reads inbox file

3. Testing Agent processes task

4. Testing Agent writes status updates to outbox:
   .tapps-agents/messages/outbox/testing-002.json

5. Orchestrator polls outbox files

6. Orchestrator reads completion message

7. Orchestrator routes to next agent
```

### Advantages
- ✅ Simple file-based system
- ✅ No external dependencies
- ✅ Easy to debug (just read JSON files)
- ✅ Version controlled

### Disadvantages
- ⚠️ Polling overhead
- ⚠️ Not real-time (file system latency)

---

## Knowledge Sharing

### Context7 RAG (Technical Knowledge)

**Purpose:** Shared library documentation and code patterns

**Structure:**
```
.tapps-agents/context7/
├── cache/
│   ├── fastapi/
│   │   ├── index.faiss          # Vector index
│   │   ├── metadata.json        # Chunk metadata
│   │   └── chunks/              # Cached chunks
│   ├── pytest/
│   ├── pydantic/
│   └── sqlalchemy/
└── stats/
    ├── hit_rate.json
    └── usage.json
```

**Query Example:**
```python
from tapps_agents.context7 import Context7Manager

context7 = Context7Manager()

# Query for patterns
results = context7.query(
    query="How to create async endpoints in FastAPI?",
    library="fastapi",
    top_k=3
)

# Returns:
[
    {
        "content": "@app.post('/users/') async def create_user...",
        "source": "fastapi/async-sql-databases",
        "similarity": 0.92
    },
    ...
]
```

**Advantages:**
- ✅ Fast retrieval (cached embeddings)
- ✅ 90%+ token savings
- ✅ Consistent knowledge across agents
- ✅ No duplication

**Disadvantages:**
- ⚠️ Read-only (agents can't share learnings)
- ⚠️ Requires pre-population
- ⚠️ Cache miss = slower retrieval

---

### Expert RAG (Business Knowledge)

**Purpose:** Domain-specific business expertise

**Structure:**
```
.tapps-agents/experts/
├── industry/
│   ├── healthcare/
│   │   ├── expert.yaml
│   │   ├── knowledge/
│   │   │   ├── compliance/hipaa.md
│   │   │   ├── standards/hl7_fhir.md
│   │   │   └── examples/
│   │   └── rag/
│   │       ├── index.faiss
│   │       └── metadata.json
│   ├── fintech/
│   └── ecommerce/
└── builtin/
    ├── security/
    ├── performance/
    └── ... (14 more)
```

**Consultation Flow:**
```python
# Design Agent consults experts
experts = ExpertRegistry()

# Get relevant experts
healthcare = experts.get("healthcare")  # Primary (51%)
fintech = experts.get("fintech")        # Secondary (24.5%)
security = experts.get("security")      # Builtin (12.25%)

# Query each
healthcare_rec = await healthcare.consult(requirements)
fintech_rec = await fintech.consult(requirements)
security_rec = await security.consult(requirements)

# Weighted decision
final = weighted_combine([
    (healthcare_rec, 0.51),
    (fintech_rec, 0.245),
    (security_rec, 0.1225)
])
```

**Advantages:**
- ✅ Domain expertise accessible
- ✅ Weighted decision-making
- ✅ RAG enables semantic search
- ✅ Fine-tuning possible

**Disadvantages:**
- ⚠️ Requires knowledge base population
- ⚠️ Query latency (embedding generation)
- ⚠️ Expert conflicts need resolution

---

## Complete Communication Flow

### Example: Feature Implementation

**Scenario:** Implement user authentication feature

```
═══════════════════════════════════════════════════════════════════
STEP 1: USER REQUEST
═══════════════════════════════════════════════════════════════════
User: "Add user authentication with email/password"
    ↓
Orchestrator receives request

═══════════════════════════════════════════════════════════════════
STEP 2: PLANNING PHASE
═══════════════════════════════════════════════════════════════════
Orchestrator → Planning Agent
    Writes: .tapps-agents/messages/inbox/planning-001.json
    
Planning Agent (Foreground):
    ├─ Reads: inbox/planning-001.json
    ├─ Generates user stories and tasks
    ├─ Writes: .tapps-agents/state/feature_plan.json
    └─ Writes: outbox/planning-001.json (status: completed)

Orchestrator reads completion:
    ├─ Reads: outbox/planning-001.json
    └─ Reads: state/feature_plan.json

═══════════════════════════════════════════════════════════════════
STEP 3: DESIGN PHASE
═══════════════════════════════════════════════════════════════════
Orchestrator → Design Agent
    Writes: .tapps-agents/messages/inbox/design-001.json
    
Design Agent (Foreground):
    ├─ Reads: inbox/design-001.json
    ├─ Reads: state/feature_plan.json
    ├─ Queries Context7: "FastAPI auth patterns"
    │   └─ Returns: Async endpoint examples
    ├─ Consults Expert: Security (password hashing)
    │   └─ Returns: "Use bcrypt with 12 rounds"
    ├─ Consults Expert: Healthcare (HIPAA compliance)
    │   └─ Returns: "Encrypt credentials, audit all access"
    ├─ Creates architecture design
    ├─ Writes: .tapps-agents/state/architecture.json
    └─ Writes: outbox/design-001.json (status: completed)

═══════════════════════════════════════════════════════════════════
STEP 4: PARALLEL EXECUTION
═══════════════════════════════════════════════════════════════════
Orchestrator assigns parallel tasks:
    ├─ Code Agent: inbox/code-003.json
    ├─ Testing Agent: inbox/testing-002.json
    ├─ Docs Agent: inbox/docs-004.json
    └─ Context Agent: inbox/context-005.json

───────────────────────────────────────────────────────────────────
CODE AGENT (Foreground, worktree/code-003)
───────────────────────────────────────────────────────────────────
├─ Reads: architecture.json, feature_plan.json
├─ Queries Context7: "FastAPI async database"
├─ Implements:
│   ├─ src/api/auth.py (login, register endpoints)
│   ├─ src/models/user.py (User model)
│   └─ src/utils/security.py (password hashing)
├─ Commits to: worktree/code-003
└─ Writes: outbox/code-003.json (status: completed)

───────────────────────────────────────────────────────────────────
TESTING AGENT (Background Cloud, worktree/testing-002)
───────────────────────────────────────────────────────────────────
├─ Reads: architecture.json
├─ Generates tests:
│   ├─ tests/api/test_auth.py (15 tests)
│   ├─ tests/models/test_user.py (8 tests)
│   └─ tests/utils/test_security.py (5 tests)
├─ Runs: pytest (tests fail - no implementation yet)
├─ Commits to: worktree/testing-002
└─ Writes: outbox/testing-002.json (status: tests_pending)

───────────────────────────────────────────────────────────────────
DOCS AGENT (Background Cloud, worktree/docs-004)
───────────────────────────────────────────────────────────────────
├─ Reads: architecture.json
├─ Generates:
│   ├─ docs/api/authentication.md
│   ├─ docs/guides/user-management.md
│   └─ Updates: README.md (auth section)
├─ Commits to: worktree/docs-004
└─ Writes: outbox/docs-004.json (status: completed)

───────────────────────────────────────────────────────────────────
CONTEXT AGENT (Background Cloud)
───────────────────────────────────────────────────────────────────
├─ Pre-warms Context7:
│   ├─ FastAPI authentication docs
│   ├─ pytest async testing patterns
│   └─ SQLAlchemy user model examples
└─ Writes: outbox/context-005.json (status: completed)

═══════════════════════════════════════════════════════════════════
STEP 5: QUALITY ANALYSIS (Sequential after Code)
═══════════════════════════════════════════════════════════════════
Orchestrator → Quality Agent
    Writes: inbox/quality-001.json
    
Quality Agent (Background Cloud, worktree/quality-001):
    ├─ Reads: worktree/code-003 changes
    ├─ Runs: Ruff, mypy, Bandit
    ├─ Analyzes: Complexity, security, maintainability
    ├─ Writes: .tapps-agents/state/quality_results.json
    │   Score: 8.5/10
    │   Issues: 2 medium security (hardcoded salt)
    └─ Writes: outbox/quality-001.json (status: completed)

═══════════════════════════════════════════════════════════════════
STEP 6: TEST EXECUTION (After Code + Tests)
═══════════════════════════════════════════════════════════════════
Orchestrator → Testing Agent (re-run)
    Writes: inbox/testing-002.json
    
Testing Agent (Background Cloud):
    ├─ Merges: worktree/code-003 changes
    ├─ Runs: pytest tests/
    │   Results: 28 tests, 27 passed, 1 failed
    │   Coverage: 87.3%
    ├─ Writes: .tapps-agents/state/test_results.json
    └─ Writes: outbox/testing-002.json (status: completed)

═══════════════════════════════════════════════════════════════════
STEP 7: CODE REVIEW
═══════════════════════════════════════════════════════════════════
Orchestrator → Review Agent
    Writes: inbox/review-001.json
    
Review Agent (Foreground):
    ├─ Reads: quality_results.json (8.5/10)
    ├─ Reads: test_results.json (87.3% coverage, 1 fail)
    ├─ Reviews: Code changes (git diff)
    ├─ Calculates: Aggregate score = 8.2/10
    ├─ Decision: APPROVED_WITH_SUGGESTIONS
    ├─ Creates PR comments:
    │   1. Fix failing test (edge case)
    │   2. Remove hardcoded salt (use env var)
    │   3. Add rate limiting to login endpoint
    ├─ Writes: .tapps-agents/state/review_results.json
    └─ Writes: outbox/review-001.json (status: completed)

═══════════════════════════════════════════════════════════════════
STEP 8: FINAL AGGREGATION
═══════════════════════════════════════════════════════════════════
Orchestrator:
    ├─ Merges all worktrees:
    │   ├─ code-003 → main (feature code)
    │   ├─ testing-002 → main (tests)
    │   └─ docs-004 → main (documentation)
    ├─ Creates GitHub PR:
    │   Title: "Add user authentication with email/password"
    │   Body: Generated from template
    │   Labels: ["feature", "high-priority"]
    ├─ Adds comments:
    │   ├─ Quality report (8.5/10)
    │   ├─ Test report (87.3% coverage)
    │   └─ Review suggestions (3 items)
    └─ Notifies: User for final review

═══════════════════════════════════════════════════════════════════
STEP 9: HUMAN REVIEW
═══════════════════════════════════════════════════════════════════
Developer:
    ├─ Reviews PR with all agent comments
    ├─ Addresses failing test (quick fix)
    ├─ Fixes hardcoded salt (use os.getenv)
    ├─ Adds rate limiting (10 attempts/hour)
    └─ Merges PR to main

═══════════════════════════════════════════════════════════════════
METRICS
═══════════════════════════════════════════════════════════════════
Total Time: ~45 minutes
    - Sequential would be: ~90 minutes
    - Time saved: 50%

Agents Used: 8 (6 in parallel)
    - Planning: 10 min
    - Design: 15 min
    - Parallel (max): 30 min
        - Code: 30 min
        - Testing: 25 min
        - Docs: 20 min
        - Context: 5 min
    - Quality: 8 min (sequential)
    - Testing (re-run): 12 min (sequential)
    - Review: 10 min

Human Involvement: 3 interactions
    1. Initial request (1 min)
    2. Review PR (10 min)
    3. Merge decision (1 min)
    Total human time: 12 minutes
```

---

## Communication Patterns Summary

### Pattern Selection Guide

| Scenario | Recommended Method | Rationale |
|----------|-------------------|-----------|
| **Share analysis results** | Git Worktree + JSON | Version controlled, persistent |
| **Share expert knowledge** | Context7/Expert RAG | Cached, token efficient |
| **Task coordination** | File messages (inbox/outbox) | Simple, no infrastructure |
| **Tool execution** | MCP Gateway | Standardized, reusable |
| **Human validation** | PR comments | Audit trail, GitHub native |
| **Real-time updates** | File polling | Simple, no dependencies |

### Best Practices

1. **Use Git Worktrees for:**
   - Code changes
   - Generated files
   - Analysis results

2. **Use File Messages for:**
   - Task assignments
   - Status updates
   - Coordination

3. **Use Context7/Expert RAG for:**
   - Library documentation
   - Domain knowledge
   - Code patterns

4. **Use PR Comments for:**
   - Code review feedback
   - Quality reports
   - Human decisions

---

**Next Document:** Part 4 - Expert System Design
