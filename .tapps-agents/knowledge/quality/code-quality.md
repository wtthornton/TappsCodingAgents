# Code Quality

## Standards

- **Reviewer:** 7-category scoring (complexity, security, maintainability, test_coverage, performance, structure, devex). Quality gates: overall ≥70 (≥75 for framework).
- **Linting:** Ruff. Type checking: mypy.
- **Security:** Bandit; use `@reviewer *security-scan` and `@ops *audit-security`.

## Workflows

- Use `@simple-mode *build` or `*full` for features so review and test steps run.
- Use `@simple-mode *review <file>` for pre-commit quality checks.
