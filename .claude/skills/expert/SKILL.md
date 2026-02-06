---
name: expert
description: Expert system discovery and consultation. List available experts, consult domain experts, search knowledge bases, and browse cached libraries.
---

# Expert System Skill

Discover and consult the TappsCodingAgents expert system.

## Commands

| Command | What It Does |
|---------|-------------|
| `@expert *list [--domain <d>]` | List all available experts (name, domain, triggers, knowledge file count) |
| `@expert *consult "<question>" --domain <domain>` | Consult expert(s) in a domain — returns RAG knowledge + expert analysis |
| `@expert *info <expert-id>` | Show detailed info about a specific expert (knowledge files, triggers, priority) |
| `@expert *search "<query>"` | Search across all expert knowledge bases |
| `@expert *cached [--library <name>]` | List cached Context7 libraries, or show cached topics for a library |

## How Expert Consultation Works

1. When you invoke `@expert *consult`, the skill runs: `tapps-agents expert consult <domain> "<question>"`
2. The CLI internally queries the RAG knowledge base for the domain
3. Matching knowledge is returned with expert analysis context
4. You can use this knowledge in your response to the user

## Examples

```
@expert *list
@expert *list --domain security
@expert *consult "How should I handle JWT refresh tokens?" --domain security
@expert *info expert-security-owasp
@expert *search "authentication best practices"
@expert *cached
@expert *cached --library fastapi
```

## Integration with Other Agents

All TappsCodingAgents agents (reviewer, implementer, architect, designer, tester, debugger, ops, enhancer) automatically consult domain experts when relevant domains are detected via `ExpertSupportMixin`.

You can also **explicitly** consult experts before using other agents:
- `@expert *consult "question" --domain security` — get security expert knowledge first
- `@expert *cached --library fastapi` — check what library documentation is cached
- Then use `@implementer *implement` or `@reviewer *review` with the expert context in mind

## CLI Equivalent

```bash
tapps-agents expert list [--domain <domain>] [--format json|text]
tapps-agents expert consult <domain> "<question>" [--format json|text|markdown]
tapps-agents expert info <expert-id> [--format json|text]
tapps-agents expert search "<query>" [--format json|text]
tapps-agents expert cached [--library <name>] [--format json|text]
```
