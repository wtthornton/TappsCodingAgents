"""
Project Type Detector - Auto-detect project characteristics for workflow selection.
"""

from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import re


class ProjectType(Enum):
    """Project type classification."""
    GREENFIELD = "greenfield"
    BROWNFIELD = "brownfield"
    QUICK_FIX = "quick_fix"
    HYBRID = "hybrid"
    UNKNOWN = "unknown"


class WorkflowTrack(Enum):
    """Recommended workflow track."""
    QUICK_FLOW = "quick_flow"  # Bug fixes, small features (< 5 min)
    BMAD_METHOD = "bmad_method"  # Standard development (< 15 min)
    ENTERPRISE = "enterprise"  # Complex/compliance (< 30 min)


@dataclass
class ProjectCharacteristics:
    """Detected project characteristics."""
    project_type: ProjectType
    workflow_track: WorkflowTrack
    confidence: float
    indicators: Dict[str, any]
    recommendations: List[str]


class ProjectDetector:
    """Detect project type and recommend workflow track."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize project detector.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root or Path.cwd()
        
        # Detection rules
        self.greenfield_indicators = [
            ("no_src", lambda p: not (p / "src").exists() and not (p / "lib").exists()),
            ("no_package_files", lambda p: not self._has_package_files(p)),
            ("no_git_history", lambda p: not (p / ".git").exists()),
            ("minimal_files", lambda p: len(list(p.glob("*"))) < 5),
        ]
        
        self.brownfield_indicators = [
            ("has_src", lambda p: (p / "src").exists() or (p / "lib").exists()),
            ("has_package_files", lambda p: self._has_package_files(p)),
            ("has_git_history", lambda p: (p / ".git").exists()),
            ("has_tests", lambda p: (p / "tests").exists() or (p / "test").exists()),
            ("has_docs", lambda p: (p / "docs").exists() or (p / "README.md").exists()),
            ("many_files", lambda p: len(list(p.glob("*"))) >= 5),
        ]
        
        self.quick_fix_keywords = [
            "bug", "fix", "hotfix", "patch", "issue", "error", "bugfix",
            "repair", "correct", "resolve"
        ]
        
        self.complexity_indicators = [
            ("has_compliance", lambda p: self._has_compliance_files(p)),
            ("has_security", lambda p: self._has_security_files(p)),
            ("multiple_domains", lambda p: self._has_multiple_domains(p)),
            ("large_codebase", lambda p: self._is_large_codebase(p)),
        ]
    
    def _has_package_files(self, project_root: Path) -> bool:
        """Check if project has package management files."""
        package_files = [
            "package.json", "requirements.txt", "Pipfile", "pyproject.toml",
            "Cargo.toml", "go.mod", "pom.xml", "build.gradle", "composer.json"
        ]
        return any((project_root / f).exists() for f in package_files)
    
    def _has_compliance_files(self, project_root: Path) -> bool:
        """Check if project has compliance-related files."""
        compliance_patterns = [
            "compliance", "hipaa", "pci", "gdpr", "soc2", "audit"
        ]
        paths = [project_root / f for f in compliance_patterns]
        return any(p.exists() for p in paths) or any(
            compliance_pattern in str(p).lower() 
            for p in project_root.rglob("*")
            if p.is_file()
            for compliance_pattern in compliance_patterns
        )
    
    def _has_security_files(self, project_root: Path) -> bool:
        """Check if project has security-related files."""
        security_files = [
            ".security", "security.md", "SECURITY.md", ".bandit", ".safety"
        ]
        return any((project_root / f).exists() for f in security_files)
    
    def _has_multiple_domains(self, project_root: Path) -> bool:
        """Check if project has multiple domain configurations."""
        domains_file = project_root / ".tapps-agents" / "domains.md"
        if domains_file.exists():
            content = domains_file.read_text(encoding='utf-8')
            # Count domain sections
            domain_count = len(re.findall(r'### Domain \d+:', content))
            return domain_count > 1
        return False
    
    def _is_large_codebase(self, project_root: Path) -> bool:
        """Check if codebase is large (heuristic: >1000 files)."""
        code_extensions = {".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c"}
        count = 0
        for ext in code_extensions:
            count += len(list(project_root.rglob(f"*{ext}")))
            if count > 1000:
                return True
        return False
    
    def detect_from_context(
        self,
        user_query: Optional[str] = None,
        file_count: Optional[int] = None,
        scope_description: Optional[str] = None
    ) -> ProjectCharacteristics:
        """
        Detect project type from user context (for quick-fix detection).
        
        Args:
            user_query: User's query or request
            file_count: Estimated number of files to change
            scope_description: Description of the change scope
        
        Returns:
            ProjectCharacteristics with detection results
        """
        indicators = {}
        confidence = 0.0
        recommendations = []
        
        # Check for quick-fix keywords
        quick_fix_score = 0.0
        if user_query:
            query_lower = user_query.lower()
            for keyword in self.quick_fix_keywords:
                if keyword in query_lower:
                    quick_fix_score += 0.2
            indicators["quick_fix_keywords"] = quick_fix_score > 0
        
        if scope_description:
            desc_lower = scope_description.lower()
            for keyword in self.quick_fix_keywords:
                if keyword in desc_lower:
                    quick_fix_score += 0.2
        
        # Check file scope
        small_scope = file_count is not None and file_count < 5
        if small_scope:
            quick_fix_score += 0.4
            indicators["small_scope"] = True
        
        # Determine if quick-fix
        if quick_fix_score >= 0.6:
            confidence = min(0.9, quick_fix_score)
            recommendations.append("Consider Quick Flow track for fast turnaround")
            return ProjectCharacteristics(
                project_type=ProjectType.QUICK_FIX,
                workflow_track=WorkflowTrack.QUICK_FLOW,
                confidence=confidence,
                indicators=indicators,
                recommendations=recommendations
            )
        
        # Otherwise, use standard detection
        return self.detect()
    
    def detect(self) -> ProjectCharacteristics:
        """
        Detect project type from file system analysis.
        
        Returns:
            ProjectCharacteristics with detection results
        """
        indicators = {}
        greenfield_score = 0.0
        brownfield_score = 0.0
        
        # Check greenfield indicators
        for name, check in self.greenfield_indicators:
            if check(self.project_root):
                greenfield_score += 0.25
                indicators[name] = True
            else:
                indicators[name] = False
        
        # Check brownfield indicators
        for name, check in self.brownfield_indicators:
            if check(self.project_root):
                brownfield_score += 0.15
                indicators[name] = True
            else:
                indicators[name] = False
        
        # Check for enterprise/complexity indicators first (before type determination)
        complexity_score = 0.0
        recommendations = []  # Initialize recommendations list
        
        for name, check in self.complexity_indicators:
            if check(self.project_root):
                complexity_score += 0.25
                indicators[name] = True
                if name == "has_compliance":
                    recommendations.append("Compliance requirements detected - consider Enterprise track")
            else:
                indicators[name] = False
        
        # Determine project type
        # Prioritize brownfield if both greenfield and brownfield indicators present
        if brownfield_score >= 0.45:  # Lower threshold to prefer brownfield
            project_type = ProjectType.BROWNFIELD
            confidence = min(0.9, brownfield_score)
            workflow_track = WorkflowTrack.BMAD_METHOD
            if not recommendations:
                recommendations = [
                    "Existing project detected - use BMad Method workflow",
                    "Leverage existing codebase structure and patterns"
                ]
        elif greenfield_score >= 0.5:
            project_type = ProjectType.GREENFIELD
            confidence = min(0.9, greenfield_score)
            workflow_track = WorkflowTrack.BMAD_METHOD
            if not recommendations:
                recommendations = [
                    "New project detected - use BMad Method workflow",
                    "Start with requirements gathering and architecture design"
                ]
        else:
            project_type = ProjectType.HYBRID
            confidence = 0.5
            workflow_track = WorkflowTrack.BMAD_METHOD
            if not recommendations:
                recommendations = [
                    "Mixed indicators detected - defaulting to BMad Method workflow",
                    "Review workflow steps and customize as needed"
                ]
        
        # Upgrade to Enterprise track if complexity is high
        if complexity_score >= 0.25:  # Lower threshold - any compliance/complexity indicator
            workflow_track = WorkflowTrack.ENTERPRISE
            if not any("Complex project detected" in rec for rec in recommendations):
                recommendations.append("Complex project detected - Enterprise workflow recommended")
            confidence = min(0.95, confidence + 0.1)
        
        return ProjectCharacteristics(
            project_type=project_type,
            workflow_track=workflow_track,
            confidence=confidence,
            indicators=indicators,
            recommendations=recommendations
        )
    
    def get_recommended_workflow(self, characteristics: ProjectCharacteristics) -> Optional[str]:
        """
        Get recommended workflow file name based on characteristics.
        
        Args:
            characteristics: Detected project characteristics
        
        Returns:
            Recommended workflow file name (without extension) or None
        """
        if characteristics.workflow_track == WorkflowTrack.QUICK_FLOW:
            return "quick-fix"
        elif characteristics.workflow_track == WorkflowTrack.ENTERPRISE:
            return "enterprise-development"
        else:  # BMAD_METHOD
            if characteristics.project_type == ProjectType.GREENFIELD:
                return "greenfield-development"
            elif characteristics.project_type == ProjectType.BROWNFIELD:
                return "brownfield-development"
            else:
                return "feature-development"  # Default

