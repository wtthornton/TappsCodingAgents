"""Generator modules for TappsCodingAgents.

This package contains modules for auto-generating configuration:
- Expert generation from knowledge files
- Project overview generation from metadata and architecture
- Configuration templates
- Project scaffolding
"""

from tapps_agents.core.generators.expert_generator import (
    ExpertConfig,
    ExpertGenerator,
    KnowledgeFileAnalysis,
)
from tapps_agents.core.generators.project_overview_generator import (
    ArchitecturePattern,
    ArchitectureType,
    ComponentMap,
    ProjectMetadata,
    ProjectOverviewGenerator,
)

__all__ = [
    "ArchitecturePattern",
    "ArchitectureType",
    "ComponentMap",
    "ExpertConfig",
    "ExpertGenerator",
    "KnowledgeFileAnalysis",
    "ProjectMetadata",
    "ProjectOverviewGenerator",
]
