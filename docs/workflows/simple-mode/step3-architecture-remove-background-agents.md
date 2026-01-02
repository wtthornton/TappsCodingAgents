# Step 3: Architecture Design - Remove Background Agents

## System Architecture Changes

### Current Architecture (Before)

```
┌─────────────────────────────────────────────────────────────┐
│                    Workflow Executor                        │
│                                                             │
│  ┌──────────────────┐      ┌──────────────────────────┐   │
│  │ Runtime Mode     │      │ Execution Router         │   │
│  │ Detection        │─────▶│                          │   │
│  └──────────────────┘      │  ┌────────────────────┐  │   │
│                            │  │ Cursor Mode?       │  │   │
│                            │  └────────────────────┘  │   │
│                            │           │               │   │
│                            │    ┌──────┴──────┐       │   │
│                            │    │             │       │   │
│                            │  YES            NO       │   │
│                            │    │             │       │   │
│  ┌──────────────────┐      │    ▼             ▼       │   │
│  │ Cursor Executor  │      │ ┌──────────┐ ┌─────────┐│   │
│  │                  │      │ │ Cursor   │ │ Headless││   │
│  │ ┌──────────────┐ │      │ │ Executor │ │Executor ││   │
│  │ │ Skill        │ │      │ └──────────┘ └─────────┘│   │
│  │ │ Invoker      │ │      └──────────────────────────┘   │
│  │ └──────────────┘ │                                      │
│  │        │         │                                      │
│  │        ▼         │                                      │
│  │ ┌──────────────┐ │                                      │
│  │ │ Background   │ │                                      │
│  │ │ Agent API    │ │                                      │
│  │ └──────────────┘ │                                      │
│  └──────────────────┘                                      │
└─────────────────────────────────────────────────────────────┘
```

### Target Architecture (After)

```
┌─────────────────────────────────────────────────────────────┐
│                    Workflow Executor                        │
│                                                             │
│  ┌──────────────────┐      ┌──────────────────────────┐   │
│  │ Runtime Mode     │      │ Execution Router         │   │
│  │ Detection        │─────▶│                          │   │
│  └──────────────────┘      │  ┌────────────────────┐  │   │
│                            │  │ Cursor Mode?       │  │   │
│                            │  └────────────────────┘  │   │
│                            │           │               │   │
│                            │    ┌──────┴──────┐       │   │
│                            │    │             │       │   │
│                            │  YES            NO       │   │
│                            │    │             │       │   │
│  ┌──────────────────┐      │    ▼             ▼       │   │
│  │ Cursor Executor  │      │ ┌──────────┐ ┌─────────┐│   │
│  │                  │      │ │ Cursor   │ │ Headless││   │
│  │ ┌──────────────┐ │      │ │ Executor │ │Executor ││   │
│  │ │ Skill        │ │      │ └──────────┘ └─────────┘│   │
│  │ │ Invoker      │ │      └──────────────────────────┘   │
│  │ └──────────────┘ │                                      │
│  │        │         │                                      │
│  │        ▼         │                                      │
│  │ ┌──────────────┐ │                                      │
│  │ │ Direct       │ │                                      │
│  │ │ Execution    │ │                                      │
│  │ │ Fallback     │ │                                      │
│  │ └──────────────┘ │                                      │
│  └──────────────────┘                                      │
└─────────────────────────────────────────────────────────────┘
```

## Component Changes

### Removed Components

1. **Background Agent API Client** (`background_agent_api.py`)
   - No longer needed - Background Agents removed
   - API calls to Background Agents eliminated

2. **Background Agent Configuration** (`background_agent_config.py`)
   - Config validation removed
   - Config generation removed
   - Empty config file kept for reference only

3. **Background Agent Generator** (`background_agent_generator.py`)
   - No longer generates Background Agent configs
   - Cleanup methods removed

4. **Background Agent Auto Executor** (`background_auto_executor.py`)
   - No longer needed - direct execution used instead

5. **Background Agent Wrapper** (`background_wrapper.py`)
   - No longer wraps Background Agent execution
   - Worktree/progress features may be reused elsewhere

6. **Background Agent Implementation Classes**
   - `BackgroundContextAgent`
   - `BackgroundDocsAgent`
   - `BackgroundOpsAgent`
   - `BackgroundQualityAgent`
   - `BackgroundTestingAgent`

### Modified Components

1. **WorkflowExecutor**
   - Remove Background Agent Generator initialization
   - Remove Background Agent cleanup calls
   - Remove Background Agent imports

2. **CursorWorkflowExecutor**
   - Remove Background Agent API dependency
   - Use direct execution/Skills only
   - Remove Background Agent routing

3. **SkillInvoker**
   - Remove Background Agent API calls
   - Use direct execution fallback only
   - Remove Background Agent-specific agent classes

4. **CLI Commands**
   - Remove Background Agent status checks
   - Remove Background Agent configuration commands
   - Remove Background Agent warnings/messages

5. **Init Project**
   - Remove Background Agent config generation
   - Keep empty background-agents.yaml for reference

6. **Health Checker**
   - Remove Background Agent config validation
   - Remove Background Agent health checks

## Data Flow Changes

### Before: Workflow Execution with Background Agents

```
Workflow Step
    ↓
CursorWorkflowExecutor
    ↓
SkillInvoker
    ↓
Background Agent API
    ↓
Background Agent (separate process)
    ↓
Results via file/API
```

### After: Workflow Execution (Direct/Skills Only)

```
Workflow Step
    ↓
CursorWorkflowExecutor
    ↓
SkillInvoker
    ↓
Direct Execution Fallback
    ↓
Results directly
```

## Integration Points

### Removed Integrations

1. **Background Agent API Integration**
   - No API calls to Background Agents
   - No Background Agent triggering

2. **Background Agent Config Integration**
   - No config generation
   - No config validation
   - No config cleanup

### Preserved Integrations

1. **Cursor Skills Integration**
   - Skills continue to work (foreground agents)
   - Skill invoker continues to work
   - Direct execution fallback for Skills

2. **Worktree Management**
   - Worktree manager still used for isolation
   - Not Background Agent specific

3. **Progress Reporting**
   - Progress reporting still used
   - Not Background Agent specific

4. **Artifact Structures**
   - Artifact classes preserved (data structures)
   - Can be produced by Skills or direct execution

## Migration Strategy

### Phase 1: Remove Implementation (Stories 1-2)
- Delete Background Agent implementation files
- Update executor to remove Background Agent routing

### Phase 2: Update Dependencies (Stories 3-7, 10)
- Remove Background Agent imports
- Update dependent code
- Update module exports

### Phase 3: Cleanup (Stories 8-9)
- Remove Background Agent tests
- Update documentation

## Risk Mitigation

### Risk 1: Breaking Existing Workflows
**Mitigation:** Keep artifact structures unchanged, workflows will use direct execution

### Risk 2: Missing Dependencies
**Mitigation:** Systematic removal following dependency graph, comprehensive testing

### Risk 3: Documentation Gaps
**Mitigation:** Update all documentation, add migration notes if needed

## Performance Considerations

### Benefits
- Reduced code complexity
- Faster execution (no Background Agent API overhead)
- Simpler architecture

### No Performance Impact
- Direct execution is already used as fallback
- Skills work the same way
- No user-visible performance changes expected

## Security Considerations

### Reduced Attack Surface
- Fewer components = fewer attack vectors
- No Background Agent API endpoints to secure

### No Security Impact
- Direct execution uses same security model
- Skills use same security model
- No security degradation
