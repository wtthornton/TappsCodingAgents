# Workflow Recommendation Guide

## Overview

The workflow recommendation system helps you select the most appropriate workflow for your project by analyzing project characteristics and providing interactive guidance.

## Quick Start

```bash
# Get a workflow recommendation
tapps-agents workflow recommend

# Non-interactive mode (for scripts)
tapps-agents workflow recommend --non-interactive --format json

# With auto-load after confirmation
tapps-agents workflow recommend --auto-load
```

## Command Options

### Basic Usage

```bash
tapps-agents workflow recommend [OPTIONS]
```

### Options

- `--non-interactive`: Run in non-interactive mode (no prompts, JSON output)
- `--format {json,text}`: Output format (default: text)
- `--auto-load`: Automatically load the recommended workflow after confirmation

## How It Works

### 1. Project Analysis

The system automatically analyzes your project to detect:
- Project type (greenfield, brownfield, quick fix)
- Project scope (full-stack, service, UI-only)
- Complexity indicators
- Existing documentation

### 2. Recommendation

Based on the analysis, the system recommends:
- **Workflow track**: Quick Flow, BMad Method, or Enterprise
- **Specific workflow**: The best matching workflow file
- **Confidence level**: How certain the recommendation is
- **Time estimate**: Approximate time to complete setup

### 3. Interactive Q&A (for Ambiguous Cases)

If the recommendation has low confidence (< 70%) or multiple valid options, the system asks clarifying questions:

1. **Project Scope**: What is the scope of your change?
   - Bug fix or small feature (< 5 files)
   - New feature or enhancement (5-20 files)
   - Major feature or refactoring (20+ files)
   - Enterprise/compliance work

2. **Time Constraint**: What is your time constraint?
   - Quick fix needed ASAP
   - Standard development timeline
   - No rush, quality is priority

3. **Documentation Needs**: How much documentation is needed?
   - Minimal (code comments only)
   - Standard (README updates)
   - Comprehensive (full docs, architecture)

### 4. Confirmation and Override

After the recommendation, you can:
- **Accept** (y): Use the recommended workflow
- **Decline** (N): Just view the recommendation
- **Override** (o): Manually select a different workflow from the available list

## Output Formats

### Text Format (Default)

```
============================================================
Workflow Recommendation
============================================================

📋 **BMad Method** workflow recommended
Confidence: 85%
Project Type: brownfield
✅ Loaded: `brownfield-fullstack.yaml`

⏱️  Estimated Time: 15-30 minutes (approximate)

Alternative Workflows:
  • quick-fix
  • enterprise-fullstack

Accept this recommendation? [y/N/o] (o=override):
```

### JSON Format

```json
{
  "workflow_file": "brownfield-fullstack",
  "track": "bmad_method",
  "confidence": 0.85,
  "message": "📋 **BMad Method** workflow recommended...",
  "time_estimate": "15-30 minutes",
  "alternative_workflows": ["quick-fix", "enterprise-fullstack"],
  "is_ambiguous": false,
  "characteristics": {
    "project_type": "brownfield",
    "workflow_track": "bmad_method",
    "confidence": 0.85
  }
}
```

## Workflow Tracks

### ⚡ Quick Flow
- **Best for**: Bug fixes, small features (< 5 files)
- **Time**: 5-15 minutes
- **Characteristics**: Minimal planning, direct implementation

### 📋 BMad Method (Standard)
- **Best for**: New features, enhancements, standard development
- **Time**: 15-30 minutes
- **Characteristics**: Full planning, comprehensive QA

### 🏢 Enterprise
- **Best for**: Enterprise applications, compliance, complex integrations
- **Time**: 30-60 minutes
- **Characteristics**: Full governance, enhanced documentation

## Examples

### Example 1: Quick Recommendation

```bash
$ tapps-agents workflow recommend

============================================================
Workflow Recommendation
============================================================

📋 **BMad Method** workflow recommended
Confidence: 90%
Project Type: brownfield
✅ Loaded: `brownfield-fullstack.yaml`

⏱️  Estimated Time: 15-30 minutes (approximate)

Accept this recommendation? [y/N/o]: y
```

### Example 2: Ambiguous Case with Q&A

```bash
$ tapps-agents workflow recommend

============================================================
Workflow Recommendation
============================================================

📋 **BMad Method** workflow recommended
Confidence: 55%

------------------------------------------------------------
Clarifying Questions
------------------------------------------------------------

1. What is the scope of your change?
   [1] Bug fix or small feature (< 5 files)
   [2] New feature or enhancement (5-20 files)
   [3] Major feature or refactoring (20+ files)
   [4] Enterprise/compliance work
   Your choice [1-4]: 2

2. What is your time constraint?
   [1] Quick fix needed ASAP
   [2] Standard development timeline
   [3] No rush, quality is priority
   Your choice [1-3]: 2

3. How much documentation is needed?
   [1] Minimal (code comments only)
   [2] Standard (README updates)
   [3] Comprehensive (full docs, architecture)
   Your choice [1-3]: 2

⏱️  Estimated Time: 15-30 minutes (approximate)

Accept this recommendation? [y/N/o]: y
```

### Example 3: Override Selection

```bash
$ tapps-agents workflow recommend

... (recommendation shown) ...

Accept this recommendation? [y/N/o]: o

Available workflows:
  [1] Quick Fix - Fast bug fixes and hotfixes
  [2] Rapid Development - Feature development workflow
  [3] Full SDLC - Complete development lifecycle
  [4] Enterprise - Enterprise-grade workflow
  [5] Quality Improvement - Code quality focus

Select workflow number: 2

✅ Selected: Rapid Development
✅ Loaded workflow: Rapid Development
```

### Example 4: Non-Interactive (Scripts)

```bash
$ tapps-agents workflow recommend --non-interactive --format json | jq '.workflow_file'
"brownfield-fullstack"
```

## Troubleshooting

### Issue: "No workflows found"

**Solution**: Ensure you have workflow files in the `workflows/` directory. Run `tapps-agents init` to set up default workflows.

### Issue: "Low confidence recommendation"

**Solution**: The system detected ambiguity. Answer the clarifying questions to get a better recommendation, or use `--non-interactive` to skip Q&A.

### Issue: "Workflow file not found"

**Solution**: The recommended workflow file doesn't exist. Use override (option 'o') to select from available workflows, or check your `workflows/` directory.

### Issue: Command not found

**Solution**: Ensure you're using the correct command format: `tapps-agents workflow recommend` (not `workflow-recommend`).

## Integration with Workflow Executor

After confirmation, if `--auto-load` is used, the recommended workflow is automatically loaded into the workflow executor. You can then execute it:

```bash
# Get recommendation and auto-load
tapps-agents workflow recommend --auto-load

# The workflow is now loaded and ready to execute
# (WorkflowExecutor integration handles this automatically)
```

## Best Practices

1. **Use interactive mode** for first-time setup to understand the recommendation
2. **Use non-interactive mode** in scripts and CI/CD pipelines
3. **Review alternatives** if the recommendation doesn't match your needs
4. **Answer Q&A questions** honestly for better recommendations
5. **Check time estimates** to plan your workflow execution

## Related Commands

- `tapps-agents workflow list` - List all available workflow presets
- `tapps-agents workflow <preset>` - Execute a specific workflow preset
- `tapps-agents init` - Initialize project with workflow presets

## See Also

- [Workflow Selection Guide](WORKFLOW_SELECTION_GUIDE.md)
- [Quick Workflow Commands](QUICK_WORKFLOW_COMMANDS.md)
- [Workflow Executor Documentation](API.md#workflow-executor)

