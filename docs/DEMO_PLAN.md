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
- **Advanced Demo (30+ min)**: Multi-agent orchestration and workflow presets

**Key Features Demonstrated:**
- ✅ Code scoring with objective metrics
- ✅ Code generation and refactoring
- ✅ Test generation and execution
- ✅ Quality tools (linting, type checking)
- ✅ Workflow presets
- ✅ Simple Mode (new user friendly)
- ✅ Cursor Skills integration (if using Cursor IDE)

---

## Prerequisites

### Required

1. **Python 3.13+** installed
2. **TappsCodingAgents** installed:
   ```bash
   pip install -e .
   ```

3. **Basic project structure** (created during demo)

### Optional (for enhanced demo)

4. **Cursor IDE** (for Skills integration)
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

**Goal:** Complete workflow from requirements to tested code

### Scenario: Build a Task Management API

### Step 1: Setup

```bash
# Create demo project
mkdir task-api-demo
cd task-api-demo
tapps-agents init
```

### Step 2: Use Simple Mode (New User Friendly)

```bash
# Enable Simple Mode
tapps-agents simple-mode on

# Run onboarding wizard
tapps-agents simple-mode init
```

### Step 3: Build Feature (Natural Language)

```bash
# Build a REST API endpoint for tasks
tapps-agents simple-mode build -p "Create a REST API endpoint for managing tasks with CRUD operations"
```

**What happens:**
- Planner creates user stories
- Architect designs system
- Designer creates API contracts
- Implementer generates code

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

**Goal:** Showcase workflow presets and multi-agent orchestration

### Scenario 1: Rapid Development Workflow

```bash
# Create project
mkdir rapid-demo
cd rapid-demo
tapps-agents init

# Run rapid development workflow
tapps-agents workflow rapid --prompt "Add user authentication with JWT tokens"

# Monitor workflow execution
# Check generated artifacts:
# - stories/ (user stories)
# - src/ (generated code)
# - tests/ (generated tests)
```

### Scenario 2: Bug Fix Workflow

```bash
# Create project with buggy code
mkdir bugfix-demo
cd bugfix-demo
tapps-agents init

# Copy example bug file
cp ../examples/example_bug.py src/buggy.py

# Run quick-fix workflow
tapps-agents workflow fix --file src/buggy.py

# Review fixes
tapps-agents reviewer review src/buggy.py
```

### Scenario 3: Quality Improvement Workflow

```bash
# Create project
mkdir quality-demo
cd quality-demo
tapps-agents init

# Add some code
# ... (create code files)

# Run quality improvement workflow
tapps-agents workflow quality --file src/legacy_code.py

# Review improvements
tapps-agents reviewer report . json markdown html
```

### Scenario 4: Full SDLC Workflow

```bash
# Create project
mkdir sdlc-demo
cd sdlc-demo
tapps-agents init

# Run full SDLC workflow
tapps-agents workflow full --prompt "Build a microservice for order processing"

# This runs complete SDLC:
# - Requirements analysis
# - Planning
# - Architecture design
# - API design
# - Implementation
# - Testing
# - Documentation
# - Review
```

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

### Scenario D: Cursor IDE Integration

**Duration:** 10-15 minutes  
**Audience:** Cursor IDE users

**Prerequisites:** Cursor IDE installed

**Steps:**
1. Open Cursor IDE
2. Use `@reviewer` skill
3. Use `@implementer` skill
4. Use `@tester` skill
5. Show Simple Mode in Cursor

**Key Points:**
- Skills integration
- Natural language in IDE
- Context-aware assistance

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

