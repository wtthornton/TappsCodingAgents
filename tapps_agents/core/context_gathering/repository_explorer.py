"""Repository explorer for autonomous code exploration."""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RepositoryExplorer:
    """Autonomous repository exploration."""

    def explore(self, project_root: Path) -> dict[str, Any]:
        """Explore repository structure."""
        structure = {
            "modules": [],
            "packages": [],
            "layers": [],
        }
        
        # Analyze Python modules
        for py_file in project_root.rglob("*.py"):
            if "test" not in str(py_file):
                rel_path = py_file.relative_to(project_root)
                structure["modules"].append(str(rel_path))
        
        return structure

