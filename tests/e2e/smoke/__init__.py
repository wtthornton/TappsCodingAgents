"""
Smoke E2E tests - Fast, deterministic tests that validate critical vertical slices.

These tests:
- Use mocked services (no real LLM, no real Context7)
- Are fully deterministic (no network calls, fixed fixtures)
- Run in under 30 seconds total
- Validate stable contracts (exit codes, JSON shape, file system invariants)
"""
