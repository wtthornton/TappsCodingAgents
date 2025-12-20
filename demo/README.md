# TappsCodingAgents Demo

Quick-start demo materials for TappsCodingAgents.

## Quick Start

Run the demo script:

```bash
# From project root
python demo/run_demo.py

# Or make it executable and run directly
chmod +x demo/run_demo.py
./demo/run_demo.py
```

## Demo Files

- `run_demo.py` - Interactive demo script
- `sample_code/` - Sample code files for demonstration
- `demo_scenarios/` - Pre-configured demo scenarios

## Manual Demo Steps

See [docs/DEMO_PLAN.md](../docs/DEMO_PLAN.md) for complete demo instructions.

## Demo Scenarios

### 1. Code Review Demo (5 min)
```bash
cd demo/sample_code
tapps-agents reviewer review calculator.py
tapps-agents reviewer score calculator.py
```

### 2. Code Generation Demo (10 min)
```bash
mkdir my-demo-project
cd my-demo-project
tapps-agents init
tapps-agents simple-mode build -p "Create a REST API for tasks"
```

### 3. Workflow Demo (15 min)
```bash
mkdir workflow-demo
cd workflow-demo
tapps-agents init
tapps-agents workflow rapid --prompt "Add user authentication"
```

