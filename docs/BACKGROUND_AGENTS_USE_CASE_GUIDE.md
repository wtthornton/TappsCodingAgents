# Background Agents - Use Case Guide

## Overview

This guide provides comprehensive guidance on when to use and when not to use Background Agents in TappsCodingAgents. It includes a decision framework, real-world examples, and best practices to help you make informed decisions.

**Related Documentation:**
- [Background Agents Evaluation](../docs/BACKGROUND_AGENTS_EVALUATION.md) - Complete evaluation and analysis
- [Migration Guide](../docs/BACKGROUND_AGENTS_MIGRATION_GUIDE.md) - Step-by-step migration instructions
- [Troubleshooting Guide](../docs/BACKGROUND_AGENTS_TROUBLESHOOTING.md) - Common issues and solutions

---

## Quick Decision Guide

### ✅ Use Background Agents When:

- **Task Duration:** > 30 seconds
- **Task Type:** Deterministic (no LLM required)
- **Execution Mode:** Non-blocking required
- **Isolation Needed:** Parallel execution or conflict prevention
- **Monitoring Required:** Progress tracking needed

### ❌ Don't Use Background Agents When:

- **Task Duration:** < 30 seconds
- **Task Type:** LLM-driven (code generation, refactoring)
- **Execution Mode:** Blocking is acceptable
- **Isolation Not Needed:** Single task, no conflicts
- **Simple Operation:** Single file or small scope

---

## Decision Framework

### Step 1: Assess Task Duration

**Question:** How long will this task take?

- **< 30 seconds:** Use direct execution
- **30 seconds - 2 minutes:** Consider direct execution (unless other factors apply)
- **> 2 minutes:** Background Agents may be appropriate

**Example:**
```bash
# ❌ Too short for Background Agents
tapps-agents reviewer review src/app.py  # < 10 seconds

# ✅ Appropriate for Background Agents
tapps-agents reviewer review src/ --pattern "**/*.py"  # 5-15 minutes
```

### Step 2: Determine Task Type

**Question:** Is this task deterministic or LLM-driven?

- **Deterministic:** Quality checks, security scans, tests, documentation generation
- **LLM-driven:** Code generation, refactoring, design decisions

**Example:**
```bash
# ✅ Deterministic - Good for Background Agents
tapps-agents ops security-scan src/
tapps-agents tester run-tests
tapps-agents reviewer analyze-project

# ❌ LLM-driven - Use direct Cursor chat instead
@implementer *implement "Add authentication" src/auth.py
@architect *design "Design microservice architecture"
```

### Step 3: Evaluate Execution Mode

**Question:** Do you need non-blocking execution?

- **Non-blocking required:** Continue working while task runs
- **Blocking acceptable:** Wait for results before continuing

**Example:**
```bash
# ✅ Non-blocking - Background Agents appropriate
# Run quality analysis while working on other features
tapps-agents workflow quality --prompt "Analyze project quality" --auto

# ❌ Blocking acceptable - Direct execution simpler
# Need results immediately before proceeding
tapps-agents reviewer score src/main.py
```

### Step 4: Check Isolation Requirements

**Question:** Do you need isolation or parallel execution?

- **Parallel execution:** Multiple tasks running simultaneously
- **Conflict prevention:** Prevent file conflicts between tasks
- **Single task:** No isolation needed

**Example:**
```bash
# ✅ Parallel execution - Background Agents needed
# Run security scan and quality analysis simultaneously
tapps-agents ops security-scan src/ --auto &
tapps-agents workflow quality --prompt "Analyze quality" --auto &

# ❌ Single task - Direct execution simpler
tapps-agents reviewer review src/app.py
```

### Step 5: Assess Monitoring Needs

**Question:** Do you need progress tracking?

- **Progress tracking needed:** Long-running tasks, batch operations
- **Progress not needed:** Quick tasks, immediate results

**Example:**
```bash
# ✅ Progress tracking - Background Agents appropriate
# Monitor progress of long-running analysis
tapps-agents workflow quality --prompt "Full codebase analysis" --auto
# Check progress: tapps-agents status

# ❌ Progress not needed - Direct execution simpler
tapps-agents reviewer lint src/app.py
```

---

## Real-World Use Cases

### ✅ Use Case 1: Full Codebase Quality Analysis

**Scenario:** Analyze code quality across entire codebase (500+ files)

**Why Background Agents:**
- ✅ Duration: 5-15 minutes (long-running)
- ✅ Deterministic: No LLM required
- ✅ Non-blocking: Can continue working
- ✅ Isolation: Prevents conflicts
- ✅ Monitoring: Progress tracking useful

**Command:**
```bash
tapps-agents workflow quality --prompt "Analyze project quality" --auto
```

**Result:**
- Task runs in background
- Progress tracked via unified state
- Results delivered when complete
- **Net Value: +1** (benefits outweigh complexity)

---

### ❌ Use Case 2: Single File Review

**Scenario:** Review single Python file (50 lines)

**Why NOT Background Agents:**
- ❌ Duration: < 10 seconds (too short)
- ❌ Overhead: Worktree creation takes longer than task
- ❌ Complexity: Not justified for simple operation

**Better Approach:**
```bash
# Direct execution
tapps-agents reviewer review src/app.py
```

**Result:**
- Immediate execution
- No worktree overhead
- No progress tracking needed
- **Net Value: -4** (complexity not justified)

---

### ❌ Use Case 3: LLM-Driven Code Generation

**Scenario:** Generate authentication code using LLM

**Why NOT Background Agents:**
- ❌ LLM-driven: Requires Cursor chat interaction
- ❌ File-based fallback: Fragile and unreliable
- ❌ Monitoring overhead: Not needed for interactive task

**Better Approach:**
```bash
# Direct Cursor chat
@implementer *implement "Generate JWT authentication" src/auth.py
```

**Result:**
- Direct execution in Cursor chat
- Interactive feedback
- No file-based coordination
- **Net Value: -3** (complexity outweighs benefits)

---

### ✅ Use Case 4: Batch Security Scan

**Scenario:** Security scan across 10 microservices

**Why Background Agents:**
- ✅ Duration: 3-10 minutes per service
- ✅ Parallel execution: Multiple services simultaneously
- ✅ Isolation: Worktrees prevent conflicts
- ✅ Progress tracking: Monitor all services

**Command:**
```bash
for service in services/*; do
  tapps-agents ops security-scan --target "$service" --auto
done
```

**Result:**
- Parallel execution of 10 services
- Isolated worktrees prevent conflicts
- Progress tracked for each service
- **Net Value: +1** (benefits justify complexity)

---

### ✅ Use Case 5: Test Suite Execution

**Scenario:** Run full test suite (200+ tests)

**Why Background Agents:**
- ✅ Duration: 2-8 minutes (long-running)
- ✅ Deterministic: No LLM required
- ✅ Non-blocking: Continue working
- ✅ Monitoring: Track test progress

**Command:**
```bash
tapps-agents tester run-tests --coverage
```

**Result:**
- Tests run in background
- Progress tracked
- Results available when complete
- **Net Value: +1** (benefits justify complexity)

---

### ❌ Use Case 6: Quick Lint Check

**Scenario:** Lint check on single file

**Why NOT Background Agents:**
- ❌ Duration: < 5 seconds (too short)
- ❌ Overhead: Not justified
- ❌ Simple operation: Direct execution better

**Better Approach:**
```bash
tapps-agents reviewer lint src/app.py
```

**Result:**
- Immediate results
- No overhead
- **Net Value: -4** (complexity not justified)

---

## Decision Tree

```
START: Need to execute a task
│
├─ Is task duration > 30 seconds?
│  ├─ NO → Use direct execution
│  └─ YES → Continue
│
├─ Is task deterministic (no LLM)?
│  ├─ NO → Use direct Cursor chat
│  └─ YES → Continue
│
├─ Is non-blocking execution required?
│  ├─ NO → Use direct execution
│  └─ YES → Continue
│
├─ Is parallel execution needed?
│  ├─ NO → Consider direct execution
│  └─ YES → Use Background Agents
│
└─ Use Background Agents ✅
```

---

## Best Practices

### 1. Start with Direct Execution

**Default to direct execution** unless you have a specific need for Background Agents.

```bash
# ✅ Default: Direct execution
tapps-agents reviewer review src/app.py

# Only use Background Agents when needed
tapps-agents workflow quality --prompt "Full analysis" --auto
```

### 2. Use Task Duration Detection

**Let the system decide** - Phase 1 improvements automatically route short tasks to direct execution.

```bash
# System automatically detects duration
# Short tasks (< 30s) → Direct execution
# Long tasks (> 30s) → Background Agents
tapps-agents reviewer review src/
```

### 3. Monitor Progress

**Use unified status command** to monitor Background Agent tasks.

```bash
# Check status of all Background Agents
tapps-agents status

# Detailed status
tapps-agents status --detailed

# Worktrees only
tapps-agents status --worktrees-only
```

### 4. Clean Up Automatically

**Auto-cleanup system** (Phase 1) automatically removes old worktrees.

```bash
# Manual cleanup if needed
tapps-agents status --worktrees-only
# Old worktrees are automatically cleaned up
```

### 5. Use Health Checks

**Check API availability** before using Background Agents (Phase 2).

```python
from tapps_agents.workflow.background_agent_api import BackgroundAgentAPI

api = BackgroundAgentAPI()
health = api.health_check()

if health["available"]:
    # Use Background Agents
else:
    # Use direct execution fallback
```

---

## Common Mistakes

### ❌ Mistake 1: Using Background Agents for Short Tasks

**Problem:** Using Background Agents for tasks < 30 seconds

**Example:**
```bash
# ❌ Wrong
tapps-agents workflow quality --prompt "Review src/app.py" --auto
```

**Solution:**
```bash
# ✅ Correct
tapps-agents reviewer review src/app.py
```

### ❌ Mistake 2: Using Background Agents for LLM Tasks

**Problem:** Using Background Agents for LLM-driven code generation

**Example:**
```bash
# ❌ Wrong
tapps-agents workflow rapid --prompt "Generate auth code" --auto
```

**Solution:**
```bash
# ✅ Correct
@implementer *implement "Generate auth code" src/auth.py
```

### ❌ Mistake 3: Not Monitoring Progress

**Problem:** Starting Background Agent tasks without monitoring

**Example:**
```bash
# ❌ Wrong
tapps-agents workflow quality --prompt "Analysis" --auto
# No way to check progress
```

**Solution:**
```bash
# ✅ Correct
tapps-agents workflow quality --prompt "Analysis" --auto
# Monitor progress
tapps-agents status
```

---

## Summary

**Key Takeaways:**

1. **Use Background Agents for:**
   - Long-running deterministic tasks (> 30s)
   - Non-blocking execution needs
   - Parallel execution requirements
   - Progress tracking needs

2. **Use Direct Execution for:**
   - Short tasks (< 30s)
   - LLM-driven workflows
   - Simple operations
   - Immediate results needed

3. **Let the System Decide:**
   - Task duration detection (Phase 1) automatically routes tasks
   - Health checks (Phase 2) ensure API availability
   - Direct execution fallback (Phase 2) handles API unavailability

**Related Documentation:**
- [Background Agents Evaluation](../docs/BACKGROUND_AGENTS_EVALUATION.md)
- [Migration Guide](../docs/BACKGROUND_AGENTS_MIGRATION_GUIDE.md)
- [Troubleshooting Guide](../docs/BACKGROUND_AGENTS_TROUBLESHOOTING.md)

