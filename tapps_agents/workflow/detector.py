"""
Project Type Detector - Auto-detect project characteristics for workflow selection.
"""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


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
    indicators: dict[str, Any]
    recommendations: list[str]


class ProjectDetector:
    """Detect project type and recommend workflow track."""

    def __init__(self, project_root: Path | None = None):
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
            "bug",
            "fix",
            "hotfix",
            "patch",
            "issue",
            "error",
            "bugfix",
            "repair",
            "correct",
            "resolve",
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
            "package.json",
            "requirements.txt",
            "Pipfile",
            "pyproject.toml",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            "build.gradle",
            "composer.json",
        ]
        return any((project_root / f).exists() for f in package_files)

    def _has_compliance_files(self, project_root: Path) -> bool:
        """Check if project has compliance-related files."""
        compliance_patterns = ["compliance", "hipaa", "pci", "gdpr", "soc2", "audit"]
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
            ".security",
            "security.md",
            "SECURITY.md",
            ".bandit",
            ".safety",
        ]
        return any((project_root / f).exists() for f in security_files)

    def _has_multiple_domains(self, project_root: Path) -> bool:
        """Check if project has multiple domain configurations."""
        domains_file = project_root / ".tapps-agents" / "domains.md"
        if domains_file.exists():
            content = domains_file.read_text(encoding="utf-8")
            # Count domain sections
            domain_count = len(re.findall(r"### Domain \d+:", content))
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

    def detect_deployment_type(self) -> tuple[str | None, float, list[str]]:
        """
        Detect deployment type with confidence score.

        Returns:
            Tuple of (deployment_type, confidence, indicators)
            deployment_type: "local", "cloud", or "enterprise" (or None)
            confidence: 0.0-1.0
            indicators: List of indicator names that matched
        """
        indicators = []
        cloud_score = 0.0
        enterprise_score = 0.0
        local_score = 0.0

        # Enterprise indicators (Kubernetes, Helm, compliance, security)
        enterprise_checks = [
            (
                "has_kubernetes",
                lambda p: (p / "k8s").exists() or (p / "kubernetes").exists(),
            ),
            (
                "has_helm",
                lambda p: (p / "helm").exists()
                or any((p / f).exists() for f in ["Chart.yaml", "values.yaml"]),
            ),
            (
                "has_compliance",
                lambda p: (p / "compliance").exists()
                or any((p / f).exists() for f in ["HIPAA.md", "GDPR.md", "SOC2.md"]),
            ),
            (
                "has_security",
                lambda p: (p / "security").exists()
                or (p / ".security").exists()
                or (p / "security.md").exists(),
            ),
        ]

        for name, check in enterprise_checks:
            if check(self.project_root):
                enterprise_score += 0.25
                indicators.append(name)

        # Cloud indicators (Docker, serverless, terraform)
        cloud_checks = [
            ("has_dockerfile", lambda p: (p / "Dockerfile").exists()),
            (
                "has_docker_compose",
                lambda p: (p / "docker-compose.yml").exists()
                or (p / "docker-compose.yaml").exists(),
            ),
            (
                "has_serverless",
                lambda p: (p / "serverless.yml").exists()
                or (p / "serverless.yaml").exists(),
            ),
            (
                "has_terraform",
                lambda p: (p / "terraform").exists()
                or any(
                    (p / f).exists()
                    for f in ["main.tf", "variables.tf", "terraform.tf"]
                ),
            ),
        ]

        for name, check in cloud_checks:
            if check(self.project_root):
                cloud_score += 0.2
                indicators.append(name)

        # Local indicators (conservative - default to local)
        if cloud_score < 0.3 and enterprise_score < 0.3:
            local_score = 0.5  # Conservative default
            indicators.append("no_cloud_infrastructure")

        # Determine result (enterprise takes precedence)
        if enterprise_score >= 0.5:
            return ("enterprise", min(0.95, enterprise_score), indicators)
        elif cloud_score >= 0.6:
            return ("cloud", min(0.9, cloud_score), indicators)
        elif cloud_score >= 0.3:
            return ("cloud", min(0.7, cloud_score), indicators)
        else:
            return ("local", min(0.8, local_score), indicators)

    def detect_compliance_requirements(self) -> list[tuple[str, float, list[str]]]:
        """
        Detect compliance requirements from files.

        Returns:
            List of tuples: (compliance_name, confidence, indicators)
        """
        compliance_patterns = {
            "GDPR": ["gdpr", "general data protection regulation"],
            "HIPAA": ["hipaa", "health insurance portability"],
            "PCI": ["pci", "payment card industry"],
            "SOC2": ["soc2", "soc 2", "service organization control"],
            "ISO27001": ["iso27001", "iso 27001"],
        }

        requirements = []
        project_root = self.project_root

        # Check for compliance files/directories
        for compliance_name, patterns in compliance_patterns.items():
            indicators = []
            confidence = 0.0

            # Check file/directory names
            for pattern in patterns:
                # Check exact file/directory names
                if (project_root / pattern).exists():
                    confidence += 0.4
                    indicators.append(f"{pattern}_file_found")

                # Check in file paths
                matching_files = list(project_root.rglob(f"*{pattern}*"))
                if matching_files:
                    confidence += 0.3
                    indicators.append(f"{pattern}_pattern_in_paths")

            # Check in compliance directory
            compliance_dir = project_root / "compliance"
            if compliance_dir.exists():
                # Check if compliance name appears in compliance directory
                for pattern in patterns:
                    if any(
                        pattern in str(p).lower() for p in compliance_dir.rglob("*")
                    ):
                        confidence += 0.3
                        indicators.append(f"{compliance_name}_in_compliance_dir")
                        break

            # If we found indicators, add requirement
            if confidence > 0.0:
                requirements.append((compliance_name, min(0.9, confidence), indicators))

        return requirements

    def detect_security_level(self) -> tuple[str | None, float, list[str]]:
        """
        Detect security level with confidence score.

        Returns:
            Tuple of (security_level, confidence, indicators)
            security_level: "basic", "standard", "high", or "critical" (or None)
            confidence: 0.0-1.0
            indicators: List of indicator names that matched
        """
        security_files = [
            ".security",
            "security.md",
            "SECURITY.md",
            ".bandit",
            ".safety",
            ".snyk",
            "snyk.yml",
            ".dependabot",
            "dependabot.yml",
        ]

        indicators = []
        found_files = []

        for security_file in security_files:
            if (self.project_root / security_file).exists():
                found_files.append(security_file)
                indicators.append(
                    f"has_{security_file.replace('.', '').replace('-', '_')}"
                )

        # Determine security level based on number of files
        num_files = len(found_files)

        if num_files >= 3:
            return ("high", 0.8, indicators)
        elif num_files == 2:
            return ("standard", 0.7, indicators)
        elif num_files == 1:
            return ("standard", 0.6, indicators)
        else:
            return ("basic", 0.5, ["no_security_files"])

    def detect_tenancy(self) -> tuple[str | None, float, list[str]]:
        """
        Detect tenancy model (single-tenant vs multi-tenant) by grepping code.

        Returns:
            Tuple of (tenancy, confidence, indicators)
            tenancy: "single-tenant" or "multi-tenant" (or None)
            confidence: 0.0-1.0
            indicators: List of indicator names that matched
        """
        import re

        indicators = []
        tenant_patterns = [
            r"\btenant_id\b",
            r"\btenantId\b",
            r"\btenant-id\b",
            r"\btenant_uuid\b",
            r"\btenant_context\b",
            r"\bmulti_tenant\b",
            r"\bmultiTenant\b",
        ]

        # Search in common code files
        code_extensions = {
            ".py",
            ".js",
            ".ts",
            ".java",
            ".go",
            ".rs",
            ".cpp",
            ".c",
            ".cs",
        }
        matching_files = set()

        for ext in code_extensions:
            for code_file in self.project_root.rglob(f"*{ext}"):
                try:
                    # Skip very large files and binary-like files
                    if code_file.stat().st_size > 1_000_000:  # 1MB limit
                        continue

                    content = code_file.read_text(encoding="utf-8", errors="ignore")

                    # Check for tenant patterns
                    for pattern in tenant_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            matching_files.add(code_file)
                            indicators.append(f"tenant_pattern_in_{code_file.name}")
                            break  # Count file once even if multiple patterns match
                except (UnicodeDecodeError, PermissionError, OSError):
                    # Skip files that can't be read
                    continue

        num_files = len(matching_files)

        # Determine tenancy based on number of files with tenant patterns
        if num_files > 3:
            return ("multi-tenant", 0.8, indicators)
        elif num_files >= 1:
            return ("multi-tenant", 0.6, indicators)  # Medium confidence, suggest
        else:
            # Conservative: default to single-tenant if no patterns found
            return ("single-tenant", 0.7, ["no_tenant_patterns_found"])

    def detect_user_scale(self) -> tuple[str | None, float, list[str]]:
        """
        Detect expected user scale from infrastructure patterns.

        Returns:
            Tuple of (user_scale, confidence, indicators)
            user_scale: "single-user", "small-team", "department", "enterprise" (or None)
            confidence: 0.0-1.0
            indicators: List of indicator names that matched
        """
        indicators = []
        scale_score = {
            "single-user": 0.0,
            "small-team": 0.0,
            "department": 0.0,
            "enterprise": 0.0,
        }

        # Enterprise indicators (high scale)
        enterprise_checks = [
            (
                "has_load_balancer",
                lambda p: any(
                    (p / f).exists()
                    for f in ["nginx.conf", "haproxy.cfg", "traefik.yml"]
                ),
            ),
            (
                "has_oauth",
                lambda p: any(
                    "oauth" in str(f).lower() for f in p.rglob("*") if f.is_file()
                ),
            ),
            (
                "has_saml",
                lambda p: any(
                    "saml" in str(f).lower() for f in p.rglob("*") if f.is_file()
                ),
            ),
            (
                "has_ldap",
                lambda p: any(
                    "ldap" in str(f).lower() for f in p.rglob("*") if f.is_file()
                ),
            ),
            (
                "has_kubernetes",
                lambda p: (p / "k8s").exists() or (p / "kubernetes").exists(),
            ),
            (
                "has_helm",
                lambda p: (p / "helm").exists()
                or any((p / f).exists() for f in ["Chart.yaml", "values.yaml"]),
            ),
        ]

        for name, check in enterprise_checks:
            if check(self.project_root):
                scale_score["enterprise"] += 0.15
                indicators.append(name)

        # Department indicators (medium scale - caching, queues)
        department_checks = [
            (
                "has_redis",
                lambda p: any(
                    "redis" in str(f).lower() for f in p.rglob("*") if f.is_file()
                )
                or (p / "redis.conf").exists(),
            ),
            (
                "has_memcached",
                lambda p: any(
                    "memcached" in str(f).lower() for f in p.rglob("*") if f.is_file()
                ),
            ),
            (
                "has_message_queue",
                lambda p: any(
                    q in str(f).lower()
                    for q in ["rabbitmq", "kafka", "sqs"]
                    for f in p.rglob("*")
                    if f.is_file()
                ),
            ),
        ]

        for name, check in department_checks:
            if check(self.project_root):
                scale_score["department"] += 0.2
                indicators.append(name)

        # Small team indicators (basic infrastructure)
        small_team_checks = [
            (
                "has_docker",
                lambda p: (p / "Dockerfile").exists()
                or (p / "docker-compose.yml").exists(),
            ),
            (
                "has_database",
                lambda p: any(
                    db in str(f).lower()
                    for db in ["postgres", "mysql", "sqlite"]
                    for f in p.rglob("*")
                    if f.is_file()
                ),
            ),
        ]

        for name, check in small_team_checks:
            if check(self.project_root):
                scale_score["small-team"] += 0.3
                indicators.append(name)

        # Determine result
        max_scale = max(scale_score.items(), key=lambda x: x[1])
        max_scale_name, max_scale_score = max_scale

        if max_scale_score >= 0.6:
            confidence = min(0.8, max_scale_score)
            return (max_scale_name, confidence, indicators)
        elif max_scale_score >= 0.3:
            confidence = min(0.6, max_scale_score)
            return (
                max_scale_name,
                confidence,
                indicators,
            )  # Medium confidence, suggest
        else:
            # Default to small-team with low confidence
            return ("small-team", 0.5, indicators + ["default_small_team"])

    def detect_from_context(
        self,
        user_query: str | None = None,
        file_count: int | None = None,
        scope_description: str | None = None,
    ) -> ProjectCharacteristics:
        """
        Detect project type from user context (for fix-workflow selection).

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
                recommendations=recommendations,
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
                    recommendations.append(
                        "Compliance requirements detected - consider Enterprise track"
                    )
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
                    "Leverage existing codebase structure and patterns",
                ]
        elif greenfield_score >= 0.5:
            project_type = ProjectType.GREENFIELD
            confidence = min(0.9, greenfield_score)
            workflow_track = WorkflowTrack.BMAD_METHOD
            if not recommendations:
                recommendations = [
                    "New project detected - use BMad Method workflow",
                    "Start with requirements gathering and architecture design",
                ]
        else:
            project_type = ProjectType.HYBRID
            confidence = 0.5
            workflow_track = WorkflowTrack.BMAD_METHOD
            if not recommendations:
                recommendations = [
                    "Mixed indicators detected - defaulting to BMad Method workflow",
                    "Review workflow steps and customize as needed",
                ]

        # Upgrade to Enterprise track if complexity is high
        if (
            complexity_score >= 0.25
        ):  # Lower threshold - any compliance/complexity indicator
            workflow_track = WorkflowTrack.ENTERPRISE
            if not any("Complex project detected" in rec for rec in recommendations):
                recommendations.append(
                    "Complex project detected - Enterprise workflow recommended"
                )
            confidence = min(0.95, confidence + 0.1)

        return ProjectCharacteristics(
            project_type=project_type,
            workflow_track=workflow_track,
            confidence=confidence,
            indicators=indicators,
            recommendations=recommendations,
        )

    def get_recommended_workflow(
        self, characteristics: ProjectCharacteristics
    ) -> str | None:
        """
        Get recommended workflow preset name based on characteristics.

        Returns canonical preset IDs: full-sdlc, rapid-dev, fix, quality, brownfield-analysis.
        """
        if characteristics.workflow_track == WorkflowTrack.QUICK_FLOW:
            return "fix"
        elif characteristics.workflow_track == WorkflowTrack.ENTERPRISE:
            return "full-sdlc"
        else:  # BMAD_METHOD
            if characteristics.project_type == ProjectType.GREENFIELD:
                return "rapid-dev"
            elif characteristics.project_type == ProjectType.BROWNFIELD:
                return "brownfield-analysis"
            else:
                return "rapid-dev"  # Default (was feature-development)

    def detect_command_suggestions(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Detect when to suggest Epic, coverage, microservice, or Docker commands.

        Args:
            context: User action context (files, actions, errors, etc.)

        Returns:
            List of command suggestions
        """
        suggestions = []

        # Detect Epic document mentions
        if context.get("files"):
            for file_path in context["files"]:
                if "epic" in str(file_path).lower() and file_path.endswith(".md"):
                    suggestions.append({
                        "command": f"@simple-mode *epic {file_path}",
                        "description": "Execute Epic workflow for this document",
                        "confidence": 0.9,
                        "type": "epic",
                    })

        # Detect test coverage gaps
        if context.get("action") == "checking_coverage" or "coverage.json" in str(context.get("files", [])):
            suggestions.append({
                "command": "@simple-mode *test-coverage <file> --target 80",
                "description": "Generate tests to improve coverage",
                "confidence": 0.85,
                "type": "coverage",
            })

        # Detect microservice creation
        if context.get("action") == "creating_service" or "services/" in str(context.get("files", [])):
            suggestions.append({
                "command": "@simple-mode *microservice <name> --port <port> --type fastapi",
                "description": "Generate microservice structure automatically",
                "confidence": 0.8,
                "type": "microservice",
            })

        # Detect Docker errors
        if context.get("error"):
            error_msg = str(context["error"])
            if any(keyword in error_msg.lower() for keyword in ["docker", "container", "module not found", "workdir"]):
                suggestions.append({
                    "command": "@simple-mode *docker-fix <service> \"<error>\"",
                    "description": "Debug and fix Docker/container issues",
                    "confidence": 0.9,
                    "type": "docker",
                })

        return suggestions