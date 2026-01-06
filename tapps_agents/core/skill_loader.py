"""
Custom Skill Loader and Registry.

Discovers, loads, and manages custom Skills alongside built-in Skills.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class SkillMetadata:
    """Metadata for a Skill with enhanced fields."""

    name: str
    path: Path
    is_builtin: bool
    is_custom: bool
    description: str | None = None
    allowed_tools: list[str] | None = None
    model_profile: str | None = None
    version: str | None = None
    # Enhanced metadata fields
    author: str | None = None
    category: str | None = None
    tags: list[str] = field(default_factory=list)


class SkillRegistry:
    """Registry for managing loaded Skills."""

    def __init__(self):
        """Initialize empty registry."""
        self._skills: dict[str, SkillMetadata] = {}
        self._builtin_skill_names: set[str] = set()

    def register_builtin_skills(self, skill_names: list[str]) -> None:
        """
        Register list of built-in Skill names.

        Args:
            skill_names: List of built-in Skill names
        """
        self._builtin_skill_names = set(skill_names)

    def register_skill(
        self, skill: SkillMetadata, priority: str = "custom"
    ) -> None:
        """
        Register a Skill in the registry.

        Args:
            skill: Skill metadata
            priority: Priority level ("custom" or "builtin")
        """
        # Custom Skills override built-in Skills with the same name
        if skill.name in self._skills:
            existing = self._skills[skill.name]
            if existing.is_builtin and skill.is_custom:
                # Custom Skill overrides built-in
                self._skills[skill.name] = skill
            elif existing.is_custom and skill.is_builtin:
                # Built-in doesn't override custom (keep existing)
                pass
            else:
                # Same type, update
                self._skills[skill.name] = skill
        else:
            self._skills[skill.name] = skill

    def get_skill(self, name: str) -> SkillMetadata | None:
        """
        Get Skill by name.

        Args:
            name: Skill name

        Returns:
            Skill metadata or None if not found
        """
        return self._skills.get(name)

    def list_skills(self, include_builtin: bool = True, include_custom: bool = True) -> list[SkillMetadata]:
        """
        List all registered Skills.

        Args:
            include_builtin: Include built-in Skills
            include_custom: Include custom Skills

        Returns:
            List of Skill metadata
        """
        skills = []
        for skill in self._skills.values():
            if skill.is_builtin and include_builtin:
                skills.append(skill)
            elif skill.is_custom and include_custom:
                skills.append(skill)
        return skills

    def get_custom_skills(self) -> list[SkillMetadata]:
        """
        Get all custom Skills.

        Returns:
            List of custom Skill metadata
        """
        return [skill for skill in self._skills.values() if skill.is_custom]

    def get_builtin_skills(self) -> list[SkillMetadata]:
        """
        Get all built-in Skills.

        Returns:
            List of built-in Skill metadata
        """
        return [skill for skill in self._skills.values() if skill.is_builtin]

    def has_skill(self, name: str) -> bool:
        """
        Check if Skill is registered.

        Args:
            name: Skill name

        Returns:
            True if Skill is registered
        """
        return name in self._skills

    def get_conflicts(self) -> list[tuple[str, SkillMetadata, SkillMetadata]]:
        """
        Get name conflicts between custom and built-in Skills.

        Returns:
            List of tuples (name, custom_skill, builtin_skill)
        """
        conflicts = []
        custom_skills = {s.name: s for s in self.get_custom_skills()}
        builtin_skills = {s.name: s for s in self.get_builtin_skills()}

        for name in custom_skills:
            if name in builtin_skills:
                conflicts.append((name, custom_skills[name], builtin_skills[name]))

        return conflicts


class CustomSkillLoader:
    """Loader for discovering and loading custom Skills."""

    def __init__(self, project_root: Path | None = None):
        """
        Initialize loader.

        Args:
            project_root: Project root directory (defaults to current directory)
        """
        if project_root is None:
            project_root = Path.cwd()
        self.project_root = project_root
        self.skills_dir = project_root / ".claude" / "skills"

    def get_builtin_skill_names(self) -> list[str]:
        """
        Get list of built-in Skill names from framework.

        Returns:
            List of built-in Skill names
        """
        # Try to get from packaged resources
        from .init_project import _resource_at

        packaged_skills = _resource_at("claude", "skills")
        if packaged_skills is not None and packaged_skills.is_dir():
            skill_names = [
                skill_dir.name
                for skill_dir in packaged_skills.iterdir()
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists()
            ]
            return skill_names

        # Fallback: try framework source directory
        current_file = Path(__file__)
        framework_root = current_file.parent.parent.parent
        source_skills_dir = framework_root / ".claude" / "skills"

        if source_skills_dir.exists():
            skill_names = [
                skill_dir.name
                for skill_dir in source_skills_dir.iterdir()
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists()
            ]
            return skill_names

        return []

    def discover_custom_skills(self) -> list[Path]:
        """
        Discover custom Skills in project's .claude/skills/ directory.

        Returns:
            List of paths to custom Skill directories
        """
        if not self.skills_dir.exists():
            return []

        custom_skills = []
        builtin_names = set(self.get_builtin_skill_names())

        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue

            # Check if this is a custom Skill (not in built-in list)
            if skill_dir.name not in builtin_names:
                custom_skills.append(skill_dir)

        return custom_skills

    def _get_package_skills_dir(self) -> Path:
        """Get package skills directory (SYSTEM scope).
        
        Returns:
            Path to package skills directory
        """
        from .init_project import _resource_at
        
        packaged_skills = _resource_at("claude", "skills")
        if packaged_skills is not None and packaged_skills.is_dir():
            return packaged_skills
        
        # Fallback: framework source directory
        current_file = Path(__file__)
        framework_root = current_file.parent.parent.parent
        return framework_root / "tapps_agents" / "resources" / "claude" / "skills"

    def _find_git_root(self, start_path: Path) -> Path:
        """Find git root directory starting from start_path.
        
        Args:
            start_path: Starting directory path
            
        Returns:
            Git root directory, or start_path if not in git repo
        """
        current = start_path.resolve()
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent
        return start_path

    def discover_skills_multi_scope(self, project_root: Path) -> list[SkillMetadata]:
        """Discover skills from multiple scopes with precedence.
        
        Scopes (in order of precedence):
        1. REPO (current): project_root/.claude/skills/
        2. REPO (parent): project_root/../.claude/skills/
        3. REPO (git root): git_root/.claude/skills/
        4. USER: ~/.tapps-agents/skills/
        5. SYSTEM: package_skills_dir/
        
        Precedence: REPO > USER > SYSTEM (first scope wins)
        
        Args:
            project_root: Project root directory
            
        Returns:
            List of discovered Skill metadata
        """
        git_root = self._find_git_root(project_root)
        
        scopes = [
            # REPO scopes (highest priority)
            project_root / ".claude" / "skills",
            project_root.parent / ".claude" / "skills",
            git_root / ".claude" / "skills",
            
            # USER scope (personal skills)
            Path.home() / ".tapps-agents" / "skills",
            
            # SYSTEM scope (built-in, lowest priority)
            self._get_package_skills_dir(),
        ]
        
        discovered_skills = {}
        for scope in scopes:
            if scope.exists() and scope.is_dir():
                for skill_dir in scope.iterdir():
                    if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                        # REPO skills override USER/SYSTEM
                        if skill_dir.name not in discovered_skills:
                            metadata = self.parse_skill_metadata(skill_dir)
                            if metadata:
                                discovered_skills[skill_dir.name] = metadata
        
        return list(discovered_skills.values())

    def parse_skill_metadata(self, skill_dir: Path) -> SkillMetadata | None:
        """
        Parse Skill metadata from SKILL.md file using progressive disclosure.
        
        Only reads first 2KB of SKILL.md (enough for YAML frontmatter).
        Full content is loaded by Cursor when skill is invoked.

        Args:
            skill_dir: Path to Skill directory

        Returns:
            Skill metadata or None if parsing fails
        """
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            return None

        try:
            # PROGRESSIVE DISCLOSURE: Read only first 2KB
            # Frontmatter is always at top, typically <500 bytes
            content = skill_file.read_text(encoding="utf-8")[:2048]

            # Parse YAML frontmatter
            frontmatter_match = re.match(
                r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL
            )
            if not frontmatter_match:
                return None

            frontmatter_text = frontmatter_match.group(1)
            metadata = yaml.safe_load(frontmatter_text)

            if not isinstance(metadata, dict):
                return None

            # Extract metadata (existing + enhanced fields)
            name = metadata.get("name", skill_dir.name)
            description = metadata.get("description")
            version = metadata.get("version")
            author = metadata.get("author")
            category = metadata.get("category")
            tags = metadata.get("tags", [])
            if isinstance(tags, str):
                # Parse comma-separated string
                tags = [tag.strip() for tag in tags.split(",")]
            
            allowed_tools = metadata.get("allowed-tools")
            if isinstance(allowed_tools, str):
                # Parse comma-separated string
                allowed_tools = [tool.strip() for tool in allowed_tools.split(",")]
            model_profile = metadata.get("model_profile")

            # Determine if built-in or custom
            builtin_names = set(self.get_builtin_skill_names())
            is_builtin = name in builtin_names or skill_dir.name in builtin_names
            is_custom = not is_builtin

            return SkillMetadata(
                name=name,
                path=skill_dir,
                is_builtin=is_builtin,
                is_custom=is_custom,
                description=description,
                version=version,
                author=author,
                category=category,
                tags=tags,
                allowed_tools=allowed_tools,
                model_profile=model_profile,
            )
        except Exception:
            # Parsing failed, return None
            return None

    def load_custom_skills(self, validate: bool = True) -> list[SkillMetadata]:
        """
        Discover and load all custom Skills.

        Args:
            validate: If True, validate Skills before loading (default: True)

        Returns:
            List of custom Skill metadata
        """
        from .skill_validator import SkillValidator

        custom_skill_dirs = self.discover_custom_skills()
        skills = []

        validator = SkillValidator(project_root=self.project_root) if validate else None

        for skill_dir in custom_skill_dirs:
            # Validate if requested
            if validator:
                validation_result = validator.validate_skill(skill_dir)
                if validation_result.has_errors():
                    # Skip invalid Skills but log warning
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"Skipping invalid Skill '{skill_dir.name}': "
                        f"{validation_result.get_error_summary()}"
                    )
                    continue

            metadata = self.parse_skill_metadata(skill_dir)
            if metadata:
                skills.append(metadata)

        return skills

    def load_all_skills(self) -> list[SkillMetadata]:
        """
        Load both built-in and custom Skills.

        Returns:
            List of all Skill metadata
        """
        all_skills = []

        # Load built-in Skills
        builtin_names = self.get_builtin_skill_names()
        for skill_name in builtin_names:
            skill_dir = self.skills_dir / skill_name
            if skill_dir.exists() and (skill_dir / "SKILL.md").exists():
                metadata = self.parse_skill_metadata(skill_dir)
                if metadata:
                    all_skills.append(metadata)

        # Load custom Skills
        custom_skills = self.load_custom_skills()
        all_skills.extend(custom_skills)

        return all_skills


# Global registry instance
_global_registry: SkillRegistry | None = None


def get_skill_registry() -> SkillRegistry:
    """
    Get global Skill registry instance.

    Returns:
        Global Skill registry
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = SkillRegistry()
    return _global_registry


def initialize_skill_registry(project_root: Path | None = None) -> SkillRegistry:
    """
    Initialize Skill registry with multi-scope discovery.

    Args:
        project_root: Project root directory (defaults to current directory)

    Returns:
        Initialized Skill registry
    """
    registry = get_skill_registry()
    loader = CustomSkillLoader(project_root=project_root)

    # Register built-in Skill names (for is_builtin detection)
    builtin_names = loader.get_builtin_skill_names()
    registry.register_builtin_skills(builtin_names)

    # Use multi-scope discovery instead of load_all_skills()
    if project_root is None:
        project_root = Path.cwd()
    all_skills = loader.discover_skills_multi_scope(project_root)

    # Register all discovered skills
    for skill in all_skills:
        priority = "custom" if skill.is_custom else "builtin"
        registry.register_skill(skill, priority=priority)

    return registry

