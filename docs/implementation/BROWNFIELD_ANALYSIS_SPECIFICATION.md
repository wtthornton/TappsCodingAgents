# Brownfield Analysis Workflow - Complete Specification

**Date**: January 2025  
**Status**: Design Specification  
**Author**: TappsCodingAgents Framework (Self-Designed)

## Executive Summary

This specification defines a comprehensive brownfield analysis workflow for TappsCodingAgents that orchestrates existing analysis capabilities and adds missing dimensions to provide a complete assessment of existing codebases.

## Problem Statement

TappsCodingAgents currently has:
- ✅ Code quality analysis (`reviewer analyze-project`)
- ✅ Dependency security scanning (`ops audit-dependencies`)
- ✅ Project profiling (automatic detection)
- ✅ Service discovery (`ServiceDiscovery`)

**Missing for comprehensive brownfield analysis:**
- ❌ Architecture pattern analysis
- ❌ Codebase structure assessment
- ❌ Technical debt categorization
- ❌ Test coverage gap analysis
- ❌ Documentation coverage analysis
- ❌ Integration point mapping
- ❌ Modernization roadmap generation
- ❌ Unified brownfield analysis workflow

## Solution: `@analyst *analyze-brownfield` Command

### Command Syntax

**CLI:**
```bash
tapps-agents analyst analyze-brownfield [--project-root <path>] [--output-dir <dir>] [--format json|markdown|html|all] [--phases <phases>] [--skip-phases <phases>]
```

**Cursor:**
```cursor
@analyst *analyze-brownfield [--project-root <path>] [--output-dir <dir>]
```

### Parameters

- `--project-root`: Project root directory (default: current directory)
- `--output-dir`: Output directory for reports (default: `reports/brownfield-analysis/`)
- `--format`: Output format - `json`, `markdown`, `html`, or `all` (default: `all`)
- `--phases`: Comma-separated list of phases to run (default: all)
- `--skip-phases`: Comma-separated list of phases to skip

### Analysis Phases

The brownfield analysis workflow consists of 8 phases:

#### Phase 1: Discovery & Profiling
**Purpose**: Understand project structure and characteristics

**Actions**:
1. Run project profiling (`ProjectProfileDetector`)
2. Discover services (`ServiceDiscovery`)
3. Detect tech stack (`LanguageDetector`, dependency analysis)
4. Identify project type (greenfield/brownfield/hybrid)
5. Map file structure and organization

**Outputs**:
- Project profile (`.tapps-agents/project-profile.yaml`)
- Service inventory
- Tech stack summary
- File structure map

**Orchestrates**:
- `ProjectProfileDetector.detect_profile()`
- `ServiceDiscovery.discover_services()`
- `LanguageDetector.detect_languages()`

#### Phase 2: Code Quality Analysis
**Purpose**: Assess code quality across the project

**Actions**:
1. Run `reviewer analyze-project` for quality scores
2. Run `reviewer duplication` for code duplication
3. Run `reviewer security-scan` for security issues
4. Aggregate quality metrics by service/module

**Outputs**:
- Quality scores (complexity, security, maintainability, test coverage, performance)
- Duplication report
- Security vulnerabilities
- Quality trends by service

**Orchestrates**:
- `reviewer analyze-project`
- `reviewer duplication`
- `reviewer security-scan`

#### Phase 3: Architecture Analysis
**Purpose**: Understand existing architecture patterns and design decisions

**Actions**:
1. Analyze import/dependency patterns
2. Identify architectural patterns (MVC, microservices, monolith, etc.)
3. Map component relationships
4. Detect coupling/cohesion issues
5. Identify architectural technical debt

**Outputs**:
- Architecture diagram (text/markdown)
- Pattern inventory
- Component dependency graph
- Architectural debt assessment

**New Capabilities**:
- Import graph analysis
- Pattern detection (factory, singleton, repository, etc.)
- Coupling metrics
- Architecture smell detection

#### Phase 4: Codebase Structure Analysis
**Purpose**: Assess code organization and structure quality

**Actions**:
1. Analyze module organization
2. Calculate coupling/cohesion metrics
3. Assess file/directory structure
4. Identify structural issues (circular dependencies, deep nesting, etc.)

**Outputs**:
- Structure quality metrics
- Module organization report
- Coupling/cohesion scores
- Structural recommendations

**New Capabilities**:
- Module dependency graph
- Coupling analysis
- Cohesion metrics
- Structure quality scoring

#### Phase 5: Technical Debt Assessment
**Purpose**: Categorize and prioritize technical debt

**Actions**:
1. Aggregate issues from all phases
2. Categorize debt (code quality, architecture, dependencies, tests, docs)
3. Prioritize by impact and effort
4. Generate remediation recommendations

**Outputs**:
- Technical debt inventory
- Debt categorization
- Prioritized debt list
- Remediation roadmap

**New Capabilities**:
- Debt categorization engine
- Impact-effort matrix
- Debt prioritization algorithm

#### Phase 6: Dependency & Integration Analysis
**Purpose**: Map dependencies and integration points

**Actions**:
1. Run `ops audit-dependencies` for security
2. Analyze dependency tree (`DependencyAnalyzer`)
3. Map external integrations (APIs, databases, services)
4. Identify outdated dependencies
5. Assess dependency health

**Outputs**:
- Dependency tree
- Security vulnerabilities
- Outdated packages
- Integration point map
- Dependency health score

**Orchestrates**:
- `ops audit-dependencies`
- `DependencyAnalyzer.get_dependency_tree()`
- `DependencyAnalyzer.check_outdated()`

#### Phase 7: Test & Documentation Analysis
**Purpose**: Assess test coverage and documentation completeness

**Actions**:
1. Analyze test coverage (identify gaps)
2. Assess test quality
3. Analyze documentation coverage
4. Identify undocumented areas
5. Assess documentation quality

**Outputs**:
- Test coverage report
- Test gap analysis
- Documentation coverage report
- Documentation gap analysis

**New Capabilities**:
- Test coverage gap detection
- Documentation coverage analysis
- Quality assessment for tests/docs

#### Phase 8: Modernization Roadmap
**Purpose**: Generate actionable modernization recommendations

**Actions**:
1. Synthesize findings from all phases
2. Generate modernization opportunities
3. Prioritize improvements
4. Create implementation roadmap
5. Estimate effort for improvements

**Outputs**:
- Modernization roadmap
- Prioritized improvement plan
- Effort estimates
- Risk assessment
- Implementation timeline

**New Capabilities**:
- Roadmap generation
- Improvement prioritization
- Effort estimation

## Implementation Architecture

### New Components

#### 1. `BrownfieldAnalyzer` Class
**Location**: `tapps_agents/agents/analyst/brownfield_analyzer.py`

**Responsibilities**:
- Orchestrate all analysis phases
- Aggregate results from multiple agents
- Generate comprehensive reports
- Manage phase execution and dependencies

**Key Methods**:
```python
class BrownfieldAnalyzer:
    async def analyze(self, project_root: Path, phases: list[str] | None = None) -> dict[str, Any]
    async def run_phase(self, phase: str, project_root: Path) -> dict[str, Any]
    async def generate_report(self, results: dict[str, Any], format: str) -> dict[str, Any]
```

#### 2. `ArchitectureAnalyzer` Class
**Location**: `tapps_agents/agents/analyst/architecture_analyzer.py`

**Responsibilities**:
- Analyze import/dependency patterns
- Detect architectural patterns
- Map component relationships
- Calculate coupling/cohesion metrics

**Key Methods**:
```python
class ArchitectureAnalyzer:
    def analyze_imports(self, project_root: Path) -> dict[str, Any]
    def detect_patterns(self, codebase: dict[str, Any]) -> list[dict[str, Any]]
    def map_components(self, project_root: Path) -> dict[str, Any]
    def calculate_coupling(self, component_graph: dict[str, Any]) -> dict[str, Any]
```

#### 3. `StructureAnalyzer` Class
**Location**: `tapps_agents/agents/analyst/structure_analyzer.py`

**Responsibilities**:
- Analyze module organization
- Calculate structure quality metrics
- Detect structural issues
- Assess file/directory organization

**Key Methods**:
```python
class StructureAnalyzer:
    def analyze_structure(self, project_root: Path) -> dict[str, Any]
    def calculate_metrics(self, structure: dict[str, Any]) -> dict[str, Any]
    def detect_issues(self, structure: dict[str, Any]) -> list[dict[str, Any]]
```

#### 4. `TechnicalDebtAnalyzer` Class
**Location**: `tapps_agents/agents/analyst/technical_debt_analyzer.py`

**Responsibilities**:
- Aggregate issues from all phases
- Categorize technical debt
- Prioritize debt items
- Generate remediation recommendations

**Key Methods**:
```python
class TechnicalDebtAnalyzer:
    def categorize_debt(self, issues: list[dict[str, Any]]) -> dict[str, Any]
    def prioritize_debt(self, debt_items: list[dict[str, Any]]) -> list[dict[str, Any]]
    def generate_recommendations(self, debt: dict[str, Any]) -> list[dict[str, Any]]
```

#### 5. `TestCoverageAnalyzer` Class
**Location**: `tapps_agents/agents/analyst/test_coverage_analyzer.py`

**Responsibilities**:
- Analyze test coverage
- Identify coverage gaps
- Assess test quality
- Generate test recommendations

**Key Methods**:
```python
class TestCoverageAnalyzer:
    def analyze_coverage(self, project_root: Path) -> dict[str, Any]
    def identify_gaps(self, coverage: dict[str, Any]) -> list[dict[str, Any]]
    def assess_quality(self, tests: list[Path]) -> dict[str, Any]
```

#### 6. `DocumentationAnalyzer` Class
**Location**: `tapps_agents/agents/analyst/documentation_analyzer.py`

**Responsibilities**:
- Analyze documentation coverage
- Identify documentation gaps
- Assess documentation quality
- Generate documentation recommendations

**Key Methods**:
```python
class DocumentationAnalyzer:
    def analyze_coverage(self, project_root: Path) -> dict[str, Any]
    def identify_gaps(self, codebase: dict[str, Any], docs: dict[str, Any]) -> list[dict[str, Any]]
    def assess_quality(self, docs: list[Path]) -> dict[str, Any]
```

#### 7. `ModernizationRoadmapGenerator` Class
**Location**: `tapps_agents/agents/analyst/roadmap_generator.py`

**Responsibilities**:
- Synthesize findings from all phases
- Generate modernization opportunities
- Prioritize improvements
- Create implementation roadmap

**Key Methods**:
```python
class ModernizationRoadmapGenerator:
    def generate_roadmap(self, analysis_results: dict[str, Any]) -> dict[str, Any]
    def prioritize_improvements(self, opportunities: list[dict[str, Any]]) -> list[dict[str, Any]]
    def estimate_effort(self, improvements: list[dict[str, Any]]) -> dict[str, Any]
```

### Integration Points

#### Analyst Agent Integration

**File**: `tapps_agents/agents/analyst/agent.py`

**Changes**:
1. Add `*analyze-brownfield` command to `get_commands()`
2. Add handler in `run()` method
3. Initialize `BrownfieldAnalyzer` in `__init__()`

**Code Addition**:
```python
def get_commands(self) -> list[dict[str, str]]:
    base_commands = super().get_commands()
    return base_commands + [
        # ... existing commands ...
        {
            "command": "*analyze-brownfield",
            "description": "Comprehensive brownfield project analysis",
        },
    ]

async def run(self, command: str, **kwargs: Any) -> dict[str, Any]:
    command = command.lstrip("*")
    # ... existing handlers ...
    elif command == "analyze-brownfield":
        project_root = kwargs.get("project_root")
        output_dir = kwargs.get("output_dir")
        format_type = kwargs.get("format", "all")
        phases = kwargs.get("phases")
        skip_phases = kwargs.get("skip_phases")
        return await self._analyze_brownfield(
            project_root=project_root,
            output_dir=output_dir,
            format_type=format_type,
            phases=phases,
            skip_phases=skip_phases,
        )
```

#### CLI Integration

**File**: `tapps_agents/cli/parsers/analyst.py`

**Changes**:
Add parser for `analyze-brownfield` command

**Code Addition**:
```python
analyze_brownfield_parser = analyst_subparsers.add_parser(
    "analyze-brownfield",
    aliases=["*analyze-brownfield"],
    help="Comprehensive brownfield project analysis",
    description="""Perform comprehensive analysis of existing (brownfield) project.
    
Analyzes:
  • Project structure and organization
  • Code quality and technical debt
  • Architecture patterns and design
  • Dependencies and integrations
  • Test coverage and documentation
  • Modernization opportunities
  
Generates comprehensive report with prioritized recommendations.
    
Example:
  tapps-agents analyst analyze-brownfield
  tapps-agents analyst analyze-brownfield --output-dir reports/ --format all""",
)
analyze_brownfield_parser.add_argument("--project-root", type=str, help="Project root directory")
analyze_brownfield_parser.add_argument("--output-dir", type=str, help="Output directory for reports")
analyze_brownfield_parser.add_argument("--format", choices=["json", "markdown", "html", "all"], default="all", help="Output format")
analyze_brownfield_parser.add_argument("--phases", type=str, help="Comma-separated list of phases to run")
analyze_brownfield_parser.add_argument("--skip-phases", type=str, help="Comma-separated list of phases to skip")
```

#### CLI Command Handler

**File**: `tapps_agents/cli/commands/analyst.py`

**Changes**:
Add handler for `analyze-brownfield` command

**Code Addition**:
```python
elif args.command == "analyze-brownfield":
    from ...agents.analyst.brownfield_analyzer import BrownfieldAnalyzer
    
    project_root = Path(args.project_root) if args.project_root else Path.cwd()
    output_dir = Path(args.output_dir) if args.output_dir else project_root / "reports" / "brownfield-analysis"
    
    phases = args.phases.split(",") if args.phases else None
    skip_phases = args.skip_phases.split(",") if args.skip_phases else None
    
    analyzer = BrownfieldAnalyzer(config=config)
    result = await analyzer.analyze(
        project_root=project_root,
        phases=phases,
        skip_phases=skip_phases,
    )
    
    # Generate reports
    await analyzer.generate_report(
        results=result,
        format_type=args.format,
        output_dir=output_dir,
    )
```

## Output Format

### Report Structure

The brownfield analysis generates a comprehensive report with the following structure:

```json
{
  "metadata": {
    "project_root": "/path/to/project",
    "analysis_date": "2025-01-XX",
    "phases_executed": ["discovery", "quality", "architecture", ...],
    "duration_seconds": 123.45
  },
  "phase_1_discovery": {
    "project_profile": {...},
    "services": [...],
    "tech_stack": {...},
    "file_structure": {...}
  },
  "phase_2_quality": {
    "overall_scores": {...},
    "by_service": [...],
    "duplication": {...},
    "security_issues": [...]
  },
  "phase_3_architecture": {
    "patterns": [...],
    "component_graph": {...},
    "coupling_metrics": {...},
    "architectural_debt": [...]
  },
  "phase_4_structure": {
    "organization_quality": {...},
    "coupling_cohesion": {...},
    "structural_issues": [...]
  },
  "phase_5_technical_debt": {
    "debt_inventory": [...],
    "categorization": {...},
    "prioritized_debt": [...],
    "remediation_roadmap": [...]
  },
  "phase_6_dependencies": {
    "dependency_tree": {...},
    "security_vulnerabilities": [...],
    "outdated_packages": [...],
    "integration_points": [...]
  },
  "phase_7_tests_docs": {
    "test_coverage": {...},
    "test_gaps": [...],
    "documentation_coverage": {...},
    "documentation_gaps": [...]
  },
  "phase_8_modernization": {
    "opportunities": [...],
    "prioritized_improvements": [...],
    "effort_estimates": {...},
    "implementation_roadmap": [...]
  },
  "summary": {
    "overall_health_score": 72.5,
    "critical_issues": 5,
    "high_priority_debt": 12,
    "recommended_actions": [...]
  }
}
```

### Markdown Report

The markdown report includes:
- Executive Summary
- Current State Assessment
- Detailed Phase Results
- Technical Debt Inventory
- Modernization Roadmap
- Prioritized Action Items

### HTML Report

The HTML report provides:
- Interactive dashboard
- Visualizations (charts, graphs)
- Drill-down capabilities
- Export functionality

## Workflow YAML

**File**: `workflows/presets/brownfield-analysis.yaml`

```yaml
workflow:
  id: brownfield-analysis
  name: Brownfield Project Analysis
  description: Comprehensive analysis of existing codebase
  type: analysis
  
sequence:
  - step: discovery
    agent: analyst
    action: analyze-brownfield
    parameters:
      phase: discovery
    creates: project_profile, service_inventory
    
  - step: quality_analysis
    agent: reviewer
    action: analyze-project
    requires: discovery
    creates: quality_report
    
  - step: architecture_analysis
    agent: analyst
    action: analyze-brownfield
    parameters:
      phase: architecture
    requires: discovery
    creates: architecture_report
    
  - step: structure_analysis
    agent: analyst
    action: analyze-brownfield
    parameters:
      phase: structure
    requires: discovery
    creates: structure_report
    
  - step: dependency_analysis
    agent: ops
    action: audit-dependencies
    requires: discovery
    creates: dependency_report
    
  - step: technical_debt_assessment
    agent: analyst
    action: analyze-brownfield
    parameters:
      phase: technical_debt
    requires: [quality_analysis, architecture_analysis, structure_analysis]
    creates: debt_report
    
  - step: test_doc_analysis
    agent: analyst
    action: analyze-brownfield
    parameters:
      phase: tests_docs
    requires: discovery
    creates: test_doc_report
    
  - step: modernization_roadmap
    agent: analyst
    action: analyze-brownfield
    parameters:
      phase: modernization
    requires: [technical_debt_assessment, test_doc_analysis]
    creates: roadmap
    
  - step: generate_report
    agent: analyst
    action: analyze-brownfield
    parameters:
      phase: report_generation
    requires: [modernization_roadmap]
    creates: final_report
```

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1)
- [ ] Create `BrownfieldAnalyzer` class
- [ ] Implement phase orchestration
- [ ] Add command to Analyst Agent
- [ ] Add CLI parser and handler
- [ ] Basic report generation (JSON)

### Phase 2: Architecture Analysis (Week 2)
- [ ] Create `ArchitectureAnalyzer` class
- [ ] Implement import graph analysis
- [ ] Implement pattern detection
- [ ] Implement coupling/cohesion metrics
- [ ] Integration with Phase 3

### Phase 3: Structure Analysis (Week 2)
- [ ] Create `StructureAnalyzer` class
- [ ] Implement module organization analysis
- [ ] Implement structure quality metrics
- [ ] Implement issue detection
- [ ] Integration with Phase 4

### Phase 4: Technical Debt Analysis (Week 3)
- [ ] Create `TechnicalDebtAnalyzer` class
- [ ] Implement debt categorization
- [ ] Implement prioritization algorithm
- [ ] Implement remediation recommendations
- [ ] Integration with all phases

### Phase 5: Test & Documentation Analysis (Week 3)
- [ ] Create `TestCoverageAnalyzer` class
- [ ] Create `DocumentationAnalyzer` class
- [ ] Implement coverage gap detection
- [ ] Implement quality assessment
- [ ] Integration with Phase 7

### Phase 6: Modernization Roadmap (Week 4)
- [ ] Create `ModernizationRoadmapGenerator` class
- [ ] Implement opportunity identification
- [ ] Implement prioritization
- [ ] Implement effort estimation
- [ ] Integration with Phase 8

### Phase 7: Reporting & Polish (Week 4)
- [ ] Enhanced markdown report generation
- [ ] HTML report with visualizations
- [ ] Workflow YAML creation
- [ ] Documentation
- [ ] Testing

## Testing Strategy

### Unit Tests
- Test each analyzer class independently
- Mock external dependencies
- Test error handling

### Integration Tests
- Test phase orchestration
- Test agent integration
- Test CLI commands

### End-to-End Tests
- Test full workflow on sample projects
- Verify report generation
- Verify output formats

## Documentation

### User Documentation
- Command reference
- Usage examples
- Report interpretation guide

### Developer Documentation
- Architecture overview
- Extension points
- Contributing guide

## Success Criteria

1. ✅ Can analyze any brownfield project comprehensively
2. ✅ Generates actionable recommendations
3. ✅ Integrates with existing TappsCodingAgents capabilities
4. ✅ Produces multiple output formats
5. ✅ Handles large codebases efficiently
6. ✅ Provides clear prioritization of issues

## Future Enhancements

1. **Incremental Analysis**: Track changes over time
2. **Comparison Mode**: Compare against baseline or other projects
3. **Custom Rules**: Allow project-specific analysis rules
4. **CI/CD Integration**: Automated analysis in pipelines
5. **Visualization**: Interactive architecture diagrams
6. **ML-Based Insights**: Use ML for pattern detection and recommendations

---

**Next Steps**: 
1. Review and approve specification
2. Begin Phase 1 implementation
3. Create GitHub issues for tracking
4. Set up project board

