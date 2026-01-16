---
title: Documentation Metadata Standards
version: 1.0.0
status: active
last_updated: 2026-01-20
tags: [documentation, standards, metadata, frontmatter]
---

# Documentation Metadata Standards

This document defines the metadata standards for all documentation files in the TappsCodingAgents project. Metadata is stored as YAML frontmatter at the beginning of each documentation file.

## Overview

Documentation metadata serves multiple purposes:
- **AI Tool Context**: Provides structured context for AI coding assistants
- **Version Tracking**: Tracks document versions and update history
- **Status Management**: Indicates document status (active, deprecated, draft)
- **Navigation & Discovery**: Enables topic-based navigation and search
- **Maintenance**: Helps identify outdated or stale documentation

## Frontmatter Format

All documentation files should begin with YAML frontmatter delimited by `---`:

```yaml
---
title: Document Title
version: 1.0.0
status: active
last_updated: 2026-01-20
tags: [tag1, tag2, tag3]
---
```

## Required Fields

### `title` (Required)

**Purpose:** Human-readable document title

**Format:** String, typically matches the H1 heading

**Examples:**
```yaml
title: Documentation Metadata Standards
title: Architecture Index (BMAD Standard Path)
title: AI Comment Tag Guidelines
```

**Best Practices:**
- Use title case
- Be descriptive and specific
- Match or closely align with the H1 heading
- Keep under 80 characters when possible

---

### `version` (Required)

**Purpose:** Document version for tracking changes

**Format:** Semantic version string (major.minor.patch)

**Examples:**
```yaml
version: 1.0.0
version: 2.1.3
version: 3.3.0
```

**Versioning Guidelines:**
- **Major (X.0.0)**: Breaking changes, major rewrites, significant restructuring
- **Minor (x.Y.0)**: New sections, substantial additions, non-breaking changes
- **Patch (x.y.Z)**: Minor corrections, typo fixes, small clarifications

**Best Practices:**
- Start at `1.0.0` for new documents
- Increment appropriately when making changes
- Use semantic versioning consistently
- Update version when content changes significantly

---

### `status` (Required)

**Purpose:** Indicates the current status of the document

**Format:** String, one of the predefined status values

**Valid Values:**
- `active` - Document is current and actively maintained
- `deprecated` - Document is outdated but kept for reference
- `draft` - Document is work-in-progress, not finalized
- `archived` - Document is no longer relevant but preserved
- `superseded` - Document has been replaced by another document

**Examples:**
```yaml
status: active
status: draft
status: deprecated
```

**Best Practices:**
- Use `active` for all current documentation
- Mark as `deprecated` when content is outdated but still referenced
- Use `draft` for work-in-progress documents
- Update status when document lifecycle changes

---

### `last_updated` (Required)

**Purpose:** Date of last significant update

**Format:** ISO 8601 date format (YYYY-MM-DD)

**Examples:**
```yaml
last_updated: 2026-01-20
last_updated: 2025-12-15
```

**Best Practices:**
- Update when making substantial changes
- Use ISO 8601 format (YYYY-MM-DD) for consistency
- Update even for minor corrections to track maintenance
- Consider automated updates via CI/CD

---

### `tags` (Required)

**Purpose:** Topics and categories for navigation and discovery

**Format:** YAML array of strings

**Examples:**
```yaml
tags: [documentation, standards, metadata, frontmatter]
tags: [architecture, decisions, adr]
tags: [testing, strategy, coverage]
```

**Tag Categories:**

**Documentation Type:**
- `documentation` - General documentation
- `guide` - How-to guides
- `reference` - API or technical reference
- `tutorial` - Step-by-step tutorials
- `standards` - Standards and conventions

**Topic Areas:**
- `architecture` - System architecture
- `testing` - Testing strategy and infrastructure
- `configuration` - Configuration and setup
- `workflow` - Workflow definitions and execution
- `agents` - Agent documentation
- `experts` - Expert system documentation
- `integration` - Integration patterns (MCP, Context7, etc.)

**Technical Domains:**
- `python` - Python-specific content
- `yaml` - YAML configuration
- `cli` - Command-line interface
- `api` - API documentation
- `security` - Security-related content
- `performance` - Performance optimization

**Best Practices:**
- Use 3-6 tags per document
- Include at least one topic area tag
- Use lowercase, hyphenated tags (e.g., `code-quality`, not `Code Quality`)
- Be consistent with existing tags
- Add new tags when needed, but prefer existing tags

---

## Optional Fields

### `authors` (Optional)

**Purpose:** Document authors or maintainers

**Format:** YAML array of strings

**Examples:**
```yaml
authors: [John Doe, Jane Smith]
authors: [TappsCodingAgents Team]
```

**Best Practices:**
- Include for major documents or when attribution is important
- Use consistent name format
- Update when ownership changes

---

### `dependencies` (Optional)

**Purpose:** Related documents or prerequisites

**Format:** YAML array of strings (relative paths or document names)

**Examples:**
```yaml
dependencies: [docs/ARCHITECTURE.md, docs/CONFIGURATION.md]
dependencies: [architecture/decisions/ADR-001-instruction-based-architecture.md]
```

**Best Practices:**
- List documents that should be read first
- Use relative paths from project root
- Keep list focused (3-5 dependencies max)

---

### `related` (Optional)

**Purpose:** Related documents for further reading

**Format:** YAML array of strings (relative paths or document names)

**Examples:**
```yaml
related: [docs/AI_COMMENT_GUIDELINES.md, docs/CONTRIBUTING.md]
related: [architecture/decisions/, architecture/tech-stack.md]
```

**Best Practices:**
- List documents for additional context
- Use relative paths from project root
- Keep list focused (5-8 related docs max)

---

### `supersedes` (Optional)

**Purpose:** Document that this one replaces

**Format:** String (relative path or document name)

**Examples:**
```yaml
supersedes: docs/OLD_ARCHITECTURE.md
```

**Best Practices:**
- Use when replacing an existing document
- Update old document's status to `superseded`
- Include link to new document in old document

---

## Complete Example

```yaml
---
title: Documentation Metadata Standards
version: 1.0.0
status: active
last_updated: 2026-01-20
tags: [documentation, standards, metadata, frontmatter]
authors: [TappsCodingAgents Team]
dependencies: [docs/README.md]
related: [docs/AI_COMMENT_GUIDELINES.md, docs/CONTRIBUTING.md]
---
```

## Metadata Template

Use this template for new documentation files:

```yaml
---
title: Document Title
version: 1.0.0
status: active
last_updated: YYYY-MM-DD
tags: [tag1, tag2, tag3]
---
```

## Migration Guide

### For Existing Documents

1. **Add frontmatter** to documents missing it:
   - Start with required fields: `title`, `version`, `status`, `last_updated`, `tags`
   - Extract title from H1 heading
   - Set version to `1.0.0` if unknown
   - Set status to `active` for current docs
   - Use file modification date for `last_updated`
   - Add 3-5 relevant tags

2. **Update existing frontmatter**:
   - Ensure all required fields are present
   - Standardize date format to YYYY-MM-DD
   - Review and update tags for consistency
   - Update version when making changes

3. **Validate frontmatter**:
   - Check YAML syntax (no tabs, proper indentation)
   - Verify all required fields are present
   - Ensure tags are lowercase and hyphenated
   - Validate date format

### Migration Priority

**High Priority** (Add frontmatter immediately):
- `docs/README.md` ✅ (already has frontmatter)
- `docs/ARCHITECTURE.md` (has minimal frontmatter, needs completion)
- `docs/CONFIGURATION.md` (needs frontmatter)
- `docs/API.md` (if exists, needs frontmatter)
- All guide documents in `docs/guides/`

**Medium Priority** (Add during regular maintenance):
- Architecture shard files (`docs/architecture/*.md`)
- ADR files (`docs/architecture/decisions/*.md`)
- Feature documentation files

**Low Priority** (Add when convenient):
- Workflow output files (`docs/workflows/`)
- Analysis and review documents

## Validation

### Manual Validation

Check that frontmatter:
- ✅ Starts with `---` on first line
- ✅ Ends with `---` before content
- ✅ Contains all required fields
- ✅ Uses valid YAML syntax
- ✅ Date format is YYYY-MM-DD
- ✅ Status is one of valid values
- ✅ Tags are lowercase arrays

### Automated Validation

Consider adding validation to:
- CI/CD pipeline (validate frontmatter on PRs)
- Documentation generation scripts
- Pre-commit hooks

Example validation script:
```python
import yaml
from pathlib import Path

def validate_frontmatter(file_path: Path) -> bool:
    """Validate documentation frontmatter."""
    content = file_path.read_text(encoding="utf-8")
    
    if not content.startswith("---\n"):
        return False
    
    # Extract frontmatter
    parts = content.split("---\n", 2)
    if len(parts) < 3:
        return False
    
    frontmatter = yaml.safe_load(parts[1])
    
    # Check required fields
    required = ["title", "version", "status", "last_updated", "tags"]
    for field in required:
        if field not in frontmatter:
            return False
    
    # Validate status
    valid_statuses = ["active", "deprecated", "draft", "archived", "superseded"]
    if frontmatter["status"] not in valid_statuses:
        return False
    
    return True
```

## Integration with Documentation Tools

### AI Coding Assistants

Metadata helps AI assistants:
- Understand document purpose and scope
- Identify related documents
- Determine document currency (via `last_updated` and `status`)
- Navigate documentation structure

### Documentation Generators

Metadata can be used by:
- Static site generators (MkDocs, Sphinx, etc.)
- Documentation indexing tools
- Search engines
- Navigation builders

### CI/CD Integration

Metadata enables:
- Outdated document detection (compare `last_updated` with code changes)
- Broken link detection (validate `dependencies` and `related` paths)
- Status-based filtering (exclude `deprecated` or `archived` docs)
- Version tracking and changelog generation

## Best Practices Summary

1. **Always include required fields** - `title`, `version`, `status`, `last_updated`, `tags`
2. **Update metadata when content changes** - Keep `last_updated` and `version` current
3. **Use consistent tags** - Prefer existing tags, add new ones thoughtfully
4. **Validate YAML syntax** - Ensure frontmatter is valid YAML
5. **Keep tags focused** - 3-6 tags per document, include topic areas
6. **Update status appropriately** - Mark deprecated/superseded documents
7. **Link related documents** - Use `dependencies` and `related` for navigation
8. **Follow date format** - Always use YYYY-MM-DD for `last_updated`

## Related Documentation

- **[AI Comment Guidelines](AI_COMMENT_GUIDELINES.md)** - AI comment tag conventions
- **[Architecture Decisions](architecture/decisions/)** - ADR system
- **[Documentation Index](README.md)** - Main documentation index
- **[Contributing Guide](../CONTRIBUTING.md)** - Contribution guidelines

## Questions or Suggestions?

If you have questions about metadata standards or suggestions for improvements:
1. Review existing documentation for patterns
2. Check this document for guidance
3. Open an issue or discussion for new metadata fields
4. Update this document when adding new standards
