# Framework Architecture

## Overview

TappsCodingAgents provides 14 workflow agents, Simple Mode orchestration, and health checks.

## Key Components

- **Agents:** analyst, architect, debugger, designer, documenter, enhancer, evaluator, implementer, improver, ops, orchestrator, planner, reviewer, tester.
- **Simple Mode:** Natural language commands (`*build`, `*fix`, `*review`, `*test`) orchestrate multiple agents.
- **Health:** `tapps-agents health overview` and `health check`; execution metrics and analytics feed usage and outcomes.

## Configuration

- `.tapps-agents/config.yaml` for agents and thresholds.
- `.cursor/rules/` and `.claude/skills/` for Cursor integration.
