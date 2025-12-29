# Quick Upgrade Guide

**TL;DR:** After upgrading TappsCodingAgents, run `tapps-agents init` to get the new Claude Desktop Commands.

## For New Projects

```bash
# 1. Upgrade
pip install --upgrade tapps-agents

# 2. Initialize
cd your-project
tapps-agents init
```

✅ Done! You now have both Cursor Skills and Claude Desktop Commands.

## For Existing Projects

```bash
# 1. Upgrade
pip install --upgrade tapps-agents

# 2. Add new commands (preserves existing files)
cd your-existing-project
tapps-agents init
```

✅ Done! New commands are added, existing files are preserved.

## What You Get

- **16 Claude Desktop Commands** (`.claude/commands/`) - Use in Claude Desktop
- **14 Cursor Skills** (`.claude/skills/`) - Use in Cursor IDE
- **Same functionality** in both environments

## Quick Test

**In Cursor IDE:**
```
@reviewer *review src/api/auth.py
```

**In Claude Desktop:**
```
@review src/api/auth.py
```

## Need More Details?

See [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md) for complete upgrade instructions.

