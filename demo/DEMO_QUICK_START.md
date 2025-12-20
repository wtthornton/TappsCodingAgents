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

## Option 3: Simple Mode Demo

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

## Next Steps

1. Read the full [Demo Plan](../docs/DEMO_PLAN.md)
2. Try [Simple Mode Guide](../docs/SIMPLE_MODE_GUIDE.md)
3. Explore [Workflow Presets](../docs/WORKFLOW_SELECTION_GUIDE.md)
4. Check out [Cursor Skills Integration](../docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md)

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

