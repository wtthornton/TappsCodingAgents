# Performance Checklist (Lean BMAD Shard)

- **Tests**: Prefer `pytest -n auto` unless debugging isolation issues.
- **Coverage**: Only enable coverage when needed (coverage can slow runs).
- **I/O**: Avoid large file reads/writes in tight loops; cache derived results if safe.
- **Async**: No blocking I/O inside async functions (use async libs or offload explicitly).
- **External calls**: Always use explicit timeouts and clear failure modes.
- **Loops / queues**: Ensure bounded growth and backpressure where applicable.
- **Docs**: If you introduce a performance-sensitive change, document rationale and any measurements.


