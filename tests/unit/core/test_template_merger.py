"""
Tests for template merging, conditional blocks, and variable expansion.
"""

from pathlib import Path

import pytest
import yaml

from tapps_agents.core.template_merger import (
    ConditionalTrace,
    TemplateTrace,
    _evaluate_condition,
    _process_conditional_blocks,
    _resolve_variable,
    _resolve_variable_value,
    apply_template_to_config,
    deep_merge_dict,
    expand_variables,
    load_template,
    merge_template_with_config,
)

pytestmark = pytest.mark.unit


class TestVariableResolution:
    """Tests for variable resolution functions."""

    def test_resolve_simple_variable(self):
        """Test resolving a simple variable."""
        variables = {"name": "World"}
        result = _resolve_variable("name", variables)
        assert result == "World"

    def test_resolve_nested_variable(self):
        """Test resolving a nested variable path."""
        variables = {"project": {"name": "MyProject", "root": "/app"}}
        result = _resolve_variable("project.name", variables)
        assert result == "MyProject"

    def test_resolve_missing_variable(self):
        """Test resolving a missing variable returns original syntax."""
        variables = {"name": "World"}
        result = _resolve_variable("missing", variables)
        assert result == "{{missing}}"

    def test_resolve_nested_missing_variable(self):
        """Test resolving a missing nested variable."""
        variables = {"project": {"name": "MyProject"}}
        result = _resolve_variable("project.missing", variables)
        assert result == "{{project.missing}}"

    def test_resolve_variable_value_returns_actual_value(self):
        """Test _resolve_variable_value returns the actual value, not string."""
        variables = {"count": 42, "enabled": True, "items": [1, 2, 3]}
        
        assert _resolve_variable_value("count", variables) == 42
        assert _resolve_variable_value("enabled", variables) is True
        assert _resolve_variable_value("items", variables) == [1, 2, 3]
        assert _resolve_variable_value("missing", variables) is None


class TestConditionEvaluation:
    """Tests for conditional evaluation."""

    def test_evaluate_boolean_true(self):
        """Test evaluating a boolean True condition."""
        variables = {"enabled": True}
        evaluated, value, reason = _evaluate_condition("enabled", variables)
        assert evaluated is True
        assert value is True
        assert "boolean" in reason.lower()

    def test_evaluate_boolean_false(self):
        """Test evaluating a boolean False condition."""
        variables = {"enabled": False}
        evaluated, value, reason = _evaluate_condition("enabled", variables)
        assert evaluated is False
        assert value is False

    def test_evaluate_non_empty_string(self):
        """Test evaluating a non-empty string as truthy."""
        variables = {"name": "test"}
        evaluated, value, reason = _evaluate_condition("name", variables)
        assert evaluated is True
        assert value == "test"

    def test_evaluate_empty_string(self):
        """Test evaluating an empty string as falsy."""
        variables = {"name": ""}
        evaluated, value, reason = _evaluate_condition("name", variables)
        assert evaluated is False
        assert value == ""

    def test_evaluate_non_empty_list(self):
        """Test evaluating a non-empty list as truthy."""
        variables = {"items": [1, 2, 3]}
        evaluated, value, reason = _evaluate_condition("items", variables)
        assert evaluated is True
        assert value == [1, 2, 3]

    def test_evaluate_empty_list(self):
        """Test evaluating an empty list as falsy."""
        variables = {"items": []}
        evaluated, value, reason = _evaluate_condition("items", variables)
        assert evaluated is False
        assert value == []

    def test_evaluate_non_zero_number(self):
        """Test evaluating a non-zero number as truthy."""
        variables = {"count": 42}
        evaluated, value, reason = _evaluate_condition("count", variables)
        assert evaluated is True
        assert value == 42

    def test_evaluate_zero(self):
        """Test evaluating zero as falsy."""
        variables = {"count": 0}
        evaluated, value, reason = _evaluate_condition("count", variables)
        assert evaluated is False
        assert value == 0

    def test_evaluate_missing_variable(self):
        """Test evaluating a missing variable returns False."""
        variables = {"other": "value"}
        evaluated, value, reason = _evaluate_condition("missing", variables)
        assert evaluated is False
        assert value is None
        assert "not found" in reason.lower()


class TestConditionalBlockProcessing:
    """Tests for conditional block processing."""

    def test_simple_if_true(self):
        """Test simple if block with true condition."""
        content = "prefix {{#if enabled}}true content{{/if}} suffix"
        variables = {"enabled": True}
        result = _process_conditional_blocks(content, variables)
        assert "true content" in result
        assert "{{#if enabled}}" not in result
        assert "{{/if}}" not in result

    def test_simple_if_false(self):
        """Test simple if block with false condition."""
        content = "prefix {{#if enabled}}true content{{/if}} suffix"
        variables = {"enabled": False}
        result = _process_conditional_blocks(content, variables)
        assert "true content" not in result
        assert "prefix" in result
        assert "suffix" in result

    def test_if_else_true(self):
        """Test if-else block with true condition."""
        content = "{{#if enabled}}true branch{{#else}}false branch{{/if}}"
        variables = {"enabled": True}
        result = _process_conditional_blocks(content, variables)
        assert "true branch" in result
        assert "false branch" not in result

    def test_if_else_false(self):
        """Test if-else block with false condition."""
        content = "{{#if enabled}}true branch{{#else}}false branch{{/if}}"
        variables = {"enabled": False}
        result = _process_conditional_blocks(content, variables)
        assert "true branch" not in result
        assert "false branch" in result

    def test_nested_variable_condition(self):
        """Test condition with nested variable path."""
        content = "{{#if project.enabled}}enabled{{/if}}"
        variables = {"project": {"enabled": True}}
        result = _process_conditional_blocks(content, variables)
        assert "enabled" in result

    def test_multiple_conditionals(self):
        """Test multiple conditional blocks in same content."""
        content = """{{#if feature_a}}A{{/if}}
{{#if feature_b}}B{{/if}}
{{#if feature_c}}C{{/if}}"""
        variables = {"feature_a": True, "feature_b": False, "feature_c": True}
        result = _process_conditional_blocks(content, variables)
        assert "A" in result
        assert "B" not in result
        assert "C" in result

    def test_conditional_with_trace(self):
        """Test conditional processing records trace information."""
        content = "{{#if enabled}}content{{/if}}"
        variables = {"enabled": True}
        trace = TemplateTrace()
        result = _process_conditional_blocks(content, variables, trace)
        
        assert len(trace.conditionals_evaluated) == 1
        assert trace.conditionals_evaluated[0].variable_path == "enabled"
        assert trace.conditionals_evaluated[0].evaluated is True

    def test_conditional_missing_variable(self):
        """Test conditional with missing variable evaluates to false."""
        content = "{{#if missing}}content{{/if}}"
        variables = {}
        result = _process_conditional_blocks(content, variables)
        assert "content" not in result


class TestVariableExpansion:
    """Tests for variable expansion."""

    def test_expand_simple_string(self):
        """Test expanding variables in a simple string."""
        value = "Hello {{name}}"
        variables = {"name": "World"}
        result = expand_variables(value, variables)
        assert result == "Hello World"

    def test_expand_nested_variable(self):
        """Test expanding nested variables."""
        value = "Project: {{project.name}}"
        variables = {"project": {"name": "MyProject"}}
        result = expand_variables(value, variables)
        assert result == "Project: MyProject"

    def test_expand_in_dict(self):
        """Test expanding variables in dictionary values."""
        value = {"path": "{{project.root}}/src", "name": "{{project.name}}"}
        variables = {"project": {"root": "/app", "name": "MyProject"}}
        result = expand_variables(value, variables)
        assert result == {"path": "/app/src", "name": "MyProject"}

    def test_expand_in_list(self):
        """Test expanding variables in list items."""
        value = ["{{project.root}}/src", "{{project.name}}"]
        variables = {"project": {"root": "/app", "name": "MyProject"}}
        result = expand_variables(value, variables)
        assert result == ["/app/src", "MyProject"]

    def test_expand_missing_variable(self):
        """Test expanding missing variable leaves original syntax."""
        value = "Hello {{missing}}"
        variables = {"name": "World"}
        result = expand_variables(value, variables)
        assert result == "Hello {{missing}}"

    def test_expand_with_trace(self):
        """Test variable expansion records trace information."""
        value = "Hello {{name}}"
        variables = {"name": "World"}
        trace = TemplateTrace()
        result = expand_variables(value, variables, trace=trace)
        
        assert result == "Hello World"
        assert "name" in trace.variable_expansions


class TestDeepMerge:
    """Tests for deep dictionary merging."""

    def test_merge_simple_dicts(self):
        """Test merging simple dictionaries."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = deep_merge_dict(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_merge_nested_dicts(self):
        """Test merging nested dictionaries."""
        base = {"a": 1, "b": {"c": 2, "d": 3}}
        override = {"b": {"d": 4, "e": 5}, "f": 6}
        result = deep_merge_dict(base, override)
        assert result == {"a": 1, "b": {"c": 2, "d": 4, "e": 5}, "f": 6}

    def test_merge_list_replacement(self):
        """Test that lists are replaced, not merged."""
        base = {"items": [1, 2, 3]}
        override = {"items": [4, 5]}
        result = deep_merge_dict(base, override)
        assert result == {"items": [4, 5]}


class TestTemplateLoading:
    """Tests for template loading with conditionals."""

    def test_load_template_with_conditionals(self, tmp_path: Path):
        """Test loading a template with conditional blocks."""
        template_file = tmp_path / "template.yaml"
        template_file.write_text("""key1: value1
{{#if enabled}}
key2: value2
{{/if}}
key3: value3""")
        
        variables = {"enabled": True}
        trace = TemplateTrace()
        result = load_template(template_file, variables, trace)
        
        assert result["key1"] == "value1"
        assert result["key2"] == "value2"
        assert result["key3"] == "value3"
        assert len(trace.conditionals_evaluated) == 1

    def test_load_template_conditional_false(self, tmp_path: Path):
        """Test loading template with false conditional."""
        template_file = tmp_path / "template.yaml"
        template_file.write_text("""key1: value1
{{#if enabled}}
key2: value2
{{/if}}
key3: value3""")
        
        variables = {"enabled": False}
        result = load_template(template_file, variables)
        
        assert result["key1"] == "value1"
        assert "key2" not in result
        assert result["key3"] == "value3"

    def test_load_template_without_conditionals(self, tmp_path: Path):
        """Test loading template without conditionals (backward compatibility)."""
        template_file = tmp_path / "template.yaml"
        template_file.write_text("""key1: value1
key2: value2""")
        
        result = load_template(template_file)
        assert result["key1"] == "value1"
        assert result["key2"] == "value2"


class TestTemplateMerging:
    """Tests for template merging with configs."""

    def test_merge_template_with_defaults(self):
        """Test merging template with default config."""
        template = {"agent_config": {"reviewer": {"quality_threshold": 75.0}}}
        defaults = {"agent_config": {"reviewer": {"quality_threshold": 70.0}}}
        
        result = merge_template_with_config(template, defaults)
        assert result["agent_config"]["reviewer"]["quality_threshold"] == 75.0

    def test_merge_with_user_override(self):
        """Test merging with user config override."""
        template = {"agent_config": {"reviewer": {"quality_threshold": 75.0}}}
        defaults = {"agent_config": {"reviewer": {"quality_threshold": 70.0}}}
        user_config = {"agent_config": {"reviewer": {"quality_threshold": 80.0}}}
        
        result = merge_template_with_config(template, defaults, user_config)
        assert result["agent_config"]["reviewer"]["quality_threshold"] == 80.0

    def test_merge_with_variables(self):
        """Test merging with variable expansion."""
        template = {"path": "{{project.root}}/src"}
        defaults = {}
        variables = {"project": {"root": "/app"}}
        
        result = merge_template_with_config(template, defaults, None, variables)
        assert result["path"] == "/app/src"


class TestApplyTemplateToConfig:
    """Tests for apply_template_to_config (main entry point)."""

    def test_apply_template_with_trace(self, tmp_path: Path):
        """Test applying template with trace enabled."""
        template_file = tmp_path / "template.yaml"
        # Use a simpler template that doesn't require variable expansion in YAML keys
        template_file.write_text("""agent_config:
  reviewer:
    quality_threshold: 75.0
{{#if project.name}}
project_name: "TestProject"
{{/if}}""")
        
        defaults = {"agent_config": {"reviewer": {"quality_threshold": 70.0}}}
        
        trace_file = tmp_path / "trace.json"
        config, trace = apply_template_to_config(
            template_file,
            defaults,
            project_root=tmp_path,
            tech_stack=None,
            project_name="TestProject",
            enable_trace=True,
            trace_output_path=trace_file,
        )
        
        assert config["agent_config"]["reviewer"]["quality_threshold"] == 75.0
        assert config["project_name"] == "TestProject"
        assert trace is not None
        assert trace_file.exists()
        
        # Verify trace content
        trace_data = trace.to_dict()
        assert trace_data["template_path"] == str(template_file)
        assert len(trace_data["conditionals_evaluated"]) > 0

    def test_apply_template_no_file(self):
        """Test applying template when file doesn't exist."""
        defaults = {"key": "value"}
        config, trace = apply_template_to_config(None, defaults)
        assert config == defaults
        assert trace is None

    def test_apply_template_merge_order(self, tmp_path: Path):
        """Test that merge order is correct: defaults < project-type < tech-stack < user."""
        # Simulate project-type template
        project_type_template = tmp_path / "project_type.yaml"
        project_type_template.write_text("""agent_config:
  reviewer:
    quality_threshold: 75.0""")
        
        defaults = {"agent_config": {"reviewer": {"quality_threshold": 70.0}}}
        
        # Apply project-type template
        config1, _ = apply_template_to_config(project_type_template, defaults)
        assert config1["agent_config"]["reviewer"]["quality_threshold"] == 75.0
        
        # Simulate tech-stack template (should override project-type)
        tech_stack_template = tmp_path / "tech_stack.yaml"
        tech_stack_template.write_text("""agent_config:
  reviewer:
    quality_threshold: 80.0""")
        
        # Apply tech-stack template on top of project-type result
        config2, _ = apply_template_to_config(tech_stack_template, config1)
        assert config2["agent_config"]["reviewer"]["quality_threshold"] == 80.0
        
        # Apply user config (should override everything)
        from tapps_agents.core.template_merger import deep_merge_dict
        user_config = {"agent_config": {"reviewer": {"quality_threshold": 85.0}}}
        config3 = deep_merge_dict(config2, user_config)
        assert config3["agent_config"]["reviewer"]["quality_threshold"] == 85.0


class TestTemplateTrace:
    """Tests for TemplateTrace dataclass."""

    def test_trace_to_dict(self):
        """Test converting trace to dictionary."""
        trace = TemplateTrace()
        trace.template_path = "/path/to/template.yaml"
        trace.variables_used = {"project": {"name": "Test"}}
        trace.conditionals_evaluated.append(
            ConditionalTrace(
                condition="{{#if enabled}}",
                variable_path="enabled",
                variable_value=True,
                evaluated=True,
                reason="Variable 'enabled' is boolean: True",
            )
        )
        
        result = trace.to_dict()
        assert result["template_path"] == "/path/to/template.yaml"
        assert len(result["conditionals_evaluated"]) == 1
        assert result["conditionals_evaluated"][0]["evaluated"] is True

    def test_trace_to_json(self):
        """Test converting trace to JSON string."""
        trace = TemplateTrace()
        trace.template_path = "/path/to/template.yaml"
        json_str = trace.to_json()
        
        import json
        data = json.loads(json_str)
        assert data["template_path"] == "/path/to/template.yaml"

