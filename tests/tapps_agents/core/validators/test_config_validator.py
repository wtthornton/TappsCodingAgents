"""Tests for ConfigValidator module.

Module: Phase 1.1 - Configuration Validator Tests
Target Coverage: ≥90%
"""

import pytest
import tempfile
from pathlib import Path
import yaml

from tapps_agents.core.validators.config_validator import (
    ConfigValidator,
    ValidationResult,
    ValidationError,
    ValidationWarning,
)

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


@pytest.fixture
def temp_project():
    """Create temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        tapps_dir = project_root / ".tapps-agents"
        tapps_dir.mkdir(parents=True, exist_ok=True)
        yield project_root


@pytest.fixture
def validator(temp_project):
    """Create ConfigValidator instance."""
    return ConfigValidator(project_root=temp_project)


class TestValidationDataClasses:
    """Test validation data classes."""

    def test_validation_error_str(self):
        """Test ValidationError string formatting."""
        error = ValidationError(file="test.yaml", message="Test error", line=10, column=5)
        assert str(error) == "ERROR [test.yaml:10:5] Test error"

    def test_validation_error_str_no_line(self):
        """Test ValidationError string formatting without line number."""
        error = ValidationError(file="test.yaml", message="Test error")
        assert str(error) == "ERROR [test.yaml] Test error"

    def test_validation_warning_str(self):
        """Test ValidationWarning string formatting."""
        warning = ValidationWarning(file="test.yaml", message="Test warning", line=5)
        assert str(warning) == "WARNING [test.yaml:5] Test warning"

    def test_validation_result_add_error(self):
        """Test adding error to ValidationResult."""
        result = ValidationResult(valid=True)
        result.add_error(file="test.yaml", message="Error")
        assert not result.valid
        assert len(result.errors) == 1
        assert result.errors[0].message == "Error"

    def test_validation_result_add_warning(self):
        """Test adding warning to ValidationResult."""
        result = ValidationResult(valid=True)
        result.add_warning(file="test.yaml", message="Warning")
        assert result.valid  # Warnings don't invalidate
        assert len(result.warnings) == 1

    def test_validation_result_str_success(self):
        """Test ValidationResult string formatting for success."""
        result = ValidationResult(valid=True)
        assert "✅ Validation passed" in str(result)

    def test_validation_result_str_with_errors(self):
        """Test ValidationResult string formatting with errors."""
        result = ValidationResult(valid=False)
        result.add_error(file="test.yaml", message="Test error")
        output = str(result)
        assert "Errors (1)" in output
        assert "Test error" in output


class TestExpertsYamlValidation:
    """Test experts.yaml validation."""

    def test_missing_experts_yaml(self, validator):
        """Test validation when experts.yaml is missing."""
        result = validator.validate_experts_yaml()
        assert result.valid
        assert len(result.warnings) == 1
        assert "does not exist" in result.warnings[0].message

    def test_invalid_yaml_syntax(self, validator, temp_project):
        """Test validation with invalid YAML syntax."""
        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_file.write_text("invalid: yaml: syntax:")

        result = validator.validate_experts_yaml()
        assert not result.valid
        assert len(result.errors) >= 1
        assert "YAML parsing error" in result.errors[0].message

    def test_missing_experts_key(self, validator, temp_project):
        """Test validation when 'experts' key is missing."""
        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_file.write_text(yaml.dump({"other_key": "value"}))

        result = validator.validate_experts_yaml()
        assert not result.valid
        assert any("Missing 'experts' key" in e.message for e in result.errors)

    def test_experts_not_list(self, validator, temp_project):
        """Test validation when 'experts' is not a list."""
        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_file.write_text(yaml.dump({"experts": "not_a_list"}))

        result = validator.validate_experts_yaml()
        assert not result.valid
        assert any("'experts' must be a list" in e.message for e in result.errors)

    def test_missing_required_fields(self, validator, temp_project):
        """Test validation when required fields are missing."""
        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_data = {
            "experts": [
                {
                    "name": "test-expert",
                    # Missing: description, priority, domain, consultation_triggers, knowledge_files
                }
            ]
        }
        experts_file.write_text(yaml.dump(experts_data))

        result = validator.validate_experts_yaml()
        assert not result.valid
        assert len(result.errors) >= 5  # One for each missing field

    def test_invalid_priority_type(self, validator, temp_project):
        """Test validation with invalid priority type."""
        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_data = {
            "experts": [
                {
                    "name": "test-expert",
                    "description": "Test",
                    "priority": "invalid",  # Should be number
                    "domain": "test",
                    "consultation_triggers": [],
                    "knowledge_files": [],
                }
            ]
        }
        experts_file.write_text(yaml.dump(experts_data))

        result = validator.validate_experts_yaml()
        assert not result.valid
        assert any("priority must be a number" in e.message for e in result.errors)

    def test_priority_out_of_range(self, validator, temp_project):
        """Test validation with priority out of valid range."""
        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_data = {
            "experts": [
                {
                    "name": "test-expert",
                    "description": "Test",
                    "priority": 1.5,  # Should be 0.0-1.0
                    "domain": "test",
                    "consultation_triggers": [],
                    "knowledge_files": [],
                }
            ]
        }
        experts_file.write_text(yaml.dump(experts_data))

        result = validator.validate_experts_yaml()
        assert not result.valid
        assert any("priority must be between" in e.message for e in result.errors)

    def test_missing_knowledge_files(self, validator, temp_project):
        """Test validation with missing knowledge files."""
        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_data = {
            "experts": [
                {
                    "name": "test-expert",
                    "description": "Test",
                    "priority": 0.8,
                    "domain": "test",
                    "consultation_triggers": ["test"],
                    "knowledge_files": ["nonexistent/file.md"],
                }
            ]
        }
        experts_file.write_text(yaml.dump(experts_data))

        result = validator.validate_experts_yaml()
        assert not result.valid
        assert any("knowledge file not found" in e.message for e in result.errors)

    def test_valid_experts_yaml(self, validator, temp_project):
        """Test validation with valid experts.yaml."""
        # Create knowledge file
        kb_dir = temp_project / ".tapps-agents" / "kb"
        kb_dir.mkdir(parents=True, exist_ok=True)
        kb_file = kb_dir / "test.md"
        kb_file.write_text("# Test Knowledge")

        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_data = {
            "experts": [
                {
                    "name": "test-expert",
                    "description": "Test expert",
                    "priority": 0.8,
                    "domain": "test",
                    "consultation_triggers": ["test"],
                    "knowledge_files": ["kb/test.md"],
                }
            ]
        }
        experts_file.write_text(yaml.dump(experts_data))

        result = validator.validate_experts_yaml()
        assert result.valid
        assert len(result.errors) == 0


class TestDomainsValidation:
    """Test domains.md validation."""

    def test_missing_domains_md(self, validator):
        """Test validation when domains.md is missing."""
        result = validator.validate_domains_md()
        assert result.valid
        assert len(result.warnings) == 1
        assert "does not exist" in result.warnings[0].message

    def test_empty_domains_md(self, validator, temp_project):
        """Test validation with empty domains.md."""
        domains_file = temp_project / ".tapps-agents" / "domains.md"
        domains_file.write_text("")

        result = validator.validate_domains_md()
        assert result.valid
        assert len(result.warnings) == 1
        assert "File is empty" in result.warnings[0].message

    def test_valid_domains_md(self, validator, temp_project):
        """Test validation with valid domains.md."""
        domains_file = temp_project / ".tapps-agents" / "domains.md"
        domains_file.write_text("# Domains\n\n## Test Domain\n")

        result = validator.validate_domains_md()
        assert result.valid


class TestTechStackValidation:
    """Test tech-stack.yaml validation."""

    def test_missing_tech_stack_yaml(self, validator):
        """Test validation when tech-stack.yaml is missing."""
        result = validator.validate_tech_stack_yaml()
        assert result.valid
        assert len(result.warnings) == 1
        assert "does not exist" in result.warnings[0].message
        assert len(result.suggestions) == 1
        assert "tapps-agents init" in result.suggestions[0]

    def test_invalid_yaml_syntax(self, validator, temp_project):
        """Test validation with invalid YAML syntax."""
        tech_stack_file = temp_project / ".tapps-agents" / "tech-stack.yaml"
        tech_stack_file.write_text("invalid: yaml: syntax:")

        result = validator.validate_tech_stack_yaml()
        assert not result.valid
        assert len(result.errors) >= 1
        assert "YAML parsing error" in result.errors[0].message

    def test_missing_recommended_keys(self, validator, temp_project):
        """Test validation with missing recommended keys."""
        tech_stack_file = temp_project / ".tapps-agents" / "tech-stack.yaml"
        tech_stack_file.write_text(yaml.dump({"other_key": "value"}))

        result = validator.validate_tech_stack_yaml()
        assert result.valid
        # Should have warnings for missing recommended keys
        assert len(result.warnings) >= 1

    def test_valid_tech_stack_yaml(self, validator, temp_project):
        """Test validation with valid tech-stack.yaml."""
        tech_stack_file = temp_project / ".tapps-agents" / "tech-stack.yaml"
        tech_stack_data = {
            "languages": ["python"],
            "libraries": ["pyyaml"],
            "frameworks": ["pytest"],
            "context7_priority": ["pyyaml"],
        }
        tech_stack_file.write_text(yaml.dump(tech_stack_data))

        result = validator.validate_tech_stack_yaml()
        assert result.valid
        assert len(result.warnings) == 0


class TestConfigYamlValidation:
    """Test config.yaml validation."""

    def test_missing_config_yaml(self, validator):
        """Test validation when config.yaml is missing."""
        result = validator.validate_config_yaml()
        assert not result.valid
        assert len(result.errors) == 1
        assert "does not exist" in result.errors[0].message
        assert "required" in result.errors[0].message

    def test_invalid_yaml_syntax(self, validator, temp_project):
        """Test validation with invalid YAML syntax."""
        config_file = temp_project / ".tapps-agents" / "config.yaml"
        config_file.write_text("invalid: yaml: syntax:")

        result = validator.validate_config_yaml()
        assert not result.valid
        assert len(result.errors) >= 1
        assert "YAML parsing error" in result.errors[0].message

    def test_valid_config_yaml(self, validator, temp_project):
        """Test validation with valid config.yaml."""
        config_file = temp_project / ".tapps-agents" / "config.yaml"
        config_data = {
            "version": "3.5.39",
            "simple_mode": {"enabled": True},
        }
        config_file.write_text(yaml.dump(config_data))

        result = validator.validate_config_yaml()
        assert result.valid


class TestKnowledgeFilesValidation:
    """Test knowledge files validation."""

    def test_missing_experts_yaml(self, validator):
        """Test validation when experts.yaml doesn't exist."""
        result = validator.validate_knowledge_files()
        assert result.valid  # Should pass if experts.yaml is missing

    def test_missing_knowledge_files(self, validator, temp_project):
        """Test validation with missing knowledge files."""
        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_data = {
            "experts": [
                {
                    "name": "test-expert",
                    "knowledge_files": ["nonexistent.md"],
                }
            ]
        }
        experts_file.write_text(yaml.dump(experts_data))

        result = validator.validate_knowledge_files()
        assert not result.valid
        assert any("Knowledge file not found" in e.message for e in result.errors)

    def test_valid_knowledge_files(self, validator, temp_project):
        """Test validation with valid knowledge files."""
        # Create knowledge file
        kb_dir = temp_project / ".tapps-agents" / "kb"
        kb_dir.mkdir(parents=True, exist_ok=True)
        kb_file = kb_dir / "test.md"
        kb_file.write_text("# Test")

        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_data = {
            "experts": [
                {
                    "name": "test-expert",
                    "knowledge_files": ["kb/test.md"],
                }
            ]
        }
        experts_file.write_text(yaml.dump(experts_data))

        result = validator.validate_knowledge_files()
        assert result.valid


class TestValidateAll:
    """Test validate_all method."""

    def test_validate_all_minimal(self, validator, temp_project):
        """Test validate_all with minimal valid configuration."""
        # Create only required files
        config_file = temp_project / ".tapps-agents" / "config.yaml"
        config_file.write_text(yaml.dump({"version": "3.5.39"}))

        result = validator.validate_all()
        # Should have warnings but be valid overall
        assert result.valid or len(result.errors) == 0

    def test_validate_all_complete(self, validator, temp_project):
        """Test validate_all with complete valid configuration."""
        # Create all files
        config_file = temp_project / ".tapps-agents" / "config.yaml"
        config_file.write_text(yaml.dump({"version": "3.5.39"}))

        tech_stack_file = temp_project / ".tapps-agents" / "tech-stack.yaml"
        tech_stack_file.write_text(yaml.dump({"languages": ["python"]}))

        kb_dir = temp_project / ".tapps-agents" / "kb"
        kb_dir.mkdir(parents=True, exist_ok=True)
        kb_file = kb_dir / "test.md"
        kb_file.write_text("# Test")

        experts_file = temp_project / ".tapps-agents" / "experts.yaml"
        experts_data = {
            "experts": [
                {
                    "name": "test-expert",
                    "description": "Test",
                    "priority": 0.8,
                    "domain": "test",
                    "consultation_triggers": ["test"],
                    "knowledge_files": ["kb/test.md"],
                }
            ]
        }
        experts_file.write_text(yaml.dump(experts_data))

        domains_file = temp_project / ".tapps-agents" / "domains.md"
        domains_file.write_text("# Domains")

        result = validator.validate_all()
        assert result.valid


class TestAutoFix:
    """Test auto-fix functionality."""

    def test_fix_creates_directory(self, temp_project):
        """Test that auto-fix creates missing .tapps-agents directory."""
        # Remove directory
        tapps_dir = temp_project / ".tapps-agents"
        if tapps_dir.exists():
            import shutil
            shutil.rmtree(tapps_dir)

        validator = ConfigValidator(project_root=temp_project, auto_fix=True)
        fixes = validator.fix_common_issues()

        assert fixes >= 1
        assert tapps_dir.exists()

    def test_fix_without_auto_fix_flag(self, temp_project):
        """Test that fix does nothing without auto_fix flag."""
        tapps_dir = temp_project / ".tapps-agents"
        if tapps_dir.exists():
            import shutil
            shutil.rmtree(tapps_dir)

        validator = ConfigValidator(project_root=temp_project, auto_fix=False)
        fixes = validator.fix_common_issues()

        assert fixes == 0
        assert not tapps_dir.exists()


class TestCLI:
    """Test CLI entry point."""

    def test_main_help(self):
        """Test CLI help."""
        import sys
        from io import StringIO
        from tapps_agents.core.validators.config_validator import main

        old_argv = sys.argv
        old_stdout = sys.stdout

        try:
            sys.argv = ["config_validator", "--help"]
            sys.stdout = StringIO()

            with pytest.raises(SystemExit) as exc:
                main()

            assert exc.value.code == 0
        finally:
            sys.argv = old_argv
            sys.stdout = old_stdout
