"""
Reviewer Agent - Performs code review with scoring
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import json

from ...core.mal import MAL
from ...core.agent_base import BaseAgent
from .scoring import CodeScorer


class ReviewerAgent(BaseAgent):
    """
    Reviewer Agent - Code review with Code Scoring.
    
    Permissions: Read, Grep, Glob (read-only)
    """
    
    def __init__(self, mal: Optional[MAL] = None):
        super().__init__(agent_id="reviewer", agent_name="Reviewer Agent")
        self.mal = mal or MAL()
        self.scorer = CodeScorer()
    
    def get_commands(self) -> List[Dict[str, str]]:
        """Return available commands for reviewer agent"""
        base_commands = super().get_commands()
        return base_commands + [
            {"command": "*review", "description": "Review code file with scoring and feedback"},
            {"command": "*score", "description": "Calculate code scores only (no LLM feedback)"},
        ]
    
    async def run(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        Execute reviewer agent command.
        
        Commands:
        - help: Show available commands
        - review: Review file with scoring and feedback
        - score: Calculate scores only
        """
        if command == "help":
            return {"type": "help", "content": self.format_help()}
        
        elif command == "review":
            file_path = kwargs.get("file")
            if not file_path:
                return {"error": "File path required. Usage: *review <file>"}
            
            model = kwargs.get("model", "qwen2.5-coder:7b")
            return await self.review_file(
                Path(file_path),
                model=model,
                include_scoring=True,
                include_llm_feedback=True
            )
        
        elif command == "score":
            file_path = kwargs.get("file")
            if not file_path:
                return {"error": "File path required. Usage: *score <file>"}
            
            return await self.review_file(
                Path(file_path),
                include_scoring=True,
                include_llm_feedback=False
            )
        
        else:
            return {"error": f"Unknown command: {command}. Use *help to see available commands."}
    
    async def review_file(
        self,
        file_path: Path,
        model: str = "qwen2.5-coder:7b",
        include_scoring: bool = True,
        include_llm_feedback: bool = True
    ) -> Dict[str, Any]:
        """
        Review a code file.
        
        Args:
            file_path: Path to code file
            model: LLM model to use for feedback
            include_scoring: Include code scores
            include_llm_feedback: Include LLM-generated feedback
            
        Returns:
            Review results with scores and feedback
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Input validation: Check file size (limit to 1MB)
        file_size = file_path.stat().st_size
        MAX_FILE_SIZE = 1024 * 1024  # 1MB
        if file_size > MAX_FILE_SIZE:
            raise ValueError(f"File too large: {file_size} bytes (max {MAX_FILE_SIZE} bytes)")
        
        # Input validation: Check path traversal (allow absolute paths for testing)
        # In production, we'd restrict to project directory
        # For now, just ensure it's an absolute path or within reasonable bounds
        resolved_path = file_path.resolve()
        
        # Check for obvious path traversal patterns
        path_str = str(resolved_path)
        if ".." in str(file_path) and not resolved_path.exists():
            raise ValueError(f"Path traversal detected: {file_path}")
        
        # Additional check: ensure path doesn't contain suspicious patterns
        suspicious_patterns = ["%2e%2e", "%2f", "%5c"]  # URL-encoded traversal attempts
        if any(pattern in path_str.lower() for pattern in suspicious_patterns):
            raise ValueError(f"Suspicious path detected: {file_path}")
        
        # Read code
        try:
            code = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError as e:
            raise ValueError(f"Cannot decode file as UTF-8: {e}")
        
        result = {
            "file": str(file_path),
            "review": {}
        }
        
        # Calculate scores
        if include_scoring:
            scores = self.scorer.score_file(file_path, code)
            result["scoring"] = scores
        
        # Generate LLM feedback
        if include_llm_feedback:
            feedback = await self._generate_feedback(code, scores if include_scoring else None, model)
            result["feedback"] = feedback
        
        # Determine pass/fail
        if include_scoring:
            result["passed"] = scores["overall_score"] >= 70.0
            result["threshold"] = 70.0
        
        return result
    
    async def _generate_feedback(
        self,
        code: str,
        scores: Optional[Dict[str, Any]],
        model: str
    ) -> Dict[str, Any]:
        """Generate LLM feedback on code"""
        
        # Build prompt
        prompt_parts = [
            "Review this code and provide feedback:",
            "",
            "Code:",
            "```python",
            code[:2000],  # Limit to first 2000 chars
            "```",
        ]
        
        if scores:
            prompt_parts.extend([
                "",
                "Code Scores:",
                f"- Complexity: {scores['complexity_score']:.1f}/10",
                f"- Security: {scores['security_score']:.1f}/10",
                f"- Maintainability: {scores['maintainability_score']:.1f}/10",
                f"- Overall: {scores['overall_score']:.1f}/100",
            ])
        
        prompt_parts.extend([
            "",
            "Provide:",
            "1. What the code does",
            "2. Potential issues or improvements",
            "3. Security concerns (if any)",
            "4. Style/best practices",
        ])
        
        prompt = "\n".join(prompt_parts)
        
        try:
            response = await self.mal.generate(prompt, model=model)
            return {
                "summary": response[:500],  # First 500 chars
                "full_feedback": response
            }
        except Exception as e:
            return {
                "error": str(e),
                "summary": "Could not generate LLM feedback"
            }
    
    async def close(self):
        """Clean up resources"""
        await self.mal.close()

