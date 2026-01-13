# Workflow File Structure Analysis & Recommendations

## Problem Summary

The Full SDLC workflow (`@simple-mode *full`) failed because it expects a specific file structure that wasn't present:

- **Step `design`** expects: `stories/` directory
- **Step `api_design`** expects: `architecture.md` file
- **Step `implementation`** expects: `architecture.md`, `api-specs/`, `stories/`
- **Steps `review`, `testing`, `security`, `documentation`** expect: `src/` directory

The workflow blocked with error:
```
Workflow blocked: no ready steps and workflow not complete. 
Completed: 3/10. Blocking issues:
- Step design (architect/design_system): missing ['stories/']
- Step api_design (designer/api_design): missing ['architecture.md']
- Step implementation (implementer/write_code): missing ['architecture.md', 'api-specs/', 'stories/']
- Step review (reviewer/review_code): missing ['src/']
- Step testing (tester/write_tests): missing ['src/']
- Step security (ops/security_scan): missing ['src/']
- Step documentation (documenter/generate_docs): missing ['src/']
```

## Root Cause Analysis

### Full SDLC Workflow Characteristics

The Full SDLC workflow (`workflows/presets/full-sdlc.yaml`) is designed for **greenfield projects** and has strict artifact dependency requirements:

```yaml
steps:
  - id: planning
    creates:
      - stories/              # Must create stories/ directory
  - id: design
    requires:
      - stories/              # Requires stories/ from planning step
    creates:
      - architecture.md       # Must create architecture.md
  - id: api_design
    requires:
      - architecture.md       # Requires architecture.md from design step
    creates:
      - api-specs/            # Must create api-specs/ directory
  - id: implementation
    requires:
      - architecture.md       # Requires architecture.md
      - api-specs/            # Requires api-specs/ directory
      - stories/              # Requires stories/ directory
    creates:
      - src/                  # Must create src/ directory
```

**Key Characteristics:**
1. **Strict artifact dependencies**: Each step requires specific files/directories from previous steps
2. **Greenfield-focused**: Designed for new projects starting from scratch
3. **YAML-based execution**: Uses workflow executor that validates artifact existence
4. **File structure assumptions**: Assumes standard project layout (`src/`, `stories/`, `api-specs/`)

### Why It Failed

The workflow executor validates that required artifacts exist before allowing a step to execute. When the `planning` step completed (step 2), it was supposed to create a `stories/` directory, but the workflow executor didn't detect it, blocking subsequent steps.

**Possible reasons:**
1. The `planning` step didn't actually create the `stories/` directory
2. The artifact was created in a different location than expected
3. The workflow executor's artifact detection failed
4. The workflow was interrupted before artifacts were properly registered

## Simple Mode `*build` Workflow - The Better Alternative

### How Simple Mode `*build` Works

Simple Mode's `*build` workflow (`@simple-mode *build`) uses **skill orchestration** instead of YAML workflow dependencies:

**Workflow Steps:**
1. **@enhancer *enhance** - Enhances the prompt (7-stage pipeline)
   - Creates: `docs/workflows/simple-mode/{workflow-id}/step1-enhanced-prompt.md`
   - **No strict file dependencies**

2. **@planner *plan** - Creates user stories
   - Creates: `docs/workflows/simple-mode/{workflow-id}/step2-user-stories.md`
   - **Uses enhanced prompt as input** (not file dependency)

3. **@architect *design** - Designs architecture
   - Creates: `docs/workflows/simple-mode/{workflow-id}/step3-architecture.md`
   - **Uses previous step outputs as context** (not file dependency)

4. **@designer *design-api** - Designs components/API
   - Creates: `docs/workflows/simple-mode/{workflow-id}/step4-design.md`
   - **Uses previous step outputs as context**

5. **@implementer *implement** - Implements code
   - **Writes code directly to target files** (works with existing project structure)
   - **No requirement for `src/` directory**

6. **@reviewer *review** - Reviews code quality
   - Creates: `docs/workflows/simple-mode/{workflow-id}/step6-review.md`
   - **Reviews actual code files** (not dependent on `src/` structure)

7. **@tester *test** - Generates tests
   - Creates: `docs/workflows/simple-mode/{workflow-id}/step7-testing.md`
   - **Generates tests for actual code files**

### Key Advantages of Simple Mode `*build`

1. **No strict file structure requirements**
   - Works with existing project layouts
   - Adapts to React/TypeScript/JavaScript projects
   - Doesn't require `src/`, `stories/`, `api-specs/` directories

2. **Skill-based orchestration**
   - Uses Cursor Skills directly (`@enhancer`, `@planner`, etc.)
   - Passes outputs between steps as context (not file dependencies)
   - More flexible and resilient

3. **Documentation-focused artifacts**
   - Creates workflow documentation in `docs/workflows/simple-mode/`
   - Doesn't require specific file structures in the codebase
   - Better for brownfield/refactoring projects

4. **Better for React/UI components**
   - Works with component-based architectures
   - Doesn't assume backend API structures
   - Adapts to frontend project layouts

## Recommendations

### ✅ Recommendation 1: Use Simple Mode `*build` for React Components

**For React component updates, use:**
```cursor
@simple-mode *build "Update [component name] to [description]"
```

**Why:**
- No strict file structure requirements
- Works with existing React/TypeScript project layouts
- Creates documentation artifacts in `docs/workflows/simple-mode/`
- Skill orchestration adapts to your project structure

### ✅ Recommendation 2: Use Full SDLC Only for Greenfield Projects

**Use `@simple-mode *full` only when:**
- Starting a new project from scratch
- You can create the required file structure (`src/`, `stories/`, `api-specs/`)
- Building backend APIs or full-stack applications
- You need the complete 9-step SDLC with security scanning

**For React component updates:**
- ❌ Don't use `@simple-mode *full` (too strict)
- ✅ Use `@simple-mode *build` (flexible, skill-based)

### ✅ Recommendation 3: Workflow Selection Guide

| Use Case | Workflow | Why |
|----------|----------|-----|
| React component update | `@simple-mode *build` | Flexible, no strict file structure |
| Frontend feature (React/Vue/Angular) | `@simple-mode *build` | Adapts to component architecture |
| Backend API feature | `@simple-mode *build` | Works with existing API structure |
| Bug fix | `@simple-mode *fix` | Focused debugging workflow |
| Code review | `@simple-mode *review` | Quality review workflow |
| New project (greenfield) | `@simple-mode *full` | Complete SDLC with file structure |
| Framework development | `@simple-mode *full` | Requires full SDLC rigor |

### ✅ Recommendation 4: Fix the Full SDLC Workflow (If Needed)

If you specifically need Full SDLC for future projects, ensure:

1. **Artifact Creation**: Each step properly creates required artifacts
   - `planning` step must create `stories/` directory
   - `design` step must create `architecture.md` file
   - `api_design` step must create `api-specs/` directory
   - `implementation` step must create `src/` directory

2. **Artifact Detection**: Workflow executor must detect artifacts correctly
   - Check artifact paths in workflow state
   - Verify artifact registration after each step

3. **Project Structure**: Create required directories before running workflow
   ```bash
   mkdir -p stories api-specs src
   ```

## Implementation Steps for React Component Update

### Step 1: Use Simple Mode `*build`

```cursor
@simple-mode *build "Update [Your Component Name] to [describe changes]"
```

### Step 2: Workflow Will Execute

The workflow will:
1. Enhance your prompt (requirements analysis)
2. Create user stories (if needed)
3. Design architecture/component structure
4. Design component API/props
5. Implement/update the React component
6. Review code quality
7. Generate tests

### Step 3: Documentation Created

All workflow artifacts will be in:
```
docs/workflows/simple-mode/{workflow-id}/
├── step1-enhanced-prompt.md
├── step2-user-stories.md
├── step3-architecture.md
├── step4-design.md
├── step6-review.md
└── step7-testing.md
```

### Step 4: Code Updated

The React component will be updated directly in your project structure (no `src/` requirement).

## Conclusion

**For React component updates:**
- ✅ **Use `@simple-mode *build`** - Flexible, skill-based, works with existing projects
- ❌ **Don't use `@simple-mode *full`** - Too strict, requires specific file structures

**Simple Mode `*build` is the recommended workflow for:**
- React/TypeScript/JavaScript component updates
- Frontend feature development
- Brownfield/refactoring projects
- Projects with existing file structures

**Full SDLC workflow should only be used for:**
- Greenfield projects
- Backend API development (where you can create required structures)
- Framework development
- Enterprise projects requiring complete SDLC rigor
