# Project Profiling System Guide

**Version:** 1.0.0  
**Last Updated:** December 2025

## Overview

The Project Profiling System automatically detects project characteristics (deployment type, tenancy model, user scale, compliance requirements, security level) to provide context-aware expert guidance.

The implementation lives in `tapps_agents/core/project_profile.py` and persists the detected profile to `.tapps-agents/project-profile.yaml`.

## What Gets Detected

The detector produces a `ProjectProfile` with confidence scores and evidence (indicators):

- **Deployment type**: `local` | `cloud` | `enterprise`
- **Tenancy**: `single-tenant` | `multi-tenant`
- **User scale**: `single-user` | `small-team` | `department` | `enterprise`
- **Compliance requirements**: GDPR, HIPAA, PCI, SOC2, ISO27001 (each with confidence + indicators)
- **Security level**: `basic` | `standard` | `high` | `critical`

When formatting context for expert prompts, only fields meeting a minimum confidence are included (default is 0.7).

## Storage

Profiles are stored at:

- `.tapps-agents/project-profile.yaml`

Example structure:

```yaml
deployment_type: cloud
deployment_type_confidence: 0.9
deployment_type_indicators:
  - has_dockerfile
  - has_docker_compose

tenancy: multi-tenant
tenancy_confidence: 0.8
tenancy_indicators:
  - tenant_pattern_in_user_service.py

user_scale: enterprise
user_scale_confidence: 0.75
user_scale_indicators:
  - has_load_balancer
  - has_oauth

compliance_requirements:
  - name: GDPR
    confidence: 0.9
    indicators:
      - gdpr_file_found

security_level: high
security_level_confidence: 0.8
security_level_indicators:
  - has_security
  - has_.bandit

detected_at: "2025-12-15T10:30:00Z"
```

## Usage

### Manual Detection

```python
from pathlib import Path
from tapps_agents.core.project_profile import ProjectProfileDetector, save_project_profile

detector = ProjectProfileDetector(project_root=Path.cwd())
profile = detector.detect_profile()
path = save_project_profile(profile, project_root=Path.cwd())
print(path)  # .tapps-agents/project-profile.yaml
```

### Loading an Existing Profile

```python
from tapps_agents.core.project_profile import load_project_profile

profile = load_project_profile()
if profile:
    print(profile.format_context(min_confidence=0.7))
```

## Expert Integration

Experts can incorporate project context by using `ProjectProfile.format_context()` output, which only includes high-confidence values.

## API Reference

### `ProjectProfileDetector`

- `ProjectProfileDetector(project_root: Optional[Path] = None)`
- `detect_profile() -> ProjectProfile`

### Functions

- `save_project_profile(profile: ProjectProfile, project_root: Optional[Path] = None) -> Path`
- `load_project_profile(project_root: Optional[Path] = None) -> Optional[ProjectProfile]`

## Notes

- The file name is **`project-profile.yaml`** (hyphenated), not `project_profile.yaml`.
- This module does **not** provide profile-template matching utilities; it only detects and persists the profile.
