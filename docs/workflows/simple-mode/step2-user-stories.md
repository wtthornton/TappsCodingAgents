# Step 2: User Stories - Doctor Cache Status Feature

## User Stories

### Story 1: Basic Cache Status in Doctor
**As a** developer using TappsCodingAgents  
**I want** to see basic Context7 cache status in the doctor command  
**So that** I can quickly verify cache setup without running separate health checks

**Acceptance Criteria:**
- Doctor reports if Context7 is enabled in config
- Doctor reports if cache directory is accessible
- Doctor reports cache entry count (populated or empty)
- Status appears in doctor findings with appropriate severity
- Remediation messages provided if issues found

**Story Points:** 3  
**Priority:** Medium

### Story 2: Doctor --full Flag
**As a** developer troubleshooting issues  
**I want** to run both doctor and health checks with one command  
**So that** I get comprehensive diagnostics in a single run

**Acceptance Criteria:**
- `tapps-agents doctor --full` runs both doctor and health checks
- Default `tapps-agents doctor` behavior unchanged (backward compatible)
- --full flag documented in help text
- Output clearly distinguishes doctor vs health check results

**Story Points:** 2  
**Priority:** Medium

### Story 3: Separation of Concerns
**As a** framework maintainer  
**I want** doctor to provide basic status while health checks provide detailed metrics  
**So that** each command has a clear, focused purpose

**Acceptance Criteria:**
- Doctor shows only: enabled/disabled, accessible, entry count
- Health check shows: hit rate, response time, staleness, health score
- No duplication of detailed metrics in doctor
- Clear documentation of what each command provides

**Story Points:** 1  
**Priority:** Low

## Implementation Order
1. Story 1 (Basic Cache Status) - Foundation
2. Story 2 (--full Flag) - Enhancement
3. Story 3 (Separation) - Already achieved by design
