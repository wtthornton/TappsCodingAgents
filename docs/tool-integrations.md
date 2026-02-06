---
title: Multi-Tool Integration Guide
version: 1.0.0
status: active
last_updated: 2026-01-28
tags: [integration, cursor, claude-code, vscode, codespaces, tools]
---

# Multi-Tool Integration Guide

**Version**: 1.0.0
**Last Updated**: 2026-01-28
**Status**: Active

---

## Overview

TappsCodingAgents is designed to work with multiple AI coding tools and development environments. This guide explains how to use TappsCodingAgents with different tools, their capabilities, limitations, and setup instructions.

**Supported Tools**:
- ✅ **Cursor IDE** (Primary, fully supported)
- ✅ **Claude Code CLI** (Supported)
- ⚠️ **VS Code + Continue** (Partial support)
- ⚠️ **GitHub Codespaces** (Supported with limitations)
- ⚠️ **Claude.ai Web** (Limited support)

---

## Quick Comparison

| Feature | Cursor | Claude Code CLI | VS Code + Continue | Codespaces | Claude.ai Web |
|---------|--------|-----------------|-------------------|------------|---------------|
| Cursor Skills | ✅ Full | ✅ Full (via .claude/skills/) | ❌ No | ✅ Full | ❌ No |
| CLI Commands | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| Expert System | ✅ Full | ✅ Full | ⚠️ Partial | ✅ Full | ⚠️ Limited |
| Workflows | ✅ Full | ✅ Full (automatic orchestration) | ⚠️ Manual | ✅ Full | ❌ No |
| Subagents | ✅ Background Agents | ✅ Native (.claude/agents/) | ❌ No | ✅ Yes | ❌ No |
| Epic Orchestration | ✅ Full | ✅ Full (parallel waves) | ⚠️ CLI only | ✅ Full | ❌ No |
| Knowledge Base | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ❌ No |
| File Access | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ⚠️ Limited |
| Performance | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |

**Recommendation**: Use **Cursor IDE** for the best experience. Use **Claude Code CLI** for terminal-focused workflows.

---

## Cursor IDE Integration (Primary)

### Overview

Cursor is the **primary and recommended** tool for TappsCodingAgents. All features are fully supported with native integration.

**Why Cursor**:
- ✅ Native Cursor Skills support (workflow execution)
- ✅ Model-agnostic (uses your configured LLM)
- ✅ Full expert system integration
- ✅ IDE-integrated experience (no context switching)
- ✅ Best performance and UX

### Setup

**1. Install Cursor**:
```bash
# Download from cursor.sh
# Or install via package manager
```

**2. Install TappsCodingAgents**:
```bash
pip install tapps-agents
```

**3. Install Cursor Skills**:
```bash
cd your-project
tapps-agents setup-skills
```

This creates `.claude/skills/` with all agent skills.

**4. Configure Project**:
```bash
tapps-agents init
```

This creates `.tapps-agents/config.yaml` with project configuration.

### Usage

#### Via Cursor Chat (@-commands)

```cursor
# Invoke agents via @ commands
@simple-mode *build "Add user authentication"
@reviewer *review src/auth.py
@tester *test src/auth.py
@debugger *debug "AuthError: Invalid token"
```

#### Via CLI (Terminal in Cursor)

```bash
# Same commands via CLI
tapps-agents simple-mode build --prompt "Add user authentication"
tapps-agents reviewer review src/auth.py
tapps-agents tester test src/auth.py
```

### Features

**Expert System**:
- ✅ Automatic expert consultation
- ✅ Passive notifications
- ✅ Knowledge base RAG
- ✅ Expert history tracking

**Workflows**:
- ✅ Full SDLC workflow (`@simple-mode *full`)
- ✅ Rapid development workflow (`@simple-mode *build`)
- ✅ Quality workflow (`@simple-mode *review`)
- ✅ Custom workflows

**Code Quality**:
- ✅ Automatic code review
- ✅ Quality gates (≥70 score required)
- ✅ Security scanning (Bandit)
- ✅ Test coverage enforcement (≥75%)

### Limitations

- ⚠️ Requires Cursor Pro for full AI features
- ⚠️ Skills configuration needed per project
- ⚠️ Windows path issues (use `\` or raw strings)

---

## Claude Code CLI Integration

### Overview

Claude Code CLI is Anthropic's official command-line interface for Claude. TappsCodingAgents has **full integration** with Claude Code, including Skills, subagents, and automatic orchestration.

**Why Claude Code CLI**:
- ✅ Terminal-native (no IDE required)
- ✅ Full CLI command support
- ✅ **Skills support** (via `.claude/skills/` - same as Cursor)
- ✅ **Native subagents** (`.claude/agents/` for parallel execution)
- ✅ **Automatic workflow orchestration** (same as Cursor)
- ✅ Expert system works fully (including `@expert` skill)
- ✅ **Epic orchestration** with parallel story execution
- ✅ Good for remote/SSH workflows
- ✅ Cross-platform (Windows, Mac, Linux)

**Limitations**:
- ⚠️ No IDE integration (terminal-only experience)
- ⚠️ No visual diff or inline code changes

### Setup

**1. Install Claude Code CLI**:
```bash
# Install from npm
npm install -g @anthropic/claude-code

# Or via pip
pip install claude-code
```

**2. Install TappsCodingAgents**:
```bash
pip install tapps-agents
```

**3. Configure Project**:
```bash
cd your-project
tapps-agents init
```

**4. Auto-Configure Claude Code Settings**:
```bash
# tapps-agents init automatically detects Claude Code and configures:
# - .claude/settings.json (permissions, env, MCP)
# - .claude/agents/ (subagent definitions)
# - .claude/skills/ (all agent skills)
tapps-agents init
```

### Usage

#### Via Claude Code Chat (Skills - Same as Cursor)

```bash
# Start Claude Code session
claude

# Use Skills directly in Claude Code (same syntax as Cursor):
@simple-mode *build "Add user authentication"
@reviewer *review src/auth.py
@tester *test src/auth.py
@expert *list
@expert *consult security "OAuth2 best practices"
```

#### Via Claude Code Subagents

Claude Code natively supports subagents defined in `.claude/agents/`:
- **story-executor** (sonnet): Execute individual stories from Epics
- **code-reviewer** (sonnet): Parallel code review
- **researcher** (haiku): Fast codebase exploration
- **epic-orchestrator**: Multi-story Epic execution
- **debugger-agent** (sonnet): Error analysis
- **security-auditor** (sonnet): Security-focused review

#### Via Direct CLI

```bash
# Use tapps-agents CLI commands directly
tapps-agents reviewer review src/auth.py
tapps-agents tester test src/auth.py
tapps-agents simple-mode build --prompt "Add user authentication"

# Epic commands
tapps-agents simple-mode epic docs/prd/epic-51.md --approved --story-workflow-mode story-only
tapps-agents epic status --epic-id my-epic
tapps-agents epic approve --epic-id my-epic

# Expert commands
tapps-agents expert list
tapps-agents expert consult --domain security --question "OAuth2 patterns"
tapps-agents expert search --query "authentication"
tapps-agents expert cached
```

### Features

**Expert System**:
- ✅ Automatic expert consultation
- ✅ `@expert` skill for interactive use
- ✅ Knowledge base RAG
- ✅ Expert history tracking
- ✅ CLI expert commands (list, consult, info, search, cached)

**Workflows**:
- ✅ **Full automatic orchestration** (same as Cursor via Skills)
- ✅ CLI commands for all agents
- ✅ Epic orchestration with parallel story waves
- ✅ Story-only workflow mode for pre-approved stories
- ✅ State persistence, resume, and handoff across sessions

**Code Quality**:
- ✅ Code review via CLI and Skills
- ✅ Quality gates enforced
- ✅ Security scanning
- ✅ Test coverage reports

**Subagents**:
- ✅ Native Claude Code subagents (`.claude/agents/`)
- ✅ Model routing (haiku for research, sonnet for implementation)
- ✅ Persistent project memory across sessions

### Workflow Execution

**Claude Code** (Automatic - Same as Cursor):
```bash
# Skills-based - all steps execute automatically
@simple-mode *build "Add user authentication"
# All 7 steps execute automatically

# Full SDLC
@simple-mode *full "Implement new authentication system"

# Epic execution with parallel stories
@simple-mode *epic docs/prd/epic-51.md
```

**Claude Code CLI** (Direct):
```bash
# Workflow presets (automated)
tapps-agents simple-mode build --prompt "Add user authentication" --auto
tapps-agents simple-mode full --prompt "Build API" --auto
tapps-agents workflow rapid --prompt "Add feature" --auto
```

### Limitations

- ⚠️ No IDE integration (terminal-only, no inline diff)
- ⚠️ No visual code navigation

---

## VS Code + Continue Integration

### Overview

Continue is an open-source AI coding assistant for VS Code. TappsCodingAgents can work with Continue, but integration is less seamless than Cursor.

**Why VS Code + Continue**:
- ✅ Free and open-source
- ✅ Works with any LLM (OpenAI, Anthropic, local models)
- ✅ CLI commands work fully
- ✅ Familiar VS Code environment

**Limitations**:
- ❌ No Cursor Skills support
- ⚠️ Manual workflow execution
- ⚠️ Must configure Continue separately
- ⚠️ Expert system requires CLI invocation

### Setup

**1. Install VS Code + Continue**:
```bash
# Install VS Code
# Install Continue extension from marketplace
```

**2. Install TappsCodingAgents**:
```bash
pip install tapps-agents
```

**3. Configure Continue**:
```json
// .continue/config.json
{
  "models": [
    {
      "title": "Claude Sonnet",
      "provider": "anthropic",
      "model": "claude-sonnet-4.5",
      "apiKey": "your-api-key"
    }
  ],
  "customCommands": [
    {
      "name": "tapps-review",
      "description": "Review code with TappsCodingAgents",
      "prompt": "Run: tapps-agents reviewer review {filepath}"
    }
  ]
}
```

**4. Configure Project**:
```bash
cd your-project
tapps-agents init
```

### Usage

#### Via Continue Chat

```
# In Continue chat
@tapps-review src/auth.py

# Continue will execute:
tapps-agents reviewer review src/auth.py
```

#### Via VS Code Terminal

```bash
# Use tapps-agents CLI directly
tapps-agents reviewer review src/auth.py
tapps-agents tester test src/auth.py
```

### Features

**Expert System**:
- ✅ Works via CLI
- ⚠️ Must manually invoke
- ✅ Knowledge base RAG
- ⚠️ No passive notifications (CLI doesn't support yet)

**Workflows**:
- ⚠️ Manual execution only
- ✅ All CLI commands available
- ❌ No automatic orchestration

**Code Quality**:
- ✅ Code review via CLI
- ✅ Quality gates enforced
- ✅ Security scanning
- ✅ Test coverage reports

### Custom Commands

Add custom Continue commands for common TappsCodingAgents workflows:

```json
// .continue/config.json
{
  "customCommands": [
    {
      "name": "tapps-review",
      "prompt": "tapps-agents reviewer review {filepath}"
    },
    {
      "name": "tapps-test",
      "prompt": "tapps-agents tester test {filepath}"
    },
    {
      "name": "tapps-fix",
      "prompt": "tapps-agents debugger debug \"{error}\""
    },
    {
      "name": "tapps-build",
      "prompt": "tapps-agents simple-mode build --prompt \"{prompt}\""
    }
  ]
}
```

### Limitations

- ❌ No Cursor Skills
- ❌ No automatic workflows
- ⚠️ Must configure Continue separately
- ⚠️ Less integrated than Cursor
- ⚠️ Requires API key for Anthropic models

---

## GitHub Codespaces Integration

### Overview

GitHub Codespaces provides cloud-based development environments. TappsCodingAgents works in Codespaces with full feature support.

**Why Codespaces**:
- ✅ Cloud-based (no local setup)
- ✅ Pre-configured environments
- ✅ Full CLI access
- ✅ Works with Cursor and VS Code

**Use Cases**:
- Remote development
- Team collaboration
- CI/CD integration
- Quick prototyping

### Setup

**1. Create Codespace**:
```bash
# From GitHub repository, create Codespace
# Or use gh CLI:
gh codespace create
```

**2. Install TappsCodingAgents**:
```bash
# In Codespace terminal
pip install tapps-agents
```

**3. Configure Project**:
```bash
tapps-agents init
```

**4. (Optional) Install Cursor Skills**:
```bash
# If using Cursor in Codespace
tapps-agents setup-skills
```

### Usage

**With Cursor**:
```cursor
# Same as local Cursor usage
@simple-mode *build "Add user authentication"
@reviewer *review src/auth.py
```

**With VS Code**:
```bash
# Use CLI commands
tapps-agents reviewer review src/auth.py
tapps-agents tester test src/auth.py
```

### Features

**Expert System**:
- ✅ Full support
- ✅ Knowledge base works (stored in `.tapps-agents/knowledge`)
- ✅ Expert consultation
- ✅ Passive notifications (if using Cursor)

**Workflows**:
- ✅ Full support (if using Cursor)
- ⚠️ Manual execution (if using VS Code)

**Code Quality**:
- ✅ All features work
- ✅ Quality gates enforced
- ✅ Security scanning
- ✅ Test coverage

### Credential Management

**Challenge**: Codespaces are ephemeral—credentials don't persist.

**Solutions**:

**Option 1: GitHub Secrets**:
```bash
# Store secrets in GitHub repo settings
# Access in Codespace:
echo $GITHUB_SECRET
```

**Option 2: Codespace Secrets**:
```bash
# gh CLI
gh secret set API_KEY --repos owner/repo
```

**Option 3: Environment Variables**:
```bash
# In .devcontainer/devcontainer.json
{
  "remoteEnv": {
    "API_KEY": "${localEnv:API_KEY}"
  }
}
```

**Best Practice**: Use `.env.example` with required variables:
```bash
# .env.example
SITE24X7_CLIENT_ID=your-client-id
SITE24X7_CLIENT_SECRET=your-client-secret

# In Codespace:
cp .env.example .env
# Edit .env with real values
```

### Limitations

- ⚠️ Ephemeral environment (credentials don't persist)
- ⚠️ Slower than local (network latency)
- ⚠️ Costs money (GitHub Codespaces pricing)
- ⚠️ Limited to 60 hours/month (free tier)

---

## Claude.ai Web Integration

### Overview

Claude.ai (web interface) has **limited** support for TappsCodingAgents. You can discuss TappsCodingAgents concepts but cannot execute commands.

**Why Claude.ai Web**:
- ✅ No installation required
- ✅ Mobile accessible
- ✅ Quick prototyping (ideas, architecture)

**Limitations**:
- ❌ Cannot execute tapps-agents commands
- ❌ No file system access
- ❌ No expert system integration
- ❌ No workflows
- ⚠️ Can only discuss concepts, not execute

### What You CAN Do

**✅ Discuss Concepts**:
```
> How should I structure my Site24x7 knowledge base for TappsCodingAgents?

Claude: Based on TappsCodingAgents best practices, structure your knowledge
base with INDEX.md, RAG_SUMMARY.md, and topic-specific files...
```

**✅ Get Architecture Advice**:
```
> What expert priority should I use for OAuth authentication in TappsCodingAgents?

Claude: OAuth authentication is security-critical, so use priority 0.95+...
```

**✅ Review Configuration**:
```
> Here's my experts.yaml. Is this correct?

[paste experts.yaml]

Claude: Your configuration looks good, but I'd recommend...
```

### What You CANNOT Do

**❌ Execute Commands**:
```
> Run tapps-agents reviewer review src/auth.py

Claude: I cannot execute commands from Claude.ai web interface.
You'll need to run this locally or in Codespaces.
```

**❌ Access Files**:
```
> Review my src/auth.py file

Claude: I don't have access to your file system from this interface.
You can paste the file content, or use Cursor/Claude Code CLI.
```

**❌ Use Expert System**:
```
> Consult the Site24x7 expert

Claude: The expert system requires TappsCodingAgents installation and
knowledge base setup. This isn't available in the web interface.
```

### Best Practices

**Use Claude.ai Web For**:
- ✅ Planning and architecture discussions
- ✅ Configuration review (paste config files)
- ✅ Learning TappsCodingAgents concepts
- ✅ Quick questions while mobile

**Don't Use For**:
- ❌ Actual development work
- ❌ Code review (use Cursor or CLI)
- ❌ Running workflows
- ❌ Expert consultation

---

## Mobile Access

### Challenge

**Problem**: Mobile devices (iPhone, Android) cannot run full development environments.

**Impact**: Cannot configure `.env` files, run CLI commands, or execute workflows from mobile.

### Solutions

**Option 1: GitHub Codespaces** (Recommended):
```
1. Create Codespace from GitHub
2. Access via mobile browser
3. Use VS Code web interface
4. Execute commands in terminal
```

**Pros**:
- ✅ Full functionality
- ✅ No local setup
- ✅ Persistent environment (can resume)

**Cons**:
- ⚠️ Mobile UI not optimized
- ⚠️ Requires GitHub account and payment

**Option 2: Claude.ai Web + Desktop Handoff**:
```
1. Plan on mobile (Claude.ai)
2. Document decisions
3. Execute on desktop later
```

**Pros**:
- ✅ Free
- ✅ Mobile-friendly

**Cons**:
- ❌ Cannot execute commands
- ⚠️ Requires desktop for actual work

**Option 3: Remote Server SSH**:
```
1. SSH to remote server from mobile
2. Use terminal-based tools (tmux, vim)
3. Run tapps-agents CLI commands
```

**Pros**:
- ✅ Full CLI access
- ✅ Can execute commands

**Cons**:
- ⚠️ Requires SSH setup
- ⚠️ Mobile terminal UX poor

### Recommendation

**For Planning**: Use Claude.ai Web on mobile
**For Development**: Use GitHub Codespaces or desktop

---

## Choosing the Right Tool

### Decision Matrix

**Use Cursor IDE if**:
- ✅ You want the best TappsCodingAgents experience
- ✅ You prefer IDE-integrated workflows
- ✅ You want automatic workflow orchestration
- ✅ You're working locally on your machine

**Use Claude Code CLI if**:
- ✅ You prefer terminal-based workflows
- ✅ You're working via SSH
- ✅ You want fine-grained control with full orchestration
- ✅ You need subagent-based parallel execution
- ✅ You want persistent memory across sessions

**Use VS Code + Continue if**:
- ✅ You're already a VS Code user
- ✅ You want free and open-source
- ✅ You're okay with manual workflows
- ✅ You want to use different LLMs

**Use GitHub Codespaces if**:
- ✅ You need cloud-based development
- ✅ You're collaborating with a team
- ✅ You want quick setup
- ✅ You need remote access

**Use Claude.ai Web if**:
- ✅ You're planning or discussing concepts
- ✅ You're on mobile without Codespaces
- ✅ You need quick advice
- ❌ You don't need to execute commands

---

## Migration Guide

### From Cursor to Claude Code CLI

**What Changes**:
- ✅ Same `@simple-mode` commands work in Claude Code
- ✅ Same `.claude/skills/` are used
- ✅ Additional subagents available (`.claude/agents/`)
- ⚠️ No IDE integration (inline diff, visual navigation)

**Migration**:
```bash
# Cursor (before)
@simple-mode *build "Add authentication"

# Claude Code CLI (same syntax works!)
@simple-mode *build "Add authentication"

# Or use CLI directly
tapps-agents simple-mode build --prompt "Add authentication" --auto
```

### From VS Code + Continue to Cursor

**What Improves**:
- ✅ Cursor Skills support
- ✅ Automatic workflows
- ✅ Better UX

**Migration**:
```bash
# Install Cursor
# Install skills
cd your-project
tapps-agents setup-skills

# Start using @-commands
@simple-mode *build "..."
```

### From Claude.ai Web to Any Tool

**What You Gain**:
- ✅ File system access
- ✅ Command execution
- ✅ Expert system
- ✅ Workflows

**Migration**:
```bash
# Choose a tool (Cursor recommended)
# Install TappsCodingAgents
pip install tapps-agents

# Initialize project
tapps-agents init

# Start developing
```

---

## Troubleshooting

### Cursor Skills Not Working

**Symptoms**:
- `@simple-mode` not recognized
- Commands not executing

**Solutions**:
1. **Re-run setup**:
   ```bash
   tapps-agents setup-skills
   ```

2. **Check `.claude/skills/` directory exists**:
   ```bash
   ls -la .claude/skills/
   ```

3. **Restart Cursor**

### CLI Commands Fail

**Symptoms**:
- `tapps-agents: command not found`
- `ModuleNotFoundError: No module named 'tapps_agents'`

**Solutions**:
1. **Check installation**:
   ```bash
   pip show tapps-agents
   ```

2. **Reinstall**:
   ```bash
   pip install --upgrade tapps-agents
   ```

3. **Check Python path**:
   ```bash
   which python
   which tapps-agents
   ```

### Expert System Not Working

**Symptoms**:
- No expert consultation
- "No knowledge available" messages

**Solutions**:
1. **Check configuration**:
   ```bash
   cat .tapps-agents/config.yaml
   ```

2. **Check knowledge base**:
   ```bash
   ls -la .tapps-agents/knowledge/
   ```

3. **Reinitialize**:
   ```bash
   tapps-agents init
   ```

---

## Related Documentation

- **[Installation Guide](../README.md#installation)** - How to install TappsCodingAgents
- **[Configuration Guide](CONFIGURATION.md)** - Complete configuration reference
- **[Cursor Skills Guide](CURSOR_SKILLS_INSTALLATION_GUIDE.md)** - Cursor Skills setup

---

## FAQ

### Q: Which tool is fastest?

**A**: **Cursor IDE** is fastest due to native integration and automatic orchestration.

### Q: Can I use TappsCodingAgents without an IDE?

**A**: Yes, use **Claude Code CLI** for terminal-only workflows.

### Q: Does TappsCodingAgents work on mobile?

**A**: Indirectly via **GitHub Codespaces** (mobile browser), but mobile UX is poor. Use **Claude.ai Web** for planning only.

### Q: Can I use my own LLM (not Claude)?

**A**: Yes with **Cursor** (configure your LLM in Cursor settings) or **VS Code + Continue** (supports many LLMs).

### Q: Which tool is cheapest?

**A**: **VS Code + Continue** (free and open-source). **Cursor** requires Cursor Pro subscription.

### Q: Can I switch tools mid-project?

**A**: Yes, all tools use the same `.tapps-agents/` configuration. You can switch freely.

---

**Version History**:
- **1.1.0** (2026-02-05): Updated Claude Code CLI section with full Skills, subagents, Epic orchestration, and expert system integration
- **1.0.0** (2026-01-28): Initial release based on Site24x7 feedback

**Maintainer**: TappsCodingAgents Team
**Feedback**: Create GitHub issue or update this document via PR
