"""
Code Generator - Generates code from specifications using LLM
"""

from typing import Dict, Any, Optional
from pathlib import Path

from ...core.mal import MAL


class CodeGenerator:
    """Generates code from specifications using LLM."""
    
    def __init__(self, mal: MAL):
        self.mal = mal
    
    async def generate_code(
        self,
        specification: str,
        file_path: Optional[Path] = None,
        context: Optional[str] = None,
        language: str = "python",
        expert_guidance: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generate code from specification.
        
        Args:
            specification: Description of what code to generate
            file_path: Optional target file path for context
            context: Optional context (existing code, patterns, etc.)
            language: Programming language (default: python)
            expert_guidance: Optional expert guidance dictionary
        
        Returns:
            Generated code string
        """
        prompt = self._build_generation_prompt(specification, file_path, context, language, expert_guidance)
        
        try:
            response = await self.mal.generate(prompt, model="qwen2.5-coder:7b")
            return self._extract_code(response, language)
        except Exception as e:
            raise RuntimeError(f"Code generation failed: {str(e)}")
    
    async def refactor_code(
        self,
        code: str,
        instruction: str,
        language: str = "python"
    ) -> str:
        """
        Refactor existing code based on instruction.
        
        Args:
            code: Existing code to refactor
            instruction: Refactoring instruction
            language: Programming language
        
        Returns:
            Refactored code string
        """
        prompt = self._build_refactor_prompt(code, instruction, language)
        
        try:
            response = await self.mal.generate(prompt, model="qwen2.5-coder:7b")
            return self._extract_code(response, language)
        except Exception as e:
            raise RuntimeError(f"Code refactoring failed: {str(e)}")
    
    def _build_generation_prompt(
        self,
        specification: str,
        file_path: Optional[Path],
        context: Optional[str],
        language: str,
        expert_guidance: Optional[Dict[str, str]] = None
    ) -> str:
        """Build prompt for code generation."""
        prompt_parts = [
            f"You are a senior {language} developer. Generate production-quality code.",
            "",
            "Requirements:",
            "- Follow best practices and conventions",
            "- Include error handling",
            "- Add inline comments for complex logic",
            "- Consider edge cases",
            "- Write clean, maintainable code",
            "",
        ]
        
        # Add expert guidance if available
        if expert_guidance:
            prompt_parts.append("Expert Guidance:")
            if "security" in expert_guidance:
                prompt_parts.append(f"\nSecurity Expert:\n{expert_guidance['security'][:500]}...")
            if "performance" in expert_guidance:
                prompt_parts.append(f"\nPerformance Expert:\n{expert_guidance['performance'][:300]}...")
            prompt_parts.append("")
        
        prompt_parts.append(f"Specification:\n{specification}")
        
        if file_path:
            prompt_parts.append(f"\nTarget file: {file_path}")
        
        if context:
            prompt_parts.append(f"\nContext:\n{context}")
        
        prompt_parts.append(
            f"\nGenerate only the {language} code. Do not include explanations or markdown."
        )
        
        return "\n".join(prompt_parts)
    
    def _build_refactor_prompt(
        self,
        code: str,
        instruction: str,
        language: str
    ) -> str:
        """Build prompt for code refactoring."""
        return f"""You are a senior {language} developer. Refactor the following code based on the instruction.

Original Code:
```{language}
{code}
```

Refactoring Instruction:
{instruction}

Requirements:
- Maintain functionality
- Improve code quality
- Follow best practices
- Preserve comments and documentation
- Keep the same API/interface if applicable

Generate only the refactored {language} code. Do not include explanations or markdown."""
    
    def _extract_code(self, response: str, language: str) -> str:
        """Extract code from LLM response."""
        # Try to extract code from code blocks
        import re
        
        # Look for code blocks
        code_block_pattern = rf"```(?:{language}|python)?\n?(.*?)```"
        matches = re.findall(code_block_pattern, response, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # If no code blocks, return the response as-is (might be plain code)
        return response.strip()


