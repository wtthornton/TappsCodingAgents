# Project Profiling System Guide

**Version:** 1.0.0  
**Last Updated:** December 2025

## Overview

The Project Profiling System automatically detects project characteristics (deployment type, tenancy model, user scale, compliance requirements, security level) to provide context-aware expert guidance. This system enables experts to tailor their advice based on your project's specific context.

## Features

- **Automatic Detection**: Analyzes your codebase to detect project characteristics
- **Context-Aware Expert Advice**: Experts receive project context and tailor recommendations accordingly
- **Confidence-Based Filtering**: Only high-confidence detections (≥0.7) are used in expert prompts
- **Profile Templates**: Match your project to common templates (local-development, saas-application, enterprise-internal, startup-mvp)
- **YAML Persistence**: Profiles are saved and cached for performance

## How It Works

### Detection Flow

```
Codebase Analysis
    ↓
ProjectDetector Methods
    ↓
ProjectProfileDetector
    ↓
ProjectProfile (with confidence scores)
    ↓
Expert Consultation (context-aware)
```

### Detection Methods

1. **Deployment Type** (`detect_deployment_type`)
   - Detects: `local`, `cloud`, or `enterprise`
   - Indicators: Docker, Kubernetes, Helm, Terraform, serverless configs
   - Enterprise: Kubernetes + Helm + compliance/security files

2. **Compliance Requirements** (`detect_compliance_requirements`)
   - Detects: GDPR, HIPAA, PCI, SOC2, ISO27001
   - Indicators: Compliance files, directories, documentation

3. **Security Level** (`detect_security_level`)
   - Detects: `basic`, `standard`, `high`, `critical`
   - Indicators: Security files, security directories, security tools

4. **Tenancy Model** (`detect_tenancy`) - Phase 3
   - Detects: `single-tenant` or `multi-tenant`
   - Indicators: Code patterns (tenant_id, tenantId, tenant-id, etc.)
   - Confidence: 0.6-0.8 for multi-tenant, 0.7 for single-tenant

5. **User Scale** (`detect_user_scale`) - Phase 3
   - Detects: `single-user`, `small-team`, `department`, `enterprise`
   - Indicators: Infrastructure patterns (load balancers, OAuth/SAML, Redis, Kubernetes)
   - Confidence: 0.5-0.8 based on indicators

## Profile Structure

### ProjectProfile Dataclass

```python
@dataclass
class ProjectProfile:
    deployment_type: Optional[str] = None
    deployment_type_confidence: float = 0.0
    deployment_type_indicators: List[str] = field(default_factory=list)
    
    tenancy: Optional[str] = None
    tenancy_confidence: float = 0.0
    tenancy_indicators: List[str] = field(default_factory=list)
    
    user_scale: Optional[str] = None
    user_scale_confidence: float = 0.0
    user_scale_indicators: List[str] = field(default_factory=list)
    
    compliance_requirements: List[ComplianceRequirement] = field(default_factory=list)
    
    security_level: Optional[str] = None
    security_level_confidence: float = 0.0
    security_level_indicators: List[str] = field(default_factory=list)
    
    detected_at: Optional[str] = None  # ISO timestamp
```

### YAML Storage Format

Profiles are stored in `.tapps-agents/project_profile.yaml`:

```yaml
deployment_type: cloud
deployment_type_confidence: 0.9
deployment_type_indicators:
  - has_dockerfile
  - has_docker_compose
  - has_kubernetes

tenancy: multi-tenant
tenancy_confidence: 0.8
tenancy_indicators:
  - tenant_pattern_in_user_service.py
  - tenant_pattern_in_auth.py

user_scale: enterprise
user_scale_confidence: 0.75
user_scale_indicators:
  - has_load_balancer
  - has_oauth
  - has_kubernetes

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
  - has_dependabot

detected_at: "2025-12-15T10:30:00Z"
```

## Profile Templates

The system includes 4 pre-defined templates:

### 1. local-development
- **Deployment**: local
- **Tenancy**: single-tenant
- **User Scale**: small-team
- **Security**: basic

### 2. saas-application
- **Deployment**: cloud
- **Tenancy**: multi-tenant
- **User Scale**: enterprise
- **Security**: high

### 3. enterprise-internal
- **Deployment**: enterprise
- **Tenancy**: single-tenant
- **User Scale**: department
- **Security**: high

### 4. startup-mvp
- **Deployment**: cloud
- **Tenancy**: single-tenant
- **User Scale**: small-team
- **Security**: standard

## Usage

### Automatic Detection

Profiles are automatically detected when experts are consulted:

```python
from tapps_agents.experts.expert_registry import ExpertRegistry

registry = ExpertRegistry(load_builtin=True)
# Profile is automatically loaded and used
result = await registry.consult(
    query="How should I secure my API?",
    domain="security"
)
```

### Manual Detection

You can manually detect and save a profile:

```python
from tapps_agents.core.project_profile import ProjectProfileDetector, save_project_profile

detector = ProjectProfileDetector(project_root=Path.cwd())
profile = detector.detect()
save_project_profile(profile, project_root=Path.cwd())
```

### Template Matching

Match your profile to a template:

```python
from tapps_agents.core.project_profile import match_template, load_project_profile

profile = load_project_profile()
template = match_template(profile, min_confidence=0.7)
if template:
    print(f"Project matches template: {template}")
```

## Expert Integration

### How Experts Use Profiles

When an expert is consulted, the project profile is automatically included in the consultation prompt if:

1. A profile exists (saved in `.tapps-agents/project_profile.yaml`)
2. Profile values have high confidence (≥0.7)

### Example Expert Prompt

```
You are a security domain expert.

Domain Context:
[Retrieved knowledge base context]

Project Context:
- Deployment: cloud (confidence: 90%)
- Compliance Requirements: GDPR
- Security Level: high (confidence: 80%)

Question: How should I secure my cloud deployment?

Provide a clear, accurate answer based on your domain expertise. 
Tailor your advice to the project's characteristics if relevant.
```

### Confidence Calculation

Project context relevance is included in confidence calculation (10% weight):

```python
confidence = (
    max_confidence * 0.35 +           # Maximum expert confidence (35%)
    agreement_level * 0.25 +          # Expert agreement (25%)
    rag_quality * 0.2 +                # Knowledge base match quality (20%)
    domain_relevance * 0.1 +           # Domain relevance score (10%)
    project_context_relevance * 0.1    # Project context relevance (10%)
)
```

## Detection Details

### Deployment Type Detection

**Local:**
- No cloud infrastructure indicators
- Default if no indicators found

**Cloud:**
- Dockerfile or docker-compose.yml
- Serverless configs (serverless.yml)
- Terraform files
- Confidence: 0.7-0.9

**Enterprise:**
- Kubernetes (k8s/) or Helm charts
- Compliance files (HIPAA.md, GDPR.md, SOC2.md)
- Security files
- Confidence: 0.95

### Tenancy Detection

**Multi-Tenant:**
- Code patterns: `tenant_id`, `tenantId`, `tenant-id`, `tenant_uuid`, `tenant_context`, `multi_tenant`
- >3 files with patterns → confidence 0.8
- 1-2 files with patterns → confidence 0.6 (suggest)

**Single-Tenant:**
- No tenant patterns found
- Confidence: 0.7 (conservative default)

### User Scale Detection

**Enterprise:**
- Load balancers (nginx.conf, haproxy.cfg, traefik.yml)
- OAuth/SAML/LDAP configs
- Kubernetes/Helm
- Confidence: 0.6-0.8

**Department:**
- Redis/Memcached configs
- Message queues (RabbitMQ, Kafka, SQS)
- Confidence: 0.6-0.8

**Small-Team:**
- Docker/Docker Compose
- Database configs
- Default if no indicators
- Confidence: 0.5-0.6

### Compliance Detection

**Supported Standards:**
- GDPR (General Data Protection Regulation)
- HIPAA (Health Insurance Portability)
- PCI (Payment Card Industry)
- SOC2 (Service Organization Control)
- ISO27001 (Information Security)

**Detection:**
- File names containing compliance keywords
- Compliance directory with relevant files
- Documentation mentioning compliance standards

### Security Level Detection

**High:**
- 3+ security files/tools
- Examples: .security, security.md, .bandit, .snyk, dependabot.yml
- Confidence: 0.8

**Standard:**
- 2 security files
- Confidence: 0.7

**Basic:**
- 1 security file
- Confidence: 0.6

## Configuration

### Profile Storage Location

Profiles are stored in `.tapps-agents/project_profile.yaml` in your project root.

### Manual Override

You can manually edit the profile YAML file to override detections:

```yaml
# .tapps-agents/project_profile.yaml
deployment_type: enterprise  # Override detection
deployment_type_confidence: 1.0
```

### Disabling Profile Usage

To disable profile usage in expert consultations, simply delete or rename the profile file:

```bash
mv .tapps-agents/project_profile.yaml .tapps-agents/project_profile.yaml.bak
```

## Best Practices

1. **Review Detected Profile**: After first detection, review the profile to ensure accuracy
2. **Manual Override When Needed**: If detection is incorrect, manually edit the YAML file
3. **High Confidence Only**: Only values with confidence ≥0.7 are used in expert prompts
4. **Template Matching**: Use template matching to validate your profile matches expected patterns
5. **Regular Updates**: Re-detect profile when project characteristics change significantly

## Troubleshooting

### Profile Not Detected

**Issue**: Profile detection returns None or low confidence values.

**Solutions:**
- Ensure project has clear indicators (Docker files, compliance docs, etc.)
- Check that files are in expected locations
- Review detection indicators in profile YAML

### Incorrect Detection

**Issue**: Profile detects wrong deployment type or tenancy.

**Solutions:**
- Manually edit `.tapps-agents/project_profile.yaml`
- Add more indicators to help detection (e.g., add compliance files)
- Use template matching to validate

### Expert Not Using Profile

**Issue**: Expert advice doesn't seem to use project context.

**Solutions:**
- Check profile confidence scores (must be ≥0.7)
- Verify profile file exists and is valid YAML
- Check expert prompt includes "Project Context" section

## API Reference

### ProjectProfileDetector

```python
class ProjectProfileDetector:
    def __init__(self, project_root: Optional[Path] = None)
    def detect(self) -> ProjectProfile
```

### Functions

```python
def save_project_profile(
    profile: ProjectProfile, 
    project_root: Optional[Path] = None
) -> Path

def load_project_profile(
    project_root: Optional[Path] = None
) -> Optional[ProjectProfile]

def match_template(
    profile: ProjectProfile, 
    min_confidence: float = 0.7
) -> Optional[str]
```

## Examples

### Example 1: Cloud SaaS Application

```python
from tapps_agents.core.project_profile import ProjectProfileDetector, save_project_profile

detector = ProjectProfileDetector()
profile = detector.detect()

# Profile will detect:
# - deployment_type: "cloud" (Dockerfile present)
# - tenancy: "multi-tenant" (tenant_id patterns in code)
# - user_scale: "enterprise" (OAuth configs, Kubernetes)
# - security_level: "high" (multiple security files)

save_project_profile(profile)
```

### Example 2: Local Development Project

```python
detector = ProjectProfileDetector()
profile = detector.detect()

# Profile will detect:
# - deployment_type: "local" (no cloud indicators)
# - tenancy: "single-tenant" (no tenant patterns)
# - user_scale: "small-team" (default)
# - security_level: "basic" (minimal security files)

template = match_template(profile)
# Returns: "local-development"
```

### Example 3: Enterprise Internal Tool

```python
detector = ProjectProfileDetector()
profile = detector.detect()

# Profile will detect:
# - deployment_type: "enterprise" (Kubernetes + compliance)
# - tenancy: "single-tenant" (no tenant patterns)
# - user_scale: "department" (Redis, message queues)
# - security_level: "high" (multiple security tools)

template = match_template(profile)
# Returns: "enterprise-internal"
```

## Related Documentation

- [Expert Confidence Guide](EXPERT_CONFIDENCE_GUIDE.md) - How confidence is calculated
- [Configuration Guide](CONFIGURATION.md) - Project configuration
- [Architecture Overview](ARCHITECTURE.md) - System architecture
- [Built-in Experts Guide](BUILTIN_EXPERTS_GUIDE.md) - Available experts

---

**Last Updated**: December 2025  
**Version**: 1.0.0

