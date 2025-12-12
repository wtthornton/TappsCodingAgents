"""
Improver Agent - Refactors and enhances existing code
"""

from pathlib import Path
from typing import Any

from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config
from ...core.mal import MAL


class ImproverAgent(BaseAgent):
    """
    Improver Agent - Code refactoring, performance optimization, and quality improvements.

    Permissions: Read, Write, Edit, Grep, Glob (no Bash)
    """

    def __init__(self, mal: MAL | None = None, config: ProjectConfig | None = None):
        super().__init__(
            agent_id="improver", agent_name="Improver Agent", config=config
        )
        if config is None:
            config = load_config()
        self.config = config

        # Initialize MAL with config
        mal_config = config.mal if config else None
        self.mal = mal or MAL(
            ollama_url=mal_config.ollama_url if mal_config else "http://localhost:11434"
        )
        self.project_root: Path = Path.cwd()

    async def activate(self, project_root: Path | None = None):
        await super().activate(project_root)
        if project_root is not None:
            self.project_root = project_root
        self.greet()
        await self.run("help")

    def greet(self):
        print(
            f"Hello! I am the {self.agent_name}. I help refactor and improve code quality."
        )

    async def run(self, command: str, **kwargs: Any) -> dict[str, Any]:
        command = command.lstrip("*")  # Remove star prefix if present
        handler_name = f"_handle_{command.replace('-', '_')}"
        if hasattr(self, handler_name):
            handler = getattr(self, handler_name)
            return await handler(**kwargs)
        else:
            return {
                "error": f"Unknown command: {command}. Use '*help' to see available commands."
            }

    async def _handle_refactor(
        self,
        file_path: str | None = None,
        instruction: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Refactor existing code to improve structure and maintainability."""
        if not file_path:
            return {
                "error": "File path required. Usage: *refactor <file_path> [instruction]"
            }

        file_path_obj = Path(file_path)
        if not file_path_obj.is_absolute():
            file_path_obj = self.project_root / file_path_obj

        try:
            self._validate_path(file_path_obj)
        except (FileNotFoundError, ValueError) as e:
            return {"error": str(e)}

        if not file_path_obj.exists():
            return {"error": f"File not found: {file_path}"}

        # Refactoring in progress...

        # Read current code
        current_code = file_path_obj.read_text(encoding="utf-8")

        # Get context for refactoring
        context_text = self.get_context_text(file_path_obj, tier=2)
        # Get context for refactoring
        context_text = self.get_context_text(file_path_obj, tier=2)
        # Get context for refactoring
        context_text = self.get_context_text(file_path_obj, tier=2)

        # Build prompt for refactoring
        instruction_text = (
            instruction
            or "Improve code structure, readability, and maintainability while preserving functionality."
        )

        prompt = f"""Refactor the following code to improve its quality:
        
{instruction_text}

Current code:
```python
{current_code}
```

Context (other related files):
{context_text}

Provide the refactored code that:
1. Improves code structure and organization
2. Enhances readability and maintainability
3. Preserves all existing functionality
4. Follows best practices and design patterns
5. Maintains backward compatibility

Return only the refactored code, wrapped in ```python code blocks."""

        # Generate refactored code using LLM
        try:
            response = await self.mal.generate(prompt)
            refactored_code = self._extract_code_from_response(response)

            # Write refactored code back to file
            file_path_obj.write_text(refactored_code, encoding="utf-8")

            return {
                "message": f"Successfully refactored {file_path}",
                "file": str(file_path),
                "refactored": True,
            }
        except Exception as e:
            return {"error": f"Failed to refactor code: {str(e)}"}

    async def _handle_optimize(
        self,
        file_path: str | None = None,
        optimization_type: str = "performance",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Optimize code for performance, memory, or other metrics."""
        if not file_path:
            return {
                "error": "File path required. Usage: *optimize <file_path> [optimization_type]"
            }

        file_path_obj = Path(file_path)
        if not file_path_obj.is_absolute():
            file_path_obj = self.project_root / file_path_obj

        try:
            self._validate_path(file_path_obj)
        except (FileNotFoundError, ValueError) as e:
            return {"error": str(e)}

        if not file_path_obj.exists():
            return {"error": f"File not found: {file_path}"}

        # Optimizing in progress...

        # Read current code
        current_code = file_path_obj.read_text(encoding="utf-8")

        # Get context
        context_text = self.get_context_text(file_path_obj, tier=2)

        optimization_prompts = {
            "performance": "Optimize for execution speed and efficiency",
            "memory": "Optimize for memory usage and reduce memory footprint",
            "both": "Optimize for both performance and memory usage",
        }

        optimization_instruction = optimization_prompts.get(
            optimization_type, optimization_prompts["performance"]
        )

        prompt = f"""Optimize the following code for {optimization_type}:
        
{optimization_instruction}

Current code:
```python
{current_code}
```

Context (other related files):
{context_text}

Provide the optimized code that:
1. Improves {optimization_type} characteristics
2. Maintains functionality and correctness
3. Preserves code readability
4. Uses efficient algorithms and data structures
5. Eliminates unnecessary operations

Return only the optimized code, wrapped in ```python code blocks."""

        try:
            response = await self.mal.generate(prompt)
            optimized_code = self._extract_code_from_response(response)

            # Write optimized code back to file
            file_path_obj.write_text(optimized_code, encoding="utf-8")

            return {
                "message": f"Successfully optimized {file_path} for {optimization_type}",
                "file": str(file_path),
                "optimization_type": optimization_type,
                "optimized": True,
            }
        except Exception as e:
            return {"error": f"Failed to optimize code: {str(e)}"}

    async def _handle_improve_quality(
        self, file_path: str | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """Improve overall code quality (structure, patterns, best practices)."""
        if not file_path:
            return {"error": "File path required. Usage: *improve-quality <file_path>"}

        file_path_obj = Path(file_path)
        if not file_path_obj.is_absolute():
            file_path_obj = self.project_root / file_path_obj

        try:
            self._validate_path(file_path_obj)
        except (FileNotFoundError, ValueError) as e:
            return {"error": str(e)}

        if not file_path_obj.exists():
            return {"error": f"File not found: {file_path}"}

        # Improving code quality in progress...

        # Read current code
        current_code = file_path_obj.read_text(encoding="utf-8")

        # Get context
        context_text = self.get_context_text(file_path_obj, tier=2)

        prompt = f"""Improve the overall code quality of the following code:
        
Current code:
```python
{current_code}
```

Context (other related files):
{context_text}

Provide improved code that:
1. Follows Python best practices and PEP 8 style guide
2. Uses appropriate design patterns
3. Improves error handling and robustness
4. Enhances type hints and documentation
5. Reduces code complexity where possible
6. Improves naming conventions
7. Adds appropriate docstrings

Return only the improved code, wrapped in ```python code blocks."""

        try:
            response = await self.mal.generate(prompt)
            improved_code = self._extract_code_from_response(response)

            # Write improved code back to file
            file_path_obj.write_text(improved_code, encoding="utf-8")

            return {
                "message": f"Successfully improved code quality for {file_path}",
                "file": str(file_path),
                "improved": True,
            }
        except Exception as e:
            return {"error": f"Failed to improve code quality: {str(e)}"}

    async def _handle_help(self) -> dict[str, Any]:
        """Show this help message."""
        help_message = {
            "*refactor [file_path] [instruction]": "Refactor existing code to improve structure and maintainability",
            "*optimize [file_path] [type]": "Optimize code for performance, memory, or both (type: performance|memory|both)",
            "*improve-quality [file_path]": "Improve overall code quality (best practices, patterns, documentation)",
            "*help": "Show this help message",
        }
        return {"content": help_message}

    def _extract_code_from_response(self, response: str) -> str:
        """Extract code from LLM response (handles code blocks)."""
        # Look for ```python or ``` blocks
        if "```python" in response:
            start = response.find("```python") + 9
            end = response.find("```", start)
            if end > start:
                return response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            if end > start:
                return response[start:end].strip()

        # If no code blocks, return the response as-is
        return response.strip()
