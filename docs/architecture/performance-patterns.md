# Performance Patterns (Lean BMAD Shard)

This shard exists because BMAD’s dev agent is configured to always load it (`.bmad-core/core-config.yaml`).

## Common Patterns

- **Bounded concurrency**: avoid unlimited fan-out; prefer semaphores / worker pools.
- **Timeouts everywhere**: network/subprocess calls must set timeouts.
- **Avoid accidental quadratic behavior**: watch nested loops, repeated scans, repeated file reads.
- **Prefer incremental computation**: reuse parsed/compiled artifacts where safe.

## Baseline Reference

- See `CLAUDE.md` for the review baseline headings (API/DB/Caching/Event processing/Targets).


