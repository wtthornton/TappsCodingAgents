# Analyst Agent - Skill Definition

## Purpose

The Analyst Agent gathers requirements, performs technical research, and estimates effort/risk. It is a read-only agent that analyzes and provides recommendations.

## Permissions

- **Read**: ✅
- **Write**: ❌
- **Edit**: ❌
- **Grep**: ✅
- **Glob**: ✅
- **Bash**: ❌

**Type**: Read-only agent (analysis and research only)

## Commands

### `*gather-requirements`

Gather and extract detailed requirements from a description.

**Example:**
```bash
tapps-agents analyst gather-requirements "Build a user authentication system"
```

**Parameters:**
- `description` (required): Requirement description
- `--context`: Additional context
- `--output-file`: Save requirements to file

### `*analyze-stakeholders`

Analyze stakeholders and their needs.

**Example:**
```bash
tapps-agents analyst analyze-stakeholders "New payment feature" --stakeholders "Product Manager" "Engineering Lead"
```

### `*research-technology`

Research technology options for a requirement.

**Example:**
```bash
tapps-agents analyst research-technology "Need real-time messaging" --criteria "performance" "scalability"
```

### `*estimate-effort`

Estimate effort and complexity for a feature.

**Example:**
```bash
tapps-agents analyst estimate-effort "Implement OAuth2 authentication"
```

### `*assess-risk`

Assess risks for a feature or project.

**Example:**
```bash
tapps-agents analyst assess-risk "Migrate database to new schema"
```

### `*competitive-analysis`

Perform competitive analysis.

**Example:**
```bash
tapps-agents analyst competitive-analysis "Mobile banking app" --competitors "Chase" "Bank of America"
```

## Context Tier Usage

The analyst uses **Tier 1** context (minimal) since it focuses on high-level analysis and doesn't need deep code context.

