# TappsMCP: Standalone MCP Server for LLM Code Quality

**Status:** Draft (Revised after code audit + architecture review)
**Created:** 2026-02-07
**Revised:** 2026-02-07
**Source:** TappsCodingAgents evaluation — extracting the highest-value components into a standalone MCP server

> **Code Audit Note (2026-02-07):** This plan was revised after a deep review of
> the actual TappsCodingAgents codebase (~200+ Python files across reviewer, quality,
> context7, experts, core, workflow, and mcp packages). The original draft missed
> ~60 extractable modules, an existing MCP infrastructure, and several security-critical
> components. All findings are incorporated below.

> **Architecture Review Note (2026-02-07):** Plan updated with recommendations from
> cross-referencing the plan against the actual codebase. Key changes: (1) reframed
> existing MCP infra as "adapt + significantly extend" since it doesn't speak MCP wire
> protocol, (2) extraction map marked as draft pending Task 0.2 import graph analysis,
> (3) merged `tapps_lint` into `tapps_score_file` with `quick` mode to reduce tool count,
> (4) added `TAPPS_MCP_PROJECT_ROOT` hard enforcement to security section, (5) scoped
> session notes to project root, (6) moved Docker image from Phase 1 to Phase 5,
> (7) adjusted Phase 2b LOE from 2-3 weeks to 3-4 weeks with optional deferrals,
> (8) added MCP resources/prompts evaluation to Phase 5.

---

## Why TappsMCP Exists

LLMs writing code make predictable, repeatable mistakes. These aren't random — they follow patterns that a deterministic tool layer can catch and correct. TappsMCP moves the proven quality infrastructure from TappsCodingAgents out of prompt injection and into MCP tools, so any LLM (Opus, Sonnet, Haiku, GPT, Gemini, DeepSeek, Codestral) gets reliable quality enforcement without consuming context window on framework instructions.

### LLM Error Sources TappsMCP Addresses

| Error Source | What Goes Wrong | TappsMCP Tool | How It Helps |
|---|---|---|---|
| **Hallucinated APIs** | LLM confidently uses methods that don't exist or have wrong signatures | `tapps_lookup_docs` | Returns real, current library documentation at the moment the LLM is writing the call |
| **Skipped edge cases** | LLM writes happy path, forgets error handling, null checks, boundary conditions | `tapps_score_file` | Bandit + static analysis catches unhandled exceptions, missing input validation |
| **Missed tests** | LLM implements feature and says "done" without adequate test coverage | `tapps_quality_gate` | Enforces coverage thresholds — returns `passed: false` until tests exist |
| **Security blindspots** | LLM introduces SQL injection, XSS, hardcoded secrets, insecure defaults | `tapps_security_scan` | Bandit security scanning + secret detection returns specific findings |
| **Scope drift** | LLM refactors adjacent code, adds abstractions nobody asked for, over-engineers | `tapps_project_profile` | Returns project constraints and tech stack — keeps LLM focused on what exists |
| **Stale knowledge** | LLM uses deprecated APIs, old patterns, pre-training-cutoff library versions | `tapps_lookup_docs` | Context7 integration returns up-to-date docs, not training data |
| **Wrong domain patterns** | LLM applies web patterns to CLI tools, uses SQL idioms in NoSQL code | `tapps_consult_expert` | Domain-specific knowledge retrieval — 16 built-in technical domains |
| **Inconsistent quality** | Output quality varies wildly between models, prompts, and context sizes | `tapps_quality_gate` | Same deterministic gate for all models — score is score regardless of who produced the code |
| **Lost context in long sessions** | By step 7, LLM has forgotten constraints from step 1 | `tapps_session_notes` | Server-side note persistence — LLM can save and retrieve key decisions/constraints at any point |
| **Self-review bias** | LLM "reviews" its own code and confirms its own assumptions | `tapps_score_file` | External objective metrics — ruff, mypy, bandit, radon don't have confirmation bias |
| **Misinterpreted tool output** | LLM runs linter via bash, misparses output, reports wrong score | All tools | Structured JSON responses — no parsing, no misinterpretation |
| **Unsafe config files** | LLM writes Dockerfiles with root user, docker-compose with exposed ports | `tapps_validate_config` | Deterministic config validation against best practices |
| **Prompt injection via RAG** | Malicious content in knowledge files or docs manipulates LLM behavior | `tapps_consult_expert` | `rag_safety.py` scans all retrieved content for injection patterns before returning |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│  LLM Client (Claude Code, Cursor, any MCP host) │
│                                                   │
│  System prompt: ~50 lines                         │
│  "Use tapps tools for scoring, docs, gates"       │
│                                                   │
│  Tool calls: tapps_score_file, tapps_lookup_docs  │
│              tapps_quality_gate, tapps_checklist  │
└──────────────────┬──────────────────────────────┘
                   │ MCP Protocol (stdio or SSE)
                   ▼
┌─────────────────────────────────────────────────┐
│              TappsMCP Server                      │
│                                                   │
│  ┌──────────┐ ┌──────────┐ ┌───────────────┐    │
│  │ Scoring  │ │ Context7 │ │ Expert System │    │
│  │ Engine   │ │ Docs     │ │ (16 domains)  │    │
│  │          │ │          │ │               │    │
│  │ ruff     │ │ KB cache │ │ RAG retrieval │    │
│  │ mypy     │ │ fuzzy    │ │ confidence    │    │
│  │ bandit   │ │ match    │ │ scoring       │    │
│  │ radon    │ │ refresh  │ │               │    │
│  │ jscpd    │ │ queue    │ │               │    │
│  └──────────┘ └──────────┘ └───────────────┘    │
│                                                   │
│  ┌──────────┐ ┌──────────┐ ┌───────────────┐    │
│  │ Quality  │ │ Project  │ │ Checklist &   │    │
│  │ Gates    │ │ Profile  │ │ Session Notes │    │
│  │          │ │          │ │               │    │
│  │ thresholds│ │ tech stack│ │ call log     │    │
│  │ pluggable│ │ detection│ │ key-value     │    │
│  │ registry │ │ config   │ │ persistence   │    │
│  └──────────┘ └──────────┘ └───────────────┘    │
└─────────────────────────────────────────────────┘
```

### Existing MCP Infrastructure (IMPORTANT — Adapt + Significantly Extend)

TappsCodingAgents already has an MCP module at `tapps_agents/mcp/` that provides foundational **patterns**, but these modules are internal wrappers — they do **not** speak MCP wire protocol (stdio/SSE). The `ToolRegistry` registers handlers as Python callables (not MCP-compliant tool definitions with JSON Schema), and the `MCPGateway` routes calls internally but doesn't implement MCP transport. Reuse the architectural patterns, but budget significant effort for wiring to the MCP Python SDK.

| Existing File | What It Provides | Reuse Strategy |
|---|---|---|
| `mcp/tool_registry.py` | `ToolRegistry`, `ToolDefinition`, `ToolCategory` enum | **Adapt + extend** — reuse registry pattern, rewrite serialization to MCP JSON Schema format |
| `mcp/gateway.py` | `MCPGateway` — routes tool calls, standard result wrapping | **Adapt + extend** — reuse routing pattern, implement MCP SDK `@server.tool()` transport layer |
| `mcp/servers/analysis.py` | `AnalysisMCPServer` — registers `score_code`, `detect_issues`, `analyze_complexity` | **Reference** — handler logic is useful, but needs new MCP-compliant wrapper |
| `mcp/servers/context7.py` | `Context7MCPServer` — wraps `resolve-library-id`, `get-library-docs` | **Reference** — same: useful logic, needs MCP wrapper |
| `mcp/servers/filesystem.py` | File operation tools | Reference only |
| `mcp/servers/git.py` | Git operation tools | Reference only |

**TappsMCP should build ON these patterns, not ignore them.** The registry/gateway architecture is sound, but adapting it to the MCP Python SDK's `@server.tool()` decorator pattern and stdio/SSE transport is a **significant rewrite** of the transport layer (budget 2-3 days in Phase 0, not a single task item).

### Design Principles

1. **Reuse, don't rewrite** — Extract proven code from TappsCodingAgents, not rebuild from scratch
2. **Build on existing MCP infra** — The `tapps_agents/mcp/` module already has registry, gateway, and server patterns
3. **Deterministic tools** — MCP tools run deterministic code (linters, analyzers, doc lookup), not LLM reasoning
4. **Model-agnostic** — Works with any LLM that supports MCP (Claude, GPT, Gemini, local models)
5. **Structured I/O** — All tools return typed JSON, no freeform text for the LLM to misparse
6. **Server-side state** — The MCP server maintains state, caches, and config — not the LLM's context
7. **Continuous feedback** — Tools are called inline during work, not as end-of-pipeline gates
8. **Security by default** — Path validation, I/O guardrails, prompt injection defense, PII filtering on all inputs/outputs

---

## MCP Tool Definitions

### Tier 0: Server Meta (Phase 0)

#### `tapps_server_info`
Return server version, capabilities, and installed tool checkers.

```json
{
  "name": "tapps_server_info",
  "description": "Return TappsMCP server version, available tools, and installed external checkers. Call this at the start of a session to discover capabilities and verify the server is working.",
  "inputSchema": {
    "type": "object",
    "properties": {}
  }
}
```

**Returns:**
```json
{
  "version": "0.1.0",
  "protocol_version": "2024-11-05",
  "tools_available": ["tapps_server_info", "tapps_score_file", "tapps_security_scan", "tapps_quality_gate", "tapps_checklist"],
  "external_tools": {
    "ruff": {"installed": true, "version": "0.8.4"},
    "mypy": {"installed": true, "version": "1.13.0"},
    "bandit": {"installed": false, "install_hint": "pip install bandit"},
    "radon": {"installed": true, "version": "6.0.1"},
    "coverage": {"installed": false, "install_hint": "pip install coverage"}
  },
  "config": {
    "project_root": "/path/to/project",
    "quality_preset": "standard",
    "config_source": "env_vars"
  }
}
```

### Tier 1: Core Quality (Phase 1)

#### `tapps_score_file`
Score a file using objective quality metrics.

```json
{
  "name": "tapps_score_file",
  "description": "Score code quality using static analysis (ruff, mypy, bandit, radon). Returns objective metrics across 7 categories. Call this after writing or modifying code to catch issues early.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "file_path": {"type": "string", "description": "Path to the file to score"},
      "categories": {
        "type": "array",
        "items": {"type": "string", "enum": ["complexity", "security", "maintainability", "test_coverage", "performance", "structure", "devex"]},
        "description": "Categories to score (default: all)"
      },
      "quick": {"type": "boolean", "description": "Fast mode — ruff only, < 500ms. Use for tight edit-lint-fix loops (default: false)"},
      "fix": {"type": "boolean", "description": "Auto-fix ruff issues. Requires quick: true (default: false)"}
    },
    "required": ["file_path"]
  }
}
```

**Returns:**
```json
{
  "overall": 82.3,
  "categories": {
    "complexity": {"score": 8.2, "details": "Cyclomatic complexity avg 4.3"},
    "security": {"score": 9.0, "issues": []},
    "maintainability": {"score": 7.5, "mi_score": 68.2},
    "test_coverage": {"score": 6.0, "coverage_pct": 60.0},
    "performance": {"score": 8.8, "details": "No deep nesting, no oversized functions"},
    "structure": {"score": 9.0, "details": "Standard project layout"},
    "devex": {"score": 8.0, "details": "Docs, tooling config present"}
  },
  "ruff_issues": [{"code": "F401", "message": "unused import", "line": 3}],
  "mypy_errors": [],
  "bandit_findings": [],
  "tool_versions": {"ruff": "0.8.x", "mypy": "1.13.x", "bandit": "1.8.x"}
}
```

**Reuses from TappsCodingAgents:**
- `tapps_agents/agents/reviewer/scoring.py` — `CodeScorer`, `BaseScorer`
- `tapps_agents/agents/reviewer/score_constants.py` — scoring constants
- `tapps_agents/agents/reviewer/maintainability_scorer.py` — MI calculations
- `tapps_agents/agents/reviewer/performance_scorer.py` — performance analysis
- `tapps_agents/agents/reviewer/typescript_scorer.py` — TypeScript support
- `tapps_agents/agents/reviewer/react_scorer.py` — React/JSX support
- `tapps_agents/agents/reviewer/tools/ruff_grouping.py` — ruff output grouping
- `tapps_agents/agents/reviewer/tools/scoped_mypy.py` — scoped mypy execution
- `tapps_agents/agents/reviewer/tools/parallel_executor.py` — parallel tool execution
- `tapps_agents/agents/reviewer/validation.py` — input validation
- `tapps_agents/agents/reviewer/scorer_registry.py` — scorer plugin system
- `tapps_agents/agents/reviewer/adaptive_scorer.py` — adaptive weight learning
- `tapps_agents/agents/reviewer/pattern_detector.py` — detects RAG, multi-agent, weighted-decision patterns (standalone)
- `tapps_agents/agents/reviewer/context_detector.py` — file age/status for context-aware gates (standalone)
- `tapps_agents/agents/reviewer/score_validator.py` — validates score integrity (standalone)
- `tapps_agents/agents/reviewer/metric_strategies.py` — pluggable metric strategies (standalone)
- `tapps_agents/agents/reviewer/library_patterns.py` — library-specific scoring patterns (standalone)
- `tapps_agents/agents/reviewer/library_detector.py` — detects libraries used in code (standalone)
- `tapps_agents/agents/reviewer/output_enhancer.py` — enriches scoring output (standalone)
- `tapps_agents/mcp/servers/analysis.py` — existing `AnalysisMCPServer` with `score_code` handler

#### ~~`tapps_lint`~~ — Merged into `tapps_score_file`

> **Architecture review decision:** `tapps_lint` has been merged into `tapps_score_file`
> as a `quick: true` fast path. Fewer tools = less cognitive load for LLMs deciding which
> to call. The fast linting use case (ruff only, < 500ms, auto-fix support) is now accessed
> via `tapps_score_file` with `quick: true`. If user feedback after Phase 1 indicates strong
> demand for a dedicated lint tool, it can be split back out in a later phase.
>
> The `tapps_score_file` schema above already includes `quick` and `fix` parameters to
> support this use case. When `quick: true`, only ruff is executed (no mypy, bandit, radon),
> and the response includes `ruff_issues` with fix suggestions. When `fix: true` (requires
> `quick: true`), ruff auto-fixes are applied and the response includes a `fixes_applied` count.

#### `tapps_security_scan`
Scan for security vulnerabilities.

```json
{
  "name": "tapps_security_scan",
  "description": "Scan code for security vulnerabilities using bandit (Python) and custom pattern detection. Returns OWASP-categorized findings.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "file_path": {"type": "string"},
      "scan_secrets": {"type": "boolean", "description": "Also scan for hardcoded secrets (default: true)"}
    },
    "required": ["file_path"]
  }
}
```

**Reuses from TappsCodingAgents:**
- `tapps_agents/quality/secret_scanner.py` — secret detection
- `tapps_agents/quality/enforcement.py` — gate enforcement
- `tapps_agents/core/security_scanner.py` — standalone `SecurityScanner` (cleaner Bandit wrapper than scoring.py's inline version)
- `tapps_agents/quality/gates/security_gate.py` — `SecurityGate` with PII/credential/secret checking
- `tapps_agents/experts/governance.py` — `GovernanceLayer` for filtering secrets/PII from responses
- Bandit integration from `scoring.py`

#### `tapps_quality_gate`
Check if code meets quality thresholds.

```json
{
  "name": "tapps_quality_gate",
  "description": "Check if a file passes quality gates. Returns pass/fail with specific failures. The LLM MUST call this before declaring work complete.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "file_path": {"type": "string"},
      "preset": {
        "type": "string",
        "enum": ["standard", "strict", "framework"],
        "description": "Gate preset (standard: 70+, strict: 80+, framework: 75+ with 8.5 security)"
      }
    },
    "required": ["file_path"]
  }
}
```

**Returns:**
```json
{
  "passed": false,
  "score": 68.5,
  "threshold": 70.0,
  "failures": ["security: 6.2 < 7.0 minimum", "test_coverage: 45% < 75% minimum"],
  "warnings": ["maintainability: 7.2 approaching 7.0 minimum"],
  "recommendation": "Add input validation for user-facing endpoints. Add tests for auth_handler and token_refresh."
}
```

**Reuses from TappsCodingAgents:**
- `tapps_agents/quality/quality_gates.py` — `QualityGate`, `QualityGateResult`, `QualityThresholds`
- `tapps_agents/quality/gates/registry.py` — pluggable gate registry
- `tapps_agents/quality/gates/base.py` — `BaseGate`, `GateResult`, `GateSeverity` (base for all gates)
- `tapps_agents/quality/gates/security_gate.py` — `SecurityGate` (secrets, PII, credentials)
- `tapps_agents/quality/gates/policy_gate.py` — policy-based gating
- `tapps_agents/quality/gates/exceptions.py` — gate-specific exceptions
- `tapps_agents/quality/coverage_analyzer.py` — `CoverageAnalyzer`, `CoverageMetrics`, `CoverageReport` (required for test_coverage gate)
- `tapps_agents/core/config.py` — `QualityGatesConfig`

> **Note:** `core/predictive_gates.py` was referenced in the original draft but does not exist.
> Predictive analysis lives in the adaptive scorer and checkpoint systems instead.

#### `tapps_checklist`
Soft enforcement — verify the LLM has called required tools before declaring work complete.

> **Design rationale:** The system prompt tells the LLM to call `tapps_quality_gate` before declaring work complete, but LLMs frequently skip instructions — especially in long sessions. `tapps_checklist` provides a server-side mechanism to catch these skips. The LLM calls it at the end of a task, and the server checks its own call log to report which recommended tools were never invoked. This is "soft enforcement" — the checklist doesn't block, but it gives the LLM a clear signal to go back and do the work.

```json
{
  "name": "tapps_checklist",
  "description": "Check which recommended tools have been called in this session. Call this before declaring work complete. Returns a list of tools that should have been called but weren't.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "task_type": {
        "type": "string",
        "enum": ["feature", "bugfix", "refactor", "config", "general"],
        "description": "Type of task (affects which tools are recommended). Default: general"
      }
    }
  }
}
```

**Returns:**
```json
{
  "passed": false,
  "called": ["tapps_score_file"],
  "missing": [
    {"tool": "tapps_quality_gate", "reason": "Quality gate was never checked — call this before declaring work complete"},
    {"tool": "tapps_lookup_docs", "reason": "Code uses 'fastapi' but docs were never looked up — risk of hallucinated APIs"}
  ],
  "optional_missing": [
    {"tool": "tapps_security_scan", "reason": "No dedicated security scan was run (tapps_score_file includes basic security scoring)"}
  ]
}
```

**Implementation:** Server-side call log tracking. No extraction from TappsCodingAgents — this is new logic specific to MCP server-side enforcement. Lightweight (~50 lines of code).

### Tier 2: Knowledge (Phase 2)

#### `tapps_lookup_docs`
Look up library documentation.

```json
{
  "name": "tapps_lookup_docs",
  "description": "Look up current library/framework documentation. Use this BEFORE writing code that uses external libraries to avoid hallucinating APIs.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "library": {"type": "string", "description": "Library name (e.g., 'fastapi', 'react', 'sqlalchemy')"},
      "topic": {"type": "string", "description": "Specific topic (e.g., 'dependency-injection', 'hooks', 'routing')"}
    },
    "required": ["library"]
  }
}
```

**Reuses from TappsCodingAgents:**
- `tapps_agents/context7/kb_cache.py` — KB cache with TTL, staleness detection
- `tapps_agents/context7/cache_structure.py` — atomic writes, race-condition safe
- `tapps_agents/context7/fuzzy_matcher.py` — library name fuzzy matching with language hints
- `tapps_agents/context7/backup_client.py` — Context7 API client
- `tapps_agents/context7/circuit_breaker.py` — fail-fast on API failures
- `tapps_agents/context7/cache_warming.py` — pre-warm cache for detected dependencies
- `tapps_agents/context7/cache_prewarm.py` — alternative pre-warm from detected deps
- `tapps_agents/context7/lookup.py` — lookup orchestration
- `tapps_agents/context7/security.py` — SecretStr API key handling
- `tapps_agents/context7/staleness_policies.py` — `StalenessPolicy`, per-library TTL rules (standalone)
- `tapps_agents/context7/refresh_queue.py` — `RefreshTask` queue for async cache updates (standalone)
- `tapps_agents/context7/cache_locking.py` — file-based locking for concurrent access (standalone)
- `tapps_agents/context7/cache_metadata.py` — cache metadata management (standalone)
- `tapps_agents/context7/analytics.py` — cache hit/miss analytics (standalone)
- `tapps_agents/context7/cleanup.py` — cache cleanup policies (standalone)
- `tapps_agents/context7/credential_validation.py` — API key validation (standalone)
- `tapps_agents/context7/bundle_loader.py` — offline bundle loading for air-gapped environments (standalone)
- `tapps_agents/context7/language_detector.py` — language detection (**Note: NOT at `core/language_detector.py`**)
- `tapps_agents/context7/cross_references.py` — cross-reference between docs (standalone)
- `tapps_agents/mcp/servers/context7.py` — existing `Context7MCPServer` with library resolution

#### `tapps_consult_expert`
Consult domain experts.

```json
{
  "name": "tapps_consult_expert",
  "description": "Consult a domain expert for specialized guidance. Use when facing domain-specific decisions (security, performance, accessibility, database design, etc.).",
  "inputSchema": {
    "type": "object",
    "properties": {
      "domain": {
        "type": "string",
        "enum": ["security", "performance", "testing", "data-privacy", "accessibility", "ux", "code-quality", "architecture", "devops", "documentation", "ai-frameworks", "observability", "api-design", "cloud-infrastructure", "database", "agent-learning"],
        "description": "Expert domain"
      },
      "question": {"type": "string", "description": "Specific question for the expert"},
      "context": {"type": "string", "description": "Code or architectural context for the question"}
    },
    "required": ["domain", "question"]
  }
}
```

**Reuses from TappsCodingAgents:**
- `tapps_agents/experts/expert_engine.py` — core consultation engine
- `tapps_agents/experts/expert_registry.py` — expert registration and lookup
- `tapps_agents/experts/builtin_registry.py` — 16 built-in domain experts
- `tapps_agents/experts/simple_rag.py` — file-based RAG (no vector DB required)
- `tapps_agents/experts/vector_rag.py` — FAISS-based semantic search with auto-fallback to simple_rag (optional, high value)
- `tapps_agents/experts/rag_chunker.py` — chunk knowledge files for vector RAG
- `tapps_agents/experts/rag_embedder.py` — embedding generation for vector RAG
- `tapps_agents/experts/rag_index.py` — vector index management for vector RAG
- `tapps_agents/experts/rag_safety.py` — **prompt injection defense for RAG** (critical for MCP security)
- `tapps_agents/experts/rag_evaluation.py` — RAG quality evaluation
- `tapps_agents/experts/rag_metrics.py` — RAG performance metrics
- `tapps_agents/experts/domain_detector.py` — detect which domains are relevant
- `tapps_agents/experts/adaptive_domain_detector.py` — improved adaptive domain detection
- `tapps_agents/experts/confidence_calculator.py` — response confidence scoring
- `tapps_agents/experts/confidence_breakdown.py` — detailed confidence metrics
- `tapps_agents/experts/confidence_metrics.py` — confidence metric models
- `tapps_agents/experts/knowledge/` — 119 knowledge files across 16 domains
- `tapps_agents/experts/knowledge_freshness.py` — knowledge file staleness tracking (standalone)
- `tapps_agents/experts/knowledge_validator.py` — validate knowledge files (standalone)
- `tapps_agents/experts/knowledge_ingestion.py` — ingest new knowledge (standalone)
- `tapps_agents/experts/adaptive_voting.py` — expert voting weight adaptation
- `tapps_agents/experts/weight_distributor.py` — expert weight distribution
- `tapps_agents/experts/performance_tracker.py` — track expert accuracy over time
- `tapps_agents/experts/governance.py` — `GovernanceLayer` for filtering secrets/PII from responses (critical)
- `tapps_agents/experts/expert_suggester.py` — suggests relevant experts for a task (standalone)
- `tapps_agents/experts/base_expert.py` — base expert class
- `tapps_agents/experts/domain_config.py` — domain configuration
- `tapps_agents/experts/domain_utils.py` — domain utility functions
- `tapps_agents/experts/expert_config.py` — expert configuration models
- `tapps_agents/experts/cache.py` — expert response caching
- `tapps_agents/experts/history_logger.py` — consultation history logging
- `tapps_agents/experts/observability.py` — expert system observability
- `tapps_agents/experts/report_generator.py` — expert report generation

#### `tapps_list_experts`
List available expert domains and their capabilities.

```json
{
  "name": "tapps_list_experts",
  "description": "List available expert domains. Call this at the start of a task to understand what specialized knowledge is available.",
  "inputSchema": {
    "type": "object",
    "properties": {}
  }
}
```

### Tier 3: Project Context (Phase 3)

#### `tapps_project_profile`
Detect project characteristics.

```json
{
  "name": "tapps_project_profile",
  "description": "Detect project tech stack, dependencies, and configuration. Call once at the start of a task to understand the project context.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "project_root": {"type": "string", "description": "Project root path (default: current directory)"}
    }
  }
}
```

**Returns:**
```json
{
  "languages": ["python"],
  "frameworks": ["fastapi", "sqlalchemy"],
  "test_framework": "pytest",
  "package_manager": "pip",
  "has_ci": true,
  "has_docker": false,
  "deployment_type": "cloud",
  "security_level": "standard",
  "quality_config": {
    "min_score": 70,
    "security_min": 7.0,
    "test_coverage_min": 75
  }
}
```

**Reuses from TappsCodingAgents:**
- `tapps_agents/core/project_profile.py` — `ProjectProfile`, `ProjectProfileDetector` (coupled to `workflow.detector`)
- `tapps_agents/workflow/detector.py` — `ProjectDetector` (tech stack detection)
- `tapps_agents/context7/language_detector.py` — language detection (**NOT `core/language_detector.py`** — that path does not exist)
- `tapps_agents/context7/library_detector.py` — library/dependency detection
- `tapps_agents/core/project_type_detector.py` — project type detection
- `tapps_agents/core/stack_analyzer.py` — `StackAnalyzer` for comprehensive tech stack analysis
- `tapps_agents/core/ast_parser.py` — `ModuleInfo`, `FunctionInfo`, `ClassInfo` code structure extraction (standalone)

#### `tapps_session_notes`
Lightweight key-value note storage for maintaining context across a session.

> **Design note:** This replaces the original `tapps_workflow_state` which was full checkpoint/restore. Session notes provide lightweight context persistence (e.g., "auth_approach: JWT", "db: postgres", "constraints: must support offline") without reimplementing workflow orchestration. Full state management is deferred to Phase 5 as an optional advanced tool for power users.

```json
{
  "name": "tapps_session_notes",
  "description": "Save and retrieve key-value notes for this session. Use 'save' to record a decision or constraint, 'get' to retrieve it later, 'list' to see all notes. Useful for maintaining context across long sessions.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "action": {"type": "string", "enum": ["save", "get", "list", "clear"]},
      "key": {"type": "string", "description": "Note key (for save/get)"},
      "value": {"type": "string", "description": "Note value (for save)"}
    },
    "required": ["action"]
  }
}
```

**Returns (list action):**
```json
{
  "session_id": "abc-123",
  "notes": {
    "auth_approach": "JWT with refresh tokens",
    "database": "PostgreSQL 16",
    "constraints": "Must support offline mode, max 3 external dependencies",
    "files_modified": "src/auth.py, src/middleware.py, tests/test_auth.py"
  },
  "note_count": 4,
  "session_started": "2026-02-07T10:30:00Z"
}
```

**Implementation:** Server-side in-memory dict per session, persisted to `{TAPPS_MCP_PROJECT_ROOT}/.tapps-mcp/sessions/{session_id}.json` as JSON for crash recovery. Notes are scoped to the project root to prevent context leakage between projects in multi-project setups. No extraction from TappsCodingAgents — this is simpler than the workflow state system.

### Tier 4: Extended Tools (Phase 3+)

These tools were identified during code audit as high-value additions built from existing modules.

#### `tapps_validate_config`
Validate configuration files (Dockerfiles, docker-compose, etc.).

```json
{
  "name": "tapps_validate_config",
  "description": "Validate configuration files for best practices and security. Supports Dockerfile, docker-compose.yml, and infrastructure configs.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "file_path": {"type": "string", "description": "Path to config file"},
      "config_type": {
        "type": "string",
        "enum": ["dockerfile", "docker-compose", "auto"],
        "description": "Config type (default: auto-detect)"
      }
    },
    "required": ["file_path"]
  }
}
```

**Reuses from TappsCodingAgents:**
- `tapps_agents/agents/reviewer/dockerfile_validator.py` — `DockerfileValidator` (standalone)
- `tapps_agents/agents/reviewer/docker_compose_validator.py` — `DockerComposeValidator` (standalone)
- `tapps_agents/agents/reviewer/websocket_validator.py` — WebSocket pattern validation (standalone)
- `tapps_agents/agents/reviewer/mqtt_validator.py` — MQTT pattern validation (standalone)
- `tapps_agents/agents/reviewer/influxdb_validator.py` — InfluxDB pattern validation (standalone)

#### `tapps_impact_analysis`
Analyze the impact of a code change on the project.

```json
{
  "name": "tapps_impact_analysis",
  "description": "Analyze which files and modules are affected by a change. Use before large refactors to understand blast radius.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "file_path": {"type": "string", "description": "File being changed"},
      "change_type": {"type": "string", "enum": ["added", "modified", "removed"], "description": "Type of change"}
    },
    "required": ["file_path"]
  }
}
```

**Reuses from TappsCodingAgents:**
- `tapps_agents/core/change_impact_analyzer.py` — `ChangeImpactAnalyzer`, `ChangeImpact`, `ChangeImpactReport`
- `tapps_agents/core/ast_parser.py` — code structure extraction for dependency analysis
- `tapps_agents/agents/reviewer/service_discovery.py` — discovers services in monorepo (standalone)

#### `tapps_report`
Generate a quality report from score data.

```json
{
  "name": "tapps_report",
  "description": "Generate a formatted quality report from scoring data. Returns JSON, markdown, or HTML.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "file_path": {"type": "string", "description": "File to report on (or omit for project-wide)"},
      "format": {"type": "string", "enum": ["json", "markdown", "html"], "description": "Report format (default: json)"}
    }
  }
}
```

**Reuses from TappsCodingAgents:**
- `tapps_agents/agents/reviewer/report_generator.py` — `ReportGenerator` multi-format reports (standalone, optional jinja2)
- `tapps_agents/agents/reviewer/aggregator.py` — aggregates multi-file results
- `tapps_agents/experts/report_generator.py` — expert report generation

---

## Security Hardening (Required for MCP)

An MCP server accepting file paths and queries from untrusted LLMs requires security hardening beyond what a framework-internal tool needs. These modules MUST be extracted in Phase 1.

| Module | What It Provides | Priority |
|---|---|---|
| `core/path_validator.py` | `assert_write_allowed()` — prevents directory traversal in all file-path tools | **Phase 1** |
| `core/io_guardrails.py` | `sanitize_for_log()`, `detect_likely_prompt_injection()` — sanitize all inputs | **Phase 1** |
| `experts/rag_safety.py` | Prompt injection defense for RAG-retrieved content (regex pattern matching) | **Phase 1** |
| `experts/governance.py` | `GovernanceLayer` — filter secrets/PII/credentials from tool responses | **Phase 1** |
| `context7/security.py` | `SecretStr` handling for API keys | **Phase 1** |
| `quality/gates/security_gate.py` | `SecurityGate` with PII/credential/secret detection | **Phase 2** |
| `context7/credential_validation.py` | API key format validation | **Phase 2** |

### Security Rules for MCP Tools

1. **Project root boundary (CRITICAL):** All `file_path` parameters must be resolved to absolute paths and confirmed to be within `TAPPS_MCP_PROJECT_ROOT`. This is a **hard enforcement** — if `TAPPS_MCP_PROJECT_ROOT` is set, no file I/O is permitted outside that directory tree. If not set, it defaults to the current working directory. This prevents a rogue LLM from scanning or scoring arbitrary files on the filesystem. Implemented via `path_validator.assert_write_allowed()` which must check both directory traversal AND project root containment.
2. **All `file_path` parameters** must pass `assert_write_allowed()` before any file I/O (includes project root check from rule 1)
3. **All log output** must pass through `sanitize_for_log()` to strip control characters
4. **All RAG-retrieved content** must pass through `rag_safety.py` prompt injection detection
5. **All tool responses** containing knowledge must pass through `GovernanceLayer` PII filter
6. **API keys** must use `SecretStr` — never appear in logs, responses, or error messages
7. **No rate limiting required (Phase 1):** The project root boundary (rule 1) provides sufficient protection against filesystem enumeration. Rate limiting can be evaluated in Phase 5 if abuse patterns emerge.

---

## Windows Compatibility

TappsCodingAgents is actively developed on Windows. TappsMCP must maintain cross-platform support.

**Key module:** `tapps_agents/core/subprocess_utils.py` — `wrap_windows_cmd_shim()` which wraps subprocess calls for Windows `.cmd` shims (ruff, mypy, etc. installed via npm/pip on Windows use `.cmd` wrappers).

**Rules:**
- All subprocess calls to external tools (ruff, mypy, bandit) must use `wrap_windows_cmd_shim()`
- File path handling must use `pathlib.Path` (already the pattern in TappsCodingAgents)
- Cache file locking must work on Windows (no `fcntl` — use `msvcrt` or cross-platform lib)
- Test suite must pass on both Windows and Linux/macOS

---

## Code Extraction Map

> **DRAFT NOTICE:** This extraction map is a best-effort assessment based on code review.
> Many modules marked "copy directly" or "standalone" may have hidden transitive imports
> to framework utilities (`core/exceptions.py`, `core/config.py`, logging helpers, etc.).
> **Task 0.2 (dependency analysis)** will run import graph analysis on all modules listed
> below and produce the definitive extraction map. The Phase 1-3 extraction lists should
> be revised based on Task 0.2 findings before extraction begins. Treat this section as
> the starting point, not the final word.

### What to copy directly (high reuse, low coupling)

#### Existing MCP Infrastructure (Phase 0 — adapt and extend)

| Source Module | Target Module | Coupling Notes |
|---|---|---|
| `mcp/tool_registry.py` | `tapps_mcp/core/tool_registry.py` | **Adapt + extend** — reuse registry pattern, rewrite for MCP JSON Schema serialization |
| `mcp/gateway.py` | `tapps_mcp/core/gateway.py` | **Adapt + extend** — reuse routing pattern, implement MCP SDK transport layer |
| `mcp/servers/analysis.py` | `tapps_mcp/servers/analysis.py` | **Reference + rewrite** — handler logic useful, needs MCP-compliant wrapper |
| `mcp/servers/context7.py` | `tapps_mcp/servers/context7.py` | **Reference + rewrite** — handler logic useful, needs MCP-compliant wrapper |

#### Security Hardening (Phase 1 — mandatory)

| Source Module | Target Module | Coupling Notes |
|---|---|---|
| `core/path_validator.py` | `tapps_mcp/security/path_validator.py` | Standalone — `assert_write_allowed()` |
| `core/io_guardrails.py` | `tapps_mcp/security/io_guardrails.py` | Standalone — `sanitize_for_log()`, `detect_likely_prompt_injection()` |
| `experts/rag_safety.py` | `tapps_mcp/security/rag_safety.py` | Standalone — prompt injection defense patterns |
| `experts/governance.py` | `tapps_mcp/security/governance.py` | Uses `GovernancePolicy` — decouple from expert base |

#### Scoring Engine (Phase 1)

| Source Module | Target Module | Coupling Notes |
|---|---|---|
| `agents/reviewer/scoring.py` | `tapps_mcp/scoring/scorer.py` | Remove `ProjectConfig` + `Language` imports, accept config as dict |
| `agents/reviewer/score_constants.py` | `tapps_mcp/scoring/constants.py` | No changes needed |
| `agents/reviewer/maintainability_scorer.py` | `tapps_mcp/scoring/maintainability.py` | Standalone |
| `agents/reviewer/performance_scorer.py` | `tapps_mcp/scoring/performance.py` | Standalone |
| `agents/reviewer/typescript_scorer.py` | `tapps_mcp/scoring/typescript.py` | Standalone |
| `agents/reviewer/react_scorer.py` | `tapps_mcp/scoring/react.py` | Standalone |
| `agents/reviewer/validation.py` | `tapps_mcp/scoring/validation.py` | Standalone |
| `agents/reviewer/scorer_registry.py` | `tapps_mcp/scoring/registry.py` | Standalone plugin system |
| `agents/reviewer/adaptive_scorer.py` | `tapps_mcp/scoring/adaptive.py` | Remove agent base dependency |
| `agents/reviewer/pattern_detector.py` | `tapps_mcp/scoring/pattern_detector.py` | Standalone — RAG/multi-agent/weighted patterns |
| `agents/reviewer/context_detector.py` | `tapps_mcp/scoring/context_detector.py` | Standalone — file age/status for context-aware gates |
| `agents/reviewer/score_validator.py` | `tapps_mcp/scoring/score_validator.py` | Standalone — validates score integrity |
| `agents/reviewer/metric_strategies.py` | `tapps_mcp/scoring/metric_strategies.py` | Standalone — pluggable metrics |
| `agents/reviewer/library_patterns.py` | `tapps_mcp/scoring/library_patterns.py` | Standalone — library-specific scoring |
| `agents/reviewer/library_detector.py` | `tapps_mcp/scoring/library_detector.py` | Standalone — detect libraries in code |
| `agents/reviewer/output_enhancer.py` | `tapps_mcp/scoring/output_enhancer.py` | Standalone — enriches scoring output |
| `agents/reviewer/report_generator.py` | `tapps_mcp/scoring/report_generator.py` | Standalone — multi-format reports (optional jinja2) |
| `agents/reviewer/aggregator.py` | `tapps_mcp/scoring/aggregator.py` | Standalone — multi-file result aggregation |
| `core/security_scanner.py` | `tapps_mcp/security/security_scanner.py` | Standalone — cleaner Bandit wrapper |

#### Tools (Phase 1)

| Source Module | Target Module | Coupling Notes |
|---|---|---|
| `agents/reviewer/tools/ruff_grouping.py` | `tapps_mcp/tools/ruff.py` | Standalone |
| `agents/reviewer/tools/scoped_mypy.py` | `tapps_mcp/tools/mypy.py` | Standalone |
| `agents/reviewer/tools/parallel_executor.py` | `tapps_mcp/tools/parallel.py` | Standalone |
| `core/subprocess_utils.py` | `tapps_mcp/tools/subprocess_utils.py` | Standalone — `wrap_windows_cmd_shim()` |
| `utils/subprocess_runner.py` | `tapps_mcp/tools/subprocess_runner.py` | Standalone — `run_command()` / `run_command_async()` |

#### Quality Gates (Phase 1)

| Source Module | Target Module | Coupling Notes |
|---|---|---|
| `quality/quality_gates.py` | `tapps_mcp/gates/quality_gates.py` | Nearly standalone, extract gate registry |
| `quality/gates/base.py` | `tapps_mcp/gates/base.py` | Standalone — `BaseGate`, `GateResult`, `GateSeverity` |
| `quality/gates/registry.py` | `tapps_mcp/gates/registry.py` | Standalone — pluggable gate registry |
| `quality/gates/security_gate.py` | `tapps_mcp/gates/security_gate.py` | Coupled (uses `governance.py`) — extract together |
| `quality/gates/policy_gate.py` | `tapps_mcp/gates/policy_gate.py` | Unknown coupling — evaluate |
| `quality/gates/exceptions.py` | `tapps_mcp/gates/exceptions.py` | Standalone |
| `quality/secret_scanner.py` | `tapps_mcp/security/secret_scanner.py` | Standalone |
| `quality/enforcement.py` | `tapps_mcp/gates/enforcement.py` | Minimal coupling |
| `quality/coverage_analyzer.py` | `tapps_mcp/gates/coverage_analyzer.py` | Standalone — required for test_coverage gate |

#### Config Validators (Phase 2)

| Source Module | Target Module | Coupling Notes |
|---|---|---|
| `agents/reviewer/dockerfile_validator.py` | `tapps_mcp/validators/dockerfile.py` | Standalone |
| `agents/reviewer/docker_compose_validator.py` | `tapps_mcp/validators/docker_compose.py` | Standalone |
| `agents/reviewer/websocket_validator.py` | `tapps_mcp/validators/websocket.py` | Standalone |
| `agents/reviewer/mqtt_validator.py` | `tapps_mcp/validators/mqtt.py` | Standalone |
| `agents/reviewer/influxdb_validator.py` | `tapps_mcp/validators/influxdb.py` | Standalone |
| `agents/reviewer/service_discovery.py` | `tapps_mcp/validators/service_discovery.py` | Standalone |

#### Knowledge Layer (Phase 2)

| Source Module | Target Module | Coupling Notes |
|---|---|---|
| `context7/kb_cache.py` | `tapps_mcp/knowledge/kb_cache.py` | Remove framework config coupling |
| `context7/cache_structure.py` | `tapps_mcp/knowledge/cache_structure.py` | Standalone (atomic writes) |
| `context7/fuzzy_matcher.py` | `tapps_mcp/knowledge/fuzzy_matcher.py` | Standalone |
| `context7/backup_client.py` | `tapps_mcp/knowledge/context7_client.py` | Standalone HTTP client |
| `context7/circuit_breaker.py` | `tapps_mcp/knowledge/circuit_breaker.py` | Standalone |
| `context7/lookup.py` | `tapps_mcp/knowledge/lookup.py` | Orchestration — adapt |
| `context7/security.py` | `tapps_mcp/security/api_keys.py` | SecretStr handling |
| `context7/staleness_policies.py` | `tapps_mcp/knowledge/staleness_policies.py` | Standalone |
| `context7/refresh_queue.py` | `tapps_mcp/knowledge/refresh_queue.py` | Uses staleness_policies |
| `context7/cache_warming.py` | `tapps_mcp/knowledge/cache_warming.py` | Standalone |
| `context7/cache_prewarm.py` | `tapps_mcp/knowledge/cache_prewarm.py` | Standalone |
| `context7/cache_locking.py` | `tapps_mcp/knowledge/cache_locking.py` | Standalone |
| `context7/cache_metadata.py` | `tapps_mcp/knowledge/cache_metadata.py` | Standalone |
| `context7/analytics.py` | `tapps_mcp/knowledge/analytics.py` | Standalone |
| `context7/cleanup.py` | `tapps_mcp/knowledge/cleanup.py` | Standalone |
| `context7/credential_validation.py` | `tapps_mcp/knowledge/credential_validation.py` | Standalone |
| `context7/bundle_loader.py` | `tapps_mcp/knowledge/bundle_loader.py` | Standalone — air-gapped support |
| `context7/language_detector.py` | `tapps_mcp/project/language.py` | Standalone |
| `context7/cross_references.py` | `tapps_mcp/knowledge/cross_references.py` | Standalone |
| `context7/library_detector.py` | `tapps_mcp/project/library_detector.py` | Standalone |

#### Expert System (Phase 2)

| Source Module | Target Module | Coupling Notes |
|---|---|---|
| `experts/expert_engine.py` | `tapps_mcp/experts/engine.py` | Remove agent coupling |
| `experts/expert_registry.py` | `tapps_mcp/experts/registry.py` | Standalone |
| `experts/builtin_registry.py` | `tapps_mcp/experts/builtins.py` | Standalone |
| `experts/base_expert.py` | `tapps_mcp/experts/base_expert.py` | Core base class |
| `experts/simple_rag.py` | `tapps_mcp/experts/rag.py` | Standalone file-based RAG |
| `experts/vector_rag.py` | `tapps_mcp/experts/vector_rag.py` | Optional FAISS — auto-fallback to simple_rag |
| `experts/rag_chunker.py` | `tapps_mcp/experts/rag_chunker.py` | Needed by vector_rag |
| `experts/rag_embedder.py` | `tapps_mcp/experts/rag_embedder.py` | Needed by vector_rag |
| `experts/rag_index.py` | `tapps_mcp/experts/rag_index.py` | Needed by vector_rag |
| `experts/rag_evaluation.py` | `tapps_mcp/experts/rag_evaluation.py` | Standalone |
| `experts/rag_metrics.py` | `tapps_mcp/experts/rag_metrics.py` | Standalone |
| `experts/domain_detector.py` | `tapps_mcp/experts/domain_detector.py` | Standalone |
| `experts/adaptive_domain_detector.py` | `tapps_mcp/experts/adaptive_domain_detector.py` | Standalone |
| `experts/confidence_calculator.py` | `tapps_mcp/experts/confidence.py` | Standalone |
| `experts/confidence_breakdown.py` | `tapps_mcp/experts/confidence_breakdown.py` | Standalone |
| `experts/confidence_metrics.py` | `tapps_mcp/experts/confidence_metrics.py` | Standalone |
| `experts/knowledge/` (119 files) | `tapps_mcp/experts/knowledge/` | Copy entire directory |
| `experts/knowledge_freshness.py` | `tapps_mcp/experts/knowledge_freshness.py` | Standalone |
| `experts/knowledge_validator.py` | `tapps_mcp/experts/knowledge_validator.py` | Standalone |
| `experts/knowledge_ingestion.py` | `tapps_mcp/experts/knowledge_ingestion.py` | Standalone |
| `experts/expert_suggester.py` | `tapps_mcp/experts/expert_suggester.py` | Standalone |
| `experts/domain_config.py` | `tapps_mcp/experts/domain_config.py` | Standalone |
| `experts/domain_utils.py` | `tapps_mcp/experts/domain_utils.py` | Standalone |
| `experts/expert_config.py` | `tapps_mcp/experts/expert_config.py` | Standalone |
| `experts/cache.py` | `tapps_mcp/experts/cache.py` | Standalone |
| `experts/history_logger.py` | `tapps_mcp/experts/history_logger.py` | Standalone |
| `experts/observability.py` | `tapps_mcp/experts/observability.py` | Standalone |
| `experts/report_generator.py` | `tapps_mcp/experts/report_generator.py` | Standalone |

#### Project Context (Phase 3)

| Source Module | Target Module | Coupling Notes |
|---|---|---|
| `core/project_profile.py` | `tapps_mcp/project/profile.py` | Decouple from workflow.detector |
| `core/project_type_detector.py` | `tapps_mcp/project/type_detector.py` | Standalone |
| `core/stack_analyzer.py` | `tapps_mcp/project/stack_analyzer.py` | Standalone |
| `core/ast_parser.py` | `tapps_mcp/project/ast_parser.py` | Standalone — code structure extraction |
| `core/change_impact_analyzer.py` | `tapps_mcp/project/impact_analyzer.py` | Standalone |
| `workflow/detector.py` | `tapps_mcp/project/detector.py` | Tech stack detection — extract relevant parts |

#### Adaptive Learning (Phase 4)

| Source Module | Target Module | Coupling Notes |
|---|---|---|
| `agents/reviewer/adaptive_scorer.py` | `tapps_mcp/scoring/adaptive.py` | Remove agent base dependency |
| `experts/adaptive_voting.py` | `tapps_mcp/experts/adaptive_voting.py` | Standalone |
| `experts/weight_distributor.py` | `tapps_mcp/experts/weight_distributor.py` | Standalone |
| `experts/performance_tracker.py` | `tapps_mcp/experts/performance_tracker.py` | Standalone |
| `core/adaptive_scoring.py` | `tapps_mcp/scoring/adaptive_weights.py` | Standalone — adaptive weight system |

#### Session Notes (Phase 3) — replaces State Management

`tapps_session_notes` is a new lightweight implementation (key-value store + JSON persistence), not extracted from TappsCodingAgents. No source modules to copy.

#### State Management (Phase 5, optional — full workflow state for power users)

| Source Module | Target Module | Coupling Notes |
|---|---|---|
| `workflow/state_manager.py` | `tapps_mcp/state/manager.py` | Heavy coupling — extract state persistence only |
| `workflow/durable_state.py` | `tapps_mcp/state/durable_state.py` | Decouple from workflow models |
| `workflow/checkpoint_manager.py` | `tapps_mcp/state/checkpoints.py` | Standalone save/restore |
| `workflow/execution_metrics.py` | `tapps_mcp/state/metrics.py` | Standalone metrics |

### What NOT to copy (framework-specific)

| Module | Why Not |
|---|---|
| `agents/*/agent.py` | Agent base classes, LLM instruction objects — framework orchestration |
| `workflow/cursor_executor.py` | Cursor-specific workflow execution |
| `workflow/skill_invoker.py` | Cursor Skills invocation |
| `workflow/cursor_chat.py` | Cursor chat integration |
| `workflow/cursor_skill_helper.py` | Cursor skill helper |
| `workflow/agent_handlers/` | All agent handlers — framework orchestration, not tool logic |
| `workflow/quality_loopback.py` | Invokes @improver agent — framework orchestration |
| `workflow/remediation_loop.py` | Coupled to evaluation models — framework orchestration |
| `workflow/worktree_manager.py` | Git worktree management — framework-specific |
| `simple_mode/` | Prompt orchestration — the LLM client handles this now |
| `cli/` | CLI is a TappsCodingAgents concern, TappsMCP is a server |
| `agents/enhancer/` | Prompt enhancement — LLM reasoning, not a tool |
| `epic/` | Epic management — framework orchestration |
| `core/agent_base.py` | Agent base class — framework-specific |
| `core/llm_communicator.py` | LLM communication — framework-specific |
| `core/llm_behavior.py` | LLM behavior modeling — framework-specific |
| `core/skill_integration.py` | Cursor Skills integration — framework-specific |
| `experts/agent_integration.py` | Wires experts into agent handlers — framework-specific |
| `experts/auto_generator.py` | Auto-generates experts from prompts — framework-specific (could be Phase 5) |
| `experts/proactive_orchestrator.py` | Proactive expert invocation — framework orchestration |
| `experts/setup_wizard.py` | Expert system setup — framework-specific |
| `context7/agent_integration.py` | Wires context7 into agents — framework-specific |
| `context7/commands.py` | CLI commands for context7 — framework-specific |
| `context7/tiles_integration.py` | Cursor tiles integration — framework-specific |
| `resources/claude/skills/` | Skill prompts — replaced by MCP tool descriptions |
| `agents/reviewer/batch_review.py` | Coupled to `ReviewerAgent` — framework-specific |
| `agents/reviewer/phased_review.py` | Multi-phase review — framework orchestration |
| `agents/reviewer/progressive_review.py` | Progressive task-level review — framework orchestration |
| `agents/reviewer/context7_enhancer.py` | Wires context7 into reviewer — framework-specific |

---

## Lessons Learned to Carry Forward

From TappsCodingAgents development (audit fix, 1381 tests, 4 phases of hardening):

1. **Atomic file writes** — Use `tempfile.mkstemp` + `os.replace` for cache writes (C6 fix). Already in `cache_structure.py`.
2. **Timezone-aware datetimes** — Always use `datetime.now(UTC)`, never naive datetimes (C3 fix).
3. **Path validation** — Validate all file paths to prevent directory traversal (C2 fix). Already in `cache_structure.py` and `agent_integration.py`.
4. **Specific exception handling** — Never `except Exception`, always specific catches (H2 fix). Use the exception hierarchy from `core/exceptions.py`.
5. **Copy-before-iterate** — When iterating collections that might be modified concurrently, copy first (H4 fix, event_bus.py).
6. **File size limits** — Enforce `MAX_CACHE_FILE_SIZE` on cached content (H7 fix).
7. **SecretStr for API keys** — Never log or expose API keys in plain text (M9 fix).
8. **Circuit breakers** — Wrap external API calls with circuit breakers for fail-fast (context7 pattern).
9. **TTL on cached data** — Cache entries have `fetched_at` and `is_expired(ttl)` (M7 fix).
10. **Graceful degradation** — If ruff/mypy/bandit aren't installed, degrade gracefully with `HAS_RUFF`, `HAS_BANDIT` flags.
11. **Windows subprocess shims** — Use `wrap_windows_cmd_shim()` from `core/subprocess_utils.py` for all external tool calls. Windows npm/pip installs use `.cmd` wrappers that need special handling.
12. **RAG safety** — All knowledge retrieved from files must pass prompt injection detection before being returned to LLMs. Patterns in `experts/rag_safety.py`.
13. **PII/secret governance** — Expert responses and knowledge lookups must pass through `GovernanceLayer` to filter secrets, tokens, credentials, and PII before reaching the LLM.

---

## Synchronization Strategy

TappsCodingAgents will continue evolving after TappsMCP is extracted. Without a clear synchronization strategy, the codebases will diverge and bug fixes in one will not propagate to the other.

### Recommended Approach: Shared `tapps-core` Package (Phase 6)

| Option | Pros | Cons | Recommendation |
|---|---|---|---|
| **One-time fork + independent evolution** | Simple, no coupling | Bug fixes don't propagate, double maintenance | Phase 0-3 only (pragmatic start) |
| **Shared `tapps-core` package** | Single source of truth for scoring, gates, security, experts | Requires refactoring both repos to depend on shared package | **Target for Phase 6** |
| **Monorepo with workspaces** | Everything in one repo, atomic changes | Heavy migration, complex CI | Evaluate if team grows |

**Plan:**
1. **Phases 0-3:** One-time fork. Accept divergence during extraction. Track upstream changes in a `SYNC_LOG.md`.
2. **Phase 6 (post-launch):** Extract the truly shared modules (scoring engine, quality gates, security layer, expert system core) into a `tapps-core` PyPI package. Both `tapps-agents` and `tapps-mcp` depend on `tapps-core`.
3. **Ongoing:** Bug fixes to shared logic go into `tapps-core`. Both consumers get them via version bumps.

**Modules likely to move into `tapps-core`:**
- `scoring/` (scorer, constants, registry, validators)
- `gates/` (base, quality gates, security gate, enforcement)
- `security/` (path validator, io guardrails, rag safety, governance)
- `knowledge/` (kb cache, fuzzy matcher, circuit breaker, context7 client)
- `experts/` core (engine, registry, builtins, base expert, simple RAG)

---

## Performance Budget

MCP tools are called inline during coding. If a tool takes too long, the developer experience degrades. All tools must meet latency targets.

### Target Latencies

| Tool | Target (p95) | Notes |
|---|---|---|
| `tapps_server_info` | < 50ms | In-memory, no I/O |
| `tapps_score_file` (quick mode) | < 500ms | Ruff only, fast path |
| `tapps_score_file` | < 3s | Parallel execution of ruff + mypy + bandit + radon |
| `tapps_security_scan` | < 2s | Bandit + secret scanner |
| `tapps_quality_gate` | < 5s | Runs full scoring + gate evaluation |
| `tapps_checklist` | < 100ms | Server-side state lookup |
| `tapps_lookup_docs` (cache hit) | < 500ms | Local file I/O only |
| `tapps_lookup_docs` (cache miss) | < 5s | Context7 API call + cache write |
| `tapps_consult_expert` | < 2s | RAG retrieval + confidence scoring |
| `tapps_list_experts` | < 100ms | In-memory registry |
| `tapps_project_profile` | < 3s | File system scanning + detection |
| `tapps_session_notes` | < 100ms | Local file I/O |
| `tapps_impact_analysis` | < 5s | AST parsing + dependency graph |
| `tapps_report` | < 2s | Formatting only (data already scored) |
| `tapps_validate_config` | < 1s | Pattern matching, no external tools |

### Implementation Notes

- `tapps_score_file` (full mode) uses `parallel_executor.py` to run ruff, mypy, bandit, and radon concurrently. Sequential execution would take ~8-12s.
- `tapps_score_file` (quick mode) runs ruff only — target < 500ms for tight edit-lint-fix loops.
- `tapps_lookup_docs` should return cached results immediately. The `refresh_queue.py` can update stale entries in the background without blocking the response.
- All tools should include `elapsed_ms` in their response so clients can monitor performance degradation.

---

## Error Handling Strategy

### Standard Error Response Schema

All tools must return structured errors when they cannot function. This prevents the LLM from misinterpreting failures.

```json
{
  "error": true,
  "error_code": "tool_unavailable",
  "tool": "ruff",
  "message": "ruff is not installed or not found in PATH",
  "install_hint": "pip install ruff",
  "partial_results": {},
  "degraded": false
}
```

### Error Codes

| Code | Meaning | LLM Action |
|---|---|---|
| `tool_unavailable` | External tool (ruff, mypy, etc.) not installed | Suggest installation, skip category |
| `file_not_found` | Target file does not exist | LLM should verify file path |
| `path_denied` | Path validation rejected the file path (directory traversal, outside project) | LLM should not retry |
| `timeout` | Tool execution exceeded time limit | LLM may retry once |
| `api_unavailable` | External API (Context7) unreachable | Fall back to cached/bundled data |
| `degraded_result` | Partial result — some tools ran, others failed | Use `partial_results` |
| `config_error` | Server misconfiguration | Report to user |

### Graceful Degradation Rules

When external tools are missing, the server degrades gracefully:

| Missing Tool | Affected MCP Tool | Degradation |
|---|---|---|
| `ruff` | `tapps_score_file` (full and quick mode) | Skip lint category, warn in response |
| `mypy` | `tapps_score_file` | Skip type-checking category, warn |
| `bandit` | `tapps_security_scan`, `tapps_score_file` | Skip security static analysis, warn |
| `radon` | `tapps_score_file` | Skip complexity metrics, warn |
| `coverage` | `tapps_quality_gate` | Skip test coverage gate, warn |
| Context7 API key | `tapps_lookup_docs` | Fall back to bundled/cached docs |
| `faiss-cpu` | `tapps_consult_expert` | Fall back to `simple_rag` (file-based) |

The `tapps_server_info` tool reports which tools are available so the LLM knows what to expect before calling other tools.

---

## Versioning & Compatibility

### Semantic Versioning

TappsMCP follows [semver](https://semver.org/):
- **Major:** Breaking changes to tool input/output schemas
- **Minor:** New tools added, new optional fields in responses
- **Patch:** Bug fixes, performance improvements, knowledge base updates

### Version Discovery

The `tapps_server_info` tool (Tier 0, Phase 0) provides version and capability discovery. LLM clients should call this first.

### Compatibility Matrix

| TappsMCP Version | MCP Protocol | Python | Breaking Changes |
|---|---|---|---|
| 0.1.x (Phase 1) | 2024-11-05+ | ≥3.12 | N/A (initial release) |
| 0.2.x (Phase 2) | 2024-11-05+ | ≥3.12 | None — additive tools only |
| 0.3.x (Phase 3) | 2024-11-05+ | ≥3.12 | None — additive tools only |
| 1.0.0 (Phase 5) | 2024-11-05+ | ≥3.12 | Stable API contract |

### Response Schema Stability

Once a tool is released, its response schema is **append-only**:
- New fields may be added (minor version bump)
- Existing fields are never removed or renamed (would require major version bump)
- Enum values may be added but never removed

---

## Test Extraction Map

All extracted modules must maintain their original test coverage. This maps source tests to target test files.

### Approximate Test Distribution

| Source Test Area | Approx. Tests | Target Test File(s) | Phase |
|---|---|---|---|
| `tests/unit/agents/reviewer/test_scoring*.py` | ~80 | `test_scoring.py` | 1 |
| `tests/unit/agents/reviewer/test_*_scorer.py` | ~40 | `test_scoring.py` | 1 |
| `tests/unit/agents/reviewer/test_*_validator.py` | ~30 | `test_validators.py` | 2a |
| `tests/unit/quality/test_quality_gates.py` | ~25 | `test_gates.py` | 1 |
| `tests/unit/quality/test_gates_*.py` | ~20 | `test_gates.py` | 1 |
| `tests/unit/quality/test_secret_scanner.py` | ~15 | `test_security.py` | 1 |
| `tests/unit/context7/test_kb_cache.py` | ~30 | `test_knowledge.py` | 2a |
| `tests/unit/context7/test_fuzzy_matcher.py` | ~20 | `test_knowledge.py` | 2a |
| `tests/unit/context7/test_cache_*.py` | ~25 | `test_knowledge.py` | 2a |
| `tests/unit/experts/test_expert_engine.py` | ~20 | `test_experts.py` | 2b |
| `tests/unit/experts/test_simple_rag.py` | ~15 | `test_experts.py` | 2b |
| `tests/unit/experts/test_rag_safety.py` | ~10 | `test_security.py` | 0 |
| `tests/unit/core/test_path_validator.py` | ~10 | `test_security.py` | 0 |
| `tests/unit/core/test_project_profile.py` | ~15 | `test_project.py` | 3 |
| `tests/unit/core/test_change_impact*.py` | ~10 | `test_project.py` | 3 |
| MCP protocol / integration | ~15 | `test_server.py` | 0-1 |
| **Total ported** | **~380** | | |

### Test Porting Rules

1. **Port, don't rewrite** — Adapt import paths and fixture setup, keep test logic intact
2. **Cross-platform tests** — All ported tests must pass on Windows and Linux
3. **Mock boundaries** — Mock at the subprocess boundary (ruff, mypy, bandit calls), not internal functions
4. **Coverage target** — Ported modules must maintain ≥80% coverage in TappsMCP

---

## Project Structure

```
tapps-mcp/
├── pyproject.toml
├── README.md
├── src/
│   └── tapps_mcp/
│       ├── __init__.py
│       ├── server.py                  # MCP server entry point (stdio + SSE)
│       ├── config.py                  # Server configuration
│       ├── checklist.py               # tapps_checklist — call log tracking + enforcement
│       ├── session_notes.py           # tapps_session_notes — key-value note storage
│       │
│       ├── common/                    # Shared utilities (from Phase 0 dependency analysis)
│       │   ├── __init__.py
│       │   ├── exceptions.py          # Exception hierarchy (extracted from core/exceptions.py)
│       │   ├── logging.py             # Logging helpers
│       │   └── models.py              # Shared Pydantic models (config, results)
│       │
│       ├── core/                      # ← from mcp/ (existing infrastructure)
│       │   ├── __init__.py
│       │   ├── tool_registry.py       # ToolRegistry, ToolDefinition (extend existing)
│       │   └── gateway.py             # MCPGateway routing (extend existing)
│       │
│       ├── scoring/                   # ← from agents/reviewer/
│       │   ├── __init__.py
│       │   ├── scorer.py              # CodeScorer, BaseScorer
│       │   ├── constants.py           # Score constants
│       │   ├── maintainability.py     # MI scorer
│       │   ├── performance.py         # Performance scorer
│       │   ├── typescript.py          # TS scorer
│       │   ├── react.py              # React scorer
│       │   ├── adaptive.py           # Adaptive weight learning
│       │   ├── adaptive_weights.py   # Core adaptive weight system
│       │   ├── registry.py           # Scorer plugin system
│       │   ├── validation.py         # Input validation
│       │   ├── pattern_detector.py   # RAG/multi-agent/weighted pattern detection
│       │   ├── context_detector.py   # File age/status for context-aware gates
│       │   ├── score_validator.py    # Score integrity validation
│       │   ├── metric_strategies.py  # Pluggable metric strategies
│       │   ├── library_patterns.py   # Library-specific scoring patterns
│       │   ├── library_detector.py   # Detect libraries in code
│       │   ├── output_enhancer.py    # Enrich scoring output
│       │   ├── report_generator.py   # Multi-format reports (JSON, markdown, HTML)
│       │   └── aggregator.py         # Multi-file result aggregation
│       │
│       ├── tools/                     # ← from agents/reviewer/tools/ + core/
│       │   ├── __init__.py
│       │   ├── ruff.py               # Ruff integration
│       │   ├── mypy.py               # Scoped mypy
│       │   ├── parallel.py           # Parallel tool executor
│       │   ├── subprocess_utils.py   # Windows cmd shim (from core/subprocess_utils.py)
│       │   └── subprocess_runner.py  # run_command() / run_command_async()
│       │
│       ├── gates/                     # ← from quality/
│       │   ├── __init__.py
│       │   ├── base.py               # BaseGate, GateResult, GateSeverity
│       │   ├── quality_gates.py       # QualityGate, thresholds
│       │   ├── registry.py            # Pluggable gate registry
│       │   ├── security_gate.py       # SecurityGate (secrets, PII, credentials)
│       │   ├── policy_gate.py         # Policy-based gating
│       │   ├── exceptions.py          # Gate-specific exceptions
│       │   ├── enforcement.py         # Gate enforcement
│       │   └── coverage_analyzer.py   # CoverageAnalyzer, CoverageMetrics
│       │
│       ├── security/                  # ← from quality/ + context7/ + core/ + experts/
│       │   ├── __init__.py
│       │   ├── secret_scanner.py      # Secret detection
│       │   ├── security_scanner.py    # Standalone Bandit wrapper (from core/)
│       │   ├── api_keys.py           # SecretStr handling
│       │   ├── path_validator.py     # Directory traversal prevention (from core/)
│       │   ├── io_guardrails.py      # Input sanitization + prompt injection detection (from core/)
│       │   ├── rag_safety.py         # RAG prompt injection defense (from experts/)
│       │   └── governance.py         # PII/secret filtering for responses (from experts/)
│       │
│       ├── validators/                # ← from agents/reviewer/ (config validation)
│       │   ├── __init__.py
│       │   ├── dockerfile.py          # Dockerfile best practices
│       │   ├── docker_compose.py      # Docker Compose validation
│       │   ├── websocket.py           # WebSocket pattern validation
│       │   ├── mqtt.py                # MQTT pattern validation
│       │   ├── influxdb.py            # InfluxDB pattern validation
│       │   └── service_discovery.py   # Service discovery in monorepos
│       │
│       ├── knowledge/                 # ← from context7/
│       │   ├── __init__.py
│       │   ├── kb_cache.py           # KB cache with TTL
│       │   ├── cache_structure.py    # Atomic writes
│       │   ├── fuzzy_matcher.py      # Library name matching
│       │   ├── context7_client.py    # Context7 API client
│       │   ├── circuit_breaker.py    # Fail-fast wrapper
│       │   ├── lookup.py            # Lookup orchestration
│       │   ├── cache_warming.py     # Pre-warm for detected deps
│       │   ├── cache_prewarm.py     # Alternative pre-warm
│       │   ├── cache_locking.py     # File-based locking for concurrent access
│       │   ├── cache_metadata.py    # Cache metadata management
│       │   ├── staleness_policies.py # Per-library TTL rules
│       │   ├── refresh_queue.py     # Async cache refresh queue
│       │   ├── analytics.py         # Cache hit/miss analytics
│       │   ├── cleanup.py           # Cache cleanup policies
│       │   ├── credential_validation.py # API key format validation
│       │   ├── bundle_loader.py     # Offline bundle loading (air-gapped)
│       │   └── cross_references.py  # Cross-reference between docs
│       │
│       ├── experts/                   # ← from experts/
│       │   ├── __init__.py
│       │   ├── engine.py             # Expert consultation engine
│       │   ├── registry.py           # Expert registration
│       │   ├── builtins.py           # 16 built-in domains
│       │   ├── base_expert.py        # Base expert class
│       │   ├── rag.py               # Simple file-based RAG
│       │   ├── vector_rag.py        # Optional FAISS semantic search (auto-fallback)
│       │   ├── rag_chunker.py       # Knowledge file chunking
│       │   ├── rag_embedder.py      # Embedding generation
│       │   ├── rag_index.py         # Vector index management
│       │   ├── rag_evaluation.py    # RAG quality evaluation
│       │   ├── rag_metrics.py       # RAG performance metrics
│       │   ├── domain_detector.py   # Domain detection
│       │   ├── adaptive_domain_detector.py # Adaptive domain detection
│       │   ├── domain_config.py     # Domain configuration
│       │   ├── domain_utils.py      # Domain utility functions
│       │   ├── expert_config.py     # Expert configuration models
│       │   ├── expert_suggester.py  # Suggest relevant experts
│       │   ├── confidence.py        # Confidence scoring
│       │   ├── confidence_breakdown.py # Detailed confidence metrics
│       │   ├── confidence_metrics.py # Confidence metric models
│       │   ├── adaptive_voting.py   # Voting weight adaptation
│       │   ├── weight_distributor.py # Expert weight distribution
│       │   ├── performance_tracker.py # Track expert accuracy
│       │   ├── knowledge_freshness.py # Knowledge file staleness
│       │   ├── knowledge_validator.py # Validate knowledge files
│       │   ├── knowledge_ingestion.py # Ingest new knowledge
│       │   ├── cache.py             # Expert response caching
│       │   ├── history_logger.py    # Consultation history
│       │   ├── observability.py     # Expert system observability
│       │   ├── report_generator.py  # Expert report generation
│       │   └── knowledge/           # 119 knowledge files (copy)
│       │       ├── security/
│       │       ├── performance/
│       │       ├── testing/
│       │       ├── data-privacy-compliance/
│       │       ├── accessibility/
│       │       ├── user-experience/
│       │       ├── observability-monitoring/
│       │       ├── api-design-integration/
│       │       ├── cloud-infrastructure/
│       │       ├── database-data-management/
│       │       ├── agent-learning/
│       │       ├── ai-frameworks/
│       │       ├── software-architecture/
│       │       ├── code-quality-analysis/
│       │       ├── development-workflow/
│       │       └── documentation-knowledge-management/
│       │
│       ├── project/                   # ← from core/ + workflow/ + context7/
│       │   ├── __init__.py
│       │   ├── profile.py           # Project profile detection
│       │   ├── language.py          # Language detection (from context7/)
│       │   ├── library_detector.py  # Library/dependency detection
│       │   ├── detector.py          # Tech stack detection
│       │   ├── type_detector.py     # Project type detection
│       │   ├── stack_analyzer.py    # Comprehensive tech stack analysis
│       │   ├── ast_parser.py        # Code structure extraction
│       │   └── impact_analyzer.py   # Change impact analysis
│       │
│       └── state/                     # ← Phase 5 only (optional advanced)
│           ├── __init__.py
│           ├── manager.py            # State persistence (from workflow/)
│           ├── durable_state.py     # Durable state with quality gate recording
│           ├── checkpoints.py       # Checkpoint save/restore
│           └── metrics.py           # Execution metrics
│
├── tests/
│   ├── unit/
│   │   ├── test_scoring.py
│   │   ├── test_gates.py
│   │   ├── test_security.py          # Path validation, guardrails, RAG safety
│   │   ├── test_knowledge.py
│   │   ├── test_experts.py
│   │   ├── test_validators.py
│   │   ├── test_project.py
│   │   └── test_state.py
│   ├── integration/
│   │   ├── test_server.py             # MCP protocol integration
│   │   ├── test_context7_api.py       # Context7 API (or mock)
│   │   └── test_cross_platform.py     # Windows + Linux compatibility
│   └── conftest.py
│
└── config/
    └── default.yaml                  # Default thresholds, presets
```

---

## Implementation Phases

**Total estimated LOE:** ~12-17 weeks (1 developer), ~6-9 weeks (2 developers with parallelized Phase 2a/2b)

| Phase | Scope | LOE | Cumulative |
|---|---|---|---|
| 0 | Foundation + security + dependency analysis | ~1 week | 1 week |
| 1 | Scoring + gates + security scan (MVP) | ~2-3 weeks | 3-4 weeks |
| 2a | Documentation lookup + config validators | ~2 weeks | 5-6 weeks |
| 2b | Expert system core + RAG + 119 knowledge files | ~3-4 weeks | 8-10 weeks |
| 3 | Project context + session notes + impact analysis | ~2 weeks | 10-12 weeks |
| 4 | Adaptive learning + feedback loop + deferred 2b components | ~2-3 weeks | 12-15 weeks |
| 5 | Distribution + PyPI + Docker + CI + optional advanced tools | ~2-3 weeks | 14-18 weeks |

### Phase 0: Foundation (extract existing MCP infrastructure)

**LOE:** ~1 week (1 developer)

**Goal:** Create the `tapps-mcp` package scaffolding by adapting the existing MCP patterns from `tapps_agents/mcp/`. This gives us a working tool registry and gateway before writing any new tools.

**Tasks:**
- [ ] **0.1** Create `tapps-mcp` repo with `pyproject.toml`, `src/tapps_mcp/` structure
- [ ] **0.2** **Dependency analysis of "standalone" modules** — Run import graph analysis on all modules marked "copy directly" in the extraction map. Identify transitive imports to framework utilities (`core/exceptions.py`, `core/config.py`, logging helpers, etc.). Create `tapps_mcp/common/` package with shared utilities (exceptions, logging, config models) that standalone modules actually depend on. This prevents discovery of hidden coupling during Phase 1-2 extraction. **IMPORTANT: The Phase 1-3 extraction lists in the Code Extraction Map should be revised based on this analysis before extraction begins.**
- [ ] **0.3** Adapt `mcp/tool_registry.py` → `tapps_mcp/core/tool_registry.py` — reuse registry pattern, **rewrite** serialization to produce MCP-compliant JSON Schema tool definitions (the existing `ToolRegistry` registers Python callables, not MCP wire-protocol tools)
- [ ] **0.4** Adapt `mcp/gateway.py` → `tapps_mcp/core/gateway.py` — reuse routing pattern, **implement** MCP Python SDK stdio/SSE transport layer (the existing `MCPGateway` is internal-only, no wire protocol)
- [ ] **0.5** Implement `server.py` with MCP Python SDK — wire adapted registry/gateway to `@server.tool()` decorator pattern. **Budget 2-3 days for tasks 0.3-0.5 combined** — this is a transport layer rewrite, not a simple extraction.
- [ ] **0.6** Extract security hardening modules:
  - `core/path_validator.py` → `tapps_mcp/security/path_validator.py` — **extend** `assert_write_allowed()` to also enforce `TAPPS_MCP_PROJECT_ROOT` boundary (all file paths must resolve within project root)
  - `core/io_guardrails.py` → `tapps_mcp/security/io_guardrails.py`
  - `experts/rag_safety.py` → `tapps_mcp/security/rag_safety.py`
  - `experts/governance.py` → `tapps_mcp/security/governance.py` (decouple from expert base)
  - `context7/security.py` → `tapps_mcp/security/api_keys.py`
- [ ] **0.7** Extract `core/subprocess_utils.py` → `tapps_mcp/tools/subprocess_utils.py` (Windows compatibility)
- [ ] **0.8** Add YAML configuration support (`config/default.yaml`). **Config precedence:** env vars > YAML config > `config/default.yaml` defaults.
- [ ] **0.9** Implement `tapps_server_info` tool (returns version, capabilities, installed tool checkers — see Tier 0 definition below)
- [ ] **0.10** Test: server starts, registers tools, responds to MCP protocol handshake

**Dependencies:** `mcp` (Python MCP SDK), `pyyaml`

**Definition of done:** `tapps-mcp serve` starts a working MCP server with the security layer and an empty tool registry. Claude Code connects and sees `tapps_server_info` as the only tool, and the handshake works. Dependency analysis is complete and `tapps_mcp/common/` contains all shared utilities needed by later phases.

### Phase 1: Core Scoring MCP (MVP)

**LOE:** ~2-3 weeks (1 developer)

**Goal:** A working MCP server with `tapps_score_file` (including quick/fix mode), `tapps_security_scan`, `tapps_quality_gate`, and `tapps_checklist`. This alone addresses 6 of the 13 LLM error sources.

**Tasks:**
- [ ] **1.1** Extract scoring engine from `agents/reviewer/`:
  - `scoring.py` — decouple from `ProjectConfig` + `Language`, accept config as dict
  - `score_constants.py`, `validation.py`, `scorer_registry.py` — copy directly
  - `maintainability_scorer.py`, `performance_scorer.py`, `typescript_scorer.py`, `react_scorer.py` — copy directly
  - `pattern_detector.py`, `context_detector.py`, `score_validator.py` — copy directly
  - `metric_strategies.py`, `library_patterns.py`, `library_detector.py` — copy directly
  - `output_enhancer.py`, `report_generator.py`, `aggregator.py` — copy directly
  - `adaptive_scorer.py` — remove agent base dependency
- [ ] **1.2** Extract tools from `agents/reviewer/tools/`:
  - `ruff_grouping.py`, `scoped_mypy.py`, `parallel_executor.py` — copy directly
- [ ] **1.3** Extract quality gates from `quality/`:
  - `quality_gates.py`, `enforcement.py` — decouple from framework
  - `gates/base.py`, `gates/registry.py`, `gates/exceptions.py` — copy directly
  - `gates/security_gate.py` — extract with governance dependency
  - `gates/policy_gate.py` — evaluate coupling, extract if standalone
  - `coverage_analyzer.py` — copy directly (required for test_coverage gate)
- [ ] **1.4** Extract security scanning:
  - `quality/secret_scanner.py` — copy directly
  - `core/security_scanner.py` — copy directly (standalone Bandit wrapper)
- [ ] **1.5** Wire 4 tools into MCP server: `tapps_score_file` (with `quick`/`fix` fast path), `tapps_security_scan`, `tapps_quality_gate`, `tapps_checklist`
  - All `file_path` inputs must pass `path_validator.assert_write_allowed()` first
  - All outputs must pass `io_guardrails.sanitize_for_log()` before logging
- [ ] **1.6** Test: unit tests for scoring, gates, security scanning, path validation
- [ ] **1.7** Test: MCP protocol integration tests (tool call → response)
- [ ] **1.8** Test: Windows + Linux cross-platform (subprocess_utils, path handling)
- [ ] **1.9** Documentation: README with Claude Code and Cursor setup instructions
~~- [ ] **1.10** Docker image~~ *(Moved to Phase 5, task 5.9 — not needed for MVP, adds CI/CD complexity early.)*

**Dependencies:** `ruff`, `radon`, `bandit`, `mcp` (Python SDK)
**Optional:** `mypy`, `jscpd`, `coverage`, `jinja2` (for HTML reports — graceful degradation if not installed)

**Definition of done:** `tapps-mcp` runs as an MCP server, Claude Code can call `tapps_score_file` on a Python file and get back structured quality scores. All file paths are validated. Works on Windows and Linux.

### Phase 2a: Documentation Lookup (highest-value knowledge tool)

**LOE:** ~2 weeks (1 developer)

**Goal:** Add `tapps_lookup_docs` and `tapps_validate_config`. Addresses hallucinated APIs (the single highest-impact LLM error source) without the complexity of the full expert system.

**Tasks:**
- [ ] **2a.1** Extract Context7 client and cache from `context7/` — decouple from framework config:
  - `kb_cache.py`, `cache_structure.py`, `fuzzy_matcher.py` — remove framework config coupling
  - `backup_client.py`, `circuit_breaker.py`, `lookup.py` — adapt
  - `cache_warming.py`, `cache_prewarm.py` — copy directly
  - `staleness_policies.py`, `refresh_queue.py` — copy directly
  - `cache_locking.py`, `cache_metadata.py` — copy directly
  - `analytics.py`, `cleanup.py` — copy directly
  - `credential_validation.py` — copy directly
  - `bundle_loader.py` — copy directly (air-gapped support)
  - `language_detector.py` → `project/language.py`
  - `cross_references.py` — copy directly
  - `library_detector.py` → `project/library_detector.py`
- [ ] **2a.2** Extract config validators from `agents/reviewer/`:
  - `dockerfile_validator.py`, `docker_compose_validator.py` — copy directly
  - `websocket_validator.py`, `mqtt_validator.py`, `influxdb_validator.py` — copy directly
  - `service_discovery.py` — copy directly
- [ ] **2a.3** Wire 2 tools: `tapps_lookup_docs`, `tapps_validate_config`
- [ ] **2a.4** Add cache warming on server startup (detect project deps, pre-fetch docs)
- [ ] **2a.5** Test: unit tests for KB cache, fuzzy matching, validators
- [ ] **2a.6** Test: integration tests with Context7 API (or mock)

**Dependencies:** `pyyaml`, `httpx` (for Context7 API)
**Optional:** Context7 API key (degrades to cached/bundled docs without it)

**Definition of done:** `tapps_lookup_docs` returns real library documentation for any detected project dependency. Cache warming pre-fetches docs on startup.

### Phase 2b: Expert System (core knowledge layer)

**LOE:** ~3-4 weeks (1 developer)

> **Architecture review note:** Original estimate of 2-3 weeks was optimistic for 40+ files,
> 119 knowledge files, decoupling `expert_engine.py` from agent base, wiring RAG safety +
> governance filtering, two MCP tools, and tests. The coupling chain
> `expert_engine.py` → `expert_registry.py` → `builtin_registry.py` → `base_expert.py` →
> domain configs requires careful extraction. Adjusted to 3-4 weeks, with optional components
> (vector_rag, adaptive_domain_detector, knowledge_ingestion) deferred to Phase 4.

**Goal:** Add `tapps_consult_expert` and `tapps_list_experts`. Addresses wrong domain patterns with RAG-backed expert consultation across 16 domains. This is the largest extraction and is intentionally separated from 2a.

**Tasks:**
- [ ] **2b.1** Extract expert engine core from `experts/`:
  - `expert_engine.py` — remove agent coupling (this is the hardest decoupling task)
  - `expert_registry.py`, `builtin_registry.py`, `base_expert.py` — copy directly
  - `simple_rag.py` — copy directly (core RAG, no dependencies)
  - `rag_evaluation.py`, `rag_metrics.py` — copy directly
  - `domain_detector.py` — copy directly
  - `confidence_calculator.py`, `confidence_breakdown.py`, `confidence_metrics.py` — copy directly
  - `expert_suggester.py`, `domain_config.py`, `domain_utils.py`, `expert_config.py` — copy directly
  - `cache.py`, `history_logger.py`, `observability.py`, `report_generator.py` — copy directly
- [ ] **2b.2** Copy 119 knowledge files from `experts/knowledge/` (16 domains) and validate post-copy
- [ ] **2b.3** Wire 2 tools: `tapps_consult_expert`, `tapps_list_experts`
  - All RAG-retrieved content must pass `rag_safety.py` prompt injection check
  - All expert responses must pass `governance.py` PII/secret filter
- [ ] **2b.4** Test: unit tests for expert consultation, RAG retrieval, confidence scoring
- [ ] **2b.5** Test: RAG safety — prompt injection in knowledge files is caught

**Deferred to Phase 4:**
- `vector_rag.py`, `rag_chunker.py`, `rag_embedder.py`, `rag_index.py` — optional FAISS chain (auto-fallback to simple_rag works fine without these)
- `adaptive_domain_detector.py` — improved domain detection (basic `domain_detector.py` is sufficient for launch)
- `knowledge_freshness.py`, `knowledge_validator.py`, `knowledge_ingestion.py` — knowledge management (static knowledge files work for initial release)

**Dependencies:** `pyyaml`
**Optional (Phase 4):** `faiss-cpu` + `sentence-transformers` (for vector RAG — auto-fallback to simple_rag)

### Phase 3: Project Context & Extended Tools

**LOE:** ~2 weeks (1 developer)

**Goal:** Add `tapps_project_profile`, `tapps_session_notes`, `tapps_impact_analysis`, `tapps_report`. Addresses scope drift, lost context, and change management.

> **Design decision:** The original `tapps_workflow_state` was reworked into the simpler `tapps_session_notes` (key-value note storage per session). Full workflow state management is an orchestration concern — the exact thing the "What NOT to copy" section excludes. An LLM managing workflow checkpoints via MCP tool calls would essentially reimplement the workflow engine through prompt instructions. `tapps_session_notes` provides lightweight context persistence without the orchestration complexity. Full state management is deferred to Phase 5 as an optional advanced tool.

**Tasks:**
- [ ] **3.1** Extract project profiling:
  - `core/project_profile.py` — decouple from `workflow.detector`
  - `workflow/detector.py` — extract tech stack detection parts
  - `core/project_type_detector.py`, `core/stack_analyzer.py` — copy directly
  - `core/ast_parser.py` — copy directly (code structure extraction)
  - `core/change_impact_analyzer.py` — copy directly
- [ ] **3.2** Implement `tapps_session_notes` — lightweight key-value note storage (see Tier 3 definition below)
- [ ] **3.3** Wire 4 tools: `tapps_project_profile`, `tapps_session_notes`, `tapps_impact_analysis`, `tapps_report`
- [ ] **3.4** Test: profile detection on Python, JS/TS, Rust, Go, and multi-language projects
- [ ] **3.5** Test: session notes save/get/list lifecycle
- [ ] **3.6** Test: impact analysis on multi-file changes

### Phase 4: Adaptive Learning + Deferred Phase 2b Components

**LOE:** ~2-3 weeks (1 developer)

**Goal:** The MCP server learns from usage to improve quality predictions over time. Also completes the expert system with optional components deferred from Phase 2b.

**Tasks:**
- [ ] **4.1** Extract adaptive scoring:
  - `agents/reviewer/adaptive_scorer.py` — remove agent base dependency
  - `core/adaptive_scoring.py` — copy directly
- [ ] **4.2** Extract expert adaptation:
  - `experts/adaptive_voting.py` — copy directly
  - `experts/weight_distributor.py` — copy directly
  - `experts/performance_tracker.py` — copy directly
- [ ] **4.3** Implement feedback loop: track which gate failures lead to rework, adjust weights
- [ ] **4.4** Add `tapps_feedback` tool for LLM to report outcomes
- [ ] **4.5** Add `tapps_stats` tool to report server-side usage statistics
- [ ] **4.6** Extract deferred Phase 2b components:
  - `vector_rag.py`, `rag_chunker.py`, `rag_embedder.py`, `rag_index.py` — optional FAISS vector RAG chain
  - `adaptive_domain_detector.py` — improved adaptive domain detection
  - `knowledge_freshness.py`, `knowledge_validator.py`, `knowledge_ingestion.py` — knowledge management tools
- [ ] **4.7** Test: weight adaptation over multiple scoring sessions
- [ ] **4.8** Test: expert accuracy tracking and vote weight adjustment
- [ ] **4.9** Test: vector RAG fallback behavior (FAISS available → use it, missing → simple_rag)

### Phase 5: Distribution, Integration & Advanced Tools

**LOE:** ~2-3 weeks (1 developer)

**Goal:** Easy installation and setup for all major LLM clients. Optional advanced tools.

**Tasks:**
- [ ] **5.1** Publish to PyPI as `tapps-mcp` (base) + `tapps-mcp[vector]` (FAISS extras)
- [ ] **5.2** One-command setup: `tapps-mcp init` writes config for Claude Code / Cursor
- [ ] **5.3** npm wrapper for Cursor users: `npx tapps-mcp`
- [ ] **5.4** Documentation: setup guides for Claude Code, Cursor, VS Code + Continue, etc.
- [ ] **5.5** CI pipeline: test on Windows + Linux + macOS, publish to PyPI on tag
- [ ] **5.6** Evaluate extracting `experts/auto_generator.py` as a `tapps_generate_expert` tool
- [ ] **5.7** *(Optional advanced)* Extract full `tapps_workflow_state` tool from `workflow/state_manager.py`, `durable_state.py`, `checkpoint_manager.py`, `execution_metrics.py` — for power users who want full checkpoint/restore semantics via MCP. Only if demand exists from Phase 3 `tapps_session_notes` users.
- [ ] **5.8** **Evaluate MCP resources and prompts.** MCP supports [resources](https://modelcontextprotocol.io/) (server-exposed data clients can browse) and [prompts](https://modelcontextprotocol.io/) (server-defined prompt templates auto-injected by the server). Evaluate: (a) exposing the 119 knowledge files as MCP resources so clients can browse/select expert domains, (b) providing the workflow system prompt (currently ~50 lines in client config) as an MCP prompt template, eliminating manual system prompt configuration. This could significantly improve the onboarding experience.
- [ ] **5.9** **Docker image** (`Dockerfile` + `docker-compose.yml`) for zero-dependency deployment. Include ruff, mypy, bandit pre-installed. Publish to Docker Hub / GitHub Container Registry. *(Moved from Phase 1 — not needed for MVP, adds CI/CD complexity early.)*

---

## Client Configuration

### Claude Code (`~/.claude/settings.json`)

```json
{
  "mcpServers": {
    "tapps-mcp": {
      "command": "tapps-mcp",
      "args": ["serve"],
      "env": {
        "TAPPS_MCP_PROJECT_ROOT": ".",
        "CONTEXT7_API_KEY": "optional-key-here"
      }
    }
  }
}
```

### Cursor (`.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "tapps-mcp": {
      "command": "tapps-mcp",
      "args": ["serve"],
      "env": {
        "TAPPS_MCP_PROJECT_ROOT": "."
      }
    }
  }
}
```

### Minimal System Prompt (replaces 14 skill files)

```
You have access to TappsMCP tools for code quality enforcement.

Required workflow:
1. Call tapps_server_info at the start of each session to discover available tools
2. Call tapps_project_profile at the start of each task
3. Call tapps_lookup_docs BEFORE using any external library API
4. Call tapps_score_file (quick: true) for fast lint checks during edit-lint-fix loops
5. Call tapps_score_file (full) after completing a file for comprehensive quality scoring
6. Call tapps_quality_gate before declaring work complete — work is NOT done until it passes
7. Call tapps_checklist before declaring work complete — verify you haven't skipped required tools
8. Call tapps_consult_expert when making domain-specific decisions (security, database, etc.)
9. Call tapps_validate_config when writing Dockerfiles, docker-compose, or infrastructure configs
10. Call tapps_impact_analysis before large refactors to understand blast radius

Quality rules:
- Score must be >= 70 (standard) or >= 75 (framework code)
- Security score must be >= 7.0
- If tapps_quality_gate returns passed: false, fix the issues and re-check
- If tapps_checklist returns passed: false, call the missing tools before declaring done
```

**~50 lines replaces ~2,000+ lines of skill prompts while maintaining the same behavioral constraints.**

> **Honest limitation:** The system prompt is a *suggestion* to the LLM, not enforcement. Without a workflow engine (like TappsCodingAgents provides), the LLM may skip steps — especially in long sessions or under context pressure. `tapps_checklist` provides soft enforcement by catching skipped tools at the end of a task, but it still requires the LLM to call `tapps_checklist` itself. This is a fundamental limitation of the MCP tool model vs. orchestrated workflows. TappsMCP optimizes for the common case where the LLM cooperates, and `tapps_checklist` catches the uncommon case where it forgets.

---

## Relationship to TappsCodingAgents

TappsMCP is **not a replacement** for TappsCodingAgents. It's a complementary extraction:

| Concern | TappsCodingAgents | TappsMCP |
|---|---|---|
| **Workflow orchestration** | Yes (skill-based, YAML presets) | No (LLM decides) |
| **Workflow enforcement** | Yes (hard — workflow engine controls step order) | Soft (checklist tool suggests, LLM cooperates) |
| **Quality scoring** | Yes (via reviewer agent) | Yes (via MCP tool) |
| **Quality gates** | Yes (in workflow engine) | Yes (via MCP tool) |
| **Expert knowledge** | Yes (16 domains) | Yes (same 16 domains) |
| **Context7 docs** | Yes (cache + lookup) | Yes (same cache + lookup) |
| **Config validation** | Yes (Dockerfile, docker-compose validators) | Yes (same validators via MCP tool) |
| **Impact analysis** | Yes (change_impact_analyzer) | Yes (via MCP tool) |
| **Security hardening** | Yes (path validation, guardrails, governance) | Yes (same modules, mandatory for MCP) |
| **Vector RAG** | Yes (FAISS-based, optional) | Yes (same, optional extra) |
| **Session context** | Yes (full workflow state + checkpoints) | Lightweight (key-value session notes) |
| **Version discovery** | N/A (framework is the client) | Yes (`tapps_server_info` tool) |
| **CLI interface** | Yes (tapps-agents CLI) | No (MCP protocol only) |
| **Cursor Skills** | Yes (14 skills) | No (tools instead of skills) |
| **Epic management** | Yes | No |
| **Adaptive learning** | Yes | Yes (extracted) |
| **Target users** | Cursor IDE users, teams needing workflow enforcement | Any LLM client with MCP support |

TappsCodingAgents can optionally use TappsMCP as its quality backend, replacing its internal subprocess calls with MCP tool calls. This is a future integration point, not a Phase 1 concern.

---

## Success Metrics

1. **Phase 1 complete:** A Haiku-class model using TappsMCP produces code that passes quality gates at the same rate as Sonnet without TappsMCP
2. **API hallucinations reduced:** Measurable reduction in hallucinated library APIs when `tapps_lookup_docs` is called before implementation
3. **Model-agnostic quality floor:** Regardless of which model is used, `tapps_quality_gate` ensures a minimum quality bar
4. **Setup time < 5 minutes:** From `pip install tapps-mcp` (or `docker run tapps-mcp`) to working MCP server with Claude Code
5. **Zero prompt overhead for deterministic work:** Scoring, linting, secret scanning, gate checking — all happen server-side, zero LLM tokens consumed on tool execution logic
6. **Cross-platform:** Test suite passes on Windows, Linux, and macOS — no platform-specific failures
7. **Security hardened:** Zero directory traversal, zero API key leakage, zero prompt injection pass-through in RAG responses
8. **Extraction fidelity:** All extracted modules maintain their original test coverage (~380 tests ported — see Test Extraction Map)
9. **Performance:** All tools meet latency targets defined in the Performance Budget (e.g., `tapps_score_file` quick mode < 500ms, full mode < 3s)
10. **Checklist compliance:** In user testing, `tapps_checklist` catches ≥80% of skipped quality gate calls

---

## References

- [TappsCodingAgents Audit Fixes](../planning/) — Lessons learned from 4-phase security/quality audit
- [MCP Specification](https://modelcontextprotocol.io/) — Model Context Protocol standard
- [TappsCodingAgents Architecture](../ARCHITECTURE.md) — Source architecture
- [Quality Gates](../../tapps_agents/quality/quality_gates.py) — Gate implementation to extract
- [Scoring Engine](../../tapps_agents/agents/reviewer/scoring.py) — Scorer to extract
- [Expert System](../../tapps_agents/experts/) — Expert engine to extract
- [Context7 Integration](../../tapps_agents/context7/) — Knowledge layer to extract
