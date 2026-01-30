# Static Analysis Patterns

## Overview

Static analysis tools examine code without executing it, identifying potential bugs, security vulnerabilities, and code quality issues early in the development cycle.

## Common Static Analysis Categories

### Code Smells
- Long methods (excessive lines of code)
- Large classes (too many responsibilities)
- Duplicate code (DRY violations)
- Complex conditionals (high cyclomatic complexity)
- God objects (classes that know/do too much)

### Security Vulnerabilities
- SQL injection risks
- Cross-site scripting (XSS) vulnerabilities
- Insecure deserialization
- Hardcoded credentials
- Weak cryptographic algorithms

### Performance Issues
- Inefficient algorithms (O(n²) when O(n) possible)
- Unnecessary object creation
- Memory leaks
- Database N+1 queries
- Inefficient string concatenation

### Code Style and Best Practices
- Naming convention violations
- Missing documentation
- Unused imports/variables
- Inconsistent formatting
- Deprecated API usage

## Popular Static Analysis Tools

### Python
- **Ruff**: Linting and formatting (recommended—single tool, 10–100x faster than alternatives)
- **mypy**: Static type checking
- **bandit**: Security vulnerability scanner
- **radon**: Complexity and maintainability metrics

### JavaScript/TypeScript
- **ESLint**: JavaScript/TypeScript linter
- **Prettier**: Code formatter
- **TypeScript**: Built-in type checking
- **SonarJS**: Advanced static analysis

### General Purpose
- **SonarQube**: Multi-language code quality platform
- **CodeQL**: Semantic code analysis
- **Semgrep**: Fast pattern-based analysis

## Integration Strategies

### Pre-Commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: check-yaml
      - id: end-of-file-fixer
```

### CI/CD Integration
```yaml
# .github/workflows/lint.yml
name: Code Quality
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Ruff (lint)
        run: ruff check .
      - name: Ruff (format)
        run: ruff format --check .
      - name: Type check
        run: mypy .
      - name: Security scan
        run: bandit -r .
```

## Best Practices

1. **Run Early and Often**: Integrate into IDE and pre-commit hooks
2. **Fix Issues Immediately**: Don't let technical debt accumulate
3. **Customize Rules**: Adjust to match your team's standards
4. **Track Metrics**: Monitor code quality trends over time
5. **Gradual Adoption**: Start with critical rules, expand gradually

## Metrics to Track

- Cyclomatic complexity
- Code duplication percentage
- Test coverage
- Maintainability index
- Technical debt ratio
- Security vulnerabilities count
