"""
Code Generator - Prepares code generation instructions for Cursor Skills
"""

from pathlib import Path

from ...core.instructions import CodeGenerationInstruction


class CodeGenerator:
    """Prepares code generation instructions for Cursor Skills execution."""

    def __init__(self):
        """Initialize code generator."""
        pass

    def prepare_code_generation(
        self,
        specification: str,
        file_path: Path | None = None,
        context: str | None = None,
        language: str = "python",
        expert_guidance: dict[str, str] | None = None,
    ) -> CodeGenerationInstruction:
        """
        Prepare code generation instruction for Cursor Skills.

        Args:
            specification: Description of what code to generate
            file_path: Optional target file path for context
            context: Optional context (existing code, patterns, etc.)
            language: Programming language (default: python)
            expert_guidance: Optional expert guidance dictionary

        Returns:
            CodeGenerationInstruction object for Cursor Skills execution
        """
        return CodeGenerationInstruction(
            specification=specification,
            file_path=file_path,
            context=context,
            language=language,
            expert_guidance=expert_guidance,
        )

    def prepare_refactoring(
        self, code: str, instruction: str, language: str = "python"
    ) -> CodeGenerationInstruction:
        """
        Prepare refactoring instruction for Cursor Skills.

        Args:
            code: Existing code to refactor
            instruction: Refactoring instruction
            language: Programming language

        Returns:
            CodeGenerationInstruction object for Cursor Skills execution
        """
        # Combine code and instruction into specification
        specification = f"Refactor the following code:\n\n```{language}\n{code}\n```\n\nRefactoring instruction: {instruction}"
        return CodeGenerationInstruction(
            specification=specification,
            file_path=None,
            context=code,
            language=language,
            expert_guidance=None,
        )
