"""
Planner Agent - Creates user stories and task breakdowns
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from ...agents.analyst.agent import AnalystAgent
from ...context7.agent_integration import Context7AgentHelper, get_context7_helper
from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config
from ...core.instructions import GenericInstruction
from ...core.runtime_mode import is_cursor_mode

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

    def __init__(self, config: ProjectConfig | None = None):
        super().__init__(agent_id="planner", agent_name="Planner Agent", config=config)
        # Use config if provided, otherwise load defaults
        if config is None:
            config = load_config()
        self.config = config

        # Story storage path (from config or default)
        planner_config = config.agents.planner if config and config.agents else None
        stories_dir_str = planner_config.stories_dir if planner_config else None
        self.stories_dir = Path(stories_dir_str) if stories_dir_str else None

        # Initialize Context7 helper (Enhancement: Universal Context7 integration)
        self.context7: Context7AgentHelper | None = None
        if config:
            self.context7 = get_context7_helper(self, config)

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
            {
                "command": "*evaluate-stories",
                "description": "Evaluate story quality using INVEST criteria",
            },
            {
                "command": "*validate-stories",
                "description": "Validate stories for completeness and quality",
            },
            {
                "command": "*trace-stories",
                "description": "Map stories to acceptance criteria and test cases",
            },
            {
                "command": "*review-stories",
                "description": "Structured review of stories with INVEST checklist",
            },
            {
                "command": "*calibrate-estimates",
                "description": "Get calibrated estimates based on historical accuracy",
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
            return self._help()

        elif command == "plan":
            description = kwargs.get("description") or kwargs.get("text", "")
            if not description:
                return {"error": "Description required. Usage: *plan <description>"}

            generate_doc = kwargs.get("generate_doc", False) or kwargs.get("generate-doc", False)
            output_file = kwargs.get("output_file") or kwargs.get("output-file")
            output_format = kwargs.get("output_format", "markdown") or kwargs.get("output-format", "markdown")

            result = await self.create_plan(description)
            
            # Generate document if requested
            if generate_doc:
                from ...core.document_generator import DocumentGenerator
                doc_generator = DocumentGenerator(project_root=self._project_root)
                
                # Determine output file if not provided
                if not output_file:
                    docs_dir = self._project_root / "docs" / "plans"
                    docs_dir.mkdir(parents=True, exist_ok=True)
                    # Create filename from description
                    safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in description[:50])
                    safe_name = safe_name.replace(' ', '_').lower()
                    output_file = docs_dir / f"{safe_name}_plan.{output_format if output_format != 'html' else 'html'}"
                
                # Generate document
                doc_path = doc_generator.generate_plan_doc(
                    plan_data=result,
                    output_file=output_file,
                    format=output_format,
                )
                
                result["document"] = {
                    "path": str(doc_path),
                    "format": output_format,
                }
            
            return result

        elif command == "create-story":
            description = kwargs.get("description") or kwargs.get("text", "")
            if not description:
                return {
                    "error": "Description required. Usage: *create-story <description> [--epic=<epic>] [--priority=<priority>]"
                }

            epic = kwargs.get("epic")
            priority = kwargs.get("priority", "medium")
            generate_doc = kwargs.get("generate_doc", False) or kwargs.get("generate-doc", False)
            output_file = kwargs.get("output_file") or kwargs.get("output-file")
            output_format = kwargs.get("output_format", "markdown") or kwargs.get("output-format", "markdown")

            result = await self.create_story(description, epic=epic, priority=priority)
            
            # Generate document if requested
            if generate_doc:
                from ...core.document_generator import DocumentGenerator
                doc_generator = DocumentGenerator(project_root=self._project_root)
                
                # Determine output file if not provided
                if not output_file:
                    stories_dir = self.stories_dir or (self._project_root / "stories")
                    stories_dir.mkdir(parents=True, exist_ok=True)
                    safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in description[:50])
                    safe_name = safe_name.replace(' ', '_').lower()
                    output_file = stories_dir / f"{safe_name}_story.{output_format if output_format != 'html' else 'html'}"
                
                # Generate document
                doc_path = doc_generator.generate_user_story_doc(
                    story_data=result,
                    output_file=output_file,
                    format=output_format,
                )
                
                result["document"] = {
                    "path": str(doc_path),
                    "format": output_format,
                }
            
            return result

        elif command == "list-stories":
            epic_filter = kwargs.get("epic")
            status_filter = kwargs.get("status")
            return await self.list_stories(epic=epic_filter, status=status_filter)

        elif command == "evaluate-stories":
            stories = kwargs.get("stories", [])
            if isinstance(stories, str):
                # Try to load from file
                story_path = Path(stories)
                if story_path.exists():
                    import json
                    stories = json.loads(story_path.read_text(encoding="utf-8"))
                else:
                    return {"error": f"Stories file not found: {stories}"}

            return await self._evaluate_stories(stories)

        elif command == "validate-stories":
            stories = kwargs.get("stories", [])
            if isinstance(stories, str):
                # Try to load from file
                story_path = Path(stories)
                if story_path.exists():
                    import json
                    stories = json.loads(story_path.read_text(encoding="utf-8"))
                else:
                    return {"error": f"Stories file not found: {stories}"}

            return await self._validate_stories(stories)

        elif command == "trace-stories":
            stories = kwargs.get("stories", [])
            test_cases = kwargs.get("test_cases", [])
            output_file = kwargs.get("output_file")

            return await self._trace_stories(stories, test_cases, output_file)

        elif command == "review-stories":
            stories = kwargs.get("stories", [])
            if isinstance(stories, str):
                story_path = Path(stories)
                if story_path.exists():
                    import json
                    stories = json.loads(story_path.read_text(encoding="utf-8"))
                else:
                    return {"error": f"Stories file not found: {stories}"}

            return await self._review_stories(stories)

        elif command == "calibrate-estimates":
            estimated_points = kwargs.get("estimated_points", 0)
            complexity = kwargs.get("complexity", "medium")

            if estimated_points <= 0:
                return {"error": "estimated_points must be greater than 0"}

            return await self._calibrate_estimates(estimated_points, complexity)

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
        # If in Cursor mode, return instruction for Cursor Skills
        if is_cursor_mode():
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

            # Prepare instruction for Cursor Skills
            instruction = GenericInstruction(
                agent_name="planner",
                command="plan",
                prompt=prompt,
                parameters={"description": description},
            )

            return {
                "type": "plan",
                "description": description,
                "instruction": instruction.to_dict(),
                "skill_command": instruction.to_skill_command(),
                "created_at": datetime.now().isoformat(),
            }
        
        # For CLI mode, actually generate the plan using analyst agent
        analyst = None
        try:
            analyst = AnalystAgent(config=self.config)
            await analyst.activate(project_root=self._project_root, offline_mode=False)
            
            # Gather requirements first
            requirements_result = await analyst.run(
                "gather-requirements",
                description=description,
            )
            
            # Check for errors in result
            if isinstance(requirements_result, dict) and "error" in requirements_result:
                error_msg = requirements_result.get("error", "Unknown error")
                logger.warning(f"Analyst agent returned error: {error_msg}")
                raise RuntimeError(f"Requirements gathering failed: {error_msg}")
            
            # Extract requirements information
            requirements = requirements_result.get("requirements", {})
            if isinstance(requirements, dict):
                functional_reqs = requirements.get("functional_requirements", [])
                non_functional_reqs = requirements.get("non_functional_requirements", [])
            else:
                functional_reqs = []
                non_functional_reqs = []
            
            # Generate user stories in standard format
            user_stories = await self._generate_user_stories(description, functional_reqs)
            
            # Build plan structure with user stories
            plan_text = self._format_plan_markdown(
                description=description,
                requirements_result=requirements_result,
                functional_reqs=functional_reqs,
                non_functional_reqs=non_functional_reqs,
                user_stories=user_stories,
            )
            
            return {
                "type": "plan",
                "description": description,
                "plan": plan_text,
                "requirements": requirements,
                "user_stories": user_stories,
                "markdown": plan_text,
                "created_at": datetime.now().isoformat(),
            }
        except (ConnectionError, TimeoutError, OSError) as e:
            # Network-related errors
            error_msg = f"Network error: {e!s}"
            logger.error(f"Network error generating plan: {e}", exc_info=True)
            # Fallback to instruction if analyst fails
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

            instruction = GenericInstruction(
                agent_name="planner",
                command="plan",
                prompt=prompt,
                parameters={"description": description},
            )

            return {
                "type": "plan",
                "description": description,
                "error": error_msg,
                "error_type": "network_error",
                "instruction": instruction.to_dict(),
                "skill_command": instruction.to_skill_command(),
                "created_at": datetime.now().isoformat(),
            }
        except Exception as e:
            # All other errors
            error_msg = f"Error generating plan: {e!s}"
            logger.error(f"Error generating plan: {e}", exc_info=True)
            # Fallback to instruction if analyst fails
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

            instruction = GenericInstruction(
                agent_name="planner",
                command="plan",
                prompt=prompt,
                parameters={"description": description},
            )

            return {
                "type": "plan",
                "description": description,
                "error": error_msg,
                "error_type": "unknown_error",
                "instruction": instruction.to_dict(),
                "skill_command": instruction.to_skill_command(),
                "created_at": datetime.now().isoformat(),
            }
        finally:
            # Ensure analyst is always closed, even on error
            if analyst is not None:
                try:
                    await analyst.close()
                except Exception as close_error:
                    logger.warning(f"Error closing analyst agent: {close_error}", exc_info=True)

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

        # Prepare instruction for Cursor Skills
        instruction = GenericInstruction(
            agent_name="planner",
            command="estimate-complexity",
            prompt=prompt,
            parameters={"description": description},
        )

        # Return instruction - complexity will be determined by Cursor Skills
        # Default to medium complexity for now
        return {
            "instruction": instruction.to_dict(),
            "skill_command": instruction.to_skill_command(),
            "estimated_complexity": 3,  # Default
        }

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

        # Prepare instruction for Cursor Skills
        GenericInstruction(
            agent_name="planner",
            command="generate-story-details",
            prompt=prompt,
            parameters={"description": description},
        )

        # Return instruction - details will be generated by Cursor Skills
        # Return basic criteria/tasks for now
        acceptance_criteria = ["Story implementation meets requirements"]
        tasks = ["Implement story requirements"]
        
        return acceptance_criteria, tasks

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
    
    async def _generate_user_stories(
        self, description: str, functional_requirements: list[str]
    ) -> list[dict[str, Any]]:
        """Generate user stories in standard format from requirements."""
        from ...core.mal import MAL
        mal = MAL()
        
        # Build prompt for user story generation
        reqs_text = "\n".join(f"- {req}" for req in functional_requirements) if functional_requirements else description
        
        prompt = f"""Generate user stories in the standard format "As a {{user}}, I want {{goal}}, so that {{benefit}}" from the following requirements:

Description: {description}

Functional Requirements:
{reqs_text}

For each user story, provide:
1. The story in standard format: "As a [user type], I want [goal], so that [benefit]"
2. Acceptance criteria (3-5 items)
3. Story points estimate (Fibonacci: 1, 2, 3, 5, 8, 13)

Format as JSON array with:
- story: The story text in standard format
- user: User type
- goal: What they want to do
- benefit: Why they want it
- acceptance_criteria: List of criteria
- story_points: Number (1-13)
"""
        
        try:
            response = await mal.generate(
                prompt=prompt,
                system_prompt="You are a product planner. Generate user stories in standard format from requirements.",
            )
            
            # Parse JSON response
            import json as json_lib
            try:
                stories_data = json_lib.loads(response)
                if not isinstance(stories_data, list):
                    stories_data = [stories_data]
            except (json_lib.JSONDecodeError, ValueError):
                # Fallback: create basic story from description
                stories_data = [{
                    "story": f"As a user, I want {description.lower()}, so that I can accomplish my goal",
                    "user": "user",
                    "goal": description.lower(),
                    "benefit": "accomplish my goal",
                    "acceptance_criteria": ["Feature works as described", "Tests pass", "Documentation updated"],
                    "story_points": 3,
                }]
            
            return stories_data
        except Exception as e:
            logger.warning(f"Error generating user stories: {e}")
            # Fallback: create basic story
            return [{
                "story": f"As a user, I want {description.lower()}, so that I can accomplish my goal",
                "user": "user",
                "goal": description.lower(),
                "benefit": "accomplish my goal",
                "acceptance_criteria": ["Feature works as described"],
                "story_points": 3,
            }]
    
    def _format_plan_markdown(
        self,
        description: str,
        requirements_result: dict[str, Any],
        functional_reqs: list[str],
        non_functional_reqs: list[str],
        user_stories: list[dict[str, Any]],
    ) -> str:
        """Format plan as markdown document with user stories."""
        lines = [
            f"# Plan: {description}",
            "",
            "## Overview",
            "",
            requirements_result.get('summary', {}).get('overview', 'Feature implementation plan') if isinstance(requirements_result.get('summary'), dict) else 'Feature implementation plan',
            "",
            "## Requirements",
            "",
            "### Functional Requirements",
            "",
        ]
        
        if functional_reqs:
            for req in functional_reqs:
                lines.append(f"- {req}")
        else:
            lines.append("- Requirements analysis in progress")
        
        lines.extend([
            "",
            "### Non-Functional Requirements",
            "",
        ])
        
        if non_functional_reqs:
            for req in non_functional_reqs:
                lines.append(f"- {req}")
        else:
            lines.append("- Requirements analysis in progress")
        
        lines.extend([
            "",
            "## User Stories",
            "",
        ])
        
        if user_stories:
            for i, story in enumerate(user_stories, 1):
                story_text = story.get("story", f"Story {i}")
                story.get("user", "user")
                story.get("goal", "")
                story.get("benefit", "")
                acceptance_criteria = story.get("acceptance_criteria", [])
                story_points = story.get("story_points", 0)
                
                lines.extend([
                    f"### Story {i}: {story_text}",
                    "",
                    f"**Story Points:** {story_points}",
                    "",
                    "**Acceptance Criteria:**",
                    "",
                ])
                
                for ac in acceptance_criteria:
                    lines.append(f"- [ ] {ac}")
                
                lines.append("")
        else:
            lines.append("(User stories to be generated)")
            lines.append("")
        
        lines.extend([
            "## Estimated Complexity",
            "",
            "(To be estimated per story)",
            "",
            "## Dependencies",
            "",
            "(To be identified)",
            "",
            "## Priority Order",
            "",
            "(To be determined)",
            "",
        ])
        
        return "\n".join(lines)

    def _help(self) -> dict[str, Any]:
        """
        Return help information for Planner Agent.
        
        Returns standardized help format with commands, examples, and usage notes.
        This method is synchronous as it performs no I/O operations.
        
        Returns:
            dict: Help information with standardized format:
                - type (str): Always "help"
                - content (str): Formatted markdown help text containing:
                    - Available commands list
                    - Usage examples
                    - Story storage information
                    
        Note:
            This method is called via agent.run("help") which handles async context.
            Command list is cached via BaseAgent.get_commands() for performance.
        """
        commands = self.get_commands()
        command_lines = [
            f"- **{cmd['command']}**: {cmd['description']}"
            for cmd in commands
        ]
        
        content = f"""# {self.agent_name} - Help

## Available Commands

{chr(10).join(command_lines)}

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

    async def _evaluate_stories(self, stories: list[dict[str, Any]]) -> dict[str, Any]:
        """Evaluate story quality using INVEST criteria."""
        from ...core.story_evaluator import StoryEvaluator

        evaluator = StoryEvaluator()
        results = []

        for story in stories:
            score = evaluator.evaluate(story)
            results.append(
                {
                    "story_id": story.get("id", "unknown"),
                    "title": story.get("title", "Untitled"),
                    "score": {
                        "overall": score.overall,
                        "independent": score.independent,
                        "negotiable": score.negotiable,
                        "valuable": score.valuable,
                        "estimable": score.estimable,
                        "small": score.small,
                        "testable": score.testable,
                    },
                    "issues": score.issues,
                    "strengths": score.strengths,
                    "recommendations": score.recommendations,
                }
            )

        # Calculate average scores
        avg_scores = {
            "overall": sum(r["score"]["overall"] for r in results) / len(results) if results else 0.0,
            "independent": sum(r["score"]["independent"] for r in results) / len(results) if results else 0.0,
            "negotiable": sum(r["score"]["negotiable"] for r in results) / len(results) if results else 0.0,
            "valuable": sum(r["score"]["valuable"] for r in results) / len(results) if results else 0.0,
            "estimable": sum(r["score"]["estimable"] for r in results) / len(results) if results else 0.0,
            "small": sum(r["score"]["small"] for r in results) / len(results) if results else 0.0,
            "testable": sum(r["score"]["testable"] for r in results) / len(results) if results else 0.0,
        }

        return {
            "success": True,
            "stories_evaluated": len(results),
            "average_scores": avg_scores,
            "story_results": results,
        }

    async def _validate_stories(self, stories: list[dict[str, Any]]) -> dict[str, Any]:
        """Validate stories for completeness and quality."""
        from ...core.story_evaluator import StoryEvaluator

        evaluator = StoryEvaluator()
        results = []
        all_valid = True

        for story in stories:
            result = evaluator.validate(story)
            all_valid = all_valid and result.is_valid
            results.append(
                {
                    "story_id": story.get("id", "unknown"),
                    "title": story.get("title", "Untitled"),
                    "is_valid": result.is_valid,
                    "score": {
                        "overall": result.score.overall,
                        "independent": result.score.independent,
                        "negotiable": result.score.negotiable,
                        "valuable": result.score.valuable,
                        "estimable": result.score.estimable,
                        "small": result.score.small,
                        "testable": result.score.testable,
                    },
                    "missing_elements": result.missing_elements,
                    "weak_acceptance_criteria": result.weak_acceptance_criteria,
                    "dependency_issues": result.dependency_issues,
                    "issues": result.score.issues,
                    "recommendations": result.score.recommendations,
                }
            )

        return {
            "success": True,
            "all_valid": all_valid,
            "stories_validated": len(results),
            "validation_results": results,
        }

    async def _trace_stories(
        self, stories: list[dict[str, Any]], test_cases: list[dict[str, Any]], output_file: str | None = None
    ) -> dict[str, Any]:
        """Map stories to acceptance criteria and test cases."""
        from ...core.traceability import TraceabilityManager

        manager = TraceabilityManager()
        matrix = manager.get_matrix()

        traceability_map = []

        for story in stories:
            story_id = story.get("id", "unknown")
            matrix.add_story(story_id, story)

            acceptance_criteria = story.get("acceptance_criteria", [])
            linked_tests = []

            # Link test cases to acceptance criteria
            for test_case in test_cases:
                test_story_id = test_case.get("story_id") or test_case.get("related_story")
                if test_story_id == story_id:
                    test_id = test_case.get("id", "unknown")
                    linked_tests.append(test_id)

                    # Link story to test
                    matrix.link("story", story_id, "test", test_id, "validates", 1.0)

            traceability_map.append(
                {
                    "story_id": story_id,
                    "title": story.get("title", "Untitled"),
                    "acceptance_criteria": acceptance_criteria,
                    "linked_tests": linked_tests,
                    "coverage": len(linked_tests) / len(acceptance_criteria) * 100.0 if acceptance_criteria else 0.0,
                }
            )

        # Save matrix
        manager.save_matrix()

        # Generate report
        report = {
            "stories_traced": len(traceability_map),
            "total_acceptance_criteria": sum(len(m["acceptance_criteria"]) for m in traceability_map),
            "total_tests": len(test_cases),
            "average_coverage": sum(m["coverage"] for m in traceability_map) / len(traceability_map) if traceability_map else 0.0,
            "traceability_map": traceability_map,
        }

        # Save to file if specified
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            import yaml
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(report, f, default_flow_style=False)

        return {
            "success": True,
            "traceability_report": report,
            "matrix_file": str(manager.matrix_file),
            "output_file": str(output_path) if output_file else None,
        }

    async def _review_stories(self, stories: list[dict[str, Any]]) -> dict[str, Any]:
        """Structured review of stories with INVEST checklist."""
        from ...core.review_checklists import StoryReviewChecklist

        checklist = StoryReviewChecklist()
        results = []

        for story in stories:
            result = checklist.review(story)
            results.append(
                {
                    "story_id": story.get("id", "unknown"),
                    "title": story.get("title", "Untitled"),
                    "overall_score": result.overall_score,
                    "items_checked": result.items_checked,
                    "items_total": result.items_total,
                    "critical_issues": result.critical_issues,
                    "high_issues": result.high_issues,
                    "medium_issues": result.medium_issues,
                    "low_issues": result.low_issues,
                    "recommendations": result.recommendations,
                }
            )

        avg_score = sum(r["overall_score"] for r in results) / len(results) if results else 0.0

        return {
            "success": True,
            "stories_reviewed": len(results),
            "average_score": avg_score,
            "review_results": results,
        }

    async def _calibrate_estimates(self, estimated_points: int, complexity: str) -> dict[str, Any]:
        """Get calibrated estimates based on historical accuracy."""
        from ...core.estimation_tracker import EstimationTracker

        tracker = EstimationTracker()
        tracker.load()

        calibrated = tracker.get_calibrated_estimate(estimated_points, complexity)

        return {
            "success": True,
            **calibrated,
        }

    async def close(self):
        """Clean up resources"""
        pass
