"""
Design Validator - Validates architecture and API designs against requirements.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ArchitectureValidationResult:
    """Result of architecture validation."""

    is_valid: bool
    requirements_coverage: float = 0.0  # 0-100: % of requirements covered
    missing_requirements: list[str] = field(default_factory=list)
    pattern_violations: list[str] = field(default_factory=list)
    security_issues: list[str] = field(default_factory=list)
    scalability_concerns: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class APIConsistencyResult:
    """Result of API design consistency check."""

    is_consistent: bool
    violations: list[str] = field(default_factory=list)
    pattern_deviations: list[str] = field(default_factory=list)
    naming_inconsistencies: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class DesignValidator:
    """Validates design artifacts against requirements and patterns."""

    def validate_requirements_alignment(
        self, architecture: dict[str, Any], requirements: dict[str, Any]
    ) -> ArchitectureValidationResult:
        """
        Validate that architecture covers all requirements.

        Args:
            architecture: Architecture document with components, patterns, etc.
            requirements: Requirements document

        Returns:
            ArchitectureValidationResult
        """
        result = ArchitectureValidationResult(is_valid=True)

        # Extract functional requirements
        func_reqs = requirements.get("functional_requirements", [])
        if not func_reqs:
            result.is_valid = False
            result.missing_requirements.append("No functional requirements to validate against")
            return result

        # Extract architecture components
        components = architecture.get("components", [])
        architecture_text = str(architecture).lower()

        # Check coverage
        covered_count = 0
        missing = []

        for req in func_reqs:
            if isinstance(req, dict):
                req_text = req.get("description", "").lower()
                req_id = req.get("id", "")
            else:
                req_text = str(req).lower()
                req_id = ""

            # Simple keyword matching (could be enhanced with semantic similarity)
            req_keywords = self._extract_keywords(req_text)
            covered = any(keyword in architecture_text for keyword in req_keywords if len(keyword) > 3)

            if covered:
                covered_count += 1
            else:
                missing.append(req_id or req_text[:100])

        result.requirements_coverage = (covered_count / len(func_reqs)) * 100.0 if func_reqs else 0.0

        if result.requirements_coverage < 80.0:
            result.is_valid = False
            result.missing_requirements = missing

        # Check for security requirements
        nfr_reqs = requirements.get("non_functional_requirements", [])
        security_reqs = [req for req in nfr_reqs if "security" in str(req).lower() or "auth" in str(req).lower()]
        if security_reqs:
            # Check if architecture addresses security
            if "security" not in architecture_text and "auth" not in architecture_text:
                result.security_issues.append("Security requirements not addressed in architecture")

        # Check for scalability requirements
        scalability_reqs = [req for req in nfr_reqs if "scalability" in str(req).lower() or "scale" in str(req).lower()]
        if scalability_reqs:
            if "scal" not in architecture_text and "load" not in architecture_text:
                result.scalability_concerns.append("Scalability requirements not addressed")

        # Generate recommendations
        if result.requirements_coverage < 80.0:
            result.recommendations.append(
                f"Improve requirements coverage: {result.requirements_coverage:.1f}% (target: 80%+)"
            )
        if result.security_issues:
            result.recommendations.append("Add security architecture section")
        if result.scalability_concerns:
            result.recommendations.append("Add scalability considerations to architecture")

        return result

    def validate_api_consistency(self, api_design: dict[str, Any], project_patterns: dict[str, Any] | None = None) -> APIConsistencyResult:
        """
        Validate API design consistency with project patterns.

        Args:
            api_design: API design document with endpoints, methods, etc.
            project_patterns: Optional project-specific patterns to check against

        Returns:
            APIConsistencyResult
        """
        result = APIConsistencyResult(is_consistent=True)

        endpoints = api_design.get("endpoints", [])
        if not endpoints:
            result.is_consistent = False
            result.violations.append("No endpoints defined")
            return result

        # Check naming consistency
        naming_issues = self._check_naming_consistency(endpoints)
        if naming_issues:
            result.is_consistent = False
            result.naming_inconsistencies = naming_issues

        # Check RESTful patterns
        rest_violations = self._check_restful_patterns(endpoints)
        if rest_violations:
            result.is_consistent = False
            result.violations.extend(rest_violations)

        # Check against project patterns if provided
        if project_patterns:
            pattern_deviations = self._check_project_patterns(api_design, project_patterns)
            if pattern_deviations:
                result.is_consistent = False
                result.pattern_deviations = pattern_deviations

        # Generate recommendations
        if result.naming_inconsistencies:
            result.recommendations.append("Standardize endpoint naming convention")
        if result.violations:
            result.recommendations.append("Review RESTful design principles")
        if result.pattern_deviations:
            result.recommendations.append("Align with project design patterns")

        return result

    def detect_pattern_violations(self, architecture: dict[str, Any], patterns: list[str]) -> list[str]:
        """
        Detect violations of specified design patterns.

        Args:
            architecture: Architecture document
            patterns: List of pattern names to check (e.g., ["layered", "microservices"])

        Returns:
            List of violation descriptions
        """
        violations = []
        architecture_text = str(architecture).lower()

        # Check for pattern-specific violations
        if "layered" in patterns:
            # Layered architecture should have clear layers
            layers = architecture.get("layers", [])
            if not layers:
                violations.append("Layered architecture pattern specified but no layers defined")

        if "microservices" in patterns:
            # Microservices should have service boundaries
            services = architecture.get("services", [])
            if not services:
                violations.append("Microservices pattern specified but no services defined")

        if "mvc" in patterns or "model-view-controller" in patterns:
            # MVC should have model, view, controller components
            components = architecture.get("components", [])
            component_names = [c.get("name", "").lower() if isinstance(c, dict) else str(c).lower() for c in components]
            has_model = any("model" in name for name in component_names)
            has_view = any("view" in name for name in component_names)
            has_controller = any("controller" in name for name in component_names)

            if not (has_model and has_view and has_controller):
                violations.append("MVC pattern specified but missing model, view, or controller components")

        return violations

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract meaningful keywords from text."""
        # Remove common stop words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        words = re.findall(r"\b\w+\b", text.lower())
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        return keywords[:10]  # Top 10 keywords

    def _check_naming_consistency(self, endpoints: list[dict[str, Any]]) -> list[str]:
        """Check endpoint naming consistency."""
        issues = []

        # Check URL pattern consistency
        url_patterns = []
        for endpoint in endpoints:
            if isinstance(endpoint, dict):
                path = endpoint.get("path", "")
                method = endpoint.get("method", "").upper()
                url_patterns.append((path, method))

        # Check for inconsistent naming conventions
        # e.g., some use camelCase, some use snake_case, some use kebab-case
        paths = [p[0] for p in url_patterns]
        has_camel = any(re.search(r"[a-z][A-Z]", p) for p in paths)
        has_snake = any("_" in p for p in paths)
        has_kebab = any("-" in p for p in paths)

        if sum([has_camel, has_snake, has_kebab]) > 1:
            issues.append("Inconsistent URL naming conventions (camelCase, snake_case, kebab-case mixed)")

        # Check for inconsistent resource naming (singular vs plural)
        resource_names = [p.split("/")[-1] for p in paths if "/" in p]
        singular_count = sum(1 for r in resource_names if not r.endswith("s"))
        plural_count = sum(1 for r in resource_names if r.endswith("s"))

        if singular_count > 0 and plural_count > 0:
            issues.append("Inconsistent resource naming (singular and plural mixed)")

        return issues

    def _check_restful_patterns(self, endpoints: list[dict[str, Any]]) -> list[str]:
        """Check RESTful design pattern compliance."""
        violations = []

        for endpoint in endpoints:
            if isinstance(endpoint, dict):
                path = endpoint.get("path", "")
                method = endpoint.get("method", "").upper()

                # Check HTTP method usage
                if method not in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
                    violations.append(f"Non-standard HTTP method: {method} for {path}")

                # Check GET should not modify state
                if method == "GET" and ("create" in path.lower() or "delete" in path.lower() or "update" in path.lower()):
                    violations.append(f"GET method used for state modification: {path}")

                # Check resource naming
                if method in ["POST", "PUT", "PATCH"] and not path.endswith(("/", "s")):
                    # POST/PUT/PATCH should typically target resources (plural or singular)
                    pass  # This is OK, just checking

        return violations

    def _check_project_patterns(self, api_design: dict[str, Any], project_patterns: dict[str, Any]) -> list[str]:
        """Check API design against project-specific patterns."""
        deviations = []

        # Example: Check response format consistency
        endpoints = api_design.get("endpoints", [])
        response_formats = set()

        for endpoint in endpoints:
            if isinstance(endpoint, dict):
                response = endpoint.get("response", {})
                if isinstance(response, dict):
                    format_type = response.get("format", "json")
                    response_formats.add(format_type)

        # If project pattern specifies single format but multiple found
        expected_format = project_patterns.get("response_format", "json")
        if len(response_formats) > 1:
            deviations.append(f"Multiple response formats found, project pattern expects: {expected_format}")

        # Check authentication pattern
        auth_pattern = project_patterns.get("authentication", {})
        if auth_pattern:
            api_auth = api_design.get("authentication", {})
            if not api_auth:
                deviations.append("Project requires authentication but API design doesn't specify it")

        return deviations
