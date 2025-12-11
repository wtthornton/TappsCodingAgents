# Project Profiling System - Implementation Plan

**Date:** December 2025  
**Status:** Planning  
**Version:** 1.0.0  
**Estimated Duration:** 2-3 weeks

---

## Executive Summary

This plan implements a project profiling system that automatically detects project characteristics (deployment type, tenancy, user scale, etc.) to provide context-aware expert guidance. The system extends the existing `ProjectDetector` pattern and integrates with the expert consultation system.

**Key Principles:**
- ✅ Reuse existing `ProjectDetector` patterns
- ✅ Auto-detect high-confidence characteristics (no user input)
- ✅ Minimal new components
- ✅ Progressive enhancement (detect → suggest → ask)
- ✅ Integrate with existing config system

---

## Current State Analysis

### What Exists
- ✅ `ProjectDetector` class with file-based detection patterns
- ✅ `ProjectConfig` model with Pydantic validation
- ✅ Expert consultation system with confidence calculation
- ✅ Configuration system (YAML-based)

### What's Missing
- ❌ Project profile model (deployment type, tenancy, user scale)
- ❌ Profile detection logic (beyond workflow selection)
- ❌ Profile storage and persistence
- ❌ Expert prompt integration (profile context)
- ❌ Confidence adjustment based on profile relevance

---

## Implementation Phases

### Phase 1: Core Profile Model & Detection (Week 1)

**Goal:** Create profile data model and basic auto-detection

#### 1.1 Profile Data Model

**File:** `tapps_agents/core/project_profile.py`

**Components:**
- `ProjectProfile` dataclass with:
  - `deployment_type`: Optional[str] (local, cloud, enterprise)
  - `tenancy`: Optional[str] (single-tenant, multi-tenant)
  - `user_scale`: Optional[str] (single-user, small-team, department, enterprise)
  - `compliance_requirements`: List[str] (GDPR, HIPAA, etc.)
  - `security_level`: Optional[str] (basic, standard, high, critical)
  - `detection_confidence`: Dict[str, float] (confidence per field)
  - `detection_indicators`: Dict[str, List[str]] (which indicators matched)

**Design:**
- All fields optional (progressive disclosure)
- Confidence scores for each detected value
- Track which indicators led to detection (for explainability)

#### 1.2 Extend ProjectDetector

**File:** `tapps_agents/workflow/detector.py` (modify)

**Add Methods:**
- `detect_deployment_type()` → Tuple[str, float]
  - Check for Dockerfile, docker-compose.yml → `local` or `cloud`
  - Check for k8s/, kubernetes/, serverless.yml → `cloud`
  - Check for terraform/, *.tf → `cloud`
  - Default: `local` (conservative)
  
- `detect_compliance_requirements()` → List[Tuple[str, float]]
  - Reuse existing `_has_compliance_files()` logic
  - Extract specific compliance from file names (GDPR, HIPAA, PCI, SOC2)
  - Return list of (compliance_name, confidence)
  
- `detect_security_level()` → Tuple[str, float]
  - Reuse existing `_has_security_files()` logic
  - Multiple security files → `high`
  - Single security file → `standard`
  - None → `basic`

**Pattern:** Follow existing indicator-based detection pattern

#### 1.3 Profile Detection Orchestrator

**File:** `tapps_agents/core/project_profile.py` (add)

**Component:**
- `ProjectProfileDetector` class
  - Wraps `ProjectDetector`
  - Calls detection methods
  - Aggregates results into `ProjectProfile`
  - Calculates confidence scores

**Design:**
- Simple wrapper, no complex logic
- Reuse existing detector methods
- Combine results into profile

#### 1.4 Profile Storage

**File:** `tapps_agents/core/project_profile.py` (add)

**Components:**
- `load_project_profile()` → Optional[ProjectProfile]
  - Load from `.tapps-agents/project-profile.yaml`
  - Return None if not found (not required)
  
- `save_project_profile(profile: ProjectProfile)`
  - Save to `.tapps-agents/project-profile.yaml`
  - Include confidence scores and indicators

**Design:**
- YAML format (consistent with existing config)
- Optional file (system works without it)
- Include metadata (detection timestamp, indicators)

**Success Criteria:**
- ✅ Profile model defined
- ✅ Auto-detect deployment_type, compliance, security_level
- ✅ Save/load profile from YAML
- ✅ Basic tests (3-5 unit tests)

---

### Phase 2: Expert Integration (Week 2)

**Goal:** Integrate profile into expert consultation system

#### 2.1 Profile Context in Expert Prompts

**File:** `tapps_agents/experts/base_expert.py` (modify)

**Changes:**
- `_build_consultation_prompt()` accepts optional `project_profile`
- Add profile context section to prompt:
  ```
  Project Context:
  - Deployment: {deployment_type} (confidence: {confidence})
  - Security Level: {security_level} (confidence: {confidence})
  - Compliance: {compliance_requirements}
  ```

**Design:**
- Only include high-confidence profile values (>= 0.7)
- Format clearly for LLM consumption
- Optional parameter (backward compatible)

#### 2.2 Profile Loading in Expert Registry

**File:** `tapps_agents/experts/expert_registry.py` (modify)

**Changes:**
- `consult()` method loads profile if available
- Passes profile to expert `run()` calls
- Profile automatically available to all experts

**Design:**
- Lazy loading (only load if profile file exists)
- Cache profile in registry (don't reload every call)
- Fail gracefully if profile missing

#### 2.3 Profile-Aware Confidence Adjustment

**File:** `tapps_agents/experts/confidence_calculator.py` (modify)

**Changes:**
- Add `project_context_relevance` factor (10% weight)
- Calculate based on how well advice matches profile
- Adjust existing weights:
  - Max confidence: 35% (down from 40%)
  - Agreement: 25% (down from 30%)
  - RAG quality: 20% (same)
  - Domain relevance: 10% (same)
  - **Project context: 10% (NEW)**

**Calculation:**
- If advice mentions enterprise patterns and profile is enterprise → +0.1
- If advice mentions local dev and profile is local → +0.1
- If advice conflicts with profile → -0.05
- Default: 0.0 (neutral)

**Design:**
- Simple keyword matching (don't over-engineer)
- Conservative scoring (small impact)
- Optional (works without profile)

**Success Criteria:**
- ✅ Profile included in expert prompts
- ✅ Profile automatically loaded in consultations
- ✅ Confidence calculation includes profile relevance
- ✅ Backward compatible (works without profile)
- ✅ Tests (3-5 integration tests)

---

### Phase 3: Enhanced Detection & Templates (Week 3 - Optional)

**Goal:** Add medium-confidence detection and profile templates

#### 3.1 Multi-Tenancy Detection

**File:** `tapps_agents/workflow/detector.py` (modify)

**Add Method:**
- `detect_tenancy()` → Tuple[str, float]
  - Grep for "tenant_id", "tenantId", "tenant-id" in code
  - Count matches:
    - >3 files → `multi-tenant` (confidence: 0.8)
    - 1-2 files → `multi-tenant` (confidence: 0.6, suggest)
    - 0 files → `single-tenant` (confidence: 0.7)

**Design:**
- Simple grep (don't parse AST)
- Conservative (prefer single-tenant)
- Medium confidence (ask user to confirm)

#### 3.2 User Scale Detection

**File:** `tapps_agents/workflow/detector.py` (modify)

**Add Method:**
- `detect_user_scale()` → Tuple[str, float]
  - Check for Redis/Memcached configs → `department`+ (confidence: 0.6)
  - Check for load balancer configs → `enterprise` (confidence: 0.7)
  - Check for OAuth/SAML configs → `enterprise` (confidence: 0.7)
  - Default: `small-team` (confidence: 0.5, suggest)

**Design:**
- File-based checks (config files, not code)
- Multiple indicators increase confidence
- Always suggest (never auto-apply)

#### 3.3 Profile Templates

**File:** `tapps_agents/core/project_profile.py` (add)

**Components:**
- `PROFILE_TEMPLATES` dict with common profiles:
  - `local-development`: local, single-tenant, small-team
  - `saas-application`: cloud, multi-tenant, enterprise
  - `enterprise-internal`: enterprise, single-tenant, department

- `match_template(profile: ProjectProfile)` → Optional[str]
  - Match detected profile to closest template
  - Return template name if match confidence > 0.7

**Design:**
- Simple matching (count matching fields)
- Templates as defaults (not enforced)
- User can override

**Success Criteria:**
- ✅ Tenancy detection working
- ✅ User scale detection working
- ✅ Template matching working
- ✅ Tests (2-3 tests per feature)

---

## File Structure

```
tapps_agents/
├── core/
│   └── project_profile.py          # NEW: Profile model, detector, storage
│
├── workflow/
│   └── detector.py                 # MODIFY: Add detection methods
│
└── experts/
    ├── base_expert.py               # MODIFY: Add profile to prompts
    ├── expert_registry.py           # MODIFY: Load and pass profile
    └── confidence_calculator.py     # MODIFY: Add profile relevance

.tapps-agents/
└── project-profile.yaml             # NEW: Profile storage (optional)

tests/
└── unit/
    ├── core/
    │   └── test_project_profile.py  # NEW: Profile tests
    └── workflow/
        └── test_detector_profile.py # NEW: Detection tests
```

---

## Implementation Details

### Profile YAML Format

```yaml
# .tapps-agents/project-profile.yaml

deployment_type: cloud
deployment_type_confidence: 0.9
deployment_type_indicators:
  - has_dockerfile
  - has_kubernetes

tenancy: multi-tenant
tenancy_confidence: 0.6
tenancy_indicators:
  - tenant_id_patterns_found: 5

user_scale: enterprise
user_scale_confidence: 0.7
user_scale_indicators:
  - has_redis_config
  - has_load_balancer

compliance_requirements:
  - name: GDPR
    confidence: 0.8
    indicators:
      - gdpr_file_found

security_level: high
security_level_confidence: 0.8
security_level_indicators:
  - multiple_security_files

detected_at: 2025-12-15T10:30:00Z
```

### Detection Method Pattern

```python
def detect_deployment_type(self) -> Tuple[str, float]:
    """Detect deployment type with confidence score."""
    indicators = {
        "cloud": [
            ("has_dockerfile", lambda p: (p / "Dockerfile").exists()),
            ("has_k8s", lambda p: (p / "k8s").exists()),
            ("has_serverless", lambda p: (p / "serverless.yml").exists()),
        ],
        "local": [
            ("no_infrastructure", lambda p: not self._has_cloud_indicators(p)),
        ]
    }
    
    # Score-based detection (reuse existing pattern)
    cloud_score = sum(0.3 for name, check in indicators["cloud"] if check(self.project_root))
    local_score = sum(0.3 for name, check in indicators["local"] if check(self.project_root))
    
    if cloud_score >= 0.6:
        return ("cloud", min(0.9, cloud_score))
    elif local_score >= 0.3:
        return ("local", min(0.8, local_score))
    else:
        return ("local", 0.5)  # Conservative default
```

### Expert Prompt Integration

```python
async def _build_consultation_prompt(
    self, 
    query: str, 
    context: str, 
    domain: str,
    project_profile: Optional[ProjectProfile] = None
) -> str:
    prompt = f"""You are a {domain} domain expert.
    
Domain Context:
{context}
"""
    
    # Add profile context if available and high confidence
    if project_profile:
        profile_context = self._format_profile_context(project_profile)
        if profile_context:
            prompt += f"\nProject Context:\n{profile_context}\n"
    
    prompt += f"""
Question: {query}

Provide advice tailored to this project's characteristics.
Answer:"""
    
    return prompt
```

---

## Testing Strategy

### Unit Tests

**File:** `tests/unit/core/test_project_profile.py`

**Test Cases:**
1. Profile model creation and validation
2. Profile save/load from YAML
3. Profile detection orchestrator
4. Template matching

### Integration Tests

**File:** `tests/unit/workflow/test_detector_profile.py`

**Test Cases:**
1. Deployment type detection (Dockerfile present)
2. Deployment type detection (no infrastructure)
3. Compliance detection (GDPR file)
4. Security level detection (multiple files)
5. Tenancy detection (tenant_id patterns)

### Expert Integration Tests

**File:** `tests/integration/test_expert_profile.py`

**Test Cases:**
1. Expert consultation with profile
2. Profile context in prompts
3. Confidence adjustment with profile
4. Backward compatibility (no profile)

---

## Success Metrics

### Phase 1 Complete When:
- ✅ Profile model defined and tested
- ✅ Auto-detect 3+ characteristics (deployment, compliance, security)
- ✅ Profile save/load working
- ✅ 5+ unit tests passing

### Phase 2 Complete When:
- ✅ Profile integrated into expert prompts
- ✅ Confidence calculation includes profile relevance
- ✅ Backward compatible (works without profile)
- ✅ 5+ integration tests passing

### Phase 3 Complete When (Optional):
- ✅ Tenancy detection working
- ✅ User scale detection working
- ✅ Template matching working
- ✅ 5+ tests passing

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Detection accuracy low | Medium | Conservative defaults, always allow override |
| Performance impact | Low | Lazy loading, cache profile |
| Breaking changes | High | All changes backward compatible |
| Over-engineering | Medium | Follow existing patterns, keep simple |

---

## Timeline

**Week 1:** Phase 1 (Core Profile Model & Detection)
- Day 1-2: Profile model and detection methods
- Day 3-4: Profile storage and orchestrator
- Day 5: Testing and refinement

**Week 2:** Phase 2 (Expert Integration)
- Day 1-2: Expert prompt integration
- Day 3-4: Confidence calculation updates
- Day 5: Testing and refinement

**Week 3:** Phase 3 (Enhanced Detection - Optional)
- Day 1-2: Tenancy and user scale detection
- Day 3-4: Template matching
- Day 5: Testing and documentation

---

## Next Steps

1. **Review and approve this plan**
2. **Create Phase 1 tasks** (Week 1)
3. **Set up test infrastructure** for profile tests
4. **Begin implementation** starting with profile model

---

## Appendix: Detection Indicators Reference

### Deployment Type Indicators

**Cloud:**
- `Dockerfile` exists
- `docker-compose.yml` exists
- `k8s/` or `kubernetes/` directory
- `serverless.yml` exists
- `terraform/` directory
- `*.tf` files

**Local:**
- No infrastructure files
- Only package files (requirements.txt, package.json)

### Compliance Indicators

**Files/Directories:**
- `compliance/` directory
- `hipaa`, `pci`, `gdpr`, `soc2`, `audit` in file names

### Security Level Indicators

**High:**
- Multiple security files (.security, security.md, SECURITY.md, .bandit, .safety)

**Standard:**
- Single security file

**Basic:**
- No security files

### Tenancy Indicators

**Multi-Tenant:**
- `tenant_id` in code (>3 files)
- `tenantId` in code
- `tenant-id` in code
- `tenants/` directory

### User Scale Indicators

**Enterprise:**
- Load balancer configs (nginx.conf, haproxy.cfg)
- OAuth/SAML configs
- Monitoring (prometheus.yml, grafana configs)

**Department:**
- Redis/Memcached configs
- Connection pooling configs
- Caching configs

**Small Team:**
- Basic auth only
- No infrastructure patterns

