# Recommendations for Improving TappsCodingAgents Framework

**Date:** 2026-01-24  
**Audience:** TappsCodingAgents framework developers and maintainers  
**Context:** This document provides actionable recommendations for improving the framework based on gaps identified when handling external API client tasks (e.g. Site24x7, Zoho OAuth2 refresh-token flows).

---

## Overview

This document outlines **framework improvements** needed to better support external API client development and review. These are code changes, new features, and enhancements to the TappsCodingAgents framework itself.

---

## 1. Extend Expert Knowledge (High Priority)

### 1.1 Add OAuth2 Refresh-Token Patterns

**Problem:** Framework experts only cover OAuth2 **authorization-code** flow (Google, authlib, Flask). No knowledge of **refresh-token** flows, token expiry handling, or custom auth headers.

**Recommendation:** Extend `tapps_agents/experts/knowledge/api-design-integration/api-security-patterns.md`

**Changes:**
1. **Add OAuth2 Refresh-Token Flow section:**
   ```markdown
   ### 4. OAuth2 Refresh-Token Flow
   
   **Use Case:** Long-lived API access without user re-authentication
   
   **Pattern:**
   ```
   Client → Exchange refresh_token → Access Token
   Client → API (with Access Token)
   Client → Refresh before expiry → New Access Token
   ```
   
   **Implementation:**
   ```python
   class OAuth2RefreshTokenClient:
       def __init__(self, client_id, client_secret, refresh_token, token_url):
           self.client_id = client_id
           self.client_secret = client_secret
           self.refresh_token = refresh_token
           self.token_url = token_url
           self._access_token = None
           self._expiry_epoch = 0.0
       
       def _refresh_access_token(self) -> str:
           """Exchange refresh_token for access_token."""
           resp = requests.post(
               self.token_url,
               data={
                   "refresh_token": self.refresh_token,
                   "client_id": self.client_id,
                   "client_secret": self.client_secret,
                   "grant_type": "refresh_token",
               }
           )
           resp.raise_for_status()
           payload = resp.json()
           
           if "access_token" not in payload:
               raise RuntimeError("Token response missing access_token")
           
           access_token = payload["access_token"]
           expires_in = payload.get("expires_in_sec", payload.get("expires_in", 3600))
           
           # Refresh proactively (e.g. 60 seconds before expiry)
           self._expiry_epoch = time.time() + int(expires_in) - 60
           self._access_token = access_token
           return access_token
       
       def _get_access_token(self) -> str:
           """Get valid access token, refreshing if necessary."""
           if self._access_token and time.time() < self._expiry_epoch:
               return self._access_token
           return self._refresh_access_token()
   ```
   
   **Best Practices:**
   - Refresh tokens proactively (e.g. 60 seconds before expiry) to avoid race conditions
   - Handle both `expires_in` and `expires_in_sec` fields (Zoho uses both)
   - Cache access tokens until near expiry
   - Use secure storage for refresh tokens (environment variables, secret managers)
   ```

2. **Add Custom Auth Headers section:**
   ```markdown
   ### 5. Custom Authentication Headers
   
   Some APIs use non-standard auth headers:
   - `Authorization: Zoho-oauthtoken <token>` (Zoho/Site24x7)
   - `Authorization: Bearer <token>` (standard OAuth2)
   - `X-API-Key: <key>` (API key)
   
   **Implementation:**
   ```python
   def _headers(self) -> dict[str, str]:
       token = self._get_access_token()
       return {
           "Authorization": f"Zoho-oauthtoken {token}",  # Custom header
           "Accept": "application/json",
       }
   ```
   ```

**Files to Modify:**
- `tapps_agents/experts/knowledge/api-design-integration/api-security-patterns.md`

**Testing:**
- Verify expert consultation returns refresh-token guidance when querying about OAuth2 refresh flows
- Test with domain detector to ensure `api-design-integration` domain is detected for refresh-token client code

---

### 1.2 Extend External API Integration Patterns

**Problem:** `external-api-integration.md` covers OpenWeatherMap (API key), WattTime (user/pass), AirNow (API key), but **not** OAuth2-based external APIs.

**Recommendation:** Extend `tapps_agents/experts/knowledge/api-design-integration/external-api-integration.md`

**Changes:**
1. **Add OAuth2-Based External APIs section:**
   ```markdown
   ## OAuth2-Based External APIs
   
   Many SaaS APIs (Zoho, Okta, Salesforce) use OAuth2 refresh-token flows.
   
   ### Pattern: OAuth2 Refresh-Token Client
   
   ```python
   class OAuth2ExternalAPIClient:
       def __init__(self, client_id, client_secret, refresh_token, api_base_url, token_url):
           # ... (see api-security-patterns.md for full implementation)
       
       def get(self, path: str, params: dict | None = None) -> dict:
           """Make authenticated GET request."""
           url = f"{self.api_base_url}/{path.lstrip('/')}"
           resp = requests.get(
               url,
               headers=self._headers(),
               params=params,
               timeout=self.timeout_s
           )
           resp.raise_for_status()
           return resp.json()
   ```
   
   ### Examples
   
   - **Zoho/Site24x7:** `Authorization: Zoho-oauthtoken <token>`, token endpoint: `https://accounts.zoho.com/oauth/v2/token`
   - **Okta:** `Authorization: Bearer <token>`, token endpoint: `https://<org>.okta.com/oauth2/v1/token`
   - **Salesforce:** `Authorization: Bearer <token>`, token endpoint: `https://login.salesforce.com/services/oauth2/token`
   ```

2. **Add to "Best Practices" section:**
   - Token refresh strategies (proactive vs reactive)
   - Error handling for token expiry
   - Multi-region support (e.g. Zoho EU vs US endpoints)

**Files to Modify:**
- `tapps_agents/experts/knowledge/api-design-integration/external-api-integration.md`

**Testing:**
- Verify expert consultation returns OAuth2 external API guidance when querying about external API clients with OAuth2

---

## 2. Use API-Design Experts in Reviewer and Implementer (High Priority)

### 2.1 Reviewer Enhancement

**Problem:** Reviewer only consults **security**, **performance-optimization**, and **code-quality-analysis** experts. It does **not** consult **api-design-integration** or **external-api-integration**, so it can't provide API client-specific guidance.

**Recommendation:** Add API-design expert consultation to reviewer when code appears to be an HTTP/API client.

**Changes to `tapps_agents/agents/reviewer/agent.py`:**

1. **Add domain detection for API clients:**
   ```python
   async def _detect_api_client_pattern(self, code: str) -> bool:
       """Detect if code appears to be an HTTP/API client."""
       api_client_indicators = [
           "requests.get", "requests.post", "httpx.Client", "httpx.AsyncClient",
           "Authorization:", "Bearer", "Zoho-oauthtoken", "X-API-Key",
           "refresh_token", "access_token", "token_url", "api_base_url",
           "class.*Client", "def get(", "def post("
       ]
       code_lower = code.lower()
       return any(indicator.lower() in code_lower for indicator in api_client_indicators)
   ```

2. **Add API-design expert consultation:**
   ```python
   # In _review_file method, after existing expert consultations:
   
   # Consult API Design expert if code appears to be an API client
   if await self._detect_api_client_pattern(code_preview):
       try:
           api_consultation = await expert_registry.consult(
               query=f"Review this API client code for best practices:\n\n{code_preview}",
               domain="api-design-integration",
               include_all=True,
               prioritize_builtin=True,
               agent_id="reviewer",
           )
           expert_guidance["api_design"] = api_consultation.weighted_answer
           expert_guidance["api_design_confidence"] = api_consultation.confidence
       except Exception:
           logger.debug("API design expert consultation failed", exc_info=True)
       
       # Also consult external-api-integration if relevant
       if "external" in code_preview.lower() or "third-party" in code_preview.lower():
           try:
               external_consultation = await expert_registry.consult(
                   query=f"Review this external API integration code:\n\n{code_preview}",
                   domain="api-design-integration",  # external-api is a subdomain
                   include_all=True,
                   prioritize_builtin=True,
                   agent_id="reviewer",
               )
               expert_guidance["external_api"] = external_consultation.weighted_answer
           except Exception:
               logger.debug("External API expert consultation failed", exc_info=True)
   ```

3. **Include API-design guidance in feedback:**
   ```python
   # In feedback_generator.py, add to expert guidance section:
   if expert_guidance:
       if "api_design" in expert_guidance:
           feedback_parts.append(
               f"\nAPI Design Expert:\n{expert_guidance['api_design'][:500]}..."
           )
       if "external_api" in expert_guidance:
           feedback_parts.append(
               f"\nExternal API Expert:\n{expert_guidance['external_api'][:300]}..."
           )
   ```

**Files to Modify:**
- `tapps_agents/agents/reviewer/agent.py` (around line 1477-1523)
- `tapps_agents/agents/reviewer/feedback_generator.py` (around line 85-98)

**Testing:**
- Unit test: Reviewer consults API-design expert when code contains `requests.get` or `Authorization:` header
- Integration test: Review an API client file, verify API-design guidance appears in feedback

---

### 2.2 Implementer Enhancement

**Problem:** Implementer only uses **security** and **performance-optimization** experts. It does **not** use **api-design-integration** when implementing API clients.

**Recommendation:** Add API-design expert consultation to implementer when implementing or refactoring API clients.

**Changes to `tapps_agents/agents/implementer/agent.py`:**

1. **Add same API client detection** (reuse from reviewer or create shared utility)

2. **Add API-design expert consultation in `implement` and `refactor` methods:**
   ```python
   # After existing expert consultations (around line 217-358):
   
   # Consult API Design expert if implementing/refactoring an API client
   if await self._detect_api_client_pattern(code_preview or description):
       try:
           api_consultation = await self.expert_registry.consult(
               query=f"Provide implementation guidance for this API client:\n\n{description or code_preview}",
               domain="api-design-integration",
               include_all=True,
               prioritize_builtin=True,
               agent_id="implementer",
           )
           expert_guidance["api_design"] = api_consultation.weighted_answer
       except Exception:
           logger.debug("API design expert consultation failed", exc_info=True)
   ```

3. **Include API-design guidance in implementation prompts**

**Files to Modify:**
- `tapps_agents/agents/implementer/agent.py` (around line 217-358)

**Testing:**
- Unit test: Implementer consults API-design expert when description contains "API client" or "OAuth2"
- Integration test: Implement an API client, verify API-design patterns are applied

---

## 3. Improve Intent Detection for "Review + Compare + Fix" (Medium Priority)

### 3.1 Add "Compare" Semantics

**Problem:** Intent parser doesn't recognize "compare to codebase" or "match our patterns" as actionable intents.

**Recommendation:** Enhance `tapps_agents/simple_mode/intent_parser.py`

**Changes:**
1. **Add "compare" keywords to review intent:**
   ```python
   self.review_keywords = [
       "review",
       "check",
       "analyze",
       "inspect",
       "examine",
       "score",
       "quality",
       "audit",
       "assess",
       "evaluate",
       "compare",  # NEW
       "compare to",
       "match",
       "align with",
       "follow patterns",
   ]
   ```

2. **Add intent parameter for "compare" behavior:**
   ```python
   # In Intent dataclass:
   compare_to_codebase: bool = False  # NEW field
   
   # In parse method, detect compare intent:
   if any(phrase in input_lower for phrase in ["compare to", "match our", "align with", "follow patterns"]):
       intent.compare_to_codebase = True
   ```

3. **Pass compare intent to reviewer:**
   - Reviewer can use this flag to attempt pattern matching (see Section 4)

**Files to Modify:**
- `tapps_agents/simple_mode/intent_parser.py`
- `tapps_agents/simple_mode/intent_parser.py` (Intent dataclass)

**Testing:**
- Unit test: "Review this and compare to our patterns" → `compare_to_codebase=True`
- Integration test: Review workflow receives compare flag

---

### 3.2 Improve Workflow Suggester for Hybrid Requests

**Problem:** When user says both "review" and "fix", suggester doesn't offer a clear path.

**Recommendation:** Enhance `tapps_agents/simple_mode/workflow_suggester.py`

**Changes:**
1. **Detect hybrid intents:**
   ```python
   def suggest_workflow(self, user_input: str, context: dict[str, Any] | None = None) -> WorkflowSuggestion | None:
       intent = self.intent_parser.parse(user_input)
       
       # Detect hybrid "review + fix" intent
       has_review = intent.type == IntentType.REVIEW or "review" in user_input.lower()
       has_fix = intent.type == IntentType.FIX or "fix" in user_input.lower()
       
       if has_review and has_fix:
           return WorkflowSuggestion(
               workflow_command=f'@simple-mode *review <file>  # Then: @simple-mode *fix <file> "issues from review"',
               workflow_type="review-then-fix",
               benefits=[
                   "Comprehensive quality analysis first",
                   "Targeted fixes based on review feedback",
                   "Quality gates after fixes",
               ],
               confidence=0.85,
               reason="Review + fix hybrid request detected",
           )
   ```

2. **Add "review-then-fix" workflow suggestion**

**Files to Modify:**
- `tapps_agents/simple_mode/workflow_suggester.py`

**Testing:**
- Unit test: "Review and fix this" → suggests review-then-fix workflow
- Integration test: Workflow suggester provides clear guidance for hybrid requests

---

### 3.3 Handle Pasted Code in Fix Workflow

**Problem:** `*fix` expects a file path, but users often paste code in chat.

**Recommendation:** Enhance fix workflow to handle pasted code.

**Option A: Document requirement clearly**
- Update `.cursor/rules/simple-mode.mdc` to state: "`*fix` requires a file path. Save pasted code to a file first."

**Option B: Auto-create temp file (future enhancement)**
- If no file provided but code is pasted, create temp file and run fix on it
- Lower priority; document requirement for now

**Files to Modify:**
- `.cursor/rules/simple-mode.mdc` (documentation)
- `tapps_agents/simple_mode/orchestrators/fix_orchestrator.py` (future: auto-create temp file)

---

## 4. "Compare to Codebase" / Project Patterns (Medium-Long Term)

### 4.1 Define Project API Client Patterns

**Problem:** No systematic way to extract "project patterns" from existing code (e.g. logging style, type hints, error handling).

**Recommendation:** Create a "pattern extractor" component.

**Design:**
1. **Pattern Extractor:**
   ```python
   class ProjectPatternExtractor:
       """Extract coding patterns from existing project files."""
       
       def extract_api_client_patterns(self, project_root: Path) -> dict[str, Any]:
           """Extract API client patterns from existing clients."""
           patterns = {
               "type_hints": "str | None",  # vs Optional[str]
               "logging": "logger.debug(...)",
               "error_handling": "try/except with logging",
               "structure": "class Client: __init__, _headers, get, post",
           }
           # Scan existing client files (backup_client.py, etc.)
           # Extract patterns
           return patterns
   ```

2. **Pattern Comparator:**
   ```python
   class PatternComparator:
       """Compare code against project patterns."""
       
       def compare(self, code: str, patterns: dict[str, Any]) -> list[str]:
           """Return list of deviations from patterns."""
           deviations = []
           # Check type hints
           # Check logging style
           # Check error handling
           return deviations
   ```

3. **Integrate with Reviewer:**
   - Reviewer can use pattern extractor + comparator when `compare_to_codebase=True`
   - Add "pattern consistency" score to review results

**Files to Create:**
- `tapps_agents/core/pattern_extractor.py` (new)
- `tapps_agents/core/pattern_comparator.py` (new)

**Files to Modify:**
- `tapps_agents/agents/reviewer/agent.py` (integrate pattern comparison)

**Testing:**
- Unit test: Pattern extractor identifies type hint style from existing files
- Integration test: Reviewer includes pattern consistency in feedback

---

### 4.2 Project Pattern Configuration

**Recommendation:** Allow projects to define patterns explicitly in `.tapps-agents/config.yaml`:

```yaml
project_patterns:
  api_clients:
    type_hints: "str | None"  # Modern Python 3.10+
    logging: "logger.debug(...)"
    error_handling: "try/except with logging"
    structure:
      - "class Client:"
      - "__init__ method"
      - "_headers method"
      - "get/post methods"
```

**Files to Modify:**
- `tapps_agents/core/config.py` (add project_patterns schema)
- `tapps_agents/core/pattern_extractor.py` (read from config)

---

## 5. Context7 and External APIs (Lower Priority)

### 5.1 Current State
Context7 is **library**-oriented (FastAPI, requests, pytest). External SaaS APIs (Site24x7, Zoho) are not libraries.

### 5.2 Recommendation
**Option A (Recommended):** Keep Context7 as-is for libraries. Rely on **expert knowledge** (Sections 1-2) for external APIs.

**Option B (Future):** Allow "external API" as first-class concept:
- Curated docs/links for common APIs (Zoho, Okta, Salesforce)
- Wire into review/implement when relevant
- Higher effort, only if many similar tasks emerge

**Decision:** Prioritize expert knowledge improvements (Sections 1-2). Consider Option B only if user feedback shows high demand.

---

## 6. Documentation and User Guidance (Quick Win)

### 6.1 Update Workflow Enforcement Guide

**Files to Modify:**
- `docs/WORKFLOW_ENFORCEMENT_GUIDE.md`

**Changes:**
- Add section: "Handling External API Clients"
- Document: "Review + compare + fix" → use two-step workflow (review then fix)
- Mention: "Compare to codebase" is best-effort until feature exists

---

### 6.2 Update When-to-Use Rules

**Files to Modify:**
- `.cursor/rules/when-to-use.mdc`

**Changes:**
- Add guidance for "review + compare + fix" requests
- Document limitations: "compare to codebase" not yet supported

---

### 6.3 Update Simple Mode Skill

**Files to Modify:**
- `.claude/skills/simple-mode/SKILL.md`

**Changes:**
- Document: `*fix` requires file path (save pasted code first)
- Document: "compare to codebase" best-effort via review feedback

---

## 7. Implementation Priority

| Priority | Recommendation | Effort | Impact |
|----------|----------------|--------|--------|
| **High** | 1.1: Add OAuth2 refresh-token patterns | Medium | High |
| **High** | 1.2: Extend external API integration | Medium | High |
| **High** | 2.1: Reviewer uses API-design experts | Medium | High |
| **High** | 2.2: Implementer uses API-design experts | Medium | High |
| **Medium** | 3.1: Add "compare" semantics | Low | Medium |
| **Medium** | 3.2: Improve workflow suggester | Low | Medium |
| **Medium** | 4.1: Pattern extractor/comparator | High | Medium |
| **Low** | 3.3: Handle pasted code in fix | Low | Low |
| **Low** | 5.2: Context7 for external APIs | High | Low |
| **Quick Win** | 6.1-6.3: Documentation updates | Low | Medium |

---

## 8. Testing Strategy

### Unit Tests
- Expert consultation returns OAuth2 refresh-token guidance
- Reviewer/implementer detect API client patterns
- Intent parser recognizes "compare" keywords
- Pattern extractor identifies project patterns

### Integration Tests
- Review API client → API-design guidance appears
- Implement API client → API-design patterns applied
- "Review + compare + fix" → suggests review-then-fix workflow

### E2E Tests
- Full workflow: Review Site24x7 client → Get API-design feedback → Apply fixes → Verify improvements

---

## 9. Related Documentation

- **User workarounds:** `docs/RECOMMENDATIONS_FOR_USING_TAPPS_AGENTS_EXTERNAL_API_CLIENTS.md`
- **Root cause analysis:** `docs/RESEARCH_WHY_TAPPS_AGENTS_MISSED_EXTERNAL_API_CLIENT_TASK.md`
- **Expert knowledge:** `tapps_agents/experts/knowledge/api-design-integration/`
- **Reviewer implementation:** `tapps_agents/agents/reviewer/agent.py`
- **Implementer implementation:** `tapps_agents/agents/implementer/agent.py`

---

## 10. Summary

**Key Framework Improvements:**
1. **Extend expert knowledge** with OAuth2 refresh-token and external OAuth2 API patterns
2. **Use API-design experts** in reviewer and implementer when handling API clients
3. **Improve intent detection** for "review + compare + fix" hybrid requests
4. **Add "compare to codebase"** capability (pattern extractor/comparator)
5. **Update documentation** to guide users on workarounds

**Expected Impact:**
- Reviewer and implementer will provide API client-specific guidance
- Users will get better suggestions for "review + compare + fix" requests
- Framework will handle OAuth2 refresh-token flows in expert knowledge
- Long-term: "compare to codebase" feature will reduce manual pattern matching
