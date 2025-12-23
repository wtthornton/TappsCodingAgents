"""Stack analyzer for comprehensive tech stack analysis."""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class StackAnalyzer:
    """Analyzes tech stack comprehensively."""

    def analyze(self, project_root: Path) -> dict[str, Any]:
        """Analyze tech stack."""
        stack = {
            "languages": [],
            "frameworks": [],
            "libraries": [],
            "tools": [],
        }
        
        # Detect languages
        if (project_root / "requirements.txt").exists():
            stack["languages"].append("python")
        if (project_root / "package.json").exists():
            stack["languages"].append("javascript")
        
        # Detect frameworks
        if (project_root / "Dockerfile").exists():
            stack["tools"].append("docker")
        if (project_root / ".github").exists():
            stack["tools"].append("github_actions")
        
        return stack

