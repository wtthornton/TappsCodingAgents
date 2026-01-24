"""
Adaptive Domain Detector

Detects new domains from user prompts, code patterns, and expert consultation gaps.
This extends the existing DomainStackDetector to support adaptive learning.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .domain_detector import DomainStackDetector, RepoSignal


@dataclass
class DomainSuggestion:
    """Suggestion for a new domain requiring expert knowledge."""

    domain: str
    confidence: float  # 0.0-1.0
    source: str  # "prompt", "code_pattern", "consultation_gap", "recurring_pattern"
    evidence: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    priority: str = "normal"  # "low", "normal", "high", "critical"
    usage_frequency: int = 0  # Times detected in tracking period


class AdaptiveDomainDetector:
    """
    Detects new domains requiring expert knowledge from multiple sources.
    
    Extends DomainStackDetector with adaptive learning capabilities:
    - Prompt analysis for domain keywords
    - Code pattern detection
    - Expert consultation gap analysis
    - Recurring pattern identification
    """

    # Domain keyword patterns for prompt analysis
    DOMAIN_KEYWORDS = {
        "oauth2": ["oauth2", "oauth", "refresh token", "access token", "token refresh"],
        "oauth2-refresh-tokens": [
            "oauth2 refresh",
            "refresh token",
            "token expiry",
            "access token refresh",
            "zoho-oauthtoken",
        ],
        "api-clients": [
            "api client",
            "http client",
            "rest client",
            "external api",
            "third-party api",
        ],
        "graphql": ["graphql", "gql", "graph query"],
        "microservices": ["microservice", "service mesh", "service-to-service"],
        "event-driven": ["event bus", "event stream", "pub/sub", "message queue"],
        "websocket": ["websocket", "ws", "real-time", "socket.io"],
        "mqtt": ["mqtt", "iot protocol", "message queue telemetry"],
        "grpc": ["grpc", "rpc", "protobuf"],
        "serverless": ["serverless", "lambda", "function as a service", "faas"],
        "kubernetes": ["kubernetes", "k8s", "pod", "deployment", "service"],
        "docker": ["docker", "container", "dockerfile", "docker-compose"],
        "ci-cd": ["ci/cd", "continuous integration", "pipeline", "deployment"],
        "monitoring": ["monitoring", "observability", "metrics", "logging", "tracing"],
        "authentication": [
            "authentication",
            "auth",
            "login",
            "session",
            "jwt",
            "bearer token",
        ],
        "authorization": ["authorization", "permissions", "rbac", "acl"],
        "database": ["database", "sql", "nosql", "orm", "migration"],
        "caching": ["cache", "redis", "memcached", "caching strategy"],
        "search": ["search", "elasticsearch", "lucene", "full-text search"],
        "queue": ["queue", "rabbitmq", "kafka", "message queue"],
    }

    # Code pattern indicators
    CODE_PATTERNS = {
        "oauth2-refresh-tokens": [
            r"refresh_token",
            r"access_token",
            r"token_url",
            r"expires_in",
            r"Zoho-oauthtoken",
            r"Bearer\s+token",
        ],
        "api-clients": [
            r"class\s+\w+Client",
            r"requests\.(get|post|put|delete)",
            r"httpx\.(Client|AsyncClient)",
            r"api_base_url",
            r"Authorization:\s*",
        ],
        "websocket": [
            r"websocket",
            r"WebSocket",
            r"socket\.io",
            r"ws://",
            r"wss://",
        ],
        "mqtt": [
            r"mqtt",
            r"MQTT",
            r"paho-mqtt",
            r"publish",
            r"subscribe",
        ],
        "database": [
            r"CREATE TABLE",
            r"SELECT.*FROM",
            r"ORM",
            r"migration",
            r"schema",
        ],
    }

    def __init__(self, project_root: Path | None = None):
        """
        Initialize adaptive domain detector.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or Path.cwd()
        self.stack_detector = DomainStackDetector(project_root=project_root)

    async def detect_domains(
        self,
        prompt: str | None = None,
        code_context: str | None = None,
        consultation_history: list[dict] | None = None,
    ) -> list[DomainSuggestion]:
        """
        Detect potential new domains from multiple sources.

        Args:
            prompt: User prompt text
            code_context: Code snippet or file content
            consultation_history: History of expert consultations with confidence scores

        Returns:
            List of domain suggestions sorted by confidence
        """
        suggestions: dict[str, DomainSuggestion] = {}

        # 1. Detect from prompt keywords
        if prompt:
            prompt_suggestions = self._detect_from_prompt(prompt)
            for suggestion in prompt_suggestions:
                domain = suggestion.domain
                if domain not in suggestions:
                    suggestions[domain] = suggestion
                else:
                    # Merge evidence and increase confidence
                    suggestions[domain].evidence.extend(suggestion.evidence)
                    suggestions[domain].confidence = max(
                        suggestions[domain].confidence, suggestion.confidence
                    )
                    suggestions[domain].keywords.extend(suggestion.keywords)

        # 2. Detect from code patterns
        if code_context:
            code_suggestions = self._detect_from_code_patterns(code_context)
            for suggestion in code_suggestions:
                domain = suggestion.domain
                if domain not in suggestions:
                    suggestions[domain] = suggestion
                else:
                    suggestions[domain].evidence.extend(suggestion.evidence)
                    suggestions[domain].confidence = max(
                        suggestions[domain].confidence, suggestion.confidence
                    )

        # 3. Detect from consultation gaps (low confidence consultations)
        if consultation_history:
            gap_suggestions = self._detect_from_consultation_gaps(consultation_history)
            for suggestion in gap_suggestions:
                domain = suggestion.domain
                if domain not in suggestions:
                    suggestions[domain] = suggestion
                else:
                    suggestions[domain].evidence.extend(suggestion.evidence)
                    suggestions[domain].confidence = max(
                        suggestions[domain].confidence, suggestion.confidence
                    )
                    suggestions[domain].priority = "high"  # Gaps are high priority

        # 4. Check against existing domains (filter out known domains)
        existing_domains = self._get_existing_domains()
        filtered_suggestions = [
            s for s in suggestions.values() if s.domain not in existing_domains
        ]

        # Sort by confidence and priority
        filtered_suggestions.sort(
            key=lambda s: (
                {"critical": 3, "high": 2, "normal": 1, "low": 0}[s.priority],
                s.confidence,
            ),
            reverse=True,
        )

        return filtered_suggestions

    def _detect_from_prompt(self, prompt: str) -> list[DomainSuggestion]:
        """Detect domains from prompt keywords."""
        suggestions = []
        prompt_lower = prompt.lower()

        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            matches = [kw for kw in keywords if kw.lower() in prompt_lower]
            if matches:
                confidence = min(0.9, 0.5 + len(matches) * 0.1)
                suggestions.append(
                    DomainSuggestion(
                        domain=domain,
                        confidence=confidence,
                        source="prompt",
                        evidence=[f"Found keywords: {', '.join(matches)}"],
                        keywords=matches,
                        priority="high" if len(matches) >= 2 else "normal",
                    )
                )

        return suggestions

    def _detect_from_code_patterns(self, code: str) -> list[DomainSuggestion]:
        """Detect domains from code patterns."""
        suggestions = []

        for domain, patterns in self.CODE_PATTERNS.items():
            matches = []
            for pattern in patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    matches.append(pattern)

            if matches:
                confidence = min(0.85, 0.4 + len(matches) * 0.15)
                suggestions.append(
                    DomainSuggestion(
                        domain=domain,
                        confidence=confidence,
                        source="code_pattern",
                        evidence=[f"Found patterns: {', '.join(matches[:3])}"],
                        keywords=matches[:5],
                        priority="high" if len(matches) >= 2 else "normal",
                    )
                )

        return suggestions

    def _detect_from_consultation_gaps(
        self, consultation_history: list[dict]
    ) -> list[DomainSuggestion]:
        """Detect domains from low-confidence expert consultations."""
        suggestions = []
        low_confidence_threshold = 0.6

        for consultation in consultation_history:
            domain = consultation.get("domain", "")
            confidence = consultation.get("confidence", 1.0)
            query = consultation.get("query", "")

            if confidence < low_confidence_threshold and domain:
                # Extract potential domain from query
                query_lower = query.lower()
                detected_domain = None

                # Try to infer domain from query
                for known_domain, keywords in self.DOMAIN_KEYWORDS.items():
                    if any(kw in query_lower for kw in keywords):
                        detected_domain = known_domain
                        break

                if detected_domain:
                    suggestions.append(
                        DomainSuggestion(
                            domain=detected_domain,
                            confidence=0.7,  # Medium confidence for gaps
                            source="consultation_gap",
                            evidence=[
                                f"Low confidence ({confidence:.2f}) consultation for domain: {domain}",
                                f"Query: {query[:100]}",
                            ],
                            priority="high",
                        )
                    )

        return suggestions

    def _get_existing_domains(self) -> set[str]:
        """Get list of existing domains from expert registry."""
        existing = set()

        # Check built-in domains
        from .builtin_registry import BuiltinExpertRegistry

        existing.update(BuiltinExpertRegistry.TECHNICAL_DOMAINS)

        # Check project-defined domains
        domains_file = self.project_root / ".tapps-agents" / "domains.md"
        if domains_file.exists():
            try:
                from .domain_config import DomainConfigParser

                domain_config = DomainConfigParser.parse(domains_file)
                existing.update(domain_config.get_domain_names())
            except Exception:
                pass

        return existing

    async def detect_recurring_patterns(
        self, detection_history: list[DomainSuggestion]
    ) -> list[DomainSuggestion]:
        """
        Identify recurring patterns that suggest missing expertise.

        Args:
            detection_history: Historical domain detections

        Returns:
            Domain suggestions for recurring patterns
        """
        # Count domain occurrences
        domain_counts: dict[str, int] = {}
        for detection in detection_history:
            domain_counts[detection.domain] = domain_counts.get(detection.domain, 0) + 1

        # Suggest domains that appear frequently
        suggestions = []
        for domain, count in domain_counts.items():
            if count >= 3:  # Appeared 3+ times
                suggestions.append(
                    DomainSuggestion(
                        domain=domain,
                        confidence=min(0.9, 0.6 + count * 0.1),
                        source="recurring_pattern",
                        evidence=[f"Detected {count} times in recent history"],
                        priority="high" if count >= 5 else "normal",
                        usage_frequency=count,
                    )
                )

        return suggestions
