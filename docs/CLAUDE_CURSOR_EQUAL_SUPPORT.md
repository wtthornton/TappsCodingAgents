# Claude and Cursor Equal Support Policy

**Date:** 2026-02-03
**Status:** ACTIVE POLICY
**Supersedes:** "Cursor-first" runtime policy

---

## Policy Statement

TappsCodingAgents provides **equal, first-class support for both Claude and Cursor** as execution environments. Neither platform is prioritized over the other. The framework is designed to work seamlessly in both environments with feature parity.

---

## Why Equal Support Matters

### 1. **User Choice**
- Users should be able to choose their preferred environment without feature limitations
- Claude Desktop users get the same capabilities as Cursor IDE users
- CLI users (via Claude Code) have equal access to all features

### 2. **Platform Independence**
- Framework value comes from workflow orchestration, not platform-specific features
- Skills and agents should work universally across platforms
- No vendor lock-in to any single IDE or tool

### 3. **Future-Proofing**
- New platforms (VS Code, other IDEs) can be added without rewriting core logic
- Framework architecture remains platform-agnostic
- Migration between platforms is seamless

---

## Current Implementation Status

### ✅ What Works Equally

| Feature | Claude Desktop | Cursor IDE | Claude Code CLI |
|---------|----------------|------------|-----------------|
| Workflow Execution | ✅ | ✅ | ✅ |
| Agent Invocation | ✅ | ✅ | ✅ |
| Task Management (Beads) | ✅ | ✅ | ✅ |
| Quality Gates | ✅ | ✅ | ✅ |
| Expert System | ✅ | ✅ | ✅ |
| Context7 Integration | ✅ | ✅ | ✅ |

### ⚠️ Platform-Specific Features

**These are acceptable** as long as they're optional and don't block core functionality:

| Feature | Claude | Cursor | Notes |
|---------|--------|--------|-------|
| Cursor Skills | ❌ | ✅ | Cursor-only feature, but framework works without it |
| Background Agents | ❌ | ✅ | Cursor-specific, optional enhancement |
| IDE Integration | ❌ | ✅ | Natural IDE feature, doesn't affect CLI users |

**Key Rule:** If removing Cursor-specific features breaks the framework for Claude users, the design is wrong.

---

## Architecture Principles

### 1. **Handler-First Execution**

**CORRECT:**
```python
# Try AgentHandlerRegistry first (platform-agnostic)
handler = registry.find_handler(agent_name, action)

if handler:
    # Use handler (works everywhere)
    result = await handler.execute(step, action, target_path)
else:
    # Platform-specific fallback
    if is_cursor_mode():
        result = await skill_invoker.invoke_skill(...)
    else:
        result = await direct_agent_invocation(...)
```

**WRONG:**
```python
# Cursor-first approach (locks out other platforms)
if is_cursor_mode():
    # Only works in Cursor
    result = await skill_invoker.invoke_skill(...)
else:
    # Fallback treated as second-class
    result = await handler.execute(...)
```

### 2. **Feature Detection, Not Platform Detection**

**CORRECT:**
```python
# Check if feature is available
if supports_background_agents():
    use_background_execution()
else:
    use_direct_execution()
```

**WRONG:**
```python
# Platform-specific branching
if is_cursor_mode():
    # Cursor path
else:
    # Claude path
```

### 3. **Graceful Degradation**

All core features must work without platform-specific enhancements:
- ✅ Workflows work without Cursor Skills
- ✅ Agents work without Background Agents
- ✅ Quality gates work without IDE integration

---

## Migration from "Cursor-First"

### What Needs to Change

1. **Code Comments**
   - Remove "@ai-prime-directive: Cursor-native" comments
   - Update to "@ai-prime-directive: Platform-agnostic execution"

2. **Execution Order**
   - BUG-003 Fix: CursorExecutor now tries handlers BEFORE skill_invoker ✅
   - Ensures equal execution paths for all platforms

3. **Documentation**
   - Update ADR-002 to reflect equal support policy
   - Remove references to "Cursor-first runtime"
   - Emphasize dual-platform support

4. **Testing**
   - Test all workflows in both Claude and Cursor environments
   - Ensure feature parity across platforms
   - Add CI checks for both execution modes

---

## Implementation Guidelines

### For New Features

**Before implementing:**
1. ✅ Will this work in Claude Desktop?
2. ✅ Will this work in Cursor IDE?
3. ✅ Will this work in Claude Code CLI?
4. ✅ If platform-specific, is it optional?

**Example: Adding Background Execution**
```python
class StepExecutor:
    async def execute(self, step):
        # Try background execution if available (optional enhancement)
        if self.supports_background():
            return await self._execute_background(step)

        # Always have a platform-agnostic fallback (required)
        return await self._execute_direct(step)
```

### For Bug Fixes

**BUG-003 is a perfect example:**
- ❌ Problem: CursorExecutor bypassed AgentHandlerRegistry (Cursor-specific path)
- ✅ Solution: Use handlers FIRST, fall back to platform-specific features

This ensures Claude users get the same quality of execution as Cursor users.

---

## Benefits of Equal Support

### For Users
- ✨ Choose the best tool for their workflow
- ✨ No feature limitations based on platform
- ✨ Seamless migration between platforms

### For Framework
- 🎯 Better architecture (handler pattern works everywhere)
- 🎯 More robust (platform-agnostic code is better tested)
- 🎯 Easier maintenance (one code path, not two)

### For Contributors
- 🚀 Clear architectural principles
- 🚀 Easier to understand (no platform-specific branches)
- 🚀 Better testing (works the same everywhere)

---

## Related Documents

- [Architecture Overview](ARCHITECTURE.md)
- [Tool Integrations](tool-integrations.md)
- [Handler System](agent_handlers/README.md)
- [BUG-003: Handler Bypass Fix](bugs/BUG-003-IMPLEMENTATION-WRONG-ARTIFACTS.md)

---

## Conclusion

**TappsCodingAgents is Claude AND Cursor, not Cursor-first.**

The framework's value comes from:
- 🎯 Workflow orchestration
- 🎯 Agent coordination
- 🎯 Quality enforcement
- 🎯 Expert system

None of these require platform-specific features. Platform-specific enhancements are welcome as **optional** improvements, but core functionality must work equally well everywhere.

---

**Policy Owner:** TappsCodingAgents Team
**Last Updated:** 2026-02-03
**Next Review:** When adding new platform support
