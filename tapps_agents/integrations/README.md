# TappsCodingAgents Integrations

This module provides integration layers for AI assistants and other tools to use TappsCodingAgents capabilities programmatically.

## ClawdbotIntegration

Integration for AI assistants (like Clawdbot/Claude) to use TappsCodingAgents tools directly.

### Features

- **Code Scoring**: Get objective quality metrics for any file
- **Domain Detection**: Automatically detect relevant domains from prompts or code
- **Expert Consultation**: Query domain experts for guidance
- **Outcome Tracking**: Record task outcomes for learning and improvement

### Usage

```python
from tapps_agents.integrations import ClawdbotIntegration
import asyncio

async def main():
    bot = ClawdbotIntegration(project_root="/path/to/project")
    
    # Score a file
    result = await bot.score_file("src/main.py")
    print(f"Score: {result.overall_score}/100")
    print(f"Passed: {result.passed}")
    print(f"Issues: {result.issues}")
    
    # Detect domains from a prompt
    domains = await bot.detect_domains("Implement OAuth2 refresh token flow")
    print(f"Detected: {domains.domains}")  # ['oauth2', 'authentication', ...]
    
    # Track task outcomes for learning
    await bot.track_outcome(
        task_id="task-123",
        task_type="implement",
        success=True,
        iterations=1,
        notes="First-pass success"
    )
    
    # Get success statistics
    stats = bot.get_stats()
    print(f"First-pass success rate: {stats['first_pass_rate']:.1%}")

asyncio.run(main())
```

### ScoreResult Fields

| Field | Type | Description |
|-------|------|-------------|
| `overall_score` | float | Combined score (0-100) |
| `complexity` | float | Cyclomatic complexity score |
| `security` | float | Security vulnerability score |
| `maintainability` | float | Code maintainability score |
| `linting` | float | Linting/style score |
| `type_checking` | float | Type annotation score |
| `passed` | bool | Whether score meets threshold |
| `threshold` | float | Minimum passing score |
| `issues` | list | List of detected issues |

## MemoryBridge

Bridge between AI assistant workspace files and the TappsCodingAgents knowledge base.

### Features

- Syncs MEMORY.md, USER.md, SOUL.md, etc. to knowledge base
- Creates "user-preferences" domain for personalized guidance
- Extracts patterns from workspace files automatically
- Enables expert consultation about user preferences

### Usage

```python
from tapps_agents.integrations import MemoryBridge
import asyncio

async def main():
    bridge = MemoryBridge(
        workspace_root="/path/to/workspace",  # Where MEMORY.md lives
        project_root="/path/to/project"       # Where .tapps-agents/ is
    )
    
    # Sync all workspace files to knowledge base
    result = await bridge.sync_all()
    print(f"Files processed: {result.files_processed}")
    print(f"Patterns extracted: {result.patterns_extracted}")
    
    # Get structured user context
    context = bridge.get_user_context()
    print(f"User: {context['user']}")
    print(f"Identity: {context['identity']}")
    
    # Query preferences
    results = await bridge.query_preferences("How should I handle errors?")
    for r in results:
        print(f"Source: {r['source']}")
        print(f"Content: {r['content'][:200]}...")

asyncio.run(main())
```

### Supported Workspace Files

| File | Category | Description |
|------|----------|-------------|
| `MEMORY.md` | preferences | Long-term memories and lessons |
| `USER.md` | identity | User information and context |
| `SOUL.md` | identity | Persona and behavior guidelines |
| `AGENTS.md` | context | Workspace conventions |
| `TOOLS.md` | context | Tool configurations |
| `IDENTITY.md` | identity | Assistant identity info |
| `memory/*.md` | daily | Daily notes and context |

## Requirements

- Python 3.12+
- TappsCodingAgents installed

## Notes

- Scoring works without LLM calls (uses static analysis)
- Context7 integration is optional (provides library documentation)
- Outcome tracking persists to `.tapps-agents/outcomes/` as JSONL files
- Knowledge base stored in `.tapps-agents/knowledge/`
