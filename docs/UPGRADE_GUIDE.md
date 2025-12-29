# Upgrade Guide: Claude Desktop Commands & Cursor Skills

This guide explains what new and existing projects need to do after upgrading TappsCodingAgents to ensure they have the latest Claude Desktop Commands and Cursor Skills.

## What's New

TappsCodingAgents now includes **Claude Desktop Commands** that work alongside Cursor Skills:

- **16 Claude Desktop Commands** (`.claude/commands/`) - Work in Claude Desktop
- **14 Cursor Skills** (`.claude/skills/`) - Work in Cursor IDE
- **Unified Experience** - Same functionality in both environments

## Quick Upgrade Steps

### For New Projects

**Step 1: Upgrade TappsCodingAgents**

```bash
pip install --upgrade tapps-agents
```

**Step 2: Initialize Project**

```bash
cd your-project
tapps-agents init
```

This automatically installs:
- ✅ Cursor Skills (`.claude/skills/`)
- ✅ Claude Desktop Commands (`.claude/commands/`)
- ✅ Cursor Rules (`.cursor/rules/`)
- ✅ Background Agents config (`.cursor/background-agents.yaml`)
- ✅ Workflow presets (`workflows/presets/`)

**That's it!** Your project is now set up with both Skills and Commands.

### For Existing Projects

**Step 1: Upgrade TappsCodingAgents**

```bash
pip install --upgrade tapps-agents
```

**Step 2: Update Project Integration**

Run `init` again to get the new Claude Desktop Commands:

```bash
cd your-existing-project
tapps-agents init
```

**What happens:**
- ✅ New Claude Desktop Commands are installed (`.claude/commands/`)
- ✅ Existing Cursor Skills are preserved (`.claude/skills/`)
- ✅ Existing Cursor Rules are preserved (`.cursor/rules/`)
- ✅ Your customizations are preserved

**Note:** `init` is **idempotent** - it won't overwrite existing files unless you use `--reset`.

## Upgrade Options

### Option 1: Standard Upgrade (Recommended)

Just run `init` to get new commands:

```bash
tapps-agents init
```

This adds new files without modifying existing ones.

### Option 2: Reset Framework Files

If you want to update framework-managed files to the latest version:

```bash
tapps-agents init --reset
```

**What gets reset:**
- Framework Skills (`.claude/skills/`)
- Framework Commands (`.claude/commands/`)
- Framework Rules (`.cursor/rules/`)
- Framework Background Agents config (`.cursor/background-agents.yaml`)

**What's preserved:**
- Your customizations (`.tapps-agents/customizations/`)
- Your config (`.tapps-agents/config.yaml`)
- Your workflow presets (if customized)
- Your custom Skills/Commands

### Option 3: Preview Changes

See what would be reset without making changes:

```bash
tapps-agents init --reset --dry-run
```

## What Gets Installed

### Claude Desktop Commands (`.claude/commands/`)

16 commands for Claude Desktop:

**Core Development:**
- `review.md` - Code review with scoring
- `score.md` - Quick quality scoring
- `implement.md` - Code generation
- `test.md` - Test generation
- `debug.md` - Error debugging
- `refactor.md` - Code refactoring
- `improve.md` - Code improvement
- `lint.md` - Code linting

**Planning & Design:**
- `plan.md` - Development planning
- `design.md` - System design
- `docs.md` - Documentation

**Quality & Security:**
- `security-scan.md` - Security scanning
- `library-docs.md` - Library documentation

**Workflows:**
- `build.md` - Complete feature workflow
- `fix.md` - Bug fixing workflow

### Cursor Skills (`.claude/skills/`)

14 skills for Cursor IDE:

- `reviewer/` - Code review
- `implementer/` - Code generation
- `tester/` - Test generation
- `debugger/` - Error debugging
- `planner/` - Development planning
- `architect/` - System design
- `designer/` - API/data design
- `analyst/` - Requirements gathering
- `documenter/` - Documentation
- `improver/` - Code improvement
- `ops/` - Security/operations
- `orchestrator/` - Workflow coordination
- `enhancer/` - Prompt enhancement
- `simple-mode/` - Natural language orchestrator

## Verification

### Check Installation

**Verify Commands:**
```bash
ls .claude/commands/
# Should show 16 .md files
```

**Verify Skills:**
```bash
ls .claude/skills/
# Should show 14 skill directories
```

**Verify in Cursor:**
1. Open Cursor IDE
2. Type `@reviewer` in chat
3. Should see Reviewer agent available

**Verify in Claude Desktop:**
1. Open Claude Desktop
2. Type `@review` in chat
3. Should see review command available

### Test Commands

**In Cursor IDE:**
```
@reviewer *review src/api/auth.py
@simple-mode *build "Create a user authentication feature"
```

**In Claude Desktop:**
```
@review src/api/auth.py
@build "Create a user authentication feature"
```

## Troubleshooting

### Commands Not Appearing in Claude Desktop

**Issue:** Commands don't show up when typing `@` in Claude Desktop.

**Solution:**
1. Verify commands are installed:
   ```bash
   ls .claude/commands/
   ```

2. Restart Claude Desktop

3. Check command syntax - use `@command-name` (no spaces)

### Skills Not Working in Cursor

**Issue:** Skills don't work when typing `@agent-name` in Cursor.

**Solution:**
1. Verify skills are installed:
   ```bash
   ls .claude/skills/
   ```

2. Restart Cursor IDE

3. Check skill syntax - use `@agent-name *command`

### Files Not Updating After Upgrade

**Issue:** Running `init` doesn't update existing files.

**Solution:**
- Use `--reset` to update framework-managed files:
  ```bash
  tapps-agents init --reset
  ```

- Or manually update specific files if needed

### Custom Skills/Commands Not Preserved

**Issue:** Custom skills or commands are overwritten.

**Solution:**
- `init` preserves custom files by default
- Use `--preserve-custom` (default) to ensure preservation
- Custom files should be in separate directories or have different names

## Migration Checklist

For existing projects upgrading to the new version:

- [ ] Upgrade TappsCodingAgents: `pip install --upgrade tapps-agents`
- [ ] Run `tapps-agents init` to install new commands
- [ ] Verify commands: `ls .claude/commands/`
- [ ] Verify skills: `ls .claude/skills/`
- [ ] Test in Cursor: `@reviewer *help`
- [ ] Test in Claude Desktop: `@review --help` (if supported)
- [ ] Review new documentation: `docs/CLAUDE_DESKTOP_COMMANDS.md`
- [ ] Update team documentation with new command syntax

## Command Comparison

| Task | Claude Desktop | Cursor IDE | CLI |
|------|---------------|------------|-----|
| Code Review | `@review <file>` | `@reviewer *review <file>` | `tapps-agents reviewer review <file>` |
| Build Feature | `@build "<desc>"` | `@simple-mode *build "<desc>"` | `tapps-agents simple-mode full --prompt "<desc>"` |
| Generate Tests | `@test <file>` | `@tester *test <file>` | `tapps-agents tester test <file>` |
| Get Library Docs | `@library-docs fastapi` | `@reviewer *docs fastapi` | `tapps-agents reviewer docs fastapi` |

## Related Documentation

- **Claude Desktop Commands Guide**: `docs/CLAUDE_DESKTOP_COMMANDS.md`
- **Cursor Skills Guide**: `docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md`
- **Command Reference**: `docs/TAPPS_AGENTS_COMMAND_REFERENCE.md`
- **Quick Reference**: `.cursor/rules/quick-reference.mdc`

## Summary

**For New Projects:**
1. `pip install --upgrade tapps-agents`
2. `tapps-agents init`
3. Done! ✅

**For Existing Projects:**
1. `pip install --upgrade tapps-agents`
2. `tapps-agents init` (adds new commands)
3. Optional: `tapps-agents init --reset` (updates framework files)
4. Done! ✅

Both Skills and Commands are now available in your project, providing a unified experience across Claude Desktop and Cursor IDE.

