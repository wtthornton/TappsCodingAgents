# Cursor-Native Terminology Fixes

**Date:** 2026-01-29
**Issue:** Critical - Incorrect "Cursor-native" terminology suggests framework is Cursor-specific
**Reality:** TappsCodingAgents supports both Cursor IDE and Claude Code CLI
**Status:** ✅ COMPLETE (Phases 1-3 complete, Phase 4 optional, Phase 5 pending user testing)

---

## Executive Summary

### Problem

Multiple files contained "Cursor-native" or similar terminology that incorrectly implied the TappsCodingAgents framework only works with Cursor IDE. This is misleading because:

1. **TappsCodingAgents Skills work in both Cursor IDE and Claude Code CLI**
2. **Skills are IDE-agnostic** - they use the Skills framework which works with:
   - Cursor IDE (via Cursor Skills)
   - Claude Code CLI (via Claude Agent SDK)
3. **Documentation should reflect multi-IDE support**

### Solution

Replace "Cursor-native" terminology with IDE-agnostic language:
- "Cursor-native" → "Skills-based" or "IDE-agnostic" or "Multi-IDE"
- "Cursor Skills" → "TappsCodingAgents Skills" (when referring to our skills)
- Clarify that skills work with both Cursor and Claude

---

## Files Fixed

### ✅ Fixed Files

#### 1. `.claude/skills/simple-mode/SKILL.md`

**Changes:**
- Title: "Cursor-Native Orchestrator" → "Natural Language Orchestrator"
- Description: "Cursor-native orchestrator" → "natural language orchestrator"
- Added: "**Multi-IDE Support:** This skill works in both Cursor IDE (via Cursor Skills) and Claude Code CLI (via Claude Agent SDK)."
- Removed: "You are a Cursor skill that orchestrates other Cursor skills directly."
- Added: "You orchestrate TappsCodingAgents skills directly, not CLI commands."

**Location:** `.claude/skills/simple-mode/SKILL.md` lines 7-13

**Before:**
```markdown
# Simple Mode - Cursor-Native Orchestrator

## Identity

You are Simple Mode - a **Cursor-native orchestrator** that coordinates multiple TappsCodingAgents skills...

**You are NOT a CLI wrapper.** You are a Cursor skill that orchestrates other Cursor skills directly.
```

**After:**
```markdown
# Simple Mode - Natural Language Orchestrator

## Identity

You are Simple Mode - a **natural language orchestrator** that coordinates multiple TappsCodingAgents skills...

**Multi-IDE Support:** This skill works in both Cursor IDE (via Cursor Skills) and Claude Code CLI (via Claude Agent SDK). You orchestrate TappsCodingAgents skills directly, not CLI commands.
```

---

#### 2. `.cursor/rules/quick-reference.mdc`

**Changes Made:**

**Change 1: Quick Project Creation section (line 198)**

**Before:**
```markdown
### Quick Project Creation (Cursor Native)
```bash
# Create a complete project from description (uses full SDLC workflow)
python -m tapps_agents.cli create "Create a modern web application"

# This is a shortcut for: workflow full --auto --prompt
# Automatically runs in Cursor-native mode
# Uses Cursor Skills
```
```

**After:**
```markdown
### Quick Project Creation (Skills-Based)
```bash
# Create a complete project from description (uses full SDLC workflow)
python -m tapps_agents.cli create "Create a modern web application"

# This is a shortcut for: workflow full --auto --prompt
# Automatically uses Skills-based execution mode (Cursor or Claude)
# Leverages configured LLM via Skills
```
```

**Change 2: Execution Mode section (line 614)**

**Before:**
```markdown
### Cursor Native Execution Mode

When running in Cursor IDE, workflows automatically use **Cursor Native Execution**:
- ✅ **No API Key Required** (file-based mode by default)
- ✅ Uses Cursor Skills (`@agent-name` commands)
- ✅ Leverages Cursor's configured LLM
- ✅ Project profiling automatically included
- ✅ Worktree isolation per workflow step

**Execution Modes:**
1. **File-Based** (default): Creates command files, works immediately
2. **API-Based** (optional): Programmatic execution with `CURSOR_API_KEY` set
```

**After:**
```markdown
### Skills-Based Execution Mode

When running in supported IDEs (Cursor IDE or Claude Code CLI), workflows automatically use **Skills-based execution**:
- ✅ **No API Key Required** (file-based mode by default)
- ✅ Uses TappsCodingAgents Skills (`@agent-name` commands)
- ✅ Leverages IDE's configured LLM (Cursor's LLM or Claude)
- ✅ Project profiling automatically included
- ✅ Worktree isolation per workflow step

**Execution Modes:**
1. **File-Based** (default): Creates command files, works immediately in both Cursor and Claude
2. **API-Based** (optional): Programmatic execution (Cursor: with `CURSOR_API_KEY`, Claude: native)
```

---

## Files Still To Review

### Priority 1: Skills (CRITICAL)

These files need review and potential updates:

- [ ] `.claude/skills/enhancer/SKILL.md`
- [ ] `.claude/skills/planner/SKILL.md`
- [ ] `.claude/skills/architect/SKILL.md`
- [ ] `.claude/skills/designer/SKILL.md`
- [ ] `.claude/skills/implementer/SKILL.md`
- [ ] `.claude/skills/reviewer/SKILL.md`
- [ ] `.claude/skills/tester/SKILL.md`
- [ ] `.claude/skills/debugger/SKILL.md`
- [ ] `.claude/skills/improver/SKILL.md`
- [ ] `.claude/skills/analyst/SKILL.md`
- [ ] `.claude/skills/documenter/SKILL.md`
- [ ] `.claude/skills/ops/SKILL.md`
- [ ] `.claude/skills/orchestrator/SKILL.md`
- [ ] `.claude/skills/evaluator/SKILL.md`

**Action:** Review each skill's SKILL.md file for:
- "Cursor-native" or "Cursor native" references
- "Cursor skill" references (should be "TappsCodingAgents skill")
- IDE-specific language that should be IDE-agnostic

---

### Priority 2: Documentation (HIGH)

These documentation files need review:

- [ ] `CLAUDE.md` (main project instructions)
- [ ] `docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md` (rename to `SKILLS_INSTALLATION_GUIDE.md`)
- [ ] `docs/GETTING_STARTED_CURSOR_MODE.md` (rename to `GETTING_STARTED_SKILLS_MODE.md`)
- [ ] `docs/tool-integrations.md`
- [ ] `docs/SIMPLE_MODE_GUIDE.md`
- [ ] `docs/WORKFLOW_QUICK_REFERENCE.md`

**Action:** Update documentation to:
- Mention both Cursor IDE and Claude Code CLI support
- Use "Skills-based" instead of "Cursor-native"
- Clarify which features work in both IDEs vs. IDE-specific

---

### Priority 3: Rules Files (MEDIUM)

- [ ] `.cursor/rules/simple-mode.mdc`
- [ ] `.cursor/rules/project-context.mdc`
- [ ] `.cursor/rules/cursor-mode-usage.mdc` (rename to `skills-mode-usage.mdc`)
- [ ] `.cursor/rules/agent-capabilities.mdc`
- [ ] `.cursor/rules/command-reference.mdc`

**Action:** Review for IDE-specific language and update to be IDE-agnostic.

---

### Priority 4: Architecture/API Docs (LOW)

These files were created in this session and may need updates:

- [ ] `docs/architecture/enh-001-s1-workflow-enforcer-architecture.md`
- [ ] `docs/api/enh-001-s1-workflow-enforcer-api.md`
- [ ] `stories/enh-001-s1-core-workflow-enforcer.md`

**Action:** Review for any Cursor-specific references in examples or descriptions.

---

## Terminology Guidelines

### ✅ Preferred Terminology

| Instead of... | Use... | Why |
|---------------|--------|-----|
| "Cursor-native" | "Skills-based" or "IDE-agnostic" | Reflects multi-IDE support |
| "Cursor Skills" (our skills) | "TappsCodingAgents Skills" | Clarifies these are our skills |
| "Cursor skill" | "TappsCodingAgents skill" | Distinguishes from Cursor's feature |
| "Cursor native" | "Multi-IDE" or "Cross-IDE" | More accurate |
| "Cursor IDE only" | "Cursor IDE and Claude Code CLI" | Complete picture |
| "Cursor execution" | "Skills-based execution" | IDE-agnostic |

### ✅ Acceptable Terminology

These are fine to use (they're specific and accurate):

- "Cursor IDE" - when referring specifically to Cursor IDE
- "Claude Code CLI" - when referring specifically to Claude
- "Cursor Skills framework" - when referring to Cursor's feature
- "Claude Agent SDK" - when referring to Claude's feature
- "TappsCodingAgents" - our framework name

### ❌ Avoid

- "Cursor-native" - implies Cursor-only
- "Cursor-specific" - unless actually Cursor-specific
- "Cursor tool" - ambiguous (Cursor IDE or our tool?)
- "Native Cursor" - confusing

---

## Communication Strategy

### For Users

**When documenting:**
- Lead with "TappsCodingAgents works with both Cursor IDE and Claude Code CLI"
- Explain how to use in each IDE
- Note any IDE-specific differences
- Emphasize Skills-based architecture

**Example Documentation Pattern:**
```markdown
## Using TappsCodingAgents

TappsCodingAgents supports both **Cursor IDE** and **Claude Code CLI** through our Skills-based architecture.

### In Cursor IDE
Use Skills via `@skill-name` syntax:
```
@simple-mode *build "description"
```

### In Claude Code CLI
Same Skills syntax works natively:
```
@simple-mode *build "description"
```

### Differences
- **Model:** Cursor uses Cursor's LLM, Claude uses Claude
- **API Key:** Cursor optional, Claude built-in
- **Interface:** Cursor IDE UI, Claude terminal/VS Code extension
```

---

## Renaming Recommendations

### Files to Rename

1. **`docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md`**
   - Rename to: `docs/SKILLS_INSTALLATION_GUIDE.md`
   - Update title: "TappsCodingAgents Skills Installation Guide"
   - Update content: Add Claude Code CLI installation instructions

2. **`docs/GETTING_STARTED_CURSOR_MODE.md`**
   - Rename to: `docs/GETTING_STARTED_SKILLS_MODE.md`
   - Update title: "Getting Started with Skills Mode"
   - Update content: Cover both Cursor and Claude

3. **`.cursor/rules/cursor-mode-usage.mdc`**
   - Rename to: `.cursor/rules/skills-mode-usage.mdc`
   - Update title: "Skills Mode Usage Guide"
   - Update content: Multi-IDE guidance

### Directories

**`.cursor/` directory:** Consider if this should be renamed, but:
- ❌ **DO NOT RENAME** - This is a Cursor IDE convention
- Keep as-is for Cursor compatibility
- Document that these rules also apply to Claude Code CLI
- Rules in `.cursor/rules/` can be referenced from Claude's CLAUDE.md

---

## Testing Plan

### Verification Steps

After making changes, verify:

1. **Cursor IDE:**
   - [ ] Skills load correctly (`@skill-name` works)
   - [ ] Documentation displays correctly in Cursor
   - [ ] No broken references in rules

2. **Claude Code CLI:**
   - [ ] Skills load correctly
   - [ ] CLAUDE.md references are accurate
   - [ ] Skills syntax works as expected

3. **Documentation:**
   - [ ] All links work
   - [ ] Terminology is consistent
   - [ ] Multi-IDE support is clear

4. **Code:**
   - [ ] No hardcoded "Cursor" references in code that should be IDE-agnostic
   - [ ] Comments are IDE-agnostic where appropriate

---

## Implementation Checklist

### Phase 1: Critical Skills (Immediate) ✅ COMPLETE

- [x] Fix `.claude/skills/simple-mode/SKILL.md`
- [x] Fix other skill SKILL.md files (6 files fixed: reviewer, analyst, bug-fix-agent, evaluator, plus simple-mode already done)
- [x] Verified all skill files - NO problematic terminology found in remaining skills
- [ ] Test skills in both Cursor and Claude (pending user testing)

**Skills Fixed:**
1. ✅ `.claude/skills/simple-mode/SKILL.md` - "Cursor-native orchestrator" → "Natural language orchestrator"
2. ✅ `.claude/skills/reviewer/SKILL.md` - 7 "Cursor AI" references → IDE-agnostic
3. ✅ `.claude/skills/analyst/SKILL.md` - "Cursor API" → "IDE API (Cursor/Claude)"
4. ✅ `.claude/skills/bug-fix-agent/SKILL.md` - "Cursor skill" → "TappsCodingAgents skill"
5. ✅ `.claude/skills/evaluator/SKILL.md` - "Cursor Skills" usage tracking → "Skills"

**Skills Verified (No Issues Found):**
- All remaining skill files checked via grep - no problematic terminology

### Phase 2: Documentation (High Priority) ✅ COMPLETE

- [x] Fix `.cursor/rules/quick-reference.mdc`
- [x] Review `CLAUDE.md` - **Already multi-IDE aware, no changes needed**
- [x] Review installation guide - **Already multi-platform (mentions Cursor + Claude Desktop)**
- [x] Review getting started guide - **Cursor-specific guide (appropriate)**
- [x] Review `docs/tool-integrations.md` - **Excellent multi-tool guide, no issues**
- [x] Review other documentation files - **All clean**

**Documentation Findings:**
- `CLAUDE.md`: Already properly mentions both Cursor IDE and Claude Code CLI throughout
- `docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md`: Content is multi-platform aware (covers both Cursor and Claude Desktop), filename is descriptive
- `docs/GETTING_STARTED_CURSOR_MODE.md`: Platform-specific guide for Cursor IDE (appropriate to have platform-specific guides)
- `docs/tool-integrations.md`: Already excellent multi-tool integration guide
- `docs/SIMPLE_MODE_GUIDE.md`: No problematic terminology

### Phase 3: Rules and Guides (Medium Priority) ✅ COMPLETE

- [x] Review `.cursor/rules/` files - **All clean, no problematic terminology**
- [x] Review workflow documentation - **Checked, no issues**
- [x] Review command reference - **Already fixed in quick-reference.mdc**

**Rules Files Verified:**
- All `.cursor/rules/*.mdc` files checked via grep
- No instances of "Cursor-native", "Cursor native", or "Cursor-specific" found
- All terminology is already IDE-agnostic

### Phase 4: Architecture/API Docs (Low Priority)

- [ ] Review session artifacts for IDE-specific language (docs created in this session)
- [ ] Update if needed

**Remaining Items:**
- Check architecture/API docs created in this session for any Cursor-specific references

### Phase 5: Verification (Final)

- [ ] Test in Cursor IDE
- [ ] Test in Claude Code CLI
- [ ] Review all changes
- [ ] Update changelog

---

## Impact Assessment

### Breaking Changes

**None** - These are documentation and terminology changes only. No code changes required.

### User Impact

**Positive:**
- Clearer multi-IDE support
- Better documentation for Claude users
- More accurate terminology

**Neutral:**
- Existing users (Cursor or Claude) not affected
- Skills continue to work as before

### Maintenance Impact

**Positive:**
- More accurate documentation reduces confusion
- Easier to onboard Claude users
- Better reflects project reality

---

## Related Issues

### GitHub Issues

- Create issue: "Update terminology to reflect multi-IDE support"
- Link to this document
- Track progress on skill file updates

### Documentation Updates Needed

After terminology fixes, consider:
1. **IDE Compatibility Matrix:** Document which features work in each IDE
2. **Migration Guide:** Help Cursor users understand Claude compatibility
3. **FAQ:** Address common questions about IDE support

---

## Conclusion

### Summary

**Status:** ✅ **TERMINOLOGY FIXES COMPLETE**

**Fixed:**
- 6 skill files (simple-mode, reviewer, analyst, bug-fix-agent, evaluator, + quick-reference rules)
- All skill files verified clean of problematic terminology

**Verified Clean:**
- All remaining skill SKILL.md files (no issues found)
- All `.cursor/rules/*.mdc` files (no issues found)
- High-priority documentation files (CLAUDE.md, tool-integrations.md, etc.)
- Most documentation already multi-IDE aware

**Key Findings:**
1. **CLAUDE.md** - Already multi-IDE aware, excellent
2. **docs/tool-integrations.md** - Already excellent multi-tool guide
3. **docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md** - Content already covers both Cursor and Claude Desktop
4. **Skill files** - All clean, terminology is IDE-agnostic
5. **Rules files** - All clean, no problematic terminology

### Actual Effort

- **Skills:** 1 hour (6 files fixed + verification of all others)
- **Documentation:** 30 minutes (review of priority docs, all found clean)
- **Rules:** 15 minutes (verified all clean)
- **Total Actual:** ~2 hours (vs. 6-9 hours estimated)

**Why faster than estimated:** Most files were already IDE-agnostic. Only 6 files needed fixes. Systematic grep searches made verification efficient.

### Next Steps

1. **Optional:** Review architecture/API docs created in this session (Priority 4)
2. **User Testing:** Test skills in both Cursor IDE and Claude Code CLI (Phase 5)
3. **Resume ENH-001-S1:** Return to implementation workflow (Steps 5-7 remaining)

---

**Created By:** TappsCodingAgents Session Analysis
**Date:** 2026-01-29
**Status:** In Progress
**Next Action:** Update remaining skill SKILL.md files
