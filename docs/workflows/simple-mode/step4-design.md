# Step 4: Component Design Specifications - Fix Suggestions Generation Bug

## Method Specification

### Method: `_generate_category_suggestions()`

**Location:** `tapps_agents/agents/reviewer/score_validator.py`  
**Line Range:** ~250-353 (will expand with new cases)

**Current Signature:**
```python
def _generate_category_suggestions(
    self, category: str, score: float, language: Language | None = None
) -> list[str]:
    """Generate category-specific improvement suggestions."""
```

**No Changes to Signature** - Additive implementation only

---

## Implementation Specifications

### Case 1: Linting Category

**Category Name:** `"linting"`  
**Trigger:** When `category == "linting"` and `score < 7.0`

**Base Suggestions (All Languages):**
```python
suggestions.extend([
    "Run linting tool to identify specific code style issues",
    "Fix code style violations (PEP 8 for Python, ESLint rules for JS/TS)",
    "Address all errors (E) and fatal issues (F) first, then warnings (W)",
    "Review and fix warnings for better code quality",
])
```

**Python-Specific Suggestions:**
```python
if language == Language.PYTHON:
    suggestions.extend([
        "Run 'ruff check' to identify specific linting issues",
        "Run 'ruff check --fix' to auto-fix many issues automatically",
        "Configure ruff in pyproject.toml for project-specific rules",
        "Ensure consistent import ordering and formatting",
        "Fix line length violations (aim for 88-100 characters per line)",
    ])
```

**TypeScript/JavaScript/React-Specific Suggestions:**
```python
elif language in [Language.TYPESCRIPT, Language.JAVASCRIPT, Language.REACT]:
    suggestions.extend([
        "Run 'eslint' to identify specific linting issues",
        "Run 'eslint --fix' to auto-fix many issues automatically",
        "Configure ESLint rules in .eslintrc or package.json",
        "Ensure consistent code formatting (integrate Prettier if needed)",
        "Fix TypeScript-specific linting issues (strict mode violations)",
    ])
```

**Implementation Location:** After `elif category == "performance":` block, before `elif category == "overall":`

---

### Case 2: Type Checking Category

**Category Name:** `"type_checking"`  
**Trigger:** When `category == "type_checking"` and `score < 7.0`

**Base Suggestions (All Languages):**
```python
suggestions.extend([
    "Add type annotations to function parameters and return types",
    "Fix type errors reported by type checker",
    "Use type hints consistently throughout the codebase",
    "Enable strict type checking mode for better type safety",
])
```

**Python-Specific Suggestions:**
```python
if language == Language.PYTHON:
    suggestions.extend([
        "Run 'mypy <file>' to see specific type errors",
        "Add type hints using typing module or Python 3.9+ built-in types",
        "Use Optional[T] for nullable types, Union[T, U] for multiple types",
        "Consider using mypy --strict for maximum type safety",
        "Add return type annotations: 'def func() -> int:'",
        "Use TypeVar for generic types, Protocol for structural typing",
    ])
```

**TypeScript/JavaScript/React-Specific Suggestions:**
```python
elif language in [Language.TYPESCRIPT, Language.JAVASCRIPT, Language.REACT]:
    suggestions.extend([
        "Enable strict mode in tsconfig.json (strict: true)",
        "Add explicit return types to functions",
        "Use proper interface/type definitions instead of 'any'",
        "Fix TypeScript compiler errors systematically",
        "Avoid using 'any' type - use 'unknown' or specific types",
        "Use type guards for runtime type checking",
    ])
```

**Implementation Location:** After `elif category == "linting":` block

---

### Case 3: Duplication Category

**Category Name:** `"duplication"`  
**Trigger:** When `category == "duplication"` and `score < 7.0`

**Base Suggestions (All Languages):**
```python
suggestions.extend([
    "Identify and extract duplicate code into reusable functions",
    "Use helper functions or utility modules for common patterns",
    "Consider refactoring similar code blocks into shared components",
    f"Aim for < 3% code duplication across the project (current threshold: {self.duplication_threshold if hasattr(self, 'duplication_threshold') else 3.0}%)",
])
```

**Python-Specific Suggestions:**
```python
if language == Language.PYTHON:
    suggestions.extend([
        "Run 'jscpd' to identify specific duplicate code blocks",
        "Extract common logic into utility functions or classes",
        "Use decorators or context managers for repeated patterns",
        "Create shared utility modules for common functionality",
        "Consider using mixins for shared class behavior",
    ])
```

**TypeScript/JavaScript/React-Specific Suggestions:**
```python
elif language in [Language.TYPESCRIPT, Language.JAVASCRIPT, Language.REACT]:
    suggestions.extend([
        "Extract duplicate code into shared utility functions",
        "Create reusable React components for repeated UI patterns",
        "Use higher-order components (HOCs) or custom hooks for common logic",
        "Create shared utility modules or helper functions",
        "Use composition over duplication for React components",
    ])
```

**Implementation Location:** After `elif category == "type_checking":` block, before `elif category == "overall":`

---

## Code Structure

### Complete Implementation Block

```python
# ... existing cases ...

elif category == "linting":
    suggestions.extend([
        "Run linting tool to identify specific code style issues",
        "Fix code style violations (PEP 8 for Python, ESLint rules for JS/TS)",
        "Address all errors (E) and fatal issues (F) first, then warnings (W)",
        "Review and fix warnings for better code quality",
    ])
    if language == Language.PYTHON:
        suggestions.extend([
            "Run 'ruff check' to identify specific linting issues",
            "Run 'ruff check --fix' to auto-fix many issues automatically",
            "Configure ruff in pyproject.toml for project-specific rules",
            "Ensure consistent import ordering and formatting",
            "Fix line length violations (aim for 88-100 characters per line)",
        ])
    elif language in [Language.TYPESCRIPT, Language.JAVASCRIPT, Language.REACT]:
        suggestions.extend([
            "Run 'eslint' to identify specific linting issues",
            "Run 'eslint --fix' to auto-fix many issues automatically",
            "Configure ESLint rules in .eslintrc or package.json",
            "Ensure consistent code formatting (integrate Prettier if needed)",
            "Fix TypeScript-specific linting issues (strict mode violations)",
        ])

elif category == "type_checking":
    suggestions.extend([
        "Add type annotations to function parameters and return types",
        "Fix type errors reported by type checker",
        "Use type hints consistently throughout the codebase",
        "Enable strict type checking mode for better type safety",
    ])
    if language == Language.PYTHON:
        suggestions.extend([
            "Run 'mypy <file>' to see specific type errors",
            "Add type hints using typing module or Python 3.9+ built-in types",
            "Use Optional[T] for nullable types, Union[T, U] for multiple types",
            "Consider using mypy --strict for maximum type safety",
            "Add return type annotations: 'def func() -> int:'",
            "Use TypeVar for generic types, Protocol for structural typing",
        ])
    elif language in [Language.TYPESCRIPT, Language.JAVASCRIPT, Language.REACT]:
        suggestions.extend([
            "Enable strict mode in tsconfig.json (strict: true)",
            "Add explicit return types to functions",
            "Use proper interface/type definitions instead of 'any'",
            "Fix TypeScript compiler errors systematically",
            "Avoid using 'any' type - use 'unknown' or specific types",
            "Use type guards for runtime type checking",
        ])

elif category == "duplication":
    suggestions.extend([
        "Identify and extract duplicate code into reusable functions",
        "Use helper functions or utility modules for common patterns",
        "Consider refactoring similar code blocks into shared components",
        f"Aim for < 3% code duplication across the project",
    ])
    if language == Language.PYTHON:
        suggestions.extend([
            "Run 'jscpd' to identify specific duplicate code blocks",
            "Extract common logic into utility functions or classes",
            "Use decorators or context managers for repeated patterns",
            "Create shared utility modules for common functionality",
            "Consider using mixins for shared class behavior",
        ])
    elif language in [Language.TYPESCRIPT, Language.JAVASCRIPT, Language.REACT]:
        suggestions.extend([
            "Extract duplicate code into shared utility functions",
            "Create reusable React components for repeated UI patterns",
            "Use higher-order components (HOCs) or custom hooks for common logic",
            "Create shared utility modules or helper functions",
            "Use composition over duplication for React components",
        ])

# ... existing "overall" case ...
```

---

## Design Decisions

### Decision 1: Suggestion Count
**Decision:** 4-6 base suggestions + 4-6 language-specific suggestions  
**Rationale:** 
- Consistent with existing categories (test_coverage has 4, performance has 4-6)
- Provides comprehensive guidance without overwhelming users
- Language-specific suggestions add value without duplication

### Decision 2: Tool Command Format
**Decision:** Include actual commands users can run (e.g., `'ruff check'`)  
**Rationale:**
- Actionable suggestions are more valuable
- Users can copy-paste commands directly
- Follows pattern from "overall" category suggestions

### Decision 3: Language Detection
**Decision:** Use same `if/elif` pattern as existing categories  
**Rationale:**
- Consistency with existing code
- Easy to understand and maintain
- Supports multiple languages per category

### Decision 4: Duplication Threshold Reference
**Decision:** Use f-string to reference threshold if available  
**Rationale:**
- Dynamic threshold is more accurate
- Falls back gracefully if attribute not available
- Consistent with other threshold references in codebase

---

## Edge Cases

### Edge Case 1: Score = 7.0 (Threshold)
**Behavior:** Suggestions should be generated (score < 7.0 is the condition)  
**Implementation:** Use `score < 7.0` check (handled by `explain_score()` calling this method)

### Edge Case 2: Score = 10.0 (Perfect)
**Behavior:** No suggestions (handled upstream in `explain_score()`)  
**Implementation:** Method not called for excellent scores

### Edge Case 3: Unknown Language
**Behavior:** Return base suggestions only, skip language-specific  
**Implementation:** `if/elif` pattern naturally handles this

### Edge Case 4: Language = None
**Behavior:** Return base suggestions only  
**Implementation:** `if language == Language.PYTHON:` check handles None gracefully

---

## Testing Specifications

### Unit Test Cases

#### Test: Linting Suggestions - Python
```python
def test_linting_suggestions_python():
    validator = ScoreValidator()
    suggestions = validator._generate_category_suggestions(
        category="linting",
        score=5.0,
        language=Language.PYTHON
    )
    assert len(suggestions) > 0
    assert any("ruff" in s.lower() for s in suggestions)
    assert any("check" in s.lower() for s in suggestions)
```

#### Test: Type Checking Suggestions - TypeScript
```python
def test_type_checking_suggestions_typescript():
    validator = ScoreValidator()
    suggestions = validator._generate_category_suggestions(
        category="type_checking",
        score=5.0,
        language=Language.TYPESCRIPT
    )
    assert len(suggestions) > 0
    assert any("typescript" in s.lower() or "tsconfig" in s.lower() for s in suggestions)
```

#### Test: Duplication Suggestions - All Languages
```python
def test_duplication_suggestions_all_languages():
    validator = ScoreValidator()
    for lang in [Language.PYTHON, Language.TYPESCRIPT, None]:
        suggestions = validator._generate_category_suggestions(
            category="duplication",
            score=5.0,
            language=lang
        )
        assert len(suggestions) > 0
        assert any("duplicate" in s.lower() or "reusable" in s.lower() for s in suggestions)
```

---

## Validation Checklist

- ✅ Method signature unchanged
- ✅ Follows existing pattern (base + language-specific)
- ✅ Suggestions are actionable and specific
- ✅ Tool commands are included
- ✅ Language-specific suggestions are relevant
- ✅ No breaking changes
- ✅ Consistent with existing code style
- ✅ Handles edge cases gracefully
