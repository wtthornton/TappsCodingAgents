# Step 3: Architecture Design - Doctor Cache Status Feature

## System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Doctor Command                        │
│  (tapps_agents/cli/commands/top_level.py)               │
│                                                          │
│  ┌──────────────────┐      ┌──────────────────────┐  │
│  │ handle_doctor()  │──────│ collect_doctor_report│  │
│  │                  │      │ (core/doctor.py)     │  │
│  │ --full flag      │      │                      │  │
│  └──────────────────┘      └──────────────────────┘  │
│         │                            │                 │
│         │                            │                 │
│         └────────────┬────────────────┘                │
│                      │                                 │
│         ┌────────────▼────────────┐                    │
│         │  Health Check System    │                    │
│         │  (health/checks/)       │                    │
│         └────────────────────────┘                    │
└─────────────────────────────────────────────────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
    ┌────▼────┐  ┌───▼────┐  ┌───▼────┐
    │ Context7│  │ Cache  │  │Analytics│
    │ Config  │  │Structure│  │         │
    └─────────┘  └─────────┘  └─────────┘
```

## Design Decisions

### 1. Cache Status Helper Function
**Location:** `tapps_agents/core/doctor.py`  
**Purpose:** Encapsulate cache status checks logic  
**Signature:**
```python
def _check_context7_cache_status(
    config: ProjectConfig,
    project_root: Path
) -> DoctorFinding
```

**Logic:**
1. Check if Context7 enabled in config
2. If enabled, check cache directory accessibility
3. If accessible, get entry count from analytics
4. Return appropriate DoctorFinding

### 2. Integration Point
**Location:** `collect_doctor_report()` in `doctor.py`  
**Position:** After config file check, before return statement  
**Rationale:** Follows existing pattern, provides cache status in standard doctor output

### 3. --full Flag Implementation
**Location:** `handle_doctor_command()` in `top_level.py`  
**Logic:**
- Check for `--full` flag
- If set, run health checks after doctor checks
- Combine results in output
- Maintain separate result structures

### 4. Error Handling Strategy
- **Context7 not configured:** Warn (not error) - optional feature
- **Cache directory missing:** Warn with remediation
- **Import errors:** Graceful degradation, skip cache checks
- **Permission errors:** Warn with remediation

## Data Flow

```
User runs: tapps-agents doctor [--full]
    │
    ├─> Parser adds --full flag
    │
    ├─> handle_doctor_command()
    │   │
    │   ├─> collect_doctor_report()
    │   │   │
    │   │   ├─> Check Python version
    │   │   ├─> Check tools
    │   │   ├─> Check MCP servers
    │   │   ├─> Check Cursor integration
    │   │   ├─> Check config file
    │   │   └─> _check_context7_cache_status() ← NEW
    │   │
    │   └─> If --full:
    │       └─> Run health checks
    │           └─> Context7CacheHealthCheck (detailed metrics)
    │
    └─> Format and output results
```

## Component Interactions

### Doctor Module
- **Imports:** Context7 components (optional, with try/except)
- **Dependencies:** `context7.analytics`, `context7.cache_structure`
- **Output:** DoctorFinding with cache status

### CLI Handler
- **Imports:** Health check system
- **Dependencies:** `health.checks.context7_cache`, `health.orchestrator`
- **Output:** Combined doctor + health results

## Performance Considerations

- **Lazy Loading:** Only import Context7 if enabled
- **Fast Path:** Basic checks only (no detailed metrics)
- **Caching:** Reuse existing cache structure instances
- **Timeout:** Cache checks should complete in <500ms

## Security Considerations

- **Path Validation:** Ensure cache path is within project root
- **Permission Checks:** Test write access safely (create/delete test file)
- **Error Messages:** Don't expose sensitive paths in errors
