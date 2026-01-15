# Crash Analysis Fixes - Implementation Plan

**Date:** January 16, 2026  
**Status:** In Progress  
**Related:** `CODEBASE_WIDE_CRASH_ANALYSIS_RECOMMENDATIONS.md`

## Overview

This document tracks the implementation of all 3 phases of crash analysis fixes across the entire tapps-agents codebase.

---

## Phase 1: Critical Fixes (Week 1)

**Priority:** 🔴 Critical  
**Target Completion:** 1-2 days  
**Status:** ✅ Complete

### Phase 1.1: Create Centralized Debug Logger ✅

**File:** `tapps_agents/core/debug_logger.py`  
**Status:** ✅ Complete  
**Description:** Centralized utility for debug logging with project root detection and non-blocking error handling

**Features:**
- Project root detection via `PathValidator`
- Non-blocking error handling
- Automatic directory creation
- Structured JSON logging

### Phase 1.2: Update All Debug Log Locations ✅

**Target Files (11 locations):**
1. ✅ `agents/reviewer/agent.py:733, 827` (2 instances) - Updated
2. ✅ `context7/backup_client.py:64, 242, 329, 710, 830` (5 instances) - Updated
3. ✅ `context7/agent_integration.py:50, 276` (2 instances) - Updated
4. ✅ `context7/lookup.py:271` (1 instance) - Updated
5. ✅ `continuous_bug_fix/bug_fix_coordinator.py:59` (1 instance) - Updated

**Status:** ✅ Complete (11/11 locations updated)

### Phase 1.3: Fix Artifact Helper Path Resolution ✅

**File:** `tapps_agents/workflow/artifact_helper.py:48`  
**Status:** ✅ Complete  
**Change:** Uses `PathValidator` to detect project root instead of `Path.cwd()`

### Phase 1.4: Fix Cache Manager Path Resolution ✅

**Files:**
- ✅ `tapps_agents/agents/reviewer/cache.py:71` - Updated
- ✅ `tapps_agents/context7/async_cache.py:660` - Updated

**Status:** ✅ Complete

### Phase 1.5: Fix State Manager Path Resolution ✅

**File:** `tapps_agents/workflow/durable_state.py:315, 584, 650` (3 instances)  
**Status:** ✅ Complete  
**Change:** All instances now use `PathValidator` for project root detection

---

## Phase 2: High Priority (Week 2-3)

**Priority:** 🟡 High  
**Target Completion:** 1-2 weeks  
**Status:** 🟡 In Progress (2/3 tasks complete)

### Phase 2.1: Standardize PathValidator Usage

**Scope:** Update all 234 `Path.cwd()` instances  
**Status:** ⏳ Pending  
**Note:** This is a large refactoring task. Critical path issues (debug logs, artifacts, cache, state) have been fixed. Remaining instances are lower priority.

### Phase 2.2: Add Progress Indicators

**Agents:**
- ✅ Reviewer (batch operations) - Progress updates every 5s for operations >10s
- ⏳ Tester - Pending
- ⏳ Enhancer - Pending
- ⏳ Implementer - Pending
- ⏳ Workflow commands - Pending

**Status:** 🟡 In Progress (1/5 complete)  
**Completed:** Reviewer batch processing now shows progress: "Reviewing files: X/Y (Z%) - Ns elapsed"

### Phase 2.3: Implement Connection Retry Logic ✅

**File:** `tapps_agents/core/retry_handler.py`  
**Status:** ✅ Complete  
**Features:**
- Retry decorator with exponential backoff
- Support for async and sync functions
- Configurable retry attempts and delays
- Automatic retry on connection errors, timeouts, and OS errors

---

## Phase 3: Medium Priority (Week 4+)

**Priority:** 🟢 Medium  
**Target Completion:** 2-3 weeks  
**Status:** ⏳ Not Started

### Phase 3.1: Add Timeout Handling

**Status:** ⏳ Pending

### Phase 3.2: Standardize Error Handling

**Status:** ⏳ Pending

### Phase 3.3: Update Documentation

**Status:** ⏳ Pending

---

## Progress Tracking

**Overall Progress:** 5% (Phase 1.1 complete)

**By Phase:**
- Phase 1: 20% (1/5 tasks complete)
- Phase 2: 0% (0/3 tasks started)
- Phase 3: 0% (0/3 tasks started)

**Next Steps:**
1. Complete Phase 1.2 (update all debug log locations)
2. Complete Phase 1.3-1.5 (fix path resolution in utilities)
3. Begin Phase 2.1 (standardize PathValidator usage)
