# MCP/AI Systems Comparative Score

**TappsCodingAgents-style scoring of wtthornton MCP and AI-assistant repositories**

| Document | Version | Last Updated |
|----------|---------|--------------|
| MCP_SYSTEMS_COMPARATIVE_SCORE.md | 1.2.0 | 2026-01-20 |

---

## 1. Scope and Repositories

| Repository | URL | Purpose |
|------------|-----|---------|
| **LocalMCP** (PromptMCP) | [github.com/wtthornton/LocalMCP](https://github.com/wtthornton/LocalMCP) | Prompt enhancement, todo, task breakdown; Context7 + MCP gateway |
| **codefortify** | [github.com/wtthornton/codefortify](https://github.com/wtthornton/codefortify) | Context7 MCP integration, project quality scoring, validation, 7-category analysis |
| **agentforge-mcp** | [github.com/wtthornton/agentforge-mcp](https://github.com/wtthornton/agentforge-mcp) | AgentForge MCP – AI platform with backend, frontend, MCP server, infra |
| **Agent-Forge** | `wtthornton/Agent-Forge` | **Not found** – no public repo at this path; `agentforge-mcp` may be the related MCP/AgentForge project |
| **TappsCodingAgents** | *(this project)* | SDLC orchestration: 14+ agents, Simple Mode, reviewer scoring, Context7, workflows, epic, quality gates |

---

## 2. Scoring Framework (TappsCodingAgents-Aligned)

We use a **6-category, 0–10 per category** model, with weights that sum to 1.0.  
Overall = `(sum of category_score × weight) × 10` → **0–100**.

Aligned with TappsCodingAgents concepts:

- **Complexity / scope** → Features & Scope, MCP/Protocol  
- **Security** → Code Quality & Scoring (incl. npm audit, security scans)  
- **Maintainability** → Developer Experience, Testing & Reliability  
- **Test coverage** → Testing & Reliability  
- **Performance / tooling** → MCP/Protocol, Context7/Docs

### 2.1 Category Definitions

| Category | Weight | Description | Evidence |
|----------|--------|-------------|----------|
| **MCP/Protocol** | 0.20 | MCP server quality: tools, resources, stdio/HTTP, correctness, error handling | Tools count, transport, docs |
| **Context7 / Docs** | 0.20 | Context7, library docs, RAG, framework detection, caching | resolve→query-docs, cache, SQLite/LRU |
| **Code Quality & Scoring** | 0.20 | Built-in scoring, real tools (npm audit, ESLint, coverage), quality gates | 7-cat score, fail-under, HTML/JSON |
| **Testing & Reliability** | 0.15 | Unit, integration, E2E, coverage, CI, circuit breaker | Vitest, Playwright, CI, test % |
| **Developer Experience** | 0.15 | Setup time, Docker, CLI, config, examples, troubleshooting | `npm run`, docker-compose, README |
| **Features & Scope** | 0.10 | Breadth: enhance, todo, breakdown, health, validation, etc. | Tool list, use cases |

### 2.2 Scale (per category, 0–10)

- **9–10**: Best-in-class, production-ready, well documented  
- **7–8**: Solid, minor gaps (e.g. one transport, limited formats)  
- **5–6**: Adequate, clear limitations  
- **3–4**: Partial or inconsistent  
- **0–2**: Missing or not applicable  

---

## 3. Scores by Repository

### 3.1 LocalMCP (PromptMCP)

| Category | Score | Rationale |
|----------|-------|-----------|
| **MCP/Protocol** | 8.5 | 3 core tools (enhance, todo, breakdown), stdio MCP; HTTP on 3001 for testing. Clear “no docker exec” guidance. |
| **Context7 / Docs** | 9.0 | Context7-only design, resolve→query-docs, SQLite+LRU cache, framework detection, circuit breaker. |
| **Code Quality & Scoring** | 5.0 | No built-in *project* scoring; enhancement has quality/scoring for prompts, not full codebase scoring. |
| **Testing & Reliability** | 8.0 | 23/23 tests, Context7 tests, E2E, HTML reports, `test-artifacts/`, smoke. |
| **Developer Experience** | 8.5 | Docker, `setup-cursor.js`, `mcp-config.json.example`, env overrides. |
| **Features & Scope** | 8.5 | enhance, todo, breakdown, health; RAG, task decomposition. |

**Weighted sum:**  
`(8.5×0.20 + 9.0×0.20 + 5.0×0.20 + 8.0×0.15 + 8.5×0.15 + 8.5×0.10) = 7.88`  
**Overall (0–100): 78.8**

---

### 3.2 codefortify

| Category | Score | Rationale |
|----------|-------|-----------|
| **MCP/Protocol** | 8.0 | MCP server, validation tools, patterns, `context7 serve`, `test-mcp`. |
| **Context7 / Docs** | 8.5 | Context7 integration, MCP resources, compliance checks, `.context7`. |
| **Code Quality & Scoring** | 9.5 | **7-category scoring** (Structure, Quality, Performance, Testing, Security, DevEx, Completeness); npm audit, ESLint, c8/nyc/jest; 16+ patterns; console/JSON/HTML; `--fail-under`-style usage. |
| **Testing & Reliability** | 7.5 | Vitest, MCP tests, integration, c8; less E2E/Playwright detail than LocalMCP. |
| **Developer Experience** | 8.5 | `codefortify init`, `add`, `validate`, `score`, `serve`; `context7.config.js`; React/Vue/Node. |
| **Features & Scope** | 8.0 | Scoring, validation, MCP, bundle analysis, `init`/`add`, multiple project types. |

**Weighted sum:**  
`(8.0×0.20 + 8.5×0.20 + 9.5×0.20 + 7.5×0.15 + 8.5×0.15 + 8.0×0.10) = 8.40`  
**Overall (0–100): 84.0**

---

### 3.3 agentforge-mcp

| Category | Score | Rationale |
|----------|-------|-----------|
| **MCP/Protocol** | 7.0 | MCP server in `mcp-server/`; structure suggests tools/resources; less public documentation on tool list. |
| **Context7 / Docs** | 6.0 | `.context7` present; docs do not emphasize Context7 as deeply as LocalMCP or codefortify. |
| **Code Quality & Scoring** | 5.0 | No described project-level scoring system; focus on platform/orchestration. |
| **Testing & Reliability** | 6.0 | `.github/workflows`; mixed stack (JS/TS/Java); less visible test layout. |
| **Developer Experience** | 7.0 | Backend, frontend, `mcp-server`, infra, scripts; setup appears more involved. |
| **Features & Scope** | 7.5 | Broad: backend, frontend, MCP, infra, CI/CD; agent platform vs. focused MCP toolkit. |

**Weighted sum:**  
`(7.0×0.20 + 6.0×0.20 + 5.0×0.20 + 6.0×0.15 + 7.0×0.15 + 7.5×0.10) = 6.38`  
**Overall (0–100): 63.8**

---

### 3.4 Agent-Forge (wtthornton/Agent-Forge)

**Not scored:** repository not found. If you meant **FrostLogic-AB/agent-forge** (TypeScript agent framework with MCP, RAG, etc.), it would be scored separately as a different project.

---

### 3.5 TappsCodingAgents (this project)

| Category | Score | Rationale |
|----------|-------|-----------|
| **MCP/Protocol** | 7.0 | Configures external MCP (Context7, Playwright) via `init` and `.cursor/mcp.json`; internal `MCPGateway` and tool registry (resolve-library-id, get-library-docs, Analysis, Filesystem, Git) for CLI/headless. Does not run a *standalone* MCP server that Cursor connects to with custom tools. |
| **Context7 / Docs** | 8.5 | KB-first lookup, `KBCache`, circuit breaker, fuzzy matcher, staleness/refresh; `resolve_library` + `query-docs`; library detector, analytics. Strong caching and fallbacks; Python/CLI integration rather than a Context7-dedicated MCP. |
| **Code Quality & Scoring** | 9.0 | **5-metric scoring** (complexity, security, maintainability, test_coverage, performance) plus Ruff, mypy, bandit, radon; `QualityGate` with 6 thresholds; `ReviewArtifact`; workflow loopbacks and `policy_loader`. JSON/text/markdown/HTML. Python-focused; fewer *categories* than codefortify (5 vs 7) but deeper workflow and gating. |
| **Testing & Reliability** | 8.5 | pytest, unit/integration/e2e (e2e_smoke, e2e_workflow, e2e_scenario, e2e_cli); coverage `fail_under=75`; Codecov; CI (ci.yml, e2e.yml, release.yml). Large suite (~394 test modules). |
| **Developer Experience** | 8.5 | `tapps-agents init`, `doctor`, `cursor verify`, `simple-mode`, `workflow`, `reviewer`; Cursor Skills and Rules; `.tapps-agents` config. Broad `docs/`. No Docker for the framework (Python lib); install via pip. |
| **Features & Scope** | 9.5 | **14+ agents** (analyst, planner, architect, designer, implementer, reviewer, tester, debugger, improver, documenter, ops, enhancer, orchestrator, evaluator, bug-fix-agent, simple-mode); **Simple Mode** (*build, *fix, *review, *test, *full, *epic, *refactor, etc.); workflow presets; epic execution; Beads; health; continuous-bug-fix. Broadest feature set. |

**Weighted sum:**  
`(7.0×0.20 + 8.5×0.20 + 9.0×0.20 + 8.5×0.15 + 8.5×0.15 + 9.5×0.10) = 8.40`  
**Overall (0–100): 84.0**

---

## 4. Summary Table

| System | MCP | Context7 | Quality/Scoring | Testing | DX | Features | **Overall** |
|--------|-----|----------|-----------------|---------|-----|----------|-------------|
| **codefortify** | 8.0 | 8.5 | **9.5** | 7.5 | 8.5 | 8.0 | **84.0** |
| **TappsCodingAgents** | 7.0 | 8.5 | 9.0 | **8.5** | 8.5 | **9.5** | **84.0** |
| **LocalMCP** | **8.5** | **9.0** | 5.0 | 8.0 | 8.5 | 8.5 | **78.8** |
| **agentforge-mcp** | 7.0 | 6.0 | 5.0 | 6.0 | 7.0 | 7.5 | **63.8** |
| Agent-Forge | — | — | — | — | — | — | *N/A* |

---

## 5. Comparative View

### 5.1 By Use Case

| Use Case | Best Fit | Why |
|----------|----------|-----|
| **End-to-end SDLC orchestration** | **TappsCodingAgents** | 14+ agents, Simple Mode (*build, *fix, *review, *test, *full, *epic), workflow presets, quality gates, epic execution. |
| **Project/codebase quality scoring** | **codefortify** | 7-category scoring, npm audit, ESLint, coverage, 16+ patterns, HTML/JSON. |
| **In-repo code review + gating** | **TappsCodingAgents** | Reviewer agent (5 metrics, Ruff/mypy/bandit), `QualityGate`, workflow loopbacks, `@reviewer *score` / `*review`. |
| **Prompt enhancement + Context7** | **LocalMCP** | Context7-centric, enhance/todo/breakdown, strong caching and framework detection. |
| **Full agent platform (MCP + app)** | **agentforge-mcp** | Backend, frontend, MCP, infrastructure; broader than pure MCP tooling. |
| **Validation + init for new projects** | **codefortify** or **TappsCodingAgents** | codefortify: `init`/`add`, validation, multi-framework. Tapps: `tapps-agents init`, Cursor Rules/Skills, MCP config. |
| **Task/todo and breakdown in Cursor** | **LocalMCP** | `promptmcp.todo`, `promptmcp.breakdown`. |

### 5.2 By Role in the Stack

- **TappsCodingAgents** = **Orchestration layer**: CLI + Cursor Skills + workflows; runs agents, enforces quality gates, runs epics. *Consumes* MCP (configures Context7, Playwright); can be used *together with* codefortify and LocalMCP.
- **codefortify** = **Scoring/validation MCP**: project scoring, validation, `init`/`add`; good *complement* to TappsCodingAgents for JS/TS projects.
- **LocalMCP** = **Prompt/task MCP**: enhance, todo, breakdown; good *complement* for prompt and task management in Cursor.
- **agentforge-mcp** = **Application platform**: full-stack app with MCP; different layer (runtime platform, not dev-time orchestration).

### 5.3 Strengths and Gaps

| System | Strengths | Gaps |
|--------|-----------|------|
| **TappsCodingAgents** | Broadest scope (14+ agents, Simple Mode, epic, workflows), strongest testing (pytest, 75% cov, e2e), quality gates and loopbacks, Context7 + MCP config | No standalone MCP server with custom tools; Python-focused (Ruff/mypy/bandit vs ESLint/npm); 5 vs 7 scoring categories |
| **codefortify** | Best-in-class *project* scoring (7 categories), real JS tool integration (npm audit, ESLint, c8), validation, multi-format | Context7 depth slightly below LocalMCP; less focus on prompt/todo; no SDLC orchestration |
| **LocalMCP** | Strongest Context7 usage, cache, enhance/todo/breakdown, testing | No full project/codebase scoring; narrow scope vs Tapps |
| **agentforge-mcp** | Broad platform (frontend, backend, MCP, infra) | Less documented MCP/Context7; no project scoring; heavier setup |

---

## 6. Recommendation

- **For “which is best” in a single answer:**  
  **TappsCodingAgents** and **codefortify** tie at **84.0**. **TappsCodingAgents** excels at **SDLC orchestration, breadth, and workflow** (14+ agents, Simple Mode, epic, quality gates); **codefortify** at **project scoring and validation** (7-category analysis, npm/ESLint/c8).

- **For “best” by primary goal:**
  - **SDLC orchestration, *build / *fix / *review / *epic** → **TappsCodingAgents**
  - **Code/project scoring and quality gates (especially JS/TS)** → **codefortify**
  - **Prompt enhancement and Context7/RAG** → **LocalMCP**
  - **Full agent/MCP platform** → **agentforge-mcp**

- **How TappsCodingAgents compares:**
  - **Same overall as codefortify (84.0)**, with **higher Features (9.5)** and **Testing (8.5)**, and **lower MCP (7.0)** and **Code Quality/Scoring (9.0 vs 9.5)**. Tapps does not run a standalone MCP server; it configures Context7/Playwright and uses an internal MCPGateway for CLI. Its strength is **orchestration and workflow**, not net-new MCP tools.
  - **Use TappsCodingAgents as the main orchestration layer** (Simple Mode, workflows, reviewer, epic). **Add codefortify** for JS/TS project scoring and validation, and **LocalMCP** for prompt enhancement and todo/breakdown in Cursor.

---

## 7. Methodology Notes

- Scores are based on **public README, docs, and structure** (LocalMCP, codefortify, agentforge-mcp) and on **in-repo implementation** for **TappsCodingAgents** (`ReviewArtifact`, `ScoringWeightsConfig`, `QualityGate`, `MCPGateway`, `context7.lookup`, `pytest.ini`, etc.).
- **TappsCodingAgents** is scored as an **orchestration framework** (CLI + Cursor Skills + workflows); it configures and uses MCP rather than publishing a standalone MCP server with custom tools.
- **agentforge-mcp**: limited public detail on MCP tools and Context7; scores are conservative.
- **Agent-Forge** at `wtthornton/Agent-Forge` was not found; if a different URL or fork is intended, the framework above can be applied to it.

---

## 8. Improvement Recommendations

To make TappsCodingAgents **decisively better** than the other systems, see **[MCP_SYSTEMS_IMPROVEMENT_RECOMMENDATIONS.md](MCP_SYSTEMS_IMPROVEMENT_RECOMMENDATIONS.md)**. It turns gaps and strengths of LocalMCP, codefortify, and agentforge-mcp into **7 actionable recommendations** (plus 2 deferred, 1 removed):

- **P0:** 7-category scoring (Structure, DevEx)
- **P1:** npm audit, `*enhance` / `*breakdown` in Simple Mode, `*todo` (Beads-backed), JS/TS coverage (Vitest, Jest, c8/nyc)
- **P2:** Architecture pattern detection (8–10 patterns), bundle analysis (opt-in)

**Deferred:** Tapps MCP Server, Docker. **Removed:** SQLite+LRU for Context7 cache (no proven impact).

Implementing P0 and P1 is estimated to raise TappsCodingAgents’ overall score to **~85–86** (vs 84 today).

---

## 9. References

- [LocalMCP (PromptMCP)](https://github.com/wtthornton/LocalMCP)  
- [codefortify](https://github.com/wtthornton/codefortify)  
- [agentforge-mcp](https://github.com/wtthornton/agentforge-mcp)  
- [MCP_SYSTEMS_IMPROVEMENT_RECOMMENDATIONS.md](MCP_SYSTEMS_IMPROVEMENT_RECOMMENDATIONS.md) – Improvement ideas from competing systems  
- **TappsCodingAgents** (this project): `ReviewArtifact`, `ScoringWeightsConfig`, `QualityGate`, `reviewer_handler`, `MCPGateway`, `context7.lookup`, `KBCache`
