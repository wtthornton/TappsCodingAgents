# Getting Started with TappsCodingAgents in Cursor IDE

**Quick guide to avoid common mistakes when using TappsCodingAgents in Cursor IDE.**

## ⚠️ Most Common Mistake: CLI Workflow Commands in Cursor Mode

**If you see this warning:**
```
⚠️  CLI Workflow Commands Not Recommended in Cursor Mode
```

**You're trying to run a CLI workflow command inside Cursor IDE. Here's how to fix it:**

### ✅ Quick Fix

**Instead of:**
```bash
# ❌ Don't do this in Cursor IDE
tapps-agents workflow fix --file <file> --auto
```

**Use this in Cursor chat:**
```cursor
@simple-mode *fix <file> "description"
```

## Step-by-Step Setup

### 1. Install TappsCodingAgents

```bash
pip install tapps-agents
```

### 2. Initialize Your Project

```bash
cd your-project
tapps-agents init
```

**What `init` installs:**
- ✅ Cursor Rules (`.cursor/rules/`) - 8 rule files including `cursor-mode-usage.mdc`
- ✅ Cursor Skills (`.claude/skills/`) - 15 skills including `simple-mode`
- ✅ Configuration (`.tapps-agents/config.yaml`)
- ✅ Workflow presets (`workflows/presets/`)

### 3. Verify Setup

```bash
tapps-agents simple-mode status
tapps-agents cursor verify
```

### 4. Start Using in Cursor Chat

**Use `@simple-mode` commands (recommended):**
```cursor
@simple-mode *build "Add user authentication"
@simple-mode *fix src/buggy.py "Fix the error"
@simple-mode *review src/api.py
@simple-mode *test src/service.py
```

## Understanding Cursor Mode vs CLI Mode

### Cursor Mode (Inside Cursor IDE)

**Use when:**
- ✅ Working interactively in Cursor IDE
- ✅ Need natural language commands
- ✅ Want context-aware assistance
- ✅ Learning the framework

**Commands:**
- `@simple-mode *command` (recommended)
- `@agent-name *command` (advanced)

**Example:**
```cursor
@simple-mode *build "Create a REST API for products"
```

### CLI Mode (Terminal/CI)

**Use when:**
- ✅ Running in terminal (outside Cursor IDE)
- ✅ CI/CD pipelines
- ✅ Shell scripts
- ✅ Batch processing

**Commands:**
- `tapps-agents workflow <preset>`
- `tapps-agents <agent> <command>`

**Example:**
```bash
tapps-agents workflow rapid --prompt "Add feature" --auto
```

## Command Reference

| Task | In Cursor IDE | In Terminal/CI |
|------|---------------|----------------|
| Fix bug | `@simple-mode *fix <file> "desc"` | `tapps-agents workflow fix --file <file> --auto` |
| Build feature | `@simple-mode *build "desc"` | `tapps-agents workflow rapid --prompt "desc" --auto` |
| Review code | `@simple-mode *review <file>` | `tapps-agents reviewer review <file>` |
| Generate tests | `@simple-mode *test <file>` | `tapps-agents tester test <file>` |
| Full SDLC | `@simple-mode *full "desc"` | `tapps-agents workflow full --prompt "desc" --auto` |

## Troubleshooting

### "CLI Workflow Commands Not Recommended in Cursor Mode"

**Problem:** You're running CLI workflow commands in Cursor IDE.

**Solution:**
1. Use `@simple-mode` commands in Cursor chat instead
2. Or use CLI commands in terminal (outside Cursor IDE)
3. Or add `--cli-mode` flag (not recommended)

### "Simple Mode not available"

**Problem:** `@simple-mode` commands don't work.

**Solution:**
1. Run `tapps-agents init` to install Cursor Skills
2. Verify with `tapps-agents simple-mode status`
3. Check that `.claude/skills/simple-mode/` exists

### "Cursor Skills not found"

**Problem:** `@agent-name` commands don't work.

**Solution:**
1. Run `tapps-agents init` (don't use `--no-skills`)
2. Verify with `tapps-agents cursor verify`
3. Check that `.claude/skills/` directory exists

## Next Steps

- Read `.cursor/rules/cursor-mode-usage.mdc` for detailed guidance
- Read `.cursor/rules/simple-mode.mdc` for Simple Mode documentation
- Read `.cursor/rules/quick-reference.mdc` for quick command reference
- Read `docs/CURSOR_MODE_CLI_WORKFLOW_WARNING_ANALYSIS.md` for detailed analysis

## Related Documentation

- `.cursor/rules/cursor-mode-usage.mdc` - Complete Cursor mode usage guide
- `.cursor/rules/simple-mode.mdc` - Simple Mode guide
- `.cursor/rules/quick-reference.mdc` - Quick reference
- `.cursor/rules/command-reference.mdc` - Complete command reference
