"""Generator modules for TappsCodingAgents.

This package contains modules for auto-generating configuration:
- Expert generation from knowledge files
- Project overview generation from metadata and architecture
- Configuration templates
- Project scaffolding
"""

from tapps_agents.core.generators.expert_generator import (
    ExpertGenerator,
    KnowledgeFileAnalysis,
    ExpertConfig,
)
from tapps_agents.core.generators.project_overview_generator import (
    ProjectOverviewGenerator,
    ProjectMetadata,
    ArchitecturePattern,
    ArchitectureType,
    ComponentMap,
)

__all__ = [
    "ExpertGenerator",
    "KnowledgeFileAnalysis",
    "ExpertConfig",
    "ProjectOverviewGenerator",
    "ProjectMetadata",
    "ArchitecturePattern",
    "ArchitectureType",
    "ComponentMap",
]
