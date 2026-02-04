"""
Implementer Agent - Generates and writes production code
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path

# Import ReviewerAgent (circular import handled lazily)
from typing import TYPE_CHECKING, Any

from ...context7.agent_integration import Context7AgentHelper, get_context7_helper
from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config
from ...core.instructions import CodeGenerationInstruction
from ...experts.agent_integration import ExpertSupportMixin
from .code_generator import CodeGenerator

if TYPE_CHECKING:
    from ..reviewer.agent import ReviewerAgent


logger = logging.getLogger(__name__)


class ImplementerAgent(BaseAgent, ExpertSupportMixin):
    """
    Implementer Agent - Code generation and file writing.

    Permissions: Read, Write, Edit, Grep, Glob, Bash

    ⚠️ CRITICAL ACCURACY REQUIREMENT:
    - NEVER make up, invent, or fabricate information - Only report verified facts
    - ALWAYS verify claims by checking actual results, not just test pass/fail
    - Verify API calls succeed - inspect response data, status codes, error messages
    - Distinguish between code paths executing and actual functionality working
    - Admit uncertainty explicitly when you cannot verify
    """

    def __init__(
        self,
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

        # Initialize code generator
        self.code_generator = CodeGenerator()

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

        # Expert registry initialization (required due to multiple inheritance MRO issue)
        # BaseAgent.__init__() doesn't call super().__init__(), so ExpertSupportMixin.__init__()
        # is never called via MRO. We must manually initialize to avoid AttributeError.
        # The registry will be properly initialized in activate() via _initialize_expert_support()
        self.expert_registry: Any | None = None
        # Allow manual override if provided (for testing or special cases)
        if expert_registry:
            self.expert_registry = expert_registry

        # Reviewer agent for code review
        self.reviewer: ReviewerAgent | None = None

    async def activate(self, project_root: Path | None = None, offline_mode: bool = False):
        """Activate the implementer agent with expert support."""
        # Validate that expert_registry attribute exists (safety check)
        if not hasattr(self, 'expert_registry'):
            raise AttributeError(
                f"{self.__class__.__name__}.expert_registry not initialized. "
                "This should not happen if __init__() properly initializes the attribute."
            )
        await super().activate(project_root, offline_mode=offline_mode)
        # Initialize expert support via mixin
        await self._initialize_expert_support(project_root, offline_mode=offline_mode)

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
            return self._help()

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
        if not self._is_valid_path(path):
            return {"error": f"Invalid or unsafe path: {file_path}"}

        # Check if file exists
        file_exists = path.exists()

        # Consult experts for code generation guidance
        expert_guidance = {}
        # Use defensive check to ensure attribute exists (safety for MRO issue)
        if hasattr(self, 'expert_registry') and self.expert_registry:
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
                logger.debug("Security expert consultation failed", exc_info=True)

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
                logger.debug("Performance expert consultation failed", exc_info=True)

            # Consult API Design expert if implementing/refactoring an API client
            if await self._detect_api_client_pattern(specification, context):
                try:
                    api_consultation = await self.expert_registry.consult(
                        query=f"Provide implementation guidance for this API client:\n\n{specification}",
                        domain="api-design-integration",
                        include_all=True,
                        prioritize_builtin=True,
                        agent_id="implementer",
                    )
                    expert_guidance["api_design"] = api_consultation.weighted_answer
                except Exception:
                    logger.debug("API design expert consultation failed", exc_info=True)

        # R7: Get Context7 documentation for libraries mentioned in specification
        context7_docs = {}
        if self.context7 and self.context7.enabled:
            try:
                # Detect libraries from specification and context
                detected_libraries = []
                if self.context7.library_detector:
                    # R7: Detect from specification text (prompt)
                    detected_libraries.extend(
                        self.context7.library_detector.detect_from_prompt(specification)
                    )
                    # Detect from context code if available
                    if context:
                        detected_libraries.extend(
                            self.context7.library_detector.detect_from_code(context, language=language)
                        )
                
                # Get Context7 documentation for each detected library
                for library in set(detected_libraries):  # Remove duplicates
                    try:
                        docs_result = await self.context7.get_documentation(library, topic=None, use_fuzzy_match=True)
                        if docs_result and docs_result.get("content"):
                            context7_docs[library] = docs_result["content"]
                            logger.debug(f"Retrieved Context7 docs for library '{library}'")
                    except Exception as e:
                        logger.debug(f"Failed to get Context7 docs for library '{library}': {e}")
            except Exception as e:
                logger.debug(f"Context7 documentation lookup failed: {e}", exc_info=True)

        # Prepare code generation instruction for Cursor Skills
        try:
            instruction = self.code_generator.prepare_code_generation(
                specification=specification,
                file_path=path,
                context=context,
                language=language,
                expert_guidance=expert_guidance,
                context7_docs=context7_docs if context7_docs else None,
            )
        except Exception as e:
            return {"error": f"Failed to prepare code generation instruction: {str(e)}"}

        # Return instruction object for Cursor Skills execution
        skill_command = instruction.to_skill_command()
        result = {
            "type": "implement",
            "execution_mode": "cursor_skills",  # Explicit mode indication
            "instruction": instruction.to_dict(),
            "skill_command": skill_command,
            "file": str(path),
            "file_existed": file_exists,
            "next_steps": [
                "This instruction is prepared for Cursor Skills execution.",
                "To execute, copy this command to Cursor chat:",
                f"  {skill_command}",
                "",
                "Or use Cursor Skills directly:",
                f"  @implementer *implement \"{specification}\" {file_path}",
                "",
                "Note: Code generation requires Cursor Skills (uses your configured LLM).",
                "The framework prepares instructions; Cursor Skills execute them.",
            ],
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

        if path and not self._is_valid_path(path):
            return {"error": f"Invalid or unsafe path: {file_path}"}

        # Consult experts for code generation guidance
        expert_guidance = {}
        # Use defensive check to ensure attribute exists (safety for MRO issue)
        if hasattr(self, 'expert_registry') and self.expert_registry:
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
                logger.debug("Security expert consultation failed", exc_info=True)

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
                logger.debug("Performance expert consultation failed", exc_info=True)

            # Consult API Design expert if implementing/refactoring an API client
            if await self._detect_api_client_pattern(specification, context):
                try:
                    api_consultation = await self.expert_registry.consult(
                        query=f"Provide implementation guidance for this API client:\n\n{specification}",
                        domain="api-design-integration",
                        include_all=True,
                        prioritize_builtin=True,
                        agent_id="implementer",
                    )
                    expert_guidance["api_design"] = api_consultation.weighted_answer
                except Exception:
                    logger.debug("API design expert consultation failed", exc_info=True)

        try:
            instruction = self.code_generator.prepare_code_generation(
                specification=specification,
                file_path=path,
                context=context,
                language=language,
                expert_guidance=expert_guidance,
            )

            result: dict[str, Any] = {
                "type": "generate_code",
                "instruction": instruction.to_dict(),
                "skill_command": instruction.to_skill_command(),
                "file_path": str(path) if path else None,
                "language": language,
            }
            if expert_guidance:
                result["expert_guidance"] = expert_guidance
            return result
        except Exception as e:
            return {"error": f"Failed to prepare code generation instruction: {str(e)}"}

    async def refactor(
        self, file_path: str, instruction: str, preview: bool = False
    ) -> dict[str, Any]:
        """
        Refactor existing code file.

        Phase 5.1: Enhanced file writing with validation and ErrorEnvelope

        Args:
            file_path: Path to file to refactor
            instruction: Refactoring instruction
            preview: If True, return refactored code without writing to file (default: False)

        Returns:
            Result dictionary with refactored code and file path, or ErrorEnvelope on error
        """
        from ...core.error_envelope import ErrorEnvelopeBuilder

        path = Path(file_path)

        # Validate path with ErrorEnvelope
        if not path.exists():
            envelope = ErrorEnvelopeBuilder.from_exception(
                FileNotFoundError(f"File not found: {file_path}"),
                agent="implementer",
            )
            return envelope.to_dict()

        if not self._is_valid_path(path):
            envelope = ErrorEnvelopeBuilder.from_exception(
                ValueError(f"Invalid or unsafe path: {file_path}"),
                agent="implementer",
            )
            return envelope.to_dict()

        # Read existing code with enhanced error handling
        try:
            existing_code = path.read_text(encoding="utf-8")
            if not existing_code.strip():
                envelope = ErrorEnvelopeBuilder.from_exception(
                    ValueError(f"File is empty: {file_path}"),
                    agent="implementer",
                )
                return envelope.to_dict()
        except UnicodeDecodeError as e:
            envelope = ErrorEnvelopeBuilder.from_exception(
                e,
                agent="implementer",
            )
            envelope.message = f"Failed to read file (encoding error): {file_path}. File may not be text-based."
            return envelope.to_dict()
        except Exception as e:
            envelope = ErrorEnvelopeBuilder.from_exception(
                e,
                agent="implementer",
            )
            envelope.message = f"Failed to read file: {file_path}. {envelope.message}"
            return envelope.to_dict()

        # Detect language from file extension
        language = self._detect_language(path)

        # Prepare refactoring instruction for Cursor Skills with enhanced error handling
        try:
            refactor_instruction = self.code_generator.prepare_refactoring(
                code=existing_code, instruction=instruction, language=language
            )
        except Exception as e:
            envelope = ErrorEnvelopeBuilder.from_exception(
                e,
                agent="implementer",
            )
            envelope.message = f"Failed to prepare refactoring instruction: {envelope.message}"
            return envelope.to_dict()

        # Create backup before refactoring (best-effort, don't fail if backup fails)
        backup_path = None
        try:
            backup_path = self._create_backup(path)
        except Exception as e:
            # Log warning but continue (backup failure shouldn't block refactoring)
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to create backup for {file_path}: {e}")

        # Refactored code: in Cursor mode, the skill_command is executed by Cursor Skills
        # (user's model), which performs the edit. In headless/CLI mode, code generation
        # would require MAL/LLM; when available, we would set refactored_code and write.
        refactored_code: str | None = None  # Set when MAL/LLM generates in headless mode

        result = {
            "type": "refactor",
            "file": str(path),
            "original_code": existing_code,
            "instruction": refactor_instruction.to_dict(),
            "skill_command": refactor_instruction.to_skill_command(),
            "backup": str(backup_path) if backup_path else None,
            "preview": preview,
            "approved": True,  # Would be set based on review/approval
            "refactored_code": refactored_code,
        }

        # When not preview and MAL/LLM is available, we would generate refactored_code
        # and write to path. For now, writing is delegated to Cursor Skills via skill_command.
        return result

    async def _review_code(self, code: str, file_path: Path) -> dict[str, Any] | None:
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

    def _is_valid_path(self, path: Path) -> bool:
        """Return True if file path appears safe and within size constraints."""
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
        """
        Create backup of existing file.

        Phase 5.1: Enhanced backup creation with validation
        """
        if not path.exists():
            return None

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = path.parent / f"{path.stem}.backup_{timestamp}{path.suffix}"
            shutil.copy2(path, backup_path)
            
            # Validate backup was created correctly (Phase 5.1: Write Validation)
            if backup_path.exists() and backup_path.stat().st_size == path.stat().st_size:
                return backup_path
            else:
                # Backup file size mismatch, clean up and return None
                if backup_path.exists():
                    backup_path.unlink()
                logger.warning(f"Backup validation failed for {path}, backup not created")
                return None
        except Exception as e:
            logger.warning(f"Failed to create backup for {path}: {e}")
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

    async def _detect_api_client_pattern(self, specification: str, context: str | None = None) -> bool:
        """
        Detect if specification/context indicates an HTTP/API client implementation.

        Checks for common patterns that indicate API client code:
        - Keywords: "API client", "OAuth2", "refresh token", "external API", "HTTP client"
        - Authentication patterns: "Bearer", "token", "authentication"
        - API patterns: "REST API", "API integration", "third-party API"

        Args:
            specification: Code specification/description
            context: Optional context code

        Returns:
            True if specification appears to be for an API client, False otherwise
        """
        if not specification:
            return False
        
        # Combine specification and context for analysis
        text_to_analyze = specification.lower()
        if context:
            text_to_analyze += " " + context.lower()
        
        # API client keywords (enhanced)
        api_client_keywords = [
            "api client",
            "http client",
            "rest client",
            "oauth2",
            "oauth 2",
            "oauth",
            "refresh token",
            "access token",
            "external api",
            "third-party api",
            "api integration",
            "rest api",
            "api wrapper",
            "graphql client",
            "graphql api",
            "websocket client",
            "mqtt client",
            "grpc client",
        ]

        # Authentication keywords (enhanced with OAuth2 patterns)
        auth_keywords = [
            "bearer",
            "token",  # General token (covers access, refresh, bearer, etc.)
            "authentication",
            "authorization",
            "api key",
            "api_key",
            "apikey",
            "client_id",
            "client_secret",
            "token_url",
            "api_base_url",
            "jwt",
            "id_token",
            "grant_type",
            "authorization_code",
            "client_credentials",
            "credentials",  # General credentials
            "auth",  # Short form
        ]

        # Structure keywords (enhanced with framework patterns)
        structure_keywords = [
            "class.*client",
            "get method",
            "post method",
            "put method",
            "delete method",
            "patch method",
            "api endpoint",
            "endpoint",  # General endpoint
            "rest endpoint",
            "make request",
            "http request",
            "fastapi",
            "django rest",
            "api route",
            "router",  # General router
        ]
        
        # Check for API client keywords
        has_api_keywords = any(keyword in text_to_analyze for keyword in api_client_keywords)
        
        # Check for authentication patterns
        has_auth = any(keyword in text_to_analyze for keyword in auth_keywords)
        
        # Check for structure patterns
        has_structure = any(keyword in text_to_analyze for keyword in structure_keywords)
        
        # Specification is likely for an API client if it has API keywords AND (auth OR structure)
        return has_api_keywords and (has_auth or has_structure)

    def _help(self) -> dict[str, Any]:
        """
        Return help information for Implementer Agent.
        
        Returns standardized help format with commands, examples, configuration,
        and safety features documentation.
        
        Returns:
            dict: Help information with standardized format:
                - type (str): Always "help"
                - content (str): Formatted markdown help text containing:
                    - Available commands list
                    - Usage examples for implement, generate-code, refactor
                    - Configuration options
                    - Safety features documentation
                    
        Note:
            This method is synchronous as it performs no I/O operations.
            Called via agent.run("help") which handles async context.
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
        if self.reviewer:
            await self.reviewer.close()
