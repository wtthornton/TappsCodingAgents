"""
Scorer Registry - Generic registration system for language-specific scorers

This module provides a registry pattern for registering and retrieving
language-specific scorers, making it easy to add support for new languages
without modifying core code.
"""

import logging
from typing import Any

from ...core.config import ProjectConfig
from ...core.language_detector import Language
from .scoring import BaseScorer

logger = logging.getLogger(__name__)


class ScorerRegistry:
    """
    Registry for language-specific scorers.
    
    Supports:
    - Registration of scorers for specific languages
    - Fallback chains (e.g., React → TypeScript → Generic)
    - Config-based scorer instantiation
    - Automatic registration of built-in scorers (lazy initialization)
    """
    
    # Registry mapping language to scorer class
    _scorers: dict[Language, type[BaseScorer]] = {}
    
    # Fallback chains (language -> list of fallback languages)
    _fallback_chains: dict[Language, list[Language]] = {
        Language.REACT: [Language.TYPESCRIPT, Language.JAVASCRIPT],
        Language.TYPESCRIPT: [Language.JAVASCRIPT],
    }
    
    # Track initialization state for lazy registration
    _initialized: bool = False
    
    @classmethod
    def register(
        cls,
        language: Language,
        scorer_class: type[BaseScorer],
        *,
        override: bool = False,
    ) -> None:
        """
        Register a scorer class for a language.
        
        Args:
            language: Language to register scorer for
            scorer_class: Scorer class (must implement BaseScorer)
            override: If True, override existing registration
        
        Raises:
            ValueError: If language already registered and override=False
        """
        if language in cls._scorers and not override:
            raise ValueError(
                f"Scorer for {language.value} already registered. "
                "Use override=True to replace it."
            )
        
        # Validate that scorer_class implements BaseScorer interface
        if not issubclass(scorer_class, BaseScorer):
            raise TypeError(
                f"Scorer class must inherit from BaseScorer, got {scorer_class.__name__}"
            )
        
        cls._scorers[language] = scorer_class
    
    @classmethod
    def unregister(cls, language: Language) -> None:
        """
        Unregister a scorer for a language.
        
        Args:
            language: Language to unregister
        """
        cls._scorers.pop(language, None)
    
    @classmethod
    def _ensure_initialized(cls) -> None:
        """
        Ensure built-in scorers are registered (lazy initialization).
        
        This method is called automatically before scorer lookup to ensure
        all built-in scorers (Python, TypeScript, etc.) are registered.
        
        Safe to call multiple times (idempotent).
        """
        if cls._initialized:
            return
        
        try:
            cls._register_builtin_scorers()
            # Only mark as initialized if at least Python scorer was registered
            if cls.is_registered(Language.PYTHON):
                cls._initialized = True
            else:
                # Force register Python scorer as fallback
                logger.warning(
                    "Python scorer registration failed, attempting fallback registration"
                )
                try:
                    from .scoring import CodeScorer
                    cls.register(Language.PYTHON, CodeScorer, override=True)
                    cls._initialized = True
                except Exception as fallback_error:
                    logger.error(
                        f"Failed to register Python scorer even with fallback: {fallback_error}",
                        exc_info=True,
                    )
                    # Don't set _initialized = True so it will retry next time
        except Exception as e:
            # Log error but try to register Python scorer as fallback
            logger.warning(
                f"Failed to auto-register built-in scorers: {e}. "
                "Attempting fallback Python scorer registration.",
                exc_info=True,
            )
            try:
                from .scoring import CodeScorer
                if not cls.is_registered(Language.PYTHON):
                    cls.register(Language.PYTHON, CodeScorer, override=True)
                    cls._initialized = True
            except Exception as fallback_error:
                logger.error(
                    f"Failed to register Python scorer as fallback: {fallback_error}",
                    exc_info=True,
                )
                # Don't set _initialized = True so it will retry next time
    
    @classmethod
    def _register_builtin_scorers(cls) -> None:
        """
        Register all built-in language scorers.
        
        This method registers:
        - CodeScorer for Language.PYTHON
        - TypeScriptScorer for Language.TYPESCRIPT (if available)
        - ReactScorer for Language.REACT (if available)
        
        Uses lazy imports to avoid circular dependencies.
        """
        # Register Python scorer
        from .scoring import CodeScorer
        
        if not cls.is_registered(Language.PYTHON):
            cls.register(Language.PYTHON, CodeScorer, override=False)
        
        # Register TypeScript scorer (if available)
        try:
            from .typescript_scorer import TypeScriptScorer
            
            if not cls.is_registered(Language.TYPESCRIPT):
                cls.register(Language.TYPESCRIPT, TypeScriptScorer, override=False)
        except ImportError:
            # TypeScript scorer not available - skip silently
            pass
        
        # Register React scorer (if available)
        try:
            from .react_scorer import ReactScorer
            
            if not cls.is_registered(Language.REACT):
                cls.register(Language.REACT, ReactScorer, override=False)
        except ImportError:
            # React scorer not available - skip silently
            pass
    
    @classmethod
    def get_scorer(cls, language: Language, config: ProjectConfig | None = None) -> BaseScorer:
        """
        Get appropriate scorer for a language, with fallback support.
        
        Args:
            language: Detected language
            config: Optional project configuration
            
        Returns:
            BaseScorer instance appropriate for the language
            
        Raises:
            ValueError: If no scorer found and no fallback available
        """
        # Ensure built-in scorers are registered (lazy initialization)
        cls._ensure_initialized()
        
        # Try to get scorer for this language
        scorer_class = cls._scorers.get(language)
        
        if scorer_class:
            return cls._instantiate_scorer(scorer_class, language, config)
        
        # Try fallback chain
        fallback_chain = cls._fallback_chains.get(language, [])
        for fallback_language in fallback_chain:
            fallback_scorer_class = cls._scorers.get(fallback_language)
            if fallback_scorer_class:
                return cls._instantiate_scorer(
                    fallback_scorer_class, fallback_language, config
                )
        
        # If still no scorer, try to ensure initialization one more time
        # (in case initialization failed previously)
        if not cls._initialized:
            cls._ensure_initialized()
            scorer_class = cls._scorers.get(language)
            if scorer_class:
                return cls._instantiate_scorer(scorer_class, language, config)
            
            # Try fallback chain again after re-initialization
            fallback_chain = cls._fallback_chains.get(language, [])
            for fallback_language in fallback_chain:
                fallback_scorer_class = cls._scorers.get(fallback_language)
                if fallback_scorer_class:
                    return cls._instantiate_scorer(
                        fallback_scorer_class, fallback_language, config
                    )
        
        # If still no scorer, raise error
        # In the future, we could return a GenericScorer here
        available_languages = [lang.value for lang in cls._scorers.keys()]
        raise ValueError(
            f"No scorer registered for language {language.value} "
            f"and no fallback available. Available languages: {available_languages}"
        )
    
    @classmethod
    def _instantiate_scorer(
        cls,
        scorer_class: type[BaseScorer],
        language: Language,
        config: ProjectConfig | None = None,
    ) -> BaseScorer:
        """
        Instantiate a scorer class with appropriate configuration.
        
        This method handles the complexity of extracting config values
        and passing them to the scorer constructor.
        """
        # Extract config values
        scoring_config = config.scoring if config else None
        quality_tools = config.quality_tools if config else None
        weights = scoring_config.weights if scoring_config else None
        
        # Try to instantiate with common constructor patterns
        # Different scorers may have different constructor signatures
        
        # Pattern 1: (eslint_config, tsconfig_path) - TypeScript/React scorers
        if language in [Language.TYPESCRIPT, Language.REACT, Language.JAVASCRIPT]:
            eslint_config = quality_tools.eslint_config if quality_tools else None
            tsconfig_path = quality_tools.tsconfig_path if quality_tools else None
            
            # ReactScorer has different constructor signature
            if language == Language.REACT:
                from .react_scorer import ReactScorer
                return ReactScorer(
                    eslint_config=eslint_config, tsconfig_path=tsconfig_path
                )
            else:
                from .typescript_scorer import TypeScriptScorer
                return TypeScriptScorer(
                    eslint_config=eslint_config, tsconfig_path=tsconfig_path
                )
        
        # Pattern 2: (weights, ruff_enabled, mypy_enabled, ...) - Python scorer
        elif language == Language.PYTHON:
            from .scoring import CodeScorer
            
            ruff_enabled = quality_tools.ruff_enabled if quality_tools else True
            mypy_enabled = quality_tools.mypy_enabled if quality_tools else True
            jscpd_enabled = quality_tools.jscpd_enabled if quality_tools else True
            duplication_threshold = (
                quality_tools.duplication_threshold if quality_tools else 3.0
            )
            min_duplication_lines = (
                quality_tools.min_duplication_lines if quality_tools else 5
            )
            
            return CodeScorer(
                weights=weights,
                ruff_enabled=ruff_enabled,
                mypy_enabled=mypy_enabled,
                jscpd_enabled=jscpd_enabled,
                duplication_threshold=duplication_threshold,
                min_duplication_lines=min_duplication_lines,
            )
        
        # Pattern 3: Generic instantiation (try no-args first, then with config)
        try:
            return scorer_class()
        except TypeError:
            # If no-args fails, try with config dict
            try:
                return scorer_class(config=config)
            except TypeError:
                # Last resort: try with language
                return scorer_class(language=language)
    
    @classmethod
    def list_registered_languages(cls) -> list[Language]:
        """
        Get list of languages with registered scorers.
        
        Returns:
            List of languages that have scorers registered
        """
        return list(cls._scorers.keys())
    
    @classmethod
    def is_registered(cls, language: Language) -> bool:
        """
        Check if a language has a scorer registered.
        
        Args:
            language: Language to check
            
        Returns:
            True if scorer is registered for this language
        """
        return language in cls._scorers
    
    @classmethod
    def register_fallback_chain(
        cls, language: Language, fallback_chain: list[Language]
    ) -> None:
        """
        Register a fallback chain for a language.
        
        Args:
            language: Primary language
            fallback_chain: List of languages to fall back to (in order)
        """
        cls._fallback_chains[language] = fallback_chain


def register_scorer(
    language: Language, *, override: bool = False
) -> Any:
    """
    Decorator to register a scorer class for a language.
    
    Usage:
        @register_scorer(Language.PYTHON)
        class PythonScorer(BaseScorer):
            ...
    
    Args:
        language: Language to register for
        override: If True, override existing registration
    
    Returns:
        Decorator function
    """
    def decorator(scorer_class: type[BaseScorer]) -> type[BaseScorer]:
        ScorerRegistry.register(language, scorer_class, override=override)
        return scorer_class
    
    return decorator


# Note: Built-in scorers are registered lazily via _ensure_initialized()
# which is called automatically when get_scorer() is first invoked.
# This avoids circular import issues while ensuring scorers are available.
#
# For explicit registration, use the @register_scorer decorator or
# ScorerRegistry.register() method directly.

