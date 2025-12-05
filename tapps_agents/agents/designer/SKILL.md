# Designer Agent - Skill Definition

## Purpose

The Designer Agent designs API contracts, data models, and UI/UX specifications. It creates wireframes and defines design systems.

## Permissions

- **Read**: ✅
- **Write**: ✅
- **Edit**: ❌
- **Grep**: ✅
- **Glob**: ✅
- **Bash**: ❌

**Type**: Design agent (creates design artifacts)

## Commands

### `*design-api`

Design API contracts and endpoints.

**Example:**
```bash
tapps-agents designer design-api "User management API" --api-type REST --output-file docs/api-spec.json
```

**Parameters:**
- `requirements` (required): API requirements
- `--api-type`: REST, GraphQL, or gRPC (default: REST)
- `--output-file`: Save API spec to file

### `*design-data-model`

Design data models and schemas.

**Example:**
```bash
tapps-agents designer design-data-model "E-commerce product catalog" --output-file docs/data-model.json
```

### `*design-ui`

Design UI/UX specifications.

**Example:**
```bash
tapps-agents designer design-ui "Checkout flow" --user-stories "As a user" "I want to pay" --output-file docs/ui-spec.json
```

### `*create-wireframe`

Create wireframe (text-based).

**Example:**
```bash
tapps-agents designer create-wireframe "User dashboard screen" --wireframe-type page --output-file docs/wireframe.txt
```

**Wireframe Types:**
- `page`: Page layout wireframe
- `component`: Component wireframe
- `flow`: User flow wireframe

### `*define-design-system`

Define design system (colors, typography, components).

**Example:**
```bash
tapps-agents designer define-design-system "Modern SaaS application" --brand-guidelines "Blue primary color" --output-file docs/design-system.json
```

## Context Tier Usage

The designer uses **Tier 2** context (extended) to understand existing design patterns and maintain consistency.

