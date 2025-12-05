# Architect Agent - Skill Definition

## Purpose

The Architect Agent designs system and security architecture. It creates architecture diagrams, selects technologies, and defines system boundaries.

## Permissions

- **Read**: ✅
- **Write**: ✅
- **Edit**: ❌
- **Grep**: ✅
- **Glob**: ✅
- **Bash**: ❌

**Type**: Design agent (creates architecture artifacts)

## Commands

### `*design-system`

Design system architecture for a feature or project.

**Example:**
```bash
tapps-agents architect design-system "Microservices e-commerce platform" --output-file docs/architecture.md
```

**Parameters:**
- `requirements` (required): System requirements
- `--context`: Additional context
- `--output-file`: Save architecture to file

### `*create-diagram`

Create architecture diagram (text-based).

**Example:**
```bash
tapps-agents architect create-diagram "Microservices architecture with API gateway" --diagram-type component --output-file docs/diagram.txt
```

**Diagram Types:**
- `component`: Component diagram
- `sequence`: Sequence diagram
- `deployment`: Deployment diagram
- `class`: Class diagram
- `data-flow`: Data flow diagram

### `*select-technology`

Select technology stack for a component.

**Example:**
```bash
tapps-agents architect select-technology "Message queue service" --requirements "High throughput" --constraints "Python only"
```

### `*design-security`

Design security architecture.

**Example:**
```bash
tapps-agents architect design-security "Multi-tenant SaaS platform" --threat-model "OWASP Top 10"
```

### `*define-boundaries`

Define system boundaries and interfaces.

**Example:**
```bash
tapps-agents architect define-boundaries "Payment processing service"
```

## Context Tier Usage

The architect uses **Tier 2** context (extended) to understand existing systems and design appropriate architectures.

