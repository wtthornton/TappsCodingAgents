"""
Integration tests for Cursor integration verification
"""
from pathlib import Path

from tapps_agents.core.cursor_verification import (
    format_verification_results,
    verify_cursor_integration,
)


def test_verify_cursor_integration_in_this_project():
    """Test that Cursor integration verification works in this project"""
    project_root = Path(__file__).parent.parent.parent
    
    is_valid, results = verify_cursor_integration(project_root=project_root)
    
    # Should be valid (we have all components)
    assert is_valid, f"Integration should be valid. Errors: {results.get('errors', [])}"
    
    # Check that all components are present
    assert "components" in results
    assert "skills" in results["components"]
    assert "rules" in results["components"]
    assert "background_agents" in results["components"]
    
    # Skills should be valid
    skills_result = results["components"]["skills"]
    assert skills_result["valid"], f"Skills should be valid. Errors: {skills_result.get('errors', [])}"
    assert len(skills_result["skills_found"]) >= 13, "Should have at least 13 skills"
    
    # Rules should be valid
    rules_result = results["components"]["rules"]
    assert rules_result["valid"], f"Rules should be valid. Errors: {rules_result.get('errors', [])}"
    assert len(rules_result["rules_found"]) >= 5, "Should have at least 5 rules"
    
    # Background agents should be valid
    bg_agents_result = results["components"]["background_agents"]
    assert bg_agents_result["valid"], f"Background agents should be valid. Errors: {bg_agents_result.get('errors', [])}"
    assert bg_agents_result["agents_count"] > 0, "Should have at least one background agent configured"


def test_format_verification_results_text():
    """Test that verification results can be formatted as text"""
    results = {
        "valid": True,
        "errors": [],
        "warnings": ["Test warning"],
        "components": {
            "skills": {
                "valid": True,
                "skills_found": ["reviewer", "implementer"],
                "expected_skills": ["reviewer", "implementer"],
            },
            "rules": {
                "valid": True,
                "rules_found": ["workflow-presets.mdc"],
                "expected_rules": ["workflow-presets.mdc"],
            },
            "background_agents": {
                "valid": True,
                "agents_count": 1,
            },
        },
    }
    
    output = format_verification_results(results, format="text")
    
    assert "Cursor Integration Verification" in output
    assert "Status: VALID" in output
    assert "SKILLS" in output
    assert "RULES" in output
    assert "BACKGROUND AGENTS" in output


def test_format_verification_results_json():
    """Test that verification results can be formatted as JSON"""
    results = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "components": {
            "skills": {"valid": True},
        },
    }
    
    output = format_verification_results(results, format="json")
    
    # Should be valid JSON
    import json
    parsed = json.loads(output)
    assert parsed["valid"] is True
    assert "components" in parsed


def test_verify_cursor_integration_missing_components(tmp_path):
    """Test verification with missing components"""
    # Create a temporary directory without Cursor integration
    is_valid, results = verify_cursor_integration(project_root=tmp_path)
    
    # Should be invalid
    assert not is_valid, "Should be invalid when components are missing"
    
    # Should have errors
    assert len(results["errors"]) > 0, "Should have errors for missing components"
    
    # Skills should be invalid
    assert not results["components"]["skills"]["valid"]
    
    # Rules should be invalid
    assert not results["components"]["rules"]["valid"]
    
    # Background agents should be invalid
    assert not results["components"]["background_agents"]["valid"]

