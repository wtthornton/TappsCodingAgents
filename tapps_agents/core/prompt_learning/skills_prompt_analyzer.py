"""Analyzer for Cursor Skills prompt learning."""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SkillsPromptAnalyzer:
    """Analyzes Skills system prompts for learning."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self.skills_dir = self.project_root / ".claude" / "skills"

    def analyze_skills(self) -> dict[str, Any]:
        """Analyze all Skills prompts."""
        if not self.skills_dir.exists():
            return {}
        
        skills_data = {}
        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    content = skill_md.read_text(encoding="utf-8")
                    skills_data[skill_dir.name] = {
                        "path": str(skill_md),
                        "content": content,
                        "length": len(content),
                    }
        
        return skills_data

