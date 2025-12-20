# Quick Demo Start Guide

Get TappsCodingAgents running in 5 minutes!

## Option 1: Automated Demo Script

```bash
# Run the interactive demo script
python demo/run_demo.py
```

This will:
- Check prerequisites
- Create a demo project
- Generate sample code
- Run code scoring and review demos
- Show quality tools

## Option 2: Manual Quick Demo

### Step 1: Install (if not already done)

```bash
pip install -e .
```

### Step 2: Create Demo Project

```bash
mkdir tapps-demo
cd tapps-demo
tapps-agents init
```

### Step 3: Create Sample Code

Copy the sample code from `demo/sample_code/`:

```bash
mkdir src
cp demo/sample_code/calculator.py src/
```

### Step 4: Run Code Scoring

```bash
tapps-agents score src/calculator.py
```

### Step 5: Run Full Review

```bash
tapps-agents reviewer review src/calculator.py
```

### Step 6: Generate Quality Report

```bash
tapps-agents reviewer report . json markdown html
```

## Option 3: YAML Workflow Demo (Cursor + YAML)

**Best for:** Understanding how YAML workflows work with Cursor Skills

```bash
# 1. Initialize project
tapps-agents init

# 2. View available YAML workflows
ls workflows/presets/
cat workflows/presets/rapid-dev.yaml

# 3. Run a YAML workflow with Cursor Skills (if in Cursor IDE)
tapps-agents workflow rapid --prompt "Create a REST API for tasks" --cursor-mode

# Or use Cursor Skills directly in Cursor chat:
# @orchestrator *workflow rapid --prompt "Create a REST API for tasks"

# 4. Check generated artifacts
ls stories/ src/ tests/
cat .tapps-agents/workflow-state/*/task-manifest.md
```

**Key Points:**
- ✅ Workflows are defined in YAML files (`workflows/presets/*.yaml`)
- ✅ Each step uses Cursor Skills (`@planner`, `@implementer`, `@reviewer`, etc.)
- ✅ Framework executes YAML workflow, Cursor handles LLM operations
- ✅ Artifacts are auto-generated from YAML workflow state

## Option 4: Simple Mode Demo

For new users, try Simple Mode:

```bash
# Enable Simple Mode
tapps-agents simple-mode on

# Build a feature (natural language)
tapps-agents simple-mode build -p "Create a REST API for tasks"

# Review code
tapps-agents simple-mode review --file src/api/tasks.py

# Generate tests
tapps-agents simple-mode test --file src/api/tasks.py
```

**Note:** Simple Mode uses YAML workflows under the hood (`workflows/presets/feature-implementation.yaml`)

## What You'll See

### Code Scoring Output

```
Overall Score: 45/100
├── Complexity: 6.0/10
├── Security: 2.0/10  ⚠️
├── Maintainability: 7.0/10
├── Test Coverage: 0.0/10  ⚠️
└── Performance: 7.0/10
```

### Code Review Output

- Detailed feedback on each issue
- Specific line numbers
- Severity levels
- Suggested fixes

### Quality Reports

- JSON format (machine-readable)
- Markdown format (human-readable)
- HTML format (visual dashboard)

## Understanding YAML Workflows

TappsCodingAgents uses **YAML files** as the single source of truth. All workflows are defined in `workflows/presets/*.yaml`:

**Example YAML Structure:**
```yaml
workflow:
  id: rapid-dev
  name: "Rapid Development"
  steps:
    - id: planning
      agent: planner
      action: create_stories
      requires: []
      creates:
        - stories/
    - id: implementation
      agent: implementer
      action: write_code
      requires:
        - stories/
      creates:
        - src/
```

**Available YAML Workflows:**
- `rapid-dev.yaml` - Fast feature development
- `quick-fix.yaml` - Bug fixes
- `quality.yaml` - Quality improvement
- `full-sdlc.yaml` - Complete SDLC pipeline
- `feature-implementation.yaml` - Feature-focused (used by Simple Mode)

**Using with Cursor:**
- Workflows execute via Cursor Skills (`@agent-name`)
- Framework reads YAML, Skills handle LLM operations
- All artifacts generated from YAML workflow state

## Next Steps

1. Read the full [Demo Plan](../docs/DEMO_PLAN.md)
2. Try [Simple Mode Guide](../docs/SIMPLE_MODE_GUIDE.md)
3. Explore [YAML Workflow Architecture](../docs/YAML_WORKFLOW_ARCHITECTURE_DESIGN.md)
4. Check out [Cursor Skills Integration](../docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md)
5. View [Workflow Presets](../docs/WORKFLOW_SELECTION_GUIDE.md)

## Troubleshooting

### Command Not Found

```bash
# Use module invocation instead
python -m tapps_agents.cli score src/calculator.py
```

### Doctor Shows Warnings

Warnings are okay - the framework still works. Install missing tools for full functionality:

```bash
pip install ruff mypy bandit jscpd pip-audit
```

### Need Help?

- Check [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)
- Review [Quick Start Guide](../docs/guides/QUICK_START.md)
- See [Demo Plan](../docs/DEMO_PLAN.md) for detailed scenarios

