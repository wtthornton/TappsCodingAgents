# Simple Mode Build Command - Call Tree and Prompt Enhancements

## Command
```
@simple-mode *build "create an amazing modern dark html page that features 2025 fun and cool features"
```

## Overview

This document traces the complete execution flow and prompt enhancement pipeline when executing a `*build` command through Simple Mode. The build workflow orchestrates multiple agents in sequence, starting with prompt enhancement and proceeding through planning, architecture, design, and implementation.

---

## Call Tree

```
@simple-mode *build "create an amazing modern dark html page..."
    │
    ├─> Simple Mode Skill Handler
    │   └─> Intent Parser
    │       └─> Detects: IntentType.BUILD
    │       └─> Extracts: description = "create an amazing modern dark html page..."
    │
    ├─> SimpleModeHandler.handle()
    │   └─> Routes to BuildOrchestrator
    │
    └─> BuildOrchestrator.execute()
        │
        ├─> STEP 1: Prompt Enhancement (Full Enhancement)
        │   └─> EnhancerAgent.run("enhance")
        │       │
        │       ├─> Stage 1: Analysis
        │       │   └─> _stage_analysis()
        │       │       └─> Creates GenericInstruction
        │       │       └─> Analyzes: intent, domains, scope, workflow type, technologies, complexity
        │       │
        │       ├─> Stage 2: Requirements
        │       │   └─> _stage_requirements()
        │       │       ├─> AnalystAgent.run("gather-requirements")
        │       │       │
        │       │       ├─> Expert Registry Consultation (CONDITIONAL)
        │       │       │   └─> IF self.expert_registry exists AND domains detected:
        │       │       │       ├─> For each domain in analysis["domains"]:
        │       │       │       │   └─> expert_registry.consult(query, domain, include_all=True)
        │       │       │       │       ├─> Expert.run("consult") → Uses RAG internally
        │       │       │       │       │   ├─> RAG Knowledge Base Query (CONDITIONAL)
        │       │       │       │       │   │   └─> IF expert.rag_enabled:
        │       │       │       │       │   │       ├─> VectorKnowledgeBase (FAISS) OR
        │       │       │       │       │   │       └─> SimpleKnowledgeBase (fallback)
        │       │       │       │       │   │       └─> knowledge_base.get_context(query)
        │       │       │       │       │   └─> Returns: answer, confidence, sources
        │       │       │       │       └─> Weighted aggregation (Primary 51%, Others 49%)
        │       │       │       └─> Returns: expert_consultations dict
        │       │       │   └─> ELSE: expert_consultations = {} (empty)
        │       │       │
        │       │       └─> Returns: functional_requirements, non_functional_requirements,
        │       │                    technical_constraints, assumptions, expert_consultations
        │       │
        │       ├─> Stage 3: Architecture
        │       │   └─> _stage_architecture()
        │       │       └─> ArchitectAgent.run("design-system")
        │       │           └─> ArchitectAgent._design_system()
        │       │               │
        │       │               ├─> Expert Consultation (CONDITIONAL)
        │       │               │   └─> IF self.expert_registry exists:
        │       │               │       ├─> _consult_experts_for_design()
        │       │               │       │   ├─> Consult "software-architecture" expert
        │       │               │       │   │   └─> expert_registry.consult() → Uses RAG internally
        │       │               │       │   ├─> Consult "performance-optimization" expert
        │       │               │       │   │   └─> expert_registry.consult() → Uses RAG internally
        │       │               │       │   └─> Consult "security" expert
        │       │               │       │       └─> expert_registry.consult() → Uses RAG internally
        │       │               │       └─> Returns: expert_guidance dict
        │       │               │   └─> ELSE: expert_guidance = {} (empty)
        │       │               │
        │       │               ├─> Context7 Documentation (CONDITIONAL)
        │       │               │   └─> IF self.context7 exists:
        │       │               │       ├─> _get_context7_docs_for_design()
        │       │               │       │   ├─> IF context7.should_use_context7() returns True:
        │       │               │       │   │   ├─> context7.search_libraries(requirements, limit=5)
        │       │               │       │   │   └─> For each library:
        │       │               │       │   │       └─> context7.get_documentation(lib_name, topic="architecture")
        │       │               │       │   └─> Returns: context7_docs dict
        │       │               │       └─> ELSE: context7_docs = {} (empty)
        │       │               │
        │       │               └─> Build prompt with expert_section + context7_section
        │       │               └─> Returns: system_design, design_patterns, technology_recommendations,
        │       │                            architecture_guidance
        │       │
        │       ├─> Stage 4: Codebase Context
        │       │   └─> _stage_codebase_context()
        │       │       └─> Analyzes codebase for related files and patterns
        │       │       └─> Injects relevant codebase context
        │       │       └─> Returns: related_files, existing_patterns, codebase_context
        │       │
        │       ├─> Stage 5: Quality Standards
        │       │   └─> _stage_quality()
        │       │       └─> Defines security, testing, and quality thresholds
        │       │       └─> Returns: security_requirements, testing_requirements, 
        │       │                    performance_requirements, quality_thresholds
        │       │
        │       ├─> Stage 6: Implementation Strategy
        │       │   └─> _stage_implementation()
        │       │       └─> Creates task breakdown and implementation order
        │       │       └─> Returns: task_breakdown, implementation_order, dependencies, 
        │       │                    estimated_effort
        │       │
        │       └─> Stage 7: Synthesis
        │           └─> _stage_synthesis()
        │               └─> Combines all stages into enhanced prompt
        │               └─> Returns: enhanced_prompt (markdown format)
        │
        └─> STEP 2: Build Workflow Execution
            └─> MultiAgentOrchestrator.execute_parallel()
                │
                ├─> Agent Task 1: Planner
                │   └─> PlannerAgent.run("create-story")
                │       └─> Args: {"description": enhanced_prompt}
                │
                ├─> Agent Task 2: Architect
                │   └─> ArchitectAgent.run("design")
                │       └─> Args: {"specification": enhanced_prompt}
                │
                ├─> Agent Task 3: Designer
                │   └─> DesignerAgent.run("design-api")
                │       └─> Args: {"specification": enhanced_prompt}
                │
                └─> Agent Task 4: Implementer
                    └─> ImplementerAgent.run("implement")
                        └─> Args: {"specification": enhanced_prompt}
```

---

## Prompt Enhancement Stages

### Stage 1: Analysis

**Purpose**: Detect prompt intent, scope, domains, and workflow type

**Implementation**: `EnhancerAgent._stage_analysis()`

**Prompt Template**:
```
Analyze the following prompt and extract:
1. Intent (feature, bug fix, refactor, documentation, etc.)
2. Detected domains (security, user-management, payments, etc.)
3. Estimated scope (small: 1-2 files, medium: 3-5 files, large: 6+ files)
4. Recommended workflow type (greenfield, brownfield, quick-fix)
5. Key technologies mentioned
6. Complexity level (low, medium, high)

Prompt: {original_prompt}

Provide structured JSON response.
```

**Output Structure**:
```json
{
  "original_prompt": "create an amazing modern dark html page...",
  "instruction": {
    "agent_name": "enhancer",
    "command": "analyze-prompt",
    "prompt": "...",
    "parameters": {
      "original_prompt": "..."
    }
  },
  "skill_command": "@enhancer *analyze-prompt ..."
}
```

**Expected Analysis for Example Prompt**:
- **Intent**: Feature (frontend/UI development)
- **Domains**: frontend, web-design, ui/ux
- **Scope**: Small-Medium (1-3 files: HTML, CSS, JS)
- **Workflow Type**: Greenfield
- **Technologies**: HTML5, CSS3, JavaScript, modern web APIs
- **Complexity**: Medium (requires modern features, dark theme, 2025 features)

---

### Stage 2: Requirements

**Purpose**: Gather functional/non-functional requirements with Industry Expert consultation

**Implementation**: `EnhancerAgent._stage_requirements()`

**Sub-Agents Involved**:
1. **AnalystAgent**: Gathers requirements
2. **Expert Registry**: Consults domain experts (if available)

**Analyst Agent Call**:
```python
await self.analyst.run(
    "gather-requirements",
    description=prompt,
    context=analysis.get("analysis", "")
)
```

**Expert Consultation Flow** (if domains detected):
```python
for domain in domains:
    consultation = await self.expert_registry.consult(
        query=f"What are the domain-specific requirements, business rules, and best practices for: {prompt}",
        domain=domain,
        include_all=True
    )
```

**Output Structure**:
```json
{
  "functional_requirements": [
    "Dark theme implementation",
    "Modern UI/UX design",
    "2025 web features integration",
    "Responsive design",
    "Interactive elements"
  ],
  "non_functional_requirements": [
    "Performance optimization",
    "Cross-browser compatibility",
    "Accessibility (WCAG 2.1)",
    "Mobile responsiveness"
  ],
  "technical_constraints": [
    "Modern browser support required",
    "No legacy IE support needed"
  ],
  "assumptions": [
    "Target audience: modern web users",
    "Progressive enhancement approach"
  ],
  "expert_consultations": {
    "frontend": {
      "weighted_answer": "...",
      "confidence": 0.85,
      "agreement_level": 0.80,
      "primary_expert": "expert-frontend",
      "sources": [...]
    }
  },
  "requirements_analysis": "..."
}
```

**Expert Consultation Details**:
- **Primary Expert**: expert-frontend (51% weight)
- **Secondary Experts**: expert-ui-ux (24.5%), expert-web-performance (24.5%)
- **Weighted Consensus**: Combines expert opinions with weighted aggregation
- **Confidence**: Measures certainty of recommendations
- **Agreement Level**: Measures consensus among experts

---

### Stage 3: Architecture

**Purpose**: Provide system design guidance and patterns

**Implementation**: `EnhancerAgent._stage_architecture()`

**Architect Agent Call**:
```python
await self.architect.run(
    "design-system",
    requirements=prompt,
    context=json.dumps(requirements, indent=2)
)
```

**Output Structure**:
```json
{
  "system_design": {
    "architecture_type": "Single Page Application (SPA)",
    "components": [
      "HTML5 structure",
      "CSS3 styling with CSS variables",
      "JavaScript modules",
      "Modern web APIs integration"
    ],
    "patterns": [
      "Component-based architecture",
      "Progressive enhancement",
      "Mobile-first design"
    ]
  },
  "design_patterns": [
    "Dark theme pattern",
    "Responsive grid system",
    "Component composition"
  ],
  "technology_recommendations": [
    "HTML5 semantic elements",
    "CSS Grid and Flexbox",
    "CSS Custom Properties (variables)",
    "Modern JavaScript (ES6+)",
    "Web APIs: Intersection Observer, Web Animations API",
    "CSS: backdrop-filter, clip-path, gradients"
  ],
  "architecture_guidance": "Design a modern single-page HTML application with dark theme, utilizing CSS Grid for layout, CSS variables for theming, and modern JavaScript for interactivity. Implement progressive enhancement and ensure accessibility."
}
```

---

### Stage 4: Codebase Context

**Purpose**: Inject relevant codebase context and related files

**Implementation**: `EnhancerAgent._stage_codebase_context()`

**Process**:
- Analyzes codebase for related files and patterns
- Detects existing code patterns and conventions
- Identifies cross-references and dependencies
- Injects relevant codebase context into enhanced prompt

**Output Structure**:
```json
{
  "related_files": [
    "path/to/related/file.py",
    "path/to/another/file.py"
  ],
  "existing_patterns": [
    "Pattern: Authentication middleware",
    "Pattern: Error handling decorator"
  ],
  "codebase_context": "The codebase uses FastAPI with async/await patterns...",
  "cross_references": {
    "auth.py": ["middleware.py", "routes.py"],
    "models.py": ["database.py", "schemas.py"]
  }
}
```

---

### Stage 5: Quality Standards

**Purpose**: Define security, testing, and quality thresholds

**Implementation**: `EnhancerAgent._stage_quality()`

**Process**:
- Defines security requirements based on domain and context
- Establishes testing requirements (unit, integration, e2e)
- Sets performance requirements and benchmarks
- Defines code quality thresholds (complexity, coverage, etc.)

**Output Structure**:
```json
{
  "security_requirements": [
    "Input validation required",
    "SQL injection prevention",
    "XSS protection",
    "Authentication required"
  ],
  "testing_requirements": {
    "unit_tests": "Minimum 80% coverage",
    "integration_tests": "All API endpoints",
    "e2e_tests": "Critical user flows"
  },
  "performance_requirements": {
    "response_time": "< 200ms for API endpoints",
    "throughput": "Handle 1000 req/sec",
    "resource_usage": "Memory < 512MB"
  },
  "quality_thresholds": {
    "complexity": "Max cyclomatic complexity: 10",
    "coverage": "Minimum 80%",
    "maintainability_index": "> 70"
  }
}
```

---

### Stage 6: Implementation Strategy

**Purpose**: Create task breakdown and implementation order

**Implementation**: `EnhancerAgent._stage_implementation()`

**Process**:
- Breaks down implementation into discrete tasks
- Orders tasks based on dependencies
- Estimates effort for each task
- Identifies critical path and blockers

**Output Structure**:
```json
{
  "task_breakdown": [
    {
      "task_id": "task-1",
      "description": "Create database models",
      "dependencies": [],
      "estimated_effort": "2 hours",
      "priority": "high"
    },
    {
      "task_id": "task-2",
      "description": "Implement authentication endpoints",
      "dependencies": ["task-1"],
      "estimated_effort": "4 hours",
      "priority": "high"
    }
  ],
  "implementation_order": ["task-1", "task-2", "task-3"],
  "dependencies": {
    "task-2": ["task-1"],
    "task-3": ["task-1", "task-2"]
  },
  "estimated_effort": {
    "total": "16 hours",
    "by_priority": {
      "high": "8 hours",
      "medium": "6 hours",
      "low": "2 hours"
    }
  },
  "critical_path": ["task-1", "task-2", "task-5"]
}
```

---

### Stage 7: Synthesis

**Purpose**: Combine all stages into final enhanced prompt

**Implementation**: `EnhancerAgent._stage_synthesis()`

**Synthesis Prompt Template**:
```
Synthesize an enhanced prompt from the following analysis:

Original Prompt: {prompt}

Analysis: {json.dumps(stages.get('analysis', {}), indent=2)}
Requirements: {json.dumps(stages.get('requirements', {}), indent=2)}
Architecture: {json.dumps(stages.get('architecture', {}), indent=2)}
Quality: {json.dumps(stages.get('quality', {}), indent=2)}
Implementation: {json.dumps(stages.get('implementation', {}), indent=2)}

Create a comprehensive, context-aware enhanced prompt that includes all relevant information.
```

**Output Format**: Markdown (for Quick Enhancement)

**Example Enhanced Prompt Output**:
```markdown
# Enhanced Prompt: Create an Amazing Modern Dark HTML Page

## Metadata
- **Created**: 2025-01-XX...
- **Intent**: Feature (frontend/UI development)
- **Domain**: frontend, web-design, ui/ux
- **Scope**: Small-Medium (1-3 files)
- **Workflow**: Greenfield
- **Complexity**: Medium

## Requirements

### Functional Requirements
- Dark theme implementation with modern aesthetics
- Responsive design for all device sizes
- Integration of 2025 web features (CSS Grid, modern APIs)
- Interactive and engaging user experience
- Performance optimization

### Non-Functional Requirements
- Cross-browser compatibility (modern browsers)
- Accessibility compliance (WCAG 2.1)
- Mobile-first responsive design
- Fast load times and smooth animations

### Domain Context (from Industry Experts)

#### Frontend Domain
**Confidence**: 85%
**Agreement**: 80%
**Primary Expert**: expert-frontend

**Recommendations**:
- Use CSS Custom Properties for theming
- Implement dark mode with proper contrast ratios
- Leverage modern CSS features: Grid, Flexbox, backdrop-filter
- Use Intersection Observer for scroll animations
- Implement progressive enhancement

## Architecture Guidance

### System Design
- **Type**: Single Page Application (SPA)
- **Architecture**: Component-based, progressive enhancement
- **Pattern**: Mobile-first responsive design

### Technology Stack
- HTML5 semantic elements
- CSS3 with CSS Variables for theming
- Modern JavaScript (ES6+)
- Web APIs: Intersection Observer, Web Animations API
- CSS Features: Grid, Flexbox, backdrop-filter, clip-path, gradients

### Design Patterns
- Dark theme pattern with CSS variables
- Responsive grid system
- Component composition
- Progressive enhancement

## Implementation Strategy

1. Create HTML5 structure with semantic elements
2. Implement CSS with dark theme using CSS variables
3. Add modern CSS features (Grid, Flexbox, animations)
4. Integrate JavaScript for interactivity
5. Add 2025 web features (Intersection Observer, Web Animations API)
6. Ensure accessibility and responsive design
7. Optimize performance
```

---

## Build Workflow Execution

After prompt enhancement, the enhanced prompt is passed to the MultiAgentOrchestrator which coordinates the following agents:

### Agent 1: Planner

**Command**: `create-story`
**Input**: Enhanced prompt (markdown)
**Purpose**: Create user stories and task breakdown
**Output**: User stories, acceptance criteria, task list

### Agent 2: Architect

**Command**: `design`
**Input**: Enhanced prompt (markdown)
**Purpose**: Design system architecture
**Output**: Architecture diagrams, component structure, technology decisions

### Agent 3: Designer

**Command**: `design-api`
**Input**: Enhanced prompt (markdown)
**Purpose**: Design API contracts and data models
**Output**: API specifications, data models, interface contracts

**Note**: For HTML page creation, this may focus on component interfaces and data structures

### Agent 4: Implementer

**Command**: `implement`
**Input**: Enhanced prompt (markdown)
**Purpose**: Generate actual code
**Output**: Implementation files (HTML, CSS, JavaScript)

---

## Complete Flow Summary

1. **User Input**: `@simple-mode *build "create an amazing modern dark html page..."`

2. **Intent Parsing**: Simple Mode detects BUILD intent

3. **Orchestrator Selection**: Routes to BuildOrchestrator

4. **Prompt Enhancement** (Full Enhancement - All 7 Stages):
   - **Analysis**: Intent, domains, scope, workflow type
   - **Requirements**: Functional/NFR + Expert consultation
   - **Architecture**: Design patterns, technology recommendations
   - **Codebase Context**: Related files, existing patterns, codebase context
   - **Quality Standards**: Security, testing, performance, quality thresholds
   - **Implementation Strategy**: Task breakdown, implementation order, dependencies
   - **Synthesis**: Combined enhanced prompt

5. **Build Workflow**:
   - **Planner**: Creates user stories
   - **Architect**: Designs system architecture
   - **Designer**: Creates API/component contracts
   - **Implementer**: Generates code

6. **Result**: Complete implementation with enhanced context

---

## Enhancement Modes

### Full Enhancement (Used by BuildOrchestrator)

**Stages**: All 7 stages
- Analysis → Requirements → Architecture → Codebase Context → Quality Standards → Implementation Strategy → Synthesis
**Duration**: Comprehensive (all stages)
**Use Case**: Build workflow (comprehensive context and quality)

**Stages Included**:
1. **Analysis**: Intent, domains, scope, workflow type
2. **Requirements**: Functional/NFR + Expert consultation
3. **Architecture**: Design patterns, technology recommendations
4. **Codebase Context**: Related files, existing patterns, codebase context
5. **Quality Standards**: Security, testing, performance, quality thresholds
6. **Implementation Strategy**: Task breakdown, implementation order, dependencies
7. **Synthesis**: Combined enhanced prompt

### Quick Enhancement (Alternative Mode)

**Stages**: Analysis → Requirements → Architecture → Synthesis
**Duration**: Faster (4 stages)
**Use Case**: Standalone enhancement, quick iterations, initial exploration

**Note**: Quick Enhancement is available but not used by BuildOrchestrator. BuildOrchestrator uses Full Enhancement for comprehensive context.

---

## Key Files and Locations

### Core Implementation
- **Simple Mode Handler**: `tapps_agents/simple_mode/nl_handler.py`
- **Build Orchestrator**: `tapps_agents/simple_mode/orchestrators/build_orchestrator.py`
- **Enhancer Agent**: `tapps_agents/agents/enhancer/agent.py`
- **Intent Parser**: `tapps_agents/simple_mode/intent_parser.py`

### Documentation
- **Simple Mode Guide**: `docs/SIMPLE_MODE_GUIDE.md`
- **Enhancer Agent Docs**: `docs/ENHANCER_AGENT.md`
- **Simple Mode Rule**: `tapps_agents/resources/cursor/rules/simple-mode.mdc`
- **Simple Mode Skill**: `tapps_agents/resources/claude/skills/simple-mode/SKILL.md`

### Workflows
- **Prompt Enhancement Workflow**: `workflows/prompt-enhancement.yaml`

---

## Session Management

Enhancement sessions are saved to `.tapps-agents/sessions/`:
- **Session ID**: 8-character hash
- **Format**: JSON
- **Contents**: All stage outputs, metadata, timestamps
- **Resume**: Can resume interrupted enhancements

---

## Notes

1. **Full Enhancement**: BuildOrchestrator uses `enhance` (full enhancement) for comprehensive context, including all 7 stages: analysis, requirements, architecture, codebase context, quality standards, implementation strategy, and synthesis.

2. **Fallback Behavior**: If enhancement fails, BuildOrchestrator continues with the original prompt to ensure build process completes.

3. **Parallel Execution**: MultiAgentOrchestrator can execute some agent tasks in parallel (max_parallel=2).

4. **Expert Consultation**: Only occurs if Expert Registry is available and domains are detected in the analysis stage.

5. **Output Format**: Quick enhancement returns markdown format, which is then passed to subsequent agents.

---

## Why Experts, RAG, and Context7 May Not Appear

### Expert Consultation Conditions

**Experts ARE called, but conditionally:**

1. **Expert Registry Initialization** (in `EnhancerAgent.activate()`):
   - **Condition**: `.tapps-agents/domains.md` file must exist
   - **Code**: Lines 98-108 in `tapps_agents/agents/enhancer/agent.py`
   - **If missing**: `self.expert_registry = None`, no expert consultation occurs

2. **Domain Detection** (in `_stage_requirements()`):
   - **Condition**: Analysis stage must detect domains in `analysis.get("domains", [])`
   - **Code**: Lines 674-699 in `tapps_agents/agents/enhancer/agent.py`
   - **If no domains**: Expert consultation loop is skipped

3. **Architect Agent Expert Consultation**:
   - **Condition**: `ArchitectAgent` must have `self.expert_registry` initialized
   - **Code**: Lines 161-209 in `tapps_agents/agents/architect/agent.py`
   - **If missing**: Expert guidance is empty

### RAG Usage Conditions

**RAG IS used, but it's hidden inside expert consultation:**

1. **RAG is Internal to Experts**:
   - When `expert_registry.consult()` is called, it internally calls `expert.run("consult")`
   - Each expert uses its own RAG knowledge base if `rag_enabled=True`
   - **Code**: `tapps_agents/experts/base_expert.py` lines 318-362
   - **RAG Backends**: VectorKnowledgeBase (FAISS) or SimpleKnowledgeBase (fallback)

2. **RAG Initialization** (in `BaseExpert._initialize_rag()`):
   - **Condition**: Expert config must have `rag_enabled=True`
   - **Code**: Lines 96-180 in `tapps_agents/experts/base_expert.py`
   - **If disabled**: Expert uses default knowledge without RAG

3. **Knowledge Base Location**:
   - **Path**: `.tapps-agents/experts/{domain}/knowledge/`
   - **If empty**: RAG queries return no results, but consultation still occurs

### Context7 Usage Conditions

**Context7 IS called, but conditionally:**

1. **Context7 Initialization** (in `ArchitectAgent`):
   - **Condition**: `ArchitectAgent` must have `self.context7` initialized
   - **Code**: Lines 231-258 in `tapps_agents/agents/architect/agent.py`
   - **If missing**: Context7 documentation lookup is skipped

2. **Context7 Decision** (`should_use_context7()`):
   - **Condition**: Context7 helper must determine it's appropriate to use
   - **Code**: Line 240 in `tapps_agents/agents/architect/agent.py`
   - **If False**: Context7 documentation lookup is skipped

3. **Library Detection**:
   - **Condition**: Must detect library names in requirements text
   - **Code**: Lines 244-256 in `tapps_agents/agents/architect/agent.py`
   - **If no libraries detected**: No Context7 docs retrieved

### Summary: Why They Don't Appear

**Experts don't appear if:**
- ❌ `.tapps-agents/domains.md` doesn't exist
- ❌ No domains detected in analysis stage
- ❌ Expert registry fails to initialize

**RAG doesn't appear if:**
- ❌ Experts aren't consulted (see above)
- ❌ Expert config has `rag_enabled=False`
- ❌ Knowledge base directory is empty
- ❌ RAG initialization fails (falls back gracefully)

**Context7 doesn't appear if:**
- ❌ Context7 helper not initialized in ArchitectAgent
- ❌ `should_use_context7()` returns False
- ❌ No library names detected in requirements
- ❌ Context7 API key not configured

### How to Ensure They Are Called

**To enable Expert Consultation:**
1. Create `.tapps-agents/domains.md` file
2. Ensure analysis stage detects relevant domains
3. Configure experts in `.tapps-agents/experts.yaml`

**To enable RAG:**
1. Set `rag_enabled: true` in expert configs
2. Populate knowledge bases in `.tapps-agents/experts/{domain}/knowledge/`
3. Ensure VectorKnowledgeBase dependencies are installed (or use SimpleKnowledgeBase fallback)

**To enable Context7:**
1. Configure Context7 API key in project config
2. Ensure ArchitectAgent initializes Context7 helper
3. Include library/framework names in requirements text

---

## Example: Complete Enhanced Prompt

For the input: `"create an amazing modern dark html page that features 2025 fun and cool features"`

The enhanced prompt would include:

- **Intent Analysis**: Frontend feature development
- **Requirements**: Dark theme, modern design, 2025 features, responsive
- **Architecture**: SPA with component-based structure
- **Technology Recommendations**: HTML5, CSS3, modern JavaScript, Web APIs
- **Expert Guidance**: Frontend best practices, accessibility, performance
- **Implementation Strategy**: Step-by-step breakdown

This enhanced prompt is then used by Planner, Architect, Designer, and Implementer agents to create a comprehensive solution.

