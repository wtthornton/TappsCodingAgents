# Quick Start - Try Workflow Commands

## Example 1: List Available Workflows

```bash
python -m tapps_agents.cli workflow list
```

This shows all 5 preset workflows with their descriptions and aliases.

## Example 2: Quick Fix Workflow (Recommended First Try)

I've created `example_bug.py` with some bugs. Try fixing it:

```bash
# Review the buggy file first
python -m tapps_agents.cli reviewer review example_bug.py

# Then run the quick fix workflow
python -m tapps_agents.cli workflow hotfix
```

**What it does:**
1. Debugger analyzes the errors
2. Implementer fixes the bugs
3. Reviewer checks the fixes
4. Tester ensures tests pass

## Example 3: Rapid Development

Create a new feature quickly:

```bash
python -m tapps_agents.cli workflow rapid
```

**What it does:**
1. Enhancer improves your prompt (if you provide one)
2. Planner creates user stories
3. Implementer generates code
4. Reviewer scores the code
5. Tester creates tests

## Example 4: Quality Improvement

Improve code quality of an existing file:

```bash
# First, score a file to see current quality
python -m tapps_agents.cli reviewer score example_bug.py

# Then run quality improvement
python -m tapps_agents.cli workflow quality
```

**What it does:**
1. Reviewer analyzes code (initial review)
2. Improver refactors based on findings
3. Reviewer re-reviews to validate improvements
4. Tester ensures tests still pass
5. Ops agent runs security scan

## Example 5: Maintenance & Refactoring

Refactor existing code:

```bash
python -m tapps_agents.cli workflow fix
```

**What it does:**
1. Debugger analyzes issues
2. Improver refactors code
3. Reviewer validates improvements
4. Tester updates tests
5. Documenter updates documentation

## Example 6: Full Enterprise Workflow

For complete projects:

```bash
python -m tapps_agents.cli workflow enterprise
```

**What it does:**
1. Analyst gathers requirements
2. Planner creates stories
3. Architect designs system
4. Designer creates API specs
5. Implementer writes code
6. Reviewer with strict quality gates
7. Tester generates tests
8. Ops security scan
9. Documenter generates docs

## Voice Commands

You can also use voice-friendly names:

```bash
python -m tapps_agents.cli workflow feature    # Same as "rapid"
python -m tapps_agents.cli workflow urgent    # Same as "hotfix"
python -m tapps_agents.cli workflow refactor  # Same as "fix"
python -m tapps_agents.cli workflow improve  # Same as "quality"
```

## Tips

1. **Start Simple**: Try `workflow list` first to see all options
2. **Quick Fix**: Use `hotfix` for urgent bugs (fastest)
3. **New Features**: Use `rapid` for sprint work
4. **Quality**: Use `quality` for dedicated improvement sprints
5. **Enterprise**: Use `enterprise` for compliance-heavy projects

## Next Steps

After running a workflow, check:
- Generated files in your project
- Review reports
- Test results
- Quality scores

All workflows integrate with your expert system and quality gates!

