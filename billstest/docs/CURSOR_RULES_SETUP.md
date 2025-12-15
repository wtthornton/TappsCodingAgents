# Cursor Rules Setup Guide

**Automatic setup of Cursor Rules for workflow presets**

## Overview

TappsCodingAgents can automatically set up Cursor Rules that provide context about workflow presets, making it easier to use them in Cursor AI conversations.

## What Gets Installed

### Cursor Rules

**Location:** `.cursor/rules/`

**Files installed by `tapps-agents init`:**
- `workflow-presets.mdc`
- `quick-reference.mdc`
- `agent-capabilities.mdc`
- `project-context.mdc`

**Content:**
- Documentation of all 5 workflow presets
- When to use each workflow
- Agent sequences for each workflow
- Quality gate thresholds
- Usage examples

**Benefits:**
- Cursor AI understands workflow presets
- Can suggest appropriate workflows
- Natural language support ("run rapid development")
- Voice command support

### Workflow Presets

**Location:** `workflows/presets/`

**Files:**
- `full-sdlc.yaml`
- `rapid-dev.yaml`
- `maintenance.yaml`
- `quality.yaml`
- `quick-fix.yaml`

## Installation Methods

### Method 1: During Project Initialization (Recommended)

```bash
python -m tapps_agents.cli init
```

This will:
1. Install Cursor Rules into `.cursor/rules/`
2. Copy workflow presets to `workflows/presets/`
3. Install Skills into `.claude/skills/` (unless `--no-skills`)
4. Install Background Agents config into `.cursor/background-agents.yaml` (unless `--no-background-agents`)
5. Optionally create `.tapps-agents/config.yaml` (unless `--no-config`)

**Options:**
```bash
# Skip Cursor Rules
python -m tapps_agents.cli init --no-rules

# Skip workflow presets
python -m tapps_agents.cli init --no-presets
```

Additional options:

```bash
# Skip installing Skills
python -m tapps_agents.cli init --no-skills

# Skip installing Background Agents config
python -m tapps_agents.cli init --no-background-agents
```

### Method 2: During Expert Setup

```bash
python -m tapps_agents.cli setup-experts init
```

The expert setup wizard will offer to initialize Cursor Rules and presets.

### Method 3: Manual Installation

**Copy Cursor Rules:**
```bash
# Create directory
mkdir -p .cursor/rules

# Copy rule file
cp TappsCodingAgents/.cursor/rules/workflow-presets.mdc .cursor/rules/
```

**Copy Workflow Presets:**
```bash
# Create directory
mkdir -p workflows/presets

# Copy presets
cp TappsCodingAgents/workflows/presets/*.yaml workflows/presets/
```

## Verification

### Check Cursor Rules

```bash
# Verify rule file exists
ls .cursor/rules/workflow-presets.mdc

# View rule content
cat .cursor/rules/workflow-presets.mdc
```

### Check Workflow Presets

```bash
# List presets
python -m tapps_agents.cli workflow list

# Test a preset
python -m tapps_agents.cli workflow rapid
```

## Usage in Cursor AI

Once installed, Cursor AI will understand workflow presets:

### Natural Language

**You can say:**
- "Run rapid development workflow"
- "Execute full SDLC pipeline"
- "Start quality improvement cycle"
- "Use the quick fix workflow"

**Cursor AI will:**
- Understand which workflow you mean
- Suggest the appropriate command
- Execute: `python -m tapps_agents.cli workflow <alias>`

### Voice Commands

**Supported:**
- "run rapid dev" → `workflow rapid`
- "execute enterprise workflow" → `workflow enterprise`
- "start quick fix" → `workflow hotfix`
- "run quality improvement" → `workflow quality`

## Customization

### Modify Cursor Rules

Edit `.cursor/rules/workflow-presets.mdc` to:
- Add project-specific workflows
- Customize quality thresholds
- Add domain-specific guidance

### Modify Workflow Presets

Edit files in `workflows/presets/` to:
- Change agent sequences
- Adjust quality gates
- Add custom steps

## Integration with Installation

### Automatic Setup

When installing TappsCodingAgents in a new project:

```bash
# Install package
pip install -e .

# Initialize project (includes Cursor Rules)
python -m tapps_agents.cli init
```

### Post-Installation

After installation, you can add Cursor Rules:

```bash
# Just add Cursor Rules
python -m tapps_agents.cli init --no-presets

# Or use expert setup wizard
python -m tapps_agents.cli setup-experts init
```

## Troubleshooting

### Rules Not Working

**Problem:** Cursor AI doesn't understand workflow commands

**Solution:**
1. Verify `.cursor/rules/workflow-presets.mdc` exists
2. Restart Cursor IDE
3. Check rule file syntax (should be valid markdown)

### Presets Not Found

**Problem:** `workflow list` shows no presets

**Solution:**
1. Verify `workflows/presets/` directory exists
2. Check preset YAML files are present
3. Run: `python -m tapps_agents.cli init`

### Permission Errors

**Problem:** Cannot create `.cursor/rules/` directory

**Solution:**
1. Check write permissions
2. Create directory manually: `mkdir -p .cursor/rules`
3. Copy rule file manually

## Best Practices

1. **Initialize Early:** Run `init` when starting a new project
2. **Version Control:** Commit `.cursor/rules/` to git
3. **Customize:** Modify rules for project-specific needs
4. **Update:** Re-run `init` after framework updates

## See Also

- [Quick Workflow Commands Guide](QUICK_WORKFLOW_COMMANDS.md)
- [Cursor Skills Installation Guide](CURSOR_SKILLS_INSTALLATION_GUIDE.md)
- [Workflow Selection Guide](WORKFLOW_SELECTION_GUIDE.md)

