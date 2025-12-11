# Built-in Expert Knowledge Bases

This directory contains knowledge bases for built-in framework experts. These knowledge bases provide technical domain expertise that ships with the TappsCodingAgents framework.

## Structure

Each expert has its own subdirectory containing markdown knowledge files:

```
knowledge/
├── security/          # Security Expert knowledge base
│   ├── owasp-top10.md
│   ├── secure-coding-practices.md
│   ├── threat-modeling.md
│   └── vulnerability-patterns.md
├── performance/      # Performance Expert (Phase 2)
├── testing/          # Testing Expert (Phase 2)
├── data-privacy/     # Data Privacy Expert (Phase 3)
├── accessibility/    # Accessibility Expert (Phase 4)
└── user-experience/  # UX Expert (Phase 4)
```

## Knowledge Base Format

Knowledge files are written in Markdown format. The RAG system uses:

- **Headers** (`#`, `##`, `###`) to structure knowledge and prioritize search results
- **Code blocks** for examples
- **Lists** for checklists and guidelines
- **Plain text** for explanations

## Usage

Built-in experts automatically load knowledge from this directory when:
1. The expert is activated
2. RAG is enabled for the expert
3. The expert's `primary_domain` matches a subdirectory name

## Adding Knowledge

To add knowledge to a built-in expert:

1. Create or edit markdown files in the expert's subdirectory
2. Use clear headers and structure
3. Include code examples where relevant
4. Keep content focused and actionable
5. Update this README if adding new experts

## Knowledge Base Best Practices

- **Be specific**: Include concrete examples and patterns
- **Be current**: Keep knowledge up to date with latest practices
- **Be comprehensive**: Cover common scenarios and edge cases
- **Be structured**: Use headers and sections for easy navigation
- **Be actionable**: Provide clear guidance and checklists

## References

- [Knowledge Base Guide](../../../docs/KNOWLEDGE_BASE_GUIDE.md)
- [Expert Configuration Guide](../../../docs/EXPERT_CONFIG_GUIDE.md)

