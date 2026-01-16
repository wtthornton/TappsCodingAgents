# Quality Gates

## What are Quality Gates?

Quality gates are automated checkpoints that code must pass before it can be merged or deployed. They enforce code quality standards and prevent low-quality code from entering the codebase.

## Types of Quality Gates

### Static Analysis Gates
- Linting errors: Must be zero
- Type checking: Must pass
- Code complexity: Below threshold
- Security vulnerabilities: None critical

### Test Coverage Gates
- Minimum coverage: 80%
- Critical paths: 100%
- New code coverage: 90%+
- Regression tests: All passing

### Build Gates
- All tests passing
- Build successful
- Dependencies up to date
- No deprecated APIs

### Security Gates
- No known vulnerabilities
- Security scan passing
- Secrets not committed
- Dependency audit clean

## Implementation

### Pre-Commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
      
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

### CI/CD Integration
```yaml
# GitHub Actions example
name: Quality Gates
on: [pull_request]
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Lint
        run: flake8 . --max-line-length=100
        
      - name: Type Check
        run: mypy .
        
      - name: Test Coverage
        run: pytest --cov --cov-fail-under=80
        
      - name: Security Scan
        run: bandit -r .
```

## Quality Gate Criteria

### Must-Pass (Blocking)
- Zero linting errors
- All tests passing
- No critical security issues
- Build successful
- Type checking passes

### Should-Pass (Warning)
- Test coverage > 80%
- Complexity below threshold
- Documentation complete
- Performance benchmarks met

### Nice-to-Have (Informational)
- Code style consistency
- Optimization suggestions
- Best practice recommendations

## Gradual Enforcement

### Phase 1: Measurement
- Collect baseline metrics
- Identify problem areas
- Set realistic targets

### Phase 2: Warnings
- Enable quality gates as warnings
- Don't block merges yet
- Track improvement trends

### Phase 3: Enforcement
- Make gates blocking
- Require fixes before merge
- Maintain standards

## Quality Gate Configuration

### Thresholds
```yaml
quality_gates:
  linting:
    max_errors: 0
    max_warnings: 10
    
  test_coverage:
    minimum: 80
    critical_paths: 100
    
  complexity:
    max_cyclomatic: 10
    max_cognitive: 15
    
  security:
    allow_medium: false
    allow_high: false
    allow_critical: false
```

### Per-Project Adjustments
- **Legacy Code**: Lower thresholds initially
- **New Projects**: Strict from start
- **Critical Systems**: Higher standards
- **Prototypes**: Relaxed gates

## Best Practices

1. **Start Strict**: Easier to relax than tighten
2. **Automate Everything**: No manual checks
3. **Clear Messaging**: Explain failures clearly
4. **Fast Feedback**: Run gates quickly
5. **Gradual Adoption**: Phase in over time
6. **Team Agreement**: Get buy-in on thresholds
7. **Regular Review**: Adjust as needed

## Monitoring Quality Trends

Track these metrics over time:
- **Defect Rate**: Bugs per release
- **Test Coverage**: Coverage trends
- **Complexity**: Average complexity
- **Build Times**: CI/CD performance
- **Review Time**: PR review duration
- **Deployment Frequency**: Release cadence
