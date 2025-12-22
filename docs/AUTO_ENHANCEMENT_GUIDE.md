# Auto-Enhancement Guide

## Overview

Auto-enhancement automatically improves user prompts before they reach individual agents, ensuring high-quality code generation. The system uses a Cursor-first approach where:

- **Framework** provides structured enhancement data (tools-only)
- **Cursor's LLM** performs synthesis when in Cursor mode
- **MAL** provides fallback synthesis when in headless mode

## How It Works

When you run a command like:

```bash
tapps-agents implementer implement "Create login" src/api/auth.py
```

The auto-enhancement middleware:

1. **Detects** the prompt argument (`specification` in this case)
2. **Assesses** prompt quality using heuristics
3. **Enhances** the prompt if quality is below threshold
4. **Passes** the enhanced prompt to the target agent

## Configuration

Auto-enhancement is configured in `.tapps-agents/config.yaml`:

```yaml
auto_enhancement:
  enabled: true
  mode: cursor-skills  # cursor-skills, structured, or smart
  min_prompt_length: 20
  quality_threshold: 50.0
  commands:
    implementer:
      enabled: true
      synthesis_mode: full  # full or quick
    planner:
      enabled: true
      synthesis_mode: quick
    architect:
      enabled: false  # Usually gets detailed requirements already
    designer:
      enabled: false  # Usually gets detailed requirements already
```

### Configuration Options

- **enabled**: Enable/disable auto-enhancement globally (default: true)
- **mode**: Enhancement mode
  - `cursor-skills`: Use Cursor Skills for synthesis (default, Cursor-first)
  - `structured`: Return structured data only
  - `smart`: Quality-based enhancement
- **min_prompt_length**: Minimum prompt length to trigger enhancement (default: 20)
- **quality_threshold**: Quality score below which to enhance (0-100, default: 50.0)
- **commands**: Per-command settings
  - **enabled**: Enable/disable for specific command
  - **synthesis_mode**: `full` (7 stages) or `quick` (3 stages)

## Usage

### Automatic Enhancement

Auto-enhancement works automatically when enabled. No extra steps needed:

```bash
# Prompt will be automatically enhanced if quality is low
tapps-agents implementer implement "Add auth" src/api/auth.py

# High-quality prompts are not enhanced
tapps-agents implementer implement "Create a comprehensive user authentication system with JWT tokens, password hashing using bcrypt, session management, and password reset functionality" src/api/auth.py
```

### Manual Control

Use CLI flags to control enhancement:

```bash
# Disable enhancement for this command
tapps-agents implementer implement "Add auth" src/api/auth.py --no-enhance

# Force enhancement even if quality is high
tapps-agents planner plan "Detailed plan" --enhance

# Override enhancement mode
tapps-agents implementer implement "Add auth" src/api/auth.py --enhance-mode quick
```

## Cursor vs Headless Mode

### Cursor Mode (Default)

When running in Cursor IDE:

- Enhancement stages run (analysis, requirements, architecture, etc.)
- Synthesis happens via Cursor Skills using Cursor's LLM
- Framework provides structured data, Cursor provides intelligence
- Uses whatever model you've configured in Cursor

### Headless Mode

When running from CLI outside Cursor:

- Enhancement stages run (analysis, requirements, architecture, etc.)
- Synthesis happens via MAL (Model Abstraction Layer)
- Requires MAL configuration in `.tapps-agents/config.yaml`
- Falls back to structured data if MAL not configured

## Quality Assessment

Prompts are assessed using multiple factors:

- **Length**: Longer prompts often indicate more detail
- **Keywords**: Presence of quality indicators (requirements, architecture, etc.)
- **Structure**: Multiple sentences, paragraphs
- **Technical Terms**: Domain-specific terminology

Quality score ranges from 0-100. Prompts below the threshold (default: 50.0) are enhanced.

## Supported Commands

Auto-enhancement works with these commands:

- `implementer implement` - Code generation
- `implementer generate-code` - Code generation (no file write)
- `planner plan` - Project planning
- `planner create-story` - User story creation
- `architect design-system` - Architecture design
- `designer design-api` - API design
- `designer design-data-model` - Data model design
- `analyst gather-requirements` - Requirements gathering

Commands that skip enhancement:
- `debugger debug` - Error messages don't need enhancement
- `implementer refactor` - Refactoring instructions are usually specific

## Examples

### Example 1: Low-Quality Prompt (Enhanced)

**Input:**
```bash
tapps-agents implementer implement "login" src/api/auth.py
```

**Enhanced Prompt:**
```
# Enhanced Prompt: Create login system

## Metadata
- Intent: Feature (authentication)
- Domain: security, user-management
- Scope: Medium (3-5 files)
- Workflow: greenfield

## Requirements
### Functional Requirements
- User authentication with email/password
- Session management
- Password reset functionality
- Account verification

## Architecture Guidance
- Service layer pattern for authentication logic
- JWT token management
- Password hashing with bcrypt
- Session storage in Redis

## Quality Standards
- Security Score: Minimum 8.0/10
- Test Coverage: 80% minimum
- Overall Score Threshold: 70.0

## Implementation Strategy
1. Create User model with authentication fields
2. Implement AuthService with login/logout
3. Create API endpoints for authentication
4. Add password reset flow
5. Write unit and integration tests
```

### Example 2: High-Quality Prompt (Not Enhanced)

**Input:**
```bash
tapps-agents implementer implement "Create a comprehensive user authentication system with JWT tokens, password hashing using bcrypt, session management with Redis, password reset functionality, account verification via email, and rate limiting for login attempts" src/api/auth.py
```

**Result:** Prompt is not enhanced (quality score > 50.0)

## Troubleshooting

### Enhancement Not Working

1. **Check configuration:**
   ```bash
   cat .tapps-agents/config.yaml | grep -A 10 auto_enhancement
   ```

2. **Verify it's enabled:**
   ```yaml
   auto_enhancement:
     enabled: true
   ```

3. **Check command-specific settings:**
   ```yaml
   auto_enhancement:
     commands:
       implementer:
         enabled: true
   ```

### Enhancement Too Aggressive

If prompts are being enhanced when they shouldn't be:

1. **Increase quality threshold:**
   ```yaml
   auto_enhancement:
     quality_threshold: 70.0  # Only enhance very low-quality prompts
   ```

2. **Disable for specific commands:**
   ```yaml
   auto_enhancement:
     commands:
       architect:
         enabled: false
   ```

### Enhancement Not Aggressive Enough

If prompts should be enhanced but aren't:

1. **Decrease quality threshold:**
   ```yaml
   auto_enhancement:
     quality_threshold: 30.0  # Enhance more prompts
   ```

2. **Force enhancement:**
   ```bash
   tapps-agents implementer implement "prompt" file.py --enhance
   ```

### Cursor Mode Issues

If synthesis isn't working in Cursor mode:

1. **Check runtime mode:**
   ```python
   from tapps_agents.core.runtime_mode import is_cursor_mode
   print(f"Is Cursor mode: {is_cursor_mode()}")
   ```

2. **Verify Cursor Skills are available:**
   - Check that `.claude/skills/enhancer/SKILL.md` exists
   - Verify `@enhancer *synthesize-prompt` command is available

3. **Check enhancement result:**
   - Look for `skill_command` in enhancement output
   - Execute the skill command in Cursor chat if needed

### Headless Mode Issues

If synthesis isn't working in headless mode:

1. **Check MAL configuration:**
   ```yaml
   mal:
     enabled: true
     default_provider: ollama
     default_model: qwen2.5-coder:7b
   ```

2. **Verify Ollama is running:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. **Check for errors:**
   - Look for `MALDisabledInCursorModeError` (shouldn't happen in headless)
   - Check logs for synthesis failures

## Best Practices

1. **Start with defaults** - The default configuration works well for most cases
2. **Adjust per project** - Fine-tune quality thresholds based on your team's prompt quality
3. **Use quick mode for iteration** - Use `--enhance-mode quick` for faster feedback
4. **Use full mode for production** - Use full enhancement for important features
5. **Disable for specific commands** - If a command usually gets detailed input, disable enhancement

## Advanced Usage

### Custom Enhancement Config

Create `.tapps-agents/enhancement-config.yaml` for advanced control:

```yaml
enhancement:
  stages:
    analysis: true
    requirements: true
    architecture: true
    codebase_context: true
    quality: true
    implementation: true
    synthesis: true
  
  requirements:
    consult_experts: true
    min_expert_confidence: 0.7
    include_nfr: true
  
  codebase_context:
    tier: TIER2
    include_related: true
    max_related_files: 10
```

### Programmatic Usage

Use the middleware programmatically:

```python
from tapps_agents.cli.utils.prompt_enhancer import enhance_prompt_if_needed
from argparse import Namespace
from tapps_agents.core.config import load_config

args = Namespace(
    agent="implementer",
    command="implement",
    specification="Create login",
    file_path="src/api/auth.py"
)

config = load_config()
enhanced_args = enhance_prompt_if_needed(args, config.auto_enhancement)
print(enhanced_args.specification)  # Enhanced prompt
```

## See Also

- [Enhancer Agent Documentation](ENHANCER_AGENT.md)
- [Simple Mode Guide](SIMPLE_MODE_GUIDE.md)
- [Configuration Reference](../tapps_agents/core/config.py)

