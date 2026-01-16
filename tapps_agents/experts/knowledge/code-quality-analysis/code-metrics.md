# Code Metrics

## Overview

Code metrics provide quantitative measurements of code quality, complexity, and maintainability. These metrics help identify areas needing improvement and track quality trends over time.

## Core Metrics

### Cyclomatic Complexity

Measures the number of linearly independent paths through a program's source code.

**Thresholds:**
- **1-10**: Simple (low risk)
- **11-20**: Moderate (moderate risk)
- **21-50**: Complex (high risk)
- **50+**: Very complex (very high risk)

**Reduction Strategies:**
- Extract methods for complex conditionals
- Use polymorphism instead of switch statements
- Break down large functions
- Apply design patterns (Strategy, Command)

### Maintainability Index

Composite metric based on:
- Halstead Volume
- Cyclomatic Complexity
- Lines of Code

**Scale:** 0-100 (higher is better)
- **20-40**: Difficult to maintain
- **40-60**: Moderate maintainability
- **60-80**: Good maintainability
- **80-100**: Excellent maintainability

### Lines of Code (LOC)

**Best Practices:**
- Methods: < 20 lines
- Classes: < 300 lines
- Files: < 500 lines
- Modules: < 1000 lines

### Code Duplication

**Thresholds:**
- **0-3%**: Excellent
- **3-5%**: Good
- **5-10%**: Acceptable
- **10%+**: Needs refactoring

**DRY Principle:**
- Don't Repeat Yourself
- Extract common functionality
- Use abstractions and inheritance

### Test Coverage

**Coverage Types:**
- **Line Coverage**: % of lines executed
- **Branch Coverage**: % of branches tested
- **Function Coverage**: % of functions called

**Targets:**
- **80%+**: Good coverage
- **90%+**: Excellent coverage
- **100%**: Perfect (but may be overkill)

## Advanced Metrics

### Technical Debt Ratio

```
Technical Debt Ratio = (Remediation Cost / Development Cost) × 100
```

**Interpretation:**
- **< 5%**: Low technical debt
- **5-10%**: Moderate technical debt
- **10-20%**: Significant technical debt
- **20%+**: Critical technical debt

### Code Churn

Measures how frequently code changes.

**High Churn Indicators:**
- Frequently modified files
- Unstable areas of code
- Potential architectural issues

### Coupling Metrics

**Afferent Coupling (Ca):** Number of classes outside a package that depend on classes within it.

**Efferent Coupling (Ce):** Number of classes inside a package that depend on classes outside it.

**Instability (I):** I = Ce / (Ca + Ce)
- **0**: Stable (no dependencies on external classes)
- **1**: Instable (depends on external classes)

## Metrics Collection Tools

### Python
- **radon**: Complexity metrics
- **coverage.py**: Test coverage
- **vulture**: Dead code detection
- **pylint**: Code quality scoring

### JavaScript/TypeScript
- **complexity-report**: Cyclomatic complexity
- **istanbul/nyc**: Coverage
- **escomplex**: Code complexity

### Multi-Language
- **SonarQube**: Comprehensive metrics platform
- **CodeClimate**: Automated code review
- **Better Code Hub**: Quality assessment

## Using Metrics Effectively

1. **Set Baseline**: Measure current state
2. **Define Targets**: Set improvement goals
3. **Track Trends**: Monitor over time
4. **Prioritize**: Focus on high-impact areas
5. **Automate**: Integrate into CI/CD
6. **Review Regularly**: Monthly/quarterly assessments

## Anti-Patterns to Avoid

- **Metrics Obsession**: Don't optimize for metrics alone
- **False Positives**: Understand context before acting
- **Ignoring Context**: Metrics without understanding are useless
- **Gaming Metrics**: Don't artificially improve numbers
- **One-Size-Fits-All**: Different projects need different thresholds
