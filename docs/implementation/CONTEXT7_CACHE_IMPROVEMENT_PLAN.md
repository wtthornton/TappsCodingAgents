# Context7 KB Cache Improvement Plan

**Date:** January 2025  
**Status:** ✅ **IMPLEMENTED** - Dynamic on-demand caching with staleness detection  
**Priority:** High - Critical for agent effectiveness

---

## Executive Summary

TappsCodingAgents now uses a **fully dynamic, on-demand caching system** where documentation is fetched from Context7 API in real-time when needed, automatically cached, and refreshed when stale. The system **never ships Context7 data** - all documentation comes from Context7 API dynamically.

**Current State (After Implementation):**
- ✅ Context7 integration: Working
- ✅ API key: Configured and working
- ✅ **Dynamic on-demand caching**: Documentation fetched and cached automatically
- ✅ **Staleness detection**: Entries checked for staleness during lookup
- ✅ **Automatic refresh**: Stale entries refreshed in background
- ✅ **Init pre-loading**: Critical libraries pre-loaded during init (staleness-aware)

**Target State:**
- ✅ **Dynamic cache growth**: Cache builds automatically as agents request documentation
- ✅ **Staleness-aware lookup**: Fresh entries returned immediately, stale entries refreshed in background
- ✅ **All built-in expert libraries**: Pre-loaded during init (37 libraries)
- ✅ **Automatic refresh**: Stale entries automatically refreshed without blocking requests

---

## Current Cache Status

### Baseline Cache (Pre-Implementation)

**Note:** With dynamic caching, this baseline will grow automatically as agents request documentation. The cache is no longer static - it builds organically based on actual usage.

| Library | Topics Cached | Status |
|---------|---------------|--------|
| fastapi | routing, dependency-injection, async | ✅ |
| pydantic | validation, settings | ✅ |
| sqlalchemy | async | ✅ |
| pytest | async, fixtures | ✅ |
| aiosqlite | async | ✅ |
| homeassistant | websocket | ✅ (project-specific) |
| influxdb | write | ✅ (project-specific) |

**Baseline:** 7 libraries, 11 topic entries

**Growth Pattern:** Cache expands automatically as agents request documentation from Context7 API. Use `*context7-kb-validate-cache` to monitor current coverage.

---

## Required Libraries Analysis

**Note:** With dynamic caching, these libraries will be **automatically cached** when agents first request their documentation. No manual pre-population is required. The system fetches from Context7 API on-demand and caches automatically.

### 1. Core Framework Dependencies (AUTO-CACHED ON REQUEST)

**TappsCodingAgents uses these libraries - they will be cached automatically when requested:**

| Library | Purpose | Priority | Topics Needed | Caching Status |
|---------|---------|----------|---------------|----------------|
| **httpx** | HTTP client (core dependency) | 🔴 Critical | async, client, streaming, auth | 🔄 Auto-cached on request |
| **aiohttp** | Async HTTP (core dependency) | 🔴 Critical | client, server, websockets | 🔄 Auto-cached on request |
| **pyyaml** | YAML parsing (config files) | 🟡 High | load, dump, safe_load | 🔄 Auto-cached on request |
| **jinja2** | Template engine (reporting) | 🟡 High | templates, filters, macros | 🔄 Auto-cached on request |
| **rich** | CLI formatting (UX) | 🟡 High | console, progress, tables | 🔄 Auto-cached on request |
| **plotly** | Data visualization (reports) | 🟢 Medium | charts, graphs, dash | 🔄 Auto-cached on request |
| **psutil** | System monitoring | 🟢 Medium | cpu, memory, disk | 🔄 Auto-cached on request |

**Impact:** Agents will automatically cache these libraries when they need documentation, ensuring accurate guidance on HTTP clients, async patterns, and reporting features.

---

### 2. Code Analysis Tools (MISSING)

**Used by Reviewer Agent for quality scoring:**

| Library | Purpose | Priority | Topics Needed |
|---------|---------|----------|---------------|
| **radon** | Complexity analysis | 🔴 Critical | cyclomatic, maintainability |
| **bandit** | Security scanning | 🔴 Critical | security, vulnerabilities |
| **coverage** | Test coverage | 🔴 Critical | coverage, html, xml |
| **pylint** | Code linting | 🟡 High | linting, errors, warnings |

**Impact:** Reviewer agent cannot provide accurate code quality metrics without these libraries' documentation.

---

### 3. Testing Framework (PARTIALLY MISSING)

**Currently cached:** `pytest` (async, fixtures)  
**Missing critical pytest plugins:**

| Library | Purpose | Priority | Topics Needed |
|---------|---------|----------|---------------|
| **pytest-asyncio** | Async test support | 🔴 Critical | async, fixtures, markers |
| **pytest-mock** | Mocking support | 🔴 Critical | mocker, patch, spy |
| **pytest-cov** | Coverage integration | 🔴 Critical | coverage, reporting |
| **pytest-timeout** | Test timeouts | 🟢 Medium | timeout, markers |
| **pytest-xdist** | Parallel execution | 🟢 Medium | parallel, workers |
| **unittest** | Standard library testing | 🟡 High | TestCase, mock, assert |

**Impact:** Tester agent cannot provide comprehensive testing guidance without plugin documentation.

---

### 4. Code Quality Tools (MISSING)

**Used by Reviewer and Code Quality Expert:**

| Library | Purpose | Priority | Topics Needed |
|---------|---------|----------|---------------|
| **ruff** | Fast Python linter | 🔴 Critical | linting, formatting, rules |
| **mypy** | Static type checking | 🔴 Critical | type-checking, stubs, config |
| **black** | Code formatter | 🟡 High | formatting, line-length, preview |
| **typing** | Type hints (stdlib) | 🟡 High | Type, Optional, Union, Generic |
| **typing-extensions** | Extended type hints | 🟡 High | TypedDict, Literal, Protocol |

**Impact:** Code quality recommendations are incomplete without these tools' documentation.

---

### 5. Security Tools (MISSING)

**Used by Security Expert:**

| Library | Purpose | Priority | Topics Needed |
|---------|---------|----------|---------------|
| **cryptography** | Cryptographic operations | 🔴 Critical | encryption, hashing, keys |
| **pyjwt** | JWT handling | 🟡 High | encode, decode, verify |
| **bcrypt** | Password hashing | 🟡 High | hash, verify, rounds |
| **pip-audit** | Dependency vulnerabilities | 🟡 High | audit, vulnerabilities, fix |

**Impact:** Security expert cannot provide accurate security guidance.

---

### 6. Database Libraries (PARTIALLY MISSING)

**Currently cached:** `sqlalchemy` (async), `aiosqlite` (async)  
**Missing:**

| Library | Purpose | Priority | Topics Needed |
|---------|---------|----------|---------------|
| **pymongo** | MongoDB driver | 🟡 High | client, collections, queries |
| **psycopg2** | PostgreSQL driver | 🟡 High | connection, cursor, async |
| **redis** | Redis client | 🟡 High | client, pubsub, pipelines |
| **sqlite3** | SQLite (stdlib) | 🟢 Medium | connection, cursor, transactions |

**Impact:** Database expert guidance is incomplete.

---

### 7. Web Frameworks (PARTIALLY MISSING)

**Currently cached:** `fastapi` (routing, dependency-injection, async)  
**Missing:**

| Library | Purpose | Priority | Topics Needed |
|---------|---------|----------|---------------|
| **django** | Full-stack framework | 🟡 High | models, views, urls, middleware |
| **flask** | Micro framework | 🟡 High | routes, blueprints, extensions |
| **starlette** | ASGI framework | 🟡 High | routing, middleware, websockets |
| **requests** | HTTP library (sync) | 🟡 High | get, post, sessions, auth |

**Impact:** API Design expert cannot provide comprehensive framework comparisons.

---

### 8. Observability Tools (MISSING)

**Used by Observability Expert:**

| Library | Purpose | Priority | Topics Needed |
|---------|---------|----------|---------------|
| **prometheus-client** | Metrics collection | 🟡 High | metrics, counters, gauges |
| **opentelemetry** | Observability framework | 🟡 High | tracing, metrics, logs |
| **structlog** | Structured logging | 🟡 High | logging, processors, formatters |
| **sentry-sdk** | Error tracking | 🟡 High | capture, context, breadcrumbs |

**Impact:** Observability expert cannot provide accurate guidance.

---

### 9. Cloud Infrastructure (MISSING)

**Used by Cloud Infrastructure Expert:**

| Library | Purpose | Priority | Topics Needed |
|---------|---------|----------|---------------|
| **boto3** | AWS SDK | 🟡 High | s3, ec2, lambda, dynamodb |
| **kubernetes** | K8s client | 🟢 Medium | client, pods, services |
| **docker** | Docker SDK | 🟢 Medium | client, containers, images |

**Impact:** Cloud Infrastructure expert guidance is incomplete.

---

### 10. Data Processing (MISSING)

**Used by various experts:**

| Library | Purpose | Priority | Topics Needed |
|---------|---------|----------|---------------|
| **pandas** | Data analysis | 🟡 High | DataFrame, Series, operations |
| **numpy** | Numerical computing | 🟡 High | arrays, operations, broadcasting |
| **asyncio** | Async I/O (stdlib) | 🟡 High | coroutines, tasks, event-loop |
| **aiofiles** | Async file I/O | 🟢 Medium | open, read, write |

**Impact:** Data processing guidance is incomplete.

---

## Implementation Plan (COMPLETED)

### Dynamic On-Demand Caching Approach

**Key Principle:** TappsCodingAgents uses a **fully dynamic, on-demand caching system** where:
- Documentation is fetched from Context7 API **in real-time** when needed
- Entries are **automatically cached** after fetching
- **Staleness detection** happens during lookup
- **Stale entries are refreshed in background** without blocking requests
- **No static pre-population required** - cache builds dynamically
- **No Context7 data is shipped** with TappsCodingAgents

### Implementation Steps (COMPLETED)

#### Step 1: Staleness Check During Lookup ✅

**File:** `tapps_agents/context7/lookup.py`

**Implementation:**
- Modified `KBLookup.lookup()` to check if cached entries are stale before returning
- If stale, queues refresh task and returns stale entry immediately (non-blocking)
- Fresh entries returned immediately

#### Step 2: Background Refresh Processing ✅

**File:** `tapps_agents/context7/lookup.py`

**Implementation:**
- Added `_process_refresh_queue_async()` method to process refresh queue in background
- Processes highest priority tasks first
- Non-blocking - doesn't delay lookup responses

#### Step 3: Staleness-Aware Init Pre-Loading ✅

**File:** `tapps_agents/core/init_project.py`

**Implementation:**
- Enhanced `pre_populate_context7_cache()` to use staleness-aware lookup
- Pre-loads 37 built-in expert libraries during init
- Skips entries that are already cached and fresh
- Uses `cmd_docs()` which goes through lookup (now staleness-aware)

#### Step 4: Cache Validation Command ✅

**File:** `tapps_agents/context7/commands.py`

**Implementation:**
- Added `cmd_validate_cache()` method
- Validates cache coverage against required libraries
- Identifies missing libraries and stale entries
- Calculates cache coverage percentage
- Provides actionable suggestions

#### Step 5: Documentation Updates ✅

**Files Updated:**
- `docs/implementation/CONTEXT7_CACHE_IMPROVEMENT_PLAN.md` - Updated to reflect dynamic approach
- `docs/CONTEXT7_DYNAMIC_CACHE_GUIDE.md` - New comprehensive guide (see below)

---

## Execution Plan

### Implementation Status: ✅ COMPLETED

All implementation tasks have been completed:

1. ✅ **Staleness check during lookup** - Implemented in `tapps_agents/context7/lookup.py`
2. ✅ **Background refresh processing** - Implemented in `tapps_agents/context7/lookup.py`
3. ✅ **Staleness-aware init pre-loading** - Enhanced in `tapps_agents/core/init_project.py`
4. ✅ **Cache validation command** - Added to `tapps_agents/context7/commands.py`
5. ✅ **Documentation updates** - Completed in `docs/implementation/CONTEXT7_CACHE_IMPROVEMENT_PLAN.md` and `docs/CONTEXT7_DYNAMIC_CACHE_GUIDE.md`

### Dynamic Caching Approach

With the dynamic on-demand caching system, **no manual pre-population is required**. The system:

- ✅ **Automatically fetches** documentation when agents request it
- ✅ **Automatically caches** entries after fetching
- ✅ **Automatically refreshes** stale entries in background
- ✅ **Pre-loads critical libraries** during `tapps-agents init`

### Next Steps (Optional)

1. **Monitor cache growth**: Use `*context7-kb-validate-cache` to track coverage
2. **Test agent operations**: Agents will automatically populate cache as they work
3. **Validate cache entries**: Use validation command to check coverage
4. **Review cache metrics**: Monitor cache hit rates and staleness patterns

---

## Success Metrics

### Implementation Metrics

| Metric | Status | Notes |
|--------|--------|-------|
| **Dynamic Caching System** | ✅ **COMPLETE** | Fully implemented and operational |
| **Staleness Detection** | ✅ **COMPLETE** | Active during lookup |
| **Background Refresh** | ✅ **COMPLETE** | Non-blocking refresh processing |
| **Init Pre-Loading** | ✅ **COMPLETE** | Pre-loads 37 expert libraries |
| **Cache Validation** | ✅ **COMPLETE** | Command available for monitoring |

### Dynamic Growth Metrics

With the dynamic system, cache metrics will grow automatically:

| Metric | Current Baseline | Growth Pattern | Status |
|--------|------------------|----------------|--------|
| **Total Libraries Cached** | 7 | Grows as agents request docs | ✅ **DYNAMIC** |
| **Total Cache Entries** | 11 | Grows organically with usage | ✅ **DYNAMIC** |
| **Cache Hit Rate** | TBD | Improves as cache grows | ✅ **MONITORED** |
| **Critical Libraries** | 2/10 | Auto-cached on first request | ✅ **ON-DEMAND** |
| **Expert Libraries** | 37 pre-loaded | All cached during init | ✅ **PRE-LOADED** |

### Validation Criteria

✅ **System Complete When:**
- Dynamic caching system operational ✅
- Staleness detection active ✅
- Background refresh working ✅
- Init pre-loading functional ✅
- Cache validation available ✅

**Note:** With dynamic caching, libraries are cached automatically as agents request them. No manual pre-population phases are needed. Cache coverage will grow organically based on actual agent usage patterns.

---

## Risk Assessment

### Risks

1. **Context7 API Rate Limits**
   - **Mitigation:** Batch requests, add delays between requests
   - **Impact:** Low - can spread population over multiple sessions

2. **Cache Size Growth**
   - **Mitigation:** Monitor cache size, implement cleanup for stale entries
   - **Impact:** Low - cache is file-based, can be managed

3. **Library Name Resolution**
   - **Mitigation:** Test library name resolution before caching
   - **Impact:** Medium - some libraries may need manual ID resolution

4. **Topic Availability**
   - **Mitigation:** Fallback to general documentation if topic not available
   - **Impact:** Low - general docs still useful

---

## Maintenance Plan

### Ongoing Maintenance

1. **Automatic Cache Management**
   - ✅ Staleness detection automatically identifies stale entries
   - ✅ Background refresh automatically updates stale entries
   - ✅ No manual refresh required - system handles it automatically
   - Cache grows organically as agents request documentation

2. **Cache Monitoring**
   - Use `*context7-kb-validate-cache` to check coverage
   - Monitor cache hit rates via analytics
   - Track cache size growth over time
   - Identify missing libraries from validation reports

3. **Documentation Updates**
   - Library list maintained in `get_builtin_expert_libraries()`
   - New libraries automatically cached on first request
   - Staleness policies automatically applied
   - No manual documentation updates needed for cache entries

---

## Related Documentation

- **Context7 Integration:** `TappsCodingAgents/docs/CONTEXT7_API_KEY_MANAGEMENT.md`
- **Cache Architecture:** `TappsCodingAgents/implementation/UNIFIED_CACHE_ARCHITECTURE_PLAN.md`
- **Pre-population Script:** `TappsCodingAgents/scripts/prepopulate_context7_cache.py`
- **Built-in Experts:** `TappsCodingAgents/tapps_agents/core/init_project.py` (get_builtin_expert_libraries)

---

## Conclusion

TappsCodingAgents now uses a **fully dynamic, on-demand caching system** that automatically fetches and caches documentation from Context7 API as needed. The system includes:

- ✅ **Staleness detection** during lookup
- ✅ **Automatic background refresh** for stale entries
- ✅ **Init pre-loading** of critical libraries (37 expert libraries)
- ✅ **Cache validation** command for monitoring coverage
- ✅ **No static pre-population required** - cache builds dynamically
- ✅ **No Context7 data shipped** - all documentation comes from API

**Status:** ✅ **IMPLEMENTED** - Dynamic caching system is operational

**Expected Outcome:** Cache grows dynamically as agents request documentation, with automatic staleness detection and refresh ensuring data freshness without blocking requests.

**Related Documentation:** See `docs/CONTEXT7_DYNAMIC_CACHE_GUIDE.md` for complete guide to dynamic caching.

