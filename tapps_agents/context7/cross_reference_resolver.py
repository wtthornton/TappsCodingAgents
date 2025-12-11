"""
Cross-Reference Resolver for Skills

Automatically resolves cross-references in Context7 KB lookups for Skills.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path

from .cross_references import CrossReferenceManager, CrossReference
from .cache_structure import CacheStructure
from .kb_cache import KBCache
from .metadata import MetadataManager


class CrossReferenceResolver:
    """Resolves cross-references in Context7 KB lookups."""
    
    def __init__(
        self,
        cache_structure: CacheStructure,
        kb_cache: KBCache,
        cross_ref_manager: Optional[CrossReferenceManager] = None
    ):
        """
        Initialize cross-reference resolver.
        
        Args:
            cache_structure: CacheStructure instance
            kb_cache: KBCache instance
            cross_ref_manager: Optional CrossReferenceManager instance
        """
        self.cache_structure = cache_structure
        self.kb_cache = kb_cache
        
        if cross_ref_manager is None:
            from .cross_references import CrossReferenceManager
            cross_ref_manager = CrossReferenceManager(cache_structure)
        
        self.cross_ref_manager = cross_ref_manager
    
    def resolve_cross_references(
        self,
        library: str,
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resolve cross-references for a library/topic.
        
        Args:
            library: Library name
            topic: Optional topic name
        
        Returns:
            Dictionary with resolved cross-references
        """
        result = {
            "library": library,
            "topic": topic,
            "cross_references": [],
            "related_libraries": [],
            "related_topics": []
        }
        
        # Get cross-references for this library/topic
        if topic:
            refs = self.cross_ref_manager.get_cross_references(library, topic)
        else:
            # Get all cross-references for library (get by topic "overview" or similar)
            refs = self.cross_ref_manager.get_cross_references(library, "overview")
        
        # Process cross-references
        for ref in refs:
            ref_data = {
                "target_library": ref.target_library,
                "target_topic": ref.target_topic,
                "relationship_type": ref.relationship_type,
                "confidence": ref.confidence
            }
            result["cross_references"].append(ref_data)
            
            # Add to related lists
            if ref.target_library not in result["related_libraries"]:
                result["related_libraries"].append(ref.target_library)
            
            if ref.target_topic:
                topic_key = f"{ref.target_library}/{ref.target_topic}"
                if topic_key not in result["related_topics"]:
                    result["related_topics"].append(topic_key)
        
        # Check if referenced entries exist in cache
        available_refs = []
        for ref in refs:
            entry = self.kb_cache.get(ref.target_library, ref.target_topic)
            if entry:
                available_refs.append({
                    "library": ref.target_library,
                    "topic": ref.target_topic,
                    "relationship": ref.relationship_type,
                    "available": True
                })
            else:
                available_refs.append({
                    "library": ref.target_library,
                    "topic": ref.target_topic,
                    "relationship": ref.relationship_type,
                    "available": False
                })
        
        result["available_references"] = available_refs
        
        return result
    
    def get_related_documentation(
        self,
        library: str,
        topic: Optional[str] = None,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get related documentation based on cross-references.
        
        Args:
            library: Library name
            topic: Optional topic name
            max_results: Maximum number of results
        
        Returns:
            List of related documentation entries
        """
        cross_refs = self.resolve_cross_references(library, topic)
        
        related_docs = []
        for ref_info in cross_refs.get("available_references", []):
            if ref_info.get("available"):
                entry = self.kb_cache.get(
                    ref_info["library"],
                    ref_info["topic"]
                )
                if entry:
                    related_docs.append({
                        "library": ref_info["library"],
                        "topic": ref_info["topic"],
                        "relationship": ref_info["relationship"],
                        "content_preview": entry.content[:200] + "..." if len(entry.content) > 200 else entry.content
                    })
                    
                    if len(related_docs) >= max_results:
                        break
        
        return related_docs


def create_cross_reference_resolver(
    cache_structure: CacheStructure,
    kb_cache: KBCache
) -> CrossReferenceResolver:
    """
    Convenience function to create a cross-reference resolver.
    
    Args:
        cache_structure: CacheStructure instance
        kb_cache: KBCache instance
    
    Returns:
        CrossReferenceResolver instance
    """
    return CrossReferenceResolver(cache_structure, kb_cache)

