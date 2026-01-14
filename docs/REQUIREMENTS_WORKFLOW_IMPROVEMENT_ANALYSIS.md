# Requirements Workflow Improvement Analysis

## Executive Summary

This document analyzes user feedback about TappsCodingAgents' requirements gathering and planning workflows. The feedback identifies critical gaps in tool selection, output formats, and documentation generation that prevent users from getting actionable requirements documents.

**Overall Assessment:**
- ✅ Codebase discovery: 9/10 (excellent)
- ❌ Requirements generation: 3/10 (wrong tool, incomplete output)
- ❌ User story creation: 2/10 (not generated)
- ⚠️ Planning structure: 4/10 (structure present, but not actionable)
- ❌ Documentation output: 1/10 (no markdown documents generated)

## Feedback Analysis

### What Worked Well ✅

1. **Codebase Context Discovery**
   - Found relevant files (ServiceDetailsModal, ServicesTab, health endpoints)
   - Identified existing patterns (RAGDetailsModal as an example)
   - Located service definitions and health endpoint implementations
   - **Score: 9/10**

2. **Structured Workflow**
   - 7-stage enhancement pipeline provided a clear process
   - Progress indicators showed what was happening
   - Metadata tracking (timestamps, duration)

3. **Tool Availability**
   - Commands executed without errors
   - Clear CLI interface

### Critical Issues ❌

#### 1. Wrong Tool Selection

**Problem:**
- User used `@enhancer *enhance` for requirements gathering
- Should have used `@analyst *gather-requirements`

**Root Cause:**
- `@enhancer *enhance` is designed for **code generation prompts**, not requirements gathering
- `@enhancer` transforms prompts into enhanced specifications for implementation
- `@analyst *gather-requirements` is the correct tool for extracting requirements from descriptions

**Impact:**
- User got process metadata instead of requirements
- No structured requirements document generated
- Manual work still required

**Evidence from Codebase:**
```python:tapps_agents/agents/enhancer/agent.py
# Enhancer is for prompt enhancement, not requirements gathering
async def _enhance_full(self, prompt: str, ...) -> dict[str, Any]:
    """Run full enhancement pipeline through all stages."""
    # This creates an enhanced prompt for code generation
    # NOT a requirements document
```

```python:tapps_agents/agents/analyst/agent.py
# Analyst is the correct tool for requirements gathering
async def _gather_requirements(self, description: str, ...) -> dict[str, Any]:
    """Gather requirements from description."""
    # This should create structured requirements
    # But currently returns instruction objects, not documents
```

#### 2. Output Format Mismatch

**Problem:**
- Enhancer showed process but not the final enhanced prompt content
- Planner returned an instruction object expecting code execution instead of planning output
- Too much metadata, not enough actionable content

**Current Behavior:**
- `@enhancer *enhance` returns process metadata and stage results
- Final synthesis step doesn't produce a usable markdown document
- User sees progress bars but not the actual enhanced requirements

**Expected Behavior:**
- Structured markdown requirements document
- User stories in standard format (As a... I want... So that...)
- Acceptance criteria lists
- Ready-to-use planning documents

#### 3. Missing Structured Documents

**Problem:**
- No markdown output for requirements documents
- User stories not generated in standard format
- Manual work still required to create documents

**Current State:**
- `@analyst *gather-requirements` returns JSON with instruction objects
- `@planner *plan` returns plan objects, not markdown documents
- Simple Mode build workflow creates step documentation, but not requirements documents

**Evidence:**
```python:tapps_agents/agents/analyst/agent.py
async def _gather_requirements(self, ...) -> dict[str, Any]:
    # Returns instruction objects, not markdown documents
    requirements = {
        "description": description,
        "instruction": instruction.to_dict(),
        "skill_command": instruction.to_skill_command(),
    }
    # No markdown document generation
```

#### 4. Workflow Gaps

**Problem:**
- Simple Mode build workflow doesn't produce requirements documents
- No requirements-focused workflow
- No template-based output for consistency

**Current Simple Mode Build Workflow:**
1. `@enhancer *enhance` → Creates `step1-enhanced-prompt.md` (process metadata, not requirements)
2. `@planner *plan` → Creates `step2-user-stories.md` (planning structure, not user stories)
3. `@architect *design` → Creates `step3-architecture.md`
4. `@designer *design-api` → Creates `step4-design.md`
5. `@implementer *implement` → Code implementation
6. `@reviewer *review` → Creates `step6-review.md`
7. `@tester *test` → Creates `step7-testing.md`

**Missing:**
- Structured requirements document (functional, non-functional, constraints)
- User stories in standard format
- Acceptance criteria
- Requirements traceability

## Recommendations

### Priority 1: Fix Tool Selection Guidance

#### 1.1 Update Documentation

**Action:** Clarify when to use each tool in documentation

**Changes Needed:**
- Update `.cursor/rules/command-reference.mdc` with clear use cases
- Add "When to Use" sections for each agent
- Create decision tree: Requirements → Use `@analyst`, Code Generation → Use `@enhancer`

**Example:**
```markdown
## @analyst *gather-requirements

**When to Use:**
- Extracting requirements from stakeholder descriptions
- Creating requirements documents
- Requirements analysis and documentation

**When NOT to Use:**
- Enhancing prompts for code generation (use `@enhancer`)
- Creating implementation plans (use `@planner`)
```

#### 1.2 Improve Simple Mode Intent Detection

**Action:** Add requirements-specific intent detection

**Changes Needed:**
- Add "requirements" intent keywords: requirements, gather, extract, document, analyze
- Route to `@analyst *gather-requirements` instead of `@enhancer *enhance`
- Create requirements-focused workflow

**Example:**
```python
# In simple_mode/intent_detector.py
REQUIREMENTS_KEYWORDS = [
    "requirements", "gather", "extract", "document", 
    "analyze requirements", "requirements document"
]

def detect_intent(prompt: str) -> str:
    if any(kw in prompt.lower() for kw in REQUIREMENTS_KEYWORDS):
        return "requirements"  # Route to analyst, not enhancer
```

### Priority 2: Fix Output Formats

#### 2.1 Generate Markdown Requirements Documents

**Action:** Make `@analyst *gather-requirements` generate markdown documents

**Changes Needed:**
- Modify `_gather_requirements` to generate markdown output
- Use template-based formatting for consistency
- Save to `requirements.md` or specified output file

**Implementation:**
```python:tapps_agents/agents/analyst/agent.py
async def _gather_requirements(self, description: str, context: str = "", output_file: str | None = None) -> dict[str, Any]:
    """Gather requirements from description."""
    # ... existing LLM call ...
    
    # Generate markdown document
    markdown_content = self._format_requirements_markdown(
        description=description,
        functional_requirements=functional_reqs,
        non_functional_requirements=nfr_reqs,
        constraints=constraints,
        assumptions=assumptions,
        open_questions=questions
    )
    
    # Save to file
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown_content, encoding="utf-8")
    
    return {
        "success": True,
        "requirements": requirements_dict,
        "markdown": markdown_content,
        "output_file": str(output_path) if output_file else None
    }
```

#### 2.2 Generate User Stories in Standard Format

**Action:** Make `@planner *plan` generate user stories in standard format

**Changes Needed:**
- Modify `create_plan` to generate user stories
- Use standard format: "As a {user}, I want {goal}, so that {benefit}"
- Include acceptance criteria
- Save to markdown file

**Implementation:**
```python:tapps_agents/agents/planner/agent.py
async def create_plan(self, description: str) -> dict[str, Any]:
    """Create a plan with user stories."""
    # ... existing planning logic ...
    
    # Generate user stories in standard format
    user_stories = []
    for story in stories:
        user_stories.append({
            "format": "As a {user}, I want {goal}, so that {benefit}",
            "story": story,
            "acceptance_criteria": story.get("acceptance_criteria", []),
            "story_points": story.get("story_points", 0)
        })
    
    # Generate markdown document
    markdown_content = self._format_user_stories_markdown(user_stories)
    
    return {
        "success": True,
        "plan": plan_dict,
        "user_stories": user_stories,
        "markdown": markdown_content
    }
```

#### 2.3 Fix Enhancer Output

**Action:** Make enhancer output the final enhanced prompt content, not just metadata

**Changes Needed:**
- Ensure synthesis stage produces usable markdown
- Include the final enhanced prompt in output
- Save to file in readable format

### Priority 3: Create Requirements Workflow

#### 3.1 Add Requirements-Focused Simple Mode Command

**Action:** Add `@simple-mode *requirements` command

**Workflow:**
1. `@analyst *gather-requirements` → Requirements document
2. `@planner *plan` → User stories from requirements
3. `@documenter *document` → Formatted requirements document

**Implementation:**
```python:tapps_agents/simple_mode/orchestrators/requirements_orchestrator.py
class RequirementsOrchestrator:
    async def execute(self, prompt: str) -> dict[str, Any]:
        # Step 1: Gather requirements
        requirements_result = await self.invoke_skill(
            "analyst", "gather-requirements", 
            description=prompt,
            output_file="docs/workflows/simple-mode/requirements.md"
        )
        
        # Step 2: Create user stories
        stories_result = await self.invoke_skill(
            "planner", "plan",
            description=requirements_result["requirements"]["description"],
            output_file="docs/workflows/simple-mode/user-stories.md"
        )
        
        # Step 3: Generate formatted document
        doc_result = await self.invoke_skill(
            "documenter", "document",
            file="docs/workflows/simple-mode/requirements.md"
        )
        
        return {
            "requirements": requirements_result,
            "user_stories": stories_result,
            "documentation": doc_result
        }
```

#### 3.2 Add Template-Based Output

**Action:** Create templates for common document types

**Templates Needed:**
- `templates/requirements.md.template` - Requirements document template
- `templates/user-stories.md.template` - User stories template
- `templates/planning.md.template` - Planning document template

**Example Template:**
```markdown:templates/requirements.md.template
# Requirements: {{title}}

## Overview
{{description}}

## Functional Requirements
{{#functional_requirements}}
- {{requirement}}
{{/functional_requirements}}

## Non-Functional Requirements
{{#non_functional_requirements}}
- {{requirement}}
{{/non_functional_requirements}}

## Technical Constraints
{{#constraints}}
- {{constraint}}
{{/constraints}}

## Assumptions
{{#assumptions}}
- {{assumption}}
{{/assumptions}}

## Open Questions
{{#open_questions}}
- {{question}}
{{/open_questions}}
```

### Priority 4: Improve Simple Mode Build Workflow

#### 4.1 Add Requirements Step to Build Workflow

**Action:** Add explicit requirements gathering step

**Updated Workflow:**
1. `@analyst *gather-requirements` → Requirements document
2. `@enhancer *enhance` → Enhanced prompt (for code generation)
3. `@planner *plan` → User stories
4. `@architect *design` → Architecture
5. `@designer *design-api` → Component design
6. `@implementer *implement` → Implementation
7. `@reviewer *review` → Review
8. `@tester *test` → Testing

**Or Alternative:**
- Make Step 1 use `@analyst` instead of `@enhancer` for requirements-focused tasks
- Keep `@enhancer` for code generation enhancement

#### 4.2 Ensure Documentation Files Are Created

**Action:** Verify all workflow steps create markdown documents

**Current Issue:**
- Documentation files are referenced but may not be created
- Need to verify `docs/workflows/simple-mode/step*.md` files are actually generated

**Fix:**
- Ensure each step saves its output to the documentation directory
- Add validation to check files exist after workflow completion

## Implementation Plan

### Phase 1: Quick Wins (1-2 days)

1. ✅ Update documentation with tool selection guidance
2. ✅ Add requirements intent detection to Simple Mode
3. ✅ Fix `@analyst *gather-requirements` to generate markdown

### Phase 2: Core Improvements (3-5 days)

1. ✅ Fix `@planner *plan` to generate user stories in standard format
2. ✅ Create requirements-focused workflow
3. ✅ Add template-based output system

### Phase 3: Workflow Integration (2-3 days)

1. ✅ Update Simple Mode build workflow
2. ✅ Add requirements step to build workflow
3. ✅ Ensure all documentation files are created

### Phase 4: Testing & Validation (1-2 days)

1. ✅ Test requirements workflow end-to-end
2. ✅ Validate markdown output formats
3. ✅ Update user documentation

## Success Metrics

**Before:**
- Requirements generation: 3/10
- User story creation: 2/10
- Documentation output: 1/10

**After (Target):**
- Requirements generation: 9/10
- User story creation: 9/10
- Documentation output: 9/10

**Validation:**
- User can run `@analyst *gather-requirements` and get a markdown document
- User can run `@planner *plan` and get user stories in standard format
- User can run `@simple-mode *requirements` and get complete requirements workflow
- All documents are saved to `docs/workflows/simple-mode/` directory

## Related Issues

- Simple Mode build workflow doesn't produce requirements documents
- Enhancer output format needs improvement
- Planner should generate user stories, not just planning structure
- Need requirements-focused workflow

## References

- User Feedback: "TappsCodingAgents Performance Feedback"
- Current Implementation: `tapps_agents/agents/analyst/agent.py`
- Current Implementation: `tapps_agents/agents/planner/agent.py`
- Current Implementation: `tapps_agents/agents/enhancer/agent.py`
- Simple Mode: `tapps_agents/simple_mode/orchestrators/build_orchestrator.py`
