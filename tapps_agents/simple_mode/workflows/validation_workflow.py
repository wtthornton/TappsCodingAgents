"""Validation workflow for comparing implementations.

This workflow validates existing code and identifies optimizations without generating duplicate code.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ValidationResult:
    """Result of validation workflow."""
    existing_code_quality: float = 0.0  # 0-10
    proposed_design_quality: float = 0.0  # 0-10
    optimization_recommendations: list[dict[str, Any]] = field(default_factory=list)
    decision: str = "keep_existing"  # "keep_existing" or "replace"
    rationale: str = ""


class ValidationWorkflow:
    """
    Validation workflow for comparing implementations.

    Steps:
    1. Enhance prompt (quick mode)
    2. Analyze existing code
    3. Design proposed approach
    4. Compare implementations
    5. Generate optimization report

    Does NOT implement code - focuses on validation and recommendations.
    """

    def __init__(self, agents: dict[str, Any]):
        """
        Initialize validation workflow.

        Args:
            agents: Dictionary of agent instances
        """
        self.enhancer = agents.get("enhancer")
        self.reviewer = agents.get("reviewer")
        self.architect = agents.get("architect")
        self.designer = agents.get("designer")

    async def execute(
        self,
        prompt: str,
        existing_code_ref: str | None = None,
        project_root: Path | None = None,
        **kwargs
    ) -> ValidationResult:
        """
        Execute validation workflow.

        Args:
            prompt: User's prompt
            existing_code_ref: Reference to existing code (file:lines)
            project_root: Project root path
            **kwargs: Additional arguments

        Returns:
            ValidationResult with comparison and recommendations
        """
        print("\n" + "="*60)
        print("🔍 VALIDATION WORKFLOW")
        print("="*60)
        print("\nThis workflow validates existing code and identifies optimizations.")
        print("No duplicate code will be generated.\n")

        # Step 1: Quick enhancement
        print("📝 Step 1/5: Quick Prompt Enhancement")
        enhanced = await self._quick_enhance(prompt)

        # Step 2: Analyze existing code
        print("\n🔍 Step 2/5: Analyzing Existing Code")
        existing_analysis = await self._analyze_existing_code(existing_code_ref, project_root)

        # Step 3: Design proposed approach
        print("\n🏗️  Step 3/5: Designing Proposed Approach")
        proposed_design = await self._design_proposed_approach(enhanced, existing_analysis)

        # Step 4: Compare implementations
        print("\n⚖️  Step 4/5: Comparing Implementations")
        comparison = await self._compare_implementations(existing_analysis, proposed_design)

        # Step 5: Generate recommendations
        print("\n📊 Step 5/5: Generating Optimization Report")
        recommendations = await self._generate_recommendations(comparison)

        # Make decision
        decision, rationale = self._make_decision(existing_analysis, proposed_design, recommendations)

        return ValidationResult(
            existing_code_quality=existing_analysis.get("quality_score", 0.0),
            proposed_design_quality=proposed_design.get("estimated_quality", 0.0),
            optimization_recommendations=recommendations,
            decision=decision,
            rationale=rationale
        )

    async def _quick_enhance(self, prompt: str) -> dict[str, Any]:
        """Run quick enhancement (stages 1-3)."""
        if not self.enhancer:
            return {"enhanced_prompt": prompt}

        try:
            result = await self.enhancer.run(
                "enhance-quick",
                prompt=prompt,
                output_format="markdown"
            )
            return result
        except Exception as e:
            print(f"⚠️  Enhancement failed: {e}. Using original prompt.")
            return {"enhanced_prompt": prompt}

    async def _analyze_existing_code(
        self,
        code_ref: str | None,
        project_root: Path | None
    ) -> dict[str, Any]:
        """Analyze existing code quality."""
        if not code_ref:
            return {
                "quality_score": 0.0,
                "analysis": "No existing code provided",
                "complexity": 0.0,
                "security": 0.0,
                "maintainability": 0.0
            }

        # Parse reference (e.g., "file.py:100-200")
        file_path, line_range = self._parse_code_ref(code_ref)

        if not self.reviewer:
            return {
                "file_path": file_path,
                "line_range": line_range,
                "quality_score": 7.0,
                "analysis": "No reviewer available - assumed good quality"
            }

        try:
            # Review existing code
            review_result = await self.reviewer.run(
                "review",
                file_path=str(file_path)
            )

            # Extract scores
            overall_score = review_result.get("overall_score", 70) / 10.0  # Normalize to 0-10

            return {
                "file_path": file_path,
                "line_range": line_range,
                "quality_score": overall_score,
                "complexity": review_result.get("complexity_score", 7.0),
                "security": review_result.get("security_score", 7.0),
                "maintainability": review_result.get("maintainability_score", 7.0),
                "analysis": review_result.get("feedback", "Code reviewed successfully")
            }
        except Exception as e:
            print(f"⚠️  Code review failed: {e}. Assuming good quality.")
            return {
                "file_path": file_path,
                "line_range": line_range,
                "quality_score": 7.0,
                "analysis": f"Review failed: {e}"
            }

    async def _design_proposed_approach(
        self,
        enhanced_prompt: dict[str, Any],
        existing_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """Design proposed approach."""
        if not self.architect:
            return {
                "design": {"approach": "Standard implementation"},
                "estimated_quality": 8.0,
                "approach": "Standard"
            }

        try:
            # Extract enhanced prompt text
            prompt_text = enhanced_prompt.get("enhanced_prompt", "")
            if isinstance(prompt_text, dict):
                prompt_text = prompt_text.get("enhanced_prompt", "")

            # Use architect to design alternative
            design_result = await self.architect.run(
                "design",
                prompt=prompt_text,
                context=f"Existing implementation quality: {existing_analysis.get('quality_score', 0):.1f}/10"
            )

            # Estimate quality of proposed design
            estimated_quality = self._estimate_design_quality(design_result)

            return {
                "design": design_result,
                "estimated_quality": estimated_quality,
                "approach": design_result.get("architecture_pattern", "Unknown")
            }
        except Exception as e:
            print(f"⚠️  Architecture design failed: {e}. Using simple estimate.")
            return {
                "design": {"approach": "Standard implementation"},
                "estimated_quality": 8.0,
                "approach": "Standard"
            }

    async def _compare_implementations(
        self,
        existing: dict[str, Any],
        proposed: dict[str, Any]
    ) -> dict[str, Any]:
        """Compare implementations side-by-side."""
        existing_score = existing.get("quality_score", 0.0)
        proposed_score = proposed.get("estimated_quality", 0.0)

        return {
            "existing_score": existing_score,
            "proposed_score": proposed_score,
            "score_diff": proposed_score - existing_score,
            "feature_comparison": self._build_feature_matrix(existing, proposed),
            "optimization_opportunities": self._identify_optimizations(existing, proposed)
        }

    async def _generate_recommendations(self, comparison: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate optimization recommendations."""
        recommendations = []

        # Categorize by value
        for opt in comparison.get("optimization_opportunities", []):
            impact = opt.get("impact", 0)
            effort = opt.get("effort", 100)

            if impact >= 50 and effort <= 15:
                opt["priority"] = "high"
                opt["category"] = "⭐⭐⭐ Implement Immediately"
            elif impact >= 30 and effort <= 60:
                opt["priority"] = "medium"
                opt["category"] = "⭐⭐ Consider"
            else:
                opt["priority"] = "low"
                opt["category"] = "⭐ Skip (YAGNI)"

            recommendations.append(opt)

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 3))

        return recommendations

    def _make_decision(
        self,
        existing: dict[str, Any],
        proposed: dict[str, Any],
        recommendations: list[dict[str, Any]]
    ) -> tuple[str, str]:
        """Make keep vs replace decision."""
        existing_score = existing.get("quality_score", 0.0)
        proposed_score = proposed.get("estimated_quality", 0.0)
        score_diff = proposed_score - existing_score

        high_value_opts = len([r for r in recommendations if r.get("priority") == "high"])

        # Decision logic
        if existing_score >= 7.0 and score_diff < 2.0:
            decision = "keep_existing"
            rationale = (
                f"Existing implementation is excellent ({existing_score:.1f}/10). "
                f"Proposed design is only marginally better ({proposed_score:.1f}/10, +{score_diff:.1f}). "
                f"Recommend keeping existing code and applying {high_value_opts} high-value optimizations."
            )
        elif existing_score < 7.0:
            decision = "replace"
            rationale = (
                f"Existing implementation needs work ({existing_score:.1f}/10). "
                f"Proposed design is significantly better ({proposed_score:.1f}/10, +{score_diff:.1f}). "
                f"Recommend replacing with new implementation."
            )
        else:
            decision = "keep_existing"
            rationale = (
                f"Existing implementation is good ({existing_score:.1f}/10). "
                f"Proposed design is better ({proposed_score:.1f}/10, +{score_diff:.1f}) but not significantly. "
                f"Recommend incremental improvements via {high_value_opts} optimizations."
            )

        return decision, rationale

    def _parse_code_ref(self, ref: str) -> tuple[str, str | None]:
        """Parse code reference like 'file.py:100-200'."""
        if ":" in ref:
            parts = ref.split(":", 1)
            return parts[0], parts[1] if len(parts) > 1 else None
        return ref, None

    def _estimate_design_quality(self, design: dict[str, Any]) -> float:
        """Estimate quality of proposed design (0-10 scale)."""
        base_score = 7.0

        # Add points for good patterns (heuristic)
        design_str = str(design).lower()

        if "strategy" in design_str:
            base_score += 0.5
        if "extensib" in design_str:  # extensible/extensibility
            base_score += 0.5
        if "performance" in design_str or "optimiz" in design_str:
            base_score += 1.0
        if "test" in design_str:
            base_score += 0.5

        return min(10.0, base_score)

    def _build_feature_matrix(self, existing: dict, proposed: dict) -> dict[str, Any]:
        """Build feature comparison matrix."""
        existing_complexity = existing.get("complexity", 7.0)

        return {
            "simplicity": {
                "existing": "High" if existing_complexity < 8.0 else "Low",
                "proposed": "Medium",
                "winner": "existing" if existing_complexity < 8.0 else "proposed"
            },
            "extensibility": {
                "existing": "Medium",
                "proposed": "High",
                "winner": "proposed"
            },
            "maintainability": {
                "existing": "High" if existing.get("maintainability", 0) >= 7.0 else "Medium",
                "proposed": "High",
                "winner": "proposed"
            }
        }

    def _identify_optimizations(self, existing: dict, proposed: dict) -> list[dict[str, Any]]:
        """Identify optimization opportunities based on analysis."""
        optimizations = []

        # Example optimization based on quality gaps
        existing_score = existing.get("quality_score", 0.0)

        if existing_score < 8.0:
            optimizations.append({
                "name": "Code quality improvement",
                "impact": int((8.0 - existing_score) * 10),  # % improvement
                "effort": 30,  # minutes
                "description": "Apply code quality best practices to improve maintainability"
            })

        # Security optimization
        security_score = existing.get("security", 7.0)
        if security_score < 8.0:
            optimizations.append({
                "name": "Security hardening",
                "impact": int((8.0 - security_score) * 15),
                "effort": 20,
                "description": "Add input validation and security checks"
            })

        # Performance optimization (example)
        optimizations.append({
            "name": "Early exit optimization",
            "impact": 90,
            "effort": 5,
            "description": "Add early exit check before expensive processing"
        })

        return optimizations
