"""
Review Output Enhancer - Enhances review output with library and pattern guidance.

Maintains backward compatibility by adding new sections without
modifying existing review output structure.
"""

from typing import Any

from .context7_enhancer import LibraryRecommendation, PatternGuidance


class ReviewOutputEnhancer:
    """
    Enhances review output with library recommendations and pattern guidance.
    
    Maintains backward compatibility by adding new sections without
    modifying existing review output structure.
    """
    
    def enhance_output(
        self,
        base_result: dict[str, Any],
        library_recommendations: dict[str, LibraryRecommendation],
        pattern_guidance: dict[str, PatternGuidance]
    ) -> dict[str, Any]:
        """
        Enhance review output with library and pattern guidance.
        
        Args:
            base_result: Base review result dictionary
            library_recommendations: Library recommendations from Context7
            pattern_guidance: Pattern guidance from Context7
            
        Returns:
            Enhanced review result dictionary
        """
        # Create a copy to avoid modifying the original
        enhanced_result = base_result.copy()
        
        # Add library recommendations if available
        if library_recommendations:
            enhanced_result["library_recommendations"] = self._format_library_recommendations(
                library_recommendations
            )
        
        # Add pattern guidance if available
        if pattern_guidance:
            enhanced_result["pattern_guidance"] = self._format_pattern_guidance(
                pattern_guidance
            )
        
        return enhanced_result
    
    def _format_library_recommendations(
        self,
        recommendations: dict[str, LibraryRecommendation]
    ) -> dict[str, Any]:
        """
        Format library recommendations for output.
        
        Args:
            recommendations: Dictionary of LibraryRecommendation objects
            
        Returns:
            Formatted dictionary for output
        """
        formatted = {}
        
        for lib_name, recommendation in recommendations.items():
            formatted[lib_name] = {
                "best_practices": recommendation.best_practices,
                "common_mistakes": recommendation.common_mistakes,
                "usage_examples": recommendation.usage_examples,
                "source": recommendation.source,
                "cached": recommendation.cached
            }
        
        return formatted
    
    def _format_pattern_guidance(
        self,
        guidance: dict[str, PatternGuidance]
    ) -> dict[str, Any]:
        """
        Format pattern guidance for output.
        
        Args:
            guidance: Dictionary of PatternGuidance objects
            
        Returns:
            Formatted dictionary for output
        """
        formatted = {}
        
        for pattern_name, pattern_guidance in guidance.items():
            formatted[pattern_name] = {
                "detected": True,
                "recommendations": pattern_guidance.recommendations,
                "best_practices": pattern_guidance.best_practices,
                "source": pattern_guidance.source,
                "cached": pattern_guidance.cached
            }
        
        return formatted
