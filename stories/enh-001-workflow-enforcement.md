# Epic: ENH-001 Workflow Enforcement System

**Epic ID:** ENH-001
**Status:** Ready for Implementation
**Priority:** High
**Total Story Points:** 8
**Estimated Duration:** 2 weeks
**Target Sprint:** EPIC-52 Phase 1

---

## Epic Overview

### Goal

Implement a workflow enforcement system that intercepts direct code edits and proactively suggests @simple-mode workflows, ensuring LLMs act as "Senior Developers" by default.

### User Value

**As a developer using TappsCodingAgents**, I want direct code edits to be intercepted and workflows suggested, **so that** I use workflows by default (with automatic validation, testing, and quality gates) instead of bypassing them.

### Success Metrics

- Workflow usage rate: 95%+ (currently ~30%)
- Issue detection: 95%+ caught before user sees code
- Performance: <50ms interception latency
- Test coverage: ≥85%

---

## User Stories

### Story 1: Core Workflow Enforcer

**Story ID:** ENH-001-S1
**Priority:** High
**Story Points:** 3
**Status:** Todo

#### User Story

> As a developer, I want my direct code edits to be intercepted before execution, so that I can be reminded to use workflows for better quality.

#### Acceptance Criteria

1. ✅ All Write tool invocations are intercepted before execution
2. ✅ All Edit tool invocations are intercepted before execution
3. ✅ File creation operations are intercepted
4. ✅ Interception latency <50ms (p95)
5. ✅ User intent is captured from context (prompt, file path, operation type)
6. ✅ Enforcement decision is made (block, warn, allow)
7. ✅ Configuration loaded from `.tapps-agents/config.yaml`

#### Technical Details

**Files to Create:**
- `tapps_agents/workflow/enforcer.py` (250 lines)

**Key Components:**
```python
class WorkflowEnforcer:
    def intercept_code_edit(
        file_path: Path,
        user_intent: str,
        is_new_file: bool
    ) -> dict[str, Any]:
        # Returns: {"action": "block"|"warn"|"allow", "message": str}
```

**Integration Points:**
- Hook into Write tool
- Hook into Edit tool
- Hook into file creation

#### Tasks

- [ ] Task 1.1: Create WorkflowEnforcer class (4 hours)
  - Implement intercept_code_edit() method
  - Add enforcement mode logic (blocking, warning, silent)
  - Integrate with configuration system

- [ ] Task 1.2: Hook into file operations (4 hours)
  - Add Write tool intercept
  - Add Edit tool intercept
  - Add file creation intercept
  - Test interception flow

- [ ] Task 1.3: Write unit tests (4 hours)
  - Test enforcement modes
  - Test configuration loading
  - Test hook integration
  - Achieve ≥85% coverage

#### Dependencies

- None (foundational story)

#### Estimated Effort

12 hours (3 story points)

---

### Story 2: Intent Detection System

**Story ID:** ENH-001-S2
**Priority:** High
**Story Points:** 2
**Status:** Todo

#### User Story

> As a developer, I want the system to detect my intent (build, fix, refactor, review) from my prompt, so that it can suggest the most appropriate workflow.

#### Acceptance Criteria

1. ✅ Detects *build intent (keywords: build, create, add, implement, new, feature)
2. ✅ Detects *fix intent (keywords: fix, bug, error, issue, broken, repair)
3. ✅ Detects *refactor intent (keywords: refactor, modernize, improve, update)
4. ✅ Detects *review intent (keywords: review, check, analyze, inspect, quality)
5. ✅ Returns confidence score (0-100%)
6. ✅ Triggers suggestion when confidence ≥60%
7. ✅ Handles ambiguous cases (multiple high scores)

#### Technical Details

**Files to Create:**
- `tapps_agents/workflow/intent_detector.py` (150 lines)

**Key Components:**
```python
class IntentDetector:
    def detect_workflow(user_intent: str) -> tuple[WorkflowType, float]:
        # Returns: (workflow_type, confidence_score)
```

**Intent Detection Logic:**
- Keyword matching (80% weight)
- Context analysis (20% weight)
- Confidence scoring

#### Tasks

- [ ] Task 2.1: Create IntentDetector class (3 hours)
  - Implement keyword matching
  - Calculate confidence scores
  - Handle ambiguous cases

- [ ] Task 2.2: Add context analysis (2 hours)
  - Analyze file path
  - Analyze operation type
  - Combine with keyword matching

- [ ] Task 2.3: Write unit tests (3 hours)
  - Test all intent types
  - Test confidence scoring
  - Test ambiguous cases
  - Achieve ≥85% coverage

#### Dependencies

- ENH-001-S1 (Core Workflow Enforcer)

#### Estimated Effort

8 hours (2 story points)

---

### Story 3: User Messaging System

**Story ID:** ENH-001-S3
**Priority:** High
**Story Points:** 2
**Status:** Todo

#### User Story

> As a developer, I want clear, actionable messages when enforcement triggers, so that I understand why I should use a workflow and how to do it.

#### Acceptance Criteria

1. ✅ Displays detected intent and confidence score
2. ✅ Shows recommended workflow command (@simple-mode *build "description")
3. ✅ Lists workflow benefits (auto-validation, auto-testing, quality gates)
4. ✅ Includes override instructions (--skip-enforcement flag, config change)
5. ✅ Formats for CLI output
6. ✅ Formats for IDE output
7. ✅ Emoji support (configurable)

#### Technical Details

**Files to Create:**
- `tapps_agents/workflow/message_formatter.py` (100 lines)

**Key Components:**
```python
class MessageFormatter:
    def format_blocking_message(
        workflow: WorkflowType,
        user_intent: str,
        file_path: Path
    ) -> str:
        # Returns formatted message with benefits and examples
```

**Message Template:**
```
⚠️  Detected direct code edit for: {file_path}

Use @simple-mode {workflow} instead for automatic quality gates.

Recommended:
@simple-mode {workflow} "{description}"

This will automatically:
  ✅ Implement code
  ✅ Review (Ruff, mypy, security)
  ✅ Generate tests (≥80% coverage)
  ✅ Enforce quality gates

To proceed with direct edit:
- Add --skip-enforcement flag
- Or set enforcement_mode: "warning" in config
```

#### Tasks

- [ ] Task 3.1: Create MessageFormatter class (2 hours)
  - Implement message templates
  - Add benefit formatting
  - Add override instructions

- [ ] Task 3.2: Format for different outputs (2 hours)
  - CLI format
  - IDE format
  - Add emoji support

- [ ] Task 3.3: Write unit tests (2 hours)
  - Test message formatting
  - Test benefit lists
  - Test override instructions
  - Achieve ≥85% coverage

#### Dependencies

- ENH-001-S2 (Intent Detection System)

#### Estimated Effort

6 hours (2 story points)

---

### Story 4: Configuration System

**Story ID:** ENH-001-S4
**Priority:** High
**Story Points:** 1
**Status:** Todo

#### User Story

> As a developer, I want to configure enforcement behavior via `.tapps-agents/config.yaml`, so that I can customize enforcement for my project.

#### Acceptance Criteria

1. ✅ Loads configuration from `.tapps-agents/config.yaml`
2. ✅ Supports enforcement mode (blocking, warning, silent)
3. ✅ Supports confidence threshold (0-100%, default: 60%)
4. ✅ Validates configuration structure
5. ✅ Provides clear error messages for invalid config
6. ✅ Uses defaults when config missing
7. ✅ Supports per-project overrides

#### Technical Details

**Files to Create:**
- `tapps_agents/core/llm_behavior.py` (150 lines)

**Key Components:**
```python
@dataclass
class EnforcementConfig:
    mode: Literal["blocking", "warning", "silent"] = "blocking"
    confidence_threshold: float = 60.0
    suggest_workflows: bool = True
    block_direct_edits: bool = True

    @classmethod
    def from_config_file(cls, config_path: Path) -> "EnforcementConfig"
```

**Configuration Schema:**
```yaml
llm_behavior:
  mode: "senior-developer"

  workflow_enforcement:
    mode: "blocking"
    confidence_threshold: 60
    suggest_workflows: true
    block_direct_edits: true
```

#### Tasks

- [ ] Task 4.1: Create EnforcementConfig class (2 hours)
  - Define configuration schema
  - Implement config loading
  - Add validation

- [ ] Task 4.2: Write unit tests (2 hours)
  - Test config loading
  - Test validation
  - Test defaults
  - Achieve ≥85% coverage

#### Dependencies

- ENH-001-S1 (Core Workflow Enforcer)

#### Estimated Effort

4 hours (1 story point)

---

## Epic Summary

### Stories Overview

| ID | Story | Points | Priority | Status |
|----|-------|--------|----------|--------|
| ENH-001-S1 | Core Workflow Enforcer | 3 | High | Todo |
| ENH-001-S2 | Intent Detection System | 2 | High | Todo |
| ENH-001-S3 | User Messaging System | 2 | High | Todo |
| ENH-001-S4 | Configuration System | 1 | High | Todo |

**Total Story Points:** 8
**Estimated Duration:** 2 weeks

### Implementation Order

1. ✅ **Story 4** (Configuration System) - Foundation
2. ✅ **Story 1** (Core Workflow Enforcer) - Core logic
3. ✅ **Story 2** (Intent Detection System) - Intelligence
4. ✅ **Story 3** (User Messaging System) - User experience

**Note:** Stories 1, 2, and 3 can be developed in parallel after Story 4 is complete.

### Files Created

| File | Lines | Story | Purpose |
|------|-------|-------|---------|
| `tapps_agents/workflow/enforcer.py` | 250 | S1 | Core enforcement engine |
| `tapps_agents/workflow/intent_detector.py` | 150 | S2 | Intent classification |
| `tapps_agents/workflow/message_formatter.py` | 100 | S3 | Message formatting |
| `tapps_agents/core/llm_behavior.py` | 150 | S4 | Configuration management |

**Total Production Code:** 650 lines

### Integration Points

- **ImplementerAgent** (`tapps_agents/agents/implementer/agent.py`)
  - Add enforcement hook before implementation
  - Pass user intent and file path to enforcer

- **CLI** (`tapps_agents/cli.py`)
  - Add --skip-enforcement flag
  - Hook enforcement before command execution

- **Configuration** (`.tapps-agents/config.yaml`)
  - Add `llm_behavior.workflow_enforcement` section
  - Document configuration options

### Testing Strategy

#### Unit Tests (≥85% coverage)

**Test Files:**
- `tests/test_workflow_enforcer.py` (Story 1)
- `tests/test_intent_detector.py` (Story 2)
- `tests/test_message_formatter.py` (Story 3)
- `tests/test_llm_behavior.py` (Story 4)

**Total Test Lines:** ~500 lines

#### Integration Tests

**Test File:** `tests/integration/test_enforcer_integration.py`

**Test Scenarios:**
- ImplementerAgent integration
- File operation interception
- Configuration changes
- Override mechanisms

#### End-to-End Tests

**Test File:** `tests/e2e/test_workflow_enforcement_e2e.py`

**Test Scenarios:**
- Full workflow (intercept → suggest → execute)
- Override scenarios
- Configuration scenarios

### Performance Targets

- **Interception Latency:** <50ms (p95)
- **Memory Overhead:** <10MB
- **CPU Overhead:** <5% during file operations
- **Configuration Load:** <100ms

### Documentation

**Files to Create:**
- `docs/guides/workflow-enforcement.md` - User guide
- Update `docs/CONFIGURATION.md` - Configuration reference
- Update `CLAUDE.md` - Document enforcement behavior

---

## Sprint Planning

### Week 1: Core Implementation

**Day 1-2: Configuration System**
- Story 4: Configuration System
- Create EnforcementConfig class
- Write unit tests
- **Deliverable:** Configuration loading works

**Day 3-4: Core Enforcer**
- Story 1: Core Workflow Enforcer
- Create WorkflowEnforcer class
- Hook into file operations
- Write unit tests
- **Deliverable:** Enforcement hooks work

**Day 5: Intent Detection**
- Story 2: Intent Detection System (Part 1)
- Create IntentDetector class
- Keyword matching logic
- **Deliverable:** Basic intent detection works

### Week 2: Polish and Testing

**Day 6: Intent Detection (cont)**
- Story 2: Intent Detection System (Part 2)
- Context analysis
- Confidence scoring
- Write unit tests
- **Deliverable:** Intent detection complete

**Day 7: User Messaging**
- Story 3: User Messaging System
- Create MessageFormatter class
- Format messages for CLI/IDE
- Write unit tests
- **Deliverable:** Clear messages shown

**Day 8-9: Integration Testing**
- Integration tests
- E2E tests
- Performance testing
- **Deliverable:** All tests passing

**Day 10: Documentation and Polish**
- Write user guide
- Update configuration docs
- Update CLAUDE.md
- **Deliverable:** Epic complete

---

## Risk Management

### Risk #1: Performance Impact

**Probability:** Medium
**Impact:** Medium

**Mitigation:**
- Optimize intent detection (keyword matching)
- Cache configuration
- Performance benchmarks (<50ms target)

**Contingency:**
- If latency >100ms, add fast-path bypass

### Risk #2: User Resistance

**Probability:** Medium
**Impact:** High

**Mitigation:**
- Default to blocking but make configurable
- Clear override instructions
- Show benefits prominently

**Contingency:**
- If >30% disable blocking, switch default to warning

### Risk #3: False Positives

**Probability:** Medium
**Impact:** Low

**Mitigation:**
- Confidence threshold (≥60%)
- Clear intent detection rules
- Easy override

**Contingency:**
- Increase threshold to 70% if false positive rate >20%

---

## Dependencies

### External Dependencies

- **Python 3.12+**: Modern type hints
- **PyYAML**: Configuration loading
- **pytest**: Testing framework

### Internal Dependencies

- None (self-contained)

### Blockers

- None

---

## Acceptance Criteria (Epic-Level)

### Functional Criteria

1. ✅ All file operations are intercepted
2. ✅ Intent detected with ≥60% confidence
3. ✅ Enforcement modes work (blocking, warning, silent)
4. ✅ Clear messages with benefits and examples
5. ✅ Configuration loaded from `.tapps-agents/config.yaml`

### Non-Functional Criteria

1. ✅ Performance: <50ms latency overhead
2. ✅ Reliability: 99.9% uptime, no false negatives
3. ✅ Security: No bypass vulnerabilities
4. ✅ Usability: Clear messaging, easy override
5. ✅ Maintainability: ≥85% test coverage

### Definition of Done

- [ ] All 4 stories completed
- [ ] All unit tests passing (≥85% coverage)
- [ ] All integration tests passing
- [ ] All E2E tests passing
- [ ] Performance benchmarks meet thresholds
- [ ] Documentation complete
- [ ] Deployed and validated in dev environment

---

## Next Steps

### Immediate Actions

1. ✅ **Review epic plan** with team
2. ✅ **Start Week 1**: Implement Story 4 (Configuration System)
3. ✅ **Use @simple-mode *build** for each story (dogfooding)

### Week 1 Kickoff

```bash
# Story 4: Configuration System
@simple-mode *build "ENH-001-S4: Configuration System - Load enforcement config from .tapps-agents/config.yaml with validation"

# Story 1: Core Workflow Enforcer
@simple-mode *build "ENH-001-S1: Core Workflow Enforcer - Intercept file operations and enforce workflow usage"

# Story 2: Intent Detection System
@simple-mode *build "ENH-001-S2: Intent Detection System - Detect user intent (build/fix/refactor/review) with confidence scoring"

# Story 3: User Messaging System
@simple-mode *build "ENH-001-S3: User Messaging System - Format clear messages with benefits and override instructions"
```

---

**Created By:** TappsCodingAgents Planner Agent
**Date:** 2026-01-29
**Epic ID:** ENH-001
**Status:** Ready for Implementation
**Next Step:** Start Week 1 - Implement Story 4 (Configuration System)
