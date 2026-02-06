# State Persistence and Session Handoff Patterns

## Overview

This knowledge covers patterns for persisting workflow/epic state across sessions and handing off context between agents. Critical for resume capability, progress tracking, and multi-agent execution.

## Epic State Persistence (Phase 1)

### State Schema

```json
{
  "epic_id": "epic-51",
  "run_id": "20260205-143022",
  "status": "in_progress",
  "started_at": "2026-02-05T14:30:22Z",
  "stories": {
    "story-1": {
      "status": "completed",
      "quality_score": 85,
      "started_at": "...",
      "completed_at": "..."
    },
    "story-2": {
      "status": "running",
      "started_at": "..."
    }
  },
  "checksum": "sha256:abc123..."
}
```

### Persistence Strategy

- **Location**: `.tapps-agents/epic-state/{epic_id}.json`
- **Concurrency**: run_id-based isolation (default)
- **Atomic writes**: Write to temp file, then rename
- **Checksum**: SHA256 of state content for integrity verification
- **Cross-platform file locking**: `fcntl` on Unix, `msvcrt` on Windows

### Resume Flow

1. Load state from disk
2. Validate checksum
3. Find last completed story
4. Resume from next pending story
5. Re-run failed stories (configurable)

## Session Handoff (Phase 4)

### Handoff Document Format

```markdown
# Session Handoff: Epic-51 Story-3

## Completed Work
- Story-1: Auth endpoints (quality: 85)
- Story-2: User model (quality: 78)

## Current Story
- Title: Add role-based access control
- Dependencies: [story-1, story-2]

## Context
- Files modified: src/auth.py, src/models/user.py
- Patterns established: JWT auth, Pydantic models
- Quality trends: improving (78 → 85)

## Next Steps
- Implement RBAC middleware
- Add permission decorators
- Update tests
```

### Context Filtering

Define what data the next agent/session needs:
- **Always include**: Current story spec, file list, quality scores
- **Selectively include**: Prior story summaries (last 3), architecture decisions
- **Never include**: Full implementation code, raw LLM responses, debug logs

## Epic Memory (Phase 4.1)

### JSONL Memory Format

```jsonl
{"event":"story_complete","story_id":"story-1","files_changed":["src/auth.py"],"quality_score":85,"patterns":["jwt_auth"],"timestamp":"2026-02-05T14:35:00Z"}
{"event":"story_complete","story_id":"story-2","files_changed":["src/models/user.py"],"quality_score":78,"patterns":["pydantic_models"],"timestamp":"2026-02-05T14:45:00Z"}
```

### Memory Injection

```python
def build_epic_context(state: EpicState, max_entries: int = 10) -> str:
    """Build context from epic memory for next story."""
    memory = load_jsonl(state.memory_path)
    recent = memory[-max_entries:]
    return format_as_context(recent)
```

## Best Practices

1. **JSON-serializable state**: All state must be JSON-serializable for persistence
2. **Checkpoints at phase boundaries**: Save state after each story completion
3. **Idempotent operations**: Resume should be safe to run multiple times
4. **Context filtering**: Pass only what the next agent needs, not entire history
5. **Atomic file operations**: Use temp file + rename pattern for crash safety
6. **Version state schema**: Include schema version for future migration

## Configuration

```yaml
epic:
  state_dir: .tapps-agents/epic-state
  memory_format: jsonl
  max_memory_entries: 50
  handoff_context_limit: 3000  # tokens
```

## Related

- Phase 1: Epic Progress Persistence
- Phase 4: Epic Memory and Session Handoff
- `tapps_agents/epic/orchestrator.py`
- `tapps_agents/workflow/session_handoff.py`
