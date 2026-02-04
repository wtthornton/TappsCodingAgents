"""
Design Pattern Library - Catalog of design patterns with recommendations.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DesignPattern:
    """A design pattern definition."""

    name: str
    category: str  # "creational", "structural", "behavioral", "architectural"
    description: str
    use_cases: list[str] = field(default_factory=list)
    benefits: list[str] = field(default_factory=list)
    drawbacks: list[str] = field(default_factory=list)
    when_to_use: list[str] = field(default_factory=list)
    when_not_to_use: list[str] = field(default_factory=list)
    related_patterns: list[str] = field(default_factory=list)


class DesignPatternLibrary:
    """Library of design patterns with recommendation engine."""

    def __init__(self):
        """Initialize pattern library with common patterns."""
        self.patterns: dict[str, DesignPattern] = {}
        self._initialize_patterns()

    def _initialize_patterns(self):
        """Initialize common design patterns."""
        # Architectural Patterns
        self.patterns["layered"] = DesignPattern(
            name="Layered Architecture",
            category="architectural",
            description="Organizes system into horizontal layers with clear separation of concerns",
            use_cases=["Enterprise applications", "Business applications", "Traditional web apps"],
            benefits=["Clear separation of concerns", "Easy to understand", "Testable"],
            drawbacks=["Can lead to performance issues", "May create unnecessary layers"],
            when_to_use=["Complex business logic", "Need clear separation", "Team familiarity"],
            when_not_to_use=["Simple applications", "Performance-critical systems"],
            related_patterns=["microservices", "hexagonal"],
        )

        self.patterns["microservices"] = DesignPattern(
            name="Microservices",
            category="architectural",
            description="Decomposes application into small, independent services",
            use_cases=["Large scale applications", "Multiple teams", "Independent scaling"],
            benefits=["Independent deployment", "Technology diversity", "Scalability"],
            drawbacks=["Complexity", "Network latency", "Data consistency"],
            when_to_use=["Large teams", "Need independent scaling", "Different tech stacks"],
            when_not_to_use=["Small applications", "Tight coupling required"],
            related_patterns=["api-gateway", "service-mesh"],
        )

        self.patterns["mvc"] = DesignPattern(
            name="Model-View-Controller",
            category="architectural",
            description="Separates application into Model (data), View (UI), Controller (logic)",
            use_cases=["Web applications", "Desktop applications", "User interfaces"],
            benefits=["Separation of concerns", "Reusability", "Testability"],
            drawbacks=["Can become complex", "Tight coupling in some implementations"],
            when_to_use=["User interface applications", "Need separation of UI and logic"],
            when_not_to_use=["API-only applications", "Simple CRUD apps"],
        )

        # Structural Patterns
        self.patterns["repository"] = DesignPattern(
            name="Repository Pattern",
            category="structural",
            description="Abstracts data access layer, provides collection-like interface",
            use_cases=["Data access abstraction", "Testing", "Multiple data sources"],
            benefits=["Testability", "Flexibility", "Separation of concerns"],
            drawbacks=["Additional abstraction layer", "Can be overkill for simple cases"],
            when_to_use=["Need to abstract data access", "Multiple data sources", "Testing"],
            when_not_to_use=["Simple CRUD", "Direct database access sufficient"],
        )

        self.patterns["factory"] = DesignPattern(
            name="Factory Pattern",
            category="creational",
            description="Creates objects without specifying exact class",
            use_cases=["Object creation", "Dependency injection", "Polymorphism"],
            benefits=["Flexibility", "Extensibility", "Decoupling"],
            drawbacks=["Complexity", "Additional classes"],
            when_to_use=["Multiple object types", "Runtime object creation", "Extensibility"],
            when_not_to_use=["Simple object creation", "Fixed object types"],
        )

        # Behavioral Patterns
        self.patterns["strategy"] = DesignPattern(
            name="Strategy Pattern",
            category="behavioral",
            description="Defines family of algorithms, makes them interchangeable",
            use_cases=["Multiple algorithms", "Runtime algorithm selection", "Extensibility"],
            benefits=["Flexibility", "Extensibility", "Testability"],
            drawbacks=["Additional classes", "Complexity"],
            when_to_use=["Multiple ways to do something", "Need to switch algorithms"],
            when_not_to_use=["Single algorithm", "Simple logic"],
        )

    def suggest_patterns(self, requirements: dict[str, Any], context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """
        Suggest design patterns based on requirements and context.

        Args:
            requirements: Requirements dict
            context: Optional context (existing architecture, team size, etc.)

        Returns:
            List of suggested patterns with scores
        """
        suggestions = []

        req_text = str(requirements).lower()
        context_text = str(context).lower() if context else ""

        # Score each pattern
        for pattern_name, pattern in self.patterns.items():
            score = 0.0
            reasons = []

            # Check use cases
            for use_case in pattern.use_cases:
                if use_case.lower() in req_text or use_case.lower() in context_text:
                    score += 20.0
                    reasons.append(f"Matches use case: {use_case}")

            # Check when_to_use criteria
            for criterion in pattern.when_to_use:
                if criterion.lower() in req_text or criterion.lower() in context_text:
                    score += 15.0
                    reasons.append(f"Applies: {criterion}")

            # Check when_not_to_use (negative scoring)
            for criterion in pattern.when_not_to_use:
                if criterion.lower() in req_text or criterion.lower() in context_text:
                    score -= 30.0
                    reasons.append(f"Not recommended: {criterion}")

            # Check pattern name/keywords in requirements
            if pattern.name.lower() in req_text:
                score += 25.0
                reasons.append("Pattern explicitly mentioned")

            if score > 0:
                suggestions.append(
                    {
                        "pattern": pattern_name,
                        "name": pattern.name,
                        "category": pattern.category,
                        "score": score,
                        "reasons": reasons,
                        "description": pattern.description,
                        "benefits": pattern.benefits,
                        "drawbacks": pattern.drawbacks,
                    }
                )

        # Sort by score (descending)
        suggestions.sort(key=lambda x: x["score"], reverse=True)

        return suggestions[:5]  # Top 5 suggestions

    def check_pattern_compliance(self, architecture: dict[str, Any], pattern_name: str) -> dict[str, Any]:
        """
        Check if architecture complies with a design pattern.

        Args:
            architecture: Architecture document
            pattern_name: Name of pattern to check

        Returns:
            Compliance report
        """
        pattern = self.patterns.get(pattern_name)
        if not pattern:
            return {"error": f"Pattern not found: {pattern_name}"}

        str(architecture).lower()
        compliance_score = 100.0
        violations = []
        matches = []

        # Pattern-specific compliance checks
        if pattern_name == "layered":
            layers = architecture.get("layers", [])
            if not layers:
                compliance_score -= 50.0
                violations.append("No layers defined")
            else:
                matches.append(f"Has {len(layers)} layers")

        elif pattern_name == "microservices":
            services = architecture.get("services", [])
            if not services:
                compliance_score -= 50.0
                violations.append("No services defined")
            else:
                matches.append(f"Has {len(services)} services")

        elif pattern_name == "mvc":
            components = architecture.get("components", [])
            component_names = [c.get("name", "").lower() if isinstance(c, dict) else str(c).lower() for c in components]
            has_model = any("model" in name for name in component_names)
            has_view = any("view" in name for name in component_names)
            has_controller = any("controller" in name for name in component_names)

            if not has_model:
                compliance_score -= 33.0
                violations.append("Missing Model component")
            else:
                matches.append("Has Model component")

            if not has_view:
                compliance_score -= 33.0
                violations.append("Missing View component")
            else:
                matches.append("Has View component")

            if not has_controller:
                compliance_score -= 34.0
                violations.append("Missing Controller component")
            else:
                matches.append("Has Controller component")

        return {
            "pattern": pattern_name,
            "compliance_score": max(0.0, compliance_score),
            "is_compliant": compliance_score >= 70.0,
            "violations": violations,
            "matches": matches,
            "pattern_description": pattern.description,
        }

    def get_pattern(self, pattern_name: str) -> DesignPattern | None:
        """Get pattern by name."""
        return self.patterns.get(pattern_name)

    def list_patterns(self, category: str | None = None) -> list[DesignPattern]:
        """List all patterns, optionally filtered by category."""
        if category:
            return [p for p in self.patterns.values() if p.category == category]
        return list(self.patterns.values())
