"""
Scenario templates for E2E scenario tests.

Extends base project templates with scenario-specific initial state and
expected outputs for feature implementation, bug fix, and refactor scenarios.
"""

from pathlib import Path
from typing import Any, Literal

from .project_templates import TemplateType, create_template

ScenarioType = Literal["feature", "bug_fix", "refactor"]


def create_small_scenario_template(
    project_path: Path,
    scenario_type: ScenarioType,
    **kwargs: Any,
) -> Path:
    """
    Create a small scenario template for feature or bug fix scenarios.

    Args:
        project_path: Path where the project should be created
        scenario_type: Type of scenario (feature, bug_fix)
        **kwargs: Additional scenario-specific configuration

    Returns:
        Path to the created project directory
    """
    # Start with base small template
    project_path = create_template("small", project_path)

    if scenario_type == "feature":
        return _setup_feature_scenario(project_path, **kwargs)
    elif scenario_type == "bug_fix":
        return _setup_bug_fix_scenario(project_path, **kwargs)
    else:
        raise ValueError(f"Small template does not support scenario type: {scenario_type}")


def create_medium_scenario_template(
    project_path: Path,
    scenario_type: ScenarioType,
    **kwargs: Any,
) -> Path:
    """
    Create a medium scenario template for refactor scenarios.

    Args:
        project_path: Path where the project should be created
        scenario_type: Type of scenario (refactor)
        **kwargs: Additional scenario-specific configuration

    Returns:
        Path to the created project directory
    """
    # Start with base medium template
    project_path = create_template("medium", project_path)

    if scenario_type == "refactor":
        return _setup_refactor_scenario(project_path, **kwargs)
    else:
        raise ValueError(f"Medium template does not support scenario type: {scenario_type}")


def _setup_feature_scenario(project_path: Path, **kwargs: Any) -> Path:
    """Set up a feature implementation scenario."""
    # Create feature request file
    feature_request = project_path / "FEATURE_REQUEST.md"
    feature_request.write_text(
        """# Feature Request: Add Multiplication Function

## Description
Add a `multiply` function to the calculator module that multiplies two numbers.

## Requirements
- Function should be named `multiply`
- Should accept two float parameters
- Should return the product as a float
- Should be added to `src/calculator.py`
- Should include docstring
- Should have corresponding test in `tests/test_calculator.py`

## Acceptance Criteria
- [ ] Function exists in calculator module
- [ ] Function has proper docstring
- [ ] Tests exist and pass
- [ ] Code follows existing style
"""
    )

    # Note: multiply function already exists in base template, but we'll
    # treat this as if it needs to be added for the scenario

    return project_path


def _setup_bug_fix_scenario(project_path: Path, **kwargs: Any) -> Path:
    """Set up a bug fix scenario with a reproducible bug."""
    # Modify calculator.py to introduce a bug
    calculator_file = project_path / "src" / "calculator.py"
    buggy_code = calculator_file.read_text()
    # Introduce a bug: divide function doesn't handle negative numbers correctly
    buggy_code = buggy_code.replace(
        'def divide(a: float, b: float) -> float:\n    """Divide two numbers."""\n    if b == 0:\n        raise ValueError("Cannot divide by zero")\n    return a / b',
        'def divide(a: float, b: float) -> float:\n    """Divide two numbers."""\n    if b == 0:\n        raise ValueError("Cannot divide by zero")\n    # BUG: Returns wrong sign for negative results\n    return abs(a / b)'
    )
    calculator_file.write_text(buggy_code)

    # Create bug report
    bug_report = project_path / "BUG_REPORT.md"
    bug_report.write_text(
        """# Bug Report: Division Returns Wrong Sign for Negative Results

## Description
The `divide` function returns incorrect results when dividing numbers that result in negative values.

## Steps to Reproduce
1. Call `divide(-6, 3)`
2. Expected: `-2.0`
3. Actual: `2.0`

## Expected Behavior
Division should preserve the sign of the result.

## Actual Behavior
Division always returns positive values due to `abs()` call.

## Environment
- Python 3.9+
- Calculator module v1.0
"""
    )

    # Update test to catch the bug (test should fail initially)
    test_file = project_path / "tests" / "test_calculator.py"
    test_content = test_file.read_text()
    # Add test for negative division
    test_content += "\n\ndef test_divide_negative():\n    \"\"\"Test division with negative result.\"\"\"\n    assert divide(-6, 3) == -2.0\n"
    test_file.write_text(test_content)

    return project_path


def _setup_refactor_scenario(project_path: Path, **kwargs: Any) -> Path:
    """Set up a refactor scenario with legacy code."""
    # Create legacy code structure (flat structure, no organization)
    legacy_file = project_path / "src" / "mypackage" / "legacy.py"
    legacy_file.write_text(
        """\"\"\"Legacy code that needs refactoring.\"\"\"

# TODO: Refactor this into separate modules
# TODO: Add proper error handling
# TODO: Improve code organization

class LegacyProcessor:
    \"\"\"Legacy processor with mixed concerns.\"\"\"
    
    def __init__(self):
        self.data = []
        self.config = {}
        self.cache = {}
    
    def process_data(self, items):
        \"\"\"Process data items.\"\"\"
        results = []
        for item in items:
            # Data processing logic
            processed = self._process_item(item)
            results.append(processed)
        
        # Configuration logic mixed in
        self.config['last_processed'] = len(results)
        
        # Caching logic mixed in
        self.cache['results'] = results
        
        return results
    
    def _process_item(self, item):
        \"\"\"Process a single item.\"\"\"
        # Simple processing
        return {'id': len(self.data), 'data': item}
    
    def get_config(self):
        \"\"\"Get configuration.\"\"\"
        return self.config
    
    def get_cache(self):
        \"\"\"Get cache.\"\"\"
        return self.cache
"""
    )

    # Create refactor requirements
    refactor_req = project_path / "REFACTOR_REQUIREMENTS.md"
    refactor_req.write_text(
        """# Refactor Requirements: Separate Concerns in LegacyProcessor

## Current Issues
- Mixed concerns: data processing, configuration, and caching in one class
- No clear separation of responsibilities
- Difficult to test individual concerns

## Refactoring Goals
1. Separate data processing logic into `DataProcessor` class
2. Extract configuration management into `ConfigManager` class
3. Extract caching logic into `CacheManager` class
4. Maintain backward compatibility
5. Ensure all tests still pass

## Expected Structure
- `src/mypackage/processor.py` - Data processing logic
- `src/mypackage/config.py` - Configuration management
- `src/mypackage/cache.py` - Caching logic
- Update `legacy.py` to use new structure (or deprecate)

## Quality Requirements
- All existing tests must pass
- Code coverage maintained or improved
- No breaking changes to public API
"""
    )

    # Create test for legacy code
    legacy_test = project_path / "tests" / "test_legacy.py"
    legacy_test.write_text(
        """\"\"\"Tests for legacy processor.\"\"\"

import pytest
from src.mypackage.legacy import LegacyProcessor

def test_legacy_processor_init():
    processor = LegacyProcessor()
    assert len(processor.data) == 0
    assert processor.config == {}
    assert processor.cache == {}

def test_legacy_processor_process_data():
    processor = LegacyProcessor()
    items = [{"name": "test1"}, {"name": "test2"}]
    results = processor.process_data(items)
    assert len(results) == 2
    assert results[0]["id"] == 0
    assert results[1]["id"] == 1

def test_legacy_processor_config():
    processor = LegacyProcessor()
    items = [{"name": "test"}]
    processor.process_data(items)
    assert processor.get_config()["last_processed"] == 1

def test_legacy_processor_cache():
    processor = LegacyProcessor()
    items = [{"name": "test"}]
    processor.process_data(items)
    assert "results" in processor.get_cache()
"""
    )

    return project_path


def get_expected_outputs(scenario_type: ScenarioType, template_size: TemplateType) -> dict[str, Any]:
    """
    Get expected outputs for a scenario type.

    Args:
        scenario_type: Type of scenario (feature, bug_fix, refactor)
        template_size: Size of template (small, medium)

    Returns:
        Dictionary of expected outputs (file changes, artifacts, test outcomes, quality signals)
    """
    if scenario_type == "feature" and template_size == "small":
        return {
            "file_changes": {
                "new_files": [
                    "src/calculator.py",  # Should be modified/verified
                ],
                "modified_files": [],
                "deleted_files": [],
            },
            "artifacts": {
                "planning": ["feature-spec.md"],
                "design": ["design.md"],
                "code": ["feature-code/"],
                "review": ["review-report.md"],
                "test": ["feature-tests/"],
            },
            "test_outcomes": {
                "all_tests_pass": True,
                "new_tests_created": True,
            },
            "quality_signals": {
                "gates_pass": True,
                "overall_score_min": 65,
            },
        }
    elif scenario_type == "bug_fix" and template_size == "small":
        return {
            "file_changes": {
                "new_files": [],
                "modified_files": ["src/calculator.py"],
                "deleted_files": [],
            },
            "artifacts": {
                "planning": ["debug-report.md"],
                "code": ["fixed-code/"],
                "review": ["review-report.md"],
                "test": ["bug-tests/"],
            },
            "test_outcomes": {
                "all_tests_pass": True,
                "bug_reproduction_test": True,
                "fix_verification_test": True,
            },
            "quality_signals": {
                "gates_pass": True,
                "quality_maintained": True,
            },
        }
    elif scenario_type == "refactor" and template_size == "medium":
        return {
            "file_changes": {
                "new_files": [
                    "src/mypackage/processor.py",
                    "src/mypackage/config.py",
                    "src/mypackage/cache.py",
                ],
                "modified_files": ["src/mypackage/legacy.py"],
                "deleted_files": [],
            },
            "artifacts": {
                "planning": ["refactor-plan.md"],
                "code": ["refactored-code/"],
                "review": ["review-report.md"],
                "docs": ["refactor-docs.md"],
            },
            "test_outcomes": {
                "all_tests_pass": True,
                "regression_tests_pass": True,
            },
            "quality_signals": {
                "gates_pass": True,
                "quality_maintained_or_improved": True,
            },
        }
    else:
        raise ValueError(f"Unknown scenario type/size combination: {scenario_type}/{template_size}")
