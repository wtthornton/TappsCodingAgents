---
title: ADR-002: Equal Platform Support Policy
version: 2.0.0
status: accepted
last_updated: 2026-02-03
tags: [adr, runtime, platform-support, policy]
supersedes: ADR-002 v1.0.0 (Cursor-First Runtime Policy)
---

# ADR-002: Equal Platform Support Policy

**Status**: Accepted
**Date**: 2026-02-03
**Deciders**: TappsCodingAgents Team
**Tags**: runtime, platform-support, policy, execution-mode

## Context

TappsCodingAgents provides workflow orchestration, agent coordination, and quality enforcement as core framework value. These capabilities should work equally well across all platforms - Claude Desktop, Cursor IDE, and Claude Code CLI. Users should be able to choose their preferred environment without feature limitations.

**Previous Policy**: ADR-002 v1.0.0 established a "Cursor-First" runtime policy that prioritized Cursor IDE integration. This created an implicit hierarchy where Cursor users were considered primary and other platforms were secondary.

**Why Change?**: The framework's value comes from workflow orchestration, agent coordination, and quality enforcement - none of which require platform-specific features. Equal support provides better architecture, wider adoption, and platform independence.

## Decision

**Equal Platform Support Policy:**

- **All platforms are first-class citizens**: Claude Desktop, Cursor IDE, and Claude Code CLI receive equal support
- **Handler-first execution**: Use `AgentHandlerRegistry` BEFORE falling back to platform-specific features
- **Platform-agnostic core**: All core functionality (workflows, agents, quality gates) works across all platforms
- **Optional enhancements**: Platform-specific features (Cursor Skills, Background Agents) are optional enhancements, not requirements

**Mental Model:**
- **Platform provides LLM reasoning**: Each platform (Claude, Cursor, CLI) uses its configured model
- **TappsCodingAgents provides orchestration**: Workflows, quality gates, agent handlers, worktree isolation, caching - works the same everywhere
- **Handlers are platform-agnostic**: `ImplementerHandler`, `ReviewerHandler`, etc. work across all platforms

## Rationale

This policy provides:

1. **User Choice**: Users can choose their preferred environment (Claude Desktop, Cursor IDE, or CLI) without feature limitations
2. **Platform Independence**: Framework value comes from orchestration, not platform-specific features
3. **Better Architecture**: Handler-first execution provides cleaner, more maintainable code paths
4. **Future-Proofing**: New platforms (VS Code, other IDEs) can be added without rewriting core logic
5. **No Vendor Lock-In**: Framework works independently of any single IDE or tool
6. **Consistent Behavior**: Same quality gates, workflows, and agent execution across all platforms

## Consequences

### Positive

- **User Flexibility**: Users choose their preferred environment without compromising features
- **Better Architecture**: Handler pattern provides cleaner, more testable code
- **Wider Adoption**: Framework appeals to Claude Desktop users, Cursor users, and CLI users equally
- **Platform Independence**: No vendor lock-in to any single IDE
- **Easier Maintenance**: One execution path (handlers), not separate platform-specific paths
- **Future-Proofing**: Easy to add new platforms (VS Code, other IDEs) without core changes

### Negative

- **More Testing Required**: Must test all features across three platforms (Claude, Cursor, CLI)
- **Platform Detection**: Need to detect platform capabilities gracefully
- **Documentation Scope**: Must document behavior across all platforms

### Neutral

- **Platform-Specific Enhancements**: Optional features (Cursor Skills, Background Agents) still available but not required
- **LLM Configuration**: Each platform handles its own LLM setup (framework delegates to platform)

## Alternatives Considered

### Alternative 1: Cursor-First Runtime (Previous Policy)

**Description**: Prioritize Cursor IDE integration, treating other platforms as secondary

**Pros**:
- Optimized for Cursor users
- Simpler initial implementation
- Leverages Cursor's native capabilities

**Cons**:
- Locks out Claude Desktop and CLI users from core features
- Creates platform hierarchy (first-class vs second-class)
- Handler bypass in CursorExecutor (BUG-003)
- Harder to add new platforms
- Architectural debt from platform-specific code paths

**Why Not Chosen**: Framework value comes from orchestration, not platform-specific features. Equal support provides better architecture and wider adoption without sacrificing Cursor integration quality.

### Alternative 2: Platform-Specific Implementations

**Description**: Maintain separate code paths for each platform (Claude, Cursor, CLI)

**Pros**:
- Optimized for each platform's unique features
- Maximum flexibility per platform

**Cons**:
- Three code paths to maintain
- High risk of feature drift between platforms
- Difficult to ensure feature parity
- Testing complexity (3x test matrix)
- Architectural complexity

**Why Not Chosen**: Handler-first execution provides platform-agnostic functionality without sacrificing platform-specific enhancements. One code path with optional platform features is simpler and more maintainable.

### Alternative 3: CLI-Only Framework

**Description**: Focus exclusively on CLI execution, no IDE integration

**Pros**:
- Simplest implementation
- No platform-specific code
- Works everywhere via command line

**Cons**:
- Poor developer experience for IDE users
- No integration with Cursor Skills or Claude Desktop
- Users must leave IDE to run workflows
- Reduced adoption among IDE users

**Why Not Chosen**: IDE integration (Cursor Skills, Claude Desktop) provides better developer experience. Equal support allows both CLI and IDE workflows.

## Implementation

The equal support policy is implemented through:

1. **Handler-First Execution** (BUG-003 Fix):
   - `CursorExecutor` now tries `AgentHandlerRegistry` BEFORE `SkillInvoker`
   - Ensures handlers like `ImplementerHandler` work across all platforms
   - Falls back gracefully to platform-specific features when handlers unavailable

2. **Platform-Agnostic Handlers**:
   - All handlers (`ImplementerHandler`, `ReviewerHandler`, `TesterHandler`, etc.) work across platforms
   - Brownfield/greenfield detection works in Claude, Cursor, and CLI
   - Quality gates enforced consistently

3. **Optional Platform Features**:
   - Cursor Skills: Optional enhancement for Cursor users
   - Background Agents: Optional for asynchronous execution in Cursor
   - CLI commands: Available for automation and CI/CD

## Related ADRs

- [ADR-001: Instruction-Based Architecture](ADR-001-instruction-based-architecture.md)

## References

- [Equal Support Policy](../../CLAUDE_CURSOR_EQUAL_SUPPORT.md) - Full policy document
- [BUG-003: Handler Bypass Fix](../../bugs/BUG-003-IMPLEMENTATION-WRONG-ARTIFACTS.md) - Implementation details
- [How It Works Documentation](../HOW_IT_WORKS.md)
- [Architecture Overview](../ARCHITECTURE.md)
- [Handler System](../../agent_handlers/README.md)

---

**Last Updated**: 2026-02-03
**Maintained By**: TappsCodingAgents Team
**Supersedes**: ADR-002 v1.0.0 (Cursor-First Runtime Policy)
