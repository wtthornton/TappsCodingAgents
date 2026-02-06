# Intent Parsing and Workflow Auto-Selection

## Overview

TappsCodingAgents uses intent parsing to automatically select the right workflow (build, fix, review, test, full, etc.) based on the user's natural language prompt. This knowledge covers the NLP patterns, intent taxonomy, and routing logic.

## Intent Taxonomy

### Primary Intents (WorkflowIntent enum)

| Intent | Keywords | Default Workflow |
|--------|----------|-----------------|
| BUILD | build, create, make, generate, add, implement, develop, write, new, feature | *build (7-step) |
| FIX | fix, repair, resolve, debug, error, bug, issue, problem, broken, correct | *fix (3-step) |
| REVIEW | review, check, analyze, inspect, examine, score, quality, audit | *review (2-step) |
| TEST | test, verify, validate, coverage, testing | *test (1-step) |
| REFACTOR | refactor, modernize, update, improve code, legacy, deprecated | *refactor (5-step) |
| EXPLORE | explore, understand, navigate, find, discover, overview, codebase, trace | *explore |
| FULL | full, complete, sdlc, lifecycle, everything | *full (9-step) |
| EPIC | epic, implement epic, execute epic, run epic, story, stories | *epic |
| ENHANCE | enhance, improve prompt, expand prompt | *enhance |
| BREAKDOWN | breakdown, task list | *breakdown |

### Intent Detection Pipeline

1. **Explicit command check**: `*build`, `*fix`, etc. → highest priority
2. **Keyword scoring**: Count matching keywords per intent
3. **Confidence threshold**: Intent must score ≥ 0.6
4. **Ambiguity resolution**: If top two intents within 0.15, use default (`build`)

## Routing Logic

### Current Components

- `IntentParser` — keyword-based intent detection
- `WorkflowSuggester` — suggests workflow with benefits explanation
- `SimpleModeHandler` — routes intent to orchestrator
- `detect_primary_intent()` — top-level detection function
- `validate_workflow_match()` — post-planning mismatch detection

### Gaps (from design plan Phase 5)

1. **Explicit command parsing**: Extract `*command` before intent detection
2. **Unified taxonomy**: Single `WorkflowIntent` enum used by all components
3. **Validate wiring**: Ensure IntentParser → WorkflowSuggester → Handler chain is consistent
4. **Framework detection**: Auto-switch to `*full` when modifying `tapps_agents/` package

## Best Practices

1. **Explicit commands always win**: `*build "improve tests"` → BUILD, not TEST
2. **Context-aware**: Consider file paths, recent history, project type
3. **Progressive confidence**: Low confidence → ask user; high confidence → auto-route
4. **Feedback loop**: Track intent accuracy via adaptive learning system

## Configuration

```yaml
simple_mode:
  auto_detect: true
  natural_language: true
  default_orchestrator: "build"
  enable_checkpoints: true
  checkpoint_confidence_threshold: 0.7
```

## Related

- Phase 5: Workflow Auto-Selection (EPIC-AND-WORKFLOW-ENHANCEMENT-DESIGN-PLAN.md)
- `tapps_agents/simple_mode/intent_parser.py`
- `tapps_agents/simple_mode/workflow_suggester.py`
- `tapps_agents/simple_mode/handler.py`
