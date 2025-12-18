# Context7 KB Cache (BMAD)

BMAD’s Context7 integration (configured in `.bmad-core/core-config.yaml`) caches fetched library docs under this folder to avoid repeated token/cost overhead.

## Structure

- `docs/kb/context7-cache/index.yaml`: library/topic index
- `docs/kb/context7-cache/cross-references.yaml`: optional topic cross-refs
- `docs/kb/context7-cache/libraries/<library>/meta.yaml`: per-library metadata
- `docs/kb/context7-cache/libraries/<library>/<topic>.md`: cached docs

If you do not use Context7 tooling, this folder may remain mostly empty.


