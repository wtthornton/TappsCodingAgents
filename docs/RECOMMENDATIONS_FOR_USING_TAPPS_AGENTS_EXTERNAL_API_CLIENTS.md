# Recommendations for Projects Using TappsCodingAgents: External API Clients

**Date:** 2026-01-24
**Audience:** Projects using TappsCodingAgents to build or review external API clients
**Context:** This document provides workarounds and best practices when tapps-agents doesn't have domain knowledge for your specific external API (e.g. custom OAuth2 flows).

---

## Overview

When building or reviewing external API clients (especially OAuth2 refresh-token flows, custom auth headers, or SaaS APIs not in tapps-agents' expert knowledge), you may encounter gaps. This guide provides **workarounds and best practices** to get the most value from tapps-agents despite these limitations.

---

## 1. Workarounds for "Review + Compare + Fix" Requests

### Problem
You want to: "Review this API client code, compare it to our existing patterns, and fix it."

### Solutions

#### Option A: Two-Step Workflow (Recommended)
1. **First, review:**
   ```cursor
   @simple-mode *review <file>
   ```
   - Save your code to a file first (e.g. `scripts/external_api_client.py`)
   - This provides quality scores and feedback

2. **Then, fix based on review:**
   ```cursor
   @simple-mode *fix <file> "Apply improvements from review: add logging, modern type hints, input validation, better error handling"
   ```
   - Use the review feedback to craft a specific fix description
   - The fix workflow will apply changes systematically

#### Option B: Use Build Workflow for New Clients
If the API client is a **new feature**:
```cursor
@simple-mode *build "Create external API client with OAuth2 refresh-token authentication"
```
- This runs the full 7-step workflow (enhance → plan → architect → design → implement → review → test)
- Provides comprehensive documentation and tests

#### Option C: Manual Comparison
1. **Review your code:**
   ```cursor
   @simple-mode *review <file>
   ```

2. **Manually compare to existing patterns:**
   - Look at your project's existing API clients (e.g. `backup_client.py`, `beads/client.py`)
   - Note patterns: logging style, type hints (`str | None` vs `Optional[str]`), error handling, structure
   - Apply those patterns manually or via `@implementer *refactor`

3. **Apply fixes:**
   ```cursor
   @implementer *refactor <file> "Match project patterns: use modern type hints (str | None), add logging, improve error messages"
   ```

---

## 2. Handling External APIs Not in Expert Knowledge

### Problem
Tapps-agents doesn't know about your specific external API (e.g. custom OAuth2 implementations).

### Solutions

#### Option A: Provide Context in Your Prompt
When using `*build` or `*enhance`, include API-specific details:
```cursor
@simple-mode *build "Create external API client using OAuth2 refresh-token flow. Auth header: 'Bearer <access_token>'. Token endpoint: https://api.example.com/oauth/token. API base: https://api.example.com/v1"
```

#### Option B: Use Generic Patterns
Tapps-agents knows **generic** patterns (retry, rate limiting, caching). Use those:
```cursor
@simple-mode *build "Create external API client with OAuth2 refresh-token authentication, retry logic, and rate limiting"
```

Then manually adapt to your specific API's requirements.

#### Option C: Create Project-Specific Expert Knowledge
Add your API patterns to your project's expert knowledge:
1. Create `.tapps-agents/experts/knowledge/api-integrations/my-api.md`
2. Document your API's auth flow, endpoints, patterns
3. Configure an expert in `.tapps-agents/experts.yaml` that uses this knowledge
4. Agents will consult this project-specific expert

**Example expert config:**
```yaml
experts:
  - expert_id: "project-my-api"
    name: "My API Integration Expert"
    primary_domain: "api-design-integration"
    knowledge_base:
      - path: ".tapps-agents/experts/knowledge/api-integrations/my-api.md"
    weight: 0.8
```

---

## 3. Handling Pasted Code (No File Yet)

### Problem
You pasted code in chat and want to review/fix it, but `*review` and `*fix` expect a file path.

### Solutions

#### Option A: Save to File First (Recommended)
1. Create a file: `scripts/external_api_client.py`
2. Paste your code
3. Then use workflows:
   ```cursor
   @simple-mode *review scripts/external_api_client.py
   @simple-mode *fix scripts/external_api_client.py "description"
   ```

#### Option B: Use Build Workflow
If it's a new feature, use `*build` which can work with descriptions:
```cursor
@simple-mode *build "Create API client: [paste your code description or requirements]"
```

#### Option C: Ask AI to Create File First
```cursor
Create a file scripts/external_api_client.py with this code: [paste]
```
Then proceed with review/fix workflows.

---

## 4. Best Practices for External API Clients

### 4.1 Use Explicit Workflows
**Don't rely on implicit intent detection** for complex tasks:
- ✅ `@simple-mode *build "description"` (explicit)
- ❌ "Build an API client" (may not route correctly)

### 4.2 Provide API-Specific Details
Include in your prompt:
- Auth method (OAuth2, API key, custom headers)
- Token refresh flow (if applicable)
- API base URL and endpoints
- Error handling requirements
- Rate limiting needs

### 4.3 Leverage Generic Patterns
Even without API-specific knowledge, tapps-agents can help with:
- **Code quality:** `@reviewer *review` (scores, linting, type checking)
- **Security:** `@ops *audit-security` (general security patterns)
- **Testing:** `@tester *test` (test generation)
- **Documentation:** `@documenter *document-api`

### 4.4 Combine Workflows
For complex tasks, use multiple workflows:
1. `@simple-mode *review` → Get quality scores
2. `@simple-mode *enhance "description"` → Get detailed spec
3. `@simple-mode *build` → Implement with full workflow
4. `@simple-mode *test` → Ensure coverage

---

## 5. When to Expect Limitations

### Current Limitations
- **No "compare to codebase"** - Tapps-agents cannot systematically compare your code to existing project patterns (yet)
- **Limited OAuth2 refresh-token knowledge** - Framework experts cover authorization-code flow, not refresh-token flows
- **No SaaS API docs** - Context7 is for libraries (FastAPI, requests), not external SaaS APIs
- **Reviewer doesn't use API-design experts** - Review focuses on security, performance, code-quality; not API client patterns

### Workarounds
- **Manual comparison** - Review existing clients in your codebase, apply patterns manually
- **Project-specific experts** - Create your own expert knowledge for your APIs
- **Explicit prompts** - Provide API details in your build/enhance prompts
- **Multi-step workflows** - Break complex tasks into review → enhance → build → test

---

## 6. Example: External API Client Workflow

### Step-by-Step

1. **Save code to file:**
   ```bash
   # Create scripts/external_api_client.py with your code
   ```

2. **Review for quality:**
   ```cursor
   @simple-mode *review scripts/external_api_client.py
   ```
   - Get scores, linting, type checking
   - Note: Won't have API-specific knowledge, but will catch general issues

3. **Enhance with project context:**
   ```cursor
   @simple-mode *enhance "Improve external API client: add logging, modern type hints (str | None), input validation, better error handling. Match patterns from backup_client.py"
   ```

4. **Apply improvements:**
   ```cursor
   @implementer *refactor scripts/external_api_client.py "Apply enhancements: add logging, use str | None, validate inputs, improve error messages"
   ```

5. **Generate tests:**
   ```cursor
   @simple-mode *test scripts/external_api_client.py
   ```

6. **Final review:**
   ```cursor
   @simple-mode *review scripts/external_api_client.py
   ```

---

## 7. Quick Reference

| Task | Command | Notes |
|------|---------|-------|
| Review code quality | `@simple-mode *review <file>` | Scores, linting, type checking |
| Fix bugs/errors | `@simple-mode *fix <file> "description"` | Requires file + error description |
| Build new client | `@simple-mode *build "description"` | Full 7-step workflow |
| Enhance prompt | `@simple-mode *enhance "description"` | Get detailed spec |
| Generate tests | `@simple-mode *test <file>` | Test generation |
| Refactor code | `@simple-mode *refactor <file>` | Pattern detection + modernization |
| Security audit | `@ops *audit-security <target>` | Security scanning |

---

## 8. Getting Help

### If Workflows Don't Work
1. **Check intent detection:**
   - Use explicit commands (`*build`, `*review`, `*fix`) instead of natural language
   - See `.cursor/rules/when-to-use.mdc` for guidance

2. **Check environment:**
   ```bash
   tapps-agents doctor
   tapps-agents cursor verify
   ```

3. **Review workflow enforcement:**
   - See `docs/WORKFLOW_ENFORCEMENT_GUIDE.md`
   - Ensure you're using workflows, not direct edits

### If Domain Knowledge is Missing
1. **Create project-specific expert** (see Section 2, Option C)
2. **Provide explicit context** in prompts (see Section 2, Option A)
3. **Use generic patterns** and adapt manually (see Section 2, Option B)

---

## 9. Related Documentation

- **Framework improvements:** See `docs/RECOMMENDATIONS_FOR_IMPROVING_TAPPS_AGENTS_FRAMEWORK.md`
- **Workflow enforcement:** `docs/WORKFLOW_ENFORCEMENT_GUIDE.md`
- **When to use:** `.cursor/rules/when-to-use.mdc`
- **Quick reference:** `.cursor/rules/quick-reference.mdc`
- **Command reference:** `.cursor/rules/command-reference.mdc`

---

## 10. Summary

**Key Takeaways:**
1. **Save code to files** before using `*review` or `*fix`
2. **Use explicit workflows** (`*build`, `*review`, `*fix`) for complex tasks
3. **Provide API-specific details** in your prompts
4. **Use multi-step workflows** (review → enhance → build → test) for best results
5. **Create project-specific experts** for APIs not in framework knowledge
6. **Expect limitations** - "compare to codebase" not yet supported; manual comparison needed

**When in doubt:** Use `@simple-mode *build` for new features, `@simple-mode *review` for quality checks, and combine workflows for complex tasks.
