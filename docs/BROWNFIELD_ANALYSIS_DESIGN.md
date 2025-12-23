# Brownfield Analysis Workflow - Design Summary

**Date**: January 2025  
**Status**: Design Complete - Ready for Implementation  
**Design Method**: Self-Designed using TappsCodingAgents Framework

## Overview

This document summarizes the comprehensive brownfield analysis workflow designed for TappsCodingAgents. The design was created using the framework's own analysis capabilities and patterns.

## What Was Designed

### New Command: `@analyst *analyze-brownfield`

A comprehensive 8-phase analysis workflow that provides complete assessment of existing codebases:

1. **Discovery & Profiling** - Project structure, services, tech stack
2. **Code Quality Analysis** - Quality scores, duplication, security
3. **Architecture Analysis** - Patterns, component relationships, coupling
4. **Codebase Structure** - Module organization, structural quality
5. **Technical Debt Assessment** - Categorization, prioritization, remediation
6. **Dependency & Integration** - Dependencies, vulnerabilities, integrations
7. **Test & Documentation** - Coverage gaps, quality assessment
8. **Modernization Roadmap** - Prioritized improvements, effort estimates

## Key Design Decisions

### 1. Orchestration Approach
- **Decision**: Create `BrownfieldAnalyzer` class that orchestrates existing agents
- **Rationale**: Leverages existing capabilities (reviewer, ops) while adding new analysis dimensions
- **Benefit**: Reuses proven code, maintains consistency

### 2. Phase-Based Architecture
- **Decision**: 8 distinct phases with clear dependencies
- **Rationale**: Allows selective execution, clear progress tracking, parallel execution where possible
- **Benefit**: Flexible, scalable, maintainable

### 3. New Analyzer Classes
- **Decision**: Create specialized analyzer classes for each new analysis dimension
- **Rationale**: Single responsibility, testable, extensible
- **Benefit**: Clean architecture, easy to extend

### 4. Multi-Format Output
- **Decision**: Generate JSON, Markdown, and HTML reports
- **Rationale**: Different use cases (automation, documentation, visualization)
- **Benefit**: Maximum utility for different stakeholders

## What Already Exists (Reused)

✅ **Project Profiling** - `ProjectProfileDetector`  
✅ **Service Discovery** - `ServiceDiscovery`  
✅ **Quality Analysis** - `reviewer analyze-project`  
✅ **Security Scanning** - `reviewer security-scan`, `ops audit-dependencies`  
✅ **Dependency Analysis** - `DependencyAnalyzer`  
✅ **Duplication Detection** - `reviewer duplication`

## What's New (To Be Built)

🆕 **ArchitectureAnalyzer** - Import graphs, pattern detection, coupling metrics  
🆕 **StructureAnalyzer** - Module organization, structure quality  
🆕 **TechnicalDebtAnalyzer** - Debt categorization and prioritization  
🆕 **TestCoverageAnalyzer** - Coverage gap analysis  
🆕 **DocumentationAnalyzer** - Documentation coverage analysis  
🆕 **ModernizationRoadmapGenerator** - Roadmap generation  
🆕 **BrownfieldAnalyzer** - Orchestration and report generation

## Implementation Files Created

### Specification
- `docs/implementation/BROWNFIELD_ANALYSIS_SPECIFICATION.md` - Complete technical specification

### Workflow
- `workflows/presets/brownfield-analysis.yaml` - Workflow YAML definition

### Summary
- `docs/BROWNFIELD_ANALYSIS_DESIGN.md` - This document

## Next Steps

### Immediate (Implementation Ready)
1. ✅ Specification complete
2. ✅ Workflow YAML created
3. ⏭️ Begin Phase 1 implementation (Core Infrastructure)

### Implementation Phases
1. **Week 1**: Core infrastructure (`BrownfieldAnalyzer`, command integration)
2. **Week 2**: Architecture and structure analysis
3. **Week 3**: Technical debt and test/doc analysis
4. **Week 4**: Modernization roadmap and reporting

## Usage Examples

### CLI Usage
```bash
# Full analysis
tapps-agents analyst analyze-brownfield

# Specific phases only
tapps-agents analyst analyze-brownfield --phases discovery,quality,architecture

# Custom output location
tapps-agents analyst analyze-brownfield --output-dir reports/my-analysis --format all
```

### Cursor Usage
```cursor
@analyst *analyze-brownfield
@analyst *analyze-brownfield --output-dir reports/
```

### Workflow Usage
```bash
tapps-agents workflow brownfield-analysis --auto
```

## Expected Outputs

### Reports Generated
- `reports/brownfield-analysis/analysis-report.json` - Machine-readable
- `reports/brownfield-analysis/analysis-report.md` - Human-readable
- `reports/brownfield-analysis/analysis-report.html` - Interactive dashboard

### Key Metrics
- Overall health score (0-100)
- Critical issues count
- High-priority debt items
- Modernization opportunities
- Effort estimates

## Success Criteria

✅ Comprehensive analysis of any brownfield project  
✅ Actionable, prioritized recommendations  
✅ Integration with existing TappsCodingAgents capabilities  
✅ Multiple output formats for different use cases  
✅ Efficient handling of large codebases  
✅ Clear prioritization of issues and improvements

## Design Validation

This design was created using TappsCodingAgents itself:
- ✅ Analyzed existing capabilities
- ✅ Identified gaps
- ✅ Designed solution using framework patterns
- ✅ Created reusable components
- ✅ Followed existing architecture patterns

## Related Documentation

- **Full Specification**: `docs/implementation/BROWNFIELD_ANALYSIS_SPECIFICATION.md`
- **Workflow Definition**: `workflows/presets/brownfield-analysis.yaml`
- **Command Reference**: `docs/TAPPS_AGENTS_COMMAND_REFERENCE.md` (to be updated)

---

**Status**: Design complete, ready for implementation review and approval.

