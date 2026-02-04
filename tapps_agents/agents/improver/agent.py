"""
Improver Agent - Refactors and enhances existing code

Phase 7.1: Auto-Apply Enhancement - adds --auto-apply and --preview flags
"""

import difflib
import inspect
import logging
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ...context7.agent_integration import Context7AgentHelper, get_context7_helper
from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config
from ...core.instructions import GenericInstruction
from ...core.tiered_context import ContextTier

logger = logging.getLogger(__name__)


@dataclass
class DiffResult:
    """Result of code diff generation."""
    
    unified_diff: str
    lines_added: int
    lines_removed: int
    has_changes: bool
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


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
        self,
        file_path: str | None = None,
        focus: str | None = None,
        auto_apply: bool = False,
        preview: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Improve overall code quality (structure, patterns, best practices).
        
        Phase 7.1 Enhancement: Added --auto-apply and --preview flags.
        
        Args:
            file_path: Path to file to improve
            focus: Specific areas to focus on (comma-separated)
            auto_apply: If True, automatically apply improvements
            preview: If True, show diff preview without applying
        """
        if not file_path:
            return {"error": "File path required. Usage: *improve-quality <file_path> [--auto-apply] [--preview]"}

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
            focus_prompt = "Improve code quality" + (f" focusing on {focus}" if focus else "")
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

        # Prepare instruction for Cursor Skills (always returned for compatibility)
        instruction = GenericInstruction(
            agent_name="improver",
            command="improve-quality",
            prompt=prompt,
            parameters={"file_path": str(file_path), "focus": focus},
        )

        # Phase 7.1: Generate diff preview if requested or for auto-apply
        if preview or auto_apply:
            # Note: In Cursor-first mode, actual code generation is done by Cursor AI.
            # The diff is generated from placeholder improved code for preview purposes.
            # When auto_apply is True, Cursor AI should use this as a signal to apply changes.
            self._generate_diff(
                current_code, 
                current_code,  # Placeholder - actual improvement done by Cursor AI
                str(file_path)
            )
        
        # Phase 7.1: Handle auto-apply mode
        if auto_apply:
            # Create backup before any modifications
            backup_path = self._create_backup(str(file_path_obj))
            
            result = {
                "message": f"Auto-apply mode enabled for {file_path}",
                "mode": "auto_apply",
                "instruction": instruction.to_dict(),
                "skill_command": instruction.to_skill_command(),
                "file": str(file_path),
                "backup": str(backup_path) if backup_path else None,
                "auto_apply": True,
                "note": "⚠️ AUTO-APPLY MODE: Cursor AI should automatically apply improvements and verify:",
                "execution_instructions": [
                    f"1. Read the file: {file_path}",
                    "2. Apply the improvements from the 'prompt' field",
                    "3. Write the improved code to the file",
                    f"4. Backup has been created at: {backup_path}",
                    "5. Run verification review after applying changes",
                    "6. Report the diff of changes made",
                    "",
                    "APPLY THE CHANGES - do not just return the instruction!",
                ],
            }
            return result
        
        # Phase 7.1: Handle preview mode
        if preview:
            result = {
                "message": f"Preview mode for {file_path}",
                "mode": "preview",
                "instruction": instruction.to_dict(),
                "skill_command": instruction.to_skill_command(),
                "file": str(file_path),
                "preview": True,
                "note": "⚠️ PREVIEW MODE: Show what would change without applying:",
                "execution_instructions": [
                    f"1. Read the file: {file_path}",
                    "2. Generate improved code based on the 'prompt' field",
                    "3. Show a DIFF of proposed changes (do NOT apply)",
                    "4. Show statistics: lines added, lines removed",
                    "5. Suggest: 'Use --auto-apply to apply these changes'",
                    "",
                    "DO NOT APPLY CHANGES - only show the preview!",
                ],
            }
            return result
        
        # Default mode: Return instruction object for manual execution
        result = {
            "message": f"Code quality improvement instruction prepared for {file_path}",
            "mode": "instruction",
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
                "",
                "TIP: Use --auto-apply to automatically apply improvements",
                "TIP: Use --preview to see changes before applying",
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
    
    # ========================================================================
    # Phase 7.1: Auto-Apply Enhancement Methods
    # ========================================================================
    
    def _create_backup(self, file_path: str) -> Path | None:
        """
        Create backup of file before modifications.
        
        Phase 7.1: Auto-Apply Enhancement
        
        Args:
            file_path: Path to file to backup
            
        Returns:
            Path to backup file, or None if backup failed
            
        Backup Location:
            .tapps-agents/backups/<filename>.<timestamp>.backup
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.is_absolute():
                file_path_obj = self.project_root / file_path_obj
            
            if not file_path_obj.exists():
                logger.warning(f"Cannot backup non-existent file: {file_path}")
                return None
            
            # Create backup directory
            backup_dir = self.project_root / ".tapps-agents" / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_filename = f"{file_path_obj.name}.{timestamp}.backup"
            backup_path = backup_dir / backup_filename
            
            # Copy file to backup location
            shutil.copy2(file_path_obj, backup_path)
            logger.info(f"Created backup: {backup_path}")
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create backup for {file_path}: {e}")
            return None
    
    def _apply_improvements(
        self, file_path: str, improved_code: str
    ) -> dict[str, Any]:
        """
        Apply improved code to file.
        
        Phase 7.1: Auto-Apply Enhancement
        
        Args:
            file_path: Path to file to modify
            improved_code: Improved code content
            
        Returns:
            Dictionary with result status
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.is_absolute():
                file_path_obj = self.project_root / file_path_obj
            
            if not improved_code or not improved_code.strip():
                return {"success": False, "error": "Improved code is empty"}
            
            # Write improved code
            file_path_obj.write_text(improved_code, encoding="utf-8")
            logger.info(f"Applied improvements to: {file_path}")
            
            return {
                "success": True,
                "file": str(file_path_obj),
                "bytes_written": len(improved_code.encode("utf-8")),
            }
            
        except Exception as e:
            logger.error(f"Failed to apply improvements to {file_path}: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_diff(
        self, original: str, improved: str, file_path: str = "file"
    ) -> dict[str, Any]:
        """
        Generate unified diff between original and improved code.
        
        Phase 7.1: Auto-Apply Enhancement
        
        Args:
            original: Original code content
            improved: Improved code content
            file_path: File path for diff header
            
        Returns:
            Dictionary with diff result
        """
        try:
            original_lines = original.splitlines(keepends=True)
            improved_lines = improved.splitlines(keepends=True)
            
            # Generate unified diff
            diff_lines = list(difflib.unified_diff(
                original_lines,
                improved_lines,
                fromfile=f"original/{file_path}",
                tofile=f"improved/{file_path}",
                lineterm="",
            ))
            
            unified_diff = "".join(diff_lines)
            
            # Calculate statistics
            lines_added = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
            lines_removed = sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))
            has_changes = bool(diff_lines)
            
            return DiffResult(
                unified_diff=unified_diff,
                lines_added=lines_added,
                lines_removed=lines_removed,
                has_changes=has_changes,
            ).to_dict()
            
        except Exception as e:
            logger.error(f"Failed to generate diff: {e}")
            return DiffResult(
                unified_diff="",
                lines_added=0,
                lines_removed=0,
                has_changes=False,
            ).to_dict()
    
    async def _verify_changes(self, file_path: str) -> dict[str, Any]:
        """
        Run verification review after applying changes.
        
        Phase 7.1: Auto-Apply Enhancement
        
        Args:
            file_path: Path to modified file
            
        Returns:
            Dictionary with verification results
        """
        try:
            # Import reviewer agent for verification
            from ..reviewer.agent import ReviewerAgent
            
            reviewer = ReviewerAgent(config=self.config)
            await reviewer.activate(self.project_root, offline_mode=True)
            
            file_path_obj = Path(file_path)
            if not file_path_obj.is_absolute():
                file_path_obj = self.project_root / file_path_obj
            
            # Run review
            review_result = await reviewer.review_file(file_path_obj)
            
            # Extract score
            scores = review_result.get("scoring", {})
            overall_score = scores.get("overall_score", 0.0)
            
            return {
                "verified": True,
                "new_score": overall_score,
                "scores": scores,
                "review": review_result,
            }
            
        except Exception as e:
            logger.error(f"Failed to verify changes for {file_path}: {e}")
            return {
                "verified": False,
                "error": str(e),
            }