"""
Planner Agent - Creates user stories and task breakdowns
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config
from ...core.mal import MAL

logger = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    """
    Planner Agent - Story/epic planning and task breakdown.

    Permissions: Read, Write, Grep, Glob

    ⚠️ CRITICAL ACCURACY REQUIREMENT:
    - NEVER make up, invent, or fabricate information - Only report verified facts
    - ALWAYS verify claims by checking actual results, not just test pass/fail
    - Verify API calls succeed - inspect response data, status codes, error messages
    - Distinguish between code paths executing and actual functionality working
    - Admit uncertainty explicitly when you cannot verify
    """

    def __init__(self, mal: MAL | None = None, config: ProjectConfig | None = None):
        super().__init__(agent_id="planner", agent_name="Planner Agent", config=config)
        # Use config if provided, otherwise load defaults
        if config is None:
            config = load_config()
        self.config = config

        # Initialize MAL with config
        mal_config = config.mal if config else None
        self.mal = mal or MAL(
            ollama_url=mal_config.ollama_url if mal_config else "http://localhost:11434"
        )

        # Story storage path (from config or default)
        planner_config = config.agents.planner if config and config.agents else None
        stories_dir_str = planner_config.stories_dir if planner_config else None
        self.stories_dir = Path(stories_dir_str) if stories_dir_str else None

    def get_commands(self) -> list[dict[str, str]]:
        """Return available commands for planner agent"""
        base_commands = super().get_commands()
        return base_commands + [
            {
                "command": "*plan",
                "description": "Create a plan for a feature/requirement",
            },
            {
                "command": "*create-story",
                "description": "Generate a user story from description",
            },
            {
                "command": "*list-stories",
                "description": "List all stories in the project",
            },
        ]

    async def run(self, command: str, **kwargs) -> dict[str, Any]:
        """
        Execute planner agent command.

        Commands:
        - *plan <description>: Create a plan
        - *create-story <description> [--epic=<epic>] [--priority=<priority>]: Create a story
        - *list-stories [--epic=<epic>] [--status=<status>]: List stories
        """
        await self.activate()

        if command == "help":
            return await self._help()

        elif command == "plan":
            description = kwargs.get("description") or kwargs.get("text", "")
            if not description:
                return {"error": "Description required. Usage: *plan <description>"}

            return await self.create_plan(description)

        elif command == "create-story":
            description = kwargs.get("description") or kwargs.get("text", "")
            if not description:
                return {
                    "error": "Description required. Usage: *create-story <description> [--epic=<epic>] [--priority=<priority>]"
                }

            epic = kwargs.get("epic")
            priority = kwargs.get("priority", "medium")
            return await self.create_story(description, epic=epic, priority=priority)

        elif command == "list-stories":
            epic_filter = kwargs.get("epic")
            status_filter = kwargs.get("status")
            return await self.list_stories(epic=epic_filter, status=status_filter)

        else:
            return {
                "error": f"Unknown command: {command}. Use *help to see available commands."
            }

    async def create_plan(self, description: str) -> dict[str, Any]:
        """
        Create a plan for a feature or requirement.

        This uses the LLM to analyze the description and generate:
        - Story breakdown
        - Task estimates
        - Dependencies
        """
        prompt = f"""You are a software planning expert. Analyze the following requirement and create a detailed plan.

Requirement:
{description}

Generate a plan that includes:
1. Overview of the feature/requirement
2. List of user stories (with brief descriptions)
3. Estimated complexity for each story (1-5 scale)
4. Dependencies between stories
5. Suggested priority order

Format your response as structured text."""

        try:
            response = await self.mal.generate(prompt, model="qwen2.5-coder:7b")
            return {
                "type": "plan",
                "description": description,
                "plan": response,
                "created_at": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"type": "plan", "error": str(e), "description": description}

    async def create_story(
        self, description: str, epic: str | None = None, priority: str = "medium"
    ) -> dict[str, Any]:
        """
        Generate a user story from a description.

        Args:
            description: Story description
            epic: Epic or feature area (optional)
            priority: Priority (high/medium/low)
        """
        # Generate story ID
        story_id = self._generate_story_id(description, epic)

        # Create story metadata
        story_metadata = {
            "story_id": story_id,
            "title": self._extract_title(description),
            "description": description,
            "epic": epic or "general",
            "domain": self._infer_domain(description),
            "priority": priority,
            "complexity": await self._estimate_complexity(description),
            "status": "draft",
            "created_at": datetime.now().isoformat(),
            "created_by": "planner",
        }

        # Generate acceptance criteria and tasks using LLM
        acceptance_criteria, tasks = await self._generate_story_details(description)

        # Create story file
        story_file = await self._write_story_file(
            story_metadata, acceptance_criteria, tasks
        )

        return {
            "type": "story",
            "story_id": story_id,
            "story_file": str(story_file),
            "metadata": story_metadata,
            "acceptance_criteria": acceptance_criteria,
            "tasks": tasks,
        }

    async def list_stories(
        self, epic: str | None = None, status: str | None = None
    ) -> dict[str, Any]:
        """
        List all stories in the project.

        Args:
            epic: Filter by epic (optional)
            status: Filter by status (optional)
        """
        if self.stories_dir is None:
            # Default to stories/ directory in project root
            project_root = Path.cwd()
            self.stories_dir = project_root / "stories"

        stories = []

        if not self.stories_dir.exists():
            return {
                "type": "list_stories",
                "stories": [],
                "count": 0,
                "message": f"Stories directory not found: {self.stories_dir}",
            }

        # Find all story files
        story_files = list(self.stories_dir.glob("story-*.md")) + list(
            self.stories_dir.glob("story-*.yaml")
        )

        for story_file in story_files:
            try:
                metadata = self._read_story_metadata(story_file)

                # Apply filters
                if epic and metadata.get("epic") != epic:
                    continue
                if status and metadata.get("status") != status:
                    continue

                stories.append(
                    {
                        "story_id": metadata.get("story_id"),
                        "title": metadata.get("title"),
                        "epic": metadata.get("epic"),
                        "status": metadata.get("status"),
                        "priority": metadata.get("priority"),
                        "complexity": metadata.get("complexity"),
                        "file": str(story_file),
                    }
                )
            except Exception:
                # Skip invalid story files
                logger.debug(
                    "Skipping invalid story file %s", story_file, exc_info=True
                )
                continue  # nosec B112 - best-effort story discovery

        return {
            "type": "list_stories",
            "stories": stories,
            "count": len(stories),
            "filters": {"epic": epic, "status": status},
        }

    def _generate_story_id(self, description: str, epic: str | None = None) -> str:
        """Generate a unique story ID from description."""
        # Create a slug from description
        slug = re.sub(r"[^a-z0-9]+", "-", description.lower()[:50])
        slug = slug.strip("-")

        # Add epic prefix if provided
        if epic:
            epic_slug = re.sub(r"[^a-z0-9]+", "-", epic.lower())
            return f"{epic_slug}-{slug[:30]}"

        return f"story-{slug[:30]}"

    def _extract_title(self, description: str) -> str:
        """Extract a short title from description."""
        # Take first line or first 60 chars
        title = description.split("\n")[0].strip()
        if len(title) > 60:
            title = title[:57] + "..."
        return title

    def _infer_domain(self, description: str) -> str:
        """Infer domain from description (basic heuristic)."""
        description_lower = description.lower()

        # Simple keyword matching (can be enhanced with LLM)
        if any(word in description_lower for word in ["api", "endpoint", "service"]):
            return "backend"
        elif any(
            word in description_lower
            for word in ["ui", "interface", "component", "page"]
        ):
            return "frontend"
        elif any(word in description_lower for word in ["test", "testing", "spec"]):
            return "testing"
        elif any(
            word in description_lower for word in ["documentation", "docs", "guide"]
        ):
            return "documentation"
        else:
            return "general"

    async def _estimate_complexity(self, description: str) -> int:
        """Estimate complexity (1-5 scale) using LLM."""
        prompt = f"""Estimate the complexity of implementing this story on a scale of 1-5:
- 1: Trivial (simple change, <1 hour)
- 2: Easy (straightforward, 1-4 hours)
- 3: Medium (moderate effort, 1-2 days)
- 4: Complex (significant effort, 3-5 days)
- 5: Very Complex (major feature, 1+ weeks)

Story: {description}

Respond with ONLY a single number (1-5)."""

        try:
            response = await self.mal.generate(prompt, model="qwen2.5-coder:7b")
            # Extract number from response
            match = re.search(r"\b([1-5])\b", response.strip())
            if match:
                return int(match.group(1))
        except Exception:
            logger.debug("Complexity estimation failed; using default", exc_info=True)

        # Default to medium complexity if estimation fails
        return 3

    async def _generate_story_details(
        self, description: str
    ) -> tuple[list[str], list[str]]:
        """Generate acceptance criteria and tasks using LLM."""
        prompt = f"""Generate a user story breakdown for:

{description}

Provide:
1. Acceptance Criteria (list of 3-5 criteria, one per line, prefixed with "- ")
2. Tasks (list of 3-7 tasks, one per line, prefixed with "1. ", "2. ", etc.)

Format:
ACCEPTANCE CRITERIA:
- Criterion 1
- Criterion 2

TASKS:
1. Task 1
2. Task 2"""

        try:
            response = await self.mal.generate(prompt, model="qwen2.5-coder:7b")

            # Parse acceptance criteria
            acceptance_criteria = []
            tasks = []

            lines = response.split("\n")
            in_criteria = False
            in_tasks = False

            for line in lines:
                line = line.strip()
                if "acceptance criteria" in line.lower():
                    in_criteria = True
                    in_tasks = False
                    continue
                elif "tasks:" in line.lower():
                    in_criteria = False
                    in_tasks = True
                    continue

                if in_criteria and (line.startswith("-") or line.startswith("*")):
                    acceptance_criteria.append(line.lstrip("-* ").strip())
                elif in_tasks and re.match(r"^\d+\.", line):
                    tasks.append(re.sub(r"^\d+\.\s*", "", line).strip())

            return acceptance_criteria or [
                "Story implementation meets requirements"
            ], tasks or ["Implement story requirements"]
        except Exception:
            # Fallback to basic criteria/tasks
            return (
                ["Story implementation meets requirements"],
                ["Implement story requirements"],
            )

    async def _write_story_file(
        self, metadata: dict[str, Any], acceptance_criteria: list[str], tasks: list[str]
    ) -> Path:
        """Write story to file (Markdown format)."""
        if self.stories_dir is None:
            project_root = Path.cwd()
            self.stories_dir = project_root / "stories"

        # Create stories directory if it doesn't exist
        self.stories_dir.mkdir(parents=True, exist_ok=True)

        story_id = metadata["story_id"]
        story_file = self.stories_dir / f"{story_id}.md"

        # Generate story content
        content = f"""# {metadata['title']}

```yaml
story_id: {metadata['story_id']}
title: {metadata['title']}
description: |
{self._indent_yaml_multiline(metadata['description'])}
epic: {metadata['epic']}
domain: {metadata['domain']}
priority: {metadata['priority']}
complexity: {metadata['complexity']}
status: {metadata['status']}
created_at: {metadata['created_at']}
created_by: {metadata['created_by']}
```

## Description

{metadata['description']}

## Acceptance Criteria

{chr(10).join(f"- [ ] {ac}" for ac in acceptance_criteria)}

## Tasks

{chr(10).join(f"{i+1}. {task}" for i, task in enumerate(tasks))}

## Technical Notes

(Technical considerations, dependencies, etc.)

## Dependencies

- Related stories: []
- Blocks: []
- Blocked by: []
"""

        story_file.write_text(content, encoding="utf-8")
        return story_file

    def _indent_yaml_multiline(self, text: str, indent: int = 2) -> str:
        """Indent multiline text for YAML."""
        lines = text.split("\n")
        return "\n".join(" " * indent + line for line in lines)

    def _read_story_metadata(self, story_file: Path) -> dict[str, Any]:
        """Read story metadata from file."""
        content = story_file.read_text(encoding="utf-8")

        # Extract YAML frontmatter
        yaml_match = re.search(r"```yaml\n(.*?)\n```", content, re.DOTALL)
        if yaml_match:
            try:
                metadata = yaml.safe_load(yaml_match.group(1))
                return metadata or {}
            except yaml.YAMLError:
                pass

        return {}

    async def _help(self) -> dict[str, Any]:
        """Return help information."""
        content = f"""# {self.agent_name} - Help

## Available Commands

{chr(10).join(f"- **{cmd['command']}**: {cmd['description']}" for cmd in self.get_commands())}

## Usage Examples

### Create a Plan
```
*plan Add user authentication with OAuth2 support
```

### Create a Story
```
*create-story User should be able to log in with Google
*create-story Add shopping cart --epic=checkout --priority=high
```

### List Stories
```
*list-stories
*list-stories --epic=checkout
*list-stories --status=draft
```

## Story Storage

Stories are saved to `stories/` directory in your project root.
Each story is saved as a Markdown file with YAML frontmatter.
"""

        return {"type": "help", "content": content}

    async def close(self):
        """Clean up resources"""
        await self.mal.close()
