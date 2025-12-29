# Universal Context7 Auto-Detection Hook

```yaml
story_id: context7-automatic-integration-universal-context7-auto-detect
title: Universal Context7 Auto-Detection Hook
description: |
  Universal Context7 Auto-Detection Hook
epic: Context7 Automatic Integration
domain: general
priority: high
complexity: {'instruction': {'agent_name': 'planner', 'command': 'estimate-complexity', 'prompt': 'Estimate the complexity of implementing this story on a scale of 1-5:\n- 1: Trivial (simple change, <1 hour)\n- 2: Easy (straightforward, 1-4 hours)\n- 3: Medium (moderate effort, 1-2 days)\n- 4: Complex (significant effort, 3-5 days)\n- 5: Very Complex (major feature, 1+ weeks)\n\nStory: Universal Context7 Auto-Detection Hook\n\nRespond with ONLY a single number (1-5).', 'parameters': {'description': 'Universal Context7 Auto-Detection Hook'}}, 'skill_command': '@planner estimate-complexity --description "Universal Context7 Auto-Detection Hook"', 'estimated_complexity': 3}
status: draft
created_at: 2025-12-29T12:20:15.728106
created_by: planner
```

## Description

Universal Context7 Auto-Detection Hook

## Acceptance Criteria

- [x] `BaseAgent` has `_auto_fetch_context7_docs()` method implemented
- [x] Method accepts `code`, `prompt`, `error_message`, and `language` parameters
- [x] Method returns `dict[str, dict[str, Any]]` with library documentation
- [x] Method automatically detects libraries from all provided sources
- [x] Method deduplicates detected libraries before fetching docs
- [x] Method returns empty dict when Context7 is disabled
- [x] Method returns empty dict when no libraries detected
- [x] All agents can access this method via inheritance from `BaseAgent`
- [x] Method uses `Context7AgentHelper` for library detection and doc fetching
- [x] Implementation follows async/await pattern for Context7 API calls

## Tasks

1. Implement story requirements

## Technical Notes

(Technical considerations, dependencies, etc.)

## Dependencies

- Related stories: []
- Blocks: []
- Blocked by: []
