# Quick Workflow Commands Guide

**One-word commands to execute complete agent workflows automatically.**

## Quick Commands

### Short Aliases

```bash
# Full SDLC Pipeline (Enterprise projects)
python -m tapps_agents.cli workflow full

# Rapid Development (Feature work)
python -m tapps_agents.cli workflow rapid

# Maintenance & Bug Fixing
python -m tapps_agents.cli workflow fix

# Quality Improvement
python -m tapps_agents.cli workflow quality

# Quick Fix (Hotfixes)
python -m tapps_agents.cli workflow hotfix
```

### Voice-Friendly Aliases

```bash
# Same as "full"
python -m tapps_agents.cli workflow enterprise

# Same as "rapid"
python -m tapps_agents.cli workflow feature

# Same as "fix"
python -m tapps_agents.cli workflow refactor

# Same as "quality"
python -m tapps_agents.cli workflow improve

# Same as "hotfix"
python -m tapps_agents.cli workflow urgent
```

## List All Presets

```bash
python -m tapps_agents.cli workflow list
```

## Workflow Details

### 1. Full SDLC Pipeline (`full` / `enterprise`)

**Best for:** Enterprise projects, new applications, compliance-heavy systems

**Agents:** Analyst → Planner → Architect → Designer → Implementer → Reviewer → Tester → Ops → Documenter

**Quality Gates:**
- Overall score: ≥70
- Security: ≥7.0
- Maintainability: ≥7.0

### 2. Rapid Development (`rapid` / `feature`)

**Best for:** Feature development, sprint work, iterative development

**Agents:** Enhancer → Planner → Implementer → Reviewer → Tester

**Quality Gates:**
- Overall score: ≥65
- Security: ≥6.5

### 3. Maintenance & Bug Fixing (`fix` / `refactor`)

**Best for:** Existing codebases, bug fixes, refactoring, technical debt

**Agents:** Debugger → Improver → Reviewer → Tester → Documenter

**Quality Gates:**
- Overall score: ≥70
- Maintainability: ≥7.5

### 4. Quality Improvement (`quality` / `improve`)

**Best for:** Code quality initiatives, refactoring sprints, quality gates

**Agents:** Reviewer → Improver → Reviewer → Tester → Ops

**Quality Gates:**
- Overall score: ≥75
- Maintainability: ≥8.0
- Security: ≥7.5

### 5. Quick Fix (`hotfix` / `urgent`)

**Best for:** Production bugs, hotfixes, urgent patches

**Agents:** Debugger → Implementer → Reviewer → Tester

**Quality Gates:**
- Overall score: ≥60
- Security: ≥7.0

## Usage Examples

### Example 1: Start New Feature

```bash
python -m tapps_agents.cli workflow rapid
```

This will:
1. Enhance your prompt (if provided)
2. Create user stories
3. Generate code
4. Review with scoring
5. Generate tests

### Example 2: Fix Production Bug

```bash
python -m tapps_agents.cli workflow hotfix
```

This will:
1. Analyze the error
2. Implement fix
3. Quick review
4. Run tests

### Example 3: Enterprise Project

```bash
python -m tapps_agents.cli workflow enterprise
```

This will:
1. Gather requirements
2. Plan stories
3. Design architecture
4. Design APIs
5. Implement code
6. Review with strict gates
7. Generate tests
8. Security scan
9. Generate documentation

## Voice Commands

These commands are designed to work with voice input:

- "run rapid development" → `workflow rapid`
- "execute full sdlc" → `workflow full`
- "start maintenance workflow" → `workflow fix`
- "run quality improvement" → `workflow quality`
- "execute quick fix" → `workflow hotfix`

## Integration

These workflows integrate with:
- ✅ Expert consultation (domain experts)
- ✅ Quality gates (scoring thresholds)
- ✅ Context tiers (token optimization)
- ✅ Multi-agent orchestration
- ✅ Git worktree isolation

## Customization

Workflow presets are defined in `workflows/presets/`:
- `full-sdlc.yaml`
- `rapid-dev.yaml`
- `maintenance.yaml`
- `quality.yaml`
- `quick-fix.yaml`

You can modify these files or create your own presets.

## See Also

- [Multi-Agent Orchestration Guide](MULTI_AGENT_ORCHESTRATION_GUIDE.md)
- [Workflow Selection Guide](WORKFLOW_SELECTION_GUIDE.md)

