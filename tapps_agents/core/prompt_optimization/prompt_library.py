"""Prompt library for best practice eval prompts."""

from typing import Any

PROMPT_LIBRARY: dict[str, dict[str, Any]] = {
    "eval_code_review": {
        "template": """Review the following code for quality issues:

{code}

Focus on:
- Security vulnerabilities
- Performance issues
- Maintainability concerns
- Code correctness
- Best practices

Provide specific, actionable feedback.""",
        "domain": "code_review",
    },
    "eval_security": {
        "template": """Security review for code:

{code}

Check for:
- Input validation issues
- Authentication/authorization flaws
- Sensitive data exposure
- Injection vulnerabilities
- Insecure dependencies

Prioritize critical security issues.""",
        "domain": "security",
    },
}

