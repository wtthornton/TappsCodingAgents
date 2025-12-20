# Simple Mode Cursor Enablement Plan

## Problem Statement (SOLVED)

Simple Mode was not working correctly in Cursor because:
1. The skill described what it should do but didn't specify HOW to invoke other skills
2. The rule had `alwaysApply: false`, making it invisible to Cursor
3. The skill was trying to use CLI commands instead of Cursor-native skill invocation

## Root Cause Analysis

### Original Issues

1. **Skill didn't invoke other skills**: The SKILL.md described workflows but didn't show the AI how to actually call `@enhancer`, `@planner`, etc.
2. **Rule not always applied**: With `alwaysApply: false`, Cursor didn't know Simple Mode existed
3. **CLI-focused instead of Cursor-native**: Instructions pointed to `tapps-agents` CLI commands instead of `@skill-name` invocations
4. **No orchestration pattern**: The skill didn't explain that it should call other skills using `@skill-name *command` syntax

## Solution Implemented

### 1. Rewrote Simple Mode Skill (`.claude/skills/simple-mode/SKILL.md`)

**Key Changes:**
- Added **Cursor-native orchestrator** identity
- Added explicit **skill invocation patterns** using `@skill-name *command` syntax
- Added **workflow sequences** showing which skills to call for each intent
- Removed CLI-focused instructions
- Added **example conversations** showing proper orchestration

**New Structure:**
```
@simple-mode *build "description"
  → @enhancer *enhance "{description}"
  → @planner *plan "{enhanced}"
  → @architect *design "{enhanced}"
  → @designer *design-api "{enhanced}"
  → @implementer *implement "{spec}" {file}
  → @reviewer *review {file}
  → @tester *test {file}
```

### 2. Updated Simple Mode Rule (`.cursor/rules/simple-mode.mdc`)

**Key Changes:**
- Set `alwaysApply: true` so Cursor always knows about Simple Mode
- Added comprehensive **skill orchestration workflows**
- Added **intent detection** table
- Added **available skills reference** table
- Added **example conversations**

### 3. Updated Resource Files

Both files in `tapps_agents/resources/` were updated to match:
- `tapps_agents/resources/claude/skills/simple-mode/SKILL.md`
- `tapps_agents/resources/cursor/rules/simple-mode.mdc`

## How It Works Now

When a user types `@simple-mode *build "Create a user auth API"`:

1. **Cursor invokes the Simple Mode skill**
2. **Simple Mode parses intent** (build, review, fix, test, full)
3. **Simple Mode invokes other skills** using `@skill-name *command` syntax:
   - `@enhancer *enhance "Create a user auth API"`
   - `@planner *plan "Enhanced: Create a user auth API with security..."`
   - `@architect *design "Auth system architecture..."`
   - etc.
4. **Results are coordinated** and reported back to the user

## Testing Checklist

- [x] Simple Mode rule has `alwaysApply: true`
- [x] Simple Mode skill shows how to invoke other skills
- [x] Skill includes workflow sequences for each intent
- [x] Examples show proper `@skill-name *command` syntax
- [x] Resource files match project files
- [ ] Test `@simple-mode *build "description"` in Cursor
- [ ] Test `@simple-mode *review file.py` in Cursor
- [ ] Verify skills are invoked correctly

## How to Use

### Build a Feature
```
@simple-mode *build "Create a user authentication API with JWT tokens"
```

### Review Code
```
@simple-mode *review src/api/auth.py
```

### Fix a Bug
```
@simple-mode *fix src/api/auth.py "Fix the null pointer error"
```

### Generate Tests
```
@simple-mode *test src/api/auth.py
```

### Full SDLC
```
@simple-mode *full "Build a complete REST API for a todo application"
```

## Files Changed

### Simple Mode Core Files
1. `.claude/skills/simple-mode/SKILL.md` - Complete rewrite as Cursor-native orchestrator
2. `.cursor/rules/simple-mode.mdc` - Set alwaysApply: true, added orchestration docs
3. `tapps_agents/resources/claude/skills/simple-mode/SKILL.md` - Synced with project file
4. `tapps_agents/resources/cursor/rules/simple-mode.mdc` - Synced with project file
5. `.cursor/rules/quick-reference.mdc` - Added Simple Mode section

### Skills Updated with Command Aliases
6. `.claude/skills/analyst/SKILL.md` - Added `*requirements` alias
7. `.claude/skills/architect/SKILL.md` - Added `*design` alias
8. `.claude/skills/improver/SKILL.md` - Added `*improve` alias
9. `.claude/skills/documenter/SKILL.md` - Added `*document-api` alias
10. `tapps_agents/resources/claude/skills/analyst/SKILL.md` - Synced
11. `tapps_agents/resources/claude/skills/architect/SKILL.md` - Synced
12. `tapps_agents/resources/claude/skills/improver/SKILL.md` - Synced
13. `tapps_agents/resources/claude/skills/documenter/SKILL.md` - Synced

## All Skills Reviewed (15 Total)

| Skill | Purpose | Simple Mode Compatible |
|-------|---------|------------------------|
| `analyst` | Requirements gathering | ✅ (added `*requirements` alias) |
| `architect` | System design | ✅ (added `*design` alias) |
| `debugger` | Error analysis | ✅ |
| `designer` | API/data design | ✅ |
| `documenter` | Documentation | ✅ (added `*document-api` alias) |
| `enhancer` | Prompt enhancement | ✅ |
| `implementer` | Code generation | ✅ |
| `improver` | Code improvement | ✅ (added `*improve` alias) |
| `ops` | Security/deployment | ✅ |
| `orchestrator` | YAML workflows | ✅ |
| `planner` | User stories | ✅ |
| `reviewer` | Code review | ✅ |
| `simple-mode` | Orchestrator | ✅ (rewritten) |
| `tester` | Test generation | ✅ |

## All Rules Reviewed (6 Total)

| Rule | alwaysApply | Purpose |
|------|-------------|---------|
| `simple-mode.mdc` | ✅ true | Simple Mode orchestrator documentation |
| `quick-reference.mdc` | false | Quick command reference |
| `agent-capabilities.mdc` | false | Detailed agent guide |
| `project-context.mdc` | false | Project context |
| `project-profiling.mdc` | false | Auto-detection |
| `workflow-presets.mdc` | false | Workflow preset docs |

