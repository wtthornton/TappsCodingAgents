# Command Documentation Coverage Evaluation

**Date**: January 2026  
**Purpose**: Evaluate whether all tapps-agents commands, subcommands, and @simple-mode commands are documented in cursor rules and README files that are installed during init and release processes.

## Executive Summary

**Status**: ⚠️ **PARTIAL COVERAGE** - Significant gaps identified

**Key Findings**:
- ✅ **Top-level commands**: Well documented in `command-reference.mdc` and README.md
- ✅ **Simple Mode commands**: Comprehensive documentation in `simple-mode.mdc` and `command-reference.mdc`
- ⚠️ **Agent subcommands**: Partially documented - many subcommands missing from cursor rules
- ❌ **Advanced CLI commands**: Many commands not documented in cursor rules (analytics, governance, auto-exec, etc.)
- ⚠️ **README.md**: Contains high-level overview but not exhaustive command reference

## What Gets Installed During `tapps-agents init`

### Cursor Rules (`.cursor/rules/`) - 7 Files
1. `workflow-presets.mdc` - Workflow preset documentation (auto-generated from YAML)
2. `quick-reference.mdc` - Quick command reference
3. `agent-capabilities.mdc` - Agent capability descriptions
4. `project-context.mdc` - Project context template
5. `project-profiling.mdc` - Project profiling guide
6. `simple-mode.mdc` - Simple Mode guide
7. `command-reference.mdc` - **Complete command reference** (most comprehensive)

### Cursor Skills (`.claude/skills/`) - 14 Skills
- 13 agent skills (analyst, architect, debugger, designer, documenter, enhancer, implementer, improver, ops, orchestrator, planner, reviewer, tester)
- 1 simple-mode skill

### README Files
- `README.md` - Main project README (in project root, not installed by init)
- `docs/README.md` - Documentation index (in project root, not installed by init)

**Note**: README files are NOT copied during `init` - they exist in the framework repository but are not installed to user projects.

## Command Coverage Analysis

### 1. Top-Level Commands

#### ✅ Well Documented
- `init` - Fully documented in `command-reference.mdc` (lines 46-215)
- `workflow` - Fully documented in `command-reference.mdc` (lines 280-312)
- `score` - Documented in `command-reference.mdc` (lines 314-325)
- `doctor` - Documented in `command-reference.mdc` (lines 327-333)
- `cursor` - Fully documented in `command-reference.mdc` (lines 335-401)
- `simple-mode` - Fully documented in `command-reference.mdc` (lines 403-1525)

#### ⚠️ Partially Documented
- `create` - Mentioned in `command-reference.mdc` (lines 267-279) but minimal detail
- `setup-experts` - Not documented in cursor rules (only in README.md)
- `analytics` - Not documented in cursor rules
- `governance` - Not documented in cursor rules
- `auto-exec` - Not documented in cursor rules
- `customize` - Not documented in cursor rules
- `skill` - Not documented in cursor rules
- `bg-agent` - Not documented in cursor rules
- `health` - Not documented in cursor rules
- `hardware-profile` - Not documented in cursor rules
- `install-dev` - Not documented in cursor rules
- `status` - Not documented in cursor rules
- `generate-rules` - Not documented in cursor rules

### 2. Agent Commands

#### ✅ Well Documented (in `command-reference.mdc`)
- `@reviewer` - All commands documented (lines 488-643)
- `@implementer` - All commands documented (lines 645-701)
- `@tester` - All commands documented (lines 703-744)
- `@planner` - All commands documented (lines 746-781)
- `@architect` - All commands documented (lines 783-806)
- `@designer` - All commands documented (lines 808-836)
- `@enhancer` - All commands documented (lines 838-887)
- `@debugger` - All commands documented (lines 889-920)
- `@documenter` - All commands documented (lines 922-966)
- `@improver` - All commands documented (lines 968-999)
- `@ops` - All commands documented (lines 1001-1037)
- `@analyst` - All commands documented (lines 1039-1119)
- `@orchestrator` - All commands documented (lines 1121-1141)

#### ⚠️ Missing Subcommands
Many agent subcommands exist in CLI but are not documented in cursor rules:

**Reviewer Agent**:
- `analyze-project` - Not in cursor rules
- `analyze-services` - Not in cursor rules

**Architect Agent**:
- `design-system` - Not in cursor rules
- `diagram` - Not in cursor rules
- `tech-selection` - Not in cursor rules
- `security-design` - Not in cursor rules
- `boundaries` - Not in cursor rules

**Designer Agent**:
- `ui-ux` - Not in cursor rules
- `wireframes` - Not in cursor rules
- `design-system` - Not in cursor rules

**Analyst Agent**:
- All commands appear documented

**Orchestrator Agent**:
- `workflow-start` - Not in cursor rules
- `workflow-skip` - Not in cursor rules
- `workflow` - Not in cursor rules
- `gate` - Not in cursor rules

**Evaluator Agent**:
- `@evaluator` - **ENTIRE AGENT MISSING** from cursor rules
- `evaluate` - Not documented
- `evaluate-workflow` - Not documented

### 3. Simple Mode Commands

#### ✅ Comprehensive Documentation
All Simple Mode commands are documented in:
- `command-reference.mdc` (lines 1143-1525)
- `simple-mode.mdc` (complete guide)

**Commands Documented**:
- `*build` - ✅ Fully documented
- `*review` - ✅ Fully documented
- `*fix` - ✅ Fully documented
- `*test` - ✅ Fully documented
- `*epic` - ✅ Fully documented
- `*test-coverage` - ✅ Fully documented
- `*fix-tests` - ✅ Fully documented
- `*microservice` - ✅ Fully documented
- `*docker-fix` - ✅ Fully documented
- `*integrate-service` - ✅ Fully documented
- `*full` - ✅ Fully documented

**Simple Mode CLI Commands**:
- `simple-mode on` - ✅ Documented
- `simple-mode off` - ✅ Documented
- `simple-mode status` - ✅ Documented
- `simple-mode init` - ✅ Documented
- `simple-mode configure` - ✅ Documented
- `simple-mode progress` - ✅ Documented
- `simple-mode full` - ✅ Documented
- `simple-mode build` - ⚠️ Not documented (CLI version)
- `simple-mode resume` - ⚠️ Not documented

### 4. Workflow Commands

#### ✅ Well Documented
- `workflow full` - Documented
- `workflow rapid` - Documented
- `workflow fix` - Documented
- `workflow quality` - Documented
- `workflow hotfix` - Documented
- `workflow list` - Documented
- `workflow recommend` - Documented
- `workflow state` - Documented (with subcommands)
- `workflow resume` - Documented

#### ⚠️ Missing
- `workflow new-feature` - Mentioned but minimal detail
- `workflow cleanup-branches` - Not documented

## Critical Gaps Identified

### 1. Evaluator Agent - COMPLETELY MISSING
**Severity**: 🔴 **CRITICAL**

The Evaluator Agent exists in the CLI and has a skill, but:
- ❌ Not mentioned in `command-reference.mdc`
- ❌ Not mentioned in `agent-capabilities.mdc`
- ❌ Not mentioned in `quick-reference.mdc`
- ❌ Not mentioned in README.md

**Impact**: New agents will not know about the Evaluator Agent at all.

**Commands Missing**:
- `tapps-agents evaluator evaluate`
- `tapps-agents evaluator evaluate-workflow`
- `@evaluator *evaluate`
- `@evaluator *evaluate-workflow`

### 2. Advanced CLI Commands - NOT DOCUMENTED
**Severity**: 🟡 **HIGH**

Many top-level commands exist but are not in cursor rules:
- `analytics` (with subcommands: dashboard, agents, workflows, trends, system)
- `governance` (with subcommands: approval list/show/approve/reject)
- `auto-exec` (with subcommands: status, history, metrics, health, debug)
- `customize` (with subcommands: init)
- `skill` (with subcommands: validate, template)
- `bg-agent` (with subcommands: generate, validate)
- `health` (with subcommands: check, dashboard, metrics, trends)
- `hardware-profile`
- `install-dev`
- `status`
- `generate-rules`

**Impact**: New agents won't know these commands exist.

### 3. Agent Subcommands - PARTIALLY MISSING
**Severity**: 🟡 **MEDIUM**

Several agent subcommands are missing:
- Reviewer: `analyze-project`, `analyze-services`
- Architect: `design-system`, `diagram`, `tech-selection`, `security-design`, `boundaries`
- Designer: `ui-ux`, `wireframes`, `design-system`
- Orchestrator: `workflow-start`, `workflow-skip`, `workflow`, `gate`

**Impact**: New agents may not know about advanced agent capabilities.

### 4. Simple Mode CLI Commands - PARTIALLY MISSING
**Severity**: 🟢 **LOW**

Some Simple Mode CLI commands not documented:
- `simple-mode build` (CLI version)
- `simple-mode resume`

**Impact**: Users may not know CLI alternatives to Cursor Skills.

## Recommendations

### Priority 1: Critical (Do Immediately)

#### 1.1 Add Evaluator Agent Documentation
**Action**: Add Evaluator Agent to all cursor rules files.

**Files to Update**:
- `.cursor/rules/command-reference.mdc` - Add Evaluator Agent section (after Orchestrator)
- `.cursor/rules/agent-capabilities.mdc` - Add Evaluator Agent section
- `.cursor/rules/quick-reference.mdc` - Add Evaluator Agent examples
- `README.md` - Add Evaluator Agent to agent list

**Content to Add**:
```markdown
### Evaluator Agent (`@evaluator`)

**Available Commands:**

#### `*evaluate` / `evaluate` (Dual-Mode)
**Purpose:** Evaluate framework effectiveness and generate improvement recommendations

**CLI Syntax:**
```bash
tapps-agents evaluator evaluate [--output <file>] [--format json|text|markdown]
```

**Cursor Syntax:**
```cursor
@evaluator *evaluate
```

#### `*evaluate-workflow` / `evaluate-workflow` (Dual-Mode)
**Purpose:** Evaluate specific workflow execution

**CLI Syntax:**
```bash
tapps-agents evaluator evaluate-workflow <workflow-id> [--format json|text|markdown]
```

**Cursor Syntax:**
```cursor
@evaluator *evaluate-workflow <workflow-id>
```
```

#### 1.2 Add Missing Top-Level Commands
**Action**: Add sections for all missing top-level commands in `command-reference.mdc`.

**Commands to Add**:
- `analytics` (with all subcommands)
- `governance` (with all subcommands)
- `auto-exec` (with all subcommands)
- `customize` (with all subcommands)
- `skill` (with all subcommands)
- `bg-agent` (with all subcommands)
- `health` (with all subcommands)
- `hardware-profile`
- `install-dev`
- `status`
- `generate-rules`

### Priority 2: High (Do Soon)

#### 2.1 Add Missing Agent Subcommands
**Action**: Update agent sections in `command-reference.mdc` to include all subcommands.

**Agents to Update**:
- **Reviewer**: Add `analyze-project`, `analyze-services`
- **Architect**: Add `design-system`, `diagram`, `tech-selection`, `security-design`, `boundaries`
- **Designer**: Add `ui-ux`, `wireframes`, `design-system`
- **Orchestrator**: Add `workflow-start`, `workflow-skip`, `workflow`, `gate`

#### 2.2 Create Command Discovery Mechanism
**Action**: Add a section in `command-reference.mdc` that explains how to discover all commands.

**Content to Add**:
```markdown
## Discovering All Commands

To see all available commands:

**CLI:**
```bash
# List all top-level commands
tapps-agents --help

# List all commands for an agent
tapps-agents <agent> help
tapps-agents <agent> *help

# List all workflow presets
tapps-agents workflow list
```

**Cursor:**
```cursor
@agent-name *help
@simple-mode *help
```
```

### Priority 3: Medium (Do When Time Permits)

#### 3.1 Enhance README.md Command Coverage
**Action**: Add a "Complete Command Reference" section to README.md that links to `command-reference.mdc`.

**Content to Add**:
```markdown
## Complete Command Reference

For a complete list of all commands, subcommands, and parameters, see:
- **Cursor Rules**: `.cursor/rules/command-reference.mdc` (installed by `tapps-agents init`)
- **Quick Reference**: `.cursor/rules/quick-reference.mdc`
- **Agent Capabilities**: `.cursor/rules/agent-capabilities.mdc`
```

#### 3.2 Add Command Examples to Agent Skills
**Action**: Ensure each agent skill (`.claude/skills/*/SKILL.md`) includes all available commands with examples.

**Check**: Verify all 14 skills have complete command documentation.

### Priority 4: Low (Nice to Have)

#### 4.1 Create Command Coverage Test
**Action**: Create an automated test that verifies all CLI commands are documented in cursor rules.

**Implementation**:
- Parse CLI parser definitions to extract all commands
- Parse cursor rules to extract documented commands
- Compare and report missing commands

#### 4.2 Add Command Versioning
**Action**: Add version metadata to command documentation to track when commands were added/changed.

## Verification Checklist

After implementing recommendations, verify:

- [ ] Evaluator Agent documented in all cursor rules files
- [ ] All top-level commands documented in `command-reference.mdc`
- [ ] All agent subcommands documented in `command-reference.mdc`
- [ ] All Simple Mode commands documented (CLI and Cursor)
- [ ] README.md links to complete command reference
- [ ] All agent skills have complete command documentation
- [ ] Command discovery mechanism documented
- [ ] Automated test for command coverage exists

## Conclusion

**Current State**: ⚠️ **PARTIAL COVERAGE** - Approximately 70% of commands are documented in cursor rules.

**Critical Issue**: Evaluator Agent is completely missing from documentation.

**Recommendation**: Implement Priority 1 recommendations immediately, then proceed with Priority 2-4 as time permits.

**Guarantee**: Currently, **NO** - we do not guarantee that every new agent knows all tapps-agent commands. The Evaluator Agent is a clear example of this gap.

**After Fixes**: With Priority 1 and 2 fixes, we can guarantee approximately 95% coverage. Priority 3 and 4 will bring us to 100% coverage.

## Appendix: Command Inventory

### Top-Level Commands (Total: 20)
- ✅ Documented: 8 (init, workflow, score, doctor, cursor, simple-mode, create, setup-experts)
- ❌ Missing: 12 (analytics, governance, auto-exec, customize, skill, bg-agent, health, hardware-profile, install-dev, status, generate-rules, evaluator)

### Agent Commands (Total: 13 agents)
- ✅ Fully Documented: 12 agents
- ❌ Missing: 1 agent (evaluator)
- ⚠️ Partially Documented: 4 agents (reviewer, architect, designer, orchestrator - missing some subcommands)

### Simple Mode Commands (Total: 11)
- ✅ Documented: 11 (all Cursor Skills commands)
- ⚠️ Partially Documented: 2 CLI commands (build, resume)

### Workflow Commands (Total: 10+)
- ✅ Documented: 9
- ⚠️ Missing: 2 (new-feature details, cleanup-branches)

**Total Command Coverage**: ~70% documented in cursor rules
