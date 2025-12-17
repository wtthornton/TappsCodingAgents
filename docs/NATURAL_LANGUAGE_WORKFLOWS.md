# Natural Language Workflow Triggers

## Overview

The natural language workflow trigger system allows you to execute workflows using conversational commands instead of remembering exact CLI syntax. Simply describe what you want to do, and the system will match your intent to the appropriate workflow.

## Quick Start

Instead of:
```bash
python -m tapps_agents.cli workflow rapid
```

You can say:
```
run rapid development
```

Or:
```
execute full SDLC pipeline
```

## Supported Commands

### Action Verbs

The system recognizes these action verbs:
- `run` - Run a workflow
- `execute` - Execute a workflow
- `start` - Start a workflow
- `trigger` - Trigger a workflow
- `launch` - Launch a workflow
- `begin` - Begin a workflow

### Workflow Types

You can reference workflows by:
- **Short names**: `rapid`, `full`, `fix`, `quality`, `hotfix`
- **Full names**: `rapid-dev`, `full-sdlc`, `maintenance`, `quick-fix`
- **Synonyms**: "rapid development", "full SDLC", "bug fix", "quick fix"

### Examples

**Rapid Development:**
```
run rapid development
execute rapid dev
start feature workflow
```

**Full SDLC:**
```
run full SDLC pipeline
execute enterprise workflow
start complete lifecycle
```

**Maintenance/Fixes:**
```
run fix workflow
execute maintenance
start bug fix
```

**Quality Improvement:**
```
run quality workflow
execute code review
start quality improvement
```

**Hotfix:**
```
run hotfix
execute urgent fix
start emergency patch
```

## Parameters

### Target File

Specify a target file:
```
run fix on example.py
execute rapid dev for bug.py
start maintenance workflow targeting test.py
```

### Auto Mode

Enable auto mode:
```
run rapid development with auto mode
execute full SDLC automatically
```

## Context-Aware Suggestions

The system provides workflow suggestions based on your project context:
- Recent git changes
- Current branch name
- Modified files
- Project type

Ask for suggestions:
```
what workflows can I run?
suggest a workflow
show workflow recommendations
```

## Confirmation

Before execution, you'll see a confirmation prompt:
```
============================================================
Workflow Execution Confirmation
============================================================

Workflow: Rapid Development
Description: Quick feature development workflow
Steps: 5

Proceed with execution? [y/N]:
```

Respond with:
- `y` or `yes` - Proceed
- `n` or `no` - Cancel

## Error Handling

### No Match Found

If no workflow matches your request:
```
Error: No workflow matches your request.

Suggestions:
  1. rapid-dev
  2. full-sdlc
  3. maintenance

CLI Command: python -m tapps_agents.cli workflow list
```

### Ambiguous Request

If multiple workflows match:
```
Multiple workflows match your request:

1. rapid-dev (confidence: 85%)
2. full-sdlc (confidence: 75%)

Please select a workflow number or type the workflow name:
```

## Troubleshooting

### Low Confidence Matches

If confidence is low, the system will show it:
```
Confidence: 60% (low)
```

You can still proceed, but consider rephrasing for better accuracy.

### Voice Commands

Voice input is supported if Cursor provides voice input capabilities. The system handles speech-to-text variations automatically.

### Fallback to CLI

If natural language parsing fails, you can always use CLI commands:
```bash
python -m tapps_agents.cli workflow rapid
python -m tapps_agents.cli workflow list
```

## Best Practices

1. **Be specific**: "run rapid development" is better than "run workflow"
2. **Use workflow names**: Direct names like "rapid" or "full" work best
3. **Include context**: "run fix on bug.py" is clearer than "run fix"
4. **Check suggestions**: Use suggestions to discover available workflows
5. **Confirm before execution**: Review the confirmation prompt carefully

## Configuration

Configuration is stored in `.cursor/nl-workflow-config.yaml`:

```yaml
parser:
  confidence_threshold: 0.7
  ambiguity_threshold: 0.1
  auto_select_threshold: 0.2
aliases:
  # Custom aliases
  quick: rapid-dev
learning:
  enabled: true
  correction_history_file: .cursor/nl-learning-history.json
```

## Learning System

The system learns from your corrections to improve accuracy over time. Corrections are stored in `.cursor/nl-learning-history.json`.

## See Also

- [Workflow Documentation](WORKFLOWS.md)
- [CLI Commands](QUICK_WORKFLOW_COMMANDS.md)
- [API Reference](../docs/API.md)

