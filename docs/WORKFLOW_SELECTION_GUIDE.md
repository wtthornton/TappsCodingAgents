# Scale-Adaptive Workflow Selection Guide

**Phase 4: Scale-Adaptive Workflow Selection**

This guide explains how the framework automatically detects project types and recommends appropriate workflows.

## Overview

The Scale-Adaptive Workflow Selection system automatically analyzes your project and recommends the best workflow track based on:

- **Project Type**: Greenfield, Brownfield, Quick-Fix, or Hybrid
- **Project Complexity**: Simple, Standard, or Enterprise
- **User Context**: Query keywords, file scope, change description

## Workflow Tracks

### ⚡ Quick Flow (< 5 min)
**Best for**: Bug fixes, hotfixes, small features, urgent patches

**Characteristics:**
- User query contains keywords like "bug", "fix", "hotfix", "patch"
- Scope is small (< 5 files typically)
- Minimal planning overhead
- Direct to implementation
- Quick QA review

### 📋 BMad Method (< 15 min)
**Best for**: New features, standard development, typical project work

**Characteristics:**
- Standard development lifecycle
- Full PRD + Architecture + UX (if needed)
- Story-driven development
- Comprehensive QA
- Works for both greenfield and brownfield projects

### 🏢 Enterprise (< 30 min)
**Best for**: Enterprise apps, compliance-heavy projects, complex systems

**Characteristics:**
- Compliance requirements (HIPAA, PCI DSS, GDPR, etc.)
- Security-focused development
- Multiple business domains
- Large codebase (>1000 files)
- Enhanced documentation and governance

## Project Type Detection

### Greenfield Projects

**Indicators:**
- No `src/` or `lib/` directory
- No package management files (`package.json`, `requirements.txt`, etc.)
- No git history (no `.git/` directory)
- Minimal files (< 5 files)
- Empty or new project

**Recommendation:** BMad Method → Greenfield Development workflow

### Brownfield Projects

**Indicators:**
- `src/` or `lib/` directory exists
- Package management files present
- Git history exists (`.git/` directory)
- Test directory exists
- Documentation exists (README, docs/)
- Many files (> 5 files)

**Recommendation:** BMad Method → Brownfield Development workflow

### Quick-Fix Projects

**Indicators:**
- User query contains: "bug", "fix", "hotfix", "patch", "issue", "error"
- Small scope (< 5 files to change)
- Change description mentions fixing/repairing

**Recommendation:** Quick Flow → Quick-Fix workflow

### Hybrid Projects

**Indicators:**
- Mixed greenfield and brownfield indicators
- Unclear project state

**Recommendation:** BMad Method → Feature Development workflow (default)

## Usage

### Automatic Detection

The workflow executor automatically detects project type when `auto_detect=True`:

```python
from tapps_agents.workflow import WorkflowExecutor

# Auto-detection enabled by default
executor = WorkflowExecutor(project_root=Path("."), auto_detect=True)

# Get workflow recommendation
recommendation = executor.recommend_workflow(
    user_query="Fix authentication bug",
    file_count=2
)

print(recommendation.message)
# Output:
# ⚡ **Quick Flow** workflow recommended
# Confidence: 80%
# Project Type: quick_fix
# ✅ Loaded: `quick-fix.yaml`
```

### Manual Detection

You can also use the detector directly:

```python
from tapps_agents.workflow import ProjectDetector

detector = ProjectDetector(project_root=Path("."))

# Detect from file system
characteristics = detector.detect()
print(f"Project Type: {characteristics.project_type.value}")
print(f"Workflow Track: {characteristics.workflow_track.value}")
print(f"Confidence: {characteristics.confidence:.0%}")

# Detect from context (for quick-fix)
characteristics = detector.detect_from_context(
    user_query="Fix the bug in auth.py",
    file_count=1
)
```

### Workflow Recommendation

Use the recommender for complete workflow recommendation:

```python
from tapps_agents.workflow import WorkflowRecommender

recommender = WorkflowRecommender(
    project_root=Path("."),
    workflows_dir=Path("./workflows")
)

# Get recommendation
recommendation = recommender.recommend(
    user_query="Implement user authentication",
    file_count=10,
    auto_load=True
)

# Access recommendation details
print(recommendation.message)
print(f"Recommended workflow: {recommendation.workflow_file}")
print(f"Track: {recommendation.track.value}")
print(f"Confidence: {recommendation.confidence:.0%}")

# Use recommended workflow
if recommendation.workflow:
    executor = WorkflowExecutor()
    executor.workflow = recommendation.workflow
    executor.start()
```

## Detection Rules

### Greenfield Indicators

| Indicator | Weight | Description |
|-----------|--------|-------------|
| `no_src` | 0.25 | No src/ or lib/ directory |
| `no_package_files` | 0.25 | No package.json, requirements.txt, etc. |
| `no_git_history` | 0.25 | No .git/ directory |
| `minimal_files` | 0.25 | < 5 files in project root |

**Threshold:** Score >= 0.5 → Greenfield

### Brownfield Indicators

| Indicator | Weight | Description |
|-----------|--------|-------------|
| `has_src` | 0.15 | src/ or lib/ directory exists |
| `has_package_files` | 0.15 | Package management files exist |
| `has_git_history` | 0.15 | .git/ directory exists |
| `has_tests` | 0.15 | tests/ or test/ directory exists |
| `has_docs` | 0.15 | docs/ or README.md exists |
| `many_files` | 0.15 | >= 5 files in project root |

**Threshold:** Score >= 0.45 → Brownfield (prioritized over greenfield)

### Quick-Fix Indicators

| Indicator | Weight | Description |
|-----------|--------|-------------|
| `quick_fix_keywords` | 0.2 per match | Query contains bug/fix keywords |
| `small_scope` | 0.4 | < 5 files to change |

**Threshold:** Score >= 0.6 → Quick-Fix

### Enterprise Indicators

| Indicator | Weight | Description |
|-----------|--------|-------------|
| `has_compliance` | 0.25 | Compliance files/directories exist |
| `has_security` | 0.25 | Security configuration files exist |
| `multiple_domains` | 0.25 | Multiple domains in domains.md |
| `large_codebase` | 0.25 | > 1000 code files |

**Threshold:** Score >= 0.25 → Upgrade to Enterprise track

## Workflow Files

The recommender looks for workflow files in the `workflows/` directory:

- `quick-fix.yaml` - Quick Flow track
- `greenfield-development.yaml` - Greenfield projects
- `brownfield-development.yaml` - Brownfield projects
- `feature-development.yaml` - Default/fallback
- `enterprise-development.yaml` - Enterprise track

If a recommended workflow file doesn't exist, the recommender will:
1. Try to find a similar workflow by name
2. List alternative workflows
3. Return recommendation without loading a workflow

## Examples

### Example 1: Quick Bug Fix

```python
recommendation = executor.recommend_workflow(
    user_query="Fix bug in authentication.py - users can't login",
    file_count=1
)

# Result: Quick Flow track, quick-fix.yaml workflow
```

### Example 2: New Feature in Existing Project

```python
# Detects brownfield project automatically
recommendation = executor.recommend_workflow(
    user_query="Add user profile page",
    file_count=15
)

# Result: BMad Method track, brownfield-development.yaml workflow
```

### Example 3: Enterprise Project

```python
# Project has compliance/ directory
# Detects enterprise automatically
recommendation = executor.recommend_workflow()

# Result: Enterprise track, enterprise-development.yaml workflow
```

### Example 4: New Project

```python
# Empty directory or new project
# Detects greenfield automatically
recommendation = executor.recommend_workflow()

# Result: BMad Method track, greenfield-development.yaml workflow
```

## Configuration

### Disable Auto-Detection

If you want to disable automatic workflow detection:

```python
executor = WorkflowExecutor(
    project_root=Path("."),
    auto_detect=False  # Disable auto-detection
)

# Must manually load workflow
executor.load_workflow(Path("workflows/custom-workflow.yaml"))
```

### Custom Workflow Directory

Specify a custom workflows directory:

```python
recommender = WorkflowRecommender(
    project_root=Path("."),
    workflows_dir=Path("./custom-workflows")
)
```

## Integration with CLI

The workflow selection integrates with the CLI and agent commands:

```bash
# CLI command (to be implemented)
tapps-agents workflow-init

# Agent command (to be implemented)
*workflow-init
```

These commands will:
1. Analyze project structure
2. Detect project type
3. Recommend workflow track
4. Load appropriate workflow
5. Update `.tapps-agents/config.yaml` with selection

## Troubleshooting

### Wrong Workflow Recommended

If the automatic recommendation is incorrect:

1. **Check indicators**: Review what indicators were detected
   ```python
   characteristics = detector.detect()
   print(characteristics.indicators)
   ```

2. **Manual override**: Disable auto-detection and load workflow manually
   ```python
   executor = WorkflowExecutor(auto_detect=False)
   executor.load_workflow(Path("workflows/correct-workflow.yaml"))
   ```

3. **Adjust thresholds**: Modify detection thresholds in `detector.py` if needed

### Workflow File Not Found

If recommended workflow file doesn't exist:

1. **Check workflows directory**: Ensure `workflows/` directory exists
2. **List available workflows**: 
   ```python
   recommender = WorkflowRecommender()
   workflows = recommender.list_available_workflows()
   print(workflows)
   ```
3. **Create workflow file**: Create the recommended workflow YAML file

### Low Confidence Scores

If confidence is low (< 50%):

- Project may be truly hybrid (mixed indicators)
- Consider manually selecting a workflow
- Review project structure and ensure clear indicators

## See Also

- [Workflow Models](../tapps_agents/workflow/models.py) - Workflow data structures
- [Workflow Executor](../tapps_agents/workflow/executor.py) - Workflow execution
- [Project Requirements](../requirements/PROJECT_REQUIREMENTS.md#174-scale-adaptive-workflow-selection) - Full specification

