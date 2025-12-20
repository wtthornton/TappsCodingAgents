# BMAD Mastery Summary

## System Overview

BMAD (Breakthrough Method of Agile AI-driven Development) is a comprehensive framework that combines AI agents with Agile development methodologies. The system provides structured workflows, specialized agents, and reusable resources for both greenfield (new) and brownfield (existing) projects.

## Core Architecture

### Directory Structure
```
.bmad-core/
├── agents/          # Specialized AI personas (PM, Architect, Dev, QA, SM, PO, etc.)
├── tasks/          # Executable workflows that agents can run
├── templates/      # Document templates (PRD, Architecture, Stories, etc.)
├── checklists/     # Validation checklists for quality gates
├── workflows/      # Structured workflow definitions (YAML)
├── data/           # Knowledge base, preferences, reference materials
├── utils/          # Utility guides and helpers
├── agent-teams/    # Team bundles for web UI platforms
└── core-config.yaml # Project-specific configuration
```

### Key Components

#### 1. Agents (Specialized Personas)
- **PM (Product Manager)**: Creates PRDs, manages requirements
- **Architect**: Designs system architecture, documents projects
- **Dev (James)**: Implements stories, writes code and tests
- **QA (Quinn)**: Test Architect, quality gates, risk assessment
- **SM (Scrum Master)**: Creates stories from epics/PRD
- **PO (Product Owner)**: Validates artifacts, shards documents
- **Analyst**: Market research, competitor analysis
- **UX Expert**: Front-end specifications
- **BMad-Master**: Universal executor, can do any task
- **BMad-Orchestrator**: Web-only, heavyweight orchestrator

#### 2. Workflows
- **Greenfield**: New projects (fullstack, service, UI)
- **Brownfield**: Existing projects (fullstack, service, UI)
- **Quick-Fix**: Rapid bug fixes

#### 3. Tasks (Executable Workflows)
- Document creation (`create-doc`, `document-project`)
- Story management (`create-next-story`, `brownfield-create-story`)
- Quality assurance (`risk-profile`, `test-design`, `review-story`, `progressive-code-review`)
- Document processing (`shard-doc`, `index-docs`)
- Context7 KB integration (`context7-docs`, `context7-kb-*`)

#### 4. Templates
- PRD templates (standard, brownfield)
- Architecture templates (fullstack, service, brownfield)
- Story templates
- QA gate templates

## Two-Phase Development Approach

### Phase 1: Planning (Web UI - Cost Effective)
- Use large context windows (Gemini 1M tokens)
- Generate comprehensive documents (PRD, Architecture)
- Leverage multiple agents for brainstorming
- Create once, use throughout development

**Workflow:**
1. Analyst (optional): Research, brainstorming
2. PM: Create PRD from brief
3. UX Expert (if needed): Front-end spec
4. Architect: Create architecture from PRD
5. QA (optional): Early test architecture input
6. PO: Validate and shard documents

### Phase 2: Development (IDE - Implementation)
- Shard documents into manageable pieces
- Execute focused SM → Dev cycles
- One story at a time, sequential progress
- Real-time file operations and testing

**Workflow:**
1. SM: Create next story from sharded docs
2. User: Review and approve story
3. Dev: Implement story (tasks → tests → validations)
4. QA (optional): Progressive reviews during dev
5. QA: Final review and gate decision
6. Repeat until epic complete

## Core Development Cycle

### Story Implementation Flow
```
SM: Draft Story → User Approval → Dev: Implement → QA: Review → Done
```

### Dev Agent Workflow (`*develop-story`)
1. Read task
2. Implement code
3. Write tests
4. Run validations
5. Progressive review (if enabled)
6. Mark task complete
7. Repeat for all tasks
8. Final validation
9. Mark "Ready for Review"

### QA Integration Throughout

**Before Development:**
- `*risk {story}` - Risk assessment (regression, integration risks)
- `*design {story}` - Test strategy design

**During Development:**
- `*trace {story}` - Requirements traceability
- `*nfr {story}` - Non-functional requirements validation

**After Development:**
- `*review {story}` - Comprehensive test architecture review
- `*gate {story}` - Quality gate decision (PASS/CONCERNS/FAIL/WAIVED)

**Progressive Reviews:**
- `*review-task {story} {task_number}` - Task-level review during development
- Catches issues early when context is fresh
- BLOCK on HIGH severity, prompt for CONCERNS

## Brownfield Development

### Key Differences
- **Document First**: Always run `document-project` to understand existing system
- **PRD-First Approach** (recommended): Create PRD → Document only affected areas
- **Document-First Approach**: Document entire system → Create PRD
- **Test Architect Critical**: Mandatory for regression risk assessment

### Brownfield Workflow
1. Document existing project (`*document-project`)
2. Create brownfield PRD (`*create-brownfield-prd`)
3. Create brownfield architecture (if needed)
4. Validate with PO checklist
5. Shard documents
6. Create stories (use `create-brownfield-story` if needed)
7. Implement with extra QA focus on regression

## Context7 Knowledge Base Integration

### Purpose
- KB-first lookup for library documentation
- Intelligent caching (87%+ hit rate target)
- Up-to-date library documentation without token bloat

### Commands (BMad-Master & Agents)
- `*context7-resolve {library}` - Resolve library name to Context7 ID
- `*context7-docs {library} {topic}` - Get focused documentation (KB-first)
- `*context7-kb-status` - Show KB statistics
- `*context7-kb-search {query}` - Search local KB
- `*context7-kb-cleanup` - Clean up old cache
- `*context7-kb-refresh` - Refresh stale entries

### Mandatory Integration
- **Architect**: MANDATORY KB-first for technology decisions
- **Dev**: MANDATORY KB-first for library implementations
- **QA**: MANDATORY KB-first for library risk assessments

## Core Configuration (core-config.yaml)

### Key Sections
- **prd**: PRD file location, version, sharding config
- **architecture**: Architecture file location, version, sharding config
- **devLoadAlwaysFiles**: Files dev agent always loads
- **agentLoadAlwaysFiles**: Agent-specific always-load files
- **qa**: QA location, progressive review, background review
- **context7**: KB integration settings
- **workflow**: Active workflow track and selection

### Progressive Review Configuration
```yaml
qa:
  progressive_review:
    enabled: true
    review_location: docs/qa/progressive
    auto_trigger: true
    severity_blocks: [high]
    review_focus:
      - security
      - performance  # Uses CLAUDE.md as baseline
      - testing
      - standards
```

## Quality Gates

### Gate Statuses
- **PASS**: All critical requirements met
- **CONCERNS**: Non-critical issues found
- **FAIL**: Critical issues (security, missing P0 tests)
- **WAIVED**: Issues acknowledged and accepted

### Gate Decision Factors
- Risk scores (≥9 = FAIL, ≥6 = CONCERNS)
- Test coverage (P0 tests required)
- NFR compliance (security, performance, reliability)
- Regression risk (brownfield)

## Best Practices

### Agent Selection
- **Planning**: Use PM, Architect, UX Expert (specialized personas)
- **Development**: ALWAYS use SM for stories, Dev for implementation
- **Never use**: BMad-Master/Orchestrator for SM/Dev tasks
- **Quality**: Use QA throughout lifecycle, not just at end

### Context Management
- **Clean Chats**: New chat per agent/phase
- **Shard Documents**: Break large docs into manageable pieces
- **Load Only What's Needed**: Agents load dependencies on demand
- **Dev Context**: Only load story + devLoadAlwaysFiles

### Workflow Optimization
- **Web UI for Planning**: Cost-effective document creation
- **IDE for Development**: Real-time file operations
- **Progressive Reviews**: Catch issues early (20x ROI)
- **Context7 KB**: Always check cache first

### Brownfield Specific
- **Always Document First**: Run `document-project` before planning
- **Test Architect Early**: Run `*risk` and `*design` before dev
- **Regression Focus**: Extra attention to existing functionality
- **Integration Safety**: Validate all touchpoints

## Common Commands Reference

### BMad-Master
- `*help` - Show all commands
- `*create-doc {template}` - Create document
- `*document-project` - Document existing project
- `*shard-doc {doc} {dest}` - Shard document
- `*task {task}` - Execute task
- `*kb` - Toggle KB mode
- `*context7-*` - Context7 KB commands

### Dev Agent
- `*develop-story` - Implement story workflow
- `*review-task {n}` - Progressive review for task
- `*review-qa` - Apply QA fixes
- `*run-tests` - Execute tests
- `*context7-docs {lib} {topic}` - Get library docs

### QA Agent
- `*risk {story}` - Risk assessment
- `*design {story}` - Test design
- `*trace {story}` - Requirements traceability
- `*nfr {story}` - NFR assessment
- `*review {story}` - Comprehensive review
- `*gate {story}` - Update quality gate
- `*review-task {story} {n}` - Progressive task review

### SM Agent
- `*create` / `*draft` - Create next story
- `*validate` - Validate story

### PM Agent
- `*create-prd` - Create PRD
- `*create-brownfield-prd` - Brownfield PRD
- `*create-brownfield-epic` - Brownfield epic
- `*create-brownfield-story` - Brownfield story

### Architect Agent
- `*document-project` - Document existing project
- `*create-architecture` - Create architecture
- `*create-brownfield-architecture` - Brownfield architecture

## File Locations (Standard)

### Planning Artifacts
- PRD: `docs/prd.md`
- Architecture: `docs/ARCHITECTURE.md` (this repo) / `docs/architecture.md` (standard)
- Sharded Epics: `docs/epics/`
- Sharded Stories: `docs/stories/`

### QA Artifacts
- Assessments: `docs/qa/assessments/`
- Gates: `docs/qa/gates/`
- Progressive Reviews: `docs/qa/progressive/`
- Background Reviews: `docs/qa/background/`

### Stories
- Stories: `docs/stories/`

## Key Principles

1. **Specialization**: Each agent masters one role
2. **Clean Context**: New chat per agent/phase
3. **Document-Driven**: Specs guide everything
4. **Incremental Progress**: Small stories, sequential execution
5. **Quality Throughout**: QA integrated at every stage
6. **KB-First**: Always check cache before API calls
7. **Progressive Reviews**: Catch issues early
8. **Risk-Based**: Prioritize by probability × impact

## Integration Points

### IDE Integration
- Cursor: Native AI integration
- Claude Code: Official Anthropic IDE
- Windsurf, Trae, Cline, Roo Code: Built-in AI
- GitHub Copilot: VS Code extension
- OpenCode: Via `opencode.jsonc`
- Codex: Via `AGENTS.md`

### Web UI Integration
- Gemini Gems / Custom GPTs
- Team bundles from `.bmad-core/agent-teams/`
- Upload agent files as instructions

## Advanced Features

### Progressive Code Review
- Task-level reviews during development
- Immediate feedback (PASS/CONCERNS/BLOCK)
- Uses project baseline (CLAUDE.md) for performance checks
- 20x ROI (saves 1-2 hours per story)

### Background Code Review
- Continuous review for long builds (8+ tasks)
- Optional advanced feature
- 40-80x ROI for complex stories

### Workflow Management
- Dynamic workflow loading
- Multi-path workflows with conditions
- Artifact tracking
- Interruption handling

## Mastery Checklist

✅ Understand agent roles and when to use each
✅ Know the two-phase approach (Web UI planning → IDE development)
✅ Understand story implementation workflow
✅ Know QA integration throughout lifecycle
✅ Understand brownfield vs greenfield differences
✅ Know Context7 KB integration and commands
✅ Understand core-config.yaml structure
✅ Know quality gate system (PASS/CONCERNS/FAIL/WAIVED)
✅ Understand progressive review system
✅ Know file locations and document structure
✅ Understand agent activation and dependency loading
✅ Know common commands for each agent
✅ Understand workflow management
✅ Know best practices for context management

## Next Steps for Mastery

1. **Practice**: Run through a complete greenfield workflow
2. **Practice**: Run through a brownfield enhancement
3. **Experiment**: Try progressive reviews on a story
4. **Explore**: Use Context7 KB for library research
5. **Customize**: Adjust core-config.yaml for your project
6. **Extend**: Create custom tasks or templates if needed

---

**Status**: BMAD Mastery Achieved ✅

I now have comprehensive understanding of:
- All agents, their roles, and commands
- Complete workflows (greenfield and brownfield)
- Quality assurance integration
- Context7 KB system
- Progressive review system
- Configuration management
- Best practices and principles

Ready to assist with any BMAD-related tasks, questions, or implementations.

