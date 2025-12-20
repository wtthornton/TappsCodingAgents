# TappsCodingAgents Demo Plan

**Version:** 1.0  
**Date:** January 2026  
**Purpose:** Provide a comprehensive, step-by-step demo plan for new users to see TappsCodingAgents in action

---

## Table of Contents

1. [Demo Overview](#demo-overview)
2. [Prerequisites](#prerequisites)
3. [Quick Demo (5 minutes)](#quick-demo-5-minutes)
4. [Full Demo (15-20 minutes)](#full-demo-15-20-minutes)
5. [Advanced Demo (30+ minutes)](#advanced-demo-30-minutes)
6. [Demo Scenarios](#demo-scenarios)
7. [Expected Outcomes](#expected-outcomes)
8. [Troubleshooting](#troubleshooting)
9. [Next Steps](#next-steps)

---

## Demo Overview

This demo plan provides multiple paths for showcasing TappsCodingAgents:

- **Quick Demo (5 min)**: Fast code review and scoring
- **Full Demo (15-20 min)**: Complete workflow from code generation to testing
- **Advanced Demo (30+ min)**: YAML workflow presets and multi-agent orchestration with Cursor

**Key Features Demonstrated:**
- ✅ **YAML Workflows**: Single source of truth for all workflows
- ✅ **Cursor Skills Integration**: Native Cursor IDE integration with 13 specialized agents
- ✅ Code scoring with objective metrics
- ✅ Code generation and refactoring
- ✅ Test generation and execution
- ✅ Quality tools (linting, type checking)
- ✅ **YAML Workflow Presets**: Pre-defined workflows in `workflows/presets/*.yaml`
- ✅ Simple Mode (new user friendly)
- ✅ **Auto-generated Artifacts**: Task manifests, docs, and configs generated from YAML

---

## Prerequisites

### Required

1. **Python 3.13+** installed
2. **TappsCodingAgents** installed:
   ```bash
   pip install -e .
   ```

3. **Basic project structure** (created during demo)

### Recommended (for full YAML + Cursor experience)

4. **Cursor IDE** (for Skills integration - **highly recommended**)
   - Enables native Cursor Skills (`@reviewer`, `@implementer`, etc.)
   - YAML workflows execute via Cursor Skills
   - Better context awareness and model selection

### Optional (for enhanced demo)

5. **Context7 API Key** (for library documentation caching)
6. **Git** (for workflow demonstrations)

### Verify Installation

```bash
# Check CLI is available
tapps-agents --help

# Verify installation
tapps-agents doctor
```

---

## Quick Demo (5 minutes)

**Goal:** Show code scoring and review capabilities

### Step 1: Create Demo Project

```bash
# Create demo directory
mkdir tapps-demo
cd tapps-demo

# Initialize project
tapps-agents init
```

### Step 2: Create Sample Code File

Create `calculator.py`:

```python
"""Simple calculator with intentional issues for demo."""

def add(a, b):
    """Add two numbers."""
    return a + b

def divide(a, b):
    """Divide two numbers."""
    return a / b  # Bug: No zero check

def calculate_total(items):
    """Calculate total price."""
    total = 0
    for item in items:
        total += item["price"]  # Bug: No error handling
    return total

def process_data(data):
    """Process user data."""
    # Security issue: No input validation
    result = eval(data)  # Dangerous!
    return result
```

### Step 3: Run Code Review

```bash
# Quick score (fast, no LLM feedback)
tapps-agents score calculator.py

# Full review (with detailed feedback)
tapps-agents reviewer review calculator.py

# Generate quality report
tapps-agents reviewer report . json markdown html
```

### Step 4: View Results

- **Score output**: Shows 5 metrics (complexity, security, maintainability, test coverage, performance)
- **Review output**: Detailed feedback with specific issues
- **Report files**: Generated in project root (JSON, Markdown, HTML)

**Expected Output:**
- Security score will be low (due to `eval()`)
- Test coverage will be 0 (no tests)
- Overall score will reflect issues

---

## Full Demo (15-20 minutes)

**Goal:** Complete workflow from requirements to tested code using YAML workflows and Cursor Skills

### Understanding YAML Workflows

Before starting, understand that TappsCodingAgents uses **YAML files** as the single source of truth:

**Workflow Location:** `workflows/presets/*.yaml`

**Example YAML Structure** (`workflows/presets/rapid-dev.yaml`):
```yaml
workflow:
  id: rapid-dev
  name: "Rapid Development"
  steps:
    - id: planning
      agent: planner          # Uses @planner Cursor Skill
      action: create_stories
      requires: []
      creates:
        - stories/
      next: implementation
      
    - id: implementation
      agent: implementer      # Uses @implementer Cursor Skill
      action: write_code
      requires:
        - stories/
      creates:
        - src/
      next: review
```

**Key Points:**
- ✅ Each `agent` field maps to a Cursor Skill (`@planner`, `@implementer`, `@reviewer`, etc.)
- ✅ `requires` defines dependencies (enables parallel execution)
- ✅ `creates` lists generated artifacts
- ✅ Framework executes YAML, Cursor Skills handle LLM operations

### Scenario: Build a Task Management API

### Step 1: Setup

```bash
# Create demo project
mkdir task-api-demo
cd task-api-demo
tapps-agents init

# View available YAML workflows
ls workflows/presets/
cat workflows/presets/rapid-dev.yaml
```

### Step 2: Use Simple Mode (New User Friendly)

```bash
# Enable Simple Mode
tapps-agents simple-mode on

# Run onboarding wizard
tapps-agents simple-mode init
```

### Step 3: Build Feature (Natural Language via YAML Workflow)

**Option A: Using Simple Mode (uses YAML workflow under the hood)**

```bash
# Build a REST API endpoint for tasks
tapps-agents simple-mode build -p "Create a REST API endpoint for managing tasks with CRUD operations"
```

**Option B: Using YAML Workflow Directly with Cursor Skills**

```bash
# Run rapid-dev YAML workflow with Cursor Skills
tapps-agents workflow rapid --prompt "Create a REST API endpoint for managing tasks with CRUD operations" --cursor-mode

# Or in Cursor IDE chat:
# @orchestrator *workflow rapid --prompt "Create a REST API endpoint for managing tasks with CRUD operations"
```

**What happens (YAML workflow execution):**
1. Framework reads `workflows/presets/rapid-dev.yaml` (or `feature-implementation.yaml` for Simple Mode)
2. Executes steps using Cursor Skills:
   - `@planner` creates user stories
   - `@architect` designs system (if in workflow)
   - `@designer` creates API contracts (if in workflow)
   - `@implementer` generates code
3. Generates artifacts: `stories/`, `src/`, `tests/`
4. Creates task manifest from YAML workflow state

### Step 4: Review Generated Code

```bash
# Review the generated code
tapps-agents simple-mode review --file src/api/tasks.py

# Or use reviewer directly
tapps-agents reviewer review src/api/tasks.py
```

### Step 5: Generate Tests

```bash
# Generate tests for the API
tapps-agents simple-mode test --file src/api/tasks.py

# Or use tester directly
tapps-agents tester test src/api/tasks.py
```

### Step 6: Run Tests

```bash
# Run the generated tests
tapps-agents tester run-tests
```

### Step 7: Quality Check

```bash
# Run linting
tapps-agents reviewer lint src/

# Run type checking
tapps-agents reviewer type-check src/

# Generate comprehensive report
tapps-agents reviewer report . json markdown html
```

### Step 8: View Results

Check generated files:
- `src/api/tasks.py` - Generated API code
- `tests/test_tasks.py` - Generated tests
- `reports/` - Quality reports (JSON, Markdown, HTML)

---

## Advanced Demo (30+ minutes)

**Goal:** Showcase YAML workflow presets and multi-agent orchestration with Cursor

### Understanding YAML Workflows

TappsCodingAgents uses **YAML files** as the single source of truth for workflows. All workflows are defined in `workflows/presets/*.yaml` files.

**Example YAML Workflow Structure** (`workflows/presets/rapid-dev.yaml`):

```yaml
workflow:
  id: rapid-dev
  name: "Rapid Development"
  description: "Fast feature development with quality checks"
  
  steps:
    - id: planning
      agent: planner
      action: create_stories
      requires: []
      creates:
        - stories/
      next: implementation
      
    - id: implementation
      agent: implementer
      action: write_code
      requires:
        - stories/
      creates:
        - src/
      next: review
      
    - id: review
      agent: reviewer
      action: review_code
      requires:
        - src/
      scoring:
        enabled: true
        thresholds:
          overall_min: 65
```

**Key Points:**
- ✅ **YAML-first**: All workflows are defined in YAML files
- ✅ **Cursor Skills**: Each step uses Cursor Skills (`@planner`, `@implementer`, `@reviewer`)
- ✅ **Dependency-based**: Steps run in parallel when dependencies are met
- ✅ **Auto-generated**: Task manifests, docs, and configs are generated from YAML

### Scenario 1: Rapid Development Workflow (YAML + Cursor)

**Option A: Using Cursor Skills (Recommended)**

```bash
# 1. Ensure Cursor IDE is open
# 2. Initialize project
mkdir rapid-demo
cd rapid-demo
tapps-agents init

# 3. View the YAML workflow file
cat workflows/presets/rapid-dev.yaml

# 4. Run workflow using Cursor Skills (via CLI)
tapps-agents workflow rapid --prompt "Add user authentication with JWT tokens" --cursor-mode

# Or use Cursor Skills directly in Cursor chat:
# @orchestrator *workflow rapid --prompt "Add user authentication with JWT tokens"
```

**Option B: Headless Mode (CLI only)**

```bash
# Run workflow in headless mode (no Cursor)
tapps-agents workflow rapid --prompt "Add user authentication with JWT tokens"
```

**What happens:**
1. Framework reads `workflows/presets/rapid-dev.yaml`
2. Executes steps using Cursor Skills (if `--cursor-mode` or in Cursor IDE)
3. Generates artifacts: `stories/`, `src/`, `tests/`
4. Creates task manifest from YAML workflow state

**Check generated artifacts:**
- `stories/` - User stories (from planner agent)
- `src/` - Generated code (from implementer agent)
- `tests/` - Generated tests (from tester agent)
- `.tapps-agents/workflow-state/` - Workflow execution state

### Scenario 2: Bug Fix Workflow (YAML + Cursor)

```bash
# Create project with buggy code
mkdir bugfix-demo
cd bugfix-demo
tapps-agents init

# Copy example bug file
cp ../examples/example_bug.py src/buggy.py

# View the YAML workflow file
cat workflows/presets/quick-fix.yaml

# Run quick-fix workflow with Cursor Skills
tapps-agents workflow fix --file src/buggy.py --cursor-mode

# Or in Cursor chat:
# @orchestrator *workflow fix --file src/buggy.py

# Review fixes
tapps-agents reviewer review src/buggy.py
```

**YAML Workflow File:** `workflows/presets/quick-fix.yaml`

### Scenario 3: Quality Improvement Workflow (YAML + Cursor)

```bash
# Create project
mkdir quality-demo
cd quality-demo
tapps-agents init

# Add some code
# ... (create code files)

# View the YAML workflow file
cat workflows/presets/quality.yaml

# Run quality improvement workflow with Cursor Skills
tapps-agents workflow quality --file src/legacy_code.py --cursor-mode

# Or in Cursor chat:
# @orchestrator *workflow quality --file src/legacy_code.py

# Review improvements
tapps-agents reviewer report . json markdown html
```

**YAML Workflow File:** `workflows/presets/quality.yaml`

### Scenario 4: Full SDLC Workflow (YAML + Cursor)

```bash
# Create project
mkdir sdlc-demo
cd sdlc-demo
tapps-agents init

# View the comprehensive YAML workflow file
cat workflows/presets/full-sdlc.yaml

# Run full SDLC workflow with Cursor Skills
tapps-agents workflow full --prompt "Build a microservice for order processing" --cursor-mode

# Or in Cursor chat:
# @orchestrator *workflow full --prompt "Build a microservice for order processing"

# This runs complete SDLC (defined in YAML):
# - Requirements analysis (analyst agent)
# - Planning (planner agent)
# - Architecture design (architect agent)
# - API design (designer agent)
# - Implementation (implementer agent)
# - Testing (tester agent)
# - Security scan (ops agent)
# - Documentation (documenter agent)
# - Review (reviewer agent)
```

**YAML Workflow File:** `workflows/presets/full-sdlc.yaml`

**Available YAML Workflow Presets:**
- `rapid-dev.yaml` - Fast feature development
- `quick-fix.yaml` - Bug fixes and hotfixes
- `quality.yaml` - Code quality improvement
- `maintenance.yaml` - Refactoring and maintenance
- `full-sdlc.yaml` - Complete SDLC pipeline
- `feature-implementation.yaml` - Feature-focused development

---

## Demo Scenarios

### Scenario A: Code Review Focus

**Duration:** 5-10 minutes  
**Audience:** Developers interested in code quality

**Steps:**
1. Create sample code with known issues
2. Run code scoring
3. Run full review
4. Show quality reports
5. Demonstrate quality tools (lint, type-check)

**Key Points:**
- Objective metrics vs subjective opinions
- 5 quality dimensions
- Actionable feedback

### Scenario B: Code Generation Focus

**Duration:** 10-15 minutes  
**Audience:** Developers wanting to accelerate development

**Steps:**
1. Use Simple Mode to build feature
2. Show natural language → code transformation
3. Review generated code
4. Generate tests
5. Run tests

**Key Points:**
- Natural language commands
- Multi-agent orchestration
- Quality gates

### Scenario C: Workflow Automation Focus

**Duration:** 15-20 minutes  
**Audience:** Teams wanting SDLC automation

**Steps:**
1. Run rapid development workflow
2. Show workflow steps execution
3. Demonstrate quality gates
4. Show artifact generation
5. Review workflow state

**Key Points:**
- Preset workflows
- Quality gates
- Artifact tracking
- State persistence

### Scenario D: Cursor IDE Integration with YAML Workflows

**Duration:** 10-15 minutes  
**Audience:** Cursor IDE users

**Prerequisites:** Cursor IDE installed

**Steps:**
1. **Open Cursor IDE** and navigate to your project
2. **View YAML Workflows:**
   ```bash
   # List available workflows
   cat workflows/presets/*.yaml
   ```
3. **Use Cursor Skills directly:**
   - `@reviewer *review {file}` - Code review
   - `@implementer *implement "description" {file}` - Code generation
   - `@tester *test {file}` - Test generation
4. **Run YAML Workflows via Cursor Skills:**
   ```
   @orchestrator *workflow rapid --prompt "Add feature X"
   @orchestrator *workflow full --prompt "Build microservice Y"
   ```
5. **Show Simple Mode in Cursor:**
   ```
   @simple-mode Build a REST API endpoint
   ```

**Key Points:**
- ✅ **YAML workflows** are the single source of truth
- ✅ **Cursor Skills** execute workflow steps using your configured model
- ✅ **Natural language** commands in Cursor chat
- ✅ **Context-aware** assistance with full project context
- ✅ **Auto-generated** artifacts from YAML (task manifests, docs, configs)

**YAML Workflow Integration:**
- Workflows defined in `workflows/presets/*.yaml`
- Each step uses Cursor Skills (`@agent-name`)
- Framework executes YAML workflow, Skills handle LLM operations
- All artifacts generated from YAML workflow state

---

## Expected Outcomes

### Quick Demo Outcomes

- ✅ Code scoring output with 5 metrics
- ✅ Quality report files (JSON, Markdown, HTML)
- ✅ Understanding of objective quality metrics

### Full Demo Outcomes

- ✅ Complete project structure
- ✅ Generated code files
- ✅ Generated test files
- ✅ Quality reports
- ✅ Understanding of workflow automation

### Advanced Demo Outcomes

- ✅ Multiple workflow executions
- ✅ Quality gate enforcement
- ✅ Artifact generation
- ✅ State persistence
- ✅ Understanding of SDLC automation

---

## Troubleshooting

### Issue: CLI Command Not Found

**Solution:**
```bash
# Verify installation
pip install -e .

# Check PATH
which tapps-agents  # Linux/Mac
where tapps-agents  # Windows

# Use module invocation
python -m tapps_agents.cli --help
```

### Issue: Doctor Command Shows Warnings

**Solution:**
- Warnings are soft-degradations (framework still works)
- Install missing tools for full functionality:
  ```bash
  pip install ruff mypy bandit jscpd pip-audit
  ```

### Issue: Simple Mode Not Working

**Solution:**
```bash
# Check status
tapps-agents simple-mode status

# Enable if needed
tapps-agents simple-mode on

# Verify config
cat .tapps-agents/config.yaml
```

### Issue: Workflow Not Executing

**Solution:**
```bash
# Check workflow file exists
ls workflows/presets/

# Verify project initialization
tapps-agents init

# Check workflow syntax
tapps-agents workflow list
```

### Issue: Code Generation Not Working

**Solution:**
- Ensure Cursor IDE is open (for Skills)
- Check LLM model is configured in Cursor
- Verify project structure exists
- Check error messages in output

---

## Next Steps

After completing the demo:

### 1. Explore Documentation

- [Quick Start Guide](guides/QUICK_START.md)
- [Simple Mode Guide](SIMPLE_MODE_GUIDE.md)
- [Cursor Skills Installation Guide](CURSOR_SKILLS_INSTALLATION_GUIDE.md)
- [Workflow Selection Guide](WORKFLOW_SELECTION_GUIDE.md)

### 2. Try Real Project

```bash
# Initialize your own project
cd your-project
tapps-agents init

# Start using agents
tapps-agents reviewer review src/
tapps-agents implementer implement "Add feature X" src/feature.py
```

### 3. Configure Experts (Optional)

```bash
# Setup industry experts
tapps-agents setup-experts init
tapps-agents setup-experts add
```

### 4. Explore Workflows

```bash
# List available workflows
tapps-agents workflow list

# Get workflow recommendation
tapps-agents workflow recommend

# Run specific workflow
tapps-agents workflow rapid --prompt "Your feature description"
```

### 5. Enable Cursor Integration

If using Cursor IDE:

1. Skills are already installed (via `tapps-agents init`)
2. Use `@reviewer`, `@implementer`, `@tester` in Cursor chat
3. Try Simple Mode: `@simple-mode Build a feature`

---

## Demo Checklist

### Before Demo

- [ ] TappsCodingAgents installed
- [ ] Python 3.13+ verified
- [ ] CLI working (`tapps-agents --help`)
- [ ] Doctor command run (check warnings)
- [ ] Demo directory created
- [ ] Sample code files prepared (optional)

### During Demo

- [ ] Show code scoring
- [ ] Show code review
- [ ] Show code generation (if time)
- [ ] Show test generation (if time)
- [ ] Show workflow execution (if time)
- [ ] Show quality reports
- [ ] Answer questions

### After Demo

- [ ] Share documentation links
- [ ] Provide next steps
- [ ] Collect feedback
- [ ] Offer support resources

---

## Demo Script Template

### Introduction (1 min)

"TappsCodingAgents is a framework for AI coding agents with 13 specialized agents for different SDLC tasks. Today we'll see it in action."

### Quick Demo (5 min)

1. "Let's start with code scoring - objective quality metrics"
2. Run `tapps-agents score calculator.py`
3. "Now let's see a full review with detailed feedback"
4. Run `tapps-agents reviewer review calculator.py`
5. "Notice the 5 metrics: complexity, security, maintainability, test coverage, performance"

### Full Demo (10 min)

1. "Now let's build a complete feature using Simple Mode"
2. Run `tapps-agents simple-mode build -p "Create REST API..."`
3. "The framework orchestrated multiple agents: Planner → Architect → Implementer"
4. "Let's review the generated code"
5. "And generate tests"
6. "Finally, run quality checks"

### Wrap-up (2 min)

1. "Key takeaways:"
   - Objective quality metrics
   - Natural language commands
   - Multi-agent orchestration
   - Quality gates
2. "Next steps: Try it on your own project"
3. "Documentation and support resources"

---

## Additional Resources

- **GitHub Repository**: [Link to repo]
- **Documentation**: `docs/` directory
- **Examples**: `examples/` directory
- **Workflows**: `workflows/presets/` directory
- **Support**: [Link to support channels]

---

## Version History

- **v1.0** (January 2026): Initial demo plan

---

**Last Updated:** January 2026  
**Maintained By:** TappsCodingAgents Team

