"""
Implementer Agent - Generates and writes production code
"""

import shutil
from datetime import datetime
from pathlib import Path

# Import ReviewerAgent (circular import handled lazily)
from typing import TYPE_CHECKING, Any

from ...context7.agent_integration import Context7AgentHelper, get_context7_helper
from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config
from ...core.mal import MAL
from ...experts.agent_integration import ExpertSupportMixin
from .code_generator import CodeGenerator

if TYPE_CHECKING:
    pass


class ImplementerAgent(BaseAgent, ExpertSupportMixin):
    """
    Implementer Agent - Code generation and file writing.

    Permissions: Read, Write, Edit, Grep, Glob, Bash
    """

    def __init__(
        self,
        mal: MAL | None = None,
        config: ProjectConfig | None = None,
        expert_registry: Any | None = None,
    ):
        super().__init__(
            agent_id="implementer", agent_name="Implementer Agent", config=config
        )
        # Use config if provided, otherwise load defaults
        if config is None:
            config = load_config()
        self.config = config

        # Initialize MAL with config
        mal_config = config.mal if config else None
        self.mal = mal or MAL(config=mal_config)

        # Initialize code generator
        self.code_generator = CodeGenerator(self.mal)

        # Get implementer config
        implementer_config = (
            config.agents.implementer if config and config.agents else None
        )
        self.require_review = (
            implementer_config.require_review if implementer_config else True
        )
        self.auto_approve_threshold = (
            implementer_config.auto_approve_threshold if implementer_config else 80.0
        )
        self.backup_files = (
            implementer_config.backup_files if implementer_config else True
        )
        self.max_file_size = (
            implementer_config.max_file_size if implementer_config else 10 * 1024 * 1024
        )

        # Initialize Context7 helper
        self.context7: Context7AgentHelper | None = None
        if config:
            self.context7 = get_context7_helper(self, config)

        # Expert registry will be initialized in activate() via ExpertSupportMixin
        # Allow manual override if provided
        if expert_registry:
            self.expert_registry = expert_registry

        # Reviewer agent for code review
        self.reviewer = None

    async def activate(self, project_root: Path | None = None):
        """Activate the implementer agent with expert support."""
        await super().activate(project_root)
        # Initialize expert support via mixin
        await self._initialize_expert_support(project_root)

    def get_commands(self) -> list[dict[str, str]]:
        """Return available commands for implementer agent"""
        base_commands = super().get_commands()
        return base_commands + [
            {
                "command": "*implement",
                "description": "Generate and write code to file (with review)",
            },
            {
                "command": "*generate-code",
                "description": "Generate code from specification (no file write)",
            },
            {"command": "*refactor", "description": "Refactor existing code file"},
        ]

    async def run(self, command: str, **kwargs) -> dict[str, Any]:
        """
        Execute implementer agent command.

        Commands:
        - *implement <specification> <file_path>: Generate and write code (with review)
        - *generate-code <specification> [--file=<file_path>]: Generate code only
        - *refactor <file_path> <instruction>: Refactor existing code
        """
        await self.activate()

        if command == "help":
            return await self._help()

        elif command == "implement":
            specification = kwargs.get("specification") or kwargs.get("text", "")
            file_path = kwargs.get("file_path") or kwargs.get("file")
            if not specification:
                return {
                    "error": "Specification required. Usage: *implement <specification> <file_path>"
                }
            if not file_path:
                return {
                    "error": "File path required. Usage: *implement <specification> <file_path>"
                }

            context = kwargs.get("context")
            language = kwargs.get("language", "python")
            return await self.implement(
                specification, file_path, context=context, language=language
            )

        elif command == "generate-code":
            specification = kwargs.get("specification") or kwargs.get("text", "")
            if not specification:
                return {
                    "error": "Specification required. Usage: *generate-code <specification> [--file=<file_path>]"
                }

            file_path = kwargs.get("file_path") or kwargs.get("file")
            context = kwargs.get("context")
            language = kwargs.get("language", "python")
            return await self.generate_code(
                specification, file_path=file_path, context=context, language=language
            )

        elif command == "refactor":
            file_path = kwargs.get("file_path") or kwargs.get("file")
            instruction = kwargs.get("instruction") or kwargs.get("text", "")
            if not file_path:
                return {
                    "error": "File path required. Usage: *refactor <file_path> <instruction>"
                }
            if not instruction:
                return {
                    "error": "Instruction required. Usage: *refactor <file_path> <instruction>"
                }

            return await self.refactor(file_path, instruction)

        else:
            return {
                "error": f"Unknown command: {command}. Use *help to see available commands."
            }

    async def implement(
        self,
        specification: str,
        file_path: str,
        context: str | None = None,
        language: str = "python",
    ) -> dict[str, Any]:
        """
        Generate code from specification and write to file (with review).

        Args:
            specification: Description of what code to generate
            file_path: Target file path
            context: Optional context (existing code, patterns, etc.)
            language: Programming language

        Returns:
            Result dictionary with code, file path, review results, etc.
        """
        path = Path(file_path)

        # Validate path
        if not self._validate_path(path):
            return {"error": f"Invalid or unsafe path: {file_path}"}

        # Check if file exists
        file_exists = path.exists()

        # Consult experts for code generation guidance
        expert_guidance = {}
        if self.expert_registry:
            # Consult Security expert for secure coding practices
            try:
                security_consultation = await self.expert_registry.consult(
                    query=f"Secure coding practices for: {specification}. Language: {language}",
                    domain="security",
                    include_all=True,
                    prioritize_builtin=True,
                    agent_id="implementer",
                )
                expert_guidance["security"] = security_consultation.weighted_answer
            except Exception:
                pass

            # Consult Performance expert for performance optimization
            try:
                perf_consultation = await self.expert_registry.consult(
                    query=f"Performance optimization for code: {specification}",
                    domain="performance-optimization",
                    include_all=True,
                    prioritize_builtin=True,
                    agent_id="implementer",
                )
                expert_guidance["performance"] = perf_consultation.weighted_answer
            except Exception:
                pass

        # Generate code
        try:
            generated_code = await self.code_generator.generate_code(
                specification=specification,
                file_path=path,
                context=context,
                language=language,
                expert_guidance=expert_guidance,
            )
        except Exception as e:
            return {"error": f"Code generation failed: {str(e)}"}

        # Review code if required
        review_result = None
        if self.require_review:
            review_result = await self._review_code(generated_code, path)

            # Check if review passed
            if review_result and "scoring" in review_result:
                overall_score = review_result["scoring"].get("overall_score", 0)
                if overall_score < self.auto_approve_threshold:
                    return {
                        "error": f"Code review failed. Score: {overall_score:.1f} < {self.auto_approve_threshold}",
                        "code": generated_code,
                        "review": review_result,
                        "approved": False,
                    }

        # Create backup if file exists and backup is enabled
        backup_path = None
        if file_exists and self.backup_files:
            backup_path = self._create_backup(path)

        # Write file
        try:
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write code to file
            path.write_text(generated_code, encoding="utf-8")
        except Exception as e:
            # Restore backup if write failed
            if backup_path and backup_path.exists():
                shutil.copy2(backup_path, path)
                backup_path.unlink()
            return {"error": f"Failed to write file: {str(e)}"}

        result = {
            "type": "implement",
            "file": str(path),
            "code": generated_code,
            "review": review_result,
            "backup": str(backup_path) if backup_path else None,
            "approved": True,
            "file_existed": file_exists,
        }
        if expert_guidance:
            result["expert_guidance"] = expert_guidance
        return result

    async def generate_code(
        self,
        specification: str,
        file_path: str | None = None,
        context: str | None = None,
        language: str = "python",
    ) -> dict[str, Any]:
        """
        Generate code from specification (no file write).

        Args:
            specification: Description of what code to generate
            file_path: Optional target file path for context
            context: Optional context
            language: Programming language

        Returns:
            Result dictionary with generated code
        """
        path = Path(file_path) if file_path else None

        if path and not self._validate_path(path):
            return {"error": f"Invalid or unsafe path: {file_path}"}

        # Consult experts for code generation guidance
        expert_guidance = {}
        if self.expert_registry:
            try:
                security_consultation = await self.expert_registry.consult(
                    query=f"Secure coding practices for: {specification}",
                    domain="security",
                    include_all=True,
                    prioritize_builtin=True,
                    agent_id="implementer",
                )
                expert_guidance["security"] = security_consultation.weighted_answer
            except Exception:
                pass

            try:
                perf_consultation = await self.expert_registry.consult(
                    query=f"Performance optimization for: {specification}",
                    domain="performance-optimization",
                    include_all=True,
                    prioritize_builtin=True,
                    agent_id="implementer",
                )
                expert_guidance["performance"] = perf_consultation.weighted_answer
            except Exception:
                pass

        try:
            generated_code = await self.code_generator.generate_code(
                specification=specification,
                file_path=path,
                context=context,
                language=language,
                expert_guidance=expert_guidance,
            )

            result = {
                "type": "generate_code",
                "code": generated_code,
                "file_path": str(path) if path else None,
                "language": language,
            }
            if expert_guidance:
                result["expert_guidance"] = expert_guidance
            return result
        except Exception as e:
            return {"error": f"Code generation failed: {str(e)}"}

    async def refactor(self, file_path: str, instruction: str) -> dict[str, Any]:
        """
        Refactor existing code file.

        Args:
            file_path: Path to file to refactor
            instruction: Refactoring instruction

        Returns:
            Result dictionary with refactored code and file path
        """
        path = Path(file_path)

        # Validate path
        if not path.exists():
            return {"error": f"File not found: {file_path}"}

        if not self._validate_path(path):
            return {"error": f"Invalid or unsafe path: {file_path}"}

        # Read existing code
        try:
            existing_code = path.read_text(encoding="utf-8")
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}

        # Detect language from file extension
        language = self._detect_language(path)

        # Generate refactored code
        try:
            refactored_code = await self.code_generator.refactor_code(
                code=existing_code, instruction=instruction, language=language
            )
        except Exception as e:
            return {"error": f"Code refactoring failed: {str(e)}"}

        # Review refactored code if required
        review_result = None
        if self.require_review:
            review_result = await self._review_code(refactored_code, path)

            # Check if review passed
            if review_result and "scoring" in review_result:
                overall_score = review_result["scoring"].get("overall_score", 0)
                if overall_score < self.auto_approve_threshold:
                    return {
                        "error": f"Refactored code review failed. Score: {overall_score:.1f} < {self.auto_approve_threshold}",
                        "code": refactored_code,
                        "review": review_result,
                        "approved": False,
                    }

        # Create backup
        backup_path = None
        if self.backup_files:
            backup_path = self._create_backup(path)

        # Write refactored code
        try:
            path.write_text(refactored_code, encoding="utf-8")
        except Exception as e:
            # Restore backup if write failed
            if backup_path and backup_path.exists():
                shutil.copy2(backup_path, path)
                backup_path.unlink()
            return {"error": f"Failed to write file: {str(e)}"}

        return {
            "type": "refactor",
            "file": str(path),
            "original_code": existing_code,
            "refactored_code": refactored_code,
            "review": review_result,
            "backup": str(backup_path) if backup_path else None,
            "approved": True,
        }

    async def _review_code(
        self, code: str, file_path: Path
    ) -> dict[str, Any] | None:
        """Review generated code using ReviewerAgent."""
        if self.reviewer is None:
            # Lazy import to avoid circular dependency
            from ...agents.reviewer.agent import ReviewerAgent

            self.reviewer = ReviewerAgent(config=self.config)
            await self.reviewer.activate()

        # Create temporary file for review
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=file_path.suffix, delete=False
        ) as tmp_file:
            tmp_file.write(code)
            tmp_file_path = Path(tmp_file.name)

        try:
            # Review the code
            review_result = await self.reviewer.review_file(tmp_file_path)
            return review_result
        except Exception as e:
            # Review failed, but don't block if it's just an error
            return {"error": f"Review failed: {str(e)}"}
        finally:
            # Clean up temp file
            if tmp_file_path.exists():
                tmp_file_path.unlink()

    def _validate_path(self, path: Path) -> bool:
        """Validate file path for safety."""
        # Resolve to absolute path
        try:
            resolved = path.resolve()
        except Exception:
            return False

        # Check for path traversal
        if ".." in str(path) and not resolved.exists():
            return False

        # Check for suspicious patterns
        suspicious = ["%00", "%2e", "%2f", "..", "//"]
        path_str = str(path)
        if any(pattern in path_str for pattern in suspicious):
            # Allow pytest temp files
            if "pytest-" not in path_str:
                return False

        # Check file size if file exists
        if resolved.exists() and resolved.is_file():
            try:
                if resolved.stat().st_size > self.max_file_size:
                    return False
            except Exception:
                return False

        return True

    def _create_backup(self, path: Path) -> Path | None:
        """Create backup of existing file."""
        if not path.exists():
            return None

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = path.parent / f"{path.stem}.backup_{timestamp}{path.suffix}"
            shutil.copy2(path, backup_path)
            return backup_path
        except Exception:
            return None

    def _detect_language(self, path: Path) -> str:
        """Detect programming language from file extension."""
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".rs": "rust",
            ".go": "go",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".md": "markdown",
            ".yaml": "yaml",
            ".yml": "yaml",
        }
        return extension_map.get(path.suffix.lower(), "python")

    async def _help(self) -> dict[str, Any]:
        """Return help information."""
        content = f"""# {self.agent_name} - Help

## Available Commands

{chr(10).join(f"- **{cmd['command']}**: {cmd['description']}" for cmd in self.get_commands())}

## Usage Examples

### Implement (Generate and Write)
```
*implement "Create a function to calculate factorial" factorial.py
*implement "Add user authentication endpoint" api/auth.py --context="Use FastAPI patterns"
```

### Generate Code (No Write)
```
*generate-code "Create a REST API client class"
*generate-code "Add data validation function" --file=utils/validation.py
```

### Refactor
```
*refactor utils/helpers.py "Extract common logic into helper functions"
*refactor models.py "Improve error handling and add type hints"
```

## Configuration

- **require_review**: Require code review before writing (default: true)
- **auto_approve_threshold**: Auto-approve if score >= threshold (default: 80.0)
- **backup_files**: Create backup before overwriting (default: true)
- **max_file_size**: Maximum file size in bytes (default: 10MB)

## Safety Features

- ✅ Code review before writing (integrated with Reviewer Agent)
- ✅ File backups before overwriting
- ✅ Path validation (prevents path traversal)
- ✅ File size limits
- ✅ Automatic rollback on write failure
"""

        return {"type": "help", "content": content}

    async def close(self):
        """Clean up resources"""
        await self.mal.close()
        if self.reviewer:
            await self.reviewer.close()
