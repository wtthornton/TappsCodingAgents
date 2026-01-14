"""
NFR Validator - Validates non-functional requirements in design phase.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class NFRValidationResult:
    """Result of NFR validation."""

    is_valid: bool
    security_score: float = 0.0  # 0-100
    performance_score: float = 0.0  # 0-100
    reliability_score: float = 0.0  # 0-100
    maintainability_score: float = 0.0  # 0-100
    overall_score: float = 0.0  # Weighted average

    security_issues: list[str] = field(default_factory=list)
    performance_issues: list[str] = field(default_factory=list)
    reliability_issues: list[str] = field(default_factory=list)
    maintainability_issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class NFRValidator:
    """Validates non-functional requirements in architecture and design."""

    SECURITY_WEIGHT = 0.30
    PERFORMANCE_WEIGHT = 0.25
    RELIABILITY_WEIGHT = 0.25
    MAINTAINABILITY_WEIGHT = 0.20

    def validate_architecture_nfr(
        self, architecture: dict[str, Any], nfr_requirements: dict[str, Any]
    ) -> NFRValidationResult:
        """
        Validate architecture against NFR requirements.

        Args:
            architecture: Architecture document
            nfr_requirements: NFR requirements dict with categories

        Returns:
            NFRValidationResult
        """
        result = NFRValidationResult(is_valid=True)

        arch_text = str(architecture).lower()
        security_reqs = nfr_requirements.get("security", [])
        performance_reqs = nfr_requirements.get("performance", [])
        reliability_reqs = nfr_requirements.get("reliability", [])
        maintainability_reqs = nfr_requirements.get("maintainability", [])

        # Validate Security
        result.security_score, result.security_issues = self._validate_security(
            architecture, security_reqs, arch_text
        )

        # Validate Performance
        result.performance_score, result.performance_issues = self._validate_performance(
            architecture, performance_reqs, arch_text
        )

        # Validate Reliability
        result.reliability_score, result.reliability_issues = self._validate_reliability(
            architecture, reliability_reqs, arch_text
        )

        # Validate Maintainability
        result.maintainability_score, result.maintainability_issues = self._validate_maintainability(
            architecture, maintainability_reqs, arch_text
        )

        # Calculate overall score
        result.overall_score = (
            result.security_score * self.SECURITY_WEIGHT
            + result.performance_score * self.PERFORMANCE_WEIGHT
            + result.reliability_score * self.RELIABILITY_WEIGHT
            + result.maintainability_score * self.MAINTAINABILITY_WEIGHT
        )

        # Determine validity (threshold: 70%)
        result.is_valid = result.overall_score >= 70.0

        # Generate recommendations
        if result.security_score < 70.0:
            result.recommendations.append("Improve security architecture - address security requirements")
        if result.performance_score < 70.0:
            result.recommendations.append("Address performance requirements in architecture")
        if result.reliability_score < 70.0:
            result.recommendations.append("Enhance reliability measures in architecture")
        if result.maintainability_score < 70.0:
            result.recommendations.append("Improve maintainability considerations")

        return result

    def validate_api_nfr(self, api_design: dict[str, Any], nfr_requirements: dict[str, Any]) -> NFRValidationResult:
        """
        Validate API design against NFR requirements.

        Args:
            api_design: API design document
            nfr_requirements: NFR requirements dict

        Returns:
            NFRValidationResult
        """
        result = NFRValidationResult(is_valid=True)

        api_text = str(api_design).lower()
        security_reqs = nfr_requirements.get("security", [])
        performance_reqs = nfr_requirements.get("performance", [])

        # Validate Security
        result.security_score, result.security_issues = self._validate_api_security(
            api_design, security_reqs, api_text
        )

        # Validate Performance
        result.performance_score, result.performance_issues = self._validate_api_performance(
            api_design, performance_reqs, api_text
        )

        # Reliability and Maintainability less critical for API design
        result.reliability_score = 80.0  # Default
        result.maintainability_score = 80.0  # Default

        # Calculate overall score
        result.overall_score = (
            result.security_score * self.SECURITY_WEIGHT
            + result.performance_score * self.PERFORMANCE_WEIGHT
            + result.reliability_score * self.RELIABILITY_WEIGHT
            + result.maintainability_score * self.MAINTAINABILITY_WEIGHT
        )

        result.is_valid = result.overall_score >= 70.0

        if result.security_score < 70.0:
            result.recommendations.append("Add security measures to API design (authentication, authorization)")
        if result.performance_score < 70.0:
            result.recommendations.append("Address performance requirements in API design (caching, pagination)")

        return result

    def _validate_security(
        self, architecture: dict[str, Any], security_reqs: list[str], arch_text: str
    ) -> tuple[float, list[str]]:
        """Validate security NFRs."""
        score = 100.0
        issues = []

        if not security_reqs:
            return 80.0, []  # No security requirements = assume basic security

        # Check for authentication
        if "authentication" in " ".join(security_reqs).lower():
            if "auth" not in arch_text and "login" not in arch_text:
                score -= 30.0
                issues.append("Authentication not addressed in architecture")

        # Check for authorization
        if "authorization" in " ".join(security_reqs).lower() or "access control" in " ".join(security_reqs).lower():
            if "authorization" not in arch_text and "permission" not in arch_text and "role" not in arch_text:
                score -= 25.0
                issues.append("Authorization/access control not addressed")

        # Check for data encryption
        if "encryption" in " ".join(security_reqs).lower() or "encrypt" in " ".join(security_reqs).lower():
            if "encrypt" not in arch_text:
                score -= 20.0
                issues.append("Data encryption not specified")

        # Check for secure communication
        if "tls" in " ".join(security_reqs).lower() or "ssl" in " ".join(security_reqs).lower() or "https" in " ".join(security_reqs).lower():
            if "tls" not in arch_text and "ssl" not in arch_text and "https" not in arch_text:
                score -= 15.0
                issues.append("Secure communication (TLS/SSL) not specified")

        return max(0.0, score), issues

    def _validate_performance(
        self, architecture: dict[str, Any], performance_reqs: list[str], arch_text: str
    ) -> tuple[float, list[str]]:
        """Validate performance NFRs."""
        score = 100.0
        issues = []

        if not performance_reqs:
            return 80.0, []  # No performance requirements = assume acceptable

        perf_text = " ".join(performance_reqs).lower()

        # Check for response time requirements
        if "response time" in perf_text or "latency" in perf_text:
            if "response" not in arch_text and "latency" not in arch_text and "performance" not in arch_text:
                score -= 25.0
                issues.append("Response time/latency not addressed")

        # Check for throughput requirements
        if "throughput" in perf_text or "requests per second" in perf_text:
            if "throughput" not in arch_text and "rps" not in arch_text:
                score -= 20.0
                issues.append("Throughput requirements not addressed")

        # Check for caching strategy
        if "cache" in perf_text:
            if "cache" not in arch_text:
                score -= 15.0
                issues.append("Caching strategy not specified")

        # Check for scalability
        if "scalability" in perf_text or "scale" in perf_text:
            if "scal" not in arch_text and "scale" not in arch_text:
                score -= 20.0
                issues.append("Scalability approach not defined")

        return max(0.0, score), issues

    def _validate_reliability(
        self, architecture: dict[str, Any], reliability_reqs: list[str], arch_text: str
    ) -> tuple[float, list[str]]:
        """Validate reliability NFRs."""
        score = 100.0
        issues = []

        if not reliability_reqs:
            return 80.0, []  # No reliability requirements = assume acceptable

        rel_text = " ".join(reliability_reqs).lower()

        # Check for error handling
        if "error handling" in rel_text or "error" in rel_text:
            if "error" not in arch_text and "exception" not in arch_text:
                score -= 25.0
                issues.append("Error handling not addressed")

        # Check for availability/uptime
        if "availability" in rel_text or "uptime" in rel_text:
            if "availability" not in arch_text and "uptime" not in arch_text and "redundancy" not in arch_text:
                score -= 25.0
                issues.append("Availability/redundancy not addressed")

        # Check for backup/recovery
        if "backup" in rel_text or "recovery" in rel_text:
            if "backup" not in arch_text and "recovery" not in arch_text:
                score -= 20.0
                issues.append("Backup/recovery strategy not specified")

        return max(0.0, score), issues

    def _validate_maintainability(
        self, architecture: dict[str, Any], maintainability_reqs: list[str], arch_text: str
    ) -> tuple[float, list[str]]:
        """Validate maintainability NFRs."""
        score = 100.0
        issues = []

        if not maintainability_reqs:
            return 80.0, []  # No maintainability requirements = assume acceptable

        # Check for documentation
        if "documentation" not in arch_text and "docs" not in arch_text:
            score -= 20.0
            issues.append("Documentation not addressed")

        # Check for modularity
        if "modular" not in arch_text and "module" not in arch_text and "component" not in arch_text:
            score -= 15.0
            issues.append("Modularity not emphasized")

        # Check for code quality
        if "quality" not in arch_text and "standard" not in arch_text:
            score -= 10.0
            issues.append("Code quality standards not mentioned")

        return max(0.0, score), issues

    def _validate_api_security(
        self, api_design: dict[str, Any], security_reqs: list[str], api_text: str
    ) -> tuple[float, list[str]]:
        """Validate API security."""
        score = 100.0
        issues = []

        if not security_reqs:
            return 80.0, []

        # Check for authentication in API
        if "authentication" in " ".join(security_reqs).lower():
            endpoints = api_design.get("endpoints", [])
            has_auth = any("auth" in str(e).lower() for e in endpoints) or "auth" in api_text
            if not has_auth:
                score -= 30.0
                issues.append("API authentication not specified")

        # Check for HTTPS
        if "https" in " ".join(security_reqs).lower() or "tls" in " ".join(security_reqs).lower():
            if "https" not in api_text and "tls" not in api_text:
                score -= 20.0
                issues.append("HTTPS/TLS not specified for API")

        return max(0.0, score), issues

    def _validate_api_performance(
        self, api_design: dict[str, Any], performance_reqs: list[str], api_text: str
    ) -> tuple[float, list[str]]:
        """Validate API performance."""
        score = 100.0
        issues = []

        if not performance_reqs:
            return 80.0, []

        # Check for pagination
        if "pagination" not in api_text and "page" not in api_text:
            score -= 15.0
            issues.append("Pagination not specified for list endpoints")

        # Check for rate limiting
        if "rate limit" in " ".join(performance_reqs).lower():
            if "rate limit" not in api_text:
                score -= 20.0
                issues.append("Rate limiting not specified")

        # Check for caching headers
        if "cache" in " ".join(performance_reqs).lower():
            if "cache" not in api_text:
                score -= 15.0
                issues.append("Caching strategy not specified")

        return max(0.0, score), issues
