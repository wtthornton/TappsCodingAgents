# Knowledge Base Guide

**Simple File-Based RAG for Industry Experts**

This guide explains how to set up and use the simple file-based knowledge base system for Industry Expert agents.

## Overview

The Simple Knowledge Base provides RAG (Retrieval-Augmented Generation) capabilities without requiring vector databases. It uses:

- **File-based storage**: Markdown files in a `knowledge/` directory
- **Keyword search**: Fast text-based keyword matching
- **Context extraction**: Smart chunking with markdown awareness
- **Zero infrastructure**: No vector DB, embeddings, or external services needed

## Directory Structure

```
.tapps-agents/
├── knowledge/
│   ├── home-automation/
│   │   ├── protocols.md
│   │   ├── devices.md
│   │   └── best-practices.md
│   ├── energy-management/
│   │   ├── optimization.md
│   │   └── monitoring.md
│   └── general/
│       └── domain-knowledge.md
```

### Best Practices

1. **Organize by domain**: Create subdirectories for each domain
2. **Use clear file names**: Descriptive names help with filtering
3. **Markdown format**: Use proper markdown structure with headers
4. **Keep files focused**: One topic per file for better retrieval

## Knowledge File Format

### Example: `knowledge/home-automation/protocols.md`

```markdown
# Home Automation Protocols

## Zigbee Protocol

Zigbee is a low-power wireless protocol ideal for home automation.
It uses mesh networking for reliability.

### Advantages
- Low power consumption
- Mesh networking
- Good for battery devices

### Disadvantages
- Requires hub/coordinator
- Limited range per node

## Z-Wave Protocol

Z-Wave is another mesh protocol, operating at 900MHz.
It's known for good range and battery life.

### Use Cases
- Long-range requirements
- Battery-powered sensors
- Interoperability needs
```

### Markdown Guidelines

- **Headers structure knowledge**: Use `#`, `##`, `###` to organize
- **Headers get priority**: Headers are weighted higher in search
- **Plain text is fine**: The system extracts context from any markdown
- **Code blocks supported**: Code examples work well in knowledge base

## Usage

### Enabling RAG for an Expert

Experts are defined in configuration files (no code required):

```yaml
# .tapps-agents/experts.yaml
experts:
  - expert_id: expert-home-automation
    expert_name: Home Automation Expert
    primary_domain: home-automation
    rag_enabled: true  # Enable RAG
```

Then load from config:

```python
from pathlib import Path
from tapps_agents.experts import ExpertRegistry

registry = ExpertRegistry.from_config_file(
    Path(".tapps-agents/experts.yaml"),
    domain_config=domain_config
)
```

See [Expert Configuration Guide](EXPERT_CONFIG_GUIDE.md) for details.

### Knowledge Base Location

The system automatically looks for knowledge files in:

1. **Domain-specific**: `.tapps-agents/knowledge/{domain}/`
2. **Fallback**: `.tapps-agents/knowledge/`

For `home-automation` domain:
- First tries: `.tapps-agents/knowledge/home-automation/`
- Falls back to: `.tapps-agents/knowledge/`

### Automatic Integration

When `rag_enabled=True`, the expert automatically:

1. **Loads knowledge files** on activation
2. **Searches knowledge base** for domain context
3. **Provides sources** in consultation responses
4. **Enhances LLM prompts** with retrieved context

### Example Consultation with RAG

```python
# Expert automatically uses knowledge base
result = await expert.run("consult", query="What protocol should I use for battery devices?")

# Result includes:
{
    "answer": "For battery-powered devices, Zigbee is recommended...",
    "confidence": 0.51,
    "domain": "home-automation",
    "sources": [
        "home-automation/protocols.md",
        "home-automation/best-practices.md"
    ],
    "expert_id": "expert-home-automation"
}
```

## Advanced Usage

### Manual Knowledge Base Access

```python
from tapps_agents.experts.simple_rag import SimpleKnowledgeBase
from pathlib import Path

# Create knowledge base
kb = SimpleKnowledgeBase(
    knowledge_dir=Path(".tapps-agents/knowledge"),
    domain="home-automation"  # Optional filter
)

# Search for relevant chunks
chunks = kb.search("Zigbee protocol", max_results=5)

# Get formatted context
context = kb.get_context("battery devices", max_length=2000)

# Get source files
sources = kb.get_sources("mesh networking", max_results=3)
```

### Custom Search Parameters

```python
# More results, more context
chunks = kb.search(
    query="automation protocols",
    max_results=10,        # Get top 10 chunks
    context_lines=15       # Include 15 lines of context
)

# Limit context length
context = kb.get_context(
    query="devices",
    max_length=1000  # Maximum 1000 characters
)
```

## How It Works

### Search Algorithm

1. **Keyword extraction**: Splits query into keywords (>2 characters)
2. **Line scoring**: Scores each line by keyword matches
3. **Header boost**: Headers (`#`) get 1.5x score multiplier
4. **Chunking**: Groups consecutive high-scoring lines
5. **Context expansion**: Adds context lines around matches
6. **Ranking**: Sorts chunks by relevance score

### Context Extraction

- **Markdown-aware**: Aligns chunks to header boundaries
- **Context windows**: Includes surrounding lines for context
- **Deduplication**: Avoids duplicate content in results
- **Length limits**: Respects max_length parameter

### Scoring

- **Keyword matches**: Each matching keyword adds to score
- **Header priority**: Headers weighted 1.5x
- **Normalization**: Scores normalized by keyword count
- **Relevance ranking**: Top-scoring chunks returned first

## Limitations

### Current Limitations

1. **Keyword-only**: No semantic similarity (exact matches)
2. **No embeddings**: Doesn't understand meaning, only keywords
3. **File-based**: All knowledge must be in markdown files
4. **Synchronous**: Loading happens at initialization

### When to Upgrade

Consider upgrading to vector DB RAG if:

- **Large knowledge bases**: >100 files or >1MB total
- **Semantic search needed**: Want to find conceptually similar content
- **Dynamic updates**: Frequently changing knowledge
- **Performance issues**: Slow search times

## Tips & Best Practices

### Organizing Knowledge

1. **One domain per directory**: Keep domains separate
2. **Descriptive file names**: `protocols.md` better than `doc1.md`
3. **Use headers liberally**: More headers = better chunking
4. **Keep files focused**: One main topic per file

### Writing Knowledge Files

1. **Lead with keywords**: Important terms in first paragraph
2. **Use headers**: Structure content with `##`, `###`
3. **Include examples**: Code/configuration examples help
4. **Cross-reference**: Mention related topics in context

### Performance

1. **Limit file size**: Keep files < 100KB each
2. **Optimize queries**: More specific queries = better results
3. **Cache knowledge**: Files are cached at initialization
4. **Domain filtering**: Use domain parameter to narrow search

## Troubleshooting

### No Results Found

**Problem**: Search returns no chunks.

**Solutions**:
- Check knowledge directory exists: `.tapps-agents/knowledge/`
- Verify file naming matches domain
- Try broader search terms
- Check file encoding (must be UTF-8)

### Poor Relevance

**Problem**: Results don't match query intent.

**Solutions**:
- Use more specific keywords
- Add headers to knowledge files
- Organize knowledge better
- Consider more context lines

### Slow Performance

**Problem**: Search is slow.

**Solutions**:
- Reduce number of knowledge files
- Use domain filtering
- Limit max_results parameter
- Consider upgrading to vector DB

## Example Knowledge Base

See `examples/knowledge/` for example knowledge files:

- `home-automation/protocols.md` - Protocol comparison
- `home-automation/devices.md` - Device recommendations
- `energy-management/optimization.md` - Optimization strategies

## Next Steps

- **Add your domain knowledge**: Create knowledge files for your experts
- **Test searches**: Try various queries to verify relevance
- **Iterate**: Refine knowledge structure based on results
- **Upgrade if needed**: Move to vector DB if limitations hit

---

**See Also:**
- [Expert Registry Guide](EXPERT_REGISTRY_GUIDE.md)
- [BaseExpert API](BASE_EXPERT_API.md)
- [Workflow Integration](WORKFLOW_INTEGRATION.md)

