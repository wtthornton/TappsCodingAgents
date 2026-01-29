---
title: Project Context
version: 3.5.30
status: active
last_updated: 2026-01-20
tags: [project-context, dual-nature, framework, self-hosting]
---

# TappsCodingAgents Project Context

## Dual Nature of This Project

**This project has TWO distinct roles:**

### 1. Framework Development (Primary Role)

**TappsCodingAgents is a framework** that provides:
- 14 workflow agents (analyst, planner, architect, designer, implementer, tester, debugger, documenter, reviewer, improver, ops, orchestrator, enhancer, evaluator)
- Industry Experts system
- Cursor Skills integration (model-agnostic)
- Code quality analysis tools
- Workflow orchestration with CLI and Python API

**When working on framework development:**
- You're modifying the framework code itself (`tapps_agents/` package)
- Focus on: `tapps_agents/`, `tests/`, `requirements/`, `docs/`

**Framework changes MUST use the Full SDLC workflow:** `@simple-mode *full "Implement [description]"` or `tapps-agents simple-mode full --prompt "..." --auto`.

### 2. Self-Hosting (Secondary Role)

**TappsCodingAgents uses its own framework** for its own development:
- Configuration: `.tapps-agents/` directory
- Industry Experts, Context7, workflows

**When working on self-hosted development:**
- You're using the framework to develop the framework itself
- Focus on: `.tapps-agents/`, `workflows/`, project-specific tasks

## Full Rules

For the complete project-context rules applied in this repo (including framework workflow requirements and self-hosting details), see:

**`.cursor/rules/project-context.mdc`** (installed by `tapps-agents init`)

## Related

- [Architecture Overview](ARCHITECTURE.md)
- [How It Works](HOW_IT_WORKS.md)
