"""
Tech Stack to Expert Priority Mapping

Maps detected technology stacks to expert priorities, enabling automatic
prioritization of relevant experts based on the project's tech stack.

Priority values range from 0.0 to 1.0, where:
- 1.0 = Highest priority (most relevant for this stack)
- 0.0 = No priority (expert not relevant)
"""


# Type definition for expert priorities: expert_id -> priority (0.0-1.0)
ExpertPriorities = dict[str, float]


# Default priority mappings for common tech stacks
# Each framework maps to a dictionary of expert_id -> priority
FRAMEWORK_PRIORITY_MAPPINGS: dict[str, ExpertPriorities] = {
    "FastAPI": {
        # API Design is most critical for FastAPI projects
        "expert-api-design": 1.0,
        # Observability is very important for API services
        "expert-observability": 0.9,
        # Performance matters for API endpoints
        "expert-performance": 0.8,
        # Security is important for APIs
        "expert-security": 0.7,
        # Database design relevant for backend services
        "expert-database": 0.6,
        # Architecture matters but secondary
        "expert-software-architecture": 0.5,
    },
    "Django": {
        # Web Framework expertise is most critical
        "expert-software-architecture": 1.0,  # Web framework patterns
        # Database management is very important
        "expert-database": 0.9,
        # Security is crucial for web apps
        "expert-security": 0.8,
        # Performance optimization matters
        "expert-performance": 0.7,
        # Testing strategies important
        "expert-testing": 0.6,
        # API design if using Django REST
        "expert-api-design": 0.5,
    },
    "React": {
        # Frontend expertise is most critical
        "expert-user-experience": 1.0,
        # UX design is very important
        "expert-software-architecture": 0.9,  # Frontend architecture patterns
        # Performance matters for client-side apps
        "expert-performance": 0.8,
        # Accessibility is important for web apps
        "expert-accessibility": 0.7,
        # Testing frontend code
        "expert-testing": 0.6,
    },
    "Next.js": {
        # Fullstack expertise most critical (Next.js is fullstack)
        "expert-software-architecture": 1.0,  # Fullstack architecture
        # Frontend UX still very important
        "expert-user-experience": 0.9,
        # Performance critical for Next.js apps
        "expert-performance": 0.8,
        # API design if using API routes
        "expert-api-design": 0.7,
        # Observability for server-side rendering
        "expert-observability": 0.6,
        # Accessibility
        "expert-accessibility": 0.5,
    },
    "NestJS": {
        # API Design is most critical (NestJS is API framework)
        "expert-api-design": 1.0,
        # Architecture patterns important (NestJS has strong patterns)
        "expert-software-architecture": 0.9,
        # Observability for enterprise APIs
        "expert-observability": 0.8,
        # Security important for APIs
        "expert-security": 0.7,
        # Performance optimization
        "expert-performance": 0.6,
        # Database integration
        "expert-database": 0.5,
    },
}


def get_priority_for_framework(framework: str) -> ExpertPriorities:
    """
    Get expert priorities for a detected framework.

    Args:
        framework: Framework name (e.g., "FastAPI", "React", "Next.js")

    Returns:
        Dictionary mapping expert_id to priority (0.0-1.0).
        Returns empty dict if framework not found.

    Examples:
        >>> priorities = get_priority_for_framework("FastAPI")
        >>> priorities["expert-api-design"]
        1.0

        >>> priorities = get_priority_for_framework("UnknownFramework")
        >>> priorities
        {}
    """
    # Case-insensitive lookup
    framework_normalized = framework.strip()
    
    # Try exact match first
    if framework_normalized in FRAMEWORK_PRIORITY_MAPPINGS:
        return FRAMEWORK_PRIORITY_MAPPINGS[framework_normalized].copy()
    
    # Try case-insensitive match
    for key, priorities in FRAMEWORK_PRIORITY_MAPPINGS.items():
        if key.lower() == framework_normalized.lower():
            return priorities.copy()
    
    # Framework not found - return empty priorities
    return {}


def get_priorities_for_frameworks(frameworks: list[str]) -> ExpertPriorities:
    """
    Get combined expert priorities for multiple frameworks.

    When multiple frameworks are detected, priorities are combined by taking
    the maximum priority for each expert across all frameworks.

    Args:
        frameworks: List of framework names

    Returns:
        Dictionary mapping expert_id to priority (0.0-1.0), combined from all frameworks.

    Examples:
        >>> priorities = get_priorities_for_frameworks(["FastAPI", "React"])
        >>> # Combines priorities from both frameworks
    """
    if not frameworks:
        return {}
    
    combined: ExpertPriorities = {}
    
    for framework in frameworks:
        framework_priorities = get_priority_for_framework(framework)
        for expert_id, priority in framework_priorities.items():
            # Take maximum priority if expert appears in multiple frameworks
            if expert_id not in combined or priority > combined[expert_id]:
                combined[expert_id] = priority
    
    return combined


def get_supported_frameworks() -> list[str]:
    """
    Get list of all supported frameworks with priority mappings.

    Returns:
        List of framework names that have priority mappings defined.
    """
    return list(FRAMEWORK_PRIORITY_MAPPINGS.keys())


def normalize_framework_name(framework: str) -> str | None:
    """
    Normalize framework name to match mapping keys.

    Args:
        framework: Framework name (potentially with variations)

    Returns:
        Normalized framework name if found, None otherwise.

    Examples:
        >>> normalize_framework_name("fastapi")
        "FastAPI"
        >>> normalize_framework_name("React.js")
        "React"
    """
    framework_normalized = framework.strip()
    
    # Empty string should return None
    if not framework_normalized:
        return None
    
    # Try exact match
    if framework_normalized in FRAMEWORK_PRIORITY_MAPPINGS:
        return framework_normalized
    
    # Try case-insensitive match
    for key in FRAMEWORK_PRIORITY_MAPPINGS.keys():
        if key.lower() == framework_normalized.lower():
            return key
    
    # Try partial match (e.g., "React.js" -> "React")
    # Only if framework_normalized is not empty
    framework_lower = framework_normalized.lower()
    for key in FRAMEWORK_PRIORITY_MAPPINGS.keys():
        if key.lower() in framework_lower or framework_lower in key.lower():
            return key
    
    return None

