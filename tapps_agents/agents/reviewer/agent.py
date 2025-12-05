"""
Reviewer Agent - Performs code review with scoring
"""

from pathlib import Path
from typing import Dict, Any, Optional
import json

from ...core.mal import MAL
from .scoring import CodeScorer


class ReviewerAgent:
    """
    Reviewer Agent - Code review with Code Scoring.
    
    Permissions: Read, Grep, Glob (read-only)
    """
    
    def __init__(self, mal: Optional[MAL] = None):
        self.mal = mal or MAL()
        self.scorer = CodeScorer()
    
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
        
        # Read code
        code = file_path.read_text(encoding='utf-8')
        
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

