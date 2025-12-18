# TappsCodingAgents Project Context

## Understanding This Project's Dual Nature

TappsCodingAgents has a dual nature: **it both develops the framework AND uses it for its own development** (self-hosting). This document clarifies the distinction.

## Two Roles

### 1. Framework Development (Primary)

**What it is:** TappsCodingAgents is a framework/library that other projects can use.

**What we do:**
- Develop the framework code in the `tapps_agents/` package
- Write tests in the `tests/` directory
- Create documentation in the `docs/` directory
- Keep specifications and requirements under `requirements/`

**Key locations:**
- `tapps_agents/` - framework source
- `tests/` - test suite
- `docs/` - user-facing documentation
- `requirements/` - specifications
- `pyproject.toml` - package metadata and tooling configuration

### 2. Self-Hosting (Secondary)

**What it is:** This repository uses its own framework to help develop and maintain itself.

**What we do:**
- Configure experts in `.tapps-agents/experts.yaml`
- Define domains in `.tapps-agents/domains.md`
- Use workflow presets in `workflows/presets/`
- Persist workflow state under `.tapps-agents/workflow-state/`
- Optionally collect analytics under `.tapps-agents/analytics/`
- Persist project profile to `.tapps-agents/project-profile.yaml`

## Why This Matters

### For Framework Users

When you install TappsCodingAgents in your project:

- You get the `tapps_agents` Python package
- You optionally add `.tapps-agents/` in **your** project for configuration
- You run agents via the CLI or Python API

Example:

```bash
# In your project
python -m tapps_agents.cli reviewer score src/main.py
```

### For Framework Developers

When working on this repo:

- You modify framework code under `tapps_agents/`
- You may also use the framework tooling via `.tapps-agents/` in this repo

## Current Self-Hosting Configuration

**Framework version**: 2.0.4 (see `tapps_agents.__version__`)

## References

- `docs/CONFIGURATION.md`
- `docs/ARCHITECTURE.md`
- `docs/EXPERT_SETUP_WIZARD.md`

---

**Last Updated**: January 2026  
**Version**: 2.0.4
