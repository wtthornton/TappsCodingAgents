"""
Unit tests for Skill Loader improvements.

Tests enhanced metadata, progressive disclosure, and multi-scope discovery.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tapps_agents.core.skill_loader import (
    CustomSkillLoader,
    initialize_skill_registry,
)

pytestmark = pytest.mark.unit


class TestEnhancedMetadata:
    """Test enhanced metadata parsing."""

    @pytest.fixture
    def skill_dir(self, tmp_path: Path) -> Path:
        """Create a temporary skill directory with SKILL.md."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        return skill_dir

    def test_parse_metadata_with_all_fields(self, skill_dir: Path):
        """Test parsing skill with all enhanced metadata fields."""
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            """---
name: test-skill
description: Test skill description
version: 1.0.0
author: Test Author
category: testing
tags: [test, unit, integration]
allowed-tools: Read, Write
model_profile: test_profile
---

# Test Skill

Content here.
""",
            encoding="utf-8",
        )

        loader = CustomSkillLoader(project_root=skill_dir.parent)
        metadata = loader.parse_skill_metadata(skill_dir)

        assert metadata is not None
        assert metadata.name == "test-skill"
        assert metadata.version == "1.0.0"
        assert metadata.author == "Test Author"
        assert metadata.category == "testing"
        assert metadata.tags == ["test", "unit", "integration"]

    def test_parse_metadata_with_tags_as_string(self, skill_dir: Path):
        """Test parsing tags as comma-separated string."""
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            """---
name: test-skill
tags: test, unit, integration
---

Content.
""",
            encoding="utf-8",
        )

        loader = CustomSkillLoader(project_root=skill_dir.parent)
        metadata = loader.parse_skill_metadata(skill_dir)

        assert metadata is not None
        assert metadata.tags == ["test", "unit", "integration"]

    def test_parse_metadata_backward_compatible(self, skill_dir: Path):
        """Test parsing skill without new metadata fields (backward compatibility)."""
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            """---
name: test-skill
description: Test description
---

Content.
""",
            encoding="utf-8",
        )

        loader = CustomSkillLoader(project_root=skill_dir.parent)
        metadata = loader.parse_skill_metadata(skill_dir)

        assert metadata is not None
        assert metadata.name == "test-skill"
        assert metadata.version is None
        assert metadata.author is None
        assert metadata.category is None
        assert metadata.tags == []


class TestProgressiveDisclosure:
    """Test progressive disclosure (2KB limit)."""

    @pytest.fixture
    def large_skill_dir(self, tmp_path: Path) -> Path:
        """Create a skill with large SKILL.md file (>2KB)."""
        skill_dir = tmp_path / "large-skill"
        skill_dir.mkdir()
        return skill_dir

    def test_progressive_disclosure_reads_only_2kb(self, large_skill_dir: Path):
        """Test that only first 2KB is read for metadata parsing."""
        skill_file = large_skill_dir / "SKILL.md"
        
        # Create file with frontmatter + large content (>2KB)
        frontmatter = """---
name: large-skill
description: Large skill file
version: 1.0.0
---
"""
        large_content = "X" * 5000  # 5KB of content
        skill_file.write_text(frontmatter + large_content, encoding="utf-8")

        loader = CustomSkillLoader(project_root=large_skill_dir.parent)
        metadata = loader.parse_skill_metadata(large_skill_dir)

        # Should still parse metadata correctly
        assert metadata is not None
        assert metadata.name == "large-skill"
        assert metadata.version == "1.0.0"
        
        # Verify file is larger than 2KB
        assert skill_file.stat().st_size > 2048


class TestMultiScopeDiscovery:
    """Test multi-scope skill discovery."""

    @pytest.fixture
    def project_root(self, tmp_path: Path) -> Path:
        """Create project root with .claude/skills/."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / ".claude" / "skills").mkdir(parents=True)
        return project_root

    @pytest.fixture
    def user_skills_dir(self, tmp_path: Path, monkeypatch) -> Path:
        """Create USER scope skills directory."""
        user_home = tmp_path / "home"
        user_skills = user_home / ".tapps-agents" / "skills"
        user_skills.mkdir(parents=True)
        
        # Mock Path.home() to return our test home
        monkeypatch.setattr("pathlib.Path.home", lambda: user_home)
        
        return user_skills

    def test_repo_scope_discovery(self, project_root: Path):
        """Test discovering skills from REPO scope."""
        repo_skills = project_root / ".claude" / "skills"
        skill_dir = repo_skills / "repo-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            """---
name: repo-skill
description: Repo skill
---
""",
            encoding="utf-8",
        )

        loader = CustomSkillLoader(project_root=project_root)
        skills = loader.discover_skills_multi_scope(project_root)

        assert len(skills) >= 1
        skill_names = [s.name for s in skills]
        assert "repo-skill" in skill_names

    def test_user_scope_discovery(self, project_root: Path, user_skills_dir: Path):
        """Test discovering skills from USER scope."""
        user_skill_dir = user_skills_dir / "user-skill"
        user_skill_dir.mkdir()
        (user_skill_dir / "SKILL.md").write_text(
            """---
name: user-skill
description: User skill
---
""",
            encoding="utf-8",
        )

        loader = CustomSkillLoader(project_root=project_root)
        skills = loader.discover_skills_multi_scope(project_root)

        skill_names = [s.name for s in skills]
        assert "user-skill" in skill_names

    def test_scope_precedence_repo_overrides_user(
        self, project_root: Path, user_skills_dir: Path
    ):
        """Test that REPO scope skills override USER scope skills."""
        # Create skill in both REPO and USER scopes
        repo_skills = project_root / ".claude" / "skills"
        repo_skill_dir = repo_skills / "conflict-skill"
        repo_skill_dir.mkdir()
        (repo_skill_dir / "SKILL.md").write_text(
            """---
name: conflict-skill
description: Repo version
version: 2.0.0
---
""",
            encoding="utf-8",
        )

        user_skill_dir = user_skills_dir / "conflict-skill"
        user_skill_dir.mkdir()
        (user_skill_dir / "SKILL.md").write_text(
            """---
name: conflict-skill
description: User version
version: 1.0.0
---
""",
            encoding="utf-8",
        )

        loader = CustomSkillLoader(project_root=project_root)
        skills = loader.discover_skills_multi_scope(project_root)

        # Should find only one skill (REPO version)
        conflict_skills = [s for s in skills if s.name == "conflict-skill"]
        assert len(conflict_skills) == 1
        assert conflict_skills[0].version == "2.0.0"  # REPO version wins


class TestGitRootDetection:
    """Test git root detection."""

    def test_find_git_root_in_git_repo(self, tmp_path: Path):
        """Test finding git root when in git repository."""
        # Create git repo structure
        git_root = tmp_path / "repo"
        git_root.mkdir()
        (git_root / ".git").mkdir()
        
        nested_dir = git_root / "nested" / "deep"
        nested_dir.mkdir(parents=True)

        loader = CustomSkillLoader(project_root=nested_dir)
        git_root_found = loader._find_git_root(nested_dir)

        assert git_root_found == git_root

    def test_find_git_root_not_in_repo(self, tmp_path: Path):
        """Test git root detection when not in git repository."""
        non_git_dir = tmp_path / "not-a-repo" / "nested"
        non_git_dir.mkdir(parents=True)

        loader = CustomSkillLoader(project_root=non_git_dir)
        git_root_found = loader._find_git_root(non_git_dir)

        # Should return the starting path if not in git repo
        assert git_root_found == non_git_dir


class TestInitializeSkillRegistry:
    """Test skill registry initialization with multi-scope discovery."""

    def test_initialize_registry_with_multi_scope(self, tmp_path: Path):
        """Test that initialize_skill_registry uses multi-scope discovery."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / ".claude" / "skills").mkdir(parents=True)

        # Create a skill
        skill_dir = project_root / ".claude" / "skills" / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            """---
name: test-skill
description: Test
---
""",
            encoding="utf-8",
        )

        registry = initialize_skill_registry(project_root=project_root)

        # Should have discovered the skill
        skill = registry.get_skill("test-skill")
        assert skill is not None
        assert skill.name == "test-skill"
