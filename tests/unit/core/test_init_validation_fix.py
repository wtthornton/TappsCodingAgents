"""
Tests for init --reset validation bug fix.

This test verifies that:
1. File sync occurs after writing rules
2. Validation correctly reports installed files
3. CLI output distinguishes Rules from Skills
"""
import tempfile
from pathlib import Path

import pytest

from tapps_agents.core.cursor_verification import verify_cursor_integration
from tapps_agents.core.init_project import init_cursor_rules


@pytest.mark.unit
class TestInitValidationFix:
    """Test suite for validation bug fix."""

    def test_file_sync_ensures_visibility(self, tmp_path):
        """
        Test that file sync ensures files are visible after write.

        This tests the fix for the bug where validation reported 0/14 rules
        when files were written but not yet visible due to buffering.
        """
        # Arrange: Set up project directory
        project_root = tmp_path

        # Act: Initialize cursor rules (which includes file sync)
        success, copied_rules = init_cursor_rules(project_root=project_root)

        # Assert: Files should be written and synced
        assert success, "init_cursor_rules should succeed"
        assert len(copied_rules) > 0, "Should have copied rule files"

        # Verify files are immediately visible (no buffering delay)
        rules_dir = project_root / ".cursor" / "rules"
        assert rules_dir.exists(), "Rules directory should exist"

        # Count files on disk
        mdc_files = list(rules_dir.glob("*.mdc"))
        assert len(mdc_files) > 0, "Should have .mdc files"

        # Validate immediately (this is where the bug occurred - files not visible)
        is_valid, results = verify_cursor_integration(project_root)

        # Extract validation results
        rules_info = results.get("components", {}).get("rules", {})
        rules_found = rules_info.get("rules_found", [])

        # Assert: Validation should find the files (this was broken before fix)
        assert len(rules_found) > 0, f"Validation should find rules, but found {len(rules_found)}"
        assert len(rules_found) == len(mdc_files), \
            f"Validation found {len(rules_found)} but disk has {len(mdc_files)}"

    def test_validation_distinguishes_rules_from_skills(self, tmp_path):
        """
        Test that validation clearly separates Rules from Skills.

        This verifies the improved validation output.
        """
        # Arrange: Set up with rules only (no skills)
        project_root = tmp_path
        init_cursor_rules(project_root=project_root)

        # Act: Run validation
        is_valid, results = verify_cursor_integration(project_root)

        # Assert: Should have separate components for rules and skills
        components = results.get("components", {})
        assert "rules" in components, "Should have rules component"
        assert "skills" in components, "Should have skills component"

        # Rules should be found (14 files)
        rules_info = components["rules"]
        assert len(rules_info.get("rules_found", [])) > 0, "Should find rules"

        # Skills should NOT be found (not installed)
        skills_info = components["skills"]
        assert len(skills_info.get("skills_found", [])) == 0, \
            "Should not find skills (not installed)"

    def test_validation_output_format(self, tmp_path):
        """
        Test that validation output has expected structure.

        This verifies the fix provides clear distinction between
        Framework Files (Rules) and Cursor Skills.
        """
        # Arrange
        project_root = tmp_path
        init_cursor_rules(project_root=project_root)

        # Act
        is_valid, results = verify_cursor_integration(project_root)

        # Assert: Validation structure
        assert "components" in results, "Should have components"
        assert "errors" in results, "Should have errors list"
        assert "warnings" in results, "Should have warnings list"

        # Verify component structure
        components = results["components"]
        for component_name in ["rules", "skills"]:
            assert component_name in components, f"Should have {component_name} component"
            component = components[component_name]
            assert "valid" in component, f"{component_name} should have 'valid' field"
            assert "rules_found" in component or "skills_found" in component, \
                f"{component_name} should have found list"
            assert "expected_rules" in component or "expected_skills" in component, \
                f"{component_name} should have expected list"

    def test_file_sync_does_not_fail_on_error(self, tmp_path, monkeypatch):
        """
        Test that file sync errors don't fail init.

        File sync is best-effort and should not break init if it fails.
        """
        # Arrange: Make os.sync raise an exception
        import os as os_module

        original_sync = getattr(os_module, 'sync', None)

        def mock_sync():
            raise OSError("Mock sync failure")

        if original_sync:
            monkeypatch.setattr(os_module, 'sync', mock_sync)

        # Act: Init should still succeed even if sync fails
        project_root = tmp_path
        success, copied_rules = init_cursor_rules(project_root=project_root)

        # Assert: Init should succeed despite sync failure
        assert success, "init_cursor_rules should succeed even if sync fails"
        assert len(copied_rules) > 0, "Should still copy files"

    def test_validation_with_both_rules_and_skills(self, tmp_path):
        """
        Test validation when both rules and skills are installed.
        """
        # Arrange: Create both rules and skills directories
        project_root = tmp_path

        # Install rules
        init_cursor_rules(project_root=project_root)

        # Create skills directory structure (simulate skills installation)
        skills_dir = project_root / ".claude" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

        # Create a sample skill
        (skills_dir / "reviewer").mkdir(parents=True, exist_ok=True)
        (skills_dir / "reviewer" / "SKILL.md").write_text(
            "---\nname: reviewer\n---\n# Reviewer Skill"
        )

        # Act: Run validation
        is_valid, results = verify_cursor_integration(project_root)

        # Assert: Both components should be found
        components = results["components"]

        rules_found = len(components["rules"].get("rules_found", []))
        skills_found = len(components["skills"].get("skills_found", []))

        assert rules_found > 0, "Should find rules"
        assert skills_found > 0, "Should find skills"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
