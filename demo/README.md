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
- `demo_prompt_enhancement.py` - Prompt enhancement feature demo
- `sample_code/` - Sample code files for demonstration
- `demo_scenarios/` - Pre-configured demo scenarios

## Manual Demo Steps

See [docs/DEMO_PLAN.md](../docs/DEMO_PLAN.md) for complete demo instructions.

## Prompt Enhancement Demo

Showcase the prompt enhancement feature:

```bash
# Run the prompt enhancement demo
python demo/demo_prompt_enhancement.py

# Or with a custom prompt
python demo/demo_prompt_enhancement.py "Create a payment processing system"
```

This demo:
- Shows the original simple prompt
- Demonstrates the 7-stage enhancement pipeline
- Prints the complete enhanced prompt (without actually running enhancement)
- Explains each stage and its contribution
- Shows before/after comparison
- Provides usage instructions

**Note:** This demo prints a simulated enhanced prompt to show what the enhancement would produce. To actually run enhancement, use:
```bash
python -m tapps_agents.cli enhancer enhance "Your prompt here"
```

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

