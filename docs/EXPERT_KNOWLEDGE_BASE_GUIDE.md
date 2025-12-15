# Expert Knowledge Base Guide

**Version:** 2.0.1  
**Last Updated:** December 2025

## Overview

Expert knowledge bases provide domain-specific knowledge through Retrieval-Augmented Generation (RAG). This guide covers knowledge base structure, format, and best practices for both built-in and customer experts.

## Knowledge Base Structure

### Built-in Knowledge Bases

Built-in expert knowledge bases are located in the framework package:

```
tapps_agents/experts/knowledge/
├── security/
│   ├── owasp-top-10.md
│   ├── security-patterns.md
│   ├── vulnerabilities.md
│   └── ...
├── performance/
│   ├── optimization-patterns.md
│   ├── caching.md
│   └── ...
└── ...
```

### Customer Knowledge Bases

Customer expert knowledge bases are located in the project:

```
.tapps-agents/knowledge/
├── {domain}/
│   ├── overview.md
│   ├── patterns.md
│   └── ...
└── general/
    └── ...
```

## Markdown Format Guidelines

### File Structure

Each knowledge file should follow this structure:

```markdown
# Title

Brief overview of the topic.

## Key Concepts

- Concept 1: Description
- Concept 2: Description

## Best Practices

1. Practice 1
2. Practice 2

## Examples

### Example 1: Title

```code
example code
```

## Anti-Patterns

- Anti-pattern 1: Why it's bad
- Anti-pattern 2: Why it's bad

## References

- [Link 1](url)
- [Link 2](url)
```

### Content Guidelines

1. **Be Specific**: Include concrete examples and code snippets
2. **Be Current**: Keep information up-to-date with latest practices
3. **Be Comprehensive**: Cover the topic thoroughly
4. **Be Structured**: Use clear headings and sections
5. **Cite Sources**: Include references when appropriate

### Code Examples

Always include code examples:

```markdown
## Example: Secure Authentication

```python
def authenticate_user(username: str, password: str) -> bool:
    # Hash password before comparison
    hashed = hash_password(password)
    return verify_hash(username, hashed)
```
```

### Anti-Patterns

Always include what NOT to do:

```markdown
## Anti-Pattern: Plain Text Passwords

❌ **Don't do this:**
```python
if password == stored_password:  # Insecure!
    return True
```

✅ **Do this instead:**
```python
if verify_password(password, stored_hash):
    return True
```
```

## Knowledge Base Organization

### By Domain

Organize knowledge by domain:

```
knowledge/
├── security/
│   ├── authentication.md
│   ├── authorization.md
│   └── encryption.md
├── performance/
│   ├── caching.md
│   ├── optimization.md
│   └── scalability.md
└── ...
```

### By Topic

Within each domain, organize by topic:

```
security/
├── authentication.md      # Authentication patterns
├── authorization.md       # Authorization models
├── encryption.md          # Encryption methods
├── vulnerabilities.md     # Common vulnerabilities
└── compliance.md          # Security compliance
```

## Best Practices

### 1. File Naming

- Use lowercase with hyphens: `owasp-top-10.md`
- Be descriptive: `keyboard-navigation.md` not `kb-nav.md`
- Group related files: `wcag-2.1.md`, `wcag-2.2.md`

### 2. Content Length

- Target 500-2000 words per file
- Break large topics into multiple files
- Keep files focused on single topics

### 3. Headings

- Use clear, descriptive headings
- Follow hierarchy: H1 → H2 → H3
- Use H1 for main title only

### 4. Code Blocks

- Include language tags: ` ```python`
- Provide context for code
- Explain what the code does

### 5. Links

- Use relative links for internal references
- Use absolute links for external references
- Keep links up-to-date

## Updating Knowledge Bases

### Built-in Knowledge Bases

Built-in knowledge bases are updated via framework releases:

1. Update knowledge files in `tapps_agents/experts/knowledge/`
2. Test knowledge retrieval
3. Update version in release notes

### Customer Knowledge Bases

Customer knowledge bases are updated in the project:

1. Edit files in `.tapps-agents/knowledge/{domain}/`
2. Knowledge is automatically reloaded
3. No restart required

## RAG Integration

### How RAG Works

1. **Query**: Agent asks a question
2. **Search**: Knowledge base searches for relevant content
3. **Retrieve**: Relevant chunks are retrieved
4. **Generate**: LLM generates answer using retrieved context
5. **Cite**: Sources are cited in response

### Optimizing for RAG

1. **Use Clear Headings**: Headings help with chunking
2. **Include Keywords**: Use domain-specific terminology
3. **Structure Content**: Use lists, tables, and code blocks
4. **Be Specific**: Include concrete examples
5. **Cross-Reference**: Link related topics

### Chunking Strategy

Knowledge bases are chunked by:
- Headings (H2, H3)
- Paragraphs
- Code blocks
- Lists

Keep content well-structured for better chunking.

## Knowledge Base Examples

### Example 1: Security Pattern

```markdown
# Authentication Patterns

## Password-Based Authentication

### Best Practices

1. **Hash Passwords**: Always hash passwords before storage
   ```python
   import bcrypt
   
   def hash_password(password: str) -> str:
       return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
   ```

2. **Use Strong Hashing**: Use bcrypt, Argon2, or scrypt
3. **Salt Passwords**: Always use unique salts

### Anti-Patterns

❌ **Plain Text Storage**
```python
# NEVER do this
users[username] = password
```

## References

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/)
```

### Example 2: Performance Pattern

```markdown
# Caching Strategies

## Cache-Aside Pattern

### Implementation

```python
def get_data(key: str):
    # Check cache first
    data = cache.get(key)
    if data:
        return data
    
    # Load from database
    data = database.get(key)
    
    # Store in cache
    cache.set(key, data, ttl=3600)
    return data
```

### When to Use

- Read-heavy workloads
- Data changes infrequently
- Cache misses are acceptable

## References

- [Cache-Aside Pattern](https://docs.microsoft.com/)
```

## Testing Knowledge Bases

### Verify Content

1. Check all files are valid markdown
2. Verify code examples are correct
3. Test links are working
4. Ensure content is up-to-date

### Test RAG Retrieval

```python
from tapps_agents.experts import ExpertRegistry

registry = ExpertRegistry(load_builtin=True)
expert = registry.get_expert("expert-security")

# Test knowledge retrieval
chunks = expert.knowledge_base.search("authentication")
assert len(chunks) > 0
```

## Maintenance

### Regular Updates

- Review knowledge bases quarterly
- Update with latest best practices
- Remove outdated information
- Add new patterns and examples

### Version Control

- Track changes in git
- Use meaningful commit messages
- Tag releases with knowledge base versions

## Troubleshooting

### Knowledge Not Found

If RAG doesn't find relevant content:
1. Check file exists in knowledge base
2. Verify domain matches expert domain
3. Try different query keywords
4. Check file format is valid markdown

### Low Quality Results

If RAG returns low-quality results:
1. Improve content structure
2. Add more specific examples
3. Use clearer headings
4. Include more keywords

## Related Documentation

- [Built-in Experts Guide](./BUILTIN_EXPERTS_GUIDE.md)
- [Expert Configuration Guide](./EXPERT_CONFIG_GUIDE.md)
- [API Documentation](./API.md)

