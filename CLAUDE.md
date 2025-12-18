# Performance & Quality Guidelines (BMAD Review Reference)

This repository uses **BMAD progressive reviews** (`.bmad-core/tasks/progressive-code-review.md`) and the config in `.bmad-core/core-config.yaml` references this file as the **performance/quality baseline**.

These guidelines are written to be broadly applicable to **TappsCodingAgents** (a Python framework) and to avoid project-specific, hard-coded SLAs.

## API Performance

Even though this repo is primarily a library/framework, it contains async code paths (HTTP calls, I/O, background work). Prefer:

- **Async-first** for network and concurrency (`httpx`, `aiohttp`) and avoid blocking I/O inside async functions.
- **Bounded concurrency** for fan-out work (avoid unbounded task creation).
- **Time bounds** for integration calls: prefer explicit timeouts and clear error paths.

## Database Performance

This repo does not have a primary production database, but when implementing DB-backed examples or integrations:

- Avoid \(N+1\) query patterns.
- Batch operations when possible.
- Prefer pagination / limits for unbounded queries.

## Caching Strategies

- Cache expensive derived results when safe (and when invalidation is clear).
- Prefer **small, explicit** caches over hidden global state.
- If caching is introduced, document:
  - what is cached
  - invalidation / expiry strategy
  - max size or bounds (if applicable)

## Event Processing

If implementing event/queue style processing:

- Prefer batch-friendly designs where it improves throughput.
- Ensure backpressure / bounded queues where relevant.
- Make long-running loops observable and stoppable.

## Performance Targets

No hard-coded latency SLA is enforced by default. Instead:

- **Do not introduce regressions** to CLI responsiveness or test runtime without justification.
- Prefer measurable improvements: add benchmarks or test timing notes when a change is performance-sensitive.

## References (project-specific)

- Test execution performance: `docs/TEST_PERFORMANCE_GUIDE.md`
- Architecture overview: `docs/ARCHITECTURE.md`
- Developer guide: `docs/DEVELOPER_GUIDE.md`


