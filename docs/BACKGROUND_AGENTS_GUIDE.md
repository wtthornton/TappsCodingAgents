# Background Agents Integration Guide

**TappsCodingAgents + Cursor AI Background Agents**

This guide explains how to use TappsCodingAgents with Cursor AI Background Agents for handling heavy tasks autonomously.

---

## Overview

Background Agents in Cursor AI allow you to run long-running tasks that complete autonomously without blocking your workflow. TappsCodingAgents provides:

- ✅ **6 Pre-configured Background Agents** for common heavy tasks
- ✅ **Git Worktree Integration** to prevent file conflicts
- ✅ **Progress Reporting** for long-running tasks
- ✅ **Context7 Cache Sharing** between Sidebar Skills and Background Agents
- ✅ **Result Delivery** via files, PRs, or web app

---

## Prerequisites

1. **Cursor AI IDE** with Background Agents support
2. **TappsCodingAgents** installed (see [QUICK_START.md](../QUICK_START.md))
3. **Git repository** initialized (for worktree support)

---

## Configuration

### 1. Background Agent Configuration File

The configuration file is located at `.cursor/background-agents.yaml`. It defines:

- Agent names and descriptions
- Commands to execute
- Triggers (natural language prompts)
- Output locations
- Context7 cache paths

**Example Configuration:**

```yaml
agents:
  - name: "TappsCodingAgents Quality Analyzer"
    type: "background"
    description: "Analyze project quality, generate reports"
    commands:
      - "python -m tapps_agents.cli reviewer analyze-project --format json"
    context7_cache: ".tapps-agents/kb/context7-cache"
    triggers:
      - "Analyze project quality"
      - "Generate quality report"
```

### 2. Available Background Agents

#### Quality Analyzer
- **Purpose**: Full project quality analysis
- **Triggers**: "Analyze project quality", "Generate quality report"
- **Output**: Quality analysis reports in `.tapps-agents/reports/`

#### Refactoring Agent
- **Purpose**: Code refactoring and modernization
- **Triggers**: "Refactor {service}", "Improve code quality in {directory}"
- **Output**: Refactored code and reports

#### Testing Agent
- **Purpose**: Test generation and execution
- **Triggers**: "Generate tests for {file}", "Run tests for {service}"
- **Output**: Test files and coverage reports

#### Documentation Agent
- **Purpose**: API documentation and README generation
- **Triggers**: "Generate API documentation", "Create README for {directory}"
- **Output**: Documentation files

#### Security Agent
- **Purpose**: Security scanning and compliance checks
- **Triggers**: "Run security scan", "Check compliance"
- **Output**: Security and compliance reports

#### Multi-Service Analyzer
- **Purpose**: Parallel analysis of multiple services
- **Triggers**: "Analyze all services", "Review multiple services"
- **Output**: Cross-service analysis reports

---

## Usage

### Triggering Background Agents

Background Agents are triggered via natural language prompts in Cursor AI:

```
# Quality Analysis
"Analyze project quality"
"Generate quality report for all services"

# Refactoring
"Refactor the auth service"
"Improve code quality in src/api/"

# Testing
"Generate tests for src/models/user.py"
"Run tests for the payment service"

# Documentation
"Generate API documentation for src/api/"
"Create README for the auth service"

# Security
"Run security scan"
"Check GDPR compliance"
```

### Monitoring Progress

Progress is reported in real-time:

1. **Progress Files**: Located in `.tapps-agents/reports/progress-{task-id}.json`
2. **Cursor UI**: Background Agents panel shows progress
3. **Logs**: Check Cursor's Background Agents logs

**Progress File Format:**

```json
{
  "task_id": "quality-analysis-2025-12-10",
  "start_time": "2025-12-10T10:00:00Z",
  "current_time": "2025-12-10T10:05:00Z",
  "elapsed_seconds": 300,
  "status": "in_progress",
  "steps": [
    {
      "step": "setup",
      "status": "completed",
      "timestamp": "2025-12-10T10:00:05Z",
      "elapsed_seconds": 5
    },
    {
      "step": "command_start",
      "status": "in_progress",
      "message": "Running reviewer analyze-project",
      "timestamp": "2025-12-10T10:00:10Z",
      "elapsed_seconds": 10
    }
  ]
}
```

### Viewing Results

Results are delivered in multiple formats:

1. **JSON Files**: `.tapps-agents/reports/{task-id}-{agent}-{command}.json`
2. **Pull Requests**: Automatically created for code changes
3. **Web App**: If configured, results available via web interface

**Example Result File:**

```json
{
  "success": true,
  "result": {
    "scores": {
      "complexity": 7.2,
      "security": 8.5,
      "maintainability": 7.8,
      "test_coverage": 85,
      "performance": 7.0,
      "overall": 76.5
    },
    "issues": [...],
    "recommendations": [...]
  },
  "result_file": ".tapps-agents/reports/quality-analysis-reviewer-analyze-project.json"
}
```

---

## Git Worktree Integration

Background Agents use git worktrees to prevent file conflicts when multiple agents run in parallel.

### How It Works

1. **Worktree Creation**: Each agent gets its own worktree
2. **Isolated Execution**: Agent runs in isolated worktree
3. **Result Merging**: Results merged back to main branch
4. **Cleanup**: Worktree removed after completion

### Worktree Locations

- **Base Directory**: `.tapps-agents/worktrees/`
- **Per Agent**: `.tapps-agents/worktrees/{agent-id}/`
- **Branch Names**: `agent/{agent-id}`

### Manual Worktree Management

```bash
# List active worktrees
git worktree list

# Remove a worktree
git worktree remove .tapps-agents/worktrees/{agent-id}

# Cleanup all agent worktrees
python -m tapps_agents.core.worktree cleanup
```

---

## Context7 Cache Sharing

Context7 KB cache is shared between Sidebar Skills and Background Agents:

- **Cache Location**: `.tapps-agents/kb/context7-cache`
- **Auto-Sync**: Cache synced on agent startup
- **Shared Access**: Both Skills and Background Agents use same cache
- **90%+ Hit Rate**: Pre-populated cache ensures high hit rate

### Pre-populating Cache

```bash
# Pre-populate cache with common libraries
python scripts/prepopulate_context7_cache.py

# Pre-populate from requirements.txt
python scripts/prepopulate_context7_cache.py --requirements requirements.txt
```

---

## Result Delivery

### File Delivery (Default)

Results are saved to `.tapps-agents/reports/`:

- JSON format for structured data
- Markdown/HTML for reports
- Progress files for monitoring

### Pull Request Delivery

For code changes, Background Agents can create PRs:

1. **Automatic PR Creation**: Enabled in configuration
2. **Branch**: `agent/{agent-id}`
3. **Title**: Based on task description
4. **Description**: Includes progress and results

### Web App Delivery

If web app is configured, results available via:

- **URL**: `http://localhost:8000/reports/{task-id}`
- **Dashboard**: View all background agent results
- **Real-time Updates**: Progress updates via WebSocket

---

## Best Practices

### 1. Task Granularity

Break large tasks into smaller, focused tasks:

```
# Good
"Analyze code quality in src/api/auth/"
"Refactor the UserService class"

# Avoid
"Analyze and refactor the entire project"
```

### 2. Resource Management

- **Parallel Agents**: Limit to 4-8 concurrent agents
- **Worktree Cleanup**: Regularly clean up unused worktrees
- **Cache Management**: Pre-populate cache for common libraries

### 3. Monitoring

- **Progress Files**: Check progress files for long-running tasks
- **Logs**: Monitor Cursor's Background Agents logs
- **Results**: Review results before merging PRs

### 4. Error Handling

- **Retry Logic**: Failed tasks can be retried
- **Error Reports**: Check error reports in `.tapps-agents/reports/`
- **Logs**: Review logs for detailed error information

---

## Troubleshooting

### Background Agent Not Triggering

1. **Check Configuration**: Verify `.cursor/background-agents.yaml` exists
2. **Check Triggers**: Ensure trigger phrase matches configuration
3. **Check Cursor Version**: Ensure Background Agents support is enabled

### Worktree Conflicts

1. **Cleanup Worktrees**: Remove unused worktrees
2. **Check Branches**: Ensure no conflicting branches
3. **Manual Cleanup**: Use `git worktree remove` manually

### Progress Not Updating

1. **Check Permissions**: Ensure write permissions to `.tapps-agents/reports/`
2. **Check Logs**: Review Cursor's Background Agents logs
3. **Manual Check**: Check progress files directly

### Context7 Cache Issues

1. **Cache Location**: Verify cache location in configuration
2. **Pre-population**: Run pre-population script
3. **Permissions**: Ensure read/write permissions to cache directory

---

## Advanced Configuration

### Custom Background Agents

Create custom Background Agents in `.cursor/background-agents.yaml`:

```yaml
agents:
  - name: "Custom Agent"
    type: "background"
    commands:
      - "python -m tapps_agents.cli {agent} {command} {args}"
    triggers:
      - "Custom trigger phrase"
```

### Environment Variables

Set environment variables for Background Agents:

```yaml
environment:
  - "CONTEXT7_KB_CACHE=.tapps-agents/kb/context7-cache"
  - "TAPPS_AGENTS_MODE=background"
  - "TAPPS_AGENTS_PARALLEL=true"
```

### Output Customization

Customize output format and location:

```yaml
output:
  format: "json"
  location: ".tapps-agents/reports"
  delivery: ["file", "pr", "web"]
```

---

## Examples

### Example 1: Quality Analysis

**Trigger:**
```
"Analyze project quality"
```

**Result:**
- Quality analysis report in `.tapps-agents/reports/`
- JSON file with scores and recommendations
- Progress file for monitoring

### Example 2: Refactoring

**Trigger:**
```
"Refactor the auth service to use dependency injection"
```

**Result:**
- Refactored code in worktree
- Pull request with changes
- Refactoring report

### Example 3: Test Generation

**Trigger:**
```
"Generate tests for src/models/user.py"
```

**Result:**
- Test files generated
- Coverage report
- Test execution results

---

## See Also

- [CURSOR_SKILLS_INSTALLATION_GUIDE.md](CURSOR_SKILLS_INSTALLATION_GUIDE.md) - Skills setup
- [CURSOR_AI_INTEGRATION_PLAN_2025.md](CURSOR_AI_INTEGRATION_PLAN_2025.md) - Full integration plan
- [QUICK_START.md](../QUICK_START.md) - Quick start guide

