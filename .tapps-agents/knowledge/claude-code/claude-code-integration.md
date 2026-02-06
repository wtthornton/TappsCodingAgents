# Claude Code CLI Integration for TappsCodingAgents

## Overview

Claude Code CLI is a powerful AI coding assistant with features that TappsCodingAgents can leverage: subagents, agent teams, persistent memory, Agent SDK (headless execution), skills, hooks, and settings configuration.

## Key Features

### Custom Subagents (`.claude/agents/`)

Subagents are specialized AI assistants with their own context window:

```markdown
---
name: story-executor
description: Execute individual stories in isolated context
model: sonnet
memory: project
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---
# Story Executor

You execute individual stories from an Epic...
```

**Benefits over skills:**
- Own context window (isolated execution — no shared context pollution)
- Persistent memory (`memory: project` → `.claude/agent-memory/<name>/MEMORY.md`)
- Model selection per agent (haiku for research, sonnet for implementation, opus for architecture)
- Tool restrictions and permission modes
- Lifecycle hooks scoped to the subagent

### Agent Teams

Multiple Claude Code sessions coordinated as a team:
- **Team lead**: Coordinates work (= Epic orchestrator)
- **Teammates**: Work independently with own context windows (= story executors)
- **Shared task list**: With dependency tracking (= Epic stories)
- Enable with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`

### Agent SDK / Headless Mode

Programmatic execution for CI/CD:

```bash
claude -p "Execute story: Add auth endpoint" \
  --output-format json \
  --max-budget-usd 10.00 \
  --allowedTools "Bash,Read,Edit,Write"
```

### Settings Configuration (`.claude/settings.json`)

Project-level settings shared via git:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": ["Bash(tapps-agents *)", "Bash(pytest *)"],
    "deny": ["Read(./.env)", "Read(./secrets/**)"]
  },
  "env": {
    "TAPPS_AGENTS_MODE": "claude-code"
  },
  "enableAllProjectMcpServers": true
}
```

### Persistent Memory

- `memory: project` → auto-curated `MEMORY.md` per subagent
- First 200 lines injected on each invocation
- Survives across sessions — cross-run learning
- Location: `.claude/agent-memory/<name>/`

### Skills Enhancements

- `context: fork` — run skill in isolated subagent context
- Skill hooks (PreToolUse, PostToolUse, Stop events)
- `!command` — dynamic context injection
- `disable-model-invocation: true` — prevent auto-triggering

### Model Routing

Assign optimal models to subagents:
- **haiku**: Fast, low-cost — research, exploration
- **sonnet**: Balanced — implementation, code review
- **opus**: Complex reasoning — architecture decisions

## Configuration in TappsCodingAgents

```yaml
claude_code:
  auto_configure: true
  enable_subagents: true
  model_routing:
    research: haiku
    implementation: sonnet
    architecture: inherit
    review: sonnet
  agent_teams:
    enabled: false  # Opt-in (experimental)
    max_teammates: 3
```

## Detection

```python
import shutil

def is_claude_code_available() -> bool:
    return shutil.which("claude") is not None
```

## References

- [Claude Code Settings](https://code.claude.com/docs/en/settings)
- [Subagents](https://code.claude.com/docs/en/sub-agents)
- [Agent Teams](https://code.claude.com/docs/en/agent-teams)
- [Skills](https://code.claude.com/docs/en/skills)
- [Agent SDK](https://code.claude.com/docs/en/headless)
- Phase 7 in EPIC-AND-WORKFLOW-ENHANCEMENT-DESIGN-PLAN.md
