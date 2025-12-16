# Installation & Initialization Summary

## Quick Installation

```bash
# 1. Install package
pip install -e .

# 2. Initialize project (sets up Cursor Rules + Skills + Background Agents + workflow presets + config)
python -m tapps_agents.cli init

# 3. Set up experts (optional)
python -m tapps_agents.cli setup-experts init
```

## What Gets Installed

### Package Installation (`pip install -e .`)

- ✅ Framework code (`tapps_agents/` package)
- ✅ All 13 workflow agents
- ✅ Expert system
- ✅ CLI commands
- ✅ Context7 integration

### Project Initialization (`python -m tapps_agents.cli init`)

- ✅ Cursor Rules (`.cursor/rules/*.mdc`) - AI context documentation
- ✅ Cursor Skills (`.claude/skills/`) - Agent capabilities for Cursor Skills system
- ✅ Cursor Background Agents config (`.cursor/background-agents.yaml`) - Background agent definitions
- ✅ `.cursorignore` - Indexing optimization file
- ✅ Workflow presets (`workflows/presets/*.yaml`)
- ✅ Starter config (`.tapps-agents/config.yaml`)

**Understanding the Setup:**
- **`.claude/skills/`**: Cursor Skills (agent_requestable_workspace_rules) - provides agent capabilities
- **`.cursor/rules/`**: Cursor Rules (.mdc files) - provides AI context and documentation
- **`.cursor/background-agents.yaml`**: Background Agents configuration - defines autonomous agents
- **`.cursorignore`**: Excludes large/generated files from Cursor indexing for better performance

### Expert Setup (`python -m tapps_agents.cli setup-experts init`)

- ✅ Expert configuration (`.tapps-agents/experts.yaml`)
- ✅ Domain configuration (`.tapps-agents/domains.md`)
- ✅ Knowledge base structure (`.tapps-agents/knowledge/`)

## Commands Available After Installation

### Workflow Commands

```bash
# List all workflows
python -m tapps_agents.cli workflow list

# Run workflows
python -m tapps_agents.cli workflow rapid
python -m tapps_agents.cli workflow full
python -m tapps_agents.cli workflow fix
python -m tapps_agents.cli workflow quality
python -m tapps_agents.cli workflow hotfix
```

### Expert Commands

```bash
# Expert setup wizard
python -m tapps_agents.cli setup-experts

# List experts
python -m tapps_agents.cli setup-experts list

# Add expert
python -m tapps_agents.cli setup-experts add
```

### Agent Commands

```bash
# Review code
python -m tapps_agents.cli reviewer review file.py

# Score code
python -m tapps_agents.cli reviewer score file.py

# All 13 agents available
python -m tapps_agents.cli --help
```

## Cursor AI Integration

After initialization, Cursor AI will understand:

- **Natural Language:** "Run rapid development workflow"
- **Voice Commands:** "Execute full SDLC pipeline"
- **Workflow References:** "Use the quality improvement cycle"

The Cursor Rules file (`.cursor/rules/workflow-presets.mdc`) provides context to Cursor AI about all available workflows.

## Verification

```bash
# Check installation
python -c "import tapps_agents; print(tapps_agents.__version__)"

# Check Cursor Rules
ls .cursor/rules/workflow-presets.mdc

# Check workflow presets
python -m tapps_agents.cli workflow list

# Check experts
python -m tapps_agents.cli setup-experts list
```

## Next Steps

1. **Try a workflow:**
   ```bash
   python -m tapps_agents.cli workflow rapid
   ```

2. **Set up experts:**
   ```bash
   python -m tapps_agents.cli setup-experts init
   ```

3. **Review code:**
   ```bash
   python -m tapps_agents.cli reviewer score example_bug.py
   ```

## See Also

- [Quick Start Guide](QUICK_START.md)
- [Cursor Rules Setup](docs/CURSOR_RULES_SETUP.md)
- [Quick Workflow Commands](docs/QUICK_WORKFLOW_COMMANDS.md)
- [Expert Setup Wizard](docs/EXPERT_SETUP_WIZARD.md)

