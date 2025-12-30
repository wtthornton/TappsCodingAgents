"""
Improver Agent - Refactors and enhances existing code
"""

import inspect
import logging
from pathlib import Path
from typing import Any

from ...context7.agent_integration import Context7AgentHelper, get_context7_helper
from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config
from ...core.instructions import GenericInstruction
from ...core.tiered_context import ContextTier

logger = logging.getLogger(__name__)


class ImproverAgent(BaseAgent):
    """
    Improver Agent - Code refactoring, performance optimization, and quality improvements.

    Permissions: Read, Write, Edit, Grep, Glob (no Bash)

    ⚠️ CRITICAL ACCURACY REQUIREMENT:
    - NEVER make up, invent, or fabricate information - Only report verified facts
    - ALWAYS verify claims by checking actual results, not just test pass/fail
    - Verify API calls succeed - inspect response data, status codes, error messages
    - Distinguish between code paths executing and actual functionality working
    - Admit uncertainty explicitly when you cannot verify
    """

    def __init__(self, config: ProjectConfig | None = None):
        super().__init__(
            agent_id="improver", agent_name="Improver Agent", config=config
        )
        if config is None:
            config = load_config()
        self.config = config
        self.project_root: Path = Path.cwd()

        # Initialize Context7 helper (Enhancement: Universal Context7 integration)
        self.context7: Context7AgentHelper | None = None
        if config:
            self.context7 = get_context7_helper(self, config)

    async def activate(self, project_root: Path | None = None, offline_mode: bool = False):
        await super().activate(project_root, offline_mode=offline_mode)
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
            # Handle both sync and async handlers
            if inspect.iscoroutinefunction(handler):
                return await handler(**kwargs)
            else:
                return handler(**kwargs)
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
        context_text = self.get_context_text(file_path_obj, tier=ContextTier.TIER2)

        # Enhancement: Auto-detect libraries and fetch Context7 documentation
        context7_docs = {}
        context7_guidance = ""
        try:
            from ...core.language_detector import LanguageDetector
            detector = LanguageDetector()
            language = detector.detect_language(file_path_obj)
            
            # Use universal auto-detection hook for Context7 docs
            context7_docs = await self._auto_fetch_context7_docs(
                code=current_code,
                prompt=instruction or "Refactor code to improve structure and maintainability",
                language=language,
            )
            
            # Add Context7 guidance to prompt if available
            if context7_docs:
                context7_guidance = "\n\nRelevant Library Best Practices from Context7:\n"
                for lib_name, lib_doc in context7_docs.items():
                    if lib_doc and lib_doc.get("content"):
                        content_preview = lib_doc.get("content", "")[:500]
                        context7_guidance += f"\n{lib_name}:\n{content_preview}...\n"
                logger.debug(f"Auto-fetched Context7 docs for {len(context7_docs)} libraries using universal hook")
        except Exception as e:
            logger.debug(f"Context7 auto-detection failed during refactor: {e}, continuing without Context7 docs")

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
{context7_guidance}

Provide the refactored code that:
1. Improves code structure and organization
2. Enhances readability and maintainability
3. Preserves all existing functionality
4. Follows best practices and design patterns
5. Maintains backward compatibility

Return only the refactored code, wrapped in ```python code blocks."""

        # Prepare instruction for Cursor Skills
        instruction = GenericInstruction(
            agent_name="improver",
            command="refactor",
            prompt=prompt,
            parameters={"file_path": str(file_path)},
        )

        return {
            "message": f"Refactoring instruction prepared for {file_path}",
            "instruction": instruction.to_dict(),
            "skill_command": instruction.to_skill_command(),
            "file": str(file_path),
            "note": "⚠️ IMPORTANT: When you see this instruction object in Cursor, you MUST execute it by:",
            "execution_instructions": [
                f"1. Read the file: {file_path}",
                "2. Use the 'prompt' field from the instruction object as your refactoring directive",
                "3. Actually refactor the code by editing the file according to the prompt",
                "4. Preserve all existing functionality while improving structure and maintainability",
                "5. Explain what refactoring changes you made and why",
                "",
                "DO NOT just return the instruction object - you must execute it by refactoring the code!",
            ],
        }

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
        context_text = self.get_context_text(file_path_obj, tier=ContextTier.TIER2)

        # Enhancement: Auto-detect libraries and fetch Context7 documentation
        context7_docs = {}
        context7_guidance = ""
        try:
            from ...core.language_detector import LanguageDetector
            detector = LanguageDetector()
            language = detector.detect_language(file_path_obj)
            
            # Use universal auto-detection hook for Context7 docs
            context7_docs = await self._auto_fetch_context7_docs(
                code=current_code,
                prompt=f"Optimize code for {optimization_type}",
                language=language,
            )
            
            # Add Context7 guidance to prompt if available
            if context7_docs:
                context7_guidance = "\n\nRelevant Library Optimization Best Practices from Context7:\n"
                for lib_name, lib_doc in context7_docs.items():
                    if lib_doc and lib_doc.get("content"):
                        content_preview = lib_doc.get("content", "")[:500]
                        context7_guidance += f"\n{lib_name}:\n{content_preview}...\n"
                logger.debug(f"Auto-fetched Context7 docs for {len(context7_docs)} libraries using universal hook")
        except Exception as e:
            logger.debug(f"Context7 auto-detection failed during optimize: {e}, continuing without Context7 docs")

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
{context7_guidance}

Provide the optimized code that:
1. Improves {optimization_type} characteristics
2. Maintains functionality and correctness
3. Preserves code readability
4. Uses efficient algorithms and data structures
5. Eliminates unnecessary operations

Return only the optimized code, wrapped in ```python code blocks."""

        # Prepare instruction for Cursor Skills
        instruction = GenericInstruction(
            agent_name="improver",
            command="optimize",
            prompt=prompt,
            parameters={
                "file_path": str(file_path),
                "optimization_type": optimization_type,
            },
        )

        return {
            "message": f"Optimization instruction prepared for {file_path}",
            "instruction": instruction.to_dict(),
            "skill_command": instruction.to_skill_command(),
            "file": str(file_path),
            "optimization_type": optimization_type,
            "note": "⚠️ IMPORTANT: When you see this instruction object in Cursor, you MUST execute it by:",
            "execution_instructions": [
                f"1. Read the file: {file_path}",
                "2. Use the 'prompt' field from the instruction object as your optimization directive",
                f"3. Actually optimize the code for {optimization_type} by editing the file according to the prompt",
                "4. Maintain functionality and correctness while improving performance/memory characteristics",
                "5. Explain what optimizations you made and why",
                "",
                "DO NOT just return the instruction object - you must execute it by optimizing the code!",
            ],
        }

    async def _handle_improve_quality(
        self, file_path: str | None = None, focus: str | None = None, **kwargs: Any
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

        # Read current code
        current_code = file_path_obj.read_text(encoding="utf-8")

        # Get context
        context_text = self.get_context_text(file_path_obj, tier=ContextTier.TIER2)

        # Enhancement: Auto-detect libraries and fetch Context7 documentation
        context7_docs = {}
        context7_guidance = ""
        try:
            from ...core.language_detector import LanguageDetector
            detector = LanguageDetector()
            language = detector.detect_language(file_path_obj)
            
            # Use universal auto-detection hook for Context7 docs
            focus_prompt = f"Improve code quality" + (f" focusing on {focus}" if focus else "")
            context7_docs = await self._auto_fetch_context7_docs(
                code=current_code,
                prompt=focus_prompt,
                language=language,
            )
            
            # Add Context7 guidance to prompt if available
            if context7_docs:
                context7_guidance = "\n\nRelevant Library Best Practices from Context7:\n"
                for lib_name, lib_doc in context7_docs.items():
                    if lib_doc and lib_doc.get("content"):
                        content_preview = lib_doc.get("content", "")[:500]
                        context7_guidance += f"\n{lib_name}:\n{content_preview}...\n"
                logger.debug(f"Auto-fetched Context7 docs for {len(context7_docs)} libraries using universal hook")
        except Exception as e:
            logger.debug(f"Context7 auto-detection failed during improve-quality: {e}, continuing without Context7 docs")

        # Parse focus areas
        focus_areas = []
        if focus:
            focus_areas = [area.strip() for area in focus.split(",") if area.strip()]

        # Build focus-specific prompt section
        focus_text = ""
        if focus_areas:
            focus_text = "\n\nFocus specifically on these quality aspects:\n"
            for area in focus_areas:
                focus_text += f"- {area}\n"
            focus_text += "\nWhile still maintaining general code quality standards."

        prompt = f"""Improve the overall code quality of the following code:
        
Current code:
```python
{current_code}
```

Context (other related files):
{context_text}
{focus_text}
{context7_guidance}

Provide improved code that:
1. Follows Python best practices and PEP 8 style guide
2. Uses appropriate design patterns
3. Improves error handling and robustness
4. Enhances type hints and documentation
5. Reduces code complexity where possible
6. Improves naming conventions
7. Adds appropriate docstrings

Return only the improved code, wrapped in ```python code blocks."""

        # Issue 8 Fix: Return instruction object for Cursor Skills execution
        # Note: MAL has been removed from the project. In Cursor-first mode,
        # code improvement is handled by Cursor Skills using the instruction object.
        # The instruction object contains all necessary information for Cursor AI
        # to improve the code when executed in Cursor chat.

        # Prepare instruction for Cursor Skills (always returned for compatibility)
        instruction = GenericInstruction(
            agent_name="improver",
            command="improve-quality",
            prompt=prompt,
            parameters={"file_path": str(file_path), "focus": focus},
        )

        result = {
            "message": f"Code quality improvement instruction prepared for {file_path}",
            "instruction": instruction.to_dict(),
            "skill_command": instruction.to_skill_command(),
            "file": str(file_path),
            "file_written": False,  # Code improvement happens in Cursor Skills
            "note": "⚠️ IMPORTANT: When you see this instruction object in Cursor, you MUST execute it by:",
            "execution_instructions": [
                f"1. Read the file: {file_path}",
                "2. Use the 'prompt' field from the instruction object as your improvement directive",
                "3. Actually improve the code by editing the file according to the prompt",
                "4. Apply all quality improvements (best practices, type hints, documentation, etc.)",
                "5. Explain what improvements you made and why",
                "",
                "DO NOT just return the instruction object - you must execute it by improving the code!",
            ],
        }
        
        return result

    def _handle_help(self) -> dict[str, Any]:
        """
        Return help information for Improver Agent.
        
        Returns standardized help format with commands and descriptions.
        
        Returns:
            dict: Help information with standardized format:
                - type (str): Always "help"
                - content (str): Formatted markdown help text containing:
                    - Available commands with descriptions
                    
        Note:
            This method is synchronous as it performs no I/O operations.
            Standardized to match format used by other agents (type + content keys).
        """
        help_message = {
            "*refactor [file_path] [instruction]": "Refactor existing code to improve structure and maintainability",
            "*optimize [file_path] [type]": "Optimize code for performance, memory, or both (type: performance|memory|both)",
            "*improve-quality [file_path]": "Improve overall code quality (best practices, patterns, documentation)",
            "*help": "Show this help message",
        }
        
        # Format as markdown for consistency with other agents
        command_lines = [
            f"- **{cmd}**: {desc}"
            for cmd, desc in help_message.items()
        ]
        
        content = f"""# {self.agent_name} - Help

## Available Commands

{chr(10).join(command_lines)}
"""
        
        return {"type": "help", "content": content}

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
