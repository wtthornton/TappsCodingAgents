"""
Single Skill–Agent–Handler Registry.

Maps Skill -> Agent -> Workflow handler (or orchestrator-only / CLI-only) for
validation, docs, and routing. Plan Phase 1.2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Agents that have a workflow handler in agent_handlers/
AGENTS_WITH_HANDLERS = frozenset({
    "analyst", "architect", "debugger", "designer", "documenter",
    "implementer", "ops", "orchestrator", "planner", "reviewer", "tester",
})
# Skills with no workflow handler (orchestrator-only or CLI-only)
SKILLS_NO_HANDLER = frozenset({"enhancer", "evaluator", "bug-fix-agent", "improver"})
ORCHESTRATOR_SKILLS = frozenset({"simple-mode"})


@dataclass
class SkillAgentEntry:
    """One source-of-truth entry: Skill -> Agent -> Handler (or not)."""

    skill_name: str
    skill_path: Path
    agent_module: str | None  # e.g. tapps_agents.agents.reviewer
    has_workflow_handler: bool
    handler_agent_name: str | None  # when has_workflow_handler, equals skill_name typically
    allowed_tools: list[str] | None = None
    capabilities: list[str] = field(default_factory=list)
    is_orchestrator: bool = False


class SkillAgentRegistry:
    """
    Registry mapping Skill -> Agent -> Workflow handler for validation and docs.

    Built by scanning .claude/skills (and packaged skills), parsing frontmatter,
    and matching to agent_handlers.
    """

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)
        self._entries: dict[str, SkillAgentEntry] = {}

    def add(self, entry: SkillAgentEntry) -> None:
        """Register an entry (overwrites same skill_name)."""
        self._entries[entry.skill_name] = entry

    def get_skill(self, skill_name: str) -> SkillAgentEntry | None:
        """Return entry for skill or None."""
        return self._entries.get(skill_name)

    def list_skills(self) -> list[SkillAgentEntry]:
        """Return all entries."""
        return list(self._entries.values())

    def list_commands(self) -> list[tuple[str, str, str]]:
        """
        List (command, skill, execution_path).

        command: canonical skill command (e.g. review, plan).
        skill: skill/agent name.
        execution_path: "workflow" | "CLI" | "orchestrator".
        """
        from ..workflow.skill_invoker import SkillInvoker

        seen: set[tuple[str, str]] = set()
        out: list[tuple[str, str, str]] = []
        for (agent, action), (skill_cmd, _) in SkillInvoker.COMMAND_MAPPING.items():
            key = (agent, skill_cmd)
            if key in seen:
                continue
            seen.add(key)
            ent = self._entries.get(agent)
            if ent and ent.is_orchestrator:
                ep = "orchestrator"
            elif agent in ORCHESTRATOR_SKILLS:
                ep = "orchestrator"
            elif agent in AGENTS_WITH_HANDLERS:
                ep = "workflow"
            else:
                ep = "CLI"
            out.append((skill_cmd, agent, ep))
        # Ensure simple-mode and other orchestrators appear
        for e in self._entries.values():
            if e.is_orchestrator and e.skill_name not in {s[1] for s in out}:
                out.append((f"*{e.skill_name}", e.skill_name, "orchestrator"))
        return sorted(out, key=lambda x: (x[1], x[0]))

    def agents_with_cli(self) -> set[str]:
        """Set of agent/skill names that appear in COMMAND_MAPPING (have a CLI path)."""
        from ..workflow.skill_invoker import SkillInvoker

        return {k[0] for k in SkillInvoker.COMMAND_MAPPING}

    def skills_with_no_execution_path(self) -> list[str]:
        """Skill names that have no workflow handler, are not orchestrator, and no CLI mapping."""
        cli_agents = self.agents_with_cli()
        return [
            e.skill_name
            for e in self._entries.values()
            if not e.has_workflow_handler and not e.is_orchestrator and e.skill_name not in cli_agents
        ]


def _parse_frontmatter(skill_dir: Path) -> dict[str, Any] | None:
    """Parse YAML frontmatter from SKILL.md; returns dict or None."""
    import re

    import yaml

    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        return None
    try:
        content = skill_file.read_text(encoding="utf-8")[:2048]
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if not m:
            return None
        meta = yaml.safe_load(m.group(1))
        return meta if isinstance(meta, dict) else None
    except Exception:
        return None


def _discover_skill_dirs(project_root: Path) -> list[Path]:
    """Discover .claude/skills subdirs and package built-in skill dirs."""
    from .skill_loader import CustomSkillLoader

    loader = CustomSkillLoader(project_root=project_root)
    skills = loader.discover_skills_multi_scope(project_root)
    # Use path from SkillMetadata; dedupe by name (first wins)
    seen: set[str] = set()
    dirs: list[Path] = []
    for s in skills:
        if s.name not in seen:
            seen.add(s.name)
            dirs.append(Path(s.path) if hasattr(s, "path") else s.path)
    # Also scan project .claude/skills directly so we don't miss local-only
    proj_skills = project_root / ".claude" / "skills"
    if proj_skills.exists():
        for d in proj_skills.iterdir():
            if d.is_dir() and (d / "SKILL.md").exists() and d.name not in seen:
                seen.add(d.name)
                dirs.append(d)
    return dirs


def get_registry(project_root: Path | None = None) -> SkillAgentRegistry:
    """
    Build and return SkillAgentRegistry for the project.

    Scans .claude/skills and package skills, parses frontmatter, and sets
    has_workflow_handler / is_orchestrator from handler coverage.
    """
    root = Path(project_root or Path.cwd())
    reg = SkillAgentRegistry(root)

    for skill_dir in _discover_skill_dirs(root):
        meta = _parse_frontmatter(skill_dir)
        name = (meta or {}).get("name", skill_dir.name)
        allowed = meta.get("allowed-tools") if meta else None
        if isinstance(allowed, str):
            allowed = [t.strip() for t in allowed.split(",")]
        caps = list(meta.get("capabilities") or []) if meta else []

        has_handler = name in AGENTS_WITH_HANDLERS
        no_handler = name in SKILLS_NO_HANDLER
        is_orb = name in ORCHESTRATOR_SKILLS

        agent_module = f"tapps_agents.agents.{name}" if (has_handler or no_handler or is_orb) and name not in ("bug-fix-agent", "simple-mode") else None
        if name == "simple-mode":
            agent_module = None
        if name == "bug-fix-agent":
            agent_module = None

        entry = SkillAgentEntry(
            skill_name=name,
            skill_path=skill_dir,
            agent_module=agent_module,
            has_workflow_handler=has_handler and not is_orb,
            handler_agent_name=name if has_handler and not is_orb else None,
            allowed_tools=allowed,
            capabilities=caps,
            is_orchestrator=is_orb,
        )
        reg.add(entry)

    return reg
