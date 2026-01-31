# Testing Guide

## Overview

TappsCodingAgents uses pytest for unit and integration tests. Coverage targets are defined in pytest.ini.

## Key Conventions

- Tests live in `tests/` mirroring package structure.
- Use `@pytest.fixture` for shared setup.
- Prefer `tests/unit/` for fast unit tests, `tests/integration/` for integration.
- Run: `pytest`, `pytest --cov=tapps_agents`, or `tapps-agents tester test <file>`.

## Coverage

- Target ≥75% (pytest.ini); framework core aims for ≥80%.
- Use `tapps-agents simple-mode *test <file>` for generated tests and coverage.
