"""
Tests for error message library detection in library_detector.py

Tests the detect_from_error method (Enhancement 5).
"""

import pytest
from pathlib import Path

from tapps_agents.context7.library_detector import LibraryDetector


class TestDetectFromError:
    """Test detect_from_error method."""
    
    def test_detect_fastapi_from_error(self):
        """Test detecting FastAPI from error messages."""
        detector = LibraryDetector()
        
        error = "FastAPI HTTPException: Route not found"
        libraries = detector.detect_from_error(error)
        
        assert "fastapi" in libraries
    
    def test_detect_pytest_from_error(self):
        """Test detecting pytest from error messages."""
        detector = LibraryDetector()
        
        error = "pytest.raises(ValueError) failed"
        libraries = detector.detect_from_error(error)
        
        assert "pytest" in libraries
    
    def test_detect_sqlalchemy_from_error(self):
        """Test detecting SQLAlchemy from error messages."""
        detector = LibraryDetector()
        
        error = "sqlalchemy.exc.IntegrityError: duplicate key"
        libraries = detector.detect_from_error(error)
        
        assert "sqlalchemy" in libraries
    
    def test_detect_django_from_error(self):
        """Test detecting Django from error messages."""
        detector = LibraryDetector()
        
        error = "django.core.exceptions.ValidationError"
        libraries = detector.detect_from_error(error)
        
        assert "django" in libraries
    
    def test_detect_pydantic_from_error(self):
        """Test detecting Pydantic from error messages."""
        detector = LibraryDetector()
        
        error = "pydantic.ValidationError: field required"
        libraries = detector.detect_from_error(error)
        
        assert "pydantic" in libraries
    
    def test_detect_multiple_libraries_from_error(self):
        """Test detecting multiple libraries from a single error."""
        detector = LibraryDetector()
        
        error = "FastAPI route failed: pydantic.ValidationError occurred"
        libraries = detector.detect_from_error(error)
        
        assert "fastapi" in libraries
        assert "pydantic" in libraries
    
    def test_detect_from_stack_trace(self):
        """Test detecting libraries from stack traces."""
        detector = LibraryDetector()
        
        stack_trace = """
        Traceback (most recent call last):
          File "app.py", line 10, in <module>
            from fastapi import FastAPI
          File "/venv/lib/fastapi/__init__.py", line 1
            import pytest
        """
        libraries = detector.detect_from_error(stack_trace)
        
        assert "fastapi" in libraries
        assert "pytest" in libraries
    
    def test_detect_from_import_in_traceback(self):
        """Test detecting libraries from import statements in tracebacks."""
        detector = LibraryDetector()
        
        error = "from sqlalchemy import create_engine\nImportError: No module named sqlalchemy"
        libraries = detector.detect_from_error(error)
        
        assert "sqlalchemy" in libraries
    
    def test_no_libraries_detected(self):
        """Test that standard library modules are not detected."""
        detector = LibraryDetector()
        
        error = "ValueError: invalid input"
        libraries = detector.detect_from_error(error)
        
        # Should not detect standard library modules
        assert "json" not in libraries
        assert "os" not in libraries
    
    def test_case_insensitive_detection(self):
        """Test that detection is case-insensitive."""
        detector = LibraryDetector()
        
        error = "FASTAPI HTTPException"
        libraries = detector.detect_from_error(error)
        
        assert "fastapi" in libraries
    
    def test_detect_all_includes_error_messages(self):
        """Test that detect_all includes error message detection."""
        detector = LibraryDetector()
        
        code = "import fastapi"
        error = "pytest.raises failed"
        
        libraries = detector.detect_all(code=code, error_message=error)
        
        assert "fastapi" in libraries
        assert "pytest" in libraries
    
    def test_detect_all_combines_all_sources(self):
        """Test that detect_all combines code, prompt, and error detection."""
        detector = LibraryDetector()
        
        code = "import fastapi"
        prompt = "Use pytest for testing"
        error = "sqlalchemy.exc.IntegrityError"
        
        libraries = detector.detect_all(code=code, prompt=prompt, error_message=error)
        
        assert "fastapi" in libraries
        assert "pytest" in libraries
        assert "sqlalchemy" in libraries
    
    def test_detect_all_deduplicates(self):
        """Test that detect_all deduplicates libraries from multiple sources."""
        detector = LibraryDetector()
        
        code = "import fastapi"
        prompt = "Use fastapi for API"
        error = "FastAPI HTTPException"
        
        libraries = detector.detect_all(code=code, prompt=prompt, error_message=error)
        
        # FastAPI should only appear once despite being in all sources
        assert libraries.count("fastapi") == 1

