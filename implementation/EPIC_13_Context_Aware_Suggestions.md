# Epic 13: Context-Aware Suggestions

## Epic Goal

Provide intelligent, context-aware suggestions for workflows, agents, and actions based on project state, recent changes, and user behavior. This reduces cognitive load and helps users make better decisions about which workflows to use.

## Epic Description

### Existing System Context

- **Current relevant functionality**: Workflow selection is manual. Users must know which workflow to use. Cursor Rules document workflows but don't provide active suggestions. Project profiling exists but may not be used for suggestions
- **Technology stack**: Python 3.13+, project profiling system, git integration, workflow executor
- **Integration points**: 
  - `tapps_agents/core/project_profiler.py` - Project profiling
  - Git integration (recent changes, branch info)
  - Workflow recommendation system
  - Cursor chat interface

### Enhancement Details

- **What's being added/changed**: 
  - Create suggestion engine that analyzes project context
  - Implement context analysis (recent changes, branch name, file types)
  - Add workflow suggestion based on context
  - Create agent suggestion system (which agent to use)
  - Implement action suggestions (what to do next)
  - Add learning from user behavior (improve suggestions over time)
  - Create suggestion ranking (most relevant first)

- **How it integrates**: 
  - Suggestion engine analyzes project state
  - Suggestions provided in Cursor chat
  - Works with project profiling system
  - Integrates with git for change analysis
  - Uses workflow recommendation system

- **Success criteria**: 
  - Suggestions are relevant to current context
  - Workflow suggestions help users select appropriate workflows
  - Agent suggestions recommend useful agents
  - Suggestions improve over time
  - Users find suggestions helpful

## Stories

1. **Story 13.1: Context Analysis Foundation**
   - Create context analyzer that examines project state
   - Implement git change analysis (recent commits, modified files)
   - Add branch analysis (branch name, PR context)
   - Create project type detection (web app, API, library)
   - Acceptance criteria: Context analyzed, git changes detected, branch info extracted, project type identified

2. **Story 13.2: Workflow Suggestion Engine**
   - Implement workflow suggestion based on context
   - Create suggestion logic (match context to workflows)
   - Add suggestion ranking (relevance scoring)
   - Implement suggestion explanation (why this workflow)
   - Acceptance criteria: Suggestions generated, logic sound, ranking accurate, explanations clear

3. **Story 13.3: Agent Suggestion System**
   - Create agent suggestion based on task context
   - Implement agent matching (task type to agent)
   - Add agent recommendation logic
   - Create agent suggestion formatting
   - Acceptance criteria: Agents suggested, matching accurate, recommendations relevant, formatting clear

4. **Story 13.4: Action Suggestions**
   - Implement action suggestion system (what to do next)
   - Create action recommendation based on project state
   - Add action priority ranking
   - Implement action suggestion display
   - Acceptance criteria: Actions suggested, recommendations relevant, priority clear, display readable

5. **Story 13.5: Learning and Improvement**
   - Create user behavior tracking (which suggestions accepted)
   - Implement learning system (improve suggestions over time)
   - Add feedback mechanism (user can rate suggestions)
   - Create suggestion accuracy metrics
   - Acceptance criteria: Behavior tracked, learning works, feedback collected, metrics calculated

## Compatibility Requirements

- [ ] Suggestions are optional (can be disabled)
- [ ] No breaking changes to workflow execution
- [ ] Works with existing project profiling
- [ ] Suggestions don't interfere with manual selection
- [ ] Backward compatible with current system

## Risk Mitigation

- **Primary Risk**: Suggestions may be inaccurate
  - **Mitigation**: Learning system, user feedback, confidence scoring, fallback to manual selection
- **Primary Risk**: Context analysis may be slow
  - **Mitigation**: Caching, async analysis, incremental updates, performance optimization
- **Primary Risk**: Suggestions may be intrusive
  - **Mitigation**: Opt-in, configurable frequency, dismissible, non-blocking
- **Rollback Plan**: 
  - Disable suggestions via configuration
  - Remove suggestion system
  - Fall back to manual selection only

## Definition of Done

- [ ] All stories completed with acceptance criteria met
- [ ] Context analysis works correctly
- [ ] Workflow suggestions are relevant
- [ ] Agent suggestions help users
- [ ] Action suggestions provide value
- [ ] Learning system improves suggestions
- [ ] Comprehensive test coverage
- [ ] Documentation complete (suggestions, configuration, troubleshooting)
- [ ] No regression in workflow execution
- [ ] Suggestions enhance user experience

## Implementation Status

**Last Updated:** 2025-01-27

**Overall Status:** ✅ Completed

**Story Status:**
- Story 13.1 (Context Analysis): ✅ Completed
- Story 13.2 (Workflow Suggestions): ✅ Completed
- Story 13.3 (Agent Suggestions): ✅ Completed
- Story 13.4 (Action Suggestions): ✅ Completed
- Story 13.5 (Learning): ✅ Completed

## Implementation Summary

### Files Created:
- `tapps_agents/workflow/suggestion_engine.py` - Context-aware suggestion engine with workflow, agent, and action suggestions

### Files Modified:
- `tapps_agents/workflow/context_analyzer.py` - Enhanced with git commit analysis, PR context, and file type analysis

### Key Features Implemented:

1. **Context Analysis Foundation** (Story 13.1):
   - Enhanced context analyzer with git commit history
   - Branch analysis with PR context detection
   - Project type detection (JavaScript, Python, Rust, Go, Java)
   - File type distribution analysis
   - Recent changes tracking

2. **Workflow Suggestion Engine** (Story 13.2):
   - Context-aware workflow recommendations
   - Suggestion ranking with confidence scores
   - Explanation generation for why workflows are suggested
   - Alternative workflow suggestions
   - Integration with existing WorkflowRecommender

3. **Agent Suggestion System** (Story 13.3):
   - Agent suggestions based on task type (requirements, design, implementation, testing, etc.)
   - Agent-to-task mapping
   - Confidence scoring for agent suggestions
   - Explanation generation for agent recommendations

4. **Action Suggestions** (Story 13.4):
   - Action suggestions based on project context
   - Action patterns for different contexts (new_feature, bug_fix, refactoring, documentation)
   - Priority ranking for actions
   - Context-aware action recommendations

5. **Learning and Improvement** (Story 13.5):
   - User behavior tracking (which suggestions accepted/rejected)
   - Learning data persistence (`.tapps-agents/suggestion_learning.json`)
   - Confidence boost based on acceptance rates
   - Feedback recording mechanism

### Configuration:

Suggestions can be controlled via environment variable:
- `TAPPS_AGENTS_SUGGESTIONS_ENABLED=true` (default) - Enable context-aware suggestions
- `TAPPS_AGENTS_SUGGESTIONS_ENABLED=false` - Disable suggestions

### Usage:

```python
from tapps_agents.workflow.suggestion_engine import ContextAwareSuggestionEngine
from pathlib import Path

# Initialize suggestion engine
engine = ContextAwareSuggestionEngine(project_root=Path.cwd())

# Get suggestions
suggestions = engine.get_suggestions(
    user_query="I need to add a new feature",
    include_workflows=True,
    include_agents=True,
    include_actions=True,
)

# Access workflow suggestions
for workflow_suggestion in suggestions.workflows:
    print(f"{workflow_suggestion.value} (confidence: {workflow_suggestion.confidence:.0%})")
    print(f"  {workflow_suggestion.explanation}")

# Record feedback
engine.record_feedback(
    suggestion_type=SuggestionType.WORKFLOW,
    value="workflow-full-sdlc",
    accepted=True,
)
```

### Backward Compatibility:

- Suggestions are optional (can be disabled)
- No breaking changes to workflow execution
- Works with existing project profiling
- Suggestions don't interfere with manual selection
- Backward compatible with current system

