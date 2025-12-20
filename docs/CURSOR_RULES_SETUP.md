# Cursor Rules Setup Guide

**Automatic setup and generation of Cursor Rules for workflow presets**

## Overview

TappsCodingAgents can automatically set up and generate Cursor Rules that provide context about workflow presets, making it easier to use them in Cursor AI conversations. **Cursor Rules are now auto-generated from workflow YAML files** (Epic 8 complete), ensuring documentation always matches the actual workflow definitions.

## What Gets Installed

### Understanding `.claude` vs `.cursor`

TappsCodingAgents sets up two complementary directory structures:

- **`.claude/skills/`**: Cursor Skills (agent_requestable_workspace_rules)
  - Contains SKILL.md files for each agent
  - Used by Cursor's Skills system to provide agent capabilities
  - Each skill has YAML frontmatter with name, description, and allowed tools

- **`.cursor/rules/`**: Cursor Rules (.mdc files for AI context)
  - Contains markdown documentation files that provide context to Cursor AI
  - Each rule has YAML frontmatter with description and alwaysApply settings
  - Helps Cursor AI understand project-specific workflows and commands

- **`.cursor/background-agents.yaml`**: Background Agents configuration
  - Defines background agents that run autonomously
  - Configured for quality analysis, testing, security scanning, and PR mode

- **`.cursorignore`**: Indexing optimization
  - Excludes large/generated artifacts from Cursor's indexing
  - Improves performance by preventing unnecessary file indexing

### Cursor Rules

**Location:** `.cursor/rules/`

**Files installed by `tapps-agents init`:**
- `workflow-presets.mdc` - Workflow preset documentation (✅ **Auto-generated from YAML** - Epic 8)
- `quick-reference.mdc` - Quick command reference
- `agent-capabilities.mdc` - Agent capabilities guide
- `project-context.mdc` - Project context (always applied)
- `project-profiling.mdc` - Project profiling system documentation
- `simple-mode.mdc` - Simple Mode documentation for new users

**Content (Auto-Generated from Workflow YAML):**
- Documentation of all 5 workflow presets extracted from YAML definitions
- When to use each workflow (from YAML metadata)
- Agent sequences for each workflow (from YAML steps)
- Quality gate thresholds (from YAML gates)
- Usage examples generated from workflow structure

**Benefits:**
- ✅ **Always in sync**: Documentation auto-generated from YAML (Epic 8)
- ✅ **Zero drift**: No manual documentation maintenance needed
- ✅ **Single source of truth**: YAML workflows are authoritative
- Cursor AI understands workflow presets
- Can suggest appropriate workflows
- Natural language support ("run rapid development")
- Voice command support

**Regenerating Rules:**

Cursor Rules can be regenerated from workflow YAML files:

```bash
# Regenerate Cursor Rules from workflow YAML
tapps-agents generate-rules

# Regenerate and overwrite existing rules
tapps-agents generate-rules --overwrite
```

This ensures documentation stays aligned with workflow definitions.

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
5. Install `.cursorignore` file (unless `--no-cursorignore`)
6. Optionally create `.tapps-agents/config.yaml` (unless `--no-config`)

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

# Skip installing .cursorignore
python -m tapps_agents.cli init --no-cursorignore
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
2. Check that rule files have proper YAML frontmatter (should start with `---`)
3. Restart Cursor IDE
4. Check rule file syntax (should be valid markdown with YAML frontmatter)

### Skills Not Available

**Problem:** Cursor Skills are not showing up in agent_requestable_workspace_rules

**Solution:**
1. Verify `.claude/skills/` directory exists
2. Check that each skill directory contains `SKILL.md` with YAML frontmatter
3. Verify frontmatter includes `name`, `description`, and `allowed-tools` fields
4. Restart Cursor IDE

### Background Agents Not Working

**Problem:** Background agents are not available in Cursor

**Solution:**
1. Verify `.cursor/background-agents.yaml` exists
2. Check YAML syntax is valid
3. Verify the file contains an `agents` key with agent definitions
4. Restart Cursor IDE

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

