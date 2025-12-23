"""Domain detector for automatic domain detection."""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DomainDetector:
    """Detects project domains from repository signals."""

    def detect_domains(self, project_root: Path) -> list[str]:
        """Detect domains from project structure."""
        domains = []
        
        # Detect from dependency manifests
        if (project_root / "requirements.txt").exists():
            domains.append("python")
        if (project_root / "package.json").exists():
            domains.append("javascript")
        
        # Detect from framework files
        if (project_root / "django").exists() or any(p.name == "django" for p in project_root.glob("*/settings.py")):
            domains.append("django")
        if (project_root / "react").exists() or (project_root / "src").exists() and any(p.suffix in [".tsx", ".jsx"] for p in (project_root / "src").glob("**/*")):
            domains.append("react")
        
        return list(set(domains))  # Deduplicate

