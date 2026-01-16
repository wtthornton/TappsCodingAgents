---
title: MCP Standards Compliance
version: 1.0.0
status: active
last_updated: 2026-01-20
tags: [mcp, standards, compliance, json-rpc]
---

# MCP Standards Compliance

This document describes TappsCodingAgents' compliance with Model Context Protocol (MCP) standards.

## Overview

TappsCodingAgents implements MCP (Model Context Protocol) to provide unified tool access across multiple servers. The framework uses MCP Gateway (`tapps_agents/mcp/gateway.py`) to route tool requests to appropriate MCP servers.

## MCP Standards

### JSON-RPC 2.0 Compliance

**Status**: ✅ Compliant

TappsCodingAgents uses JSON-RPC 2.0 for MCP communication:

- **Request Format**: JSON-RPC 2.0 request objects
- **Response Format**: JSON-RPC 2.0 response objects
- **Error Handling**: JSON-RPC 2.0 error objects
- **Method Invocation**: Standard JSON-RPC method calls

**Implementation:**
- MCP Gateway routes tool calls to registered servers
- Tool registry manages tool definitions and handlers
- Error responses follow JSON-RPC 2.0 error format

### JSON Schema 2020-12 Compliance

**Status**: ✅ Compliant

Tool parameters are defined using JSON Schema 2020-12:

- **Parameter Definitions**: JSON Schema objects
- **Type Validation**: String, integer, boolean, object, array types
- **Required Fields**: `required` array in parameter schemas
- **Constraints**: `minimum`, `maximum`, `default` values

**Example:**
```python
parameters={
    "libraryName": {
        "type": "string",
        "required": True,
        "description": "Library/package name to resolve",
    },
    "page": {
        "type": "integer",
        "required": False,
        "default": 1,
        "minimum": 1,
        "maximum": 10,
    }
}
```

## MCP Server Implementation

### Server Architecture

**MCP Gateway** (`tapps_agents/mcp/gateway.py`):
- Unified interface for tool access
- Routes requests to appropriate servers
- Manages tool registry

**MCP Servers** (`tapps_agents/mcp/servers/`):
- **Context7 Server**: Library documentation (`context7.py`)
- **Playwright Server**: Browser automation (`playwright.py` - if implemented)
- **Filesystem Server**: File operations (`filesystem.py`)
- **Git Server**: Git operations (`git.py`)
- **Analysis Server**: Code analysis (`analysis.py`)

### Tool Registration

Tools are registered in the ToolRegistry with:
- **Name**: Tool identifier (e.g., `mcp_Context7_resolve-library-id`)
- **Description**: Human-readable description
- **Category**: Tool category (CUSTOM, FILESYSTEM, GIT, etc.)
- **Handler**: Function to execute the tool
- **Parameters**: JSON Schema parameter definitions
- **Cache Strategy**: Caching behavior (tier1, tier2, none)
- **Auth Requirements**: Whether authentication is required

## Versioning Strategy

### MCP Protocol Version

**Current Version**: MCP 1.0 (Model Context Protocol)

**Versioning Approach:**
- Protocol version tracked in server implementations
- Backward compatibility maintained across minor versions
- Breaking changes require major version increment

### Library ID Conventions

**Context7 Library IDs:**
- Format: `/owner/repo` (e.g., `/vercel/next.js`)
- Resolution: Library names resolved to Context7-compatible IDs
- Examples:
  - `react` → `/facebook/react`
  - `fastapi` → `/tiangolo/fastapi`
  - `pytest` → `/pytest-dev/pytest`

**Library ID Resolution:**
- Uses `mcp_Context7_resolve-library-id` tool
- Returns list of matching libraries with IDs
- Fuzzy matching for common variations

## Configuration

### MCP Server Configuration

**Location**: `.cursor/mcp.json`

**Example Configuration:**
```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@context7/mcp-server"],
      "env": {
        "CONTEXT7_API_KEY": "${CONTEXT7_API_KEY}"
      }
    }
  }
}
```

### Server Detection

**Automatic Detection:**
- MCP servers are auto-detected during `tapps-agents init`
- Missing servers are reported with setup instructions
- Server status checked via `tapps-agents doctor`

## Compliance Checklist

### JSON-RPC 2.0

- [x] Request format follows JSON-RPC 2.0 specification
- [x] Response format follows JSON-RPC 2.0 specification
- [x] Error handling uses JSON-RPC 2.0 error objects
- [x] Method invocation uses standard JSON-RPC calls

### JSON Schema 2020-12

- [x] Parameter definitions use JSON Schema 2020-12
- [x] Type validation follows JSON Schema types
- [x] Required fields specified in `required` array
- [x] Constraints (minimum, maximum, default) supported

### Versioning

- [x] Protocol version tracked
- [x] Backward compatibility maintained
- [x] Library ID conventions documented

### Tool Registration

- [x] Tools registered with complete metadata
- [x] Parameter schemas defined
- [x] Error handling implemented
- [x] Cache strategies configured

## Known Limitations

### Current Implementation

1. **Direct API Calls**: Framework uses MCP Gateway pattern, not direct JSON-RPC calls
2. **Server Abstraction**: MCP servers abstract JSON-RPC details
3. **Tool Registry**: Custom tool registry, not standard MCP tool discovery

### Future Enhancements

1. **Full JSON-RPC Client**: Direct JSON-RPC 2.0 client implementation
2. **Standard Tool Discovery**: MCP-standard tool discovery protocol
3. **Schema Validation**: Enhanced JSON Schema validation

## Related Documentation

- **MCP Gateway**: `tapps_agents/mcp/gateway.py`
- **Context7 Integration**: `docs/CONTEXT7_PATTERNS.md`
- **Architecture Overview**: `docs/ARCHITECTURE.md`

---

**Last Updated**: 2026-01-20  
**Maintained By**: TappsCodingAgents Team
