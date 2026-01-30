# Claude Skills vs tapps-agents Experts — Review Summary

**Date:** 2026-01-30  
**Scope:** All Claude code skills (`.claude/skills/`) vs tapps-agents built-in experts (`tapps_agents/experts/`, `builtin_registry.py`, `knowledge/`).

---

## 1. Roles (Don’t Confuse)

| Concept | What it is | Where |
|--------|------------|--------|
| **Claude/Cursor Skill** | Invokable agent or composite workflow (e.g. `@reviewer`, `@backend-patterns`). Defines *who* runs and *what* they do. | `.claude/skills/` |
| **tapps-agents Expert** | Technical *domain* with a RAG knowledge base. Used by agents for guidance (e.g. security, testing, API design). | `tapps_agents/experts/` (config + `knowledge/`) |

Skills are **consumers** of experts; they are not the same thing. A skill does not need to “become” an expert.

---

## 2. Claude Skills Inventory (22 total)

### 2.1 Agent skills (invoke workflow agents)

- **analyst** — Requirements, stakeholder analysis, tech research, effort/risk  
- **architect** — System/security architecture, tech selection  
- **bug-fix-agent** — Debug → fix → test → review → commit  
- **debugger** — Error analysis, root cause  
- **designer** — API/data/UI design  
- **documenter** — Docs, README, API docs  
- **enhancer** — Prompt enhancement, requirements-for-code, implementation strategy  
- **evaluator** — Framework effectiveness, usage/workflow/quality metrics  
- **implementer** — Code generation, refactoring  
- **improver** — Refactor, optimize, improve quality  
- **ops** — Security audit, compliance, deployment  
- **orchestrator** — YAML workflow execution  
- **planner** — User stories, task breakdown  
- **reviewer** — Review, score, lint, type-check, duplication  
- **simple-mode** — Natural-language orchestrator over multiple skills  
- **tester** — Test generation and execution  

These are **roles/workflows**; they do not define new expert domains.

### 2.2 Domain/composite skills (use expert knowledge + invoke agents)

- **backend-patterns** — Uses: `api-design-integration`, `database-data-management`, `cloud-infrastructure`; invokes @architect, @designer  
- **coding-standards** — Uses: `code-quality-analysis` + `.cursor/rules/coding-style.mdc`; invokes @reviewer  
- **frontend-patterns** — Uses: `accessibility`, `user-experience`; invokes @designer, @reviewer  
- **security-review** — Uses: `security`, `data-privacy-compliance`; invokes @reviewer, @ops  

These already map to **existing** built-in experts.

### 2.3 Meta/template

- **example-custom-skill** — Template for custom skills; no expert mapping needed.

---

## 3. Built-in Experts (Current)

From `builtin_registry.py` and `knowledge/`:

- **security** — OWASP, secure coding, threat modeling  
- **performance-optimization** → `performance/`  
- **testing-strategies** → `testing/`  
- **code-quality-analysis**  
- **software-architecture**  
- **development-workflow**  
- **data-privacy-compliance**  
- **accessibility**  
- **user-experience**  
- **documentation-knowledge-management**  
- **ai-frameworks**  
- **agent-learning** (includes prompt-optimization)  
- **observability-monitoring**  
- **api-design-integration**  
- **cloud-infrastructure**  
- **database-data-management**  

---

## 4. Mapping: Skills → Experts

| Skill | Experts used | Status |
|-------|----------------|--------|
| backend-patterns | api-design-integration, database-data-management, cloud-infrastructure | All exist |
| coding-standards | code-quality-analysis | Exists |
| frontend-patterns | accessibility, user-experience | Both exist |
| security-review | security, data-privacy-compliance | Both exist |
| analyst | (Context7 + “Industry Experts” — project/customer experts) | No new built-in needed |
| architect | (Context7 + domain experts) | Covered by software-architecture, security, etc. |
| enhancer | (Context7 prompt guides + domain experts) | agent-learning has prompt-optimization |
| All other agent skills | Use Context7 and/or existing experts as needed | No new domain identified |

---

## 5. Recommendations

### 5.1 No new built-in experts required from skills

- **No Claude skill should be turned into a tapps-agents expert.**  
  Skills are agents/orchestrators; experts are domain knowledge. The domain skills (backend-patterns, coding-standards, frontend-patterns, security-review) already use the right experts; no new expert *domains* were identified.

### 5.2 Keep mapping explicit in docs

- In skill docs (and command-reference/agent-capabilities), state clearly which experts each domain skill uses (e.g. “Uses experts: api-design-integration, database-data-management, cloud-infrastructure”).  
- In expert docs, optionally list which skills consult them (e.g. “Used by: @backend-patterns, @architect”).

### 5.3 Optional: enrich prompt-enhancement knowledge

- **Enhancer** could benefit from more RAG over “prompt enhancement” and “implementation strategy” patterns.  
- **agent-learning** already has `prompt-optimization.md`. Options:  
  - Add more files under `agent-learning/` (e.g. enhancement-patterns, implementation-strategy), or  
  - Leave as-is and rely on Context7 + existing agent-learning.  
- **Recommendation:** Only add new knowledge under `agent-learning` if you see repeated enhancer gaps; no new expert *domain* is required.

### 5.4 example-custom-skill

- No change. It’s a template; no expert mapping.

---

## 6. Summary Table for Your Review

| Question | Answer |
|----------|--------|
| Should any Claude skill *become* a tapps-agents expert? | **No.** Skills are agents/workflows; experts are domains. |
| Are any domain skills missing an expert? | **No.** backend-patterns, coding-standards, frontend-patterns, security-review all use existing experts. |
| Add a new built-in expert domain because of a skill? | **No.** No skill introduced a domain not already covered. |
| Improve documentation? | **Yes.** Explicitly document “skill X uses experts A, B, C” and optionally “expert Y used by skills …”. |
| Expand expert knowledge (e.g. for Enhancer)? | **Optional.** Only under existing `agent-learning` (e.g. more prompt/enhancement docs) if you see a need. |

---

**Conclusion:** All Claude skills are either workflow/agent roles or domain composites that already consume the right tapps-agents experts. No new experts are recommended; optional doc and knowledge refinements are noted above.
